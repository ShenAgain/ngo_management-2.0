"""
accounts/tests/test_api_endpoints.py

Minimal API tests for the accounts service.
"""

from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import CustomUser


@override_settings(ROOT_URLCONF="ngo_management.urls_user_service")
class AccountsMeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username="api_user",
            password="ApiUser123!",
            email="api_user@example.com",
            role="employee",
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)

    def test_me_endpoint_returns_authenticated_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "api_user")
        self.assertEqual(response.data["role"], "employee")

    def test_me_endpoint_rejects_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid_token")
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, 401)
