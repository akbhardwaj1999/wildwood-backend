from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset endpoints
    path('password-reset/', views.password_reset_request, name='password-reset-request'),
    path('password-reset/verify/', views.password_reset_verify, name='password-reset-verify'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='profile-update'),
    
    # Admin endpoints
    path('users/', views.UserListView.as_view(), name='user-list'),
]

