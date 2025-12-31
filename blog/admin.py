from django.contrib import admin
from django.utils.html import format_html
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import BlogPost


class BlogPostAdminForm(forms.ModelForm):
    """Custom form with better help text for non-technical users"""
    class Meta:
        model = BlogPost
        fields = '__all__'
        widgets = {
            'content': CKEditorUploadingWidget(),
        }
        help_texts = {
            'tags': 'Add tags separated by commas (e.g., "hardwood, furniture, sculptures")',
        }


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for BlogPost model - User-friendly for non-technical users"""
    form = BlogPostAdminForm
    list_display = ['title', 'author', 'published_date', 'is_published', 'created_date', 'preview_image']
    list_filter = ['is_published', 'published_date', 'author', 'created_date']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_date', 'updated_date', 'preview_image']
    date_hierarchy = 'published_date'
    
    fieldsets = (
        ('📝 Basic Information', {
            'fields': ('title', 'slug', 'author'),
            'description': '<strong>Step 1:</strong> Enter the title and select the author. The slug will be auto-generated from the title.'
        }),
        ('✍️ Content', {
            'fields': ('excerpt', 'content', 'featured_image', 'preview_image'),
            'description': '<strong>Step 2:</strong> Write your blog post. Use the rich text editor toolbar to format text, add headings, lists, and <strong>insert images</strong>. Click the Image button in toolbar to add images inside your content. Upload a featured image to make your post more attractive.'
        }),
        ('🏷️ Tags', {
            'fields': ('tags',),
            'description': 'Add tags to help readers find related posts (e.g., "hardwood", "furniture", "sculptures"). Separate multiple tags with commas.'
        }),
        ('📅 Publishing', {
            'fields': ('published_date', 'is_published'),
            'description': '<strong>Step 3:</strong> Set the publish date and <strong>check "Is Published"</strong> to make your post visible on the website. If unchecked, the post will be saved but not shown to visitors.'
        }),
        ('🔍 SEO Settings (Optional)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
            'description': 'These fields help with search engine optimization. Leave blank if you\'re not sure what to enter.'
        }),
        ('📊 Information', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',),
            'description': 'Automatically tracked dates - you don\'t need to fill these.'
        }),
    )
    
    def preview_image(self, obj):
        """Display preview of featured image in admin"""
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.featured_image.url
            )
        return "No image"
    preview_image.short_description = 'Featured Image Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('author')

