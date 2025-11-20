from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class UserRegistrationTestCase(TestCase):
    """Test cases for User Registration API"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/accounts/register/'
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123!',
            'password2': 'TestPass123!'
        }

    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('access_token', response.data)
        self.assertIsNotNone(response.data['access_token'])
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        
        # Verify user is created in database
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_registration_missing_fields(self):
        """Test registration with missing required fields"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            # Missing password fields
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        # Create first user
        self.client.post(self.register_url, self.valid_data, format='json')
        
        # Try to create user with same username
        data = self.valid_data.copy()
        data['email'] = 'different@example.com'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        self.client.post(self.register_url, self.valid_data, format='json')
        
        # Try to create user with same email
        data = self.valid_data.copy()
        data['username'] = 'differentuser'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_weak_password(self):
        """Test registration with weak password"""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password2'] = '123'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_invalid_email(self):
        """Test registration with invalid email format"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(TestCase):
    """Test cases for User Login API"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/accounts/login/'
        self.username = 'testuser'
        self.password = 'TestPass123!'
        
        # Create a user for testing
        self.user = User.objects.create_user(
            username=self.username,
            email='test@example.com',
            password=self.password,
            first_name='Test',
            last_name='User'
        )

    def test_login_success(self):
        """Test successful login"""
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('access_token', response.data)
        self.assertIsNotNone(response.data['access_token'])
        self.assertEqual(response.data['user']['username'], self.username)

    def test_login_invalid_username(self):
        """Test login with invalid username"""
        data = {
            'username': 'wronguser',
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_invalid_password(self):
        """Test login with invalid password"""
        data = {
            'username': self.username,
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)


class UserLogoutTestCase(TestCase):
    """Test cases for User Logout API"""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = '/api/accounts/logout/'
        
        # Create a user and get tokens
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def test_logout_success(self):
        """Test successful logout"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'refresh_token': self.refresh_token}
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_without_authentication(self):
        """Test logout without authentication token"""
        data = {'refresh_token': self.refresh_token}
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token(self):
        """Test logout without refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.logout_url, {}, format='json')
        # Should still return success as refresh token is optional
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserProfileTestCase(TestCase):
    """Test cases for User Profile API"""

    def setUp(self):
        self.client = APIClient()
        self.profile_url = '/api/accounts/profile/'
        self.profile_update_url = '/api/accounts/profile/update/'
        
        # Create a user and get tokens
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_profile_success(self):
        """Test successful profile retrieval"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_get_profile_without_authentication(self):
        """Test profile retrieval without authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_success(self):
        """Test successful profile update"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['user']['first_name'], 'Updated')
        self.assertEqual(response.data['user']['last_name'], 'Name')
        self.assertEqual(response.data['user']['email'], 'updated@example.com')
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_update_password_success(self):
        """Test successful password update"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'current_password': 'TestPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password is changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_update_password_wrong_current_password(self):
        """Test password update with wrong current password"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'current_password': 'WrongPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)

    def test_update_password_mismatch(self):
        """Test password update with password mismatch"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'current_password': 'TestPass123!',
            'new_password': 'NewPass123!',
            'confirm_password': 'DifferentPass123!'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_update_password_missing_current_password(self):
        """Test password update without current password"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)

    def test_update_profile_without_authentication(self):
        """Test profile update without authentication"""
        data = {
            'first_name': 'Updated'
        }
        response = self.client.patch(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListTestCase(TestCase):
    """Test cases for User List API (Admin only)"""

    def setUp(self):
        self.client = APIClient()
        self.user_list_url = '/api/accounts/users/'
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='TestPass123!'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='TestPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        # Create some test users
        for i in range(5):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='TestPass123!'
            )

    def test_user_list_as_admin(self):
        """Test user list access as admin"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # Should return paginated results
        self.assertGreater(len(response.data['results']), 0)

    def test_user_list_as_regular_user(self):
        """Test user list access as regular user (should fail)"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_list_without_authentication(self):
        """Test user list access without authentication"""
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IntegrationTestCase(TestCase):
    """Integration test cases for complete user flow"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/accounts/register/'
        self.login_url = '/api/accounts/login/'
        self.profile_url = '/api/accounts/profile/'
        self.logout_url = '/api/accounts/logout/'

    def test_complete_user_flow(self):
        """Test complete user flow: register -> login -> get profile -> logout"""
        # 1. Register
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        register_response = self.client.post(self.register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        access_token = register_response.data['access_token']
        
        # 2. Get profile with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['username'], 'newuser')
        
        # 3. Logout
        logout_response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # 4. Try to access profile after logout (token will still be valid until it expires - 30 days)
        profile_response_after_logout = self.client.get(self.profile_url)
        # Token is still valid (30 days lifetime), but logout was successful
        self.assertEqual(profile_response_after_logout.status_code, status.HTTP_200_OK)
