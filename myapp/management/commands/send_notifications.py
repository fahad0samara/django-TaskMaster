from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import TodoItem

class Command(BaseCommand):
    help = 'Send email notifications for todos that are due soon'

    def handle(self, *args, **options):
        todos = TodoItem.objects.filter(
            completed=False,
            due_date__isnull=False
        ).select_related('user')

        notification_count = 0
        for todo in todos:
            todo.check_and_send_notifications()
            notification_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {notification_count} todos')
        )
