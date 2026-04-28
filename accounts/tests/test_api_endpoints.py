"""
accounts/tests/test_api_endpoints.py

Unit tests for Accounts API endpoints and permissions
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser
from ngo.models import NGO, Activity
from django.utils import timezone
from datetime import timedelta


class AccountsAPIEndpointsTests(TestCase):
    """Test Accounts API endpoints"""

    def setUp(self):
        # Create users
        self.admin = CustomUser.objects.create_user(
            username='admin1',
            password='AdminPass123!',
            email='admin@test.com',
            role='admin'
        )
        self.employee = CustomUser.objects.create_user(
            username='emp1',
            password='EmpPass123!',
            email='emp@test.com',
            role='employee'
        )
        self.employee2 = CustomUser.objects.create_user(
            username='emp2',
            password='EmpPass123!',
            email='emp2@test.com',
            role='employee'
        )

        # Create tokens
        self.admin_token, _ = Token.objects.get_or_create(user=self.admin)
        self.emp_token, _ = Token.objects.get_or_create(user=self.employee)
        self.emp2_token, _ = Token.objects.get_or_create(user=self.employee2)

        # Create test client
        self.client = APIClient()

        # Create sample NGO and Activity for testing
        self.ngo = NGO.objects.create(
            name='Helping Hands',
            contact_email='contact@help.org',
            website='https://help.org',
            description='Test NGO'
        )
        self.activity = Activity.objects.create(
            title='Beach Cleanup',
            description='Clean the beach',
            location='KL',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            max_slots=10,
            ngo=self.ngo,
            created_by=self.admin,
        )

    def _auth(self, token):
        """Helper method to set authorization header"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_user_me_endpoint_returns_user_info(self):
        """Test that /me endpoint returns authenticated user info"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'emp1')
        self.assertEqual(resp.data['role'], 'employee')
        self.assertTrue(resp.data['is_employee'])
        self.assertFalse(resp.data['is_admin'])

    def test_me_endpoint_admin_info(self):
        """Test that /me endpoint returns correct admin info"""
        self._auth(self.admin_token.key)
        resp = self.client.get('/api/v1/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'admin1')
        self.assertEqual(resp.data['role'], 'admin')
        self.assertTrue(resp.data['is_admin'])
        self.assertFalse(resp.data['is_employee'])

    def test_me_endpoint_requires_authentication(self):
        """Test that /me endpoint requires authentication"""
        resp = self.client.get('/api/v1/me/')
        self.assertEqual(resp.status_code, 401)

    def test_me_endpoint_with_invalid_token(self):
        """Test that /me endpoint rejects invalid tokens"""
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid_token')
        resp = self.client.get('/api/v1/me/')
        self.assertEqual(resp.status_code, 401)

    def test_admin_can_create_ngo(self):
        """Test that admin users can create NGO"""
        self._auth(self.admin_token.key)
        data = {
            'name': 'New NGO',
            'contact_email': 'new@ngo.com',
            'website': 'https://new.org',
            'description': 'A new test NGO'
        }
        resp = self.client.post('/api/v1/ngos/', data)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(NGO.objects.filter(name='New NGO').count(), 1)

    def test_employee_cannot_create_ngo(self):
        """Test that employee users cannot create NGO"""
        self._auth(self.emp_token.key)
        data = {
            'name': 'Evil NGO',
            'contact_email': 'evil@ngo.com',
            'website': 'https://evil.org',
            'description': 'Should fail'
        }
        resp = self.client.post('/api/v1/ngos/', data)
        self.assertIn(resp.status_code, (403, 405))

    def test_employee_can_register_activity(self):
        """Test that employee users can register for activity"""
        self._auth(self.emp_token.key)
        data = {'activity': self.activity.id}
        resp = self.client.post('/api/v1/registrations/', data)
        self.assertEqual(resp.status_code, 201)

    def test_admin_cannot_register_activity(self):
        """Test that admin users cannot register for activity"""
        self._auth(self.admin_token.key)
        data = {'activity': self.activity.id}
        resp = self.client.post('/api/v1/registrations/', data)
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_user_cannot_register(self):
        """Test that unauthenticated users cannot register"""
        data = {'activity': self.activity.id}
        resp = self.client.post('/api/v1/registrations/', data)
        self.assertEqual(resp.status_code, 401)

    def test_employee_can_view_activities(self):
        """Test that employees can view activities"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/activities/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_employee_can_view_ngos(self):
        """Test that employees can view NGOs"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/ngos/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_anonymous_cannot_register_activity(self):
        """Test that anonymous users cannot register"""
        data = {'activity': self.activity.id}
        resp = self.client.post('/api/v1/registrations/', data)
        self.assertEqual(resp.status_code, 401)

    def test_employee_cannot_update_ngo(self):
        """Test that employees cannot update NGO"""
        self._auth(self.emp_token.key)
        data = {'name': 'Updated NGO', 'contact_email': 'updated@test.com'}
        resp = self.client.patch(f'/api/v1/ngos/{self.ngo.id}/', data)
        self.assertIn(resp.status_code, (403, 405))

    def test_admin_can_update_ngo(self):
        """Test that admins can update NGO"""
        self._auth(self.admin_token.key)
        data = {'description': 'Updated description'}
        resp = self.client.patch(f'/api/v1/ngos/{self.ngo.id}/', data)
        self.assertEqual(resp.status_code, 200)
        self.ngo.refresh_from_db()
        self.assertEqual(self.ngo.description, 'Updated description')

    def test_employee_cannot_delete_ngo(self):
        """Test that employees cannot delete NGO"""
        self._auth(self.emp_token.key)
        resp = self.client.delete(f'/api/v1/ngos/{self.ngo.id}/')
        self.assertIn(resp.status_code, (403, 405))

    def test_admin_can_delete_ngo(self):
        """Test that admins can delete NGO"""
        self._auth(self.admin_token.key)
        ngo_id = self.ngo.id
        resp = self.client.delete(f'/api/v1/ngos/{ngo_id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(NGO.objects.filter(id=ngo_id).exists())
