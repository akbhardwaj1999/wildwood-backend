"""
API Test Cases for Blog Feature
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from .models import BlogPost

User = get_user_model()


class BlogAPITestCase(TestCase):
    """Test cases for Blog API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create author user
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create another user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create published blog posts
        self.published_post1 = BlogPost.objects.create(
            title='Test Blog Post 1',
            slug='test-blog-post-1',
            content='This is the content of test blog post 1.',
            excerpt='Short excerpt for post 1',
            author=self.author,
            published_date=timezone.now() - timedelta(days=1),
            is_published=True,
            meta_title='Test Post 1 Meta Title',
            meta_description='Test Post 1 Meta Description'
        )
        
        self.published_post2 = BlogPost.objects.create(
            title='Test Blog Post 2',
            slug='test-blog-post-2',
            content='This is the content of test blog post 2.',
            excerpt='Short excerpt for post 2',
            author=self.author,
            published_date=timezone.now() - timedelta(days=2),
            is_published=True
        )
        
        # Create unpublished blog post (should not appear in API)
        self.unpublished_post = BlogPost.objects.create(
            title='Unpublished Post',
            slug='unpublished-post',
            content='This post should not appear in API.',
            excerpt='This is unpublished',
            author=self.author,
            published_date=timezone.now(),
            is_published=False
        )
    
    def test_list_blog_posts_success(self):
        """Test listing all published blog posts"""
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)  # Only published posts
        
        # Check that unpublished post is not in the list
        slugs = [post['slug'] for post in response.data]
        self.assertIn('test-blog-post-1', slugs)
        self.assertIn('test-blog-post-2', slugs)
        self.assertNotIn('unpublished-post', slugs)
    
    def test_list_blog_posts_ordering(self):
        """Test that blog posts are ordered by published_date (newest first)"""
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check ordering (newest first)
        posts = response.data
        self.assertEqual(len(posts), 2)
        # post1 is newer (1 day ago) than post2 (2 days ago)
        self.assertEqual(posts[0]['slug'], 'test-blog-post-1')
        self.assertEqual(posts[1]['slug'], 'test-blog-post-2')
    
    def test_list_blog_posts_fields(self):
        """Test that list endpoint returns correct fields"""
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        post = response.data[0]
        required_fields = ['id', 'title', 'slug', 'excerpt', 'author_name', 
                          'featured_image_url', 'published_date', 'formatted_date']
        
        for field in required_fields:
            self.assertIn(field, post)
        
        # Check that full content is NOT in list view
        self.assertNotIn('content', post)
        self.assertNotIn('meta_title', post)
        self.assertNotIn('meta_description', post)
    
    def test_list_blog_posts_author_name(self):
        """Test that author name is correctly returned"""
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        post = response.data[0]
        # Author has first_name and last_name, so should return full name
        self.assertEqual(post['author_name'], 'John Doe')
    
    def test_list_blog_posts_no_featured_image(self):
        """Test that posts without featured images return null"""
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for post in response.data:
            # featured_image_url can be null
            self.assertIn('featured_image_url', post)
    
    def test_get_blog_post_detail_success(self):
        """Test retrieving a single published blog post by slug"""
        response = self.client.get('/api/blog/posts/test-blog-post-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'test-blog-post-1')
        self.assertEqual(response.data['title'], 'Test Blog Post 1')
        self.assertEqual(response.data['content'], 'This is the content of test blog post 1.')
        self.assertIn('content', response.data)  # Full content should be in detail view
        self.assertIn('meta_title', response.data)
        self.assertIn('meta_description', response.data)
    
    def test_get_blog_post_detail_not_found(self):
        """Test retrieving a non-existent blog post"""
        response = self.client.get('/api/blog/posts/non-existent-post/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_unpublished_blog_post(self):
        """Test that unpublished posts cannot be accessed via API"""
        response = self.client.get('/api/blog/posts/unpublished-post/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_blog_post_detail_fields(self):
        """Test that detail endpoint returns all required fields"""
        response = self.client.get('/api/blog/posts/test-blog-post-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        post = response.data
        required_fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 
            'author_name', 'author_username', 'featured_image_url',
            'published_date', 'formatted_date', 'is_published',
            'meta_title', 'meta_description', 'created_date', 'updated_date'
        ]
        
        for field in required_fields:
            self.assertIn(field, post)
    
    def test_get_blog_post_formatted_date(self):
        """Test that formatted_date is correctly formatted"""
        response = self.client.get('/api/blog/posts/test-blog-post-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        formatted_date = response.data['formatted_date']
        # Should be in format like "Jan. 01, 2025"
        self.assertIn('.', formatted_date)  # Contains period
        self.assertIn(',', formatted_date)  # Contains comma
        self.assertIsInstance(formatted_date, str)
    
    def test_blog_post_list_permissions(self):
        """Test that blog list endpoint is publicly accessible (no auth required)"""
        # No authentication
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_blog_post_detail_permissions(self):
        """Test that blog detail endpoint is publicly accessible (no auth required)"""
        # No authentication
        response = self.client.get('/api/blog/posts/test-blog-post-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_empty_blog_list(self):
        """Test listing when no published posts exist"""
        # Delete all published posts
        BlogPost.objects.filter(is_published=True).delete()
        
        response = self.client.get('/api/blog/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertIsInstance(response.data, list)
    
    def test_blog_post_slug_uniqueness(self):
        """Test that slugs are unique"""
        # Try to create post with duplicate slug
        with self.assertRaises(Exception):
            BlogPost.objects.create(
                title='Different Title',
                slug='test-blog-post-1',  # Duplicate slug
                content='Content',
                author=self.author,
                is_published=True
            )
    
    def test_blog_post_auto_slug_generation(self):
        """Test that slug is auto-generated from title if not provided"""
        post = BlogPost.objects.create(
            title='My Awesome Blog Post',
            content='Content here',
            author=self.author,
            is_published=True
        )
        
        self.assertEqual(post.slug, 'my-awesome-blog-post')
    
    def test_blog_post_author_relationship(self):
        """Test that blog post author relationship works correctly"""
        response = self.client.get('/api/blog/posts/test-blog-post-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['author_username'], 'author')
        self.assertEqual(response.data['author_name'], 'John Doe')
    
    def test_blog_post_published_date_filtering(self):
        """Test that only published posts are returned"""
        # Create a post with future published_date but is_published=True
        future_post = BlogPost.objects.create(
            title='Future Post',
            slug='future-post',
            content='Future content',
            author=self.author,
            published_date=timezone.now() + timedelta(days=10),
            is_published=True
        )
        
        response = self.client.get('/api/blog/posts/')
        
        # Should include future post if is_published=True
        slugs = [post['slug'] for post in response.data]
        self.assertIn('future-post', slugs)
    
    def test_blog_post_content_html_handling(self):
        """Test that content with HTML is properly returned"""
        html_post = BlogPost.objects.create(
            title='HTML Post',
            slug='html-post',
            content='<p>This is <strong>HTML</strong> content.</p>',
            author=self.author,
            is_published=True
        )
        
        response = self.client.get('/api/blog/posts/html-post/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('<p>', response.data['content'])
        self.assertIn('<strong>', response.data['content'])


class BlogModelTestCase(TestCase):
    """Test cases for BlogPost model"""
    
    def setUp(self):
        """Set up test data"""
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123'
        )
    
    def test_blog_post_creation(self):
        """Test creating a blog post"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Test content',
            author=self.author,
            is_published=True
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.author)
        self.assertTrue(post.is_published)
        self.assertIsNotNone(post.slug)
    
    def test_blog_post_slug_auto_generation(self):
        """Test that slug is auto-generated from title"""
        post = BlogPost.objects.create(
            title='My Test Blog Post',
            content='Content',
            author=self.author
        )
        
        self.assertEqual(post.slug, 'my-test-blog-post')
    
    def test_blog_post_custom_slug(self):
        """Test that custom slug is preserved"""
        post = BlogPost.objects.create(
            title='My Test Blog Post',
            slug='custom-slug',
            content='Content',
            author=self.author
        )
        
        self.assertEqual(post.slug, 'custom-slug')
    
    def test_blog_post_formatted_date(self):
        """Test formatted_date property"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.author,
            published_date=timezone.now()
        )
        
        formatted = post.formatted_date
        self.assertIsInstance(formatted, str)
        self.assertIn('.', formatted)  # Contains period (e.g., "Jan.")
        self.assertIn(',', formatted)  # Contains comma (e.g., ", 2025")
    
    def test_blog_post_str_representation(self):
        """Test string representation of blog post"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.author
        )
        
        self.assertEqual(str(post), 'Test Post')
    
    def test_blog_post_ordering(self):
        """Test that posts are ordered by published_date (newest first)"""
        post1 = BlogPost.objects.create(
            title='Post 1',
            content='Content 1',
            author=self.author,
            published_date=timezone.now() - timedelta(days=2),
            is_published=True
        )
        
        post2 = BlogPost.objects.create(
            title='Post 2',
            content='Content 2',
            author=self.author,
            published_date=timezone.now() - timedelta(days=1),
            is_published=True
        )
        
        posts = list(BlogPost.objects.all())
        # post2 should come first (newer)
        self.assertEqual(posts[0], post2)
        self.assertEqual(posts[1], post1)
    
    def test_blog_post_author_relationship(self):
        """Test author relationship"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.author
        )
        
        # Test reverse relationship
        self.assertIn(post, self.author.blog_posts.all())
    
    def test_blog_post_excerpt_optional(self):
        """Test that excerpt is optional"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.author,
            excerpt=''
        )
        
        self.assertEqual(post.excerpt, '')
    
    def test_blog_post_featured_image_optional(self):
        """Test that featured_image is optional"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.author
        )
        
        self.assertIsNone(post.featured_image)

