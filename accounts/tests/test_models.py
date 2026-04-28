"""
accounts/tests/test_models.py

Unit tests for CustomUser model
"""

from django.test import TestCase
from accounts.models import CustomUser


class CustomUserModelTests(TestCase):
    """Test CustomUser model functionality"""

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin_test",
            password="AdminTest123!",
            email="admin@test.com",
            role="admin",
        )
        self.employee = CustomUser.objects.create_user(
            username="emp_test",
            password="EmpTest123!",
            email="emp@test.com",
            role="employee",
        )

    def test_admin_user_created_successfully(self):
        """Test that admin user is created with correct role"""
        self.assertEqual(self.admin.role, "admin")
        self.assertTrue(self.admin.is_admin())
        self.assertFalse(self.admin.is_employee())

    def test_employee_user_created_successfully(self):
        """Test that employee user is created with correct role"""
        self.assertEqual(self.employee.role, "employee")
        self.assertTrue(self.employee.is_employee())
        self.assertFalse(self.employee.is_admin())

    def test_user_default_role_is_employee(self):
        """Test that default role is employee when not specified"""
        user = CustomUser.objects.create_user(
            username="default_user",
            password="DefaultUser123!",
            email="default@test.com",
        )
        self.assertEqual(user.role, "employee")
        self.assertTrue(user.is_employee())

    def test_user_password_is_hashed(self):
        """Test that user password is properly hashed"""
        user = CustomUser.objects.get(username="admin_test")
        self.assertNotEqual(user.password, "AdminTest123!")
        self.assertTrue(user.check_password("AdminTest123!"))

    def test_invalid_password_fails_check(self):
        """Test that incorrect password fails validation"""
        user = CustomUser.objects.get(username="admin_test")
        self.assertFalse(user.check_password("WrongPassword123!"))

    def test_user_email_is_stored(self):
        """Test that user email is correctly stored"""
        user = CustomUser.objects.get(username="admin_test")
        self.assertEqual(user.email, "admin@test.com")

    def test_multiple_users_exist(self):
        """Test that multiple users can be created"""
        count = CustomUser.objects.count()
        self.assertEqual(count, 2)

    def test_user_str_representation(self):
        """Test user string representation"""
        self.assertEqual(str(self.admin), "admin_test")
        self.assertEqual(str(self.employee), "emp_test")

    def test_is_active_by_default(self):
        """Test that user is active by default"""
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.employee.is_active)

    def test_unique_username_constraint(self):
        """Test that usernames must be unique"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                username="admin_test",  # Duplicate
                password="Test123!",
                role="admin",
            )
