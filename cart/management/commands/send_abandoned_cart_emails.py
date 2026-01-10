"""
Management command to send abandoned cart emails
Usage: python manage.py send_abandoned_cart_emails
"""

from django.core.management.base import BaseCommand
from cart.scheduler import send_abandoned_cart_emails


class Command(BaseCommand):
    help = 'Send abandoned cart reminder emails to users'

    def handle(self, *args, **options):
        try:
            emails_sent = send_abandoned_cart_emails()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent {emails_sent} abandoned cart email(s)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            import traceback
            traceback.print_exc()
            raise

