from django.urls import path
from . import views

app_name = 'NEW_tax_calculator'

urlpatterns = [
    # Tax exemption views
    path('exemption/request/', views.NEW_tax_exemption_request, name='exemption_request'),
    path('exemption/status/', views.NEW_tax_exemption_status, name='exemption_status'),
    
    # Tax calculation API
    path('api/calculate/', views.NEW_tax_calculator_api, name='tax_calculator_api'),
    
    # Tax summary
    path('summary/<int:order_id>/', views.NEW_tax_summary, name='tax_summary'),
    
    # Public tax rates
    path('rates/', views.NEW_tax_rates_list, name='tax_rates_list'),
]

