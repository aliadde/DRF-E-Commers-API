from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class Users(AbstractBaseUser):
    name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(max_length=150)
    password = models.CharField()
    last_login = models.DateTimeField(blank=True, null=True)
    USERNAME_FIELD = "email"
