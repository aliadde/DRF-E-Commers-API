"""all users services here."""

from django_ecommers.apps.users.models import Users
from django_ecommers.apps.users.serializer import UserRegisterResponseSerializer

from .exceptions import DuplicateHTTPException


class UserService:
    def create_user(self, user_data: dict[str, str]) -> Users:
        """creating user"""
        # if same name or email was exist in database raise error to user
        if Users.objects.filter(name=user_data.get("name")).exists():
            raise DuplicateHTTPException

        if Users.objects.filter(email=user_data.get("email")).exists():
            raise DuplicateHTTPException

        new_user = Users(
            name=user_data.get("name"),
            email=user_data.get("email"),
        )

        new_user.set_password(user_data.get("password"))
        new_user.save()

        return new_user
