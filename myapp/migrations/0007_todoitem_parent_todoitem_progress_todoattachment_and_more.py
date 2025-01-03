# Generated by Django 5.1.3 on 2025-01-03 01:03

import django.db.models.deletion
import myapp.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0006_alter_category_options_category_user_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="todoitem",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subtasks",
                to="myapp.todoitem",
            ),
        ),
        migrations.AddField(
            model_name="todoitem",
            name="progress",
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name="TodoAttachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to=myapp.models.todo_attachment_path)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "todo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="myapp.todoitem",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TodoHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("action", models.CharField(max_length=50)),
                ("description", models.TextField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "todo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="history",
                        to="myapp.todoitem",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Todo Histories",
                "ordering": ["-timestamp"],
            },
        ),
    ]
