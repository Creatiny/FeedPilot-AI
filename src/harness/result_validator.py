"""
FeedSales AI - ResultValidator

结果校验器，对关键输出进行结构化校验
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool
    errors: List[str] = field(default_factory=list)


class ResultValidator:
    """
    结果校验器
    
    对关键输出进行结构化校验，在返回用户前拦截错误
    """
    
    def validate_cost_result(self, result: Dict) -> ValidationResult:
        """
        校验成本计算结果
        
        Args:
            result: 成本结果
            
        Returns:
            ValidationResult: 校验结果
        """
        errors = []
        
        # 1. 总成本必须为正数
        total_cost = result.get('total_cost', 0)
        if total_cost <= 0:
            errors.append(f"总成本必须大于 0，实际: {total_cost}")
        
        # 2. 明细和 = 总成本
        details = result.get('details', [])
        if details:
            detail_sum = sum(d.get('cost', 0) for d in details)
            if abs(detail_sum - total_cost) > 0.01:
                errors.append(f"明细和 ({detail_sum:.2f}) 不等于总成本 ({total_cost:.2f})")
        
        # 3. 所有成分必须有价格来源
        for detail in details:
            if 'price_source' not in detail:
                errors.append(f"{detail.get('name', '未知成分')} 缺少价格来源")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_formula(self, formula: Dict) -> ValidationResult:
        """
        校验配方
        
        Args:
            formula: 配方数据
            
        Returns:
            ValidationResult: 校验结果
        """
        errors = []
        
        # 1. 成分比例和应约等于 100%
        ingredients = formula.get('ingredients', [])
        if ingredients:
            total_ratio = sum(ing.get('ratio', 0) for ing in ingredients)
            if abs(total_ratio - 100.0) > 1.0:  # 允许 1% 误差
                errors.append(f"成分比例和 ({total_ratio:.1f}%) 不等于 100%")
        
        # 2. 检查重复成分
        names = [ing.get('name') for ing in ingredients if ing.get('name')]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            unique_duplicates = list(set(duplicates))
            errors.append(f"重复成分: {', '.join(unique_duplicates)}")
        
        # 3. 检查配方名称
        if not formula.get('name'):
            errors.append("配方名称不能为空")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_customer(self, customer: Dict) -> ValidationResult:
        """
        校验客户数据
        
        Args:
            customer: 客户数据
            
        Returns:
            ValidationResult: 校验结果
        """
        errors = []
        
        # 1. 名称必填
        if not customer.get('name'):
            errors.append("客户名称不能为空")
        
        # 2. 至少有一种联系方式
        has_contact = (
            customer.get('phone') or 
            customer.get('email') or
            customer.get('company')
        )
        if not has_contact and customer.get('name'):
            errors.append("至少需要填写一种联系方式（电话/邮箱/公司）")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_price(self, price_data: Dict) -> ValidationResult:
        """
        校验价格数据
        
        Args:
            price_data: 价格数据
            
        Returns:
            ValidationResult: 校验结果
        """
        errors = []
        
        # 1. 价格必须为正数
        price = price_data.get('price', 0)
        if price <= 0:
            errors.append(f"价格必须大于 0，实际: {price}")
        
        # 2. 原料名称不能为空
        if not price_data.get('ingredient_name'):
            errors.append("原料名称不能为空")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )