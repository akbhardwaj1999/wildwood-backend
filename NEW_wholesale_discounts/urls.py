from django.urls import path
from . import views

app_name = 'NEW_wholesale_discounts'

urlpatterns = [
    # Wholesale request views
    path('request/', views.NEW_wholesale_request, name='wholesale_request'),
    path('status/', views.NEW_wholesale_status, name='wholesale_status'),
    path('dashboard/', views.NEW_wholesale_dashboard, name='wholesale_dashboard'),
    
    # Wholesale tiers
    path('tiers/', views.NEW_wholesale_tiers, name='wholesale_tiers'),
    
    # API endpoints
    path('api/discount/', views.NEW_wholesale_discount_api, name='wholesale_discount_api'),
]

