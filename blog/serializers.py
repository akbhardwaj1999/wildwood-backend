from rest_framework import serializers
import re
from django.conf import settings
from .models import BlogPost


class BlogPostSerializer(serializers.ModelSerializer):
    """Serializer for BlogPost model"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    formatted_date = serializers.CharField(read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()  # Process content to fix image URLs
    
    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'excerpt',
            'author_name',
            'author_username',
            'featured_image',
            'featured_image_url',
            'published_date',
            'formatted_date',
            'is_published',
            'tags',
            'meta_title',
            'meta_description',
            'created_date',
            'updated_date',
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'slug']
    
    def get_tags(self, obj):
        """Get tags as list of strings"""
        return [tag.name for tag in obj.tags.all()]
    
    def get_content(self, obj):
        """Process content HTML to convert relative image URLs to absolute URLs"""
        content = obj.content
        if not content:
            return content
        
        request = self.context.get('request')
        if not request:
            return content
        
        # Get base URL (e.g., http://localhost:8000)
        base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
        
        # Function to fix image src URLs
        def fix_src(match):
            url = match.group(1)
            
            # If it's already an absolute URL, return as is
            if url.startswith('http://') or url.startswith('https://'):
                return f'src="{url}"'
            
            # If it starts with /media/, make it absolute
            if url.startswith('/media/'):
                return f'src="{base_url}{url}"'
            
            # If it starts with /uploads/, add /media/ prefix
            if url.startswith('/uploads/'):
                return f'src="{base_url}/media{url}"'
            
            # If it starts with uploads/ (no leading slash), add /media/
            if url.startswith('uploads/'):
                return f'src="{base_url}/media/{url}"'
            
            # If it starts with /, it's a relative URL from root
            if url.startswith('/'):
                return f'src="{base_url}{url}"'
            
            # Default: assume it's in media/uploads/
            return f'src="{base_url}/media/uploads/{url}"'
        
        # Replace all src="..." patterns in content (for img tags)
        content = re.sub(r'src="([^"]+)"', fix_src, content)
        
        return content
    
    def get_featured_image_url(self, obj):
        """Get full URL for featured image"""
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None


class BlogPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for blog post listing"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    formatted_date = serializers.CharField(read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'author_name',
            'featured_image_url',
            'published_date',
            'formatted_date',
            'tags',
        ]
    
    def get_tags(self, obj):
        """Get tags as list of strings"""
        return [tag.name for tag in obj.tags.all()]
    
    def get_featured_image_url(self, obj):
        """Get full URL for featured image"""
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None

