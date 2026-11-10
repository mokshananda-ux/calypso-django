from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Order, Payment
from .views import _finalize_stripe_session


class StripeCheckoutTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			first_name='Test',
			last_name='Customer',
			username='test-customer',
			email='customer@example.com',
			password='test-password',
		)
		self.user.is_active = True
		self.user.save(update_fields=['is_active'])
		self.order = Order.objects.create(
			user=self.user,
			order_number='202610101',
			first_name='Test',
			last_name='Customer',
			phone='5551234',
			email='customer@example.com',
			address_line_1='1 Test Street',
			state='State',
			city='City',
			order_total=Decimal('102.00'),
			tax=Decimal('2.00'),
			ip='127.0.0.1',
		)
		self.client.force_login(self.user)

	@override_settings(STRIPE_SECRET_KEY='sk_test_example')
	@patch('orders.views.stripe.checkout.Session.create')
	def test_create_checkout_session_uses_order_total(self, create_session):
		create_session.return_value.url = 'https://checkout.stripe.com/test'

		response = self.client.post(reverse('stripe_create_checkout_session'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['url'], 'https://checkout.stripe.com/test')
		request_data = create_session.call_args.kwargs
		self.assertEqual(request_data['line_items'][0]['price_data']['unit_amount'], 10200)
		self.assertEqual(request_data['metadata']['order_id'], str(self.order.pk))
		self.assertEqual(request_data['idempotency_key'], f'checkout-order-{self.order.pk}')

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_finalizing_paid_session_is_idempotent(self):
		checkout_session = {
			'payment_status': 'paid',
			'metadata': {'order_id': str(self.order.pk)},
			'client_reference_id': str(self.user.pk),
			'currency': 'usd',
			'amount_total': 10200,
			'payment_intent': 'pi_test_payment',
			'id': 'cs_test_session',
		}

		order, payment = _finalize_stripe_session(checkout_session)
		repeated_order, repeated_payment = _finalize_stripe_session(checkout_session)

		self.assertTrue(order.is_ordered)
		self.assertEqual(order, repeated_order)
		self.assertEqual(payment, repeated_payment)
		self.assertEqual(Payment.objects.count(), 1)
		self.assertEqual(payment.payment_method, 'Stripe')
