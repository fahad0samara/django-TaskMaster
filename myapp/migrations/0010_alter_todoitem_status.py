# Generated by Django 5.1.3 on 2025-01-03 03:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0009_todoitem_actual_hours_todoitem_blocked_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="todoitem",
            name="status",
            field=models.CharField(
                choices=[
                    ("todo", "To Do"),
                    ("in_progress", "In Progress"),
                    ("done", "Done"),
                ],
                default="todo",
                max_length=20,
            ),
        ),
    ]