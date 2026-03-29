#!/usr/bin/env python3
"""
FeedSales AI - Telegram E2E 自动化测试

使用方法：
1. 设置环境变量：
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_TEST_CHAT_ID="your_chat_id"

2. 运行测试：
   python3 tests/test_telegram_e2e.py
"""

import asyncio
import os
import sys
from typing import Optional
import time

# 添加项目路径
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot 未安装，请运行：pip install python-telegram-bot")


class TelegramTestClient:
    """Telegram 测试客户端"""
    
    def __init__(self, token: str, chat_id: str):
        if not TELEGRAM_AVAILABLE:
            raise RuntimeError("python-telegram-bot 未安装")
        self.bot = Bot(token)
        self.chat_id = chat_id
        self.last_message_id = None
        self.test_results = []
    
    async def send_message(self, text: str):
        """发送消息"""
        try:
            msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=text
            )
            self.last_message_id = msg.message_id
            return msg
        except TelegramError as e:
            print(f"❌ 发送失败：{e}")
            return None
    
    async def get_response(self, timeout: int = 30) -> Optional[str]:
        """获取回复"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                updates = await self.bot.get_updates(
                    offset=-10,  # 获取最近 10 条更新
                    timeout=5,
                    allowed_updates=['message']
                )
                
                for update in reversed(updates):  # 从最新的开始
                    if update.message:
                        # 检查是否是回复我们的消息
                        if (update.message.reply_to_message and 
                            update.message.reply_to_message.message_id == self.last_message_id):
                            return update.message.text
                        
                        # 或者是新的消息（非回复）
                        # 简单判断：消息在发送之后
                        if self.last_message_id is None:
                            return update.message.text
                
                await asyncio.sleep(1)
                
            except TelegramError as e:
                print(f"⚠️ 获取更新失败：{e}")
                await asyncio.sleep(2)
        
        return None
    
    def log_result(self, test_name: str, passed: bool, input_text: str, response: str = ""):
        """记录测试结果"""
        result = {
            'name': test_name,
            'passed': passed,
            'input': input_text,
            'response': response
        }
        self.test_results.append(result)
        
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
        if not passed:
            print(f"   输入: {input_text}")
            print(f"   响应: {response[:100]}..." if len(response) > 100 else f"   响应: {response}")


class FeedSalesTestSuite:
    """FeedSales AI 测试套件"""
    
    def __init__(self, client: TelegramTestClient, user_id: str):
        self.client = client
        self.user_id = user_id
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("FeedSales AI v1.7 - Telegram E2E 测试")
        print("=" * 60)
        
        # 基础功能测试
        await self.test_basic_cost_query()
        
        # 饲料种类测试
        await self.test_formula_types()
        
        # 语言模式测试
        await self.test_language_modes()
        
        # 错误处理测试
        await self.test_error_handling()
        
        # 打印总结
        self.print_summary()
    
    async def test_basic_cost_query(self):
        """测试基础成本查询"""
        print("\n📝 基础功能测试")
        
        tests = [
            ("TC-01 公共配方成本", "计算 Nursery Diet 1 的成本", ["成本", "$", "USD"]),
            ("TC-02 中文口语", "保育料多少钱一吨", ["成本", "$"]),
            ("TC-03 简短查询", "Nursery Diet 1 成本", ["$", "USD"]),
        ]
        
        for name, input_text, keywords in tests:
            await self.client.send_message(input_text)
            response = await self.client.get_response()
            
            passed = response and any(kw in response for kw in keywords)
            self.client.log_result(name, passed, input_text, response)
            
            await asyncio.sleep(1)
    
    async def test_formula_types(self):
        """测试不同饲料类型"""
        print("\n📝 饲料种类测试")
        
        tests = [
            ("TC-10 Swine Nursery", "计算保育料成本", ["成本", "$"]),
            ("TC-11 Swine Growing", "计算生长猪料成本", ["成本", "$"]),
            ("TC-12 Swine Finishing", "计算育肥料成本", ["成本", "$"]),
            ("TC-13 Broiler Starter", "计算肉鸡开食料成本", ["成本", "$"]),
            ("TC-14 Layer Laying", "计算产蛋期料成本", ["成本", "$"]),
        ]
        
        for name, input_text, keywords in tests:
            await self.client.send_message(input_text)
            response = await self.client.get_response()
            
            passed = response and any(kw in response for kw in keywords)
            self.client.log_result(name, passed, input_text, response)
            
            await asyncio.sleep(1)
    
    async def test_language_modes(self):
        """测试语言模式"""
        print("\n📝 语言模式测试")
        
        tests = [
            ("TC-20 中文", "保育料 1 号成本", ["成本", "$"]),
            ("TC-21 中英混合", "计算 Nursery Diet 1 的成本", ["成本", "$"]),
            ("TC-22 英文", "Calculate Nursery Diet 1 cost", ["cost", "$"]),
        ]
        
        for name, input_text, keywords in tests:
            await self.client.send_message(input_text)
            response = await self.client.get_response()
            
            passed = response and any(kw.lower() in response.lower() for kw in keywords)
            self.client.log_result(name, passed, input_text, response)
            
            await asyncio.sleep(1)
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n📝 错误处理测试")
        
        tests = [
            ("TC-30 不存在的配方", "计算不存在的配方成本", ["不存在", "E002", "错误"]),
            ("TC-31 缺少参数", "计算成本", ["请指定", "配方"]),
        ]
        
        for name, input_text, keywords in tests:
            await self.client.send_message(input_text)
            response = await self.client.get_response()
            
            # 错误场景：期望包含错误提示
            passed = response and any(kw in response for kw in keywords)
            self.client.log_result(name, passed, input_text, response)
            
            await asyncio.sleep(1)
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        total = len(self.client.test_results)
        passed = sum(1 for r in self.client.test_results if r['passed'])
        failed = total - passed
        
        print(f"总计: {total} 个测试")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        if failed > 0:
            print("\n失败测试:")
            for r in self.client.test_results:
                if not r['passed']:
                    print(f"  - {r['name']}: {r['input']}")


async def main():
    """主函数"""
    # 从环境变量获取配置
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_TEST_CHAT_ID')
    user_id = os.getenv('TELEGRAM_TEST_USER_ID', 'test_user')
    
    if not token or not chat_id:
        print("❌ 请设置环境变量：")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_TEST_CHAT_ID='your_chat_id'")
        sys.exit(1)
    
    if not TELEGRAM_AVAILABLE:
        sys.exit(1)
    
    # 创建客户端和测试套件
    client = TelegramTestClient(token, chat_id)
    suite = FeedSalesTestSuite(client, user_id)
    
    # 运行测试
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())