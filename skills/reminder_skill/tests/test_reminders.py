#!/usr/bin/env python3
"""
Reminder 功能测试 - TDD
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径 - 使用绝对路径
import os
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

# 设置 PYTHONPATH 环境变量
os.environ['PYTHONPATH'] = str(_project_root)


class TestReminderService:
    """测试 ReminderService"""
    
    @pytest.fixture
    def db_pool(self):
        """创建临时数据库连接池"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        from src.database.pool import DatabasePool
        pool = DatabasePool(db_path)
        
        yield pool
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_service_initialization(self, db_pool):
        """服务应该正确初始化"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        assert service is not None
    
    def test_create_price_reminder(self, db_pool):
        """应该能创建价格提醒"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        result = service.create_reminder(
            user_id="123456",
            reminder_type="price",
            threshold=400.0,
            condition="above",
            ingredient="Soybean meal, 48%",
            ingredient_code="ING_SBM_48"
        )
        
        assert result.success
        assert result.data["user_id"] == "123456"
        assert result.data["type"] == "price"
        assert result.data["threshold"] == 400.0
    
    def test_create_formula_cost_reminder(self, db_pool):
        """应该能创建配方成本提醒"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        result = service.create_reminder(
            user_id="123456",
            reminder_type="formula_cost",
            threshold=300.0,
            condition="above",
            formula="Nursery Diet 1",
            formula_id="FORMULA_NURSERY_1"
        )
        
        assert result.success
        assert result.data["type"] == "formula_cost"
    
    def test_list_user_reminders(self, db_pool):
        """应该能查询用户的提醒列表"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        # 创建两个用户的提醒
        service.create_reminder("user_a", "price", 400, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        service.create_reminder("user_b", "price", 380, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        service.create_reminder("user_a", "price", 2000, "above", ingredient="Fish meal", ingredient_code="ING_FISH_65")
        
        # 查询 user_a 的提醒
        result = service.list_reminders("user_a")
        
        assert result.success
        assert result.data["count"] == 2
    
    def test_user_isolation(self, db_pool):
        """用户应该只能看到自己的提醒"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        # 创建多个用户的提醒
        service.create_reminder("user_a", "price", 400, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        service.create_reminder("user_b", "price", 380, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        service.create_reminder("user_c", "price", 350, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        
        # 验证每个用户只能看到自己的提醒
        for user_id in ["user_a", "user_b", "user_c"]:
            result = service.list_reminders(user_id)
            assert result.data["count"] == 1
            assert result.data["reminders"][0]["user_id"] == user_id
    
    def test_delete_reminder_with_user_check(self, db_pool):
        """删除提醒时应该检查用户 ID"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        # 创建提醒
        create_result = service.create_reminder("user_a", "price", 400, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        reminder_id = create_result.data["id"]
        
        # 用户 B 尝试删除（应该失败）
        delete_result = service.delete_reminder(reminder_id, "user_b")
        assert not delete_result.success
        assert delete_result.error_code == "NOT_FOUND"
        
        # 用户 A 删除（应该成功）
        delete_result = service.delete_reminder(reminder_id, "user_a")
        assert delete_result.success
    
    def test_get_all_enabled_reminders(self, db_pool):
        """应该能获取所有启用的提醒"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        # 创建多个提醒
        service.create_reminder("user_a", "price", 400, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        service.create_reminder("user_b", "price", 380, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        
        result = service.get_all_enabled_reminders()
        
        assert result.success
        assert result.data["count"] == 2
    
    def test_disable_reminder(self, db_pool):
        """应该能禁用提醒"""
        from src.services.reminder_service import ReminderService
        service = ReminderService(db_pool)
        
        # 创建提醒
        create_result = service.create_reminder("user_a", "price", 400, "above", ingredient="SBM", ingredient_code="ING_SBM_48")
        reminder_id = create_result.data["id"]
        
        # 禁用提醒
        disable_result = service.disable_reminder(reminder_id, "user_a")
        assert disable_result.success
        
        # 验证已禁用
        list_result = service.list_reminders("user_a", enabled_only=True)
        assert list_result.data["count"] == 0


class TestIngredientMapping:
    """测试原料名称映射"""
    
    def test_ingredient_mapping_exists(self):
        """原料映射文件应该存在"""
        mapping_path = Path(__file__).parent.parent / "reference" / "ingredient_codes.json"
        assert mapping_path.exists()
    
    def test_normalize_ingredient(self):
        """应该能标准化原料名称"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from reminder_service import normalize_ingredient
        
        result = normalize_ingredient("豆粕")
        assert result["code"] == "ING_SBM_48"
        
        result = normalize_ingredient("corn")
        assert result["code"] == "ING_CORN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
