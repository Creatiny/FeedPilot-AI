# FeedSales AI - Price Update Setup

## Automated Daily Price Updates

### Option 1: Cron Job (Linux/Mac)

1. **Edit crontab**:
   ```bash
   crontab -e
   ```

2. **Add daily update at 8:00 AM**:
   ```bash
   0 8 * * * /home/kenny/.openclaw/workspace/feed-sales-ai-mvp/scripts/daily_price_update.sh
   ```

3. **Verify**:
   ```bash
   crontab -l
   ```

### Option 2: Manual Update

Run manually whenever you want to update prices:

```bash
cd /home/kenny/.openclaw/workspace/feed-sales-ai-mvp
python3 scripts/update_prices.py
```

### Option 3: Systemd Timer (Linux)

1. **Create service file** `/etc/systemd/system/feed-sales-price-update.service`:
   ```ini
   [Unit]
   Description=FeedSales AI Daily Price Update
   After=network.target

   [Service]
   Type=oneshot
   User=kenny
   WorkingDirectory=/home/kenny/.openclaw/workspace/feed-sales-ai-mvp
   ExecStart=/usr/bin/python3 scripts/update_prices.py
   StandardOutput=journal
   StandardError=journal
   ```

2. **Create timer file** `/etc/systemd/system/feed-sales-price-update.timer`:
   ```ini
   [Unit]
   Description=Run FeedSales price update daily

   [Timer]
   OnCalendar=*-*-* 08:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. **Enable and start**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable feed-sales-price-update.timer
   sudo systemctl start feed-sales-price-update.timer
   ```

### Log Files

- **Price update log**: `logs/price_update.log`
- **Systemd journal**: `journalctl -u feed-sales-price-update.service`

### Testing

Test the update script manually:

```bash
cd /home/kenny/.openclaw/workspace/feed-sales-ai-mvp
python3 scripts/update_prices.py
```

Expected output:
```
============================================================
FeedSales AI - Price Update
============================================================
Scraping CBOT futures prices...
Scraped 4 CBOT prices
Scraping USDA national prices...
Scraped 18 USDA prices
Updated 22 price records
============================================================
Price update completed: 22 records
============================================================
```

### Verify Updated Prices

Check today's prices in database:

```bash
cd /home/kenny/.openclaw/workspace/feed-sales-ai-mvp
python3 -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('data/feed_sales.db')
cursor = conn.cursor()
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('SELECT ingredient_name, price, trend FROM ingredient_prices WHERE date = ? ORDER BY ingredient_name', (today,))
print(f'Today\\'s Prices ({today}):')
for row in cursor.fetchall():
    print(f'  {row[0]}: \${row[1]:.2f}/ton ({row[2]})')
conn.close()
"
```
