"""
notifications/tests.py

Unit tests for Notification model, services, and tasks
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import CustomUser
from ngo.models import NGO, Activity
from notifications.models import Notification
from notifications.services import send_notification
from registration.models import Registration


class NotificationModelTests(TestCase):
    """Test Notification model functionality"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com',
            role='employee'
        )

    def test_notification_created_successfully(self):
        """Test that notification is created with correct attributes"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test notification'
        )
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.message, 'Test notification')
        self.assertFalse(notification.is_read)

    def test_notification_has_sent_at_timestamp(self):
        """Test that notification has sent_at timestamp"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test'
        )
        self.assertIsNotNone(notification.sent_at)

    def test_notification_is_read_defaults_to_false(self):
        """Test that is_read defaults to False"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test'
        )
        self.assertFalse(notification.is_read)

    def test_notification_can_be_marked_as_read(self):
        """Test that notification can be marked as read"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test'
        )
        notification.is_read = True
        notification.save()
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_notification_str_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test'
        )
        self.assertIn('testuser', str(notification))

    def test_multiple_notifications_for_user(self):
        """Test that multiple notifications can be created for same user"""
        Notification.objects.create(recipient=self.user, message='Message 1')
        Notification.objects.create(recipient=self.user, message='Message 2')
        Notification.objects.create(recipient=self.user, message='Message 3')
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 3)

    def test_notification_deleted_when_user_deleted(self):
        """Test that notification is deleted when user is deleted"""
        notification = Notification.objects.create(
            recipient=self.user,
            message='Test'
        )
        notification_id = notification.id
        self.user.delete()
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())

    def test_notifications_for_different_users(self):
        """Test that notifications can be created for different users"""
        user2 = CustomUser.objects.create_user(
            username='user2',
            password='Pass123!',
            email='user2@example.com',
            role='employee'
        )
        notif1 = Notification.objects.create(recipient=self.user, message='For user1')
        notif2 = Notification.objects.create(recipient=user2, message='For user2')
        self.assertEqual(notif1.recipient, self.user)
        self.assertEqual(notif2.recipient, user2)

    def test_notification_ordering_by_sent_at(self):
        """Test that notifications are ordered by sent_at"""
        notif1 = Notification.objects.create(recipient=self.user, message='First')
        notif2 = Notification.objects.create(recipient=self.user, message='Second')
        notifications = Notification.objects.filter(recipient=self.user)
        self.assertEqual(notifications[0].message, 'Second')  # Most recent first
        self.assertEqual(notifications[1].message, 'First')

    def test_notification_with_long_message(self):
        """Test that notification can store long messages"""
        long_message = 'A' * 1000
        notification = Notification.objects.create(
            recipient=self.user,
            message=long_message
        )
        self.assertEqual(notification.message, long_message)


