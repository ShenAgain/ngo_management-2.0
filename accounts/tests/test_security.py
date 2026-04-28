"""
accounts/tests/test_security.py

Minimal invalid-input edge-case tests.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.validators import SQLInjectionValidator, XSSValidator, SafeCharacterValidator
from accounts.forms import RegisterForm


class InvalidInputSecurityTests(TestCase):
    def test_sql_injection_rejected(self):
        validator = SQLInjectionValidator()
        with self.assertRaises(ValidationError):
            validator("admin' OR '1'='1")

    def test_xss_rejected(self):
        validator = XSSValidator()
        with self.assertRaises(ValidationError):
            validator("<script>alert(1)</script>")

    def test_safe_character_validator_rejects_bad_input(self):
        validator = SafeCharacterValidator(
            allowed_pattern=r"^[\w\s\-\'\.]+$",
            message="Invalid characters.",
        )
        with self.assertRaises(ValidationError):
            validator("Bad<Name>")

    def test_register_form_rejects_invalid_username(self):
        form = RegisterForm(data={
            'username': "admin' OR '1'='1",
            'email': "test@example.com",
            'first_name': "John",
            'last_name': "Doe",
            'role': 'employee',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_register_form_rejects_mismatched_passwords(self):
        form = RegisterForm(data={
            'username': 'john_doe',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'employee',
            'password1': 'SecurePass123!',
            'password2': 'WrongPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
