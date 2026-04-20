"""
FeedSales AI - 常量定义

集中管理所有常量，避免代码重复
"""

# ============================================
# 默认价格 (USD/ton)
# ============================================
DEFAULT_PRICES = {
    'Corn, grain': 180.00,
    'Soybean meal, 48%': 350.00,
    'Fish meal, 65%': 1800.00,
    'Wheat middlings': 200.00,
    'Limestone, ag': 120.00,
    'Premix, swine': 450.00,
    'Premix, beef': 450.00,
    'Premix, dairy': 450.00,
    'Premix, broiler': 450.00,
    'Premix, layer': 450.00,
    'Dicalcium phosphate': 650.00,
    'Salt, white': 150.00,
    'L-Lysine HCl': 1200.00,
    'DL-Methionine': 2500.00,
}

# 默认价格（无具体值时使用）
DEFAULT_PRICE_GENERIC = 300.00


# ============================================
# 原料名称映射 (中文 → 英文标准名)
# ============================================
INGREDIENT_NAME_MAP = {
    # 中文 → 英文
    '玉米': 'Corn, grain',
    '豆粕': 'Soybean meal, 48%',
    '鱼粉': 'Fish meal, 65%',
    '小麦': 'Wheat middlings',
    '石粉': 'Limestone, ag',
    '预混料': 'Premix, swine',
    '磷酸氢钙': 'Dicalcium phosphate',
    '盐': 'Salt, white',
    '赖氨酸': 'L-Lysine HCl',
    '蛋氨酸': 'DL-Methionine',
    
    # 英文变体 → 标准名
    'corn': 'Corn, grain',
    'corn, grain': 'Corn, grain',
    'soybean': 'Soybean meal, 48%',
    'soybean meal': 'Soybean meal, 48%',
    'fish meal': 'Fish meal, 65%',
    'wheat': 'Wheat middlings',
    'limestone': 'Limestone, ag',
    'premix': 'Premix, swine',
    'dicalcium': 'Dicalcium phosphate',
    'salt': 'Salt, white',
    'lysine': 'L-Lysine HCl',
    'methionine': 'DL-Methionine',
}


def get_standard_ingredient_name(name: str) -> str:
    """
    获取标准原料名称
    
    Args:
        name: 原料名称（中文或英文）
        
    Returns:
        str: 标准英文名称
    """
    name_lower = name.lower()
    return INGREDIENT_NAME_MAP.get(name_lower, INGREDIENT_NAME_MAP.get(name, name))


def get_default_price(ingredient_name: str) -> float:
    """
    获取默认价格
    
    Args:
        ingredient_name: 原料名称
        
    Returns:
        float: 默认价格 (USD/ton)
    """
    # 先尝试直接匹配
    if ingredient_name in DEFAULT_PRICES:
        return DEFAULT_PRICES[ingredient_name]
    
    # 再尝试模糊匹配
    for key, price in DEFAULT_PRICES.items():
        if key.lower() in ingredient_name.lower():
            return price
    
    return DEFAULT_PRICE_GENERIC


def generate_ingredient_code(ingredient_name: str) -> str:
    """
    生成原料代码
    
    Args:
        ingredient_name: 原料名称
        
    Returns:
        str: 原料代码 (如 ING_CORN)
    """
    # 优先使用预定义映射
    code_map = {
        'Corn, grain': 'ING_CORN',
        'Soybean meal, 48%': 'ING_SBM',
        'Fish meal, 65%': 'ING_FISHM',
        'Wheat middlings': 'ING_WHEAT',
        'Limestone, ag': 'ING_LIME',
        'Premix, swine': 'ING_PREMIX',
        'Dicalcium phosphate': 'ING_DCP',
        'Salt, white': 'ING_SALT',
        'L-Lysine HCl': 'ING_LYS',
        'DL-Methionine': 'ING_MET',
    }
    
    for key, code in code_map.items():
        if key.lower() in ingredient_name.lower():
            return code
    
    # 默认：取第一个单词
    return 'ING_' + ingredient_name.split(',')[0].upper().replace(' ', '_')[:15]