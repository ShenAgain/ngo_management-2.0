"""
ngo/tests.py

Unit tests for NGO module including models, serializers, and API endpoints
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from accounts.models import CustomUser
from ngo.models import NGO, Activity
from ngo.serializers import NGOSerializer, ActivitySerializer
from registration.models import Registration


class NGOModelTests(TestCase):
    """Test NGO model functionality"""

    def setUp(self):
        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org',
            website='https://test.org',
            description='Test NGO Description'
        )

    def test_ngo_created_successfully(self):
        """Test that NGO is created with correct attributes"""
        self.assertEqual(self.ngo.name, 'Test NGO')
        self.assertEqual(self.ngo.contact_email, 'test@ngo.org')
        self.assertEqual(self.ngo.website, 'https://test.org')
        self.assertEqual(self.ngo.description, 'Test NGO Description')

    def test_ngo_has_created_at_timestamp(self):
        """Test that NGO has created_at timestamp"""
        self.assertIsNotNone(self.ngo.created_at)

    def test_ngo_name_is_unique(self):
        """Test that NGO names must be unique"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            NGO.objects.create(
                name='Test NGO',  # Duplicate
                contact_email='other@ngo.org'
            )

    def test_ngo_str_representation(self):
        """Test NGO string representation"""
        self.assertEqual(str(self.ngo), 'Test NGO')

    def test_ngo_ordering_by_name(self):
        """Test that NGOs are ordered by name"""
        ngo2 = NGO.objects.create(
            name='Another NGO',
            contact_email='another@ngo.org'
        )
        ngos = NGO.objects.all()
        self.assertEqual(ngos[0].name, 'Another NGO')
        self.assertEqual(ngos[1].name, 'Test NGO')

    def test_ngo_optional_website(self):
        """Test that website field is optional"""
        ngo = NGO.objects.create(
            name='NGO Without Website',
            contact_email='no@website.org'
        )
        self.assertEqual(ngo.website, '')

    def test_ngo_optional_description(self):
        """Test that description field is optional"""
        ngo = NGO.objects.create(
            name='NGO Without Description',
            contact_email='no@description.org'
        )
        self.assertEqual(ngo.description, '')

    def test_multiple_ngos_exist(self):
        """Test that multiple NGOs can be created"""
        NGO.objects.create(name='NGO 2', contact_email='ngo2@test.org')
        NGO.objects.create(name='NGO 3', contact_email='ngo3@test.org')
        self.assertEqual(NGO.objects.count(), 3)


class ActivityModelTests(TestCase):
    """Test Activity model functionality"""

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            role='admin'
        )
        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org'
        )
        self.activity = Activity.objects.create(
            title='Beach Cleanup',
            description='Clean the beach',
            location='Penang',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            max_slots=10,
            ngo=self.ngo,
            created_by=self.admin
        )

    def test_activity_created_successfully(self):
        """Test that Activity is created with correct attributes"""
        self.assertEqual(self.activity.title, 'Beach Cleanup')
        self.assertEqual(self.activity.description, 'Clean the beach')
        self.assertEqual(self.activity.location, 'Penang')
        self.assertEqual(self.activity.max_slots, 10)
        self.assertEqual(self.activity.ngo, self.ngo)
        self.assertEqual(self.activity.created_by, self.admin)

    def test_activity_has_timestamps(self):
        """Test that Activity has created_at timestamp"""
        self.assertIsNotNone(self.activity.created_at)

    def test_activity_str_representation(self):
        """Test Activity string representation"""
        self.assertEqual(str(self.activity), 'Beach Cleanup')

    def test_activity_ordering_by_date(self):
        """Test that Activities are ordered by date"""
        later_date = timezone.now() + timedelta(days=10)
        activity2 = Activity.objects.create(
            title='Later Activity',
            description='Later',
            location='KL',
            date=later_date,
            cut_off_datetime=later_date - timedelta(days=1),
            ngo=self.ngo,
            created_by=self.admin
        )
        activities = Activity.objects.all()
        self.assertEqual(activities[0].title, 'Beach Cleanup')
        self.assertEqual(activities[1].title, 'Later Activity')

    def test_activity_with_null_ngo(self):
        """Test that Activity can have null NGO"""
        activity = Activity.objects.create(
            title='Independent Activity',
            description='No NGO',
            location='KL',
            date=timezone.now() + timedelta(days=5),
            cut_off_datetime=timezone.now() + timedelta(days=4),
            ngo=None
        )
        self.assertIsNone(activity.ngo)

    def test_activity_with_null_created_by(self):
        """Test that Activity can have null created_by"""
        activity = Activity.objects.create(
            title='Anonymous Activity',
            description='No creator',
            location='KL',
            date=timezone.now() + timedelta(days=5),
            cut_off_datetime=timezone.now() + timedelta(days=4),
            ngo=self.ngo,
            created_by=None
        )
        self.assertIsNone(activity.created_by)

    def test_activity_default_max_slots(self):
        """Test that default max_slots is 10"""
        activity = Activity.objects.create(
            title='Default Slots Activity',
            description='Default',
            location='KL',
            date=timezone.now() + timedelta(days=5),
            cut_off_datetime=timezone.now() + timedelta(days=4),
            ngo=self.ngo
        )
        self.assertEqual(activity.max_slots, 10)

    def test_activity_ngo_relationship(self):
        """Test Activity-NGO relationship"""
        self.assertIn(self.activity, self.ngo.activities.all())


