from django.core.management.base import BaseCommand
from NEW_tax_calculator.utils import NEW_create_default_tax_rates

class Command(BaseCommand):
    help = 'NEW: Populate default US tax rates'

    def handle(self, *args, **options):
        self.stdout.write('Creating default US tax rates...')
        
        created_count = NEW_create_default_tax_rates()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} default tax rates!')
        )

