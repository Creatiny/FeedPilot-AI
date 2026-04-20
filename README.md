# FeedPilot AI

**Intelligent Feed Formula Cost Calculation System**

FeedPilot AI is an AI-powered assistant for feed manufacturers and livestock producers. It provides real-time formula cost calculations, nutrition analysis, and price tracking for feed ingredients.

## Features

- **Formula Cost Calculation** - Calculate feed formula costs with current ingredient prices
- **Nutrition Analysis** - Analyze formula nutrition against NRC standards
- **Price Tracking** - Daily updates from CBOT futures and USDA national prices
- **Customer Management** - Track customer records and interactions
- **Quote Generation** - Generate professional quotes with profit margins
- **Price Alerts** - Set alerts for ingredient price thresholds

## Supported Species

| Species | Formulas |
|---------|----------|
| Swine | 8 formulas (Nursery, Grower, Finishing) |
| Cattle | 6 formulas (Beef, Dairy) |
| Poultry | 9 formulas (Broiler, Layer) |
| Sheep | 5 formulas |
| Goat | 4 formulas |
| Duck | 3 formulas |
| Pet | 2 formulas |
| Aquatic | 3 formulas |

## Quick Start

### Prerequisites

- Python 3.11+
- SQLite3

### Installation

```bash
# Clone repository
git clone https://github.com/kenny-chenym/FeedPilot-AI.git
cd FeedPilot-AI

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Update prices
python scripts/update_prices.py
```

### Usage

```bash
# Query ingredient price
python scripts/run_skill.py price "corn price"

# Calculate formula cost
python scripts/run_skill.py cost "Nursery Diet 1 cost"

# Analyze nutrition
python scripts/run_skill.py nutrition "analyze Nursery Diet 1"

# Manage customers
python scripts/run_skill.py customer "show customers"
```

## Project Structure

```
FeedPilot-AI/
├── skills/              # AI skill modules
│   ├── price_lookup_skill/
│   ├── formula_cost_skill/
│   ├── nutrition_analysis_skill/
│   ├── customer_record_skill/
│   ├── reminder_skill/
│   └── quote_skill/
├── src/                 # Core source code
├── scripts/             # Utility scripts
├── data/                # SQLite database
├── docs/                # Documentation
├── SOUL.md              # AI personality config
└── AGENTS.md            # Agent instructions
```

## Data Sources

- **CBOT Futures** - Chicago Board of Trade commodity prices
- **USDA National** - USDA weekly ingredient prices
- **NRC Standards** - National Research Council nutrition requirements

## License

MIT License

## Author

Kenny Chen

---

**FeedPilot AI** - Making feed formulation smarter.
