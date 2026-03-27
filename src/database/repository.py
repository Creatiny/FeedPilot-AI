"""
FeedSales AI - Repository Layer

数据访问层，提供多租户隔离的 CRUD 操作
"""

import logging
from typing import Optional, List, Dict
from datetime import date
from .pool import DatabasePool


logger = logging.getLogger(__name__)


def validate_owner_open_id(owner_open_id: str) -> bool:
    """验证 owner_open_id 格式"""
    if not owner_open_id or len(owner_open_id) > 100:
        return False
    return True


def validate_formula_name(formula_name: str) -> bool:
    """验证配方名称格式"""
    if not formula_name or len(formula_name) > 200:
        return False
    return True


class FormulaRepository:
    """配方数据访问层"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
    
    def get_formula(self, owner_open_id: str, formula_name: str) -> Optional[Dict]:
        """获取用户专属配方"""
        # 输入验证
        if not validate_owner_open_id(owner_open_id):
            raise ValueError("无效的 owner_open_id")
        if not validate_formula_name(formula_name):
            raise ValueError("无效的配方名称")
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.id, f.name, f.stage_type, f.notes,
                       fi.ingredient_name, fi.ratio_percent
                FROM formulas f
                LEFT JOIN formula_ingredients fi ON f.id = fi.formula_id
                WHERE f.owner_open_id = ? AND f.name = ?
            """, (owner_open_id, formula_name))
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            # 重组数据
            formula = {
                'id': rows[0]['id'],
                'name': rows[0]['name'],
                'stage_type': rows[0]['stage_type'],
                'notes': rows[0]['notes'],
                'ingredients': []
            }
            for row in rows:
                if row['ingredient_name']:
                    formula['ingredients'].append({
                        'name': row['ingredient_name'],
                        'ratio': row['ratio_percent']
                    })
            return formula
    
    def list_formulas(self, owner_open_id: str) -> List[Dict]:
        """列出用户所有配方"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, stage_type, notes, created_at
                FROM formulas
                WHERE owner_open_id = ?
                ORDER BY created_at DESC
            """, (owner_open_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create_formula(self, owner_open_id: str, formula_data: Dict) -> int:
        """创建用户配方"""
        # 输入验证
        if not validate_owner_open_id(owner_open_id):
            raise ValueError("无效的 owner_open_id")
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入配方
            cursor.execute("""
                INSERT INTO formulas (owner_open_id, name, stage_type, notes)
                VALUES (?, ?, ?, ?)
            """, (owner_open_id, formula_data['name'], 
                  formula_data['stage_type'], formula_data.get('notes')))
            
            formula_id = cursor.lastrowid
            logger.info(f"创建配方成功 (ID: {formula_id}, 用户：{owner_open_id})")
            
            # 插入成分
            for ingredient in formula_data['ingredients']:
                cursor.execute("""
                    INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
                    VALUES (?, ?, ?)
                """, (formula_id, ingredient['name'], ingredient['ratio']))
            
            conn.commit()
            return formula_id
    
    def update_formula(self, owner_open_id: str, formula_id: int, 
                      formula_data: Dict) -> bool:
        """更新配方"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 更新配方
            cursor.execute("""
                UPDATE formulas
                SET name = ?, stage_type = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_open_id = ?
            """, (formula_data['name'], formula_data['stage_type'],
                  formula_data.get('notes'), formula_id, owner_open_id))
            
            if cursor.rowcount == 0:
                return False
            
            # 删除旧成分
            cursor.execute("""
                DELETE FROM formula_ingredients WHERE formula_id = ?
            """, (formula_id,))
            
            # 插入新成分
            for ingredient in formula_data['ingredients']:
                cursor.execute("""
                    INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
                    VALUES (?, ?, ?)
                """, (formula_id, ingredient['name'], ingredient['ratio']))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_formula(self, owner_open_id: str, formula_id: int) -> bool:
        """删除配方"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM formulas
                WHERE id = ? AND owner_open_id = ?
            """, (formula_id, owner_open_id))
            
            conn.commit()
            return cursor.rowcount > 0


class PriceRepository:
    """价格数据访问层"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
    
    def get_latest_price(self, owner_open_id: str, 
                        ingredient_code: str) -> Optional[Dict]:
        """获取最新价格"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ingredient_code, ingredient_name, price,
                       currency, unit, source, price_date
                FROM ingredient_prices
                WHERE owner_open_id = ? AND ingredient_code = ?
                ORDER BY price_date DESC
                LIMIT 1
            """, (owner_open_id, ingredient_code))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_prices_by_date(self, owner_open_id: str, 
                          price_date: str) -> List[Dict]:
        """获取指定日期的所有价格"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ingredient_code, ingredient_name, price,
                       currency, unit, source
                FROM ingredient_prices
                WHERE owner_open_id = ? AND price_date = ?
                ORDER BY ingredient_name
            """, (owner_open_id, price_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_price(self, owner_open_id: str, price_data: Dict) -> int:
        """保存价格"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ingredient_prices
                (owner_open_id, ingredient_code, ingredient_name, price,
                 currency, unit, source, price_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (owner_open_id, price_data['ingredient_code'],
                  price_data['ingredient_name'], price_data['price'],
                  price_data.get('currency', 'CNY'),
                  price_data.get('unit', 'ton'),
                  price_data.get('source', 'barchart'),
                  price_data['price_date']))
            
            conn.commit()
            return cursor.lastrowid