class NGOAPITests(TestCase):
    """Test NGO API endpoints"""

    def setUp(self):
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
        self.admin_token, _ = Token.objects.get_or_create(user=self.admin)
        self.emp_token, _ = Token.objects.get_or_create(user=self.employee)
        self.client = APIClient()

        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org',
            website='https://test.org',
            description='Test Description'
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_list_ngos_unauthenticated(self):
        """Test that unauthenticated users cannot list NGOs"""
        resp = self.client.get('/api/v1/ngos/')
        self.assertEqual(resp.status_code, 401)

    def test_list_ngos_authenticated(self):
        """Test that authenticated users can list NGOs"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/ngos/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_retrieve_ngo(self):
        """Test retrieving a single NGO"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/ngos/{self.ngo.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'Test NGO')

    def test_create_ngo_as_admin(self):
        """Test that admin can create NGO"""
        self._auth(self.admin_token.key)
        data = {
            'name': 'New NGO',
            'contact_email': 'new@ngo.org',
            'website': 'https://new.org',
            'description': 'New NGO'
        }
        resp = self.client.post('/api/v1/ngos/', data)
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(NGO.objects.filter(name='New NGO').exists())

    def test_create_ngo_as_employee(self):
        """Test that employee cannot create NGO"""
        self._auth(self.emp_token.key)
        data = {
            'name': 'Unauthorized NGO',
            'contact_email': 'unauth@ngo.org'
        }
        resp = self.client.post('/api/v1/ngos/', data)
        self.assertEqual(resp.status_code, 403)

    def test_search_ngo_by_name(self):
        """Test searching NGO by name"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/ngos/?search=Test')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_update_ngo_as_admin(self):
        """Test that admin can update NGO"""
        self._auth(self.admin_token.key)
        data = {'description': 'Updated description'}
        resp = self.client.patch(f'/api/v1/ngos/{self.ngo.id}/', data)
        self.assertEqual(resp.status_code, 200)
        self.ngo.refresh_from_db()
        self.assertEqual(self.ngo.description, 'Updated description')

    def test_update_ngo_as_employee(self):
        """Test that employee cannot update NGO"""
        self._auth(self.emp_token.key)
        data = {'description': 'Unauthorized update'}
        resp = self.client.patch(f'/api/v1/ngos/{self.ngo.id}/', data)
        self.assertEqual(resp.status_code, 403)

    def test_delete_ngo_as_admin(self):
        """Test that admin can delete NGO"""
        self._auth(self.admin_token.key)
        ngo_id = self.ngo.id
        resp = self.client.delete(f'/api/v1/ngos/{ngo_id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(NGO.objects.filter(id=ngo_id).exists())

    def test_delete_ngo_as_employee(self):
        """Test that employee cannot delete NGO"""
        self._auth(self.emp_token.key)
        resp = self.client.delete(f'/api/v1/ngos/{self.ngo.id}/')
        self.assertEqual(resp.status_code, 403)


class ActivityAPITests(TestCase):
    """Test Activity API endpoints"""

    def setUp(self):
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
        self.admin_token, _ = Token.objects.get_or_create(user=self.admin)
        self.emp_token, _ = Token.objects.get_or_create(user=self.employee)
        self.client = APIClient()

        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org'
        )
        self.activity = Activity.objects.create(
            title='Beach Cleanup',
            description='Clean beach',
            location='Penang',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            max_slots=10,
            ngo=self.ngo,
            created_by=self.admin
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_list_activities_authenticated(self):
        """Test that authenticated users can list activities"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/activities/')
        self.assertEqual(resp.status_code, 200)

    def test_retrieve_activity(self):
        """Test retrieving a single activity"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/activities/{self.activity.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'Beach Cleanup')

    def test_create_activity_as_admin(self):
        """Test that admin can create activity"""
        self._auth(self.admin_token.key)
        data = {
            'title': 'New Activity',
            'description': 'New activity desc',
            'location': 'KL',
            'date': (timezone.now() + timedelta(days=7)).isoformat(),
            'cut_off_datetime': (timezone.now() + timedelta(days=6)).isoformat(),
            'max_slots': 20,
            'ngo': self.ngo.id
        }
        resp = self.client.post('/api/v1/activities/', data)
        self.assertEqual(resp.status_code, 201)

    def test_create_activity_as_employee(self):
        """Test that employee cannot create activity"""
        self._auth(self.emp_token.key)
        data = {
            'title': 'Unauthorized Activity',
            'description': 'Should fail',
            'location': 'KL',
            'date': (timezone.now() + timedelta(days=7)).isoformat(),
            'cut_off_datetime': (timezone.now() + timedelta(days=6)).isoformat(),
            'ngo': self.ngo.id
        }
        resp = self.client.post('/api/v1/activities/', data)
        self.assertEqual(resp.status_code, 403)

    def test_activity_includes_ngo_name(self):
        """Test that activity response includes NGO name"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/activities/{self.activity.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['ngo_name'], 'Test NGO')

    def test_activity_includes_created_by(self):
        """Test that activity response includes created_by username"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/activities/{self.activity.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['created_by'], 'admin')

    def test_filter_activities_by_ngo(self):
        """Test filtering activities by NGO"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/activities/?ngo={self.ngo.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_search_activities(self):
        """Test searching activities by title"""
        self._auth(self.emp_token.key)
        resp = self.client.get('/api/v1/activities/?search=Beach')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)

    def test_activity_participants_endpoint_requires_admin(self):
        """Test that participants endpoint requires admin role"""
        self._auth(self.emp_token.key)
        resp = self.client.get(f'/api/v1/activities/{self.activity.id}/participants/')
        self.assertEqual(resp.status_code, 403)

    def test_activity_participants_endpoint_admin_access(self):
        """Test that admin can access participants endpoint"""
        self._auth(self.admin_token.key)
        resp = self.client.get(f'/api/v1/activities/{self.activity.id}/participants/')
        self.assertEqual(resp.status_code, 200)

    def test_activity_created_by_defaults_to_request_user(self):
        """Test that created_by is set to request user"""
        self._auth(self.admin_token.key)
        data = {
            'title': 'Auto Created By Activity',
            'description': 'Test',
            'location': 'KL',
            'date': (timezone.now() + timedelta(days=7)).isoformat(),
            'cut_off_datetime': (timezone.now() + timedelta(days=6)).isoformat(),
            'ngo': self.ngo.id
        }
        resp = self.client.post('/api/v1/activities/', data)
        self.assertEqual(resp.status_code, 201)
        activity = Activity.objects.get(title='Auto Created By Activity')
        self.assertEqual(activity.created_by, self.admin)


