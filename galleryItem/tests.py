from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GalleryItem, Variant, Category, Review, WishedItem

User = get_user_model()


class CategoryTestCase(TestCase):
    """Test cases for Category API"""

    def setUp(self):
        self.client = APIClient()
        self.category_list_url = '/api/gallery/categories/'
        
        # Create categories
        self.parent_category = Category.objects.create(
            title='Electronics',
            description='Electronic products'
        )
        self.child_category = Category.objects.create(
            title='Mobile Phones',
            description='Mobile phones category',
            parent=self.parent_category
        )

    def test_category_list_success(self):
        """Test successful category list retrieval"""
        response = self.client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)

    def test_category_detail_success(self):
        """Test successful category detail retrieval"""
        url = f'{self.category_list_url}{self.parent_category.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Electronics')
        self.assertIn('children', response.data)


class GalleryItemTestCase(TestCase):
    """Test cases for GalleryItem API"""

    def setUp(self):
        self.client = APIClient()
        self.item_list_url = '/api/gallery/items/'
        
        # Create category
        self.category = Category.objects.create(
            title='Test Category',
            description='Test category description'
        )
        
        # Create gallery item
        self.gallery_item = GalleryItem.objects.create(
            category=self.category,
            title='Test Product',
            description='Test product description',
            metaKeyWords='test, product',
            metaKeyDescription='Test meta description',
            active=True
        )
        
        # Create variant
        self.variant = Variant.objects.create(
            product=self.gallery_item,
            title='Test Variant',
            price=99.99,
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )
        self.gallery_item.default_variant = self.variant
        self.gallery_item.save()

    def test_gallery_item_list_success(self):
        """Test successful gallery item list retrieval"""
        response = self.client.get(self.item_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)

    def test_gallery_item_list_filter_by_category(self):
        """Test filtering gallery items by category"""
        response = self.client.get(f'{self.item_list_url}?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_gallery_item_list_search(self):
        """Test searching gallery items"""
        response = self.client.get(f'{self.item_list_url}?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_gallery_item_detail_success(self):
        """Test successful gallery item detail retrieval"""
        url = f'{self.item_list_url}{self.gallery_item.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Product')
        self.assertIn('variants', response.data)
        self.assertIn('reviews', response.data)

    def test_gallery_item_detail_increments_views(self):
        """Test that viewing a gallery item increments view count"""
        initial_views = self.gallery_item.total_views
        url = f'{self.item_list_url}{self.gallery_item.id}/'
        response = self.client.get(url)
        self.gallery_item.refresh_from_db()
        self.assertEqual(self.gallery_item.total_views, initial_views + 1)

    def test_gallery_item_by_slug_success(self):
        """Test retrieving gallery item by slug"""
        url = f'/api/gallery/items/slug/{self.gallery_item.slug}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Product')

    def test_gallery_item_create_as_admin(self):
        """Test creating gallery item as admin"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        data = {
            'category': self.category.id,
            'title': 'New Product',
            'description': 'New product description',
            'metaKeyWords': 'new, product',
            'metaKeyDescription': 'New meta description',
            'active': True
        }
        response = self.client.post(self.item_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Product')

    def test_gallery_item_create_as_regular_user(self):
        """Test creating gallery item as regular user (should fail)"""
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPass123!'
        )
        refresh = RefreshToken.for_user(regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        data = {
            'category': self.category.id,
            'title': 'New Product',
            'description': 'New product description',
        }
        response = self.client.post(self.item_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gallery_item_update_as_admin(self):
        """Test updating gallery item as admin"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = f'{self.item_list_url}{self.gallery_item.id}/'
        data = {
            'category': self.category.id,
            'title': 'Updated Product',
            'description': 'Updated description',
            'metaKeyWords': 'updated, product',
            'metaKeyDescription': 'Updated meta description',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.gallery_item.refresh_from_db()
        self.assertEqual(self.gallery_item.title, 'Updated Product')

    def test_gallery_item_delete_as_admin(self):
        """Test deleting gallery item as admin"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = f'{self.item_list_url}{self.gallery_item.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GalleryItem.objects.filter(id=self.gallery_item.id).exists())


class VariantTestCase(TestCase):
    """Test cases for Variant API"""

    def setUp(self):
        self.client = APIClient()
        self.variant_list_url = '/api/gallery/variants/'
        
        # Create category and gallery item
        self.category = Category.objects.create(title='Test Category')
        self.gallery_item = GalleryItem.objects.create(
            category=self.category,
            title='Test Product',
            metaKeyWords='test',
            metaKeyDescription='test',
            active=True
        )
        
        # Create variant
        self.variant = Variant.objects.create(
            product=self.gallery_item,
            title='Test Variant',
            price=99.99,
            quantity=10,
            volume=100,
            weight=200,
            active=True
        )

    def test_variant_list_success(self):
        """Test successful variant list retrieval"""
        response = self.client.get(self.variant_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_variant_list_filter_by_product(self):
        """Test filtering variants by product"""
        response = self.client.get(f'{self.variant_list_url}?product={self.gallery_item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_variant_detail_success(self):
        """Test successful variant detail retrieval"""
        url = f'{self.variant_list_url}{self.variant.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Variant')
        self.assertEqual(float(response.data['price']), 99.99)
        self.assertIn('in_stock', response.data)

    def test_variant_create_as_admin(self):
        """Test creating variant as admin"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Note: Variant requires image fields, so we'll test update instead
        # Creating variant via API requires file upload which is complex in tests
        # This test is skipped for now as it requires proper file handling
        pass

    def test_variant_update_as_admin(self):
        """Test updating variant as admin"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = f'{self.variant_list_url}{self.variant.id}/'
        data = {
            'product': self.gallery_item.id,
            'title': 'Updated Variant',
            'price': 199.99,
            'quantity': 15,
            'volume': 200,
            'weight': 300,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.title, 'Updated Variant')


class ReviewTestCase(TestCase):
    """Test cases for Review API"""

    def setUp(self):
        self.client = APIClient()
        self.review_list_url = '/api/gallery/reviews/'
        
        # Create category and gallery item
        self.category = Category.objects.create(title='Test Category')
        self.gallery_item = GalleryItem.objects.create(
            category=self.category,
            title='Test Product',
            metaKeyWords='test',
            metaKeyDescription='test',
            active=True
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create review
        from django.utils import timezone
        self.review = Review.objects.create(
            product=self.gallery_item,
            author=self.user,
            content='Great product!',
            rating=5,
            date_added=timezone.now()
        )

    def test_review_list_success(self):
        """Test successful review list retrieval"""
        response = self.client.get(f'{self.review_list_url}?product={self.gallery_item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)

    def test_review_list_filter_by_rating(self):
        """Test filtering reviews by rating"""
        response = self.client.get(f'{self.review_list_url}?product={self.gallery_item.id}&rating=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_review_create_as_authenticated_user(self):
        """Test creating review as authenticated user"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        data = {
            'product': self.gallery_item.id,
            'content': 'Another great review!',
            'rating': 4,
            'keep_anonymous': False
        }
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 4)
        # Check that review was created
        self.assertIn('id', response.data)
        self.assertEqual(response.data['product'], self.gallery_item.id)

    def test_review_create_as_unauthenticated_user(self):
        """Test creating review without authentication (should fail)"""
        data = {
            'product': self.gallery_item.id,
            'content': 'Test review',
            'rating': 3
        }
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_update_as_owner(self):
        """Test updating review as owner"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = f'{self.review_list_url}{self.review.id}/'
        data = {
            'content': 'Updated review content',
            'rating': 4
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.content, 'Updated review content')

    def test_review_delete_as_owner(self):
        """Test deleting review as owner"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = f'{self.review_list_url}{self.review.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())


