# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics', default='default.jpg')
    total_points = models.IntegerField(default=0)
    quizzes_taken = models.IntegerField(default=0)

    def __str__(self):
        return self.username

