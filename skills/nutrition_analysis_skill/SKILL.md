---
name: nutrition_analysis_skill
description: Nutrition analysis for feed formulas. Triggers when user asks to analyze formula nutrition, compare to NRC standards. Examples: "analyze Nursery Diet 1 nutrition", "compare to NRC standard"
---

# Nutrition Analysis Skill

## ⚠️ Important Rules

- ❌ **NEVER** give users commands to run themselves
- ✅ **ALWAYS reply in English**
- ✅ **Call the unified skill runner via exec tool**

## When to Use

- "analyze Nursery Diet 1 nutrition"
- "compare Beef Cattle Starter to NRC"
- "check if formula meets nutritional requirements"
- "营养分析" (Chinese input → English output)

## How to Execute

Use exec tool to call the unified skill runner:

```bash
python3 {baseDir}/../../scripts/run_skill.py nutrition "<user message>"
```

Example for "analyze Beef Cattle Starter nutrition":
```bash
python3 {baseDir}/../../scripts/run_skill.py nutrition "analyze Beef Cattle Starter nutrition"
```

## Workflow

1. Extract formula name from user message
2. Call: `python3 {baseDir}/../../scripts/run_skill.py nutrition "analyze <formula_name> nutrition"`
3. Parse JSON output and format in English

## Output Format (English)

```
Formula: Beef Cattle Starter
Animal: Beef Cattle | Stage: Starter

Nutrition Analysis:
| Nutrient  | Actual | NRC Standard | Status    |
|-----------|--------|--------------|-----------|
| Protein   | 17.28% | 16.0%        | ✓ Meets   |
| Calcium   | 2.00%  | 0.6%         | ✓ Meets   |
| Phosphorus| 1.14%  | 0.4%         | ✓ Meets   |
| Lysine    | 0.99%  | 0.8%         | ✓ Meets   |

Ingredients: 7 components
```

## NRC Standards Reference

- **Swine Nursery**: Protein 18%, Calcium 0.70%, Phosphorus 0.55%, Lysine 1.2%
- **Swine Growing**: Protein 16%, Calcium 0.60%, Phosphorus 0.50%, Lysine 0.9%
- **Broiler Starter**: Protein 22%, Calcium 1.00%, Phosphorus 0.45%, Lysine 1.3%
- **Beef Cattle Starter**: Protein 16%, Calcium 0.60%, Phosphorus 0.40%, Lysine 0.8%

## Error Handling

- Formula not found: List available formulas
- Incomplete data: Show partial analysis with warning
- Script error: Apologize and suggest retry