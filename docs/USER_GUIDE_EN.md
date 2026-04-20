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

FeedSales AI supports formula calculations for **30 species**:

| Category | Species |
|----------|---------|
| **Livestock** | Swine, Beef Cattle, Dairy Cattle, Sheep, Goat, Water Buffalo, Bison |
| **Poultry** | Broiler, Layer, Turkey, Duck |
| **Equine** | Horse |
| **Companion** | Cat, Dog |
| **Aquatic** | Rainbow Trout, Catfish, Channel Catfish, Tilapia, Salmon, Carp, Pangasius, Seabass, Shrimp |
| **Small Ruminant** | Alpaca, Llama, Deer, Elk |
| **Apiculture** | Honey Bee |
| **Other** | Rabbit |

### Standard Formulas

The system includes **87 NRC-standard formulas** across all 30 species:

- **Swine** (9): Nursery Diet 1/2/3, Grower Diet 1/2, Finisher Diet, Gestating Sow Diet, Lactating Sow Diet, Weaner Diet
- **Beef Cattle** (4): Starter, Grower, Finisher, Feedlot High Energy
- **Dairy Cattle** (4): Calf Starter, Heifer Grower, Lactating Cow Diet, Dairy Cow High Production
- **Broiler** (4): Pre-Starter, Starter, Grower, Finisher
- **Layer** (5): Starter, Grower, Phase 1, Phase 2, Laying Diet
- **Turkey** (3): Starter, Grower, Finisher
- **Sheep** (7): Lamb Starter, Lamb Finisher, Lamb Finishing, Ewe Gestating, Ewe Lactating, Ewe Lactation, Ewe Late Gestation
- **Goat** (6): Kid Starter (×2), Doe Gestating, Doe Lactating, Dairy Doe Early Lactation, Meat Goat Grower
- **Duck** (3): Starter, Grower, Breeder
- **Honey Bee** (5): Spring Build-Up, Brood Rearing, Pollen Substitute Patty, Fall Feeding, Winter Fondant
- **Horse** (3): Maintenance, Performance, Breeding Mare
- **Cat** (2): Kitten Diet, Adult Maintenance Diet
- **Dog** (2): Puppy Diet, Adult Maintenance Diet
- **Aquatic** (10): Trout Starter/Grower, Catfish Fingerling/Production, Rainbow Trout Starter/Fingerling/Production, Salmon Starter/Grower, Carp Fingerling/Grower, Pangasius, Tilapia, Seabass, Shrimp
- **Rabbit** (2): Grower Diet, Lactating Doe Diet
- **Alpaca** (2): Maintenance, Lactating
- **Llama** (2): Maintenance, Lactating
- **Deer** (2): Finishing, Velvet Antler
- **Elk** (2): Maintenance, Velvet Antler
- **Bison** (1): Finishing
- **Water Buffalo** (1): Growing

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

**Available Commodities** (69 feed ingredients):

