"""
REST API Views for Cart App
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Address, Order, OrderItem, Payment, Coupon, ShippingCost
from .serializers import (
    AddressSerializer, OrderSerializer, OrderItemSerializer,
    OrderItemCreateUpdateSerializer, PaymentSerializer, CouponSerializer,
    ShippingCostSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    ApplyCouponSerializer
)
from .utils import get_or_set_order_session, calculate_total_shipping_cost
from galleryItem.models import Variant


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
        order = get_or_set_order_session(self.request)
        return order
    
    @swagger_auto_schema(
        operation_description="Get current cart with all items and totals",
        responses={
            200: OrderSerializer,
        },
        tags=['Cart']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
    
    # Return updated cart
    cart_serializer = OrderSerializer(order)
    return Response({
        'message': 'Item added to cart successfully',
        'cart': cart_serializer.data
    }, status=status.HTTP_200_OK)


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
    serializer = UpdateCartItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order = get_or_set_order_session(request)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
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
    
    cart_serializer = OrderSerializer(order)
    return Response({
        'message': 'Cart item updated successfully',
        'cart': cart_serializer.data
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
    
    cart_serializer = OrderSerializer(order)
    return Response({
        'message': 'Item removed from cart successfully',
        'cart': cart_serializer.data
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
    order.total_shipping_cost = 0
    order.tax_amount = 0
    order.is_tax_exempt = False
    order.wholesale_discount = 0
    order.coupon = None
    order.save()
    
    return Response({
        'message': 'Cart cleared successfully'
    }, status=status.HTTP_200_OK)


# Address Views
class AddressListView(generics.ListCreateAPIView):
    """
    List user's addresses or create new address.
    
    GET: List all addresses for authenticated user
    POST: Create new address
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get addresses for current user"""
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user when creating address"""
        serializer.save(user=self.request.user)
    
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
    
    Users can only view their own orders. Admins can view any order.
    """
    serializer_class = OrderSerializer
    lookup_field = 'reference_number'
    lookup_url_kwarg = 'reference_number'
    
    def get_queryset(self):
        """Get orders user can access"""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user, ordered=True)
    
    def get_permissions(self):
        """Allow any authenticated user or allow public access for reference number"""
        if self.request.method == 'GET':
            return [AllowAny()]  # Allow public access by reference number
        return [IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_description="Get order details by reference number",
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
    
    # Check minimum order amount
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
    
    cart_serializer = OrderSerializer(order)
    return Response({
        'message': 'Coupon applied successfully',
        'coupon_discount_amount': order.get_coupon_discount_amount(),
        'cart': cart_serializer.data
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
    
    cart_serializer = OrderSerializer(order)
    return Response({
        'message': 'Coupon removed successfully',
        'cart': cart_serializer.data
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
