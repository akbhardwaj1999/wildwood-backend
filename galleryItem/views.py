from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import GalleryItem, Variant, Category, Review, WishedItem
from .serializers import (
    GalleryItemListSerializer,
    GalleryItemDetailSerializer,
    GalleryItemCreateUpdateSerializer,
    VariantSerializer,
    VariantCreateUpdateSerializer,
    CategorySerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    WishedItemSerializer
)


class GalleryItemListView(generics.ListCreateAPIView):
    """
    List all gallery items or create a new gallery item.
    
    GET: Returns a list of all active gallery items (no pagination - frontend handles it).
    POST: Create a new gallery item (Admin/Staff only).
    """
    queryset = GalleryItem.objects.filter(active=True).select_related(
        'category', 'default_variant'
    ).prefetch_related('reviews').order_by('-timeStamp')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'metaKeyWords']
    ordering_fields = ['timeStamp', 'updated', 'total_views', 'title']
    ordering = ['-timeStamp']
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Support multiple category filters
        category_ids = self.request.query_params.getlist('category')
        
        if category_ids:
            valid_categories = []
            for category_id in category_ids:
                try:
                    category = Category.objects.get(id=category_id)
                    valid_categories.append(category)
                except (Category.DoesNotExist, ValueError):
                    # If category doesn't exist or invalid ID, skip it
                    continue
            
            if not valid_categories:
                # No valid categories found, return empty queryset
                queryset = queryset.none()
            elif len(valid_categories) == 1:
                # Single category: get all descendants (including itself)
                category = valid_categories[0]
                descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
                queryset = queryset.filter(category_id__in=descendant_ids)
            else:
                # Multiple categories: Check if they have parent-child relationship
                # If parent-child: Use AND logic (intersection)
                # If different/sibling categories: Use OR logic (union)
                
                # Check if any category is a descendant of another
                has_parent_child_relationship = False
                for i, cat1 in enumerate(valid_categories):
                    for j, cat2 in enumerate(valid_categories):
                        if i != j:
                            # Check if cat1 is ancestor of cat2 or vice versa
                            if cat1.is_ancestor_of(cat2) or cat2.is_ancestor_of(cat1):
                                has_parent_child_relationship = True
                                break
                    if has_parent_child_relationship:
                        break
                
                if has_parent_child_relationship:
                    # Parent-child relationship: Use AND logic (intersection)
                    # Find products that are in ALL selected category trees
                    all_possible_ids = []
                    for category in valid_categories:
                        descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
                        all_possible_ids.append(set(descendant_ids))
                    
                    # Find intersection - categories that are descendants of ALL selected categories
                    if all_possible_ids:
                        intersection_ids = set.intersection(*all_possible_ids)
                        
                        if intersection_ids:
                            # Filter products that belong to categories in the intersection
                            queryset = queryset.filter(category_id__in=intersection_ids)
                        else:
                            # No intersection - no products match all categories
                            queryset = queryset.none()
                    else:
                        queryset = queryset.none()
                else:
                    # Different/sibling categories: Use OR logic (union)
                    # Show products from ANY of the selected categories
                    all_category_ids = set()
                    for category in valid_categories:
                        descendant_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
                        all_category_ids.update(descendant_ids)
                    
                    if all_category_ids:
                        queryset = queryset.filter(category_id__in=all_category_ids)
                    else:
                        queryset = queryset.none()
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GalleryItemCreateUpdateSerializer
        return GalleryItemListSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description="Get list of all active gallery items. Supports filtering, searching, and ordering. No pagination - returns all results.",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in title, description, keywords", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by: timeStamp, updated, total_views, title", type=openapi.TYPE_STRING),
        ],
        responses={
            200: GalleryItemListSerializer(many=True),
        },
        tags=['Gallery Items']
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new gallery item. Admin access required.",
        request_body=GalleryItemCreateUpdateSerializer,
        responses={
            201: GalleryItemDetailSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required'
        },
        security=[{'Bearer': []}],
        tags=['Gallery Items']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GalleryItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a gallery item.
    
    GET: Get detailed information about a gallery item including variants and reviews.
    PUT/PATCH: Update gallery item (Admin/Staff only).
    DELETE: Delete gallery item (Admin/Staff only).
    """
    queryset = GalleryItem.objects.all().select_related(
        'category', 'default_variant', 'google_product_category'
    ).prefetch_related(
        'variant_set__variantimage_set',
        'variant_set__variantvideo_set',
        'variant_set__variantyoutubevideo_set',
        'variant_set__variantsupply_set__supply__supplier',
        'reviews'
    )
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GalleryItemCreateUpdateSerializer
        return GalleryItemDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when retrieving"""
        instance = self.get_object()
        instance.total_views += 1
        instance.save(update_fields=['total_views'])
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get detailed information about a gallery item including variants, reviews, and ratings.",
        responses={
            200: GalleryItemDetailSerializer,
            404: 'Not Found'
        },
        tags=['Gallery Items']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update gallery item. Admin access required.",
        request_body=GalleryItemCreateUpdateSerializer,
        responses={
            200: GalleryItemDetailSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Gallery Items']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update gallery item. Admin access required.",
        request_body=GalleryItemCreateUpdateSerializer,
        responses={
            200: GalleryItemDetailSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Gallery Items']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete gallery item. Admin access required.",
        responses={
            204: 'No Content - Successfully deleted',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Gallery Items']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class GalleryItemBySlugView(generics.RetrieveAPIView):
    """
    Retrieve a gallery item by slug.
    
    GET: Get detailed information about a gallery item using its slug.
    Includes related products from the same category.
    """
    queryset = GalleryItem.objects.filter(active=True).select_related(
        'category', 'default_variant', 'google_product_category'
    ).prefetch_related(
        'variant_set__variantimage_set',
        'variant_set__variantvideo_set',
        'variant_set__variantyoutubevideo_set',
        'variant_set__variantsupply_set__supply__supplier',
        'reviews'
    )
    serializer_class = GalleryItemDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when retrieving and return with related products"""
        instance = self.get_object()
        instance.total_views += 1
        instance.save(update_fields=['total_views'])
        
        # Get response from parent class (related products are included in serializer)
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get gallery item by slug (SEO-friendly URL).",
        responses={
            200: GalleryItemDetailSerializer,
            404: 'Not Found'
        },
        tags=['Gallery Items']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VariantListView(generics.ListCreateAPIView):
    """
    List variants for a specific product or create a new variant.
    
    GET: Returns variants for a specific product (filter by product_id). No pagination.
    POST: Create a new variant (Admin/Staff only).
    """
    queryset = Variant.objects.filter(active=True).select_related('product')
    serializer_class = VariantSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'quantity', 'updated']
    ordering = ['-updated']
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product', None)
        is_best_seller = self.request.query_params.get('is_best_seller', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if is_best_seller is not None:
            queryset = queryset.filter(is_best_seller=is_best_seller.lower() == 'true')
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VariantCreateUpdateSerializer
        return VariantSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description="Get list of variants. Filter by product_id to get variants for a specific product. No pagination.",
        manual_parameters=[
            openapi.Parameter('product', openapi.IN_QUERY, description="Filter by product ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: VariantSerializer(many=True),
        },
        tags=['Variants']
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new variant. Admin access required.",
        request_body=VariantCreateUpdateSerializer,
        responses={
            201: VariantSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required'
        },
        security=[{'Bearer': []}],
        tags=['Variants']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class VariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a variant.
    
    GET: Get detailed information about a variant.
    PUT/PATCH: Update variant (Admin/Staff only).
    DELETE: Delete variant (Admin/Staff only).
    """
    queryset = Variant.objects.all().select_related('product').prefetch_related(
        'variantimage_set', 'variantvideo_set', 'variantyoutubevideo_set'
    )
    serializer_class = VariantSerializer
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VariantCreateUpdateSerializer
        return VariantSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description="Get detailed information about a variant including images and videos.",
        responses={
            200: VariantSerializer,
            404: 'Not Found'
        },
        tags=['Variants']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update variant. Admin access required.",
        request_body=VariantCreateUpdateSerializer,
        responses={
            200: VariantSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Variants']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update variant. Admin access required.",
        request_body=VariantCreateUpdateSerializer,
        responses={
            200: VariantSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Variants']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete variant. Admin access required.",
        responses={
            204: 'No Content - Successfully deleted',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Variants']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class CategoryListView(generics.ListAPIView):
    """
    List all categories.
    
    GET: Returns a hierarchical list of all categories. No pagination.
    """
    queryset = Category.objects.filter(level=0)  # Get root categories only
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination

    @swagger_auto_schema(
        operation_description="Get hierarchical list of all categories (tree structure). No pagination.",
        responses={
            200: CategorySerializer(many=True),
        },
        tags=['Categories']
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve a category.
    
    GET: Get detailed information about a category including children.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get category details including children categories.",
        responses={
            200: CategorySerializer,
            404: 'Not Found'
        },
        tags=['Categories']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ReviewListView(generics.ListCreateAPIView):
    """
    List reviews for a product or create a new review.
    
    GET: Returns reviews for a specific product (filter by product_id). No pagination.
    POST: Create a new review (Authenticated users only).
    """
    queryset = Review.objects.all().select_related('product', 'author').order_by('-date_added')
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_added', 'rating']
    ordering = ['-date_added']
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product', None)
        rating = self.request.query_params.get('rating', None)
        featured = self.request.query_params.get('featured', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if rating:
            queryset = queryset.filter(rating=rating)
        if featured is not None:
            queryset = queryset.filter(featured=featured.lower() == 'true')
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description="Get list of reviews. Filter by product_id to get reviews for a specific product. No pagination.",
        manual_parameters=[
            openapi.Parameter('product', openapi.IN_QUERY, description="Filter by product ID", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('rating', openapi.IN_QUERY, description="Filter by rating (1-5)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('featured', openapi.IN_QUERY, description="Filter featured reviews", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: ReviewSerializer(many=True),
        },
        tags=['Reviews']
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new review. Authentication required.",
        request_body=ReviewCreateSerializer,
        responses={
            201: ReviewSerializer,
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['Reviews']
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        # Return full review data using ReviewSerializer
        output_serializer = ReviewSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a review.
    
    GET: Get review details.
    PUT/PATCH: Update review (Owner or Admin only).
    DELETE: Delete review (Owner or Admin only).
    """
    queryset = Review.objects.all().select_related('product', 'author')
    serializer_class = ReviewSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """Filter queryset based on permissions"""
        # Check if Swagger is generating schema (fake view)
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Users can only update/delete their own reviews (unless admin)
            if self.request.user.is_staff:
                return Review.objects.all()
            if self.request.user.is_authenticated:
                return Review.objects.filter(author=self.request.user)
        return Review.objects.all()
    
    def perform_update(self, serializer):
        """Only allow updating own reviews unless admin"""
        instance = serializer.instance
        if not self.request.user.is_staff and instance.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own reviews.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only allow deleting own reviews unless admin"""
        if not self.request.user.is_staff and instance.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()

    @swagger_auto_schema(
        operation_description="Get review details.",
        responses={
            200: ReviewSerializer,
            404: 'Not Found'
        },
        tags=['Reviews']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update review. Owner or Admin access required.",
        request_body=ReviewCreateSerializer,
        responses={
            200: ReviewSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Can only update own reviews',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Reviews']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update review. Owner or Admin access required.",
        request_body=ReviewCreateSerializer,
        responses={
            200: ReviewSerializer,
            400: 'Bad Request - Invalid data provided',
            403: 'Forbidden - Can only update own reviews',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Reviews']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete review. Owner or Admin access required.",
        responses={
            204: 'No Content - Successfully deleted',
            403: 'Forbidden - Can only delete own reviews',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Reviews']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class WishedItemListView(generics.ListCreateAPIView):
    """
    List user's wishlist items or add item to wishlist.
    
    GET: Returns all items in the authenticated user's wishlist. No pagination.
    POST: Add a product to wishlist (Authenticated users only).
    """
    serializer_class = WishedItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_added', 'date_updated']
    ordering = ['-date_added']
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
        """Return only current user's wishlist items that are not unwished"""
        # Check if Swagger is generating schema (fake view)
        if getattr(self, 'swagger_fake_view', False):
            return WishedItem.objects.none()
        
        if self.request.user.is_authenticated:
            return WishedItem.objects.filter(
                user=self.request.user,
                is_unwished=False
            ).select_related('product', 'user').order_by('-date_added')
        return WishedItem.objects.none()

    @swagger_auto_schema(
        operation_description="Get current user's wishlist items. No pagination.",
        responses={
            200: WishedItemSerializer(many=True),
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['Wishlist']
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Add product to wishlist. Authentication required.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID to add to wishlist'),
            }
        ),
        responses={
            201: WishedItemSerializer,
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['Wishlist']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class WishedItemDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or remove a wishlist item.
    
    GET: Get wishlist item details.
    DELETE: Remove item from wishlist (Owner only).
    """
    serializer_class = WishedItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only current user's wishlist items"""
        # Check if Swagger is generating schema (fake view)
        if getattr(self, 'swagger_fake_view', False):
            return WishedItem.objects.none()
        
        if self.request.user.is_authenticated:
            return WishedItem.objects.filter(user=self.request.user)
        return WishedItem.objects.none()
    
    def perform_destroy(self, instance):
        """Mark as unwished instead of deleting"""
        instance.is_unwished = True
        instance.save()

    @swagger_auto_schema(
        operation_description="Get wishlist item details.",
        responses={
            200: WishedItemSerializer,
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Wishlist']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Remove item from wishlist. Owner access required.",
        responses={
            204: 'No Content - Successfully removed',
            403: 'Forbidden - Can only remove own wishlist items',
            404: 'Not Found'
        },
        security=[{'Bearer': []}],
        tags=['Wishlist']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class StockStatusAPIView(APIView):
    """
    API to get stock status of all products/variants.
    Returns products with their stock information.
    """
    permission_classes = [permissions.IsAdminUser]  # Only admins can view stock status
    
    def get(self, request):
        """Get stock status for all variants"""
        try:
            # Get filter parameters
            stock_filter = request.GET.get('filter', 'all')  # all, in_stock, out_of_stock, low_stock
            category_id = request.GET.get('category', None)
            search_query = request.GET.get('search', None)
            
            # Base queryset
            variants = Variant.objects.select_related('product', 'product__category').all()
            
            # Apply filters
            if category_id:
                variants = variants.filter(product__category_id=category_id)
            
            if search_query:
                variants = variants.filter(
                    Q(product__title__icontains=search_query) |
                    Q(title__icontains=search_query)
                )
            
            # Stock status filter
            if stock_filter == 'in_stock':
                variants = variants.filter(quantity__gt=0)
            elif stock_filter == 'out_of_stock':
                variants = variants.filter(quantity=0)
            elif stock_filter == 'low_stock':
                variants = variants.filter(quantity__gt=0, quantity__lte=10)
            
            # Serialize data
            serializer = VariantSerializer(variants, many=True, context={'request': request})
            
            # Calculate summary statistics
            total_variants = Variant.objects.count()
            in_stock_count = Variant.objects.filter(quantity__gt=0).count()
            out_of_stock_count = Variant.objects.filter(quantity=0).count()
            low_stock_count = Variant.objects.filter(quantity__gt=0, quantity__lte=10).count()
            total_quantity = Variant.objects.aggregate(total=Sum('quantity'))['total'] or 0
            
            return Response({
                'success': True,
                'summary': {
                    'total_variants': total_variants,
                    'in_stock': in_stock_count,
                    'out_of_stock': out_of_stock_count,
                    'low_stock': low_stock_count,
                    'total_quantity': total_quantity,
                },
                'variants': serializer.data,
                'count': variants.count(),
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

