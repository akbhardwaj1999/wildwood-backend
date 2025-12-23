# Wholesale Discount Setup Instructions

## PythonAnywhere पर Deploy करने के बाद

### Step 1: Script Upload करें
`setup_wholesale_discounts.py` file को PythonAnywhere server पर upload करें (project root directory में)

### Step 2: Script Run करें

**Option A: Bash Console से (Recommended)**
```bash
cd /home/yourusername/wildwud-backend
python3.10 setup_wholesale_discounts.py
```

**Option B: Web Console से**
1. PythonAnywhere dashboard में जाएं
2. "Consoles" tab पर click करें
3. "Bash console" start करें
4. Project directory में navigate करें
5. Script run करें:
```bash
python3.10 setup_wholesale_discounts.py
```

### Step 3: Verify करें

Script successfully run होने के बाद आपको यह output दिखना चाहिए:

```
============================================================
SETTING UP WHOLESALE DISCOUNT CONFIGURATION
============================================================

[SUCCESS] Created/Updated configuration: Default Wholesale Discounts

============================================================
WHOLESALE DISCOUNT CONFIGURATION
============================================================
Name: Default Wholesale Discounts
Active: True

Discount Tiers:
  Tier 1: Above $500.00 -> 10.00% off
  Tier 2: Above $1000.00 -> 15.00% off
  Tier 3: Above $2000.00 -> 20.00% off
  Tier 4: Above $2500.00 -> 25.00% off
============================================================

[SUCCESS] Wholesale discount configuration setup completed!
============================================================
```

### Step 4: Test करें

1. Frontend में जाएं: `https://yourdomain.com/wholesale/tiers`
2. Pricing tiers दिखनी चाहिए
3. Admin panel में जाएं: `https://yourdomain.com/admin`
4. "NEW_WHOLESALE_DISCOUNTS" → "Wholesale Discount Configurations" में configuration verify करें

## Local Development में Use करने के लिए

```bash
# Virtual environment activate करें
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Script run करें
python setup_wholesale_discounts.py
```

## Default Configuration

Script automatically यह configuration create करेगा:

- **Tier 1**: Above $500 → 10% discount
- **Tier 2**: Above $1,000 → 15% discount
- **Tier 3**: Above $2,000 → 20% discount
- **Tier 4**: Above $2,500 → 25% discount

## Configuration Update करना

अगर आप configuration update करना चाहते हैं:

1. Django Admin में जाएं: `/admin`
2. "NEW_WHOLESALE_DISCOUNTS" → "Wholesale Discount Configurations"
3. Configuration edit करें
4. या script को modify करके फिर से run करें

## Troubleshooting

**Error: No module named 'NEW_wholesale_discounts'**
- Make sure `NEW_wholesale_discounts` app `INSTALLED_APPS` में है
- Check `wildwud/settings.py`

**Error: no such table**
- Migrations run करें:
  ```bash
  python manage.py migrate NEW_wholesale_discounts
  ```

**Script doesn't run on PythonAnywhere**
- Python version check करें (Python 3.10 recommended)
- Make sure virtual environment activate है
- Check file permissions

## Notes

- Script idempotent है - multiple times run कर सकते हैं
- अगर active configuration already exists, तो वो update हो जाएगी
- Script safe है - existing data को delete नहीं करेगा

