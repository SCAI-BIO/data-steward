from django.db import models

from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    is_verified = models.BooleanField(default=False)
    affiliation = models.CharField(null=True, blank=True, max_length=512)
    reason = models.TextField(null=False, blank=False, default="Research")

