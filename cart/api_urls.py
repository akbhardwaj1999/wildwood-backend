"""
REST API URLs for Cart App
"""
from django.urls import path
from . import api_views

app_name = 'cart_api'

urlpatterns = [
    # Cart operations
    path('cart/', api_views.CartView.as_view(), name='cart'),
    path('cart/add-item/', api_views.add_to_cart, name='add-to-cart'),
    path('cart/update-item/<int:item_id>/', api_views.update_cart_item, name='update-cart-item'),
    path('cart/remove-item/<int:item_id>/', api_views.remove_from_cart, name='remove-from-cart'),
    path('cart/clear/', api_views.clear_cart, name='clear-cart'),
    
    # Address operations
    path('addresses/', api_views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', api_views.AddressDetailView.as_view(), name='address-detail'),
    
    # Order operations
    path('orders/', api_views.OrderListView.as_view(), name='order-list'),
    path('orders/<str:reference_number>/', api_views.OrderDetailView.as_view(), name='order-detail'),
    
    # Coupon operations
    path('coupons/apply/', api_views.apply_coupon, name='apply-coupon'),
    path('coupons/remove/', api_views.remove_coupon, name='remove-coupon'),
    
    # Admin coupon operations
    path('admin/coupons/', api_views.CouponListView.as_view(), name='admin-coupon-list'),
    path('admin/coupons/<int:pk>/', api_views.CouponDetailView.as_view(), name='admin-coupon-detail'),
]
