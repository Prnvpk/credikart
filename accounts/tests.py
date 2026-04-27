from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationFlowTests(TestCase):
    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newcustomer',
                'password': 'safe-pass-123',
                'user_type': 'customer',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newcustomer', user_type='customer').exists())
        self.assertContains(response, 'Account created successfully. Please sign in.')

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(
            username='existinguser',
            password='safe-pass-123',
            user_type='customer',
        )

        response = self.client.post(
            reverse('register'),
            {
                'username': 'existinguser',
                'password': 'another-pass-123',
                'user_type': 'customer',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That username is already taken.')
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)

    def test_login_authenticates_and_redirects_to_dashboard(self):
        user = User.objects.create_user(
            username='shopowner',
            password='safe-pass-123',
            user_type='shopkeeper',
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'shopowner',
                'password': 'safe-pass-123',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_shows_error_for_invalid_credentials(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'missing-user',
                'password': 'bad-pass',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_redirects_logged_out_users(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_shows_role_for_logged_in_user(self):
        user = User.objects.create_user(
            username='customer1',
            password='safe-pass-123',
            user_type='customer',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer Dashboard')
        self.assertContains(response, 'Welcome, customer1')

    def test_logout_clears_session(self):
        user = User.objects.create_user(
            username='logoutuser',
            password='safe-pass-123',
            user_type='customer',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('logout'), follow=True)

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'You have been logged out.')
