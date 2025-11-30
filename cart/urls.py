from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='summary'),
    path('quick-add-to-cart/', views.QuickAddToCartView.as_view(), name='quick-add-to-cart'),
    path('increase-quantity/<pk>/', views.IncreaseQuantityView.as_view(), name='increase-quantity'),
    path('decrease-quantity/<pk>/', views.DecreaseQuantityView.as_view(), name='decrease-quantity'),
    path('update-quantity/', views.UpdateQuantityView.as_view(), name='update-quantity'),
    path('remove-from-cart/<pk>/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('shipping-cost/', views.ShippingCostView.as_view(), name='shipping-cost'),
    path('get-country-states/', views.GetCountryStates.as_view(), name='get-country-states'),
    path('get-state-cities/', views.GetStateCities.as_view(), name='get-state-cities'),
    path('update-tax/', views.UpdateTaxView.as_view(), name='update-tax'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('thank-you/', views.ThankYouView.as_view(), name='thank-you'),
    path('confirm-order/', views.ConfirmOrderView.as_view(), name='confirm-order'),
    path('order-list/', views.OrdersListView.as_view(), name='order-list'),
    path('order-detail/<str:reference_number>/', views.OrdersDetailView.as_view(), name='order-detail'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply-coupon'),
    path('recover/<str:reference_number>/', views.CartRecoveryView.as_view(), name='cart-recovery'),

]
