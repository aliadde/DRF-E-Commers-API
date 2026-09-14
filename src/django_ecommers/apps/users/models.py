from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    pass


class Users(AbstractBaseUser):
    username = models.CharField(
        max_length=100,
        unique=True,
    )

    email = models.EmailField(max_length=150, unique=True)

    last_login = models.DateTimeField(
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "username"
    objects = UserManager()
