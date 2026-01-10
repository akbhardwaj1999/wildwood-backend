"""
Check abandoned cart status and why emails might not be sending
Usage: python manage.py check_abandoned_carts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from cart.models import Order


class Command(BaseCommand):
    help = 'Check abandoned cart status and email conditions'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('ABANDONED CART STATUS CHECK')
        self.stdout.write('=' * 60)
        
        # Find all carts with items
        all_orders = Order.objects.filter(
            ordered=False,
            items__isnull=False
        ).distinct().select_related('user').order_by('-start_date')
        
        self.stdout.write(f'\nTotal carts with items (not ordered): {all_orders.count()}\n')
        
        if all_orders.count() == 0:
            self.stdout.write(self.style.WARNING('No abandoned carts found!'))
            return
        
        # Check each reminder condition
        reminders = [
            {'hours_ago': 2/60, 'email_count': 0, 'name': 'First (2 min)'},
            {'hours_ago': 5/60, 'email_count': 1, 'name': 'Second (5 min)'},
            {'hours_ago': 10/60, 'email_count': 2, 'name': 'Third (10 min)'},
        ]
        
        for reminder in reminders:
            time_ago = timezone.now() - timedelta(hours=reminder['hours_ago'])
            
            self.stdout.write(f'\n--- {reminder["name"]} Email Check ---')
            
            matching_orders = all_orders.filter(
                user__isnull=False,
                start_date__lt=time_ago,
                abandoned_email_count=reminder['email_count'],
            ).exclude(user__email='').exclude(user__email__isnull=True)
            
            count = matching_orders.count()
            self.stdout.write(f'Matching carts: {count}')
            
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f'✅ {count} cart(s) ready for {reminder["name"]} email'))
                for order in matching_orders[:3]:
                    self.stdout.write(f'  - Order {order.reference_number}: {order.user.email} (created {order.start_date})')
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  No carts ready for {reminder["name"]} email'))
                
                # Show why carts don't match
                old_orders = all_orders.filter(
                    user__isnull=False,
                    start_date__lt=time_ago,
                ).exclude(user__email='').exclude(user__email__isnull=True)
                
                if old_orders.exists():
                    self.stdout.write('\n  Carts that are old enough but not matching:')
                    for order in old_orders[:3]:
                        self.stdout.write(f'    - Order {order.reference_number}:')
                        self.stdout.write(f'      Email count: {order.abandoned_email_count} (needs {reminder["email_count"]})')
                        self.stdout.write(f'      User: {order.user.email if order.user else "No user"}')
                        self.stdout.write(f'      Created: {order.start_date}')
        
        # Show all carts summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('ALL CARTS SUMMARY:')
        self.stdout.write('=' * 60)
        
        for order in all_orders[:5]:
            age_minutes = (timezone.now() - order.start_date).total_seconds() / 60
            self.stdout.write(f'\nOrder: {order.reference_number}')
            self.stdout.write(f'  User: {order.user.email if order.user else "No user (guest)"}')
            self.stdout.write(f'  Created: {order.start_date} ({age_minutes:.1f} minutes ago)')
            self.stdout.write(f'  Email count: {order.abandoned_email_count}')
            self.stdout.write(f'  Items: {order.items.count()}')
            
            # Check if ready for email
            if order.user and order.user.email:
                if order.abandoned_email_count == 0 and age_minutes >= 2:
                    self.stdout.write(self.style.SUCCESS('  ✅ Ready for 1st email'))
                elif order.abandoned_email_count == 1 and age_minutes >= 5:
                    self.stdout.write(self.style.SUCCESS('  ✅ Ready for 2nd email'))
                elif order.abandoned_email_count == 2 and age_minutes >= 10:
                    self.stdout.write(self.style.SUCCESS('  ✅ Ready for 3rd email'))
                elif order.abandoned_email_count >= 3:
                    self.stdout.write(self.style.WARNING('  ⚠️  All emails already sent (count=3+)'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  Not ready yet (needs {2 if order.abandoned_email_count == 0 else 5 if order.abandoned_email_count == 1 else 10} minutes)'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ No user or email'))
        
        self.stdout.write('\n' + '=' * 60)

