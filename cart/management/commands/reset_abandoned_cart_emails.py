"""
Reset abandoned cart email count for testing
Usage: python manage.py reset_abandoned_cart_emails [--all] [--order-id ORDER_ID]
"""

from django.core.management.base import BaseCommand
from cart.models import Order


class Command(BaseCommand):
    help = 'Reset abandoned cart email count for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset all abandoned carts',
        )
        parser.add_argument(
            '--order-id',
            type=str,
            help='Reset specific order by reference number',
        )

    def handle(self, *args, **options):
        if options['all']:
            orders = Order.objects.filter(ordered=False, items__isnull=False)
            count = orders.update(
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None
            )
            self.stdout.write(
                self.style.SUCCESS(f'Reset {count} abandoned cart(s)')
            )
        elif options['order_id']:
            try:
                order = Order.objects.get(reference_number=options['order_id'])
                order.abandoned_email_count = 0
                order.abandoned_email_sent = False
                order.abandoned_email_sent_at = None
                order.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reset order {order.reference_number} (email count: {order.abandoned_email_count})'
                    )
                )
            except Order.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Order {options["order_id"]} not found')
                )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --all or --order-id ORDER_ID')
            )

