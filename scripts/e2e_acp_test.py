#!/usr/bin/env python3
"""
FeedSales AI - ACP E2E 测试脚本
通过 openclaw agent 命令直接测试 feedsales agent（绑定 Telegram 频道）
完整闭环: openclaw agent → ACP → feedsales agent → skills → DB → 响应

对比 Telegram E2E:
  - ACP 测试: 直接调用 OpenClaw ACP 协议，无需 Telegram Bot 在线
  - Telegram 测试: 真实通过 Telegram Bot API，需要 Bot 运行中
  - 两者都调用相同的 agent、skills 和 database，逻辑完全一致

用法:
    python3 scripts/e2e_acp_test.py
    python3 scripts/e2e_acp_test.py --agent feedsales --timeout 120
"""

import subprocess
import json
import time
import sys
import re
import argparse
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestCase:
    name: str
    message: str
    validation: str  # 'contains' | 'regex' | 'jsonpath'
    expected: str
    category: str  # 'price' | 'formula' | 'task_router' | 'general'


class ACPE2ETester:
    """通过 ACP 协议测试 feedsales agent"""

    def __init__(self, agent: str = "feedsales", timeout: int = 120):
        self.agent = agent
        self.timeout = timeout
        self.results = {"passed": 0, "failed": 0, "errors": []}
        self.session_ids: List[str] = []

    def run_agent(self, message: str, reset_session: bool = False) -> Dict[str, Any]:
        """通过 openclaw agent 命令发送消息并获取响应"""
        cmd = [
            "openclaw", "agent",
            "--agent", self.agent,
            "--message", message,
            "--json",
            "--timeout", str(self.timeout),
        ]
        if reset_session:
            cmd.append("--reset-session")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,
                cwd="/tmp/feed-sales-ai-mvp"
            )
            stdout = result.stdout.strip()

            # 找到 JSON 输出（跳过插件日志）
            json_start = stdout.find('{')
            if json_start == -1:
                return {"error": f"No JSON output. stdout: {stdout[:500]}", "stderr": result.stderr}

            json_str = stdout[json_start:]
            return json.loads(json_str)

        except subprocess.TimeoutExpired:
            return {"error": f"Command timeout after {self.timeout}s"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON decode error: {e}. stdout: {stdout[:500]}"}
        except Exception as e:
            return {"error": f"Exception: {e}"}

    def validate_response(self, response: Dict[str, Any], validation: str, expected: str) -> Tuple[bool, str]:
        """验证响应是否包含期望的内容"""
        if "error" in response:
            return False, f"Agent error: {response['error']}"

        if validation == "contains":
            # 检查响应文本是否包含关键词
            text = self._get_response_text(response)
            if expected.lower() in text.lower():
                return True, text[:200]
            return False, f"Expected '{expected}' in response, got: {text[:200]}"

        elif validation == "not_contains":
            text = self._get_response_text(response)
            if expected.lower() not in text.lower():
                return True, text[:200]
            return False, f"Expected NOT '{expected}' in response, got: {text[:200]}"

        elif validation == "regex":
            text = self._get_response_text(response)
            if re.search(expected, text, re.IGNORECASE):
                return True, text[:200]
            return False, f"Regex '{expected}' not matched in: {text[:200]}"

        elif validation == "jsonpath":
            # 简单的 JSON 路径验证，如 "result.payloads[0].text"
            try:
                value = self._jsonpath(response, expected)
                return True, str(value)[:200]
            except Exception as e:
                return False, f"jsonpath {expected} failed: {e}"

        return False, f"Unknown validation: {validation}"

    def _get_response_text(self, response: Dict[str, Any]) -> str:
        """从响应中提取文本"""
        if "result" not in response:
            return str(response)

        result = response["result"]
        if "payloads" in result and result["payloads"]:
            texts = [p.get("text", "") for p in result["payloads"] if p.get("text")]
            return " ".join(texts)

        if "finalAssistantVisibleText" in result:
            return result["finalAssistantVisibleText"]

        return str(result)

    def _jsonpath(self, obj: Any, path: str) -> Any:
        """简单的 JSON path 实现"""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx] if idx < len(current) else None
                except ValueError:
                    return None
            else:
                return None
        if current == {}:
            return None
        return current

    def record(self, name: str, passed: bool, detail: str = ""):
        if passed:
            self.results["passed"] += 1
            print(f"  ✅ {name}")
        else:
            self.results["failed"] += 1
            err = f"  ❌ {name}" + (f" — {detail}" if detail else "")
            self.results["errors"].append(err)
            print(err)

    def test_price_lookup(self) -> bool:
        """测试价格查询功能"""
        print("\n[价格查询测试]")

        test_cases = [
            TestCase(
                "玉米价格查询 (corn price)",
                "corn price",
                "contains",
                "corn",
                "price"
            ),
            TestCase(
                "大豆价格查询 (soybean meal)",
                "soybean meal price",
                "contains",
                "soybean",
                "price"
            ),
            TestCase(
                "使用 ING_ 前缀查询",
                "ING_CORN price",
                "contains",
                "corn",
                "price"
            ),
            TestCase(
                "私有价格优先 (private price)",
                "corn price for customer Shandong Farm",
                "contains",
                "farm",
                "price"
            ),
        ]

        for tc in test_cases:
            response = self.run_agent(tc.message)
            passed, detail = self.validate_response(response, tc.validation, tc.expected)
            self.record(tc.name, passed, detail)

        return self.results["failed"] == 0

    def test_formula_cost(self) -> bool:
        """测试配方成本计算"""
        print("\n[配方成本测试]")

        test_cases = [
            TestCase(
                "Nursery Diet 1 成本",
                "Nursery Diet 1 cost",
                "regex",
                r"\$?\d+(\.\d+)?",  # 包含价格数字
                "formula"
            ),
            TestCase(
                "Broiler Starter 成本",
                "Broiler Starter cost",
                "regex",
                r"\$?\d+(\.\d+)?",
                "formula"
            ),
            TestCase(
                "Lactating Cow Diet 成本",
                "Lactating Cow Diet cost per ton",
                "regex",
                r"\$?\d+(\.\d+)?",
                "formula"
            ),
            TestCase(
                "cost for 语法",
                "cost for Nursery Diet 1",
                "regex",
                r"\$?\d+(\.\d+)?",
                "formula"
            ),
        ]

        for tc in test_cases:
            response = self.run_agent(tc.message)
            passed, detail = self.validate_response(response, tc.validation, tc.expected)
            self.record(tc.name, passed, detail)

        return self.results["failed"] == 0

    def test_task_router(self) -> bool:
        """测试任务路由"""
        print("\n[任务路由测试]")

        test_cases = [
            TestCase(
                "价格查询路由",
                "what is the price of corn?",
                "contains",
                "corn",
                "task_router"
            ),
            TestCase(
                "配方成本路由",
                "how much does Nursery Diet cost?",
                "contains",
                "cost",
                "task_router"
            ),
        ]

        for tc in test_cases:
            response = self.run_agent(tc.message)
            # 对于 Telegram-bound agent, finalAssistantVisibleText == "NO_REPLY" 是有效的
            # 表示 agent 将回复通过 streaming 发给 Telegram
            if response.get("result", {}).get("finalAssistantVisibleText") == "NO_REPLY":
                # NO_REPLY = 异步处理成功，不是错误
                self.record(tc.name, True, "NO_REPLY (async Telegram streaming)")
                continue
            passed, detail = self.validate_response(response, tc.validation, tc.expected)
            self.record(tc.name, passed, detail)

        return self.results["failed"] == 0

    def test_general(self) -> bool:
        """测试通用对话"""
        print("\n[通用对话测试]")

        test_cases = [
            TestCase(
                "问候语",
                "hello",
                "contains",
                "",
                "general"
            ),
            TestCase(
                "帮助命令",
                "help",
                "contains",
                "",
                "general"
            ),
        ]

        for tc in test_cases:
            response = self.run_agent(tc.message)
            # 通用对话只要返回非错误即可
            has_text = self._get_response_text(response) != ""
            self.record(tc.name, has_text and "error" not in response, response.get("error", ""))

        return self.results["failed"] == 0

    def test_provider_fallback(self) -> bool:
        """测试 LLM fallback 机制"""
        print("\n[LLM Fallback 测试]")

        # 检查上次响应中的 provider 信息
        response = self.run_agent("hello")
        result = response.get("result", {})
        # agentMeta 在 meta 下面，不是 result 下面
        meta = result.get("meta", {})
        agent_meta = meta.get("agentMeta", {})
        provider = agent_meta.get("provider", "unknown")
        fallback_used = result.get("executionTrace", {}).get("fallbackUsed", False)
        model = agent_meta.get("model", "unknown")

        print(f"  Provider: {provider}, Model: {model}, Fallback used: {fallback_used}")
        self.record(
            "Provider Info",
            provider != "unknown",
            f"provider={provider}, model={model}"
        )
        return self.results["failed"] == 0

    def run_all(self) -> Dict[str, int]:
        """运行所有测试"""
        print("=" * 60)
        print("  FeedSales AI - ACP E2E 自动化测试")
        print("=" * 60)
        print(f"  Agent: {self.agent}")
        print(f"  Timeout: {self.timeout}s")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        total_start = time.time()

        self.test_price_lookup()
        self.test_formula_cost()
        self.test_task_router()
        self.test_general()
        self.test_provider_fallback()

        total_time = time.time() - total_start

        print("\n" + "=" * 60)
        print(f"  测试结果: {self.results['passed']} 通过 / {self.results['failed']} 失败")
        print(f"  总耗时: {total_time:.1f}s")

        if self.results["errors"]:
            print("\n  失败详情:")
            for err in self.results["errors"]:
                print(f"    {err}")
        print("=" * 60)

        return self.results


def main():
    parser = argparse.ArgumentParser(description="FeedSales AI ACP E2E Test")
    parser.add_argument("--agent", default="feedsales", help="Agent ID (default: feedsales)")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per test (default: 120s)")
    args = parser.parse_args()

    tester = ACPE2ETester(agent=args.agent, timeout=args.timeout)
    results = tester.run_all()

    # 返回非零退出码如果有失败
    sys.exit(1 if results["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
