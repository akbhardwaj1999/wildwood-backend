"""
REST API Views for Cart App
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

# Optional swagger imports
try:
    from drf_yasg.utils import swagger_auto_schema
    from drf_yasg import openapi
    SWAGGER_AVAILABLE = True
except ImportError:
    # Create dummy decorators if drf_yasg is not installed
    def swagger_auto_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class openapi:
        class Response:
            def __init__(self, *args, **kwargs):
                pass
    
    SWAGGER_AVAILABLE = False
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import Address, Order, OrderItem, Payment, Coupon, ShippingCost
from .serializers import (
    AddressSerializer, OrderSerializer, OrderItemSerializer,
    OrderItemCreateUpdateSerializer, PaymentSerializer, CouponSerializer,
    ShippingCostSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    ApplyCouponSerializer, CreatePaymentSerializer
)
from .utils import get_or_set_order_session, calculate_total_shipping_cost
from galleryItem.models import Variant
from django.conf import settings


class CartView(generics.RetrieveAPIView):
    """
    Get current user's cart (order).
    
    Returns the current cart with all items, pricing, and totals.
    If user is authenticated, returns their cart. Otherwise, returns session-based cart.
    """
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    
    def get_object(self):
        """Get or create cart for current user/session"""
        from django.db.models import Prefetch
        from django.conf import settings
        
        # Debug: Log session info
        session_key = self.request.session.session_key
        order_id = self.request.session.get('order_id', None)
        print(f"DEBUG CartView - Session key: {session_key}, Order ID from session: {order_id}")
        
        order = get_or_set_order_session(self.request)
        
        # Ensure session is saved
        self.request.session['order_id'] = order.id
        self.request.session.modified = True
        self.request.session.save()
        
        # Prefetch items with related variant and product data
        order = Order.objects.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
        ).get(id=order.id)
        
        print(f"DEBUG CartView - Order ID: {order.id}, Items count: {order.items.count()}")
        
        return order
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @swagger_auto_schema(
        operation_description="Get current cart with all items and totals",
        responses={
            200: OrderSerializer,
        },
        tags=['Cart']
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Explicitly set session cookie in response
        from django.conf import settings
        if request.session.session_key:
            response.set_cookie(
                settings.SESSION_COOKIE_NAME,
                request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                domain=settings.SESSION_COOKIE_DOMAIN,
                path=settings.SESSION_COOKIE_PATH,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
        
        return response


@swagger_auto_schema(
    method='post',
    operation_description="Add item to cart. If item already exists, increases quantity.",
    request_body=AddToCartSerializer,
    responses={
        200: openapi.Response('Success', OrderSerializer),
        400: 'Bad Request - Invalid data or variant not available',
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """Add item to cart"""
    serializer = AddToCartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    variant = serializer.validated_data['variant_id']
    quantity = serializer.validated_data.get('quantity', 1)
    
    # Check if variant is in stock
    if variant.quantity <= 0:
        return Response({
            'error': 'This variant is out of stock.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create cart
    order = get_or_set_order_session(request)
    
    # Check if item already exists in cart
    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        variant=variant,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Item already exists, increase quantity
        order_item.quantity += quantity
        order_item.save()
    
    # Reset abandoned cart email counters if user is engaging
    if order.abandoned_email_count > 0:
        current_time = timezone.now()
        Order.objects.filter(id=order.id).update(
            start_date=current_time,
            last_updated=current_time,
            abandoned_email_count=0,
            abandoned_email_sent=False,
            abandoned_email_sent_at=None,
            total_shipping_cost=0
        )
        order.refresh_from_db()
    else:
        order.total_shipping_cost = 0
        order.save(update_fields=['total_shipping_cost'])
    
    # IMPORTANT: Save session to ensure order_id is persisted
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # IMPORTANT: Refresh order from DB to get updated items
    order.refresh_from_db()
    
    # Prefetch related items to ensure they're loaded
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    # Return updated cart
    cart_serializer = OrderSerializer(order, context={'request': request})
    response = Response({
        'message': 'Item added to cart successfully',
        'cart': cart_serializer.data,
        'order_id': order.id  # Also return order_id for debugging
    }, status=status.HTTP_200_OK)
    
    # Explicitly set session cookie in response
    from django.conf import settings
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        request.session.session_key,
        max_age=settings.SESSION_COOKIE_AGE,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path=settings.SESSION_COOKIE_PATH,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    
    return response


@swagger_auto_schema(
    method='put',
    operation_description="Update cart item quantity",
    request_body=UpdateCartItemSerializer,
    responses={
        200: openapi.Response('Success', OrderSerializer),
        400: 'Bad Request',
        404: 'Not Found - Cart item not found',
    },
    tags=['Cart']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    order = get_or_set_order_session(request)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    # Pass order_item to serializer context for stock validation
    serializer = UpdateCartItemSerializer(data=request.data, context={'order_item': order_item})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order_item.quantity = serializer.validated_data['quantity']
    order_item.save()
    
    # Reset abandoned cart email counters
    if order.abandoned_email_count > 0:
        current_time = timezone.now()
        Order.objects.filter(id=order.id).update(
            start_date=current_time,
            last_updated=current_time,
            abandoned_email_count=0,
            abandoned_email_sent=False,
            abandoned_email_sent_at=None,
            total_shipping_cost=0
        )
        order.refresh_from_db()
    else:
        order.total_shipping_cost = 0
        order.save(update_fields=['total_shipping_cost'])
    
    # Save order_id to session
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # Refresh order to get updated items
    order.refresh_from_db()
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    cart_serializer = OrderSerializer(order, context={'request': request})
    return Response({
        'message': 'Cart item updated successfully',
        'cart': cart_serializer.data,
        'order_id': order.id
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    operation_description="Remove item from cart",
    responses={
        200: openapi.Response('Success', OrderSerializer),
        404: 'Not Found - Cart item not found',
    },
    tags=['Cart']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    order = get_or_set_order_session(request)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    order_item.delete()
    
    # Refresh order to check if cart is now empty
    order.refresh_from_db()
    
    # If cart is now empty, clear coupon and all discounts
    if not order.items.exists():
        order.coupon = None
        if 'coupon_applied_at' in request.session:
            del request.session['coupon_applied_at']
        order.total_shipping_cost = 0
        order.tax_amount = 0
        order.is_tax_exempt = False
        order.wholesale_discount = 0
        order.save(update_fields=['coupon', 'total_shipping_cost', 'tax_amount', 'is_tax_exempt', 'wholesale_discount'])
    else:
        # Reset abandoned cart email counters
        if order.abandoned_email_count > 0:
            current_time = timezone.now()
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            order.refresh_from_db()
        else:
            order.total_shipping_cost = 0
            order.save(update_fields=['total_shipping_cost'])
    
    # Save order_id to session
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # Refresh order to get updated items
    order.refresh_from_db()
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    cart_serializer = OrderSerializer(order, context={'request': request})
    return Response({
        'message': 'Item removed from cart successfully',
        'cart': cart_serializer.data,
        'order_id': order.id
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    operation_description="Clear entire cart (remove all items)",
    responses={
        200: 'Success - Cart cleared',
    },
    tags=['Cart']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_cart(request):
    """Clear entire cart"""
    order = get_or_set_order_session(request)
    order.items.all().delete()
    
    # Clear coupon and session flag
    order.coupon = None
    if 'coupon_applied_at' in request.session:
        del request.session['coupon_applied_at']
    
    # Clear all discounts and shipping
    order.total_shipping_cost = 0
    order.tax_amount = 0
    order.is_tax_exempt = False
    order.wholesale_discount = 0
    order.save()
    
    # Save order_id to session
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # Refresh order
    order.refresh_from_db()
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    cart_serializer = OrderSerializer(order, context={'request': request})
    return Response({
        'message': 'Cart cleared successfully',
        'cart': cart_serializer.data,
        'order_id': order.id
    }, status=status.HTTP_200_OK)


# Address Views
class AddressListView(generics.ListCreateAPIView):
    """
    List user's addresses or create new address.
    
    GET: List all addresses for authenticated user
    POST: Create new address (allows guest users for checkout)
    """
    serializer_class = AddressSerializer
    permission_classes = [AllowAny]  # Allow guest checkout
    
    def get_queryset(self):
        """Get addresses for current user (if authenticated)"""
        if self.request.user.is_authenticated:
            return Address.objects.filter(user=self.request.user)
        return Address.objects.none()  # Guest users can't list addresses
    
    def perform_create(self, serializer):
        """Set user when creating address (None for guest users)"""
        user = self.request.user if self.request.user.is_authenticated else None
        address = serializer.save(user=user)
        
        # If this address is set as default, unset all other default addresses for this user
        if address.default and user:
            Address.objects.filter(user=user, default=True).exclude(pk=address.pk).update(default=False)
    
    @swagger_auto_schema(
        operation_description="List all addresses for authenticated user",
        responses={200: AddressSerializer(many=True)},
        tags=['Addresses']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create new address",
        request_body=AddressSerializer,
        responses={201: AddressSerializer},
        tags=['Addresses']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete address.
    
    GET: Get address details
    PUT/PATCH: Update address
    DELETE: Delete address
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get addresses for current user only"""
        return Address.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        """Update address and handle default address logic"""
        address = serializer.save()
        
        # If this address is set as default, unset all other default addresses for this user
        if address.default and address.user:
            Address.objects.filter(user=address.user, default=True).exclude(pk=address.pk).update(default=False)
    
    @swagger_auto_schema(
        operation_description="Get address details",
        responses={200: AddressSerializer, 404: 'Not Found'},
        tags=['Addresses']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update address",
        request_body=AddressSerializer,
        responses={200: AddressSerializer, 404: 'Not Found'},
        tags=['Addresses']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update address",
        request_body=AddressSerializer,
        responses={200: AddressSerializer, 404: 'Not Found'},
        tags=['Addresses']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete address",
        responses={204: 'No Content', 404: 'Not Found'},
        tags=['Addresses']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# Order Views (for viewing order history)
class OrderListView(generics.ListAPIView):
    """
    List user's orders.
    
    Returns all finalized orders for authenticated user.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get orders for current user"""
        return Order.objects.filter(
            user=self.request.user,
            ordered=True
        ).order_by('-ordered_date')
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @swagger_auto_schema(
        operation_description="List all orders for authenticated user",
        responses={200: OrderSerializer(many=True)},
        tags=['Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve order details by reference number.
    
    Users can view their own orders. Guest users can view orders by reference number.
    Admins can view any order.
    """
    serializer_class = OrderSerializer
    lookup_field = 'reference_number'
    lookup_url_kwarg = 'reference_number'
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Get orders user can access"""
        # Admins can see all orders
        if self.request.user.is_staff:
            return Order.objects.all()
        
        # Authenticated users can see their own orders
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user, ordered=True)
        
        # Guest users: Allow access by reference number only (for order confirmation)
        # We'll filter in get_object() method to check session
        return Order.objects.filter(ordered=True)
    
    def get_object(self):
        """Override to handle guest user access via session"""
        reference_number = self.kwargs.get(self.lookup_url_kwarg)
        
        try:
            # Try to get order by reference number
            order = Order.objects.get(
                reference_number=reference_number,
                ordered=True
            )
            
            # Check access permissions
            # If user is authenticated, must be their order
            if self.request.user.is_authenticated and not self.request.user.is_staff:
                if order.user != self.request.user:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You don't have permission to view this order.")
            
            # For guest users, allow access (they can view by reference number)
            # This is safe because reference numbers are unique and hard to guess
            
            return order
        except Order.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Order not found.")
    
    def get_permissions(self):
        """Allow any user (including guests) to view order by reference number"""
        if self.request.method == 'GET':
            return [AllowAny()]  # Allow public access by reference number
        return [IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_description="Get order details by reference number. Guest users can access by reference number.",
        responses={200: OrderSerializer, 404: 'Not Found'},
        tags=['Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# Coupon Views
@swagger_auto_schema(
    method='post',
    operation_description="Apply coupon to cart",
    request_body=ApplyCouponSerializer,
    responses={
        200: openapi.Response('Success', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'coupon_discount_amount': openapi.Schema(type=openapi.TYPE_STRING),
                'cart': OrderSerializer
            }
        )),
        400: 'Bad Request - Invalid coupon or conditions not met',
    },
    tags=['Coupons']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def apply_coupon(request):
    """Apply coupon to cart"""
    serializer = ApplyCouponSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    code = serializer.validated_data['code']
    order = get_or_set_order_session(request)
    
    # Check if wholesale discount exists
    if order.wholesale_discount > 0:
        return Response({
            'error': 'Coupons cannot be used with wholesale discounts.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        coupon = Coupon.objects.get(code=code, active=True)
    except Coupon.DoesNotExist:
        return Response({
            'error': 'Coupon code is invalid.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check single use per user
    if coupon.single_use_per_user:
        if not request.user.is_authenticated:
            return Response({
                'error': 'Please login to apply for this coupon.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Order.objects.filter(user=request.user, coupon=coupon).exclude(
            status=Order.NOT_FINALIZED
        ).exists():
            return Response({
                'error': 'This coupon has been consumed before.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if order has items
    if not order.items.exists():
        return Response({
            'error': 'Cart is empty. Add items to cart before applying coupon.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check minimum order amount (only if minimum_order_amount > 0)
    if coupon.minimum_order_amount > 0:
        subtotal = order.get_raw_subtotal()
        if subtotal < coupon.minimum_order_amount:
            return Response({
                'error': f'The minimum order amount should be ${coupon.minimum_order_amount} for this coupon.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Apply coupon
    order.coupon = coupon
    order.save(update_fields=['coupon'])
    # Mark coupon as applied in session to prevent get_or_set_order_session from clearing it
    request.session['coupon_applied_at'] = timezone.now().isoformat()
    
    # Save order_id to session
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # Refresh order
    order.refresh_from_db()
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    cart_serializer = OrderSerializer(order, context={'request': request})
    return Response({
        'message': 'Coupon applied successfully',
        'coupon_discount_amount': order.get_coupon_discount_amount(),
        'cart': cart_serializer.data,
        'order_id': order.id
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    operation_description="Remove coupon from cart",
    responses={
        200: openapi.Response('Success', OrderSerializer),
    },
    tags=['Coupons']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_coupon(request):
    """Remove coupon from cart"""
    # Get order ID from session first to avoid get_or_set_order_session clearing coupon
    order_id = request.session.get('order_id')
    if not order_id:
        return Response({
            'error': 'No cart found.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, ordered=False)
    except Order.DoesNotExist:
        return Response({
            'error': 'Cart not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Clear coupon_applied_at from session since we're removing the coupon
    if 'coupon_applied_at' in request.session:
        del request.session['coupon_applied_at']
    
    # Remove coupon
    order.coupon = None
    order.save(update_fields=['coupon'])
    
    # Save order_id to session
    request.session['order_id'] = order.id
    request.session.modified = True
    request.session.save()
    
    # Refresh order
    order.refresh_from_db()
    from django.db.models import Prefetch
    order = Order.objects.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('variant', 'variant__product').all())
    ).get(id=order.id)
    
    cart_serializer = OrderSerializer(order, context={'request': request})
    return Response({
        'message': 'Coupon removed successfully',
        'cart': cart_serializer.data,
        'order_id': order.id
    }, status=status.HTTP_200_OK)


# Admin Views
class CouponListView(generics.ListCreateAPIView):
    """
    List all coupons or create new coupon (Admin only).
    """
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    queryset = Coupon.objects.all()
    
    @swagger_auto_schema(
        operation_description="List all coupons (Admin only)",
        responses={200: CouponSerializer(many=True)},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create new coupon (Admin only)",
        request_body=CouponSerializer,
        responses={201: CouponSerializer},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete coupon (Admin only).
    """
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    queryset = Coupon.objects.all()
    
    @swagger_auto_schema(
        operation_description="Get coupon details (Admin only)",
        responses={200: CouponSerializer, 404: 'Not Found'},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update coupon (Admin only)",
        request_body=CouponSerializer,
        responses={200: CouponSerializer, 404: 'Not Found'},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update coupon (Admin only)",
        request_body=CouponSerializer,
        responses={200: CouponSerializer, 404: 'Not Found'},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete coupon (Admin only)",
        responses={204: 'No Content', 404: 'Not Found'},
        security=[{'Bearer': []}],
        tags=['Coupons (Admin)']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_description="Process payment for order (Stripe or PayPal)",
    request_body=CreatePaymentSerializer,
    responses={
        200: openapi.Response('Success', PaymentSerializer),
        400: 'Bad Request - Invalid payment data',
        404: 'Not Found - Order not found',
    },
    tags=['Payment']
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow guest checkout
def process_payment(request):
    """
    Process payment for an order.
    Supports both Stripe (card) and PayPal payments.
    """
    serializer = CreatePaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order = get_or_set_order_session(request)
    
    # Check if order has items
    if not order.items.exists():
        return Response(
            {'error': 'Order is empty. Please add items to cart first.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if order already has a successful payment
    existing_payment = Payment.objects.filter(order=order, successful=True).first()
    if existing_payment:
        return Response(
            {'error': 'Order already has a successful payment.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    payment_method = serializer.validated_data['payment_method']
    address_id = serializer.validated_data.get('address_id')
    
    # Set shipping address if provided
    if address_id:
        try:
            address = Address.objects.get(id=address_id)
            order.shipping_address = address
            order.save(update_fields=['shipping_address'])
        except Address.DoesNotExist:
            return Response(
                {'error': 'Address not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Get order total
    order_total = float(order.get_raw_total())
    
    # Process payment based on method
    if payment_method == Payment.STRIPE:
        # Stripe payment processing
        stripe_token = serializer.validated_data.get('stripe_token')
        if not stripe_token:
            return Response(
                {'error': 'Stripe token is required for card payment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate Stripe API here
        # For now, we'll simulate a successful payment
        # In production, you would:
        # 1. Use stripe library to charge the card
        # 2. Get transaction ID from Stripe
        # 3. Store the response
        
        transaction_id = f"stripe_{order.reference_number}_{timezone.now().timestamp()}"
        payment_successful = True  # In production, this comes from Stripe API response
        raw_response = f"Stripe payment processed. Token: {stripe_token[:20]}..."
        
    elif payment_method == Payment.PAYPAL:
        # PayPal payment processing
        paypal_order_id = serializer.validated_data.get('paypal_order_id')
        paypal_email = serializer.validated_data.get('paypal_email', '')
        
        # Check if PayPal credentials are configured (optional for simulation mode)
        # For now, we allow simulation mode even without credentials
        # Payment processing works in simulation mode regardless of credentials
        paypal_configured = bool(getattr(settings, 'PAYPAL_CLIENT_ID', ''))
        
        # Generate order ID if not provided (for simulation/testing)
        if not paypal_order_id:
            paypal_order_id = f"PAYPAL_{order.reference_number}_{timezone.now().timestamp()}"
        
        # TODO: Integrate PayPal API here
        # For now, we'll simulate a successful payment
        # In production, you would:
        # 1. Verify PayPal order with PayPal API
        # 2. Capture the payment
        # 3. Get transaction ID from PayPal
        # 4. Store the response
        
        transaction_id = paypal_order_id
        payment_successful = True  # In production, this comes from PayPal API response
        raw_response = f"PayPal payment processed. Order ID: {paypal_order_id}"
    
    else:
        return Response(
            {'error': 'Invalid payment method.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create payment record
    payment = Payment.objects.create(
        order=order,
        payment_method=payment_method,
        amount=order_total,
        successful=payment_successful,
        transaction_id=transaction_id,
        raw_response=raw_response
    )
    
    # If payment successful, mark order as ordered and update stock
    if payment_successful:
        with transaction.atomic():
            # Update order status
            order.ordered = True
            order.ordered_date = timezone.now()
            order.status = Order.ORDERED
            order.save(update_fields=['ordered', 'ordered_date', 'status'])
            
            # Update product stock
            for item in order.items.all():
                # Update variant quantity
                item.variant.quantity = item.variant.quantity - item.quantity
                item.variant.save()
                
                # Update supplies stock if needed
                for ps in item.variant.variantsupply_set.all():
                    ps.supply.quantity = ps.supply.quantity - (ps.quantity_required * item.quantity)
                    ps.supply.save()
            
            # Send order confirmation email (if user exists)
            if order.user:
                try:
                    from .utils import send_new_order_email
                    send_new_order_email(order)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send order email: {str(e)}")
            
            # Send out of stock email if needed
            try:
                from mainsite.tasks import send_out_of_stock_email
                send_out_of_stock_email(notify_all_in_stock=False)
            except ImportError:
                # mainsite module not available, skip email
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("mainsite module not available, skipping out of stock email")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send out of stock email: {str(e)}")
        
        # Clear session order_id so a new cart can be created
        request.session.pop('order_id', None)
        request.session.save()
    
    payment_serializer = PaymentSerializer(payment)
    return Response({
        'message': 'Payment processed successfully' if payment_successful else 'Payment failed',
        'payment': payment_serializer.data,
        'order': OrderSerializer(order).data
    }, status=status.HTTP_200_OK if payment_successful else status.HTTP_400_BAD_REQUEST)
