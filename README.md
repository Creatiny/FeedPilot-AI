# FeedSales AI - AI-Powered Feed Formulation System

An AI-powered system for feed formulation and cost calculation, designed for the North American market.

## 🎯 Features

- **38 NRC Standard Formulas** - Swine, Cattle, Poultry, Sheep, Goat, Duck, Pet, Aquatic
- **21 Feed Ingredients** - Complete nutritional data from USDA
- **Daily Price Updates** - Auto-scrape CBOT futures and USDA prices
- **Cost Calculation** - Real-time feed cost calculation
- **Multi-Species Support** - 8 animal categories
- **USD Pricing** - All prices in USD/ton

## 📊 Data Coverage

### Formulas (38 total)
- **Swine**: 8 formulas (Nursery, Growing, Finishing, Sows)
- **Cattle**: 6 formulas (Beef, Dairy)
- **Poultry**: 9 formulas (Broiler, Layer, Turkey)
- **Sheep**: 5 formulas (Lamb, Ewe)
- **Goat**: 4 formulas (Kid, Doe)
- **Duck**: 3 formulas (Starter, Grower, Breeder)
- **Pet**: 2 formulas (Cat, Dog)
- **Aquatic**: 3 formulas (Trout, Catfish)

### Ingredients (21 types)
- Energy feeds (Corn, Wheat)
- Protein feeds (Soybean meal, Fish meal)
- Forages (Alfalfa hay, Corn silage)
- Minerals (Dicalcium phosphate, Limestone, Salt)
- Amino acids (Lysine, Methionine)
- Premixes (Swine, Beef, Dairy, Poultry)

### Prices (Daily Updated)
- **CBOT Futures**: Corn, Soybean meal, Soybeans, Wheat
- **USDA National**: 18 feed ingredients
- **Total**: 22 price records daily

## 🚀 Quick Start

### 1. Database Setup

```bash
cd /home/kenny/.openclaw/workspace/feed-sales-ai-mvp
python3 scripts/migrate_data_to_db.py
```

### 2. Update Prices

```bash
python3 scripts/update_prices.py
```

### 3. Test Formula Cost

```bash
python3 tests/test_formula_skill_db.py
```

## 📁 Project Structure

```
feed-sales-ai-mvp/
├── data/
│   ├── nrc_formulas_full.json    # 38 NRC formulas
│   ├── usda_ingredients.json     # 21 ingredients nutrition
│   ├── usd_prices.json          # Base prices
│   └── feed_sales.db            # SQLite database
├── scripts/
│   ├── migrate_data_to_db.py    # Data migration
│   ├── update_prices.py         # Price scraper
│   └── daily_price_update.sh    # Cron job script
├── tests/
│   └── test_formula_skill_db.py # Skill tests
├── skills/
│   └── formula_cost_skill/
│       └── skill.py             # Cost calculation skill
└── docs/
    ├── PRICE_UPDATE_SETUP.md    # Price update guide
    └── PROJECT_SUMMARY.md       # This file
```

## 🔧 Configuration

### Database

SQLite database located at `data/feed_sales.db`

Tables:
- `formulas` - Feed formulas
- `formula_ingredients` - Formula ingredients
- `ingredients` - Ingredient nutrition data
- `ingredient_prices` - Daily prices

### Price Sources

- **CBOT**: Chicago Board of Trade futures prices
- **USDA**: USDA National Agricultural Statistics Service

### Price Update Schedule

Daily at 8:00 AM via cron job:

```bash
0 8 * * * /home/kenny/.openclaw/workspace/feed-sales-ai-mvp/scripts/daily_price_update.sh
```

## 📈 Usage Examples

### Calculate Formula Cost

```python
from skills.formula_cost_skill.skill import FormulaCostSkill

skill = FormulaCostSkill("data/feed_sales.db")
result = await skill.execute("user_123", "Calculate Nursery Diet 1 cost")

if result['success']:
    print(f"Cost: ${result['data']['cost_per_ton']}/ton")
    print(f"Animal: {result['data']['animal_type']}")
    print(f"Stage: {result['data']['stage']}")
```

### Update Prices

```bash
python3 scripts/update_prices.py
```

### Query Database

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect("data/feed_sales.db")
cursor = conn.cursor()

# Get today's prices
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute("""
    SELECT ingredient_name, price, trend 
    FROM ingredient_prices 
    WHERE date = ?
    ORDER BY ingredient_name
""", (today,))

for row in cursor.fetchall():
    print(f"{row[0]}: ${row[1]:.2f}/ton ({row[2]})")

conn.close()
```

## 🧪 Testing

Run all tests:

```bash
python3 tests/test_formula_skill_db.py
```

Expected output:
```
Testing Formula Cost Skill with SQLite Database
============================================================
Test: Nursery formula
✅ Success - Cost: $285.8/ton
   Animal: Swine
   Stage: Nursery

Test: Broiler formula
✅ Success - Cost: $335.4/ton
   Animal: Broiler
   Stage: Starter

Test: Layer formula
✅ Success - Cost: $228.9/ton
   Animal: Layer
   Stage: Laying

Testing completed!
```

## 📊 Sample Costs

| Formula | Animal | Stage | Cost (USD/ton) |
|---------|--------|-------|----------------|
| Nursery Diet 1 | Swine | Nursery | $285.80 |
| Broiler Starter | Broiler | Starter | $335.40 |
| Layer Diet | Layer | Laying | $228.90 |
| Beef Cattle Starter | Beef Cattle | Starter | $245.60 |
| Lactating Cow Diet | Dairy Cattle | Lactating | $198.50 |

*Costs calculated using current market prices*

## 🔄 Maintenance

### Daily Tasks

- [ ] Price update runs automatically (8:00 AM)
- [ ] Check `logs/price_update.log` for errors

### Weekly Tasks

- [ ] Verify price data quality
- [ ] Check database size
- [ ] Review formula costs for anomalies

### Monthly Tasks

- [ ] Backup database
- [ ] Update formula data if needed
- [ ] Review and update ingredient list

## 📝 Data Sources

### Official Sources

- **NRC Standards**: https://nap.nationalacademies.org/
- **USDA Feed Composition**: https://fdc.nal.usda.gov/
- **CBOT Futures**: https://www.cmegroup.com/markets/agriculture.html
- **USDA Prices**: https://www.ams.usda.gov/mnreports

### Reference Standards

- NRC 2012 - Swine Nutrition
- NRC 2016 - Beef Cattle Nutrition
- NRC 2001 - Dairy Cattle Nutrition
- NRC 1994 - Poultry Nutrition
- NRC 2007 - Small Ruminant Nutrition
- NRC 2011 - Aquatic Animal Nutrition
- AAFCO 2026 - Pet Food Standards

## 🐛 Troubleshooting

### Database Issues

**Problem**: Database not found
```bash
python3 scripts/migrate_data_to_db.py
```

**Problem**: Old prices
```bash
python3 scripts/update_prices.py
```

### Price Update Issues

**Problem**: Cron job not running
```bash
# Check cron status
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog
```

**Problem**: Script fails
```bash
# Run manually with debug
bash -x scripts/daily_price_update.sh
```

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `PRICE_UPDATE_SETUP.md`
3. Run test script to verify installation

## 📄 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- **NRC** - National Research Council nutrition standards
- **USDA** - United States Department of Agriculture data
- **CBOT** - Chicago Board of Trade price data

---

**Last Updated**: 2026-03-28  
**Version**: 1.0  
**Data**: 38 formulas, 21 ingredients, 22 daily prices
