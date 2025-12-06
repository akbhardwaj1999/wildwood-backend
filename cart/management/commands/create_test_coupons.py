"""
Management command to create test coupons for testing discount functionality
"""
from django.core.management.base import BaseCommand
from cart.models import Coupon
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create test coupons for discount testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test coupons...'))
        
        # Delete existing test coupons if they exist
        Coupon.objects.filter(code__in=['TEST10', 'SAVE20', 'FIXED50', 'PERCENT15', 'MIN100']).delete()
        
        # 1. 5% Discount Coupon - Simple percentage discount
        coupon1, created = Coupon.objects.get_or_create(
            code='SAVE5',
            defaults={
                'title': '5% Discount Coupon',
                'description': 'Get 5% off on your order. No minimum order required.',
                'discount': Decimal('5.00'),
                'discount_type': Coupon.DiscountType.PERCENTAGE,
                'minimum_order_amount': Decimal('0.00'),
                'single_use_per_user': False,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created coupon: {coupon1.code} - {coupon1.discount}% off'))
        else:
            # Update existing coupon
            coupon1.minimum_order_amount = Decimal('0.00')
            coupon1.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated coupon: {coupon1.code} - {coupon1.discount}% off (No minimum)'))
        
        # 2. 10% Discount Coupon
        coupon2, created = Coupon.objects.get_or_create(
            code='SAVE10',
            defaults={
                'title': '10% Discount Coupon',
                'description': 'Get 10% off on your order. No minimum order required.',
                'discount': Decimal('10.00'),
                'discount_type': Coupon.DiscountType.PERCENTAGE,
                'minimum_order_amount': Decimal('0.00'),
                'single_use_per_user': False,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created coupon: {coupon2.code} - {coupon2.discount}% off'))
        else:
            coupon2.minimum_order_amount = Decimal('0.00')
            coupon2.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated coupon: {coupon2.code} - {coupon2.discount}% off (No minimum)'))
        
        # 3. 15% Discount Coupon
        coupon3, created = Coupon.objects.get_or_create(
            code='SAVE15',
            defaults={
                'title': '15% Discount Coupon',
                'description': 'Get 15% off on your order. No minimum order required.',
                'discount': Decimal('15.00'),
                'discount_type': Coupon.DiscountType.PERCENTAGE,
                'minimum_order_amount': Decimal('0.00'),
                'single_use_per_user': False,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created coupon: {coupon3.code} - {coupon3.discount}% off'))
        else:
            coupon3.minimum_order_amount = Decimal('0.00')
            coupon3.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated coupon: {coupon3.code} - {coupon3.discount}% off (No minimum)'))
        
        # 4. 20% Discount Coupon
        coupon4, created = Coupon.objects.get_or_create(
            code='SAVE20',
            defaults={
                'title': '20% Discount Coupon',
                'description': 'Get 20% off on your order. No minimum order required.',
                'discount': Decimal('20.00'),
                'discount_type': Coupon.DiscountType.PERCENTAGE,
                'minimum_order_amount': Decimal('0.00'),
                'single_use_per_user': False,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created coupon: {coupon4.code} - {coupon4.discount}% off'))
        else:
            coupon4.minimum_order_amount = Decimal('0.00')
            coupon4.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated coupon: {coupon4.code} - {coupon4.discount}% off (No minimum)'))
        
        # 5. 25% Discount Coupon
        coupon5, created = Coupon.objects.get_or_create(
            code='SAVE25',
            defaults={
                'title': '25% Discount Coupon',
                'description': 'Get 25% off on your order. No minimum order required.',
                'discount': Decimal('25.00'),
                'discount_type': Coupon.DiscountType.PERCENTAGE,
                'minimum_order_amount': Decimal('0.00'),
                'single_use_per_user': False,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created coupon: {coupon5.code} - {coupon5.discount}% off'))
        else:
            coupon5.minimum_order_amount = Decimal('0.00')
            coupon5.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated coupon: {coupon5.code} - {coupon5.discount}% off (No minimum)'))
        
        # Delete old test coupons with minimum order requirements
        old_coupons = Coupon.objects.filter(code__in=['TEST10', 'FIXED50', 'PERCENT15', 'MIN100'])
        if old_coupons.exists():
            old_coupons.delete()
            self.stdout.write(self.style.WARNING('⚠ Deleted old test coupons with minimum order requirements'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Test coupons created successfully!'))
        self.stdout.write(self.style.SUCCESS('\n📋 Available Test Coupons (No Minimum Order Required):'))
        self.stdout.write(self.style.SUCCESS('  1. SAVE5  - 5% off'))
        self.stdout.write(self.style.SUCCESS('  2. SAVE10 - 10% off'))
        self.stdout.write(self.style.SUCCESS('  3. SAVE15 - 15% off'))
        self.stdout.write(self.style.SUCCESS('  4. SAVE20 - 20% off'))
        self.stdout.write(self.style.SUCCESS('  5. SAVE25 - 25% off'))

