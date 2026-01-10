"""
Management command to send abandoned cart emails
Usage: python manage.py send_abandoned_cart_emails
"""

from django.core.management.base import BaseCommand
from cart.scheduler import send_abandoned_cart_emails
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send abandoned cart reminder emails to users'

    def handle(self, *args, **options):
        self.stdout.write('Starting abandoned cart email check...')
        try:
            emails_sent = send_abandoned_cart_emails()
            if emails_sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully sent {emails_sent} abandoned cart email(s)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  No emails sent. Run "python manage.py check_abandoned_carts" to see why.'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )
            import traceback
            traceback.print_exc()
            raise

