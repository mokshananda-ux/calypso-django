from django.urls import path

from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('edit_review/<int:product_id>/', views.edit_review, name='edit_review'),
    path('create_review/<int:product_id>/', views.create_review, name='create_review'),
]

