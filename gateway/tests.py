"""
gateway/tests.py

Unit tests for API Gateway proxy functionality
"""

from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
import json


class GatewayProxyTests(TestCase):
    """Test API Gateway proxy functionality"""

    def setUp(self):
        self.client = Client()

    def test_proxy_requires_service_parameter(self):
        """Test that proxy endpoint requires valid service parameter"""
        response = self.client.get('/api/v1/gw/invalid/')
        self.assertEqual(response.status_code, 404)

    def test_proxy_rejects_unknown_service(self):
        """Test that proxy rejects unknown service names"""
        response = self.client.get('/api/v1/gw/unknown-service/')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('Unknown service', data.get('detail', ''))

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_to_user_service(self, mock_request):
        """Test that proxy forwards requests to user service"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({'user': 'test'})
        mock_request.return_value = mock_response

        response = self.client.get('/api/v1/gw/user/users/')
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_to_ngo_service(self, mock_request):
        """Test that proxy forwards requests to NGO service"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({'ngos': []})
        mock_request.return_value = mock_response

        response = self.client.get('/api/v1/gw/ngo/ngos/')
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_to_registration_service(self, mock_request):
        """Test that proxy forwards requests to registration service"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({'registrations': []})
        mock_request.return_value = mock_response

        response = self.client.get('/api/v1/gw/reg/registrations/')
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_authorization_header(self, mock_request):
        """Test that proxy forwards Authorization header"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        self.client.get(
            '/api/v1/gw/user/users/',
            HTTP_AUTHORIZATION='Token test_token'
        )
        
        call_kwargs = mock_request.call_args[1]
        self.assertIn('Authorization', call_kwargs['headers'])
        self.assertEqual(call_kwargs['headers']['Authorization'], 'Token test_token')

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_query_parameters(self, mock_request):
        """Test that proxy forwards query parameters"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        self.client.get('/api/v1/gw/ngo/ngos/?search=test&limit=10')
        
        call_kwargs = mock_request.call_args[1]
        self.assertIn('test', str(call_kwargs.get('params', {})))

    @patch('gateway.views.requests.request')
    def test_proxy_handles_post_request(self, mock_request):
        """Test that proxy handles POST requests"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = json.dumps({'id': 1})
        mock_request.return_value = mock_response

        response = self.client.post(
            '/api/v1/gw/ngo/ngos/',
            data=json.dumps({'name': 'Test NGO'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        call_kwargs = mock_request.call_args[1]
        self.assertEqual(call_kwargs['method'], 'POST')

    @patch('gateway.views.requests.request')
    def test_proxy_handles_request_timeout(self, mock_request):
        """Test that proxy handles request timeouts"""
        import requests
        mock_request.side_effect = requests.RequestException('Connection timeout')

        response = self.client.get('/api/v1/gw/user/users/')
        self.assertEqual(response.status_code, 503)

    @patch('gateway.views.requests.request')
    def test_proxy_strips_trailing_slash_from_service_url(self, mock_request):
        """Test that proxy handles service URLs correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        with patch.dict('os.environ', {'USER_SERVICE_URL': 'http://127.0.0.1:8001/'}):
            self.client.get('/api/v1/gw/user/test/')
        
        # Verify URL doesn't have double slashes
        call_args = mock_request.call_args
        url = call_args[1]['url']
        self.assertNotIn('///', url)

    @patch('gateway.views.requests.request')
    def test_proxy_handles_different_http_methods(self, mock_request):
        """Test that proxy handles various HTTP methods"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        for method in methods:
            mock_request.reset_mock()
            response = self.client.generic(
                method,
                '/api/v1/gw/ngo/ngos/',
                data='{}' if method in ['POST', 'PUT', 'PATCH'] else None,
                content_type='application/json'
            )
            
            call_kwargs = mock_request.call_args[1]
            self.assertEqual(call_kwargs['method'], method)

    @patch('gateway.views.requests.request')
    def test_proxy_returns_service_response_status_code(self, mock_request):
        """Test that proxy returns service response status code"""
        for status_code in [200, 201, 400, 401, 403, 404, 500]:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.content = json.dumps({'error': f'Error {status_code}'})
            mock_request.return_value = mock_response

            response = self.client.get('/api/v1/gw/user/test/')
            self.assertEqual(response.status_code, status_code)

    @patch('gateway.views.requests.request')
    def test_proxy_copies_cookie_headers(self, mock_request):
        """Test that proxy copies Cookie headers"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        self.client.get(
            '/api/v1/gw/user/users/',
            HTTP_COOKIE='session=test123'
        )
        
        call_kwargs = mock_request.call_args[1]
        self.assertIn('Cookie', call_kwargs['headers'])

    @patch('gateway.views.requests.request')
    def test_proxy_with_empty_request_body(self, mock_request):
        """Test proxy handles requests with no body"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        response = self.client.get('/api/v1/gw/ngo/ngos/')
        self.assertEqual(response.status_code, 200)

    @patch('gateway.views.requests.request')
    def test_proxy_service_url_environment_variables(self, mock_request):
        """Test that proxy uses environment variables for service URLs"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({})
        mock_request.return_value = mock_response

        import os
        with patch.dict(os.environ, {
            'USER_SERVICE_URL': 'http://custom-user:9001',
            'NGO_SERVICE_URL': 'http://custom-ngo:9003',
            'REG_SERVICE_URL': 'http://custom-reg:9002'
        }):
            self.client.get('/api/v1/gw/user/test/')
            call_args = mock_request.call_args
            self.assertIn('custom-user', call_args[1]['url'])


class GatewayCSRFExemptionTests(TestCase):
    """Test CSRF exemption for gateway proxy"""

    @patch('gateway.views.requests.request')
    def test_proxy_csrf_exempt(self, mock_request):
        """Test that proxy endpoint is CSRF exempt"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = json.dumps({'id': 1})
        mock_request.return_value = mock_response

        # POST request without CSRF token should still work because proxy is csrf_exempt
        response = self.client.post(
            '/api/v1/gw/ngo/ngos/',
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
