import pytest

from django_ecommers.apps.users.models import Users


@pytest.mark.django_db
def test_user_creation():
    user = Users(
        name="test",
    )
    user.save()
    
    assert user is not None
    assert user.name == "test"
