from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import BlogPost


class BlogPostModelTest(TestCase):
    """Test cases for BlogPost model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_blog_post_creation(self):
        """Test creating a blog post"""
        post = BlogPost.objects.create(
            title='Test Blog Post',
            content='This is a test blog post content.',
            author=self.user,
            is_published=True
        )
        self.assertEqual(post.title, 'Test Blog Post')
        self.assertEqual(post.author, self.user)
        self.assertTrue(post.is_published)
        self.assertIsNotNone(post.slug)
    
    def test_slug_auto_generation(self):
        """Test that slug is auto-generated from title"""
        post = BlogPost.objects.create(
            title='My Awesome Blog Post',
            content='Content here',
            author=self.user
        )
        self.assertEqual(post.slug, 'my-awesome-blog-post')
    
    def test_formatted_date(self):
        """Test formatted_date property"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.user,
            published_date=timezone.now()
        )
        self.assertIsNotNone(post.formatted_date)
        self.assertIn('.', post.formatted_date)  # Should contain date format like "Jan. 01, 2025"
    
    def test_blog_post_str_representation(self):
        """Test string representation"""
        post = BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=self.user
        )
        self.assertEqual(str(post), 'Test Post')

