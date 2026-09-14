import pytest


@pytest.mark.django_db
class TestItemsE2E:
    """user register in system, then want to login."""

    def test_register_then_login(self, api_client):
        resp_register = api_client.post(
            "/user/register/",
            json={
                "username": "tester",
                "password": "testpass123",
                "email": "tester@gmail.com",
            },
        )
        assert resp_register.status_code == 201
        assert resp_register.json().get("username") == "tester"
        assert resp_register.json().get("id") == 1
        assert resp_register.json().get("email") == "tester@gmail.com"

        login_data = dict(username="tester", password="testpass123")
        resp_login = api_client.post("/user/login/", json=login_data)
        assert resp_login.status_code == 200
        assert "access" in resp_login.json()

    def test_register_duplicate_username_fails(self, api_client):
        payload = {
            "username": "tester",
            "password": "testpass123",
            "email": "tester@gmail.com",
        }
        first = api_client.post("/user/register/", json=payload)
        assert first.status_code == 201

        second = api_client.post("/user/register/", json=payload)
        assert second.status_code == 400

    def test_register_duplicate_email_fails(self, api_client):
        api_client.post(
            "/user/register/",
            json={
                "username": "tester1",
                "password": "testpass123",
                "email": "same@gmail.com",
            },
        )
        resp = api_client.post(
            "/user/register/",
            json={
                "username": "tester2",
                "password": "testpass123",
                "email": "same@gmail.com",
            },
        )
        assert resp.status_code == 400

    def test_register_missing_field_fails(self, api_client):
        resp = api_client.post(
            "/user/register/",
            json={"username": "tester", "password": "testpass123"},  # no email
        )
        assert resp.status_code == 400

    def test_login_wrong_password_fails(self, api_client):
        api_client.post(
            "/user/register/",
            json={
                "username": "tester",
                "password": "testpass123",
                "email": "tester@gmail.com",
            },
        )
        resp = api_client.post(
            "/user/login/",
            json={"username": "tester", "password": "wrongpass"},
        )
        assert resp.status_code in (400, 401)

    def test_login_nonexistent_user_fails(self, api_client):
        resp = api_client.post(
            "/user/login/",
            json={"username": "ghost", "password": "whatever123"},
        )
        assert resp.status_code in (400, 401)
