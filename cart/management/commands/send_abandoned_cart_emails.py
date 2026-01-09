"""
Management command to send abandoned cart emails
This can be run via cron job or scheduled task on PythonAnywhere
Usage: python manage.py send_abandoned_cart_emails
"""

from django.core.management.base import BaseCommand
from cart.scheduler import send_abandoned_cart_emails


class Command(BaseCommand):
    help = 'Send abandoned cart reminder emails to users'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Starting abandoned cart email check...')
        try:
            emails_sent = send_abandoned_cart_emails()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✨ Successfully sent {emails_sent} abandoned cart email(s)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error sending abandoned cart emails: {e}')
            )
            import traceback
            traceback.print_exc()
            raise

