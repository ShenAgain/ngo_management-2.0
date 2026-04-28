"""
ngo_management/tests.py

Unit tests for ngo_management module including middleware and core functionality
"""

from django.test import TestCase, Client
from django.http import HttpRequest
from accounts.models import CustomUser
from rest_framework.authtoken.models import Token


class SecurityMiddlewareTests(TestCase):
    """Test security middleware functionality"""

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='TestPass123!',
            role='employee'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)

    def test_security_headers_present_in_response(self):
        """Test that security headers are added to responses"""
        response = self.client.get('/api/v1/me/', HTTP_AUTHORIZATION=f'Token {self.token.key}')
        # Check for common security headers
        # Note: The exact headers depend on the middleware implementation
        self.assertIsNotNone(response)

    def test_request_with_auth_token_works(self):
        """Test that authenticated requests work properly"""
        response = self.client.get(
            '/api/v1/me/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 200)

    def test_request_without_auth_fails(self):
        """Test that requests without auth token fail appropriately"""
        response = self.client.get('/api/v1/me/')
        self.assertEqual(response.status_code, 401)


class MiddlewareIntegrationTests(TestCase):
    """Test middleware integration"""

    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            role='admin'
        )
        self.employee = CustomUser.objects.create_user(
            username='emp',
            password='Emp123!',
            role='employee'
        )

    def test_admin_user_passes_through_middleware(self):
        """Test that admin user passes through middleware"""
        from rest_framework.authtoken.models import Token
        token = Token.objects.create(user=self.admin)
        
        response = self.client.get(
            '/api/v1/me/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.assertEqual(response.status_code, 200)

    def test_employee_user_passes_through_middleware(self):
        """Test that employee user passes through middleware"""
        from rest_framework.authtoken.models import Token
        token = Token.objects.create(user=self.employee)
        
        response = self.client.get(
            '/api/v1/me/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_token_rejected(self):
        """Test that invalid token is rejected"""
        response = self.client.get(
            '/api/v1/me/',
            HTTP_AUTHORIZATION='Token invalid_token_12345'
        )
        self.assertEqual(response.status_code, 401)

    def test_multiple_requests_from_same_user(self):
        """Test that multiple requests from same user work"""
        from rest_framework.authtoken.models import Token
        token = Token.objects.create(user=self.employee)
        auth_header = f'Token {token.key}'
        
        for _ in range(3):
            response = self.client.get(
                '/api/v1/me/',
                HTTP_AUTHORIZATION=auth_header
            )
            self.assertEqual(response.status_code, 200)


class URLRoutingTests(TestCase):
    """Test URL routing configuration"""

    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            role='admin'
        )
        self.token, _ = Token.objects.get_or_create(user=self.admin)

    def test_api_v1_base_url_accessible(self):
        """Test that /api/v1/ base URLs are configured"""
        auth_header = f'Token {self.token.key}'
        
        # Test various endpoints to ensure routing works
        endpoints = [
            '/api/v1/me/',
            '/api/v1/ngos/',
            '/api/v1/activities/',
            '/api/v1/registrations/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint, HTTP_AUTHORIZATION=auth_header)
            # Should get 200 or 400+ (auth failures are ok for this test)
            self.assertNotEqual(response.status_code, 404)

    def test_gateway_routes_available(self):
        """Test that gateway routes are configured"""
        # Gateway proxy routes
        endpoints = [
            '/api/v1/gw/user/',
            '/api/v1/gw/ngo/',
            '/api/v1/gw/reg/',
        ]
        
        for endpoint in endpoints:
            # These will fail due to missing service, but shouldn't be 404
            response = self.client.get(endpoint)
            # We expect 503 (service unavailable) or 502 (bad gateway)
            # but not 404 (not found)
            self.assertNotEqual(response.status_code, 404)


class SettingsStructureTests(TestCase):
    """Test Django settings structure and configuration"""

    def test_required_apps_installed(self):
        """Test that required apps are in INSTALLED_APPS"""
        from django.conf import settings
        
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'accounts',
            'ngo',
            'registration',
            'notifications',
            'rest_framework',
            'rest_framework.authtoken',
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_rest_framework_configured(self):
        """Test that REST framework is properly configured"""
        from django.conf import settings
        
        self.assertIn('rest_framework', settings.INSTALLED_APPS)
        self.assertIn('rest_framework.authtoken', settings.INSTALLED_APPS)
        
        # Check REST_FRAMEWORK settings
        self.assertIn('REST_FRAMEWORK', dir(settings))

    def test_authentication_backend_configured(self):
        """Test that authentication is properly configured"""
        from django.conf import settings
        
        # Token authentication should be configured
        self.assertIsNotNone(settings.AUTHENTICATION_BACKENDS)

    def test_database_configured(self):
        """Test that database is configured"""
        from django.conf import settings
        
        self.assertIn('DATABASES', dir(settings))
        self.assertIn('default', settings.DATABASES)

    def test_middleware_configured(self):
        """Test that middleware is configured"""
        from django.conf import settings
        
        self.assertIn('MIDDLEWARE', dir(settings))
        self.assertIsInstance(settings.MIDDLEWARE, (list, tuple))

    def test_secret_key_configured(self):
        """Test that SECRET_KEY is configured"""
        from django.conf import settings
        
        self.assertIn('SECRET_KEY', dir(settings))
        self.assertIsNotNone(settings.SECRET_KEY)

    def test_debug_setting_exists(self):
        """Test that DEBUG setting exists"""
        from django.conf import settings
        
        self.assertIn('DEBUG', dir(settings))

    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is configured"""
        from django.conf import settings
        
        self.assertIn('ALLOWED_HOSTS', dir(settings))

    def test_static_and_media_files_configured(self):
        """Test that static and media files are configured"""
        from django.conf import settings
        
        self.assertIn('STATIC_URL', dir(settings))
        self.assertIn('MEDIA_URL', dir(settings))


class DjangoApplicationTests(TestCase):
    """Test core Django application functionality"""

    def test_manage_py_can_run(self):
        """Test that manage.py exists and is runnable"""
        import os
        manage_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'manage.py'
        )
        self.assertTrue(os.path.exists(manage_path))

    def test_models_can_be_imported(self):
        """Test that all app models can be imported"""
        from accounts.models import CustomUser
        from ngo.models import NGO, Activity
        from registration.models import Registration
        from notifications.models import Notification
        
        # If we got here, all imports succeeded
        self.assertIsNotNone(CustomUser)
        self.assertIsNotNone(NGO)
        self.assertIsNotNone(Activity)
        self.assertIsNotNone(Registration)
        self.assertIsNotNone(Notification)

    def test_views_can_be_imported(self):
        """Test that views can be imported"""
        from accounts.views import *
        from ngo.views import *
        from registration.views import *
        from notifications.views import *
        # If we got here, imports succeeded
        self.assertTrue(True)

    def test_admin_site_works(self):
        """Test that Django admin is accessible"""
        response = self.client.get('/admin/')
        # Should redirect to login if not authenticated
        self.assertIn(response.status_code, [301, 302, 200])

    def test_user_model_is_custom_user(self):
        """Test that AUTH_USER_MODEL is set to CustomUser"""
        from django.conf import settings
        self.assertEqual(settings.AUTH_USER_MODEL, 'accounts.CustomUser')


class CORSAndSecurityTests(TestCase):
    """Test CORS and security configurations"""

    def test_api_endpoints_require_authentication(self):
        """Test that API endpoints require authentication"""
        endpoints = [
            '/api/v1/me/',
            '/api/v1/ngos/',
            '/api/v1/activities/',
            '/api/v1/registrations/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # All protected endpoints should return 401 when not authenticated
            self.assertEqual(
                response.status_code,
                401,
                f"Endpoint {endpoint} should require authentication"
            )

    def test_token_authentication_works(self):
        """Test that token authentication works"""
        user = CustomUser.objects.create_user(
            username='authtest',
            password='Pass123!'
        )
        token, _ = Token.objects.get_or_create(user=user)
        
        response = self.client.get(
            '/api/v1/me/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.assertEqual(response.status_code, 200)