| Category | Commodities |
|----------|-------------|
| Grains | Corn (#2 Yellow CBOT), Wheat (SRW CBOT), Oats (#2 White CBOT), Rice bran, Rice polishings |
| Protein Meals | Soybean meal (48%, 47.5%), Canola meal (36%), Corn gluten meal (60%), Fish meal (65%), Meat & bone meal (ruminant), Poultry by-product meal, Blood meal (porcine), Feather meal (80%), Shrimp meal, Squid meal |
| By-products | DDGS (10% fat), Wheat middlings, Beet pulp (dried), Brewer's yeast (dried), Molasses (cane), Whey (dried), Wheat gluten, Soy flour (defatted) |
| Forages | Alfalfa hay (early bloom), Corn silage, Grass hay (early bloom), Timothy hay |
| Fats/Oils | Soybean oil (crude), Fish oil, Lecithin |
| Minerals | Limestone (ag), Dicalcium phosphate, Salt (white), Urea |
| Amino Acids | L-Lysine HCl, DL-Methionine, Threonine (98%), Taurine, Choline chloride (60%) |
| Premixes (16) | Swine, Sow, Broiler, Layer, Turkey, Duck, Duck breeder, Beef, Dairy, Calf, Heifer, Sheep, Ewe, Goat, Doe, Trout, Catfish, Cat, Dog |
| Specialty | Sugar (white granulated), Vinegar (acidifier), Milk replacer (calf), Pollen (bee collected), Water, Vitamin/mineral premix |

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
Layer, Turkey, Sheep, Goat, Duck,
Horse, Cat, Dog, Rabbit,
Alpaca, Llama, Deer, Elk, Bison,
Water Buffalo, Honey Bee,
Rainbow Trout, Catfish, Salmon, Carp,
Tilapia, Pangasius, Seabass, Shrimp

FORMULAS: 87 NRC standards
COMMODITIES: 69 feed ingredients

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

**Answer**: Currently, FeedSales AI supports 87 NRC-standard formulas across 30 species. Custom formula creation is planned for v2.0. For now, you can modify standard formulas by adjusting ingredient percentages in your calculations.

---

### Q4: Which species are supported?

**Answer**: We support **30 species** across livestock, poultry, aquatic, companion, and specialty animals:

- **Livestock**: Swine, Beef Cattle, Dairy Cattle, Sheep, Goat, Water Buffalo, Bison
- **Poultry**: Broiler, Layer, Turkey, Duck
- **Equine**: Horse
- **Companion**: Cat, Dog
- **Aquatic**: Rainbow Trout, Catfish, Tilapia, Salmon, Carp, Pangasius, Seabass, Shrimp
- **Specialty**: Alpaca, Llama, Deer, Elk, Honey Bee, Rabbit

Each species has multiple phase-specific formulas (starter, grower, finisher, lactating, etc.).

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

### A. Complete Formula List (87 Formulas, 30 Species)

**Swine (9)**:
1. Nursery Diet 1 (5-10 kg)
2. Nursery Diet 2 (10-20 kg)
3. Nursery Diet 3 (20-30 kg)
4. Grower Diet 1 (30-60 kg)
5. Grower Diet 2 (60-90 kg)
6. Finisher Diet (90+ kg)
7. Gestating Sow Diet
8. Lactating Sow Diet
9. Swine Weaner Diet (5-10 kg)

**Beef Cattle (4)**:
1. Beef Cattle Starter (150-250 kg)
2. Beef Cattle Grower (250-400 kg)
3. Beef Cattle Finisher (400+ kg)
4. Beef Feedlot High Energy (400-600 kg)

**Dairy Cattle (4)**:
1. Dairy Calf Starter (0-3 months)
2. Dairy Heifer Grower (3-12 months)
3. Lactating Cow Diet
4. Dairy Cow High Production (600-700 kg)

**Broiler (4)**:
1. Broiler Pre-Starter Diet (0-0.25 kg)
2. Broiler Starter (0-10 days)
3. Broiler Grower (11-24 days)
4. Broiler Finisher (25+ days)

**Layer (5)**:
1. Layer Starter (0-6 weeks)
2. Layer Grower (7-18 weeks)
3. Layer Phase 1 Diet (18-40 weeks)
4. Layer Phase 2 Diet (40-60 weeks)
5. Layer Diet (19+ weeks)

**Turkey (3)**:
1. Turkey Starter (0-4 weeks)
2. Turkey Grower (5-12 weeks)
3. Turkey Finisher (13-20 weeks)

**Sheep (7)**:
1. Lamb Starter (15-30 kg)
2. Lamb Finisher (30+ kg)
3. Lamb Finishing (30-50 kg)
4. Ewe Gestating
5. Ewe Lactating
6. Ewe Lactation (60-80 kg)
7. Ewe Late Gestation (60-80 kg)

**Goat (6)**:
1. Goat Kid Starter (10-20 kg)
2. Kid Starter (5-15 kg)
3. Goat Doe Gestating
4. Goat Doe Lactating
5. Dairy Doe Early Lactation (50-70 kg)
6. Meat Goat Grower (20-40 kg)

**Duck (3)**:
1. Duck Starter (0-3 weeks)
2. Duck Grower (4-7 weeks)
3. Duck Breeder

**Honey Bee (5)**:
1. Spring Build-Up
2. Brood Rearing (Pollen Patty)
3. Pollen Substitute Patty
4. Fall Feeding
5. Winter Fondant

**Horse (3)**:
1. Horse Maintenance Diet (400-600 kg)
2. Horse Performance Diet (400-600 kg)
3. Horse Breeding Mare Diet (400-600 kg)

**Cat (2)**:
1. Cat Kitten Diet (0-4 kg)
2. Cat Maintenance Diet (3-6 kg)

**Dog (2)**:
1. Dog Puppy Diet (0-25 kg)
2. Dog Maintenance Diet (10-30 kg)

**Pet (2)**:
1. Cat Food Adult (AAFCO 2026)
2. Dog Food Adult (AAFCO 2026)

**Aquatic (16)**:
1. Trout Starter (Fry, 0-5 g)
2. Trout Grower (Fingerling, 5-50 g)
3. Rainbow Trout Starter (0-5 g)
4. Rainbow Trout Fingerling (5-50 g)
5. Rainbow Trout Production (50-250 g)
6. Catfish Grower (50-500 g)
7. Channel Catfish Fingerling (5-50 g)
8. Channel Catfish Production (50-500 g)
9. Atlantic Salmon Starter (0-10 g)
10. Atlantic Salmon Grower (10-500 g)
11. Common Carp Fingerling (5-50 g)
12. Common Carp Grower (50-250 g)
13. Pangasius Fingerling (5-50 g)
14. Tilapia Grower Diet (50-200 g)
15. Asian Seabass Grower (50-500 g)
16. Shrimp Grower Diet (5-20 g)

**Rabbit (2)**:
1. Rabbit Grower Diet (0.5-2 kg)
2. Rabbit Lactating Doe Diet (3-5 kg)

**Alpaca (2)**:
1. Alpaca Maintenance (50-80 kg)
2. Alpaca Lactating (60-90 kg)

**Llama (2)**:
1. Llama Maintenance (120-180 kg)
2. Llama Lactating (130-200 kg)

**Deer (2)**:
1. Deer Finishing (50-80 kg)
2. Deer Velvet Antler (80-120 kg)

**Elk (2)**:
1. Elk Maintenance (250-350 kg)
2. Elk Velvet Antler (280-400 kg)

**Bison (1)**:
1. Bison Finishing (350-500 kg)

**Water Buffalo (1)**:
1. Water Buffalo Growing (200-350 kg)

**Total**: 87 NRC-standard formulas

---

### B. Complete Ingredient List (69 Ingredients)

**Energy Feeds**:
- Corn, grain
- Corn, #2 Yellow CBOT
- Wheat, SRW CBOT
- Oats, #2 White CBOT
- Rice bran
- Rice polishings
- Wheat middlings

**Protein Feeds**:
- Soybean meal, 48%
- Soybean meal, 47.5%
- Canola meal, 36%
- Corn gluten meal, 60%
- Fish meal, 65%
- Blood meal, porcine
- Feather meal, 80%
- Meat and bone meal, ruminant
- Poultry by-product meal
- Shrimp meal
- Squid meal

**By-products**:
- DDGS, 10% fat
- Beet pulp, dried
- Brewer's yeast, dried
- Molasses, cane
- Whey, dried
- Wheat gluten
- Soy flour, defatted

**Forages**:
- Alfalfa hay, early bloom
- Corn silage
- Grass hay, early bloom
- Timothy hay

**Fats & Oils**:
- Soybean oil, crude
- Fish oil
- Lecithin

**Minerals**:
- Limestone, ag
- Dicalcium phosphate
- Salt, white
- Urea

**Amino Acids**:
- L-Lysine HCl
- DL-Methionine
- Threonine, 98%
- Taurine
- Choline chloride, 60%

**Premixes (16 species-specific)**:
- Premix, swine / sow / broiler / layer / turkey / duck / duck breeder
- Premix, beef / dairy / calf / heifer / sheep / ewe / goat / doe
- Premix, trout / catfish / cat / dog

**Specialty**:
- Sugar, white granulated
- Vinegar (acidifier)
- Milk replacer, calf
- Pollen, bee collected
- Water
- Vitamin/mineral premix

**Total**: 69 feed ingredients

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
║ Species: 30 (Swine, Cattle, Poultry,      ║
║          Equine, Aquatic, Companion,      ║
║          Small Ruminant, Apiculture)      ║
╠════════════════════════════════════════════╣
║ Formulas: 87 NRC standards                 ║
║ Ingredients: 69 feed commodities           ║
║ Prices: USD/ton                            ║
╚════════════════════════════════════════════╝
```

---

**FeedSales AI User Guide - Complete**

*Version 1.7.0 | March 31, 2026*

*© 2026 FeedSales AI. All rights reserved.*

*Telegram: @feedflow_ai_bot*

*Support: support@feedsales-ai.com*