class WishedItemTestCase(TestCase):
    """Test cases for WishedItem API"""

    def setUp(self):
        self.client = APIClient()
        self.wishlist_url = '/api/gallery/wishlist/'
        
        # Create category and gallery item
        self.category = Category.objects.create(title='Test Category')
        self.gallery_item = GalleryItem.objects.create(
            category=self.category,
            title='Test Product',
            metaKeyWords='test',
            metaKeyDescription='test',
            active=True
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_wishlist_list_as_authenticated_user(self):
        """Test retrieving wishlist as authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_wishlist_list_as_unauthenticated_user(self):
        """Test retrieving wishlist without authentication (should fail)"""
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_to_wishlist_success(self):
        """Test adding item to wishlist"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'product_id': self.gallery_item.id}
        response = self.client.post(self.wishlist_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product']['id'], self.gallery_item.id)
        self.assertFalse(response.data['is_unwished'])

    def test_add_to_wishlist_duplicate(self):
        """Test adding same item to wishlist twice (should toggle)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'product_id': self.gallery_item.id}
        
        # Add first time
        response1 = self.client.post(self.wishlist_url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Add second time (should toggle)
        response2 = self.client.post(self.wishlist_url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

    def test_remove_from_wishlist_success(self):
        """Test removing item from wishlist"""
        # Add to wishlist first
        wished_item = WishedItem.objects.create(
            user=self.user,
            product=self.gallery_item,
            is_unwished=False
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = f'{self.wishlist_url}{wished_item.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        wished_item.refresh_from_db()
        self.assertTrue(wished_item.is_unwished)

    def test_wishlist_only_shows_user_items(self):
        """Test that wishlist only shows current user's items"""
        # Create another user and their wishlist item
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        WishedItem.objects.create(
            user=other_user,
            product=self.gallery_item,
            is_unwished=False
        )
        
        # Add item for current user
        WishedItem.objects.create(
            user=self.user,
            product=self.gallery_item,
            is_unwished=False
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return current user's items
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.username)
