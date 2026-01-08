"""
Test cases for Cart REST APIs
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from .models import Address, Order, OrderItem, Coupon, ShippingCost
from galleryItem.models import Category, GalleryItem, Variant

User = get_user_model()


class CartTestCase(TestCase):
    """Test cases for Cart API"""

    def setUp(self):
        self.client = APIClient()
        self.cart_url = '/api/cart/cart/'
        self.add_item_url = '/api/cart/cart/add-item/'
        self.clear_cart_url = '/api/cart/cart/clear/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
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
            price=Decimal('99.99'),
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )
        
        # Create another variant
        self.variant2 = Variant.objects.create(
            product=self.product,
            title='Test Variant 2',
            price=Decimal('149.99'),
            quantity=5,
            volume=150,
            weight=250,
            active=True
        )

    def test_get_cart_anonymous(self):
        """Test getting cart for anonymous user"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reference_number', response.data)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 0)

    def test_get_cart_authenticated(self):
        """Test getting cart for authenticated user"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reference_number', response.data)
        self.assertIn('items', response.data)

    def test_add_item_to_cart_success(self):
        """Test successfully adding item to cart"""
        data = {
            'variant_id': self.variant.id,
            'quantity': 2
        }
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('cart', response.data)
        self.assertEqual(len(response.data['cart']['items']), 1)
        self.assertEqual(response.data['cart']['items'][0]['quantity'], 2)

    def test_add_item_to_cart_increase_quantity(self):
        """Test adding same item again increases quantity"""
        # Add item first time
        data = {
            'variant_id': self.variant.id,
            'quantity': 1
        }
        self.client.post(self.add_item_url, data, format='json')
        
        # Add same item again
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['items']), 1)
        self.assertEqual(response.data['cart']['items'][0]['quantity'], 2)

    def test_add_item_to_cart_invalid_variant(self):
        """Test adding invalid variant to cart"""
        data = {
            'variant_id': 99999,  # Non-existent variant
            'quantity': 1
        }
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_to_cart_inactive_variant(self):
        """Test adding inactive variant to cart"""
        # Make variant inactive
        self.variant.active = False
        self.variant.save()
        
        data = {
            'variant_id': self.variant.id,
            'quantity': 1
        }
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_to_cart_out_of_stock(self):
        """Test adding out of stock variant to cart"""
        # Set quantity to 0
        self.variant.quantity = 0
        self.variant.save()
        
        data = {
            'variant_id': self.variant.id,
            'quantity': 1
        }
        response = self.client.post(self.add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_cart_item_success(self):
        """Test successfully updating cart item quantity"""
        # Add item first
        data = {
            'variant_id': self.variant.id,
            'quantity': 1
        }
        self.client.post(self.add_item_url, data, format='json')
        
        # Get cart to find item ID
        cart_response = self.client.get(self.cart_url)
        item_id = cart_response.data['items'][0]['id']
        
        # Update quantity
        update_data = {'quantity': 5}
        update_url = f'/api/cart/cart/update-item/{item_id}/'
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart']['items'][0]['quantity'], 5)

    def test_update_cart_item_invalid_id(self):
        """Test updating non-existent cart item"""
        update_data = {'quantity': 5}
        update_url = '/api/cart/cart/update-item/99999/'
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_cart_item_success(self):
        """Test successfully removing item from cart"""
        # Add item first
        data = {
            'variant_id': self.variant.id,
            'quantity': 1
        }
        self.client.post(self.add_item_url, data, format='json')
        
        # Get cart to find item ID
        cart_response = self.client.get(self.cart_url)
        item_id = cart_response.data['items'][0]['id']
        
        # Remove item
        remove_url = f'/api/cart/cart/remove-item/{item_id}/'
        response = self.client.delete(remove_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['items']), 0)

    def test_remove_cart_item_invalid_id(self):
        """Test removing non-existent cart item"""
        remove_url = '/api/cart/cart/remove-item/99999/'
        response = self.client.delete(remove_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_cart_success(self):
        """Test successfully clearing entire cart"""
        # Add multiple items
        data1 = {'variant_id': self.variant.id, 'quantity': 1}
        data2 = {'variant_id': self.variant2.id, 'quantity': 2}
        self.client.post(self.add_item_url, data1, format='json')
        self.client.post(self.add_item_url, data2, format='json')
        
        # Clear cart
        response = self.client.delete(self.clear_cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify cart is empty
        cart_response = self.client.get(self.cart_url)
        self.assertEqual(len(cart_response.data['items']), 0)


class AddressTestCase(TestCase):
    """Test cases for Address API"""

    def setUp(self):
        self.client = APIClient()
        self.address_list_url = '/api/cart/addresses/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create another user
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test address
        self.address = Address.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email_address='john@example.com',
            phone_number='1234567890',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            country='United States',
            zip_code='10001',
            address_type=Address.SHIPPING
        )

    def test_create_address_success(self):
        """Test successfully creating address"""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email_address': 'jane@example.com',
            'phone_number': '9876543210',
            'address_line_1': '456 Oak Ave',
            'city': 'Los Angeles',
            'state': 'CA',
            'country': 'United States',
            'zip_code': '90001',
            'address_type': Address.SHIPPING
        }
        response = self.client.post(self.address_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['user'], self.user.id)

    def test_create_address_missing_fields(self):
        """Test creating address with missing required fields"""
        data = {
            'first_name': 'Jane',
            # Missing other required fields
        }
        response = self.client.post(self.address_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_addresses_success(self):
        """Test successfully listing user addresses"""
        response = self.client.get(self.address_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]['id'], self.address.id)

    def test_list_addresses_unauthorized(self):
        """Test listing addresses without authentication"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(self.address_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_address_detail_success(self):
        """Test successfully getting address details"""
        url = f'{self.address_list_url}{self.address.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['id'], self.address.id)

    def test_get_address_detail_other_user(self):
        """Test getting address of another user (should fail)"""
        # Create address for user2
        address2 = Address.objects.create(
            user=self.user2,
            first_name='Other',
            last_name='User',
            email_address='other@example.com',
            phone_number='1111111111',
            address_line_1='789 Pine St',
            city='Chicago',
            state='IL',
            country='United States',
            zip_code='60601',
            address_type=Address.SHIPPING
        )
        
        url = f'{self.address_list_url}{address2.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_address_success(self):
        """Test successfully updating address"""
        url = f'{self.address_list_url}{self.address.id}/'
        data = {
            'first_name': 'John Updated',
            'last_name': 'Doe',
            'email_address': 'john@example.com',
            'phone_number': '1234567890',
            'address_line_1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'country': 'United States',
            'zip_code': '10001',
            'address_type': Address.SHIPPING
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John Updated')

    def test_delete_address_success(self):
        """Test successfully deleting address"""
        url = f'{self.address_list_url}{self.address.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify address is deleted
        self.assertFalse(Address.objects.filter(id=self.address.id).exists())


class OrderTestCase(TestCase):
    """Test cases for Order API"""

    def setUp(self):
        self.client = APIClient()
        self.order_list_url = '/api/cart/orders/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create another user
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
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
            price=Decimal('99.99'),
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )
        
        # Create finalized order for user
        self.order = Order.objects.create(
            user=self.user,
            ordered=True,
            status=Order.ORDERED
        )
        OrderItem.objects.create(
            order=self.order,
            variant=self.variant,
            quantity=2
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_orders_success(self):
        """Test successfully listing user orders"""
        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]['id'], self.order.id)

    def test_list_orders_unauthorized(self):
        """Test listing orders without authentication"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_order_detail_success(self):
        """Test successfully getting order details"""
        url = f'{self.order_list_url}{self.order.reference_number}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)
        self.assertIn('items', response.data)

    def test_get_order_detail_invalid_reference(self):
        """Test getting order with invalid reference number"""
        url = f'{self.order_list_url}INVALID-REF-123/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CouponTestCase(TestCase):
    """Test cases for Coupon API"""

    def setUp(self):
        self.client = APIClient()
        self.apply_coupon_url = '/api/cart/coupons/apply/'
        self.remove_coupon_url = '/api/cart/coupons/remove/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
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
            price=Decimal('100.00'),  # Set price to meet minimum
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )
        
        # Create coupon
        self.coupon = Coupon.objects.create(
            title='Test Coupon',
            code='TEST10',
            discount=Decimal('10.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('50.00'),
            single_use_per_user=False,
            active=True
        )
        
        # Create order with items
        self.order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=self.order,
            variant=self.variant,
            quantity=1
        )

    def test_apply_coupon_success(self):
        """Test successfully applying coupon"""
        # Set order in session (simulate)
        session = self.client.session
        session['order_id'] = self.order.id
        session.save()
        
        # Verify order has items and subtotal
        self.order.refresh_from_db()
        self.assertTrue(self.order.items.exists())
        self.assertGreaterEqual(self.order.get_raw_subtotal(), Decimal('50.00'))
        
        data = {'code': 'TEST10'}
        response = self.client.post(self.apply_coupon_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('coupon_discount_amount', response.data)

    def test_apply_coupon_invalid_code(self):
        """Test applying invalid coupon code"""
        self.client.session['order_id'] = self.order.id
        self.client.session.save()
        
        data = {'code': 'INVALID'}
        response = self.client.post(self.apply_coupon_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_apply_coupon_below_minimum(self):
        """Test applying coupon when order is below minimum amount"""
        # Create coupon with high minimum
        high_min_coupon = Coupon.objects.create(
            title='High Min Coupon',
            code='HIGHMIN',
            discount=Decimal('20.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('500.00'),
            single_use_per_user=False,
            active=True
        )
        
        self.client.session['order_id'] = self.order.id
        self.client.session.save()
        
        data = {'code': 'HIGHMIN'}
        response = self.client.post(self.apply_coupon_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_remove_coupon_success(self):
        """Test successfully removing coupon"""
        # Apply coupon first
        self.order.coupon = self.coupon
        self.order.save()
        
        session = self.client.session
        session['order_id'] = self.order.id
        session.save()
        
        response = self.client.delete(self.remove_coupon_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify coupon is removed
        self.order.refresh_from_db()
        self.assertIsNone(self.order.coupon)


class AdminCouponTestCase(TestCase):
    """Test cases for Admin Coupon API"""

    def setUp(self):
        self.client = APIClient()
        self.admin_coupon_list_url = '/api/cart/admin/coupons/'
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPass123!'
        )
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_coupons_admin_success(self):
        """Test admin successfully listing all coupons"""
        # Create some coupons
        Coupon.objects.create(
            title='Coupon 1',
            code='CODE1',
            discount=Decimal('10.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('50.00'),
            single_use_per_user=False,
            active=True
        )
        
        response = self.client.get(self.admin_coupon_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_list_coupons_non_admin(self):
        """Test non-admin cannot list coupons"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.admin_coupon_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_coupon_admin_success(self):
        """Test admin successfully creating coupon"""
        data = {
            'title': 'New Coupon',
            'code': 'NEWCODE',
            'discount': Decimal('15.00'),
            'discount_type': Coupon.DiscountType.PERCENTAGE,
            'minimum_order_amount': Decimal('100.00'),
            'single_use_per_user': True,
            'active': True
        }
        response = self.client.post(self.admin_coupon_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'NEWCODE')

    def test_get_coupon_detail_admin_success(self):
        """Test admin successfully getting coupon details"""
        coupon = Coupon.objects.create(
            title='Test Coupon',
            code='TEST',
            discount=Decimal('10.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('50.00'),
            single_use_per_user=False,
            active=True
        )
        
        url = f'{self.admin_coupon_list_url}{coupon.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], coupon.id)

    def test_update_coupon_admin_success(self):
        """Test admin successfully updating coupon"""
        coupon = Coupon.objects.create(
            title='Test Coupon',
            code='TEST',
            discount=Decimal('10.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('50.00'),
            single_use_per_user=False,
            active=True
        )
        
        url = f'{self.admin_coupon_list_url}{coupon.id}/'
        data = {
            'title': 'Updated Coupon',
            'code': 'TEST',
            'discount': Decimal('20.00'),
            'discount_type': Coupon.DiscountType.FIXED_AMOUNT,
            'minimum_order_amount': Decimal('50.00'),
            'single_use_per_user': False,
            'active': True
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['discount'], '20.00')

    def test_delete_coupon_admin_success(self):
        """Test admin successfully deleting coupon"""
        coupon = Coupon.objects.create(
            title='Test Coupon',
            code='TEST',
            discount=Decimal('10.00'),
            discount_type=Coupon.DiscountType.FIXED_AMOUNT,
            minimum_order_amount=Decimal('50.00'),
            single_use_per_user=False,
            active=True
        )
        
        url = f'{self.admin_coupon_list_url}{coupon.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify coupon is deleted
        self.assertFalse(Coupon.objects.filter(id=coupon.id).exists())