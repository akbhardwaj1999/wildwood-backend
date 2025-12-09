from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    GalleryItem, Variant, Category, Review, WishedItem,
    VariantImage, VariantVideo, VariantYoutubeVideo, SpecialPrice
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'title', 'description', 'image', 'parent', 'children')
        read_only_fields = ('id',)
    
    def get_children(self, obj):
        """Recursively serialize children categories"""
        children = obj.get_children()
        return CategorySerializer(children, many=True).data if children.exists() else []


class VariantImageSerializer(serializers.ModelSerializer):
    """Serializer for VariantImage model"""
    
    class Meta:
        model = VariantImage
        fields = ('id', 'name', 'image', 'featured', 'thumbnail', 'active')
        read_only_fields = ('id',)


class VariantVideoSerializer(serializers.ModelSerializer):
    """Serializer for VariantVideo model"""
    
    class Meta:
        model = VariantVideo
        fields = ('id', 'title', 'video', 'thumbnail_image', 'active')
        read_only_fields = ('id',)


class VariantYoutubeVideoSerializer(serializers.ModelSerializer):
    """Serializer for VariantYoutubeVideo model"""
    
    class Meta:
        model = VariantYoutubeVideo
        fields = ('id', 'title', 'youtube_video_code', 'thumbnail_image', 'active')
        read_only_fields = ('id',)


class VariantSerializer(serializers.ModelSerializer):
    """Serializer for Variant model"""
    images = VariantImageSerializer(source='variantimage_set', many=True, read_only=True)
    videos = VariantVideoSerializer(source='variantvideo_set', many=True, read_only=True)
    youtube_videos = VariantYoutubeVideoSerializer(source='variantyoutubevideo_set', many=True, read_only=True)
    in_stock = serializers.ReadOnlyField()
    image = serializers.SerializerMethodField()
    largeImage = serializers.SerializerMethodField()
    
    class Meta:
        model = Variant
        fields = (
            'id', 'product', 'image', 'largeImage', 'title', 'price', 
            'quantity', 'volume', 'weight', 'is_best_seller', 'active',
            'in_stock', 'images', 'videos', 'youtube_videos', 'updated'
        )
        read_only_fields = ('id', 'updated')
    
    def get_image(self, obj):
        """Return absolute URL for image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback: use settings if no request context
            from django.conf import settings
            return f"{settings.SITE_URL}{obj.image.url}" if hasattr(settings, 'SITE_URL') else obj.image.url
        return None
    
    def get_largeImage(self, obj):
        """Return absolute URL for largeImage"""
        if obj.largeImage:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.largeImage.url)
            # Fallback: use settings if no request context
            from django.conf import settings
            return f"{settings.SITE_URL}{obj.largeImage.url}" if hasattr(settings, 'SITE_URL') else obj.largeImage.url
        return None


class VariantCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Variant (without nested objects)"""
    
    class Meta:
        model = Variant
        fields = (
            'id', 'product', 'image', 'largeImage', 'title', 'price', 
            'quantity', 'volume', 'weight', 'is_best_seller', 'active'
        )
        read_only_fields = ('id',)


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    author_name = serializers.SerializerMethodField()
    author_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = (
            'id', 'product', 'content', 'author', 'author_name', 'author_id',
            'rating', 'date_added', 'featured', 'keep_anonymous', 'is_imported',
            'import_author'
        )
        read_only_fields = ('id', 'date_added', 'author')
    
    def get_author_name(self, obj):
        """Get author name (handles imported reviews)"""
        if obj.keep_anonymous:
            return "Anonymous"
        if obj.is_imported:
            return obj.import_author or "Anonymous"
        return obj.author.username if obj.author else "Anonymous"
    
    def get_author_id(self, obj):
        """Get author ID (only for non-imported, non-anonymous reviews)"""
        if obj.keep_anonymous or obj.is_imported or not obj.author:
            return None
        return obj.author.id


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Review"""
    
    class Meta:
        model = Review
        fields = ('id', 'product', 'content', 'rating', 'keep_anonymous')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        """Create review with current user as author"""
        validated_data['author'] = self.context['request'].user
        from django.utils import timezone
        validated_data['date_added'] = timezone.now()
        return super().create(validated_data)


class GalleryItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing GalleryItems (lightweight)"""
    category_title = serializers.CharField(source='category.title', read_only=True)
    default_variant_price = serializers.DecimalField(
        source='default_variant.price', 
        max_digits=30, 
        decimal_places=2, 
        read_only=True
    )
    default_variant_image = serializers.ImageField(
        source='default_variant.image',
        read_only=True
    )
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryItem
        fields = (
            'id', 'title', 'slug', 'description', 'category', 'category_title',
            'default_variant_price', 'default_variant_image', 'active',
            'total_views', 'average_rating', 'review_count', 'timeStamp', 'updated'
        )
        read_only_fields = ('id', 'slug', 'timeStamp', 'updated')
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        reviews = obj.reviews.all()
        if reviews.exists():
            from django.db.models import Avg
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 2) if avg else 0
        return 0
    
    def get_review_count(self, obj):
        """Get total review count"""
        return obj.reviews.count()


class GalleryItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for GalleryItem detail view (with all related data)"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=True
    )
    variants = VariantSerializer(source='variant_set', many=True, read_only=True)
    default_variant = VariantSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryItem
        fields = (
            'id', 'category', 'category_id', 'title', 'slug', 'description',
            'default_variant', 'variants', 'active', 'timeStamp', 'updated',
            'total_views', 'metaKeyWords', 'metaKeyDescription',
            'google_product_category', 'reviews', 'average_rating', 'review_count'
        )
        read_only_fields = ('id', 'slug', 'timeStamp', 'updated', 'total_views')
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        reviews = obj.reviews.all()
        if reviews.exists():
            from django.db.models import Avg
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 2) if avg else 0
        return 0
    
    def get_review_count(self, obj):
        """Get total review count"""
        return obj.reviews.count()


class GalleryItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating GalleryItem"""
    
    class Meta:
        model = GalleryItem
        fields = (
            'id', 'category', 'title', 'slug', 'description', 'default_variant',
            'active', 'metaKeyWords', 'metaKeyDescription', 'google_product_category'
        )
        read_only_fields = ('id', 'slug')


class WishedItemSerializer(serializers.ModelSerializer):
    """Serializer for WishedItem model"""
    product = GalleryItemListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=GalleryItem.objects.all(),
        source='product',
        write_only=True,
        required=True
    )
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = WishedItem
        fields = ('id', 'user', 'product', 'product_id', 'date_added', 'date_updated', 'is_unwished')
        read_only_fields = ('id', 'user', 'date_added', 'date_updated')
    
    def create(self, validated_data):
        """Create wishlist item with current user"""
        validated_data['user'] = self.context['request'].user
        # Check if item already exists
        product = validated_data['product']
        user = validated_data['user']
        wished_item, created = WishedItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'is_unwished': False}
        )
        if not created:
            # If exists and was unwished, make it wished again
            if wished_item.is_unwished:
                wished_item.is_unwished = False
                wished_item.save()
        return wished_item

