from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser
from ngo.models import Activity, NGO
from registration.services import RegistrationService


class RegistrationServiceEdgeCaseTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username="emp_unit",
            password="EmpUnit123!",
            role="employee",
        )
        self.ngo = NGO.objects.create(
            name="Unit NGO",
            contact_email="unit@ngo.test",
            website="https://unit.example",
            description="Unit test NGO",
        )
        self.activity = Activity.objects.create(
            title="Unit Activity",
            description="Unit test activity",
            location="Penang",
            date=timezone.now() + timedelta(days=2),
            cut_off_datetime=timezone.now() + timedelta(days=1),
            max_slots=1,
            ngo=self.ngo,
        )

    def test_register_user_raises_error_when_activity_full(self):
        other = CustomUser.objects.create_user(
            username="emp_other",
            password="EmpOther123!",
            role="employee",
        )
        RegistrationService.register_user(other, self.activity.id)

        with self.assertRaisesMessage(ValueError, "fully booked"):
            RegistrationService.register_user(self.employee, self.activity.id)

    def test_register_user_raises_error_when_cutoff_passed(self):
        self.activity.cut_off_datetime = timezone.now() - timedelta(minutes=1)
        self.activity.save(update_fields=["cut_off_datetime"])

        with self.assertRaisesMessage(ValueError, "cut-off date has passed"):
            RegistrationService.register_user(self.employee, self.activity.id)

    def test_register_user_rejects_invalid_activity_id(self):
        with self.assertRaises(Activity.DoesNotExist):
            RegistrationService.register_user(self.employee, 999999)
