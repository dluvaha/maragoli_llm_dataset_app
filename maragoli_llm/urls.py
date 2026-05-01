"""
URL configuration for Maragoli LLM Dataset Collection App
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from datasets import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Dataset CRUD
    path('datasets/', views.dataset_list, name='dataset_list'),
    path('datasets/create/', views.dataset_create, name='dataset_create'),
    path('datasets/<int:pk>/edit/', views.dataset_update, name='dataset_update'),
    path('datasets/<int:pk>/delete/', views.dataset_delete, name='dataset_delete'),
    path('datasets/<int:pk>/validate/', views.dataset_validate_toggle, name='dataset_validate'),
    path('datasets/bulk-delete/', views.dataset_bulk_delete, name='dataset_bulk_delete'),
    path('datasets/bulk-validate/', views.dataset_bulk_validate, name='dataset_bulk_validate'),

    # Import/Export
    path('import/', views.import_preview, name='import_preview'),
    path('import/confirm/', views.import_confirm, name='import_confirm'),
    path('import/cancel/', views.import_cancel, name='import_cancel'),
    path('export/', views.export_page, name='export_page'),
    path('export/download/', views.export_download, name='export_download'),
    path('api/export-summary/', views.export_summary_api, name='export_summary_api'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Stats / Export API
    path('api/stats/', views.stats_api, name='stats_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
