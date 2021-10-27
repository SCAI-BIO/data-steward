from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserSession(models.Model):
    token = models.CharField(max_length=1024, primary_key=True)
    session = models.TextField()
