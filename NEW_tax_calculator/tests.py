"""
Test cases for Tax Calculator REST APIs
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from .models import Country, State, City, NEW_TaxRate, NEW_TaxExemption
from cart.models import Order, OrderItem, Address
from galleryItem.models import Category, GalleryItem, Variant

User = get_user_model()


class TaxCalculatorAPITestCase(TestCase):
    """Test cases for Tax Calculator API"""

    def setUp(self):
        self.client = APIClient()
        self.calculate_tax_url = '/api/tax/calculate/'
        self.update_address_url = '/api/tax/update-address/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create country, state, city
        self.country = Country.objects.create(name='United States')
        self.state = State.objects.create(name='California', country=self.country)
        self.city = City.objects.create(name='San Francisco', state=self.state)
        
        # Create tax rates
        self.state_tax_rate = NEW_TaxRate.objects.create(
            country=self.country,
            state=self.state,
            city=None,
            rate=Decimal('0.0875'),  # 8.75%
            tax_type='sales',
            effective_date=date.today() - timedelta(days=30),
            is_active=True
        )
        
        self.city_tax_rate = NEW_TaxRate.objects.create(
            country=self.country,
            state=self.state,
            city=self.city,
            rate=Decimal('0.0900'),  # 9.00%
            tax_type='sales',
            effective_date=date.today() - timedelta(days=30),
            is_active=True
        )
        
        # Create category and product for cart
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description'
        )
        
        self.product = GalleryItem.objects.create(
            title='Test Product',
            description='Test Product Description',
            category=self.category,
            active=True
        )
        
        self.variant = Variant.objects.create(
            product=self.product,
            title='Test Variant',
            price=Decimal('100.00'),
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )

    def test_calculate_tax_with_country_state(self):
        """Test calculating tax with country and state only"""
        data = {
            'country': 'United States',
            'state': 'California',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['tax_amount'], 8.75)  # 100 * 0.0875
        self.assertEqual(response.data['tax_rate'], '8.75%')
        self.assertEqual(response.data['tax_rate_decimal'], 0.0875)
        self.assertEqual(response.data['subtotal'], 100.0)
        self.assertEqual(response.data['grand_total'], 108.75)
        self.assertFalse(response.data['is_exempt'])

    def test_calculate_tax_with_city(self):
        """Test calculating tax with city (should use city rate)"""
        data = {
            'country': 'United States',
            'state': 'California',
            'city': 'San Francisco',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Should use city rate (9.00%) instead of state rate (8.75%)
        self.assertEqual(response.data['tax_amount'], 9.0)  # 100 * 0.0900
        self.assertEqual(response.data['tax_rate'], '9.00%')
        self.assertEqual(response.data['tax_rate_decimal'], 0.09)

    def test_calculate_tax_missing_country(self):
        """Test calculating tax with missing country"""
        data = {
            'state': 'California',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)

    def test_calculate_tax_missing_state(self):
        """Test calculating tax with missing state"""
        data = {
            'country': 'United States',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)

    def test_calculate_tax_no_rate_found(self):
        """Test calculating tax when no rate is found"""
        data = {
            'country': 'United States',
            'state': 'Texas',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['tax_amount'], 0.0)
        self.assertEqual(response.data['tax_rate'], '0.00%')
        self.assertIn('message', response.data)

    def test_calculate_tax_with_order_subtotal(self):
        """Test calculating tax using order subtotal (no subtotal provided)"""
        # Create order with items
        order = Order.objects.create(user=None)
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=2
        )
        
        # Set order in session
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        
        data = {
            'country': 'United States',
            'state': 'California'
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Subtotal should be 200.00 (2 * 100.00)
        self.assertEqual(response.data['subtotal'], 200.0)
        self.assertEqual(response.data['tax_amount'], 17.5)  # 200 * 0.0875

    def test_calculate_tax_tax_exempt_user(self):
        """Test calculating tax for tax exempt user"""
        # Create tax exemption for user
        NEW_TaxExemption.objects.create(
            user=self.user,
            is_exempt=True,
            exemption_type='nonprofit',
            effective_date=date.today() - timedelta(days=30)
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
        
        data = {
            'country': 'United States',
            'state': 'California',
            'subtotal': 100.00
        }
        response = self.client.post(self.calculate_tax_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['tax_amount'], 0.0)
        self.assertTrue(response.data['is_exempt'])
        self.assertIn('exemption_reason', response.data)


class UpdateAddressTaxAPITestCase(TestCase):
    """Test cases for Update Address and Calculate Tax API"""

    def setUp(self):
        self.client = APIClient()
        self.update_address_url = '/api/tax/update-address/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create country, state, city
        self.country = Country.objects.create(name='United States')
        self.state = State.objects.create(name='California', country=self.country)
        self.city = City.objects.create(name='San Francisco', state=self.state)
        
        # Create tax rate
        self.tax_rate = NEW_TaxRate.objects.create(
            country=self.country,
            state=self.state,
            city=None,
            rate=Decimal('0.0875'),  # 8.75%
            tax_type='sales',
            effective_date=date.today() - timedelta(days=30),
            is_active=True
        )
        
        # Create category and product
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description'
        )
        
        self.product = GalleryItem.objects.create(
            title='Test Product',
            description='Test Product Description',
            category=self.category,
            active=True
        )
        
        self.variant = Variant.objects.create(
            product=self.product,
            title='Test Variant',
            price=Decimal('100.00'),
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )

    def test_update_address_and_calculate_tax(self):
        """Test updating address and calculating tax"""
        # Create order with items
        order = Order.objects.create(user=None)
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=2
        )
        
        # Set order in session
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        
        data = {
            'country': 'United States',
            'state': 'California',
            'city': 'San Francisco',
            'zip_code': '94102',
            'address_line_1': '123 Main St',
            'first_name': 'John',
            'last_name': 'Doe',
            'email_address': 'john@example.com',
            'phone_number': '123-456-7890'
        }
        response = self.client.post(self.update_address_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('order_id', response.data)
        self.assertIn('tax_amount', response.data)
        self.assertIn('tax_rate', response.data)
        self.assertIn('subtotal', response.data)
        self.assertIn('shipping_cost', response.data)
        self.assertIn('grand_total', response.data)
        
        # Verify address was created
        order.refresh_from_db()
        self.assertIsNotNone(order.shipping_address)
        self.assertEqual(order.shipping_address.country, 'United States')
        self.assertEqual(order.shipping_address.state, 'California')
        self.assertEqual(order.shipping_address.city, 'San Francisco')
        
        # Verify tax was calculated
        self.assertGreater(float(order.tax_amount), 0)

    def test_update_address_empty_cart(self):
        """Test updating address with empty cart"""
        # Create empty order
        order = Order.objects.create(user=None)
        
        # Set order in session
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        
        data = {
            'country': 'United States',
            'state': 'California'
        }
        response = self.client.post(self.update_address_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
        self.assertIn('empty', response.data['error'].lower())

    def test_update_address_missing_required_fields(self):
        """Test updating address with missing required fields"""
        # Create order with items
        order = Order.objects.create(user=None)
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=1
        )
        
        # Set order in session
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        
        data = {
            'state': 'California'  # Missing country
        }
        response = self.client.post(self.update_address_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)

    def test_update_existing_address(self):
        """Test updating existing shipping address"""
        # Create order with items and existing address
        order = Order.objects.create(user=None)
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=1
        )
        
        address = Address.objects.create(
            country='United States',
            state='New York',
            city='New York',
            zip_code='10001',
            address_line_1='Old Address',
            first_name='Old',
            last_name='Name',
            email_address='old@example.com',
            phone_number='111-111-1111',
            address_type=Address.SHIPPING
        )
        order.shipping_address = address
        order.save()
        
        # Set order in session
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        
        data = {
            'country': 'United States',
            'state': 'California',
            'city': 'San Francisco',
            'zip_code': '94102',
            'address_line_1': 'New Address',
            'first_name': 'New',
            'last_name': 'Name'
        }
        response = self.client.post(self.update_address_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify address was updated
        address.refresh_from_db()
        self.assertEqual(address.state, 'California')
        self.assertEqual(address.city, 'San Francisco')
        self.assertEqual(address.address_line_1, 'New Address')
        self.assertEqual(address.first_name, 'New')


class LocationAPITestCase(TestCase):
    """Test cases for Location APIs (Countries, States, Cities)"""

    def setUp(self):
        self.client = APIClient()
        self.countries_url = '/api/tax/countries/'
        
        # Create test data
        self.country1 = Country.objects.create(name='United States')
        self.country2 = Country.objects.create(name='Canada')
        
        self.state1 = State.objects.create(name='California', country=self.country1)
        self.state2 = State.objects.create(name='New York', country=self.country1)
        
        self.city1 = City.objects.create(name='San Francisco', state=self.state1)
        self.city2 = City.objects.create(name='Los Angeles', state=self.state1)

    def test_get_countries(self):
        """Test getting list of countries"""
        response = self.client.get(self.countries_url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('countries', data)
        self.assertEqual(len(data['countries']), 2)
        # Check that both countries are in the list
        country_names = [c['name'] for c in data['countries']]
        self.assertIn('Canada', country_names)
        self.assertIn('United States', country_names)

    def test_get_states(self):
        """Test getting list of states for a country"""
        url = f'/api/tax/states/{self.country1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('states', data)
        self.assertEqual(len(data['states']), 2)

    def test_get_cities(self):
        """Test getting list of cities for a state"""
        url = f'/api/tax/cities/{self.state1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('cities', data)
        self.assertEqual(len(data['cities']), 2)
