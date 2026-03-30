# FeedSales AI User Guide

**Version 1.7.0** | Complete English Documentation

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Features](#2-features)
3. [Quick Commands](#3-quick-commands)
4. [Natural Language Commands](#4-natural-language-commands)
5. [FAQ](#5-faq)
6. [Data Management](#6-data-management)
7. [Advanced Features](#7-advanced-features)
8. [Support](#8-support)
9. [Version History](#9-version-history)

---

## 1. Getting Started

### What is FeedSales AI?

FeedSales AI is an intelligent feed formulation assistant designed for livestock and poultry nutrition professionals. It provides instant formula cost calculations, real-time commodity pricing, customer record management, and nutrition analysis against NRC (National Research Council) standards.

### How to Access

**Step 1: Find the Bot on Telegram**

1. Open Telegram on your mobile device or desktop
2. Search for `@feedflow_ai_bot` in the search bar
3. Tap on the bot profile to open the chat

**Step 2: Start the Conversation**

Send the `/start` command to activate the bot:

```
/start
```

The bot will respond with a welcome message and display available features.

**Step 3: Explore Features**

After starting, you can:
- Calculate formula costs instantly
- Check current commodity prices
- Manage your customer records
- Analyze nutrition profiles vs NRC standards

### Supported Species

FeedSales AI supports formula calculations for **9 species**:

| Species | Description |
|---------|-------------|
| Swine | Nursery, Grower, Finisher diets |
| Beef Cattle | Growing and finishing cattle |
| Dairy Cattle | Lactating and dry cows |
| Broiler | Starter, Grower, Finisher phases |
| Layer | Egg production hens |
| Turkey | Starter, Grower, Finisher phases |
| Sheep | Breeding and market lambs |
| Goat | Dairy and meat goats |
| Duck | Starter and finisher diets |

### Standard Formulas

The system includes **38 NRC-standard formulas** including:

- **Swine**: Nursery Diet 1, Nursery Diet 2, Grower Diet 1, Grower Diet 2, Finisher Diet 1, Finisher Diet 2, Gestation Diet, Lactation Diet
- **Beef Cattle**: Growing Calf, Finishing Steer, Breeding Bull
- **Dairy Cattle**: Lactating Cow High Production, Lactating Cow Medium Production, Dry Cow, Heifer Development
- **Broiler**: Broiler Starter, Broiler Grower, Broiler Finisher
- **Layer**: Layer Starter, Layer Developer, Layer Production
- **Turkey**: Turkey Starter, Turkey Grower, Turkey Finisher
- **Sheep**: Lamb Starter, Lamb Grower, Breeding Ewe
- **Goat**: Kid Starter, Dairy Goat Lactating, Meat Goat Finisher
- **Duck**: Duck Starter, Duck Finisher

---

## 2. Features

### 2.1 Formula Cost Calculator

**Description**: Calculate the total cost of feed formulas instantly using current commodity prices.

**How it works**:
1. Select a standard formula or specify custom ingredients
2. The system retrieves real-time prices
3. Calculate cost per ton or per unit

**Example Conversation**:

```
User: What's the cost of Nursery Diet 1 for swine?

Bot: 📊 Formula Cost Analysis - Nursery Diet 1 (Swine)

┌─────────────────────────────────────────┐
│ Ingredient       │ %     │ Price  │ Cost │
├─────────────────────────────────────────┤
│ Corn             │ 55.0  │ $180/ton │ $99.00 │
│ Soybean Meal     │ 22.0  │ $350/ton │ $77.00 │
│ Wheat            │ 10.0  │ $165/ton │ $16.50 │
│ DDGS             │ 8.0   │ $145/ton │ $11.60 │
│ Limestone        │ 1.5   │ $50/ton  │ $0.75 │
│ Salt             │ 0.5   │ $80/ton  │ $0.40 │
│ Premix           │ 3.0   │ $2,000/ton │ $60.00 │
├─────────────────────────────────────────┤
│ TOTAL            │ 100%  │         │ $265.25/ton │
└─────────────────────────────────────────┘

💰 Cost per ton: $265.25 USD
💡 Recommendation: Corn price trending up. Consider wheat substitution.
```

---

### 2.2 Price Lookup

**Description**: Query real-time prices for feed commodities.

**Available Commodities** (20+ items):

| Category | Commodities |
|----------|-------------|
| Grains | Corn, Wheat, Barley, Oats, Sorghum, Rice |
| Protein Meals | Soybean Meal, Canola Meal, Cottonseed Meal, Sunflower Meal, Peanut Meal |
| By-products | DDGS, Wheat Midds, Rice Bran, Corn Gluten Meal |
| Fats/Oils | Soybean Oil, Palm Oil, Fish Oil, Lard |
| Minerals | Limestone, Dicalcium Phosphate, Salt, Magnesium Oxide |
| Additives | Premix, Vitamins, Amino Acids (Lysine, Methionine, Threonine) |

**Example Conversation**:

```
User: What's the current price of corn and soybean meal?

Bot: 📈 Commodity Price Report

┌────────────────────────────────────┐
│ Commodity        │ Price    │ Trend │
├────────────────────────────────────┤
│ Corn             │ $180/ton │ ↑ +5% │
│ Soybean Meal     │ $350/ton │ ↓ -2% │
│ Wheat            │ $165/ton │ → 0%  │
│ DDGS             │ $145/ton │ ↑ +3% │
└────────────────────────────────────┘

📍 Market: US Midwest
📅 Updated: March 31, 2026

💡 Price Alerts:
   - Corn above $175 threshold
   - Soybean Meal approaching target price $340
```

```
User: Price of lysine?

Bot: 💰 Lysine (L-Lysine HCl 98%)

Current Price: $1.85/kg USD
Market: Global
Trend: ↓ -8% (down from $2.00/kg last month)

📦 Supply Status: Stable
💡 Recommendation: Good time to stock up before seasonal demand increase.
```

---

### 2.3 Customer Records

**Description**: Manage customer information with secure multi-tenant isolation. Each user's data is private and isolated.

**Features**:
- Add new customers
- View customer list
- Update customer information
- Delete customers
- Export customer data

**Example Conversation**:

```
User: Add a new customer

Bot: 📝 Add New Customer

Please provide:
1. Customer name
2. Contact person
3. Phone number
4. Email
5. Address (optional)
6. Species interest (optional)

Type the details in any format, or use:
/customer add [name] [contact] [phone]

User: Add Smith Farm, John Smith, +1-555-0100, john@smithfarm.com, interested in swine formulas

Bot: ✅ Customer Added Successfully!

┌──────────────────────────────────┐
│ Customer: Smith Farm             │
│ Contact: John Smith              │
│ Phone: +1-555-0100               │
│ Email: john@smithfarm.com        │
│ Species: Swine                   │
│ Created: March 31, 2026          │
└──────────────────────────────────┘

💡 You can now track purchases and send formula recommendations to this customer.
```

```
User: Show all my customers

Bot: 📋 Customer List (Your Private Records)

┌────┬────────────────┬─────────────┬────────────┐
│ #  │ Name           │ Contact     │ Species    │
├────┼────────────────┼─────────────┼────────────┤
│ 1  │ Smith Farm     │ John Smith  │ Swine      │
│ 2  │ Johnson Ranch  │ Mike Johnson│ Beef       │
│ 3  │ Poultry Plus   │ Sarah Lee   │ Broiler    │
│ 4  │ Dairy Dreams   │ Tom Brown   │ Dairy      │
│ 5  │ Goat Grove     │ Emma White  │ Goat       │
└────┴────────────────┴─────────────┴────────────┘

📊 Total: 5 customers
🔒 Data is private to your account

Type /customer [number] for details, or /customer export to download.
```

---

### 2.4 Nutrition Analysis

**Description**: Analyze formula nutrition profiles and compare against NRC standards for each species.

**Analysis includes**:
- Energy (ME, NE)
- Protein and amino acids
- Minerals (Ca, P, Na, Cl, Mg, K)
- Vitamins
- Comparison to NRC requirements

**Example Conversation**:

```
User: Analyze Broiler Starter formula nutrition

Bot: 🧬 Nutrition Analysis - Broiler Starter

┌───────────────────────────────────────────┐
│ Nutrient          │ Formula │ NRC Req │ %   │
├───────────────────────────────────────────┤
│ Energy (ME)       │ 3,050   │ 3,000   │ 102%│
│ Crude Protein     │ 22.0%   │ 21.5%   │ 102%│
│ Lysine            │ 1.20%   │ 1.10%   │ 109%│
│ Methionine        │ 0.50%   │ 0.45%   │ 111%│
│ Calcium           │ 1.00%   │ 0.90%   │ 111%│
│ Phosphorus (Avail)│ 0.45%   │ 0.40%   │ 113%│
│ Sodium            │ 0.18%   │ 0.15%   │ 120%│
│ Chloride          │ 0.20%   │ 0.15%   │ 133%│
├───────────────────────────────────────────┤
│ Status: ✅ MEETS NRC STANDARDS             │
│ Grade: A - Optimal                        │
└───────────────────────────────────────────┘

⚠️ Alerts:
- Chloride slightly high (133%). Consider reducing salt.
- All amino acids balanced well.

💡 Recommendation: Formula is well-balanced for broiler starter phase (0-14 days).
```

```
User: Check Finisher Diet 1 for swine against NRC

Bot: 🧬 Nutrition Analysis - Finisher Diet 1 (Swine)

┌───────────────────────────────────────────┐
│ Nutrient          │ Formula │ NRC Req │ %   │
├───────────────────────────────────────────┤
│ Energy (NE)       │ 2,600   │ 2,550   │ 102%│
│ Crude Protein     │ 14.5%   │ 13.5%   │ 107%│
│ Lysine            │ 0.75%   │ 0.70%   │ 107%│
│ Methionine        │ 0.22%   │ 0.20%   │ 110%│
│ Threonine         │ 0.48%   │ 0.45%   │ 107%│
│ Calcium           │ 0.60%   │ 0.55%   │ 109%│
│ Phosphorus (STTD) │ 0.35%   │ 0.32%   │ 109%│
├───────────────────────────────────────────┤
│ Status: ✅ MEETS NRC STANDARDS             │
│ Grade: A - Optimal                        │
└───────────────────────────────────────────┘

✅ All nutrients within optimal range for finishing pigs (100-130 kg).

💡 Cost optimization suggestion:
   - Protein could be reduced to 13.8% while maintaining NRC compliance
   - Potential savings: $8-12/ton
```

---

## 3. Quick Commands

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot and show welcome message | `/start` |
| `/help` | Display help menu and all commands | `/help` |
| `/cost` | Calculate formula cost | `/cost Nursery Diet 1` |
| `/price` | Query commodity price | `/price corn` |
| `/customer` | Manage customer records | `/customer list` |
| `/nutrition` | Analyze formula nutrition | `/nutrition Broiler Starter` |

---

### `/start` - Initialize Bot

```
/start
```

**Response**:
```
👋 Welcome to FeedSales AI!

Your intelligent feed formulation assistant.

📊 Features:
• Formula Cost Calculator - Instant cost estimates
• Price Lookup - Real-time commodity prices  
• Customer Records - Manage your contacts
• Nutrition Analysis - NRC standard comparisons

🚀 Quick Start:
• Type a formula name to calculate cost
• Type an ingredient to check price
• Use /help for all commands

🔒 Your data is private and secure.

Ready to help! What would you like to do?
```

---

### `/help` - Help Menu

```
/help
```

**Response**:
```
📖 FeedSales AI Help Guide

QUICK COMMANDS:
├─ /start - Initialize bot
├─ /help - Show this help
├─ /cost [formula] - Calculate formula cost
├─ /price [commodity] - Check commodity price
├─ /customer [action] - Manage customers
└─ /nutrition [formula] - Nutrition analysis

NATURAL LANGUAGE:
Just type your question naturally!
• "What's corn price?"
• "Calculate Nursery Diet 1 cost"
• "Add customer ABC Farm"
• "Analyze Broiler Starter nutrition"

SPECIES SUPPORTED:
Swine, Beef Cattle, Dairy Cattle, Broiler, 
Layer, Turkey, Sheep, Goat, Duck

FORMULAS: 38 NRC standards
COMMODITIES: 20+ feed ingredients

📍 Need more help? Type "support"
```

---

### `/cost` - Formula Cost Calculator

**Usage**:
```
/cost [formula name]
/cost [formula name] [species]
```

**Examples**:
```
/cost Nursery Diet 1
/cost Finisher Diet 1 swine
/cost Broiler Starter
/cost Layer Production
```

---

### `/price` - Price Lookup

**Usage**:
```
/price [commodity name]
/price [commodity 1] [commodity 2] ...
```

**Examples**:
```
/price corn
/price soybean meal wheat
/price lysine methionine
/price all grains
```

---

### `/customer` - Customer Management

**Subcommands**:

| Subcommand | Description |
|------------|-------------|
| `/customer list` | Show all customers |
| `/customer add [details]` | Add new customer |
| `/customer [number]` | View customer details |
| `/customer update [number] [field] [value]` | Update customer |
| `/customer delete [number]` | Delete customer |
| `/customer export` | Export to CSV |

**Examples**:
```
/customer list
/customer add Smith Farm John Smith +1-555-0100
/customer 1
/customer update 1 phone +1-555-0200
/customer delete 3
/customer export
```

---

### `/nutrition` - Nutrition Analysis

**Usage**:
```
/nutrition [formula name]
/nutrition [formula name] [species]
```

**Examples**:
```
/nutrition Nursery Diet 1
/nutrition Broiler Starter
/nutrition Lactating Cow dairy
/nutrition Lamb Grower sheep
```

---

## 4. Natural Language Commands

FeedSales AI understands natural language. You don't need to use exact commands—just ask naturally!

### Formula Cost Queries

```
"What's the cost of Nursery Diet 1?"
"How much is Finisher Diet 2 per ton?"
"Calculate cost for Broiler Grower"
"What does Layer Production formula cost?"
"Show me the cost breakdown for Gestation Diet"
```

### Price Queries

```
"What's the price of corn?"
"How much is soybean meal right now?"
"Check wheat and DDGS prices"
"Current lysine price"
"Show me grain prices"
"What are protein meal prices today?"
```

### Customer Management

```
"Add a customer named Johnson Ranch"
"Show my customers"
"List all customer records"
"I need to update Smith Farm's phone number"
"Delete customer number 2"
"Export my customer data"
```

### Nutrition Analysis

```
"Analyze Broiler Starter nutrition"
"Check if Nursery Diet 1 meets NRC standards"
"What's the nutrition profile of Finisher Diet?"
"Compare Grower Diet 2 to NRC requirements"
"Show nutrition analysis for Lactating Cow formula"
```

### Combined Queries

```
"Compare Nursery Diet 1 and Nursery Diet 2 costs"
"What's cheaper: wheat or corn right now?"
"Show cost and nutrition for Broiler Starter"
"Find customers interested in swine formulas"
"List formulas for dairy cattle"
```

---

## 5. FAQ

### Q1: Is my customer data private?

**Answer**: Yes! FeedSales AI uses multi-tenant isolation. Your customer records are completely private to your account. No other user can see your data. Each account operates in its own secure data space.

---

### Q2: How often are prices updated?

**Answer**: Commodity prices are updated daily based on market data from major trading hubs. You can see the last update date in each price report. For real-time quotes, contact your supplier directly—our prices are market averages.

---

### Q3: Can I create custom formulas?

**Answer**: Currently, FeedSales AI supports 38 NRC-standard formulas. Custom formula creation is planned for v2.0. For now, you can modify standard formulas by adjusting ingredient percentages in your calculations.

---

### Q4: Which species are supported?

**Answer**: We support 9 species: **Swine, Beef Cattle, Dairy Cattle, Broiler (chicken), Layer (egg-producing hens), Turkey, Sheep, Goat, and Duck**. Each species has multiple phase-specific formulas (starter, grower, finisher, etc.).

---

### Q5: How do I export my data?

**Answer**: Use `/customer export` to download your customer records as a CSV file. For formula costs and nutrition reports, you can request "export" after any analysis to receive a formatted report.

---

## 6. Data Management

### Viewing Your Data

**Customer Records**:
```
/customer list
```
Shows all your customers with key details in a table format.

**Formula History**:
```
/history
```
Shows your recent formula calculations and cost analyses.

**Saved Prices**:
```
/prices saved
```
Shows any price thresholds or alerts you've configured.

---

### Exporting Data

**Customer Export**:
```
/customer export
```
Downloads a CSV file with all customer information.

**Formula Report Export**:
After any cost calculation, type:
```
export this report
```
To receive a formatted PDF/Excel report.

**Full Data Export**:
```
/export all
```
Downloads complete archive of all your records.

---

### Deleting Data

**Delete Single Customer**:
```
/customer delete [number]
```

**Delete All Customers**:
```
/customer delete all
```
⚠️ Requires confirmation: Type "confirm delete all"

**Delete Formula History**:
```
/history clear
```

**Complete Data Reset**:
```
/reset
```
⚠️ Warning: This permanently deletes ALL your data. Requires double confirmation.

---

### Data Privacy

- All data is encrypted and stored securely
- Multi-tenant isolation ensures your data is never shared
- You can request data deletion at any time
- Exported files are delivered directly to your Telegram

---

## 7. Advanced Features

### 7.1 Batch Calculation

Calculate costs for multiple formulas at once.

**Example**:
```
User: Calculate costs for all swine formulas

Bot: 📊 Batch Cost Analysis - Swine Formulas

┌─────────────────────────────────────────────┐
│ Formula             │ Cost/ton │ Rank │
├─────────────────────────────────────────────┤
│ Nursery Diet 1      │ $265.25  │ 3    │
│ Nursery Diet 2      │ $278.50  │ 5    │
│ Grower Diet 1       │ $225.00  │ 1    │
│ Grower Diet 2       │ $235.75  │ 2    │
│ Finisher Diet 1     │ $198.50  │ ★ Lowest │
│ Finisher Diet 2     │ $205.25  │ 4    │
│ Gestation Diet      │ $240.00  │ —    │
│ Lactation Diet      │ $310.00  │ Highest │
├─────────────────────────────────────────────┤
│ Average Cost: $245.16/ton                   │
│ Range: $198.50 - $310.00                    │
└─────────────────────────────────────────────┘

💡 Most economical: Finisher Diet 1 ($198.50/ton)
⚠️ Highest cost: Lactation Diet ($310/ton)
```

---

### 7.2 Price Alerts

Set alerts for commodity price thresholds.

**Setting Alerts**:
```
User: Alert me when corn goes above $200/ton

Bot: ✅ Price Alert Set

┌──────────────────────────────────┐
│ Commodity: Corn                  │
│ Threshold: $200/ton              │
│ Current: $180/ton                │
│ Condition: Above threshold       │
│ Status: Monitoring               │
└──────────────────────────────────┘

You'll receive a notification when corn price exceeds $200/ton.
```

```
User: Alert when soybean meal drops below $320

Bot: ✅ Price Alert Set

┌──────────────────────────────────┐
│ Commodity: Soybean Meal          │
│ Threshold: $320/ton              │
│ Current: $350/ton                │
│ Condition: Below threshold       │
│ Status: Monitoring               │
└──────────────────────────────────┘

Notification will be sent when price drops below $320/ton.
```

**Managing Alerts**:
```
/alerts list - Show all active alerts
/alerts delete [number] - Remove an alert
/alerts pause - Pause all alerts
/alerts resume - Resume all alerts
```

---

### 7.3 Cost Trends

Track historical cost changes for formulas.

**Example**:
```
User: Show cost trend for Nursery Diet 1 over past month

Bot: 📈 Cost Trend - Nursery Diet 1 (30 days)

┌──────────────────────────────────────┐
│ Date       │ Cost/ton │ Change │
├──────────────────────────────────────┤
│ Mar 01     │ $260.00  │ —      │
│ Mar 08     │ $263.50  │ ↑ +1.3%│
│ Mar 15     │ $258.75  │ ↓ -1.8%│
│ Mar 22     │ $265.25  │ ↑ +2.5%│
│ Mar 31     │ $265.25  │ → 0%   │
├──────────────────────────────────────┤
│ 30-day Avg: $262.75                  │
│ Trend: ↑ Upward (+2.0%)              │
└──────────────────────────────────────┘

💡 Insight:
   - Corn price increase (+$5/ton) driving cost up
   - Soybean meal stable
   - Recommendation: Lock in current prices before further increase
```

---

### 7.4 Formula Comparison

Compare two formulas side-by-side.

**Example**:
```
User: Compare Nursery Diet 1 and Nursery Diet 2

Bot: 📊 Formula Comparison

┌─────────────────────────────────────────────┐
│                   │ Nursery 1 │ Nursery 2 │
├─────────────────────────────────────────────┤
│ Cost/ton          │ $265.25   │ $278.50   │
│ Energy (ME)       │ 3,400     │ 3,450     │
│ Protein           │ 20.0%     │ 21.5%     │
│ Lysine            │ 1.15%     │ 1.25%     │
│ Calcium           │ 0.85%     │ 0.90%     │
├─────────────────────────────────────────────┤
│ Cost Difference   │ —         │ +$13.25   │
│ Protein Difference│ —         │ +1.5%     │
└─────────────────────────────────────────────┤

💡 Analysis:
   - Nursery 2 has higher protein (+1.5%) but costs $13.25 more
   - For healthy piglets, Nursery 1 may be sufficient
   - Nursery 2 recommended for faster growth targets
```

---

### 7.5 Species-Specific Recommendations

Get formula recommendations for specific species.

**Example**:
```
User: Recommend best formula for finishing pigs weighing 110kg

Bot: 🎯 Formula Recommendation - Swine Finishing (110kg)

Based on your criteria:
• Phase: Finishing (100-130kg)
• Goal: Standard growth rate

┌──────────────────────────────────────┐
│ Recommended: Finisher Diet 1         │
├──────────────────────────────────────┤
│ Cost: $198.50/ton                    │
│ Energy (NE): 2,600 kcal/kg           │
│ Protein: 14.5%                       │
│ Lysine: 0.75%                        │
│ NRC Compliance: ✅ 100%              │
└──────────────────────────────────────┘

Alternative: Finisher Diet 2 ($205.25/ton)
• Higher energy for accelerated growth
• +$6.75/ton cost increase

💡 For 110kg pigs, Finisher Diet 1 is optimal.
```

---

## 8. Support

### Getting Help

**In-App Support**:
- Type `/help` for command reference
- Type "help [topic]" for specific guidance
- Example: "help nutrition" or "help customers"

**Contact Support**:
- Email: support@feedsales-ai.com
- Telegram: Message `@feedflow_support`
- Response time: Within 24 hours

---

### Troubleshooting

**Common Issues**:

| Issue | Solution |
|-------|----------|
| Bot not responding | Check you're messaging `@feedflow_ai_bot`, not a similar name |
| Price shows "N/A" | Commodity may be temporarily unavailable; try again or check alternative |
| Formula not found | Use exact NRC formula name; check spelling |
| Customer add failed | Ensure all required fields provided (name, contact, phone) |
| Export failed | Check Telegram file download permissions |

---

### Feedback & Suggestions

We're constantly improving FeedSales AI!

**To submit feedback**:
```
feedback [your suggestion]
```

Example:
```
feedback Please add custom formula creation feature
```

---

### Feature Requests

Planned features for upcoming versions:

- **v2.0**: Custom formula builder
- **v2.1**: Multi-language support (Spanish, Chinese)
- **v2.2**: Integration with ERP systems
- **v2.3**: Supplier price API connections
- **v2.4**: Mobile app companion

---

## 9. Version History

### Current Version: 1.7.0

**Release Date**: March 31, 2026

---

### Version Log

#### v1.7.0 (Current)
- ✨ Added nutrition analysis against NRC standards
- ✨ New species support: Turkey, Duck
- ✨ Price alerts feature
- ✨ Cost trends and historical tracking
- ✨ Batch calculation for formula comparisons
- 🐛 Fixed customer export CSV formatting
- 🐛 Fixed price lookup for amino acids

#### v1.6.0
- ✨ Added customer management with multi-tenant isolation
- ✨ Export functionality (CSV, PDF)
- ✨ Formula comparison tool
- 🐛 Fixed calculation rounding errors

#### v1.5.0
- ✨ Added Sheep and Goat species
- ✨ Natural language command recognition
- ✨ Quick command shortcuts (/cost, /price, etc.)
- 🐛 Fixed formula name matching

#### v1.4.0
- ✨ Added Dairy Cattle formulas
- ✨ Price trend indicators (↑↓→)
- 🐛 Fixed energy unit conversions

#### v1.3.0
- ✨ Added Layer (egg production) formulas
- ✨ Price caching for faster responses
- 🐛 Fixed DDGS price lookup

#### v1.2.0
- ✨ Added Broiler formulas (3 phases)
- ✨ Support for by-product ingredients
- 🐛 Fixed ingredient percentage calculations

#### v1.1.0
- ✨ Added Beef Cattle formulas
- ✨ Mineral and additive price support
- 🐛 Fixed NE energy calculations

#### v1.0.0 (Initial Release)
- ✨ Core formula cost calculator
- ✨ 8 Swine formulas (NRC standards)
- ✨ Basic commodity prices (Corn, Soybean Meal, Wheat)
- ✨ Telegram bot launch: @feedflow_ai_bot

---

### Roadmap Preview

**Coming in v2.0**:
- Custom formula creation
- Formula optimization suggestions
- Supplier integration APIs
- Real-time price API connections
- Enhanced nutrition modeling

**Coming in v2.1**:
- Spanish language support
- Chinese language support
- Voice commands
- Formula templates library

---

## Appendix

### A. Complete Formula List

**Swine (8 formulas)**:
1. Nursery Diet 1
2. Nursery Diet 2
3. Grower Diet 1
4. Grower Diet 2
5. Finisher Diet 1
6. Finisher Diet 2
7. Gestation Diet
8. Lactation Diet

**Beef Cattle (3 formulas)**:
1. Growing Calf
2. Finishing Steer
3. Breeding Bull

**Dairy Cattle (4 formulas)**:
1. Lactating Cow High Production
2. Lactating Cow Medium Production
3. Dry Cow
4. Heifer Development

**Broiler (3 formulas)**:
1. Broiler Starter
2. Broiler Grower
3. Broiler Finisher

**Layer (3 formulas)**:
1. Layer Starter
2. Layer Developer
3. Layer Production

**Turkey (3 formulas)**:
1. Turkey Starter
2. Turkey Grower
3. Turkey Finisher

**Sheep (3 formulas)**:
1. Lamb Starter
2. Lamb Grower
3. Breeding Ewe

**Goat (3 formulas)**:
1. Kid Starter
2. Dairy Goat Lactating
3. Meat Goat Finisher

**Duck (2 formulas)**:
1. Duck Starter
2. Duck Finisher

**Total**: 38 NRC-standard formulas

---

### B. Complete Commodity List

**Grains**:
- Corn (Yellow Corn, #2 Grade)
- Wheat (Hard Red, Soft Red)
- Barley
- Oats
- Sorghum (Milo)
- Rice (Rice Bran, Rice Polish)

**Protein Meals**:
- Soybean Meal (48% CP, 44% CP)
- Canola Meal (Rapeseed Meal)
- Cottonseed Meal
- Sunflower Meal
- Peanut Meal
- Fish Meal

**By-products**:
- DDGS (Distillers Dried Grains with Solubles)
- Wheat Midds (Wheat Middlings)
- Corn Gluten Meal
- Corn Gluten Feed
- Brewers Grains

**Fats & Oils**:
- Soybean Oil
- Palm Oil
- Fish Oil
- Lard
- Tallow

**Minerals**:
- Limestone (Calcium Carbonate)
- Dicalcium Phosphate
- Monocalcium Phosphate
- Salt (Sodium Chloride)
- Magnesium Oxide
- Potassium Chloride

**Amino Acids**:
- L-Lysine HCl (98%)
- DL-Methionine
- L-Threonine
- L-Valine
- L-Isoleucine

**Additives**:
- Premix (Vitamin-Mineral Premix)
- Vitamins (A, D, E, K, B-complex)
- Enzymes (Phytase, Xylanase)
- Antioxidants

**Total**: 20+ commodities tracked

---

### C. Quick Reference Card

```
╔════════════════════════════════════════════╗
║     FeedSales AI Quick Reference           ║
╠════════════════════════════════════════════╣
║ Bot: @feedflow_ai_bot                      ║
║ Version: 1.7.0                             ║
╠════════════════════════════════════════════╣
║ Commands:                                  ║
║ /start     - Initialize                    ║
║ /help      - Help menu                     ║
║ /cost      - Formula cost                  ║
║ /price     - Commodity price               ║
║ /customer  - Manage records                ║
║ /nutrition - NRC analysis                  ║
╠════════════════════════════════════════════╣
║ Species: Swine, Beef, Dairy,              ║
║          Broiler, Layer, Turkey,          ║
║          Sheep, Goat, Duck                ║
╠════════════════════════════════════════════╣
║ Formulas: 38 NRC standards                 ║
║ Commodities: 20+ ingredients               ║
║ Prices: USD/ton                            ║
╚════════════════════════════════════════════╝
```

---

**FeedSales AI User Guide - Complete**

*Version 1.7.0 | March 31, 2026*

*© 2026 FeedSales AI. All rights reserved.*

*Telegram: @feedflow_ai_bot*

*Support: support@feedsales-ai.com*