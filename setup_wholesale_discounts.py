#!/usr/bin/env python
"""
Script to setup default wholesale discount configuration
Run this script after deploying to PythonAnywhere or locally

Usage:
    python setup_wholesale_discounts.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

from decimal import Decimal
from NEW_wholesale_discounts.models import NEW_WholesaleDiscountConfig

def setup_wholesale_discounts():
    """Create or update default wholesale discount configuration"""
    
    print("=" * 60)
    print("SETTING UP WHOLESALE DISCOUNT CONFIGURATION")
    print("=" * 60)
    
    # Default configuration based on requirements
    default_config = {
        'name': 'Default Wholesale Discounts',
        'threshold_1': Decimal('500.00'),   # Above $500 → 10% off
        'discount_1': Decimal('10.00'),
        'threshold_2': Decimal('1000.00'),   # Above $1000 → 15% off
        'discount_2': Decimal('15.00'),
        'threshold_3': Decimal('2000.00'),   # Above $2000 → 20% off
        'discount_3': Decimal('20.00'),
        'threshold_4': Decimal('2500.00'),   # Above $2500 → 25% off
        'discount_4': Decimal('25.00'),
        'is_active': True
    }
    
    # Check if active configuration already exists
    existing_config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
    
    if existing_config:
        print(f"\n[INFO] Active configuration already exists: {existing_config.name}")
        print("[INFO] Updating with default values...")
        
        # Update existing configuration
        for key, value in default_config.items():
            setattr(existing_config, key, value)
        existing_config.save()
        
        print(f"[SUCCESS] Updated configuration: {existing_config.name}")
    else:
        # Create new configuration
        print("\n[INFO] No active configuration found. Creating new one...")
        config = NEW_WholesaleDiscountConfig.objects.create(**default_config)
        print(f"[SUCCESS] Created configuration: {config.name}")
        existing_config = config
    
    # Display the configuration
    print("\n" + "=" * 60)
    print("WHOLESALE DISCOUNT CONFIGURATION")
    print("=" * 60)
    print(f"Name: {existing_config.name}")
    print(f"Active: {existing_config.is_active}")
    print(f"Created: {existing_config.created_at}")
    print(f"Updated: {existing_config.updated_at}")
    print("\nDiscount Tiers:")
    print(f"  Tier 1: Above ${existing_config.threshold_1} -> {existing_config.discount_1}% off")
    print(f"  Tier 2: Above ${existing_config.threshold_2} -> {existing_config.discount_2}% off")
    print(f"  Tier 3: Above ${existing_config.threshold_3} -> {existing_config.discount_3}% off")
    print(f"  Tier 4: Above ${existing_config.threshold_4} -> {existing_config.discount_4}% off")
    print("=" * 60)
    print("\n[SUCCESS] Wholesale discount configuration setup completed!")
    print("\nYou can now:")
    print("  1. View tiers at: /wholesale/tiers")
    print("  2. Manage configuration in Django Admin: /admin")
    print("=" * 60)
    
    return existing_config

if __name__ == '__main__':
    try:
        config = setup_wholesale_discounts()
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Failed to setup wholesale discounts: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

