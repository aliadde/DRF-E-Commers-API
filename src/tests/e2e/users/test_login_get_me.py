import pytest
from typing import TypedDict


@pytest.fixture
def user() -> dict[str, str]:
    return {
        "username": "tester",
        "password": "testpass123",
        "email": "tester@gmail.com",
    }


@pytest.fixture
def register_user(user, api_client) -> dict[str, int | str]:

    resp_register = api_client.post(
        "/user/register/",
        json=user,
    )
    assert resp_register.status_code == 201
    assert resp_register.json().get("username") == "tester"
    assert resp_register.json().get("email") == "tester@gmail.com"

    return user


@pytest.mark.django_db
class TestLoginGetMeE2E:
    def test_login_get_me(self, api_client, register_user):
        user = register_user

        login_data = {
            "username": user["username"],
            "password": user["password"],
        }

        resp_login = api_client.post("/user/login/", json=login_data)
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_get_me = api_client.get(
            "/user/me/",
        )

        assert resp_get_me.status_code == 200
        assert resp_get_me.json().get("username") == user["username"]
        assert resp_get_me.json().get("email") == user["email"]
        assert "last_login" in resp_get_me.json()
