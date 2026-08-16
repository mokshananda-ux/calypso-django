from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountRegistrationRedirectTests(TestCase):
    def test_register_redirects_to_login_with_verification_query(self):
        email = 'new.user@example.com'
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'New',
                'last_name': 'User',
                'email': email,
                'phone_number': '1234567890',
                'password': 'StrongPass123',
                'confirm_password': 'StrongPass123',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('login')}?command=verification&email={email}",
        )
