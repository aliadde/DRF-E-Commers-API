import pytest

from django_ecommers.apps.users.models import Users


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    return {
        "username": "admin_tester",
        "password": "adminpass123",
    }


@pytest.fixture
def staff_user(db, admin_credentials) -> Users:
    """Create a staff (non-superuser) user directly in the DB."""
    return Users.objects.create_user(
        username=admin_credentials["username"],
        email="admin_tester@gmail.com",
        password=admin_credentials["password"],
        is_staff=True,
    )


@pytest.fixture
def regular_user(db) -> dict[str, str]:
    """A non-staff user, created directly in the DB."""
    credentials = {
        "username": "plain_user",
        "password": "plainpass123",
    }
    Users.objects.create_user(
        username=credentials["username"],
        email="plain_user@gmail.com",
        password=credentials["password"],
        is_staff=False,
    )
    return credentials


@pytest.fixture
def admin_token(staff_user, admin_credentials, api_client) -> str:
    """Log in as the staff user and return the access token."""
    resp_login = api_client.post("/user/login/", json=admin_credentials)
    assert resp_login.status_code == 200

    access_token = resp_login.json().get("access")
    assert access_token

    return access_token


@pytest.fixture
def product_data() -> dict[str, str | float]:
    return {
        "name": "Test Product",
        "description": "A product created in e2e test.",
        "price": 19.99,
    }


@pytest.mark.django_db
class TestAdminCreateProductE2E:
    """Admin logs in, then creates a product."""

    def test_admin_login_then_create_product(
        self, admin_token, product_data, api_client
    ):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        resp_create = api_client.post("/product/", json=product_data)

        assert resp_create.status_code == 201
        assert resp_create.json().get("name") == product_data["name"]
        assert resp_create.json().get("description") == product_data["description"]
        assert resp_create.json().get("price") == product_data["price"]
        assert resp_create.json().get("active") is True

    def test_admin_created_product_visible_in_public_list(
        self, admin_token, product_data, api_client
    ):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        resp_create = api_client.post("/product/", json=product_data)
        assert resp_create.status_code == 201

        # public listing requires no auth
        api_client.headers = {}
        resp_list = api_client.get("/product/all/")

        assert resp_list.status_code == 200
        names = [p["name"] for p in resp_list.json()]
        assert product_data["name"] in names

    def test_create_product_without_description(self, admin_token, api_client):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        payload = {"name": "No Description Product", "price": 5.5}
        resp_create = api_client.post("/product/", json=payload)

        assert resp_create.status_code == 201
        assert resp_create.json().get("name") == payload["name"]
        assert resp_create.json().get("price") == payload["price"]

    def test_create_product_missing_name(self, admin_token, api_client):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        resp_create = api_client.post("/product/", json={"price": 10.0})

        assert resp_create.status_code == 400

    def test_create_product_missing_price(self, admin_token, api_client):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        resp_create = api_client.post("/product/", json={"name": "No Price Product"})

        assert resp_create.status_code == 400

    def test_create_product_invalid_price_type(self, admin_token, api_client):
        api_client.headers = {"Authorization": f"Bearer {admin_token}"}

        payload = {"name": "Bad Price Product", "price": "not-a-number"}
        resp_create = api_client.post("/product/", json=payload)

        assert resp_create.status_code == 400

    def test_create_product_without_authentication(self, product_data, api_client):
        resp_create = api_client.post("/product/", json=product_data)

        assert resp_create.status_code == 401

    def test_create_product_with_invalid_token(self, product_data, api_client):
        api_client.headers = {"Authorization": "Bearer invalid-token"}

        resp_create = api_client.post("/product/", json=product_data)

        assert resp_create.status_code == 401

    def test_create_product_as_non_staff_user_forbidden(
        self, regular_user, product_data, api_client
    ):
        resp_login = api_client.post("/user/login/", json=regular_user)
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_create = api_client.post("/product/", json=product_data)

        assert resp_create.status_code == 403
