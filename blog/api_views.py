from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import BlogPost
from .serializers import BlogPostSerializer, BlogPostListSerializer
from taggit.models import Tag


class BlogPostListView(generics.ListAPIView):
    """
    List all published blog posts.
    
    Returns a list of published blog posts ordered by published_date (newest first).
    Only posts with is_published=True are returned.
    """
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostListSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all published blog posts",
        responses={
            200: BlogPostListSerializer(many=True),
        },
        tags=['Blog']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """Return only published posts, ordered by published_date"""
        return BlogPost.objects.filter(is_published=True).select_related('author').prefetch_related('tags').order_by('-published_date')
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BlogPostDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single blog post by slug.
    
    Returns detailed information about a blog post including full content.
    Only published posts are accessible.
    """
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
    
    @swagger_auto_schema(
        operation_description="Get detailed information about a blog post by slug",
        responses={
            200: BlogPostSerializer(),
            404: 'Blog post not found or not published'
        },
        tags=['Blog']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_object(self):
        """Get blog post by slug, only if published"""
        slug = self.kwargs.get('slug')
        obj = get_object_or_404(
            BlogPost.objects.filter(is_published=True).select_related('author').prefetch_related('tags'),
            slug=slug
        )
        return obj


class BlogTagListView(generics.ListAPIView):
    """
    List all tags used in published blog posts.
    
    Returns a list of all tags that are associated with published blog posts.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        # Get all tags from published blog posts
        published_posts = BlogPost.objects.filter(is_published=True)
        tags = Tag.objects.filter(blogpost__in=published_posts).distinct().order_by('name')
        
        tag_list = [{'id': tag.id, 'name': tag.name, 'slug': tag.slug} for tag in tags]
        
        return Response(tag_list, status=status.HTTP_200_OK)
