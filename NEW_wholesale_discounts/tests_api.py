"""
API Test Cases for Wholesale Discount System
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import (
    NEW_WholesaleRequest,
    NEW_WholesaleUser,
    NEW_WholesaleDiscountConfig
)

User = get_user_model()


class WholesaleAPITestCase(TestCase):
    """Test cases for Wholesale API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create wholesale discount config
        self.config = NEW_WholesaleDiscountConfig.objects.create(
            name='Test Config',
            threshold_1=Decimal('500.00'),
            discount_1=Decimal('10.00'),
            threshold_2=Decimal('1000.00'),
            discount_2=Decimal('15.00'),
            threshold_3=Decimal('2000.00'),
            discount_3=Decimal('20.00'),
            threshold_4=Decimal('2500.00'),
            discount_4=Decimal('25.00'),
            is_active=True
        )
    
    def test_get_wholesale_status_unauthenticated(self):
        """Test getting wholesale status without authentication"""
        response = self.client.get('/api/wholesale/status/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_wholesale_status_authenticated(self):
        """Test getting wholesale status for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/wholesale/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_wholesale'])
        self.assertFalse(response.data['has_pending_request'])
        self.assertFalse(response.data['has_approved_request'])
    
    def test_create_wholesale_request(self):
        """Test creating a wholesale request"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'business_name': 'Test Business',
            'business_type': 'retailer',
            'tax_id': '12-3456789',
            'website': 'https://testbusiness.com',
            'expected_monthly_volume': '5000',
            'reason': 'I need wholesale access for my retail store.'
        }
        
        response = self.client.post('/api/wholesale/request/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['business_name'], 'Test Business')
        self.assertEqual(response.data['status'], 'pending')
    
    def test_create_duplicate_wholesale_request(self):
        """Test creating duplicate wholesale request"""
        self.client.force_authenticate(user=self.user)
        
        # Create first request
        data = {
            'business_name': 'Test Business',
            'business_type': 'retailer',
            'expected_monthly_volume': '5000',
            'reason': 'I need wholesale access.'
        }
        self.client.post('/api/wholesale/request/', data, format='multipart')
        
        # Try to create second request
        response = self.client.post('/api/wholesale/request/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already have a pending', str(response.data))
    
    def test_list_wholesale_requests(self):
        """Test listing user's wholesale requests"""
        self.client.force_authenticate(user=self.user)
        
        # Create a request
        NEW_WholesaleRequest.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='retailer',
            expected_monthly_volume='5000',
            reason='Test reason'
        )
        
        response = self.client.get('/api/wholesale/requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['business_name'], 'Test Business')
    
    def test_get_wholesale_tiers(self):
        """Test getting wholesale discount tiers"""
        response = self.client.get('/api/wholesale/tiers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('config', response.data)
        self.assertEqual(len(response.data['config']['tiers']), 4)
    
    def test_calculate_discount_not_wholesale(self):
        """Test calculating discount for non-wholesale user"""
        self.client.force_authenticate(user=self.user)
        
        data = {'amount': '1500.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_wholesale'])
        self.assertEqual(float(response.data['discount_amount']), 0.00)
    
    def test_calculate_discount_wholesale_user(self):
        """Test calculating discount for wholesale user"""
        # Create wholesale user
        NEW_WholesaleUser.objects.create(
            user=self.user,
            is_wholesale=True
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Test with amount above threshold_2
        data = {'amount': '1500.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_wholesale'])
        # 15% of 1500 = 225
        self.assertEqual(float(response.data['discount_amount']), 225.00)
        self.assertEqual(float(response.data['discount_percentage']), 15.00)
    
    def test_admin_list_requests(self):
        """Test admin listing all wholesale requests"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create requests for different users
        NEW_WholesaleRequest.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='retailer',
            expected_monthly_volume='5000',
            reason='Test reason'
        )
        
        response = self.client.get('/api/wholesale/admin/requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_admin_approve_request(self):
        """Test admin approving a wholesale request"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create request
        request_obj = NEW_WholesaleRequest.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='retailer',
            expected_monthly_volume='5000',
            reason='Test reason'
        )
        
        # Approve request
        data = {
            'status': 'approved',
            'admin_notes': 'Approved for testing'
        }
        response = self.client.patch(
            f'/api/wholesale/admin/requests/{request_obj.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        
        # Check if wholesale user was created
        wholesale_user = NEW_WholesaleUser.objects.get(user=self.user)
        self.assertTrue(wholesale_user.is_wholesale)
        self.assertEqual(wholesale_user.approved_by, self.admin_user)
    
    def test_admin_reject_request(self):
        """Test admin rejecting a wholesale request"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create and approve request first
        request_obj = NEW_WholesaleRequest.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='retailer',
            expected_monthly_volume='5000',
            reason='Test reason',
            status='approved'
        )
        
        # Create wholesale user
        wholesale_user = NEW_WholesaleUser.objects.create(
            user=self.user,
            is_wholesale=True
        )
        
        # Reject request
        data = {
            'status': 'rejected',
            'admin_notes': 'Rejected for testing'
        }
        response = self.client.patch(
            f'/api/wholesale/admin/requests/{request_obj.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')
        
        # Check if wholesale access was removed
        wholesale_user.refresh_from_db()
        self.assertFalse(wholesale_user.is_wholesale)
    
    def test_discount_calculation_thresholds(self):
        """Test discount calculation for different thresholds"""
        # Create wholesale user
        NEW_WholesaleUser.objects.create(
            user=self.user,
            is_wholesale=True
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Test threshold 1 (500)
        data = {'amount': '600.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        self.assertEqual(float(response.data['discount_percentage']), 10.00)
        
        # Test threshold 2 (1000)
        data = {'amount': '1200.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        self.assertEqual(float(response.data['discount_percentage']), 15.00)
        
        # Test threshold 3 (2000)
        data = {'amount': '2200.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        self.assertEqual(float(response.data['discount_percentage']), 20.00)
        
        # Test threshold 4 (2500)
        data = {'amount': '3000.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        self.assertEqual(float(response.data['discount_percentage']), 25.00)
        
        # Test below threshold
        data = {'amount': '300.00'}
        response = self.client.post('/api/wholesale/discount/calculate/', data, format='json')
        self.assertEqual(float(response.data['discount_amount']), 0.00)

