# Generated by Django 5.1.4 on 2024-12-17 09:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0005_remove_leave_class_name_remove_leave_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="advisor",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"groups__name": "tch"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="students",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
