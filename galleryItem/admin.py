from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from mptt.admin import DraggableMPTTAdmin
import json

from .forms import GalleryItemAdminModelForm
from .models import Category, GalleryItem, Variant, VariantImage, Supplier, Review, TransferedReview, Ranking, \
    GoogleProductCategory, Supply, VariantSupply, VariantYoutubeVideo, VariantVideo, SpecialPrice


class VariantInline(admin.StackedInline):
    model = Variant
    extra = 1
    show_change_link = True


class SpecialPriceInline(admin.TabularInline):
    model = SpecialPrice
    extra = 1


class GalleryItemAdmin(admin.ModelAdmin):
    model = GalleryItem
    form = GalleryItemAdminModelForm
    list_display = ['title', 'category', 'stock_summary', 'active', 'updated']
    list_filter = ['category', 'active']
    search_fields = ['title', 'description']
    inlines = [VariantInline, SpecialPriceInline]
    date_hierarchy = 'timeStamp'
    readonly_fields = ['updated', 'timeStamp', 'stock_summary_display']
    
    def stock_summary(self, obj):
        """Show stock summary for all variants"""
        variants = obj.variant_set.all()
        if not variants.exists():
            return 'No variants'
        
        total_quantity = sum(v.quantity for v in variants)
        in_stock_count = sum(1 for v in variants if v.in_stock)
        out_of_stock_count = variants.count() - in_stock_count
        
        if out_of_stock_count == 0:
            return f'✅ All in stock ({total_quantity} total)'
        elif in_stock_count == 0:
            return f'❌ All out of stock'
        else:
            return f'⚠️ {in_stock_count} in stock, {out_of_stock_count} out of stock'
    stock_summary.short_description = 'Stock Summary'
    
    def stock_summary_display(self, obj):
        """Read-only field for stock summary"""
        return self.stock_summary(obj)
    stock_summary_display.short_description = 'Stock Summary'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name='galleryitem_import_json'),
        ]
        return custom_urls + urls
    
    def import_json_view(self, request):
        """Custom view for JSON file upload and import"""
        if request.method == 'POST':
            json_file = request.FILES.get('json_file')
            
            if not json_file:
                messages.error(request, '❌ Please select a JSON file to upload!')
                return redirect('..')
            
            if not json_file.name.endswith('.json'):
                messages.error(request, '❌ File must be a JSON file (.json extension)')
                return redirect('..')
            
            try:
                # Read and parse JSON
                json_data = json.load(json_file)
                
                # Import the utility function
                from .utils import import_products_from_json_data
                
                # Call import function
                result = import_products_from_json_data(json_data)
                
                # Show success message
                messages.success(
                    request, 
                    f'✅ Import Completed!\n'
                    f'📦 Products Created: {result["created"]}\n'
                    f'⚠️  Products Skipped: {result["skipped"]}\n'
                    f'🖼️  Images Downloaded: {result["images"]}\n'
                    f'⭐ Reviews Imported: {result["reviews"]}'
                )
                
                return redirect('..')
                
            except json.JSONDecodeError:
                messages.error(request, '❌ Invalid JSON file format!')
                return redirect('..')
            except Exception as e:
                messages.error(request, f'❌ Error during import: {str(e)}')
                return redirect('..')
        
        # GET request - show upload form
        context = {
            'title': 'Import Products from JSON',
            'site_title': 'Import Products',
            'site_header': 'Product Import',
            'has_permission': True,
        }
        return render(request, 'admin/galleryitem/import_json.html', context)


class SpecialPriceAdmin(admin.ModelAdmin):
    pass


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1


class VariantVideoInline(admin.TabularInline):
    model = VariantVideo
    extra = 1


class VariantYoutubeVideoInline(admin.TabularInline):
    model = VariantYoutubeVideo
    extra = 1


class VariantSupplyInline(admin.TabularInline):
    model = VariantSupply
    extra = 1


class VariantAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'product', 'title', 'quantity', 'stock_status', 'price', 'active', 'updated']
    list_filter = ['active', 'is_best_seller', 'product__category']
    search_fields = ['title', 'product__title']
    readonly_fields = ['in_stock', 'stock_status_display']
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'title', 'active', 'is_best_seller')
        }),
        ('Pricing', {
            'fields': ('price',)
        }),
        ('Stock Information', {
            'fields': ('quantity', 'in_stock', 'stock_status_display'),
            'description': 'Stock status is automatically calculated based on quantity.'
        }),
        ('Dimensions', {
            'fields': ('volume', 'weight')
        }),
        ('Images', {
            'fields': ('image', 'largeImage')
        }),
    )
    inlines = [
        VariantImageInline,
        VariantVideoInline,
        VariantYoutubeVideoInline,
        VariantSupplyInline,
    ]
    
    def stock_status(self, obj):
        """Display stock status with color coding"""
        if obj.quantity > 10:
            return f'✅ In Stock ({obj.quantity})'
        elif obj.quantity > 0:
            return f'⚠️ Low Stock ({obj.quantity})'
        else:
            return f'❌ Out of Stock (0)'
    stock_status.short_description = 'Stock Status'
    
    def stock_status_display(self, obj):
        """Read-only field for stock status"""
        return self.stock_status(obj)
    stock_status_display.short_description = 'Current Stock Status'


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name']


class SuppliesAdmin(admin.ModelAdmin):
    list_display = ['title', 'supplier', 'price', 'quantity']


class CategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_display = ('tree_actions', 'title',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('title',)
    search_fields = ['title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
            qs,
            GalleryItem,
            'category',
            'products_cumulative_count',
            cumulative=True
        )

        # Add non cumulative product count
        qs = Category.objects.add_related_count(
            qs,
            GalleryItem,
            'category',
            'products_count',
            cumulative=False
        )
        return qs

    def related_products_count(self, instance):
        return instance.products_count

    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count

    related_products_cumulative_count.short_description = 'Related products (in tree)'


class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'content',
        'rating',
        'author',
        'import_author',
        'keep_anonymous',
        'is_imported',
        'date_added',
    ]
    list_filter = ['rating', 'keep_anonymous', 'is_imported']
    search_fields = ['product__title', 'content']


class TransferedReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'content',
        'rating',
    ]
    list_filter = ['rating']
    search_fields = ['product__title', 'content']


class RankingAdmin(admin.ModelAdmin):
    list_display = ['product', 'criteria', 'value', 'rank', 'date_added']
    list_filter = ['criteria']
    search_fields = ['product__title']


class GoogleProductCategoryAdmin(admin.ModelAdmin):
    pass


# Register your models here.
admin.site.register(Category, CategoryAdmin)
admin.site.register(GalleryItem, GalleryItemAdmin)
admin.site.register(Supply, SuppliesAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(SpecialPrice, SpecialPriceAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(TransferedReview, TransferedReviewAdmin)
admin.site.register(Ranking, RankingAdmin)
admin.site.register(GoogleProductCategory, GoogleProductCategoryAdmin)
