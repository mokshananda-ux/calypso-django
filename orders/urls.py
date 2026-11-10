from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payment/', views.payment, name='payment'),
    path('stripe/create-checkout-session/', views.stripe_create_checkout_session, name='stripe_create_checkout_session'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('order_complete/', views.order_complete, name='order_complete'),
]