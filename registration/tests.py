from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser
from ngo.models import Activity, NGO
from registration.models import Registration
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


class RegistrationJourneyIntegrationTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username="journey_user",
            password="Journey123!",
            role="employee",
        )
        self.ngo = NGO.objects.create(
            name="Journey NGO",
            contact_email="journey@ngo.test",
            website="https://journey.example",
            description="Journey test NGO",
        )
        self.activity = Activity.objects.create(
            title="Journey Activity",
            description="Journey test activity",
            location="Kuala Lumpur",
            date=timezone.now() + timedelta(days=2),
            cut_off_datetime=timezone.now() + timedelta(days=1),
            max_slots=2,
            ngo=self.ngo,
        )

    def test_login_list_register_and_verify_slot_count(self):
        login_response = self.client.post(
            "/accounts/login/",
            {
                "username": "journey_user",
                "password": "Journey123!",
            },
            follow=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "Journey Activity", status_code=200)

        list_response = self.client.get("/ngo/")
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Journey Activity")

        register_response = self.client.post(f"/registration/register/{self.activity.id}/")
        self.assertEqual(register_response.status_code, 302)

        self.activity.refresh_from_db()
        self.assertEqual(Registration.objects.filter(employee=self.employee, activity=self.activity, status="active").count(), 1)
        self.assertEqual(self.activity.get_registered_count(), 1)
        self.assertEqual(self.activity.slots_remaining(), 1)
