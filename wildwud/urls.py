"""
URL configuration for wildwud project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions

# Optional Swagger imports
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    
    # Swagger Schema View
    schema_view = get_schema_view(
       openapi.Info(
          title="WildWud API",
          default_version='v1',
          description="REST API documentation for WildWud Backend. Use the 'Authorize' button to authenticate with JWT tokens.",
          terms_of_service="https://www.google.com/policies/terms/",
          contact=openapi.Contact(email="contact@wildwud.local"),
          license=openapi.License(name="BSD License"),
       ),
       public=True,
       permission_classes=(permissions.AllowAny,),
       patterns=[
          path('api/accounts/', include('accounts.urls')),
          path('api/gallery/', include('galleryItem.urls')),
          path('api/cart/', include('cart.api_urls')),
          path('api/tax/', include('NEW_tax_calculator.api_urls')),
       ],
    )
    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False
    schema_view = None

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/gallery/', include('galleryItem.urls')),
    path('api/cart/', include('cart.api_urls')),
    path('api/tax/', include('NEW_tax_calculator.api_urls')),
]

# Smart Selects URLs (required for chained foreign keys in admin)
# This enables chained dropdowns in Django admin (Country -> State -> City)
try:
    from smart_selects.urls import urlpatterns as smart_selects_urls
    urlpatterns += smart_selects_urls
except (ImportError, AttributeError):
    # If smart-selects is not installed or URLs not available, skip
    # The admin will still work but chained dropdowns won't function
    pass

# Swagger Documentation URLs (only if drf_yasg is installed)
if SWAGGER_AVAILABLE and schema_view:
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

# Serve media files during development
# In production, serve media files using a web server (nginx, Apache, etc.)
# This only works when DEBUG=True (local development)
# On production (PythonAnywhere), media files are served by the web server
if settings.DEBUG:
    # Serve media files (images, uploads, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve files from products/ folder when URL starts with /products/
    urlpatterns += static('/products/', document_root=settings.BASE_DIR / 'products')
