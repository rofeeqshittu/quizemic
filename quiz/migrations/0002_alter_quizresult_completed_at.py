# Generated by Django 5.1.4 on 2025-01-01 06:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizresult',
            name='completed_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
