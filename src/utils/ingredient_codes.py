"""
FeedSales AI - ingredient_codes.py

原料名称 → 原料代码 映射表及转换函数。
所有 ingredient_name 到 ingredient_code 的转换必须经过此模块，
确保映射逻辑单一来源，避免多处副本导致不一致。
"""

from typing import Dict


# 原料名称 → 原料代码 映射表（按北美饲料行业标准）
INGREDIENT_CODE_MAP: Dict[str, str] = {
    # 谷物 / Grains
    'Corn': 'ING_CORN',
    'Corn, #2 Yellow': 'ING_CORN',
    'Corn, grain': 'ING_CORN',
    'Wheat': 'ING_WHEAT',
    'Barley': 'ING_BARLEY',
    'Rice': 'ING_RICE',
    'Sorghum': 'ING_SORGHUM',
    'Oats': 'ING_OATS',

    # 蛋白源 / Protein sources
    'Soybean meal': 'ING_SBM',
    'Soybean meal, 48%': 'ING_SBM',
    'Soybean': 'ING_SBM',
    'Canola meal': 'ING_CANOLA',
    'Cottonseed meal': 'ING_COTTON',
    'Fish meal': 'ING_FISHM',
    'Fish meal, 60%': 'ING_FISHM',
    'DDGS': 'ING_DDGS',
    'Distiller\'s grains': 'ING_DDGS',
    'Meat meal': 'ING_MEATMEAL',
    'Meat and bone meal': 'ING_MBM',

    # 矿物 / Minerals
    'Limestone': 'ING_LIME',
    'Dicalcium phosphate': 'ING_DCP',
    'Dicalcium': 'ING_DCP',
    'Monocalcium phosphate': 'ING_MCP',
    'Calcium carbonate': 'ING_LIME',

    # 添加剂 / Additives
    'Salt': 'ING_SALT',
    'L-Lysine': 'ING_LYS',
    'Lysine': 'ING_LYS',
    'DL-Methionine': 'ING_MET',
    'Methionine': 'ING_MET',
    'Threonine': 'ING_THR',
    'Tryptophan': 'ING_TRP',
    'Premix': 'ING_PREMIX',
    'Vitamin premix': 'ING_PREMIX',
    'Trace mineral premix': 'ING_PREMIX',

    # 纤维 / Fiber
    'Alfalfa': 'ING_ALFALFA',
    'Alfalfa meal': 'ING_ALFALFA',
    'Corn silage': 'ING_SILAGE',
    'Grass hay': 'ING_HAY',
    'Hay': 'ING_HAY',
    'Wheat straw': 'ING_STRAW',

    # 其他 / Others
    'Molasses': 'ING_MOLASSES',
    'Fat': 'ING_FAT',
    'Animal fat': 'ING_FAT',
    'Vegetable oil': 'ING_OIL',
    'Oil': 'ING_OIL',

    # 非标准原料（蜜蜂配方等）
    'Water': 'ING_WATER',
    'Vinegar (acidifier)': 'ING_VINEGAR',
    'Sugar': 'ING_SUGAR',
    'Honey': 'ING_HONEY',
}


def generate_ingredient_code(ingredient_name: str) -> str:
    """
    将原料名称转换为 ingredient_code。

    查找逻辑：
    1. 遍历映射表，找到第一个 key（不区分大小写）匹配则返回对应 code
    2. 无法匹配时，提取名称中第一个逗号前的部分，
       大写并用下划线连接作为 fallback code（如 "Corn, grain" → "Corn" → "ING_CORN"）

    Args:
        ingredient_name: 原料名称（人类可读）

    Returns:
        原料代码（跨数据源唯一标识）

    Example:
        >>> generate_ingredient_code("Corn, grain")
        'ING_CORN'
        >>> generate_ingredient_code("Soybean meal, 48%")
        'ING_SBM'
        >>> generate_ingredient_code("Unknown ingredient")
        'ING_UNKNOWN_INGREDIENT'
    """
    if not ingredient_name:
        return 'ING_UNKNOWN'

    name_lower = ingredient_name.lower()

    # Longest-key-first matching avoids short-key shadowing
    # (e.g. "Corn" matching before "Corn, #2 Yellow").
    for key, code in sorted(
        INGREDIENT_CODE_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):
        if key.lower() in name_lower:
            return code

    # Fallback：取逗号前第一个单词作为 code
    first_word = ingredient_name.split(',')[0].strip()
    fallback = 'ING_' + first_word.upper().replace(' ', '_')[:15]
    return fallback


def get_all_codes() -> Dict[str, str]:
    """返回完整的原料代码映射表（只读）"""
    return INGREDIENT_CODE_MAP.copy()