class NotificationServiceTests(TestCase):
    """Test notification service functionality"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com',
            role='employee'
        )

    @patch('notifications.services.send_email_notification_task')
    def test_send_notification_creates_notification(self, mock_task):
        """Test that send_notification creates a notification"""
        message = 'Test notification'
        notification = send_notification(self.user, message)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.message, message)
        self.assertFalse(notification.is_read)

    @patch('notifications.services.send_email_notification_task')
    def test_send_notification_queues_email_task(self, mock_task):
        """Test that send_notification queues email task"""
        message = 'Test notification'
        notification = send_notification(self.user, message)
        mock_task.delay.assert_called_once_with(notification.id)

    @patch('notifications.services.send_email_notification_task')
    def test_send_notification_returns_notification(self, mock_task):
        """Test that send_notification returns created notification"""
        result = send_notification(self.user, 'Test')
        self.assertIsNotNone(result.id)
        self.assertEqual(result.recipient, self.user)

    @patch('notifications.services.send_email_notification_task')
    def test_multiple_notifications_to_same_user(self, mock_task):
        """Test sending multiple notifications to same user"""
        send_notification(self.user, 'Message 1')
        send_notification(self.user, 'Message 2')
        send_notification(self.user, 'Message 3')
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 3)

    @patch('notifications.services.send_email_notification_task')
    def test_send_notification_to_multiple_users(self, mock_task):
        """Test sending notifications to multiple users"""
        user2 = CustomUser.objects.create_user(
            username='user2',
            password='Pass123!',
            email='user2@example.com',
            role='employee'
        )
        send_notification(self.user, 'For user1')
        send_notification(user2, 'For user2')
        self.assertEqual(Notification.objects.count(), 2)


class NotificationTaskTests(TestCase):
    """Test Celery task functionality for notifications"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com',
            role='employee'
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            message='Test notification message'
        )

    @patch('notifications.tasks.send_mail')
    def test_send_email_notification_task_sends_email(self, mock_send_mail):
        """Test that email notification task sends email"""
        from notifications.tasks import send_email_notification_task
        result = send_email_notification_task(self.notification.id)
        self.assertEqual(result['status'], 'sent')
        mock_send_mail.assert_called_once()

    @patch('notifications.tasks.send_mail')
    def test_send_email_notification_task_with_no_email(self, mock_send_mail):
        """Test that task skips when user has no email"""
        self.user.email = ''
        self.user.save()
        from notifications.tasks import send_email_notification_task
        result = send_email_notification_task(self.notification.id)
        self.assertEqual(result['status'], 'skipped')
        mock_send_mail.assert_not_called()

    @patch('notifications.tasks.send_mail')
    def test_send_email_notification_task_uses_correct_email(self, mock_send_mail):
        """Test that task sends to correct email address"""
        from notifications.tasks import send_email_notification_task
        send_email_notification_task(self.notification.id)
        call_args = mock_send_mail.call_args
        self.assertIn(self.user.email, call_args[1]['recipient_list'])

    @patch('notifications.tasks.send_mail')
    def test_send_upcoming_activity_reminders_task(self, mock_send_mail):
        """Test send_upcoming_activity_reminders task"""
        from notifications.tasks import send_upcoming_activity_reminders
        
        admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            email='admin@example.com',
            role='admin'
        )
        ngo = NGO.objects.create(name='Test NGO', contact_email='ngo@test.com')
        activity = Activity.objects.create(
            title='Upcoming Activity',
            description='Test',
            location='KL',
            date=timezone.now() + timedelta(hours=12),
            cut_off_datetime=timezone.now() + timedelta(hours=11),
            ngo=ngo,
            created_by=admin
        )
        
        Registration.objects.create(
            employee=self.user,
            activity=activity,
            status='active'
        )
        
        result = send_upcoming_activity_reminders()
        self.assertEqual(result['status'], 'ok')
        self.assertGreater(result['reminders_sent'], 0)

    @patch('notifications.tasks.send_mail')
    def test_send_upcoming_activity_reminders_not_sent_for_cancelled(self, mock_send_mail):
        """Test that reminders are not sent for cancelled registrations"""
        from notifications.tasks import send_upcoming_activity_reminders
        
        admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            email='admin@example.com',
            role='admin'
        )
        ngo = NGO.objects.create(name='Test NGO', contact_email='ngo@test.com')
        activity = Activity.objects.create(
            title='Upcoming Activity',
            description='Test',
            location='KL',
            date=timezone.now() + timedelta(hours=12),
            cut_off_datetime=timezone.now() + timedelta(hours=11),
            ngo=ngo,
            created_by=admin
        )
        
        Registration.objects.create(
            employee=self.user,
            activity=activity,
            status='cancelled'
        )
        
        result = send_upcoming_activity_reminders()
        self.assertEqual(result['reminders_sent'], 0)

    @patch('notifications.tasks.send_mail')
    def test_send_upcoming_activity_reminders_only_within_24_hours(self, mock_send_mail):
        """Test that reminders are only sent for activities within 24 hours"""
        from notifications.tasks import send_upcoming_activity_reminders
        
        admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            email='admin@example.com',
            role='admin'
        )
        ngo = NGO.objects.create(name='Test NGO', contact_email='ngo@test.com')
        
        # Activity too far in the future
        activity_far = Activity.objects.create(
            title='Far Activity',
            description='Test',
            location='KL',
            date=timezone.now() + timedelta(days=5),
            cut_off_datetime=timezone.now() + timedelta(days=4),
            ngo=ngo,
            created_by=admin
        )
        
        Registration.objects.create(
            employee=self.user,
            activity=activity_far,
            status='active'
        )
        
        result = send_upcoming_activity_reminders()
        self.assertEqual(result['reminders_sent'], 0)


class NotificationIntegrationTests(TestCase):
    """Integration tests for notification workflows"""

    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='emp',
            password='Emp123!',
            email='emp@example.com',
            role='employee'
        )
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='Admin123!',
            email='admin@example.com',
            role='admin'
        )
        self.ngo = NGO.objects.create(name='Test NGO', contact_email='ngo@test.com')

    @patch('notifications.services.send_email_notification_task')
    def test_notification_workflow_on_activity_registration(self, mock_task):
        """Test notification workflow when employee registers for activity"""
        activity = Activity.objects.create(
            title='Beach Cleanup',
            description='Clean beach',
            location='Penang',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            ngo=self.ngo,
            created_by=self.admin
        )
        
        # Simulate registration notification
        notification = send_notification(
            self.employee,
            f'You have registered for {activity.title}'
        )
        
        self.assertEqual(notification.recipient, self.employee)
        self.assertIn(activity.title, notification.message)
        mock_task.delay.assert_called_once()

    @patch('notifications.services.send_email_notification_task')
    def test_bulk_notifications_to_activity_participants(self, mock_task):
        """Test sending bulk notifications to activity participants"""
        activity = Activity.objects.create(
            title='Beach Cleanup',
            description='Test',
            location='Penang',
            date=timezone.now() + timedelta(days=7),
            cut_off_datetime=timezone.now() + timedelta(days=6),
            ngo=self.ngo,
            created_by=self.admin
        )
        
        emp1 = CustomUser.objects.create_user(
            username='emp1', password='Pass123!', email='emp1@example.com'
        )
        emp2 = CustomUser.objects.create_user(
            username='emp2', password='Pass123!', email='emp2@example.com'
        )
        
        Registration.objects.create(employee=emp1, activity=activity, status='active')
        Registration.objects.create(employee=emp2, activity=activity, status='active')
        
        # Notify all active registrations
        registrations = Registration.objects.filter(activity=activity, status='active')
        for reg in registrations:
            send_notification(reg.employee, f'Reminder: {activity.title}')
        
        self.assertEqual(Notification.objects.count(), 2)
