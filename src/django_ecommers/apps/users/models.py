from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("username rquired.")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # hashing password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("superuser attribute is_staff=True must be.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("superuser attribute is_superuser=True must be.")

        return self.create_user(username, email, password, **extra_fields)


class Users(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=150, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # is_superuser come from PermissionsMixin

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.username