class NGOSerializerTests(TestCase):
    """Test NGOSerializer"""

    def setUp(self):
        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org',
            website='https://test.org',
            description='Test'
        )

    def test_ngo_serializer_includes_all_fields(self):
        """Test that serializer includes all required fields"""
        serializer = NGOSerializer(self.ngo)
        self.assertIn('id', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('contact_email', serializer.data)
        self.assertIn('website', serializer.data)
        self.assertIn('description', serializer.data)
        self.assertIn('created_at', serializer.data)

    def test_ngo_serializer_creates_ngo(self):
        """Test that serializer can create NGO"""
        data = {
            'name': 'New NGO',
            'contact_email': 'new@ngo.org',
            'website': 'https://new.org',
            'description': 'New'
        }
        serializer = NGOSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        ngo = serializer.save()
        self.assertEqual(ngo.name, 'New NGO')


class ActivitySerializerTests(TestCase):
    """Test ActivitySerializer"""

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            role='admin'
        )
        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_email='test@ngo.org'
        )
        self.activity = Activity.objects.create(
            title='Test Activity',
            description='Test',
            location='KL',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            ngo=self.ngo,
            created_by=self.admin
        )

    def test_activity_serializer_includes_all_fields(self):
        """Test that serializer includes all required fields"""
        serializer = ActivitySerializer(self.activity)
        self.assertIn('id', serializer.data)
        self.assertIn('title', serializer.data)
        self.assertIn('ngo_name', serializer.data)
        self.assertIn('created_by', serializer.data)

    def test_activity_serializer_ngo_name_source(self):
        """Test that ngo_name comes from ngo.name"""
        serializer = ActivitySerializer(self.activity)
        self.assertEqual(serializer.data['ngo_name'], 'Test NGO')

    def test_activity_serializer_created_by_is_username(self):
        """Test that created_by returns username"""
        serializer = ActivitySerializer(self.activity)
        self.assertEqual(serializer.data['created_by'], 'admin')
