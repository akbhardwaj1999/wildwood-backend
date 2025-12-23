from django.urls import path
from . import api_views

app_name = 'wholesale_api'

urlpatterns = [
    # User endpoints
    path('status/', api_views.WholesaleStatusView.as_view(), name='status'),
    path('request/', api_views.WholesaleRequestCreateView.as_view(), name='request-create'),
    path('requests/', api_views.WholesaleRequestListView.as_view(), name='request-list'),
    path('requests/<int:pk>/', api_views.WholesaleRequestDetailView.as_view(), name='request-detail'),
    path('tiers/', api_views.WholesaleTiersView.as_view(), name='tiers'),
    path('discount/calculate/', api_views.calculate_wholesale_discount, name='discount-calculate'),
    
    # Admin endpoints
    path('admin/requests/', api_views.AdminWholesaleRequestListView.as_view(), name='admin-request-list'),
    path('admin/requests/<int:pk>/', api_views.AdminWholesaleRequestDetailView.as_view(), name='admin-request-detail'),
]

