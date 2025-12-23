from django.core.management.base import BaseCommand
from NEW_wholesale_discounts.utils import NEW_create_default_wholesale_tiers

class Command(BaseCommand):
    help = 'NEW: Populate default wholesale tiers'

    def handle(self, *args, **options):
        self.stdout.write('Creating default wholesale tiers...')
        
        created_count = NEW_create_default_wholesale_tiers()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} default wholesale tiers!')
        )

