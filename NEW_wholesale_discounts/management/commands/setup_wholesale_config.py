from django.core.management.base import BaseCommand
from decimal import Decimal
from NEW_wholesale_discounts.models import NEW_WholesaleDiscountConfig

class Command(BaseCommand):
    help = 'Create default wholesale discount configuration based on client requirements'

    def handle(self, *args, **options):
        # Default configuration based on client requirements
        default_config = {
            'name': 'Default Wholesale Discounts',
            'threshold_1': Decimal('500.00'),  # Above $500 → 10% off
            'discount_1': Decimal('10.00'),
            'threshold_2': Decimal('1000.00'),  # Above $1000 → 15% off
            'discount_2': Decimal('15.00'),
            'threshold_3': Decimal('2000.00'),  # Above $2000 → 20% off
            'discount_3': Decimal('20.00'),
            'threshold_4': Decimal('2500.00'),  # Above $2500 → 25% off
            'discount_4': Decimal('25.00'),
            'is_active': True
        }
        
        # Check if configuration already exists
        existing_config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
        
        if existing_config:
            self.stdout.write(
                self.style.WARNING('Active configuration already exists. Updating...')
            )
            for key, value in default_config.items():
                setattr(existing_config, key, value)
            existing_config.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated configuration: {existing_config.name}')
            )
        else:
            # Create new configuration
            config = NEW_WholesaleDiscountConfig.objects.create(**default_config)
            self.stdout.write(
                self.style.SUCCESS(f'Created configuration: {config.name}')
            )
        
        # Display the configuration
        config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
        if config:
            self.stdout.write('\n' + '='*50)
            self.stdout.write('WHOLESALE DISCOUNT CONFIGURATION')
            self.stdout.write('='*50)
            self.stdout.write(f'Name: {config.name}')
            self.stdout.write(f'Active: {config.is_active}')
            self.stdout.write('\nDiscount Tiers:')
            self.stdout.write(f'  Above ${config.threshold_1} → {config.discount_1}% off')
            self.stdout.write(f'  Above ${config.threshold_2} → {config.discount_2}% off')
            self.stdout.write(f'  Above ${config.threshold_3} → {config.discount_3}% off')
            self.stdout.write(f'  Above ${config.threshold_4} → {config.discount_4}% off')
            self.stdout.write('='*50)
