from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payment/', views.payment, name='payment'),
    path('paypal/create/', views.paypal_create_order, name='paypal_create_order'),
    path('paypal/capture/', views.paypal_capture_order, name='paypal_capture_order'),
    path('order_complete/', views.order_complete, name='order_complete'),
]