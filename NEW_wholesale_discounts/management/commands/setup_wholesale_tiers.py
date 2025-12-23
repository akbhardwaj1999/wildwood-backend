from django.core.management.base import BaseCommand
from decimal import Decimal
from NEW_wholesale_discounts.models import NEW_WholesaleTier


class Command(BaseCommand):
    help = 'Create default wholesale tiers based on client requirements'

    def handle(self, *args, **options):
        # Client requirements: 20, 50, 100+ items with customizable minimums
        # Using order amounts instead of item counts for flexibility
        
        default_tiers = [
            {
                'name': 'Bronze (20+ Items)',
                'min_order_amount': Decimal('200.00'),  # Equivalent to ~20 items at $10 each
                'max_order_amount': Decimal('499.99'),
                'discount_percentage': Decimal('10.00'),
                'priority': 1,
                'is_active': True
            },
            {
                'name': 'Silver (50+ Items)',
                'min_order_amount': Decimal('500.00'),  # Equivalent to ~50 items at $10 each
                'max_order_amount': Decimal('999.99'),
                'discount_percentage': Decimal('15.00'),
                'priority': 2,
                'is_active': True
            },
            {
                'name': 'Gold (100+ Items)',
                'min_order_amount': Decimal('1000.00'),  # Equivalent to ~100 items at $10 each
                'max_order_amount': Decimal('2499.99'),
                'discount_percentage': Decimal('20.00'),
                'priority': 3,
                'is_active': True
            },
            {
                'name': 'Platinum (200+ Items)',
                'min_order_amount': Decimal('2500.00'),  # Equivalent to ~200+ items
                'discount_percentage': Decimal('25.00'),
                'priority': 4,
                'is_active': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for tier_data in default_tiers:
            tier, created = NEW_WholesaleTier.objects.get_or_create(
                name=tier_data['name'],
                defaults=tier_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created tier: {tier.name}')
                )
            else:
                # Update existing tier
                for key, value in tier_data.items():
                    setattr(tier, key, value)
                tier.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated tier: {tier.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} wholesale tiers '
                f'({created_count} created, {updated_count} updated)'
            )
        )
