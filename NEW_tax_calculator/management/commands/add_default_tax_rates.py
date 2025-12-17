"""
Django management command to add default tax rates for US states and cities
Run: python manage.py add_default_tax_rates
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date

from NEW_tax_calculator.models import Country, State, City, NEW_TaxRate


class Command(BaseCommand):
    help = 'Add default tax rates for US states and cities'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to add default tax rates...'))
        
        # Get or create United States
        country, created = Country.objects.get_or_create(name='United States')
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created country: {country.name}'))
        else:
            self.stdout.write(f'Country already exists: {country.name}')
        
        # Tax rates data: State -> Cities -> Rates
        tax_data = {
            'California': {
                'state_rate': Decimal('0.0875'),  # 8.75%
                'cities': {
                    'Los Angeles': Decimal('0.0900'),  # 9.00%
                    'San Francisco': Decimal('0.0850'),  # 8.50%
                    'San Diego': Decimal('0.0800'),  # 8.00%
                    'Sacramento': Decimal('0.0825'),  # 8.25%
                    'San Jose': Decimal('0.0925'),  # 9.25%
                }
            },
            'New York': {
                'state_rate': Decimal('0.0800'),  # 8.00%
                'cities': {
                    'New York City': Decimal('0.0888'),  # 8.88%
                    'Buffalo': Decimal('0.0825'),  # 8.25%
                    'Rochester': Decimal('0.0800'),  # 8.00%
                    'Albany': Decimal('0.0800'),  # 8.00%
                    'Syracuse': Decimal('0.0800'),  # 8.00%
                }
            },
            'Texas': {
                'state_rate': Decimal('0.0625'),  # 6.25%
                'cities': {
                    'Houston': Decimal('0.0825'),  # 8.25%
                    'Dallas': Decimal('0.0825'),  # 8.25%
                    'Austin': Decimal('0.0825'),  # 8.25%
                    'San Antonio': Decimal('0.0825'),  # 8.25%
                    'Fort Worth': Decimal('0.0825'),  # 8.25%
                }
            },
            'Florida': {
                'state_rate': Decimal('0.0600'),  # 6.00%
                'cities': {
                    'Miami': Decimal('0.0700'),  # 7.00%
                    'Tampa': Decimal('0.0700'),  # 7.00%
                    'Orlando': Decimal('0.0650'),  # 6.50%
                    'Jacksonville': Decimal('0.0700'),  # 7.00%
                    'Fort Lauderdale': Decimal('0.0700'),  # 7.00%
                }
            },
            'Illinois': {
                'state_rate': Decimal('0.0625'),  # 6.25%
                'cities': {
                    'Chicago': Decimal('0.1025'),  # 10.25%
                    'Aurora': Decimal('0.0825'),  # 8.25%
                    'Naperville': Decimal('0.0825'),  # 8.25%
                    'Joliet': Decimal('0.0825'),  # 8.25%
                    'Rockford': Decimal('0.0825'),  # 8.25%
                }
            },
            'Arizona': {
                'state_rate': Decimal('0.0560'),  # 5.60%
                'cities': {
                    'Phoenix': Decimal('0.0860'),  # 8.60%
                    'Tucson': Decimal('0.0860'),  # 8.60%
                    'Mesa': Decimal('0.0860'),  # 8.60%
                    'Chandler': Decimal('0.0860'),  # 8.60%
                    'Scottsdale': Decimal('0.0860'),  # 8.60%
                }
            },
        }
        
        total_created = 0
        total_updated = 0
        
        # Process each state
        for state_name, state_data in tax_data.items():
            # Get or create state
            state, created = State.objects.get_or_create(
                name=state_name,
                country=country,
                defaults={'name': state_name, 'country': country}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created state: {state.name}'))
            else:
                self.stdout.write(f'  State already exists: {state.name}')
            
            # Add state-level tax rate
            state_rate_obj, created = NEW_TaxRate.objects.get_or_create(
                country=country,
                state=state,
                city=None,
                defaults={
                    'rate': state_data['state_rate'],
                    'tax_type': 'sales',
                    'effective_date': date.today(),
                    'is_active': True,
                }
            )
            if created:
                total_created += 1
                self.stdout.write(self.style.SUCCESS(f'    [OK] Added state rate: {state.name} - {state_data["state_rate"] * 100:.2f}%'))
            else:
                # Update if exists
                state_rate_obj.rate = state_data['state_rate']
                state_rate_obj.is_active = True
                state_rate_obj.save()
                total_updated += 1
                self.stdout.write(f'    [UPDATED] Updated state rate: {state.name} - {state_data["state_rate"] * 100:.2f}%')
            
            # Add city-level tax rates
            for city_name, city_rate in state_data['cities'].items():
                # Get or create city
                city, created = City.objects.get_or_create(
                    name=city_name,
                    state=state,
                    defaults={'name': city_name, 'state': state}
                )
                if created:
                    self.stdout.write(f'      Created city: {city.name}')
                
                # Add city-level tax rate
                city_rate_obj, created = NEW_TaxRate.objects.get_or_create(
                    country=country,
                    state=state,
                    city=city,
                    defaults={
                        'rate': city_rate,
                        'tax_type': 'sales',
                        'effective_date': date.today(),
                        'is_active': True,
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'        [OK] Added city rate: {city.name} - {city_rate * 100:.2f}%'))
                else:
                    # Update if exists
                    city_rate_obj.rate = city_rate
                    city_rate_obj.is_active = True
                    city_rate_obj.save()
                    total_updated += 1
                    self.stdout.write(f'        [UPDATED] Updated city rate: {city.name} - {city_rate * 100:.2f}%')
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Total tax rates created: {total_created}'))
        self.stdout.write(self.style.SUCCESS(f'Total tax rates updated: {total_updated}'))
        self.stdout.write('')
        
        # Count total rates
        total_rates = NEW_TaxRate.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f'Total active tax rates in database: {total_rates}'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[SUCCESS] Default tax rates added successfully!'))
        self.stdout.write('')
        self.stdout.write('You can now test tax calculation with:')
        self.stdout.write('  - Country: United States')
        self.stdout.write('  - State: California, New York, Texas, Florida, Illinois, Arizona')
        self.stdout.write('  - Cities: Los Angeles, New York City, Houston, Miami, Chicago, Phoenix, etc.')

