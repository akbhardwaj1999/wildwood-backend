from django.urls import path
from . import api_views

app_name = 'contact'

urlpatterns = [
    path('submit/', api_views.submit_contact_form, name='submit_contact_form'),
]

