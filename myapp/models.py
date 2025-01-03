from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import os

def todo_attachment_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/user_<id>/todo_<id>/<filename>
    return f'todo_attachments/user_{instance.todo.user.id}/todo_{instance.todo.id}/{filename}'

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='primary')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'user']

    def __str__(self):
        return self.name

class NotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    notification_time = models.IntegerField(default=24, help_text='Hours before due date')
    notify_on_assignment = models.BooleanField(default=True)
    notify_on_completion = models.BooleanField(default=True)

    def __str__(self):
        return f'Notification settings for {self.user.username}'

    def send_due_date_notification(self, todo):
        if not self.email_notifications or not todo.due_date:
            return

        subject = f'Todo Reminder: {todo.title}'
        context = {
            'user': self.user,
            'todo': todo,
            'hours_remaining': (todo.due_date - timezone.now()).total_seconds() / 3600
        }
        html_message = render_to_string('email/due_date_reminder.html', context)
        plain_message = render_to_string('email/due_date_reminder.txt', context)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            fail_silently=True
        )

class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default='primary')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ['name', 'user']

    def __str__(self):
        return f"{self.name} ({self.user.username if self.user else 'No User'})"

class TodoItem(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos', null=True)
    shared_with = models.ManyToManyField(User, related_name='shared_todos', blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.IntegerField(choices=[
        (1, 'Daily'),
        (7, 'Weekly'),
        (14, 'Bi-weekly'),
        (30, 'Monthly')
    ], null=True, blank=True)
    last_recurring_date = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    progress = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True)
    last_notification_sent = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=20, default='primary')
    dependencies = models.ManyToManyField('self', symmetrical=False, related_name='dependent_tasks', blank=True)
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], default='todo')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-date']

    def __str__(self):
        return f"{self.title} ({self.user.username if self.user else 'No User'})"

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now()
        return False

    @property
    def can_start(self):
        """Check if all dependencies are completed"""
        return not self.dependencies.filter(completed__isnull=True).exists()

    def mark_complete(self, user=None):
        """Mark the todo as complete and record the completion time"""
        now = timezone.now()
        self.completed = now
        self.status = 'done'
        self.save()

        # Create history entry
        if user:
            TodoHistory.objects.create(
                todo=self,
                user=user,
                action='completed',
                description=f'Marked todo as completed'
            )

        # Check if this completion unblocks any dependent tasks
        for dependent in self.dependent_tasks.all():
            if dependent.can_start:
                dependent.blocked = False
                dependent.save()
                if user:
                    TodoHistory.objects.create(
                        todo=dependent,
                        user=user,
                        action='unblocked',
                        description=f'Unblocked due to completion of dependency: {self.title}'
                    )

    def mark_incomplete(self, user=None):
        """Mark the todo as incomplete"""
        self.completed = None
        if self.status == 'done':
            self.status = 'in_progress'
        self.save()

        # Create history entry
        if user:
            TodoHistory.objects.create(
                todo=self,
                user=user,
                action='uncompleted',
                description=f'Marked todo as incomplete'
            )

        # Check if this incompletion blocks any dependent tasks
        for dependent in self.dependent_tasks.all():
            if not dependent.can_start:
                dependent.blocked = True
                dependent.blocked_reason = f'Waiting for {self.title} to be completed'
                dependent.save()
                if user:
                    TodoHistory.objects.create(
                        todo=dependent,
                        user=user,
                        action='blocked',
                        description=f'Blocked due to incompletion of dependency: {self.title}'
                    )

    def create_next_recurring(self):
        if self.is_recurring and self.recurrence_interval:
            next_due = self.due_date + timezone.timedelta(days=self.recurrence_interval)
            new_todo = TodoItem.objects.create(
                title=self.title,
                content=self.content,
                due_date=next_due,
                category=self.category,
                priority=self.priority,
                user=self.user,
                is_recurring=True,
                recurrence_interval=self.recurrence_interval,
                color=self.color,
                all_day=self.all_day,
                location=self.location,
                status='todo',
                estimated_hours=self.estimated_hours
            )
            # Copy tags, dependencies, and shared users
            new_todo.tags.set(self.tags.all())
            new_todo.dependencies.set(self.dependencies.all())
            new_todo.shared_with.set(self.shared_with.all())
            return new_todo
        return None

    def update_progress(self):
        if not self.subtasks.exists():
            self.progress = 100 if self.completed else 0
        else:
            total_tasks = self.subtasks.count() + 1
            completed_tasks = self.subtasks.filter(completed__isnull=False).count()
            if self.completed:
                completed_tasks += 1
            self.progress = (completed_tasks * 100) // total_tasks
        self.save()

        if self.parent:
            self.parent.update_progress()

    def check_and_send_notifications(self):
        if not self.due_date or self.completed or not self.user.email:
            return

        now = timezone.now()
        if self.last_notification_sent and (now - self.last_notification_sent).total_seconds() < 86400:
            return

        try:
            notification_settings = self.user.notificationsetting
        except NotificationSetting.DoesNotExist:
            return

        hours_until_due = (self.due_date - now).total_seconds() / 3600
        if hours_until_due <= notification_settings.notification_time:
            notification_settings.send_due_date_notification(self)
            self.last_notification_sent = now
            self.save(update_fields=['last_notification_sent'])

    def to_dict(self):
        """Convert todo to dictionary for export"""
        return {
            'Title': self.title,
            'Description': self.content,
            'Status': self.status,
            'Priority': self.get_priority_display(),
            'Category': self.category.name if self.category else '',
            'Tags': ', '.join(t.name for t in self.tags.all()),
            'Created': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'Due Date': self.due_date.strftime('%Y-%m-%d %H:%M:%S') if self.due_date else '',
            'Completed': self.completed.strftime('%Y-%m-%d %H:%M:%S') if self.completed else '',
            'Progress': f"{self.progress}%",
            'Location': self.location,
            'Estimated Hours': str(self.estimated_hours) if self.estimated_hours else '',
            'Actual Hours': str(self.actual_hours) if self.actual_hours else '',
            'Dependencies': ', '.join(d.title for d in self.dependencies.all()),
            'Blocked': 'Yes' if self.blocked else 'No',
            'Blocked Reason': self.blocked_reason if self.blocked else '',
            'Completion Notes': self.completion_notes,
        }

class TodoAttachment(models.Model):
    todo = models.ForeignKey(TodoItem, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=todo_attachment_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.todo.title} - {os.path.basename(self.file.name)}"

    def filename(self):
        return os.path.basename(self.file.name)

class TodoHistory(models.Model):
    todo = models.ForeignKey(TodoItem, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Todo Histories'

    def __str__(self):
        return f"{self.todo.title} - {self.action} by {self.user.username if self.user else 'Unknown'}"

class TodoShare(models.Model):
    todo = models.ForeignKey(TodoItem, on_delete=models.CASCADE)
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_sent')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_received')
    date_shared = models.DateTimeField(auto_now_add=True)
    can_edit = models.BooleanField(default=False)

    class Meta:
        unique_together = ['todo', 'shared_with']

    def __str__(self):
        return f"{self.todo.title} shared by {self.shared_by.username} with {self.shared_with.username}"
