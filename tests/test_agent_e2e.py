#!/usr/bin/env python3
"""
FeedSales AI - True Agent E2E Test Suite

Tests the FULL agent flow:
  User Message -> Agent (LLM NLU) -> Skill Selection -> Skill Execution -> Response

Usage:
    python3 tests/test_agent_e2e.py
"""

import subprocess
import json
import time
import sys
import re
import argparse
from datetime import datetime
from typing import Dict, Any, List, Tuple


class AgentE2ETest:
    """True Agent E2E test via OpenClaw CLI"""

    def __init__(self, agent: str = "feedsales", timeout: int = 60):
        self.agent = agent
        self.timeout = timeout
        self.results = {"passed": 0, "failed": 0, "tests": []}

    def run_agent(self, message: str) -> Dict[str, Any]:
        """Send message to agent via OpenClaw CLI"""
        cmd = [
            "openclaw", "agent",
            "--agent", self.agent,
            "--message", message,
            "--json",
            "--timeout", str(self.timeout),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10
            )
            stdout = result.stdout.strip()
            json_start = stdout.find("{")
            if json_start == -1:
                return {"error": f"No JSON in output: {stdout[:300]}"}
            return json.loads(stdout[json_start:])
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout after {self.timeout}s"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def extract_text(self, response: Dict) -> str:
        """Extract response text from agent output"""
        if "error" in response:
            return response["error"]
        result = response.get("result", {})
        if "payloads" in result and result["payloads"]:
            texts = [p.get("text", "") for p in result["payloads"] if p.get("text")]
            return " ".join(texts)
        if "finalAssistantVisibleText" in result:
            return result["finalAssistantVisibleText"]
        if "assistantMessage" in result:
            return result["assistantMessage"]
        return str(result)[:500]

    def test_case(self, name: str, message: str, expected_patterns: List[str],
                  category: str = "general") -> Tuple[bool, str]:
        """Run a single test case"""
        print(f"  Testing: {name}...")
        response = self.run_agent(message)
        text = self.extract_text(response)
        
        passed = True
        missing = []
        for pattern in expected_patterns:
            if not re.search(pattern, text, re.IGNORECASE):
                passed = False
                missing.append(pattern)
        
        detail = text[:150] if passed else f"Missing: {missing}. Got: {text[:150]}"
        
        self.results["tests"].append({
            "name": name, "category": category, "message": message,
            "passed": passed, "response": text[:200]
        })
        
        if passed:
            self.results["passed"] += 1
            print(f"    PASS")
        else:
            self.results["failed"] += 1
            print(f"    FAIL - {detail}")
        
        return passed, detail


def main():
    parser = argparse.ArgumentParser(description="FeedSales Agent E2E Test")
    parser.add_argument("--quick", action="store_true", help="Run quick subset")
    args = parser.parse_args()

    tester = AgentE2ETest(agent="feedsales", timeout=60)

    print("=" * 60)
    print("  FeedSales AI - TRUE AGENT E2E Test Suite")
    print("=" * 60)
    print(f"  Agent: {tester.agent}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    start_time = time.time()

    # Price Lookup Tests
    print("\n[PRICE LOOKUP - Agent NLU Tests]")
    tests = [
        ("Direct price query", "What is the price of corn?", [r"corn", r"\$?\d+"]),
        ("Short form query", "corn price", [r"corn", r"\$?\d+"]),
        ("Soybean meal price", "How much is soybean meal per ton?", [r"soybean", r"\$?\d+"]),
    ]
    for name, msg, patterns in tests:
        tester.test_case(name, msg, patterns, "price")

    # Formula Cost Tests
    print("\n[FORMULA COST - Agent NLU Tests]")
    tests = [
        ("Nursery Diet cost", "Calculate the cost of Nursery Diet 1", [r"nursery", r"\$?\d+"]),
        ("Short form cost", "Nursery Diet 1 cost", [r"\$?\d+"]),
        ("Broiler Starter cost", "How much does Broiler Starter cost per ton?", [r"\$?\d+"]),
    ]
    for name, msg, patterns in tests:
        tester.test_case(name, msg, patterns, "formula")

    # Customer Tests
    print("\n[CUSTOMER MANAGEMENT - Agent NLU Tests]")
    tests = [
        ("List customers", "show all my customers", [r"customer|Smith"]),
        ("Find customer", "find customer Smith Farm", [r"smith"]),
    ]
    for name, msg, patterns in tests:
        tester.test_case(name, msg, patterns, "customer")

    # Nutrition Tests
    print("\n[NUTRITION ANALYSIS - Agent NLU Tests]")
    tests = [
        ("Analyze formula", "analyze Nursery Diet 1 nutrition", [r"protein|energy|nutrition"]),
    ]
    for name, msg, patterns in tests:
        tester.test_case(name, msg, patterns, "nutrition")

    # General Tests
    print("\n[GENERAL CONVERSATION - Agent NLU Tests]")
    tests = [
        ("Greeting", "hello", [r"hello|hi|help"]),
        ("Help request", "what can you do?", [r"price|cost|formula|customer"]),
    ]
    for name, msg, patterns in tests:
        tester.test_case(name, msg, patterns, "general")

    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print(f"  Results: {tester.results['passed']} PASSED / {tester.results['failed']} FAILED")
    print(f"  Total time: {total_time:.1f}s")
    print("=" * 60)

    sys.exit(1 if tester.results["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
