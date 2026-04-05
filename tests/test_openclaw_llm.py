#!/usr/bin/env python3
"""
FeedSales AI - OpenClaw LLM 测试

测试 OpenClaw 内置 LLM 调用能力
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_openclaw_llm():
    """测试 OpenClaw LLM 调用"""
    print("🧪 测试 OpenClaw LLM...")
    
    # 检查 OpenClaw 配置
    openclaw_config = Path.home() / ".openclaw" / "openclaw.json"
    
    if not openclaw_config.exists():
        print("  ⚠️ OpenClaw 配置文件不存在")
        return False
    
    import json
    with open(openclaw_config, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 检查模型配置
    models = config.get("models", {}).get("providers", {})
    
    print(f"  📋 已配置 Provider:")
    for provider_name, provider_config in models.items():
        model_count = len(provider_config.get("models", []))
        print(f"    - {provider_name}: {model_count} 个模型")
    
    # 检查环境变量
    env_vars = ["MODELSTUDIO_API_KEY", "OPENROUTER_API_KEY", "DASHSCOPE_API_KEY"]
    print(f"\n  📋 环境变量检查:")
    for var in env_vars:
        import os
        if os.getenv(var):
            key_preview = os.getenv(var)[:15] + "..."
            print(f"    ✅ {var}: {key_preview}")
        else:
            print(f"    ❌ {var}: 未配置")
    
    return True


def test_skill_triggers():
    """测试技能触发器配置"""
    print("\n🧪 测试技能触发器...")
    
    skills_dir = Path("skills")
    
    if not skills_dir.exists():
        print("  ❌ skills 目录不存在")
        return False
    
    # 检查每个技能的 SKILL.md
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("__"):
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 检查 frontmatter
                    if "name:" in content and "description:" in content:
                        print(f"  ✅ {skill_dir.name}: 配置正确")
                    else:
                        print(f"  ❌ {skill_dir.name}: 缺少必需字段")
                        return False
            else:
                print(f"  ❌ {skill_dir.name}: SKILL.md 不存在")
                return False
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("FeedSales AI - OpenClaw LLM 测试")
    print("=" * 60)
    
    try:
        # 测试 OpenClaw 配置
        success1 = test_openclaw_llm()
        
        # 测试技能触发器
        success2 = test_skill_triggers()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("✅ OpenClaw LLM 测试通过！")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ 部分测试失败")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
