from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Users


class CustomUserAdmin(UserAdmin):
    model = Users
    list_display = ["username", "email", "is_staff", "is_active"]
    ordering = ["username"]

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("username", "email")
    filter_horizontal = ("groups", "user_permissions")


admin.site.register(Users, CustomUserAdmin)
"""
claude chat that contain all detail of implementation.
https://claude.ai/chat/395465d1-a4e5-469e-8f3c-e421572621b7
"""
