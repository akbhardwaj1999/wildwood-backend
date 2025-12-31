from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager


class BlogPost(models.Model):
    """Blog post model for storing blog articles"""
    title = models.CharField(
        max_length=200,
        help_text="Enter the title of your blog post (e.g., 'Welcome to Our Blog')"
    )
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = RichTextField(
        help_text="Write your blog post content here. Use the toolbar above to format text, add headings, lists, and more. No HTML knowledge needed!"
    )
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Write a short summary (2-3 sentences) that will appear on the blog listing page"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    featured_image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    published_date = models.DateTimeField(default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False, help_text="Only published posts will be visible on frontend")
    
    # Tags
    tags = TaggableManager(blank=True, help_text="Add tags to categorize your blog post (e.g., 'hardwood', 'furniture', 'sculptures')")
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, help_text="SEO meta title")
    meta_description = models.TextField(max_length=300, blank=True, help_text="SEO meta description")
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for the blog post"""
        return reverse('blog:detail', kwargs={'slug': self.slug})
    
    @property
    def formatted_date(self):
        """Return formatted date string"""
        return self.published_date.strftime('%b. %d, %Y')

