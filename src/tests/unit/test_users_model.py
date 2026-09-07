import pytest

from django_ecommers.apps.users.models import User


@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create(
        name="test",
    )

    
    assert user is not None
    assert user.name == "test"
    