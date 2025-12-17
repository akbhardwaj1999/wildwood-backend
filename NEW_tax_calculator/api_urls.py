from django.urls import path
from . import api_views

app_name = 'tax_api'

urlpatterns = [
    # Location APIs
    path('countries/', api_views.CountriesAPIView.as_view(), name='countries'),
    path('states/<int:country_id>/', api_views.StatesAPIView.as_view(), name='states'),
    path('cities/<int:state_id>/', api_views.CitiesAPIView.as_view(), name='cities'),
    
    # Tax Calculation APIs
    path('calculate/', api_views.calculate_tax_api, name='calculate-tax'),
    path('update-address/', api_views.update_address_and_calculate_tax, name='update-address-tax'),
]

