"""
Debug command to check abandoned cart conditions
Usage: python manage.py debug_abandoned_carts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from cart.models import Order


class Command(BaseCommand):
    help = 'Debug abandoned cart conditions - check why emails might not be sending'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('ABANDONED CART DEBUG REPORT')
        self.stdout.write('=' * 60)
        
        # Check all orders with items
        all_orders = Order.objects.filter(
            ordered=False,
            items__isnull=False
        ).distinct().select_related('user')
        
        self.stdout.write(f'\nTotal carts with items (not ordered): {all_orders.count()}')
        
        # Check each reminder condition
        reminders = [
            {'hours_ago': 2/60, 'email_count': 0, 'name': 'First (2 min)'},
            {'hours_ago': 5/60, 'email_count': 1, 'name': 'Second (5 min)'},
            {'hours_ago': 10/60, 'email_count': 2, 'name': 'Third (10 min)'},
        ]
        
        for reminder in reminders:
            time_ago = timezone.now() - timedelta(hours=reminder['hours_ago'])
            
            self.stdout.write(f'\n--- {reminder["name"]} Email Check ---')
            self.stdout.write(f'Time threshold: {time_ago}')
            
            # Check conditions step by step
            orders_with_user = all_orders.filter(user__isnull=False)
            self.stdout.write(f'  - Orders with user: {orders_with_user.count()}')
            
            orders_old_enough = orders_with_user.filter(start_date__lt=time_ago)
            self.stdout.write(f'  - Orders old enough (created before {time_ago}): {orders_old_enough.count()}')
            
            orders_correct_count = orders_old_enough.filter(abandoned_email_count=reminder['email_count'])
            self.stdout.write(f'  - Orders with email_count={reminder["email_count"]}: {orders_correct_count.count()}')
            
            orders_with_email = orders_correct_count.exclude(user__email='').exclude(user__email__isnull=True)
            self.stdout.write(f'  - Orders with valid email: {orders_with_email.count()}')
            
            # Show details of matching orders
            if orders_with_email.exists():
                self.stdout.write('\n  Matching orders:')
                for order in orders_with_email[:5]:  # Show first 5
                    self.stdout.write(f'    - Order {order.reference_number}:')
                    self.stdout.write(f'      User: {order.user.email} ({order.user.username})')
                    self.stdout.write(f'      Created: {order.start_date}')
                    self.stdout.write(f'      Email count: {order.abandoned_email_count}')
                    self.stdout.write(f'      Items: {order.items.count()}')
            else:
                self.stdout.write('  No matching orders found!')
                
                # Show why orders don't match
                if orders_old_enough.exists():
                    self.stdout.write('\n  Orders that are old enough but not matching:')
                    for order in orders_old_enough[:3]:
                        self.stdout.write(f'    - Order {order.reference_number}:')
                        self.stdout.write(f'      Email count: {order.abandoned_email_count} (needs {reminder["email_count"]})')
                        self.stdout.write(f'      User email: {order.user.email if order.user else "No user"}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Debug complete!')

