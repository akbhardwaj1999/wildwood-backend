"""
Django management command to add default shipping cost rules for testing
"""
from django.core.management.base import BaseCommand
from cart.models import ShippingCost
from decimal import Decimal


class Command(BaseCommand):
    help = 'Adds default shipping cost rules for testing purposes'

    def handle(self, *args, **options):
        self.stdout.write('Adding default shipping cost rules...')
        
        # Clear existing shipping costs (optional - comment out if you want to keep existing)
        # ShippingCost.objects.all().delete()
        
        shipping_rules = [
            # LOCAL shipping (same city as warehouse)
            # Volume-based rules
            {'parameter': ShippingCost.VOLUME, 'value_start': 0, 'value_end': 100, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('5.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('8.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 501, 'value_end': 1000, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 1001, 'value_end': 5000, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('15.00')},
            # Weight-based rules
            {'parameter': ShippingCost.WEIGHT, 'value_start': 0, 'value_end': 10, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('5.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 11, 'value_end': 50, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('8.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 51, 'value_end': 100, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.LOCAL, 'charges': Decimal('15.00')},
            
            # OTHER_CITY shipping (same state, different city)
            {'parameter': ShippingCost.VOLUME, 'value_start': 0, 'value_end': 100, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('8.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 501, 'value_end': 1000, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('18.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 1001, 'value_end': 5000, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('25.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 0, 'value_end': 10, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('8.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 11, 'value_end': 50, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 51, 'value_end': 100, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('18.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.OTHER_CITY, 'charges': Decimal('25.00')},
            
            # OTHER_STATE shipping (same country, different state)
            {'parameter': ShippingCost.VOLUME, 'value_start': 0, 'value_end': 100, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('18.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 501, 'value_end': 1000, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('25.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 1001, 'value_end': 5000, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('35.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 0, 'value_end': 10, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('12.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 11, 'value_end': 50, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('18.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 51, 'value_end': 100, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('25.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.OTHER_STATE, 'charges': Decimal('35.00')},
            
            # INTERNATIONAL shipping (different country)
            {'parameter': ShippingCost.VOLUME, 'value_start': 0, 'value_end': 100, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('25.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('35.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 501, 'value_end': 1000, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('50.00')},
            {'parameter': ShippingCost.VOLUME, 'value_start': 1001, 'value_end': 5000, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('75.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 0, 'value_end': 10, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('25.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 11, 'value_end': 50, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('35.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 51, 'value_end': 100, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('50.00')},
            {'parameter': ShippingCost.WEIGHT, 'value_start': 101, 'value_end': 500, 'shipment_type': ShippingCost.INTERNATIONAL, 'charges': Decimal('75.00')},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for rule in shipping_rules:
            # Check if this rule already exists
            existing = ShippingCost.objects.filter(
                parameter=rule['parameter'],
                value_start=rule['value_start'],
                value_end=rule['value_end'],
                shipment_type=rule['shipment_type']
            ).first()
            
            if existing:
                self.stdout.write(self.style.WARNING(f'Skipping existing rule: {existing}'))
                skipped_count += 1
            else:
                ShippingCost.objects.create(**rule)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {rule["parameter"]} {rule["value_start"]}-{rule["value_end"]}, {rule["shipment_type"]}, ${rule["charges"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nCompleted! Created {created_count} shipping cost rules, skipped {skipped_count} existing rules.'))
        self.stdout.write('\nNote: Make sure WAREHOUSE_COUNTRY, WAREHOUSE_STATE, and WAREHOUSE_CITY are set in settings.py')
        self.stdout.write('Current warehouse settings:')
        from django.conf import settings
        if hasattr(settings, 'WAREHOUSE_COUNTRY'):
            self.stdout.write(f'  Country: {settings.WAREHOUSE_COUNTRY}')
            self.stdout.write(f'  State: {settings.WAREHOUSE_STATE}')
            self.stdout.write(f'  City: {settings.WAREHOUSE_CITY}')
        else:
            self.stdout.write(self.style.ERROR('  Warehouse settings not found in settings.py!'))

