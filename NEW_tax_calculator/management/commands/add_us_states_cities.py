"""
Django management command to add all US states and their cities to the database
This helps in tax rate management and address selection
"""
from django.core.management.base import BaseCommand
from NEW_tax_calculator.models import Country, State, City


class Command(BaseCommand):
    help = 'Adds all US states and their major cities to the database'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Adding United States States and Cities')
        self.stdout.write('=' * 60)
        
        # Get or create United States country
        country, created = Country.objects.get_or_create(
            name='United States',
            defaults={'code': 'US'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created country: {country.name}'))
        else:
            self.stdout.write(f'Country already exists: {country.name}')
        
        # US States with their major cities
        us_states_cities = {
            'Alabama': ['Birmingham', 'Montgomery', 'Mobile', 'Huntsville', 'Tuscaloosa'],
            'Alaska': ['Anchorage', 'Fairbanks', 'Juneau', 'Sitka', 'Ketchikan'],
            'Arizona': ['Phoenix', 'Tucson', 'Mesa', 'Chandler', 'Scottsdale', 'Glendale', 'Tempe', 'Peoria'],
            'Arkansas': ['Little Rock', 'Fort Smith', 'Fayetteville', 'Springdale', 'Jonesboro'],
            'California': ['Los Angeles', 'San Diego', 'San Jose', 'San Francisco', 'Fresno', 'Sacramento', 'Long Beach', 'Oakland', 'Bakersfield', 'Anaheim', 'Santa Ana', 'Riverside', 'Stockton', 'Irvine', 'Chula Vista', 'Fremont', 'San Bernardino', 'Modesto', 'Fontana', 'Oxnard'],
            'Colorado': ['Denver', 'Colorado Springs', 'Aurora', 'Fort Collins', 'Lakewood', 'Thornton', 'Arvada', 'Westminster'],
            'Connecticut': ['Bridgeport', 'New Haven', 'Hartford', 'Stamford', 'Waterbury', 'Norwalk', 'Danbury'],
            'Delaware': ['Wilmington', 'Dover', 'Newark', 'Middletown', 'Smyrna'],
            'Florida': ['Jacksonville', 'Miami', 'Tampa', 'Orlando', 'St. Petersburg', 'Hialeah', 'Tallahassee', 'Fort Lauderdale', 'Port St. Lucie', 'Cape Coral', 'Pembroke Pines', 'Hollywood', 'Miramar', 'Gainesville', 'Coral Springs'],
            'Georgia': ['Atlanta', 'Augusta', 'Columbus', 'Savannah', 'Athens', 'Sandy Springs', 'Roswell', 'Macon', 'Johns Creek', 'Albany'],
            'Hawaii': ['Honolulu', 'Hilo', 'Kailua', 'Kaneohe', 'Kahului'],
            'Idaho': ['Boise', 'Nampa', 'Meridian', 'Idaho Falls', 'Pocatello'],
            'Illinois': ['Chicago', 'Aurora', 'Rockford', 'Joliet', 'Naperville', 'Springfield', 'Peoria', 'Elgin', 'Waukegan', 'Cicero', 'Champaign', 'Bloomington'],
            'Indiana': ['Indianapolis', 'Fort Wayne', 'Evansville', 'South Bend', 'Carmel', 'Fishers', 'Bloomington', 'Hammond'],
            'Iowa': ['Des Moines', 'Cedar Rapids', 'Davenport', 'Sioux City', 'Iowa City', 'Waterloo'],
            'Kansas': ['Wichita', 'Overland Park', 'Kansas City', 'Olathe', 'Topeka', 'Lawrence'],
            'Kentucky': ['Louisville', 'Lexington', 'Bowling Green', 'Owensboro', 'Covington', 'Hopkinsville'],
            'Louisiana': ['New Orleans', 'Baton Rouge', 'Shreveport', 'Lafayette', 'Lake Charles', 'Kenner', 'Bossier City'],
            'Maine': ['Portland', 'Lewiston', 'Bangor', 'South Portland', 'Auburn'],
            'Maryland': ['Baltimore', 'Frederick', 'Rockville', 'Gaithersburg', 'Bowie', 'Annapolis', 'College Park'],
            'Massachusetts': ['Boston', 'Worcester', 'Springfield', 'Lowell', 'Cambridge', 'New Bedford', 'Brockton', 'Quincy', 'Lynn', 'Fall River'],
            'Michigan': ['Detroit', 'Grand Rapids', 'Warren', 'Sterling Heights', 'Lansing', 'Ann Arbor', 'Flint', 'Dearborn', 'Livonia', 'Troy'],
            'Minnesota': ['Minneapolis', 'St. Paul', 'Rochester', 'Duluth', 'Bloomington', 'Brooklyn Park', 'Plymouth', 'St. Cloud'],
            'Mississippi': ['Jackson', 'Gulfport', 'Southaven', 'Hattiesburg', 'Biloxi', 'Meridian'],
            'Missouri': ['Kansas City', 'St. Louis', 'Springfield', 'Columbia', 'Independence', 'Lee\'s Summit', 'O\'Fallon', 'St. Joseph'],
            'Montana': ['Billings', 'Missoula', 'Great Falls', 'Bozeman', 'Butte'],
            'Nebraska': ['Omaha', 'Lincoln', 'Bellevue', 'Grand Island', 'Kearney'],
            'Nevada': ['Las Vegas', 'Henderson', 'Reno', 'North Las Vegas', 'Sparks', 'Carson City'],
            'New Hampshire': ['Manchester', 'Nashua', 'Concord', 'Derry', 'Rochester'],
            'New Jersey': ['Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison', 'Woodbridge', 'Lakewood', 'Toms River', 'Hamilton', 'Trenton'],
            'New Mexico': ['Albuquerque', 'Las Cruces', 'Rio Rancho', 'Santa Fe', 'Roswell'],
            'New York': ['New York', 'Buffalo', 'Rochester', 'Yonkers', 'Syracuse', 'Albany', 'New Rochelle', 'Mount Vernon', 'Schenectady', 'Utica', 'White Plains', 'Hempstead', 'Troy'],
            'North Carolina': ['Charlotte', 'Raleigh', 'Greensboro', 'Durham', 'Winston-Salem', 'Fayetteville', 'Cary', 'Wilmington', 'High Point', 'Concord'],
            'North Dakota': ['Fargo', 'Bismarck', 'Grand Forks', 'Minot', 'West Fargo'],
            'Ohio': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo', 'Akron', 'Dayton', 'Parma', 'Canton', 'Youngstown', 'Lorain'],
            'Oklahoma': ['Oklahoma City', 'Tulsa', 'Norman', 'Broken Arrow', 'Lawton', 'Edmond', 'Moore'],
            'Oregon': ['Portland', 'Eugene', 'Salem', 'Gresham', 'Hillsboro', 'Bend', 'Beaverton', 'Medford'],
            'Pennsylvania': ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie', 'Reading', 'Scranton', 'Bethlehem', 'Lancaster', 'Harrisburg', 'Altoona'],
            'Rhode Island': ['Providence', 'Warwick', 'Cranston', 'Pawtucket', 'East Providence'],
            'South Carolina': ['Charleston', 'Columbia', 'North Charleston', 'Mount Pleasant', 'Rock Hill', 'Greenville', 'Summerville', 'Sumter'],
            'South Dakota': ['Sioux Falls', 'Rapid City', 'Aberdeen', 'Brookings', 'Watertown'],
            'Tennessee': ['Nashville', 'Memphis', 'Knoxville', 'Chattanooga', 'Clarksville', 'Murfreesboro', 'Franklin', 'Jackson'],
            'Texas': ['Houston', 'San Antonio', 'Dallas', 'Austin', 'Fort Worth', 'El Paso', 'Arlington', 'Corpus Christi', 'Plano', 'Laredo', 'Lubbock', 'Garland', 'Irving', 'Amarillo', 'Grand Prairie', 'Brownsville', 'McKinney', 'Frisco', 'Pasadena', 'Killeen'],
            'Utah': ['Salt Lake City', 'West Valley City', 'Provo', 'West Jordan', 'Orem', 'Sandy', 'Ogden', 'St. George'],
            'Vermont': ['Burlington', 'Essex', 'South Burlington', 'Colchester', 'Montpelier'],
            'Virginia': ['Virginia Beach', 'Norfolk', 'Chesapeake', 'Richmond', 'Newport News', 'Alexandria', 'Hampton', 'Portsmouth', 'Suffolk', 'Roanoke'],
            'Washington': ['Seattle', 'Spokane', 'Tacoma', 'Vancouver', 'Bellevue', 'Everett', 'Kent', 'Yakima', 'Renton', 'Spokane Valley'],
            'West Virginia': ['Charleston', 'Huntington', 'Parkersburg', 'Morgantown', 'Wheeling'],
            'Wisconsin': ['Milwaukee', 'Madison', 'Green Bay', 'Kenosha', 'Racine', 'Appleton', 'Waukesha', 'Oshkosh', 'Eau Claire', 'Janesville'],
            'Wyoming': ['Cheyenne', 'Casper', 'Laramie', 'Gillette', 'Rock Springs'],
        }
        
        total_states = 0
        total_cities = 0
        created_states = 0
        created_cities = 0
        
        for state_name, cities_list in us_states_cities.items():
            # Get or create state
            state, state_created = State.objects.get_or_create(
                name=state_name,
                country=country
            )
            
            if state_created:
                created_states += 1
                self.stdout.write(self.style.SUCCESS(f'Created state: {state_name}'))
            else:
                self.stdout.write(f'State already exists: {state_name}')
            
            total_states += 1
            
            # Add cities for this state
            for city_name in cities_list:
                city, city_created = City.objects.get_or_create(
                    name=city_name,
                    state=state,
                    defaults={}
                )
                
                if city_created:
                    created_cities += 1
                    total_cities += 1
                else:
                    total_cities += 1
            
            self.stdout.write(f'  Added {len(cities_list)} cities for {state_name}')
        
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Completed Successfully!'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total States: {total_states} (Created: {created_states}, Existing: {total_states - created_states})')
        self.stdout.write(f'Total Cities: {total_cities} (Created: {created_cities}, Existing: {total_cities - created_cities})')
        self.stdout.write('')
        self.stdout.write('Now you can add tax rates for any US state/city in Django Admin!')
        self.stdout.write('Go to: Admin -> NEW_Tax Calculator -> NEW Tax Rates -> Add New Tax Rate')

