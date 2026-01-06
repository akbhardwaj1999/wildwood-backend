from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    GalleryItem, Variant, Category, Review, WishedItem,
    VariantImage, VariantVideo, VariantYoutubeVideo, SpecialPrice,
    Supply, VariantSupply, Supplier
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


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model"""
    
    class Meta:
        model = Supplier
        fields = ('id', 'name', 'website', 'updated')
        read_only_fields = ('id', 'updated')


class SupplySerializer(serializers.ModelSerializer):
    """Serializer for Supply model"""
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True,
        required=True
    )
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Supply
        fields = (
            'id', 'title', 'description', 'link', 'price', 'quantity',
            'image', 'supplier', 'supplier_id', 'updated'
        )
        read_only_fields = ('id', 'updated')
    
    def get_image(self, obj):
        """Return absolute URL for image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            from django.conf import settings
            return f"{settings.SITE_URL}{obj.image.url}" if hasattr(settings, 'SITE_URL') else obj.image.url
        return None


class VariantSupplySerializer(serializers.ModelSerializer):
    """Serializer for VariantSupply model"""
    supply = SupplySerializer(read_only=True)
    supply_id = serializers.PrimaryKeyRelatedField(
        queryset=Supply.objects.all(),
        source='supply',
        write_only=True,
        required=True
    )
    total_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = VariantSupply
        fields = (
            'id', 'variant', 'supply', 'supply_id', 'quantity_required', 'total_cost'
        )
        read_only_fields = ('id',)
    
    def get_total_cost(self, obj):
        """Calculate total cost for this supply"""
        return float(obj.get_supply_required_cost_to_manufacturer())


class VariantSerializer(serializers.ModelSerializer):
    """Serializer for Variant model"""
    images = VariantImageSerializer(source='variantimage_set', many=True, read_only=True)
    videos = VariantVideoSerializer(source='variantvideo_set', many=True, read_only=True)
    youtube_videos = VariantYoutubeVideoSerializer(source='variantyoutubevideo_set', many=True, read_only=True)
    in_stock = serializers.ReadOnlyField()
    image = serializers.SerializerMethodField()
    largeImage = serializers.SerializerMethodField()
    supplies = serializers.SerializerMethodField()
    
    class Meta:
        model = Variant
        fields = (
            'id', 'product', 'image', 'largeImage', 'title', 'price', 
            'quantity', 'volume', 'weight', 'is_best_seller', 'active',
            'in_stock', 'images', 'videos', 'youtube_videos', 'supplies', 'updated'
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
    
    def get_supplies(self, obj):
        """
        Get supplies for this variant (ONLY for superuser/admin users).
        Each variant has its own supplies, so each product will show different supplies.
        """
        request = self.context.get('request')
        
        # STRICT SECURITY CHECK: Only return supplies for authenticated superusers
        if not request:
            return []
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return []
        
        # STRICT CHECK: Only superuser can see supplies
        if not request.user.is_superuser:
            return []
        
        # Get supplies for THIS specific variant (each variant has different supplies)
        variant_supplies = obj.variantsupply_set.select_related('supply', 'supply__supplier').all()
        return VariantSupplySerializer(variant_supplies, many=True, context=self.context).data


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
    default_variant_image = serializers.SerializerMethodField()
    default_variant_quantity = serializers.IntegerField(
        source='default_variant.quantity',
        read_only=True
    )
    default_variant_in_stock = serializers.BooleanField(
        source='default_variant.in_stock',
        read_only=True
    )
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    def get_default_variant_image(self, obj):
        """Return absolute URL for default variant image"""
        if obj.default_variant and obj.default_variant.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.default_variant.image.url)
            # Fallback: use settings if no request context
            from django.conf import settings
            return f"{settings.SITE_URL}{obj.default_variant.image.url}" if hasattr(settings, 'SITE_URL') else obj.default_variant.image.url
        return None
    
    class Meta:
        model = GalleryItem
        fields = (
            'id', 'title', 'slug', 'description', 'category', 'category_title',
            'default_variant_price', 'default_variant_image', 'default_variant_quantity',
            'default_variant_in_stock', 'active',
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
    admin_info = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryItem
        fields = (
            'id', 'category', 'category_id', 'title', 'slug', 'description',
            'default_variant', 'variants', 'active', 'timeStamp', 'updated',
            'total_views', 'metaKeyWords', 'metaKeyDescription',
            'google_product_category', 'reviews', 'average_rating', 'review_count',
            'admin_info', 'related_products'
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
    
    def get_admin_info(self, obj):
        """
        Get admin-specific information (manufacturing cost, profit, shipping charges)
        ONLY for superuser/admin users. Each product has its own admin_info based on its variants and supplies.
        """
        request = self.context.get('request')
        
        # STRICT SECURITY CHECK: Only return admin_info for authenticated superusers
        if not request:
            return None
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # STRICT CHECK: Only superuser can see admin info
        if not request.user.is_superuser:
            return None
        
        # Get default variant or first variant
        variant = obj.default_variant or obj.variant_set.first()
        if not variant:
            return None
        
        admin_info = {}
        
        # Calculate manufacturing cost and profit for THIS product's variant
        # Each product will have different manufacturing cost based on its supplies
        variant_supplies = variant.variantsupply_set.select_related('supply', 'supply__supplier').all()
        total_manufacturing_cost = sum(
            float(vs.get_supply_required_cost_to_manufacturer()) 
            for vs in variant_supplies
        )
        
        # Each product's profit is calculated based on its variant price and manufacturing cost
        admin_info['manufacturing_cost'] = round(total_manufacturing_cost, 2)
        admin_info['profit'] = round(float(variant.price) - total_manufacturing_cost, 2)
        
        # Calculate shipping charges for different shipment types
        # Shipping charges are calculated based on THIS variant's volume/weight
        # So each product will have different shipping charges
        from cart.models import ShippingCost
        from cart.utils import calculate_item_shipping_charges
        
        shipping_info = {}
        shipment_types = [
            ('international', ShippingCost.INTERNATIONAL),
            ('other_state', ShippingCost.OTHER_STATE),
            ('other_city', ShippingCost.OTHER_CITY),
            ('local', ShippingCost.LOCAL),
        ]
        
        for name, shipment_type in shipment_types:
            try:
                qs = ShippingCost.objects.filter(shipment_type=shipment_type)
                charges = calculate_item_shipping_charges(qs, variant)
                shipping_info[name] = round(float(charges), 2) if charges else None
            except Exception as e:
                shipping_info[name] = None
                shipping_info[f'{name}_error'] = str(e)
        
        admin_info['shipping_charges'] = shipping_info
        
        return admin_info
    
    def get_related_products(self, obj):
        """
        Get related products from the same category.
        Excludes current product and limits to 4 products.
        Only returns products that have a default_variant (to avoid errors).
        """
        # Get products from the same category, excluding current product
        # Filter only products that have a default_variant
        related = GalleryItem.objects.filter(
            category=obj.category,
            active=True,
            default_variant__isnull=False  # Only products with default_variant
        ).exclude(
            id=obj.id
        ).select_related(
            'default_variant', 'category'
        ).prefetch_related(
            'reviews'
        )[:4]  # Limit to 4 related products only
        
        # Use GalleryItemListSerializer for consistent format
        return GalleryItemListSerializer(related, many=True, context=self.context).data


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

