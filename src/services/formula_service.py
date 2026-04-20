"""
FeedSales AI - FormulaService

配方管理服务，支持多租户隔离和私有优先查询
import sys as _sys
from pathlib import _Path
if _Path(__file__).parent.parent not in _sys.path:
    _sys.path.insert(0, str(_Path(__file__).parent.parent))
"""

import logging
from typing import Dict, List, Optional
from ..database.pool import DatabasePool
from ..database.repository import FormulaRepository
from ..result_types import ServiceResult
from ..utils.ingredient_codes import generate_ingredient_code

logger = logging.getLogger(__name__)


class FormulaService:
    """配方管理服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.repo = FormulaRepository(db_pool)
    
    def get_formula(self, user_id: str, name: str) -> ServiceResult:
        """
        获取配方（私有优先）
        
        Args:
            user_id: 用户 ID
            name: 配方名称
            
        Returns:
            ServiceResult: 包含配方数据和来源
        """
        # 1. 先查私有配方
        formula = self.repo.get_formula(user_id, name)
        if formula:
            return ServiceResult(
                success=True,
                data=formula,
                source='private'
            )
        
        # 2. 再查公共配方
        formula = self.repo.get_formula('system_public', name)
        if formula:
            return ServiceResult(
                success=True,
                data=formula,
                source='public'
            )
        
        # 3. 不存在
        return ServiceResult(
            success=False,
            error_code='E002',
            error_message=f"配方 '{name}' 不存在"
        )
    
    def list_formulas(self, user_id: str) -> ServiceResult:
        """
        列出用户所有配方（私有 + 公共）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 包含配方列表
        """
        formulas = self.repo.list_formulas(user_id)
        
        # 获取公共配方
        public_formulas = self.repo.list_formulas('system_public')
        
        # 合并，标记来源
        all_formulas = []
        for f in formulas:
            f['source'] = 'private'
            all_formulas.append(f)
        
        private_names = {f['name'] for f in formulas}
        for f in public_formulas:
            if f['name'] not in private_names:
                f['source'] = 'public'
                all_formulas.append(f)
        
        return ServiceResult(
            success=True,
            data={'formulas': all_formulas, 'total': len(all_formulas)}
        )
    
    def create_formula(self, user_id: str, data: Dict) -> ServiceResult:
        """
        创建配方
        
        Args:
            user_id: 用户 ID
            data: 配方数据
            
        Returns:
            ServiceResult: 包含创建的配方
        """
        # 验证必填字段
        if not data.get('name'):
            return ServiceResult(
                success=False,
                error_code='E001',
                error_message='配方名称不能为空'
            )
        
        if not data.get('stage_type'):
            return ServiceResult(
                success=False,
                error_code='E001',
                error_message='饲养阶段不能为空'
            )
        
        # 检查是否已存在
        existing = self.repo.get_formula(user_id, data['name'])
        if existing:
            return ServiceResult(
                success=False,
                error_code='E004',
                error_message=f"配方 '{data['name']}' 已存在"
            )
        
        # 创建配方
        formula_data = {
            'name': data['name'],
            'stage_type': data['stage_type'],
            'notes': data.get('notes'),
            'ingredients': data.get('ingredients', [])
        }
        
        try:
            formula_id = self.repo.create_formula(user_id, formula_data)
            
            # 获取创建的配方
            formula = self.repo.get_formula(user_id, data['name'])
            formula['version'] = 1
            
            return ServiceResult(
                success=True,
                data=formula,
                source='private'
            )
            
        except Exception as e:
            logger.error(f"创建配方失败: {e}")
            return ServiceResult(
                success=False,
                error_code='E005',
                error_message=f"创建配方失败: {str(e)}"
            )
    
    def update_formula(self, user_id: str, formula_id: int, 
                      data: Dict, expected_version: int) -> ServiceResult:
        """
        更新配方（乐观锁）
        
        Args:
            user_id: 用户 ID
            formula_id: 配方 ID
            data: 更新数据
            expected_version: 期望版本号
            
        Returns:
            ServiceResult: 包含更新后的配方
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先检查版本
            cursor.execute(
                "SELECT id, version FROM formulas WHERE id = ? AND owner_open_id = ?",
                (formula_id, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return ServiceResult(
                    success=False,
                    error_code='E003',
                    error_message='无权修改此配方或配方不存在'
                )
            
            current_version = row['version']
            if current_version != expected_version:
                return ServiceResult(
                    success=False,
                    error_code='E006',
                    error_message='数据已被其他用户修改，请刷新后重试'
                )
            
            # 更新配方
            update_fields = []
            update_values = []
            
            if 'animal_type' in data:
                update_fields.append('animal_type = ?')
                update_values.append(data['animal_type'])
            
            if 'stage_type' in data:
                update_fields.append('stage_type = ?')
                update_values.append(data['stage_type'])
            
            if 'notes' in data:
                update_fields.append('notes = ?')
                update_values.append(data['notes'])
            
            update_fields.append('version = version + 1')
            update_values.extend([formula_id, user_id, expected_version])
            
            cursor.execute(f'''
                UPDATE formulas 
                SET {', '.join(update_fields)}
                WHERE id = ? AND owner_open_id = ? AND version = ?
            ''', update_values)
            
            if cursor.rowcount == 0:
                return ServiceResult(
                    success=False,
                    error_code='E006',
                    error_message='数据已被其他用户修改，请刷新后重试'
                )
            
            # 更新成分（带 ingredient_code，显式校验）
            if 'ingredients' in data:
                cursor.execute(
                    "DELETE FROM formula_ingredients WHERE formula_id = ?",
                    (formula_id,)
                )
                
                for ing in data['ingredients']:
                    if not ing.get('ingredient_code'):
                        return ServiceResult(
                            success=False,
                            error_code='E001',
                            error_message=f"ingredient['ingredient_code'] required for '{ing['name']}'"
                        )
                    ing_name = ing['name']
                    ing_code = ing['ingredient_code']  # 显式使用已有 code，不再 fallback
                    cursor.execute('''
                        INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent)
                        VALUES (?, ?, ?, ?)
                    ''', (formula_id, ing_name, ing_code, ing['ratio']))
            
            conn.commit()
            
            # 获取更新后的配方
            formula = self.repo.get_formula_by_id(formula_id)
            formula['version'] = expected_version + 1
            
            return ServiceResult(
                success=True,
                data=formula,
                source='private'
            )
    
    def delete_formula(self, user_id: str, formula_id: int) -> ServiceResult:
        """
        删除配方
        
        Args:
            user_id: 用户 ID
            formula_id: 配方 ID
            
        Returns:
            ServiceResult: 操作结果
        """
        # 检查权限
        formula = self.repo.get_formula_by_id(formula_id)
        if not formula:
            return ServiceResult(
                success=False,
                error_code='E002',
                error_message='配方不存在'
            )
        
        if formula.get('owner_open_id') != user_id:
            return ServiceResult(
                success=False,
                error_code='E003',
                error_message='无权删除此配方'
            )
        
        # 不允许删除公共配方
        if formula.get('owner_open_id') == 'system_public':
            return ServiceResult(
                success=False,
                error_code='E003',
                error_message='不能删除公共配方'
            )
        
        success = self.repo.delete_formula(user_id, formula_id)
        
        if success:
            return ServiceResult(success=True)
        else:
            return ServiceResult(
                success=False,
                error_code='E005',
                error_message='删除配方失败'
            )