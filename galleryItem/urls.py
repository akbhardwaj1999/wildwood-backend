from django.urls import path
from . import views

app_name = 'galleryItem'

urlpatterns = [
    # Gallery Items APIs
    path('items/', views.GalleryItemListView.as_view(), name='galleryitem-list'),
    path('items/<int:pk>/', views.GalleryItemDetailView.as_view(), name='galleryitem-detail'),
    path('items/slug/<slug:slug>/', views.GalleryItemBySlugView.as_view(), name='galleryitem-by-slug'),
    
    # Variants APIs
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path('variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
    
    # Categories APIs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Reviews APIs
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    
    # Wishlist APIs
    path('wishlist/', views.WishedItemListView.as_view(), name='wishlist-list'),
    path('wishlist/<int:pk>/', views.WishedItemDetailView.as_view(), name='wishlist-detail'),
]
