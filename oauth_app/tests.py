from django.test import TestCase
from django.conf import settings
from django.urls import reverse, resolve
from django.test import SimpleTestCase
from oauth_app.views import signin, logout_view
# Create your tests here.

class oauth_appTests(TestCase):

    def test_signin(self):
        response = self.client.get(reverse('signin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signin.html')

    def test_logoutview(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')