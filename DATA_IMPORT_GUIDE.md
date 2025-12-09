# Data Import Guide - simple_matched_data.json

## Overview
Yeh guide aapko `simple_matched_data.json` file se products import karne mein help karega.

---

## Step 1: File Location Check

Pehle check karo ki file exist karti hai:
```bash
# Windows PowerShell
dir simple_matched_data.json

# Ya check karo ki file project root mein hai
# F:\wildwud-backend\simple_matched_data.json
```

---

## Step 2: Import Command

### Basic Import (Sab Products)
```bash
cd F:\wildwud-backend
python manage.py import_products simple_matched_data.json
```

### Test Import (Sirf 5 Products)
```bash
python manage.py import_products simple_matched_data.json --limit 5
```

### Skip Existing Products
```bash
python manage.py import_products simple_matched_data.json --skip-existing
```

### Full Import with Options
```bash
python manage.py import_products simple_matched_data.json --limit 10 --skip-existing
```

---

## Step 3: Command Options

### Available Options:

1. **`json_file`** (Required)
   - JSON file ka path
   - Example: `simple_matched_data.json`

2. **`--limit N`** (Optional)
   - Sirf N products import karega (testing ke liye)
   - Example: `--limit 10`

3. **`--skip-existing`** (Optional)
   - Agar product already exist karta hai, to skip kar dega
   - Duplicate products avoid karne ke liye

---

## Step 4: Import Process

### What Happens During Import:

1. **File Read**: JSON file read hoti hai
2. **Validation**: JSON format check hota hai
3. **Product Creation**: 
   - Product create hota hai
   - Variant create hota hai (price, quantity, etc.)
   - Images download hoti hain
   - Reviews import hote hain
4. **Statistics**: Import stats show hote hain

### Import Statistics:

Import ke baad yeh stats dikhenge:
- ✅ **Products created**: Kitne naye products create hue
- ⚠️ **Products skipped**: Kitne products skip hue (already exist)
- 🖼️ **Images downloaded**: Kitni images download hui
- ⭐ **Reviews imported**: Kitne reviews import hue
- ❌ **Errors**: Kitne errors aaye (if any)

---

## Step 5: Example Commands

### Example 1: Full Import
```bash
python manage.py import_products simple_matched_data.json
```

**Output:**
```
Reading JSON file: simple_matched_data.json
Found 100 products in JSON file
Starting import...
==================================================
Import completed!
==================================================
Products created: 100
Products skipped: 0
Images downloaded: 500
Reviews imported: 250
Errors: 0
==================================================
```

### Example 2: Test Import (5 products)
```bash
python manage.py import_products simple_matched_data.json --limit 5
```

**Output:**
```
Reading JSON file: simple_matched_data.json
Limiting import to 5 products
Found 5 products in JSON file
Starting import...
==================================================
Import completed!
==================================================
Products created: 5
Products skipped: 0
Images downloaded: 25
Reviews imported: 10
Errors: 0
==================================================
```

### Example 3: Skip Existing
```bash
python manage.py import_products simple_matched_data.json --skip-existing
```

---

## Step 6: Troubleshooting

### Error 1: File Not Found
```
CommandError: File "simple_matched_data.json" does not exist.
```

**Solution:**
- Check karo ki file project root (`F:\wildwud-backend\`) mein hai
- Ya full path do: `python manage.py import_products "F:\wildwud-backend\simple_matched_data.json"`

### Error 2: Invalid JSON
```
CommandError: Invalid JSON file: ...
```

**Solution:**
- JSON file ko validate karo
- Check karo ki proper JSON format hai

### Error 3: No Products Created
- Check karo ki JSON file mein products hain
- Check karo ki file empty to nahi hai
- Console output check karo for errors

---

## Step 7: Verify Import

### Check in Django Admin:
1. Go to: `http://127.0.0.1:8000/admin/`
2. Navigate to: **Gallery Items > Gallery items**
3. Check imported products

### Check via API:
```bash
# Get all products
GET http://127.0.0.1:8000/api/gallery/items/
```

---

## Step 8: JSON File Format

### Expected Format:
```json
[
  {
    "TITLE": "Product Name",
    "DESCRIPTION": "Product Description",
    "PRICE": 44.99,
    "QUANTITY": 7,
    "TAGS": "tag1,tag2,tag3",
    "IMAGES": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "REVIEWS": [
      {
        "reviewer": "John",
        "date_reviewed": "01/28/2025",
        "star_rating": 5,
        "message": "Great product!"
      }
    ]
  }
]
```

---

## Quick Reference

### Most Common Commands:

```bash
# Full import
python manage.py import_products simple_matched_data.json

# Test with 10 products
python manage.py import_products simple_matched_data.json --limit 10

# Import and skip existing
python manage.py import_products simple_matched_data.json --skip-existing
```

---

## Tips

1. **Pehle Test Karo**: `--limit 5` se test karo before full import
2. **Backup Lo**: Import se pehle database backup lo
3. **Check Logs**: Console output check karo for any errors
4. **Skip Existing**: Agar duplicate products avoid karne hain, to `--skip-existing` use karo

---

## Need Help?

Agar koi issue aaye:
1. Console output check karo
2. Django admin mein check karo
3. API se verify karo
4. JSON file format check karo

Happy Importing! 🚀

