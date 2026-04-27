from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs the 24-hour upcoming activity reminder job (Topic 10.2)."

    def handle(self, *args, **options):
        from notifications.tasks import send_upcoming_activity_reminders

        result = send_upcoming_activity_reminders()
        self.stdout.write(self.style.SUCCESS(f"OK: {result}"))

