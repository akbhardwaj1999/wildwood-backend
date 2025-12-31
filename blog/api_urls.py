from django.urls import path
from . import api_views

app_name = 'blog'

urlpatterns = [
    path('posts/', api_views.BlogPostListView.as_view(), name='list'),
    path('posts/<slug:slug>/', api_views.BlogPostDetailView.as_view(), name='detail'),
    path('tags/', api_views.BlogTagListView.as_view(), name='tags'),
]

