from django.db import models


class Users(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(max_length=150)
    hashed_password = models.CharField()
