import httpx
import pytest

from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


# ============================================================
# Users
# ============================================================


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    return {
        "username": "admin_tester",
        "password": "adminpass123",
    }


@pytest.fixture
def admin_user(db, admin_credentials) -> Users:
    """Create a staff user directly in the database."""
    return Users.objects.create_user(
        username=admin_credentials["username"],
        email="admin_tester@gmail.com",
        password=admin_credentials["password"],
        is_staff=True,
    )


@pytest.fixture
def regular_user(db) -> dict[str, str]:
    """Create a non-staff user directly in the database."""
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


# ============================================================
# API Clients
# ============================================================


@pytest.fixture
def api_client(live_server):
    """
    Unauthenticated HTTP client.

    IMPORTANT:
    This client never receives an Authorization header.
    """
    with httpx.Client(
        base_url=live_server.url,
        timeout=10.0,
    ) as client:
        yield client


@pytest.fixture
def admin_token(
    admin_user,
    admin_credentials,
    api_client,
) -> str:
    """Log in as admin/staff user and return the access token."""
    response = api_client.post(
        "/user/login/",
        json=admin_credentials,
    )

    assert response.status_code == 200

    access_token = response.json().get("access")
    assert access_token

    return access_token


@pytest.fixture
def regular_token(
    regular_user,
    api_client,
) -> str:
    """Log in as regular non-staff user and return the access token."""
    response = api_client.post(
        "/user/login/",
        json=regular_user,
    )

    assert response.status_code == 200

    access_token = response.json().get("access")
    assert access_token

    return access_token


@pytest.fixture
def admin_client(live_server, admin_token):
    """
    Authenticated HTTP client for staff/admin requests.

    This is a completely separate client from api_client.
    """
    with httpx.Client(
        base_url=live_server.url,
        timeout=10.0,
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    ) as client:
        yield client


@pytest.fixture
def regular_client(live_server, regular_token):
    """
    Authenticated HTTP client for regular users.

    This is a completely separate client from api_client.
    """
    with httpx.Client(
        base_url=live_server.url,
        timeout=10.0,
        headers={
            "Authorization": f"Bearer {regular_token}",
        },
    ) as client:
        yield client


# ============================================================
# Product fixtures
# ============================================================


@pytest.fixture
def product_data() -> dict[str, str | float]:
    return {
        "name": "Test Product",
        "description": "A product created in e2e test.",
        "price": 19.99,
    }


@pytest.fixture
def created_product(
    admin_client,
    product_data,
) -> dict:
    """
    Create a product through the real API.

    This makes the fixture itself an E2E operation.
    """
    response = admin_client.post(
        "/product/",
        json=product_data,
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# Product CRUD E2E
# ============================================================


@pytest.mark.django_db
class TestProductCRUDE2E:
    """Full product create/read/update/delete workflow."""

    def test_admin_create_product(
        self,
        admin_client,
        product_data,
    ):
        response = admin_client.post(
            "/product/",
            json=product_data,
        )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["price"] == product_data["price"]
        assert data["active"] is True

    def test_admin_created_product_visible_in_public_list(
        self,
        created_product,
        api_client,
    ):
        product_id = created_product["id"]

        response = api_client.get(
            "/product/all/",
        )

        assert response.status_code == 200

        products = response.json()

        product = next(product for product in products if product["id"] == product_id)

        assert product["name"] == created_product["name"]
        assert product["description"] == created_product["description"]
        assert product["price"] == created_product["price"]
        assert product["active"] is True

    def test_admin_update_product(
        self,
        created_product,
        admin_client,
    ):
        product_id = created_product["id"]

        update_data = {
            "name": "Updated Product",
            "price": 29.99,
        }

        response = admin_client.patch(
            f"/product/{product_id}/",
            json=update_data,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product_id
        assert data["name"] == "Updated Product"
        assert data["price"] == 29.99

        # Fields not included in PATCH should remain unchanged.
        assert data["description"] == created_product["description"]
        assert data["active"] == created_product["active"]

    def test_updated_product_visible_in_public_list(
        self,
        created_product,
        admin_client,
        api_client,
    ):
        product_id = created_product["id"]

        update_data = {
            "name": "Updated Product",
            "price": 29.99,
        }

        response = admin_client.patch(
            f"/product/{product_id}/",
            json=update_data,
        )

        assert response.status_code == 200

        # Public endpoint does not require authentication.
        response = api_client.get(
            "/product/all/",
        )

        assert response.status_code == 200

        products = response.json()

        product = next(product for product in products if product["id"] == product_id)

        assert product["name"] == "Updated Product"
        assert product["price"] == 29.99

    def test_admin_delete_product(
        self,
        created_product,
        admin_client,
    ):
        product_id = created_product["id"]

        response = admin_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 204

        assert not Products.objects.filter(pk=product_id).exists()

    def test_deleted_product_is_not_visible_in_public_list(
        self,
        created_product,
        admin_client,
        api_client,
    ):
        product_id = created_product["id"]

        response = admin_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 204

        response = api_client.get(
            "/product/all/",
        )

        assert response.status_code == 200

        products = response.json()

        product_ids = [product["id"] for product in products]

        assert product_id not in product_ids


# ============================================================
# Product Create Errors
# ============================================================


@pytest.mark.django_db
class TestProductCreateErrorsE2E:
    def test_create_product_without_authentication(
        self,
        product_data,
        api_client,
    ):
        response = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response.status_code == 401

        assert Products.objects.count() == 0

    def test_create_product_with_invalid_token(
        self,
        product_data,
        live_server,
    ):
        with httpx.Client(
            base_url=live_server.url,
            timeout=10.0,
            headers={
                "Authorization": "Bearer invalid-token",
            },
        ) as client:
            response = client.post(
                "/product/",
                json=product_data,
            )

        assert response.status_code == 401

        assert Products.objects.count() == 0

    def test_create_product_as_non_staff_user(
        self,
        regular_client,
        product_data,
    ):
        response = regular_client.post(
            "/product/",
            json=product_data,
        )

        assert response.status_code == 403

        assert Products.objects.count() == 0

    def test_create_product_missing_name(
        self,
        admin_client,
    ):
        response = admin_client.post(
            "/product/",
            json={
                "description": "Product without name.",
                "price": 10.0,
            },
        )

        assert response.status_code == 400

    def test_create_product_missing_price(
        self,
        admin_client,
    ):
        response = admin_client.post(
            "/product/",
            json={
                "name": "Product without price",
            },
        )

        assert response.status_code == 400

    def test_create_product_invalid_price_type(
        self,
        admin_client,
    ):
        response = admin_client.post(
            "/product/",
            json={
                "name": "Invalid Price Product",
                "price": "not-a-number",
            },
        )

        assert response.status_code == 400


# ============================================================
# Product Update Errors
# ============================================================


@pytest.mark.django_db
class TestProductUpdateErrorsE2E:
    def test_update_nonexistent_product(
        self,
        admin_client,
    ):
        response = admin_client.patch(
            "/product/999999/",
            json={
                "name": "Updated Product",
            },
        )

        assert response.status_code == 404

    def test_update_product_with_invalid_price(
        self,
        created_product,
        admin_client,
    ):
        product_id = created_product["id"]

        response = admin_client.patch(
            f"/product/{product_id}/",
            json={
                "price": "not-a-number",
            },
        )

        assert response.status_code == 400

        product = Products.objects.get(
            pk=product_id,
        )

        assert product.price == created_product["price"]

    def test_update_product_as_non_staff_user(
        self,
        created_product,
        regular_client,
    ):
        product_id = created_product["id"]

        response = regular_client.patch(
            f"/product/{product_id}/",
            json={
                "name": "Unauthorized Update",
            },
        )

        assert response.status_code == 403

        product = Products.objects.get(
            pk=product_id,
        )

        assert product.name == created_product["name"]

    def test_update_product_without_authentication(
        self,
        created_product,
        api_client,
    ):
        product_id = created_product["id"]

        response = api_client.patch(
            f"/product/{product_id}/",
            json={
                "name": "Unauthorized Update",
            },
        )

        assert response.status_code == 401

        product = Products.objects.get(
            pk=product_id,
        )

        assert product.name == created_product["name"]

    def test_update_product_with_invalid_token(
        self,
        created_product,
        live_server,
    ):
        product_id = created_product["id"]

        with httpx.Client(
            base_url=live_server.url,
            timeout=10.0,
            headers={
                "Authorization": "Bearer invalid-token",
            },
        ) as client:
            response = client.patch(
                f"/product/{product_id}/",
                json={
                    "name": "Unauthorized Update",
                },
            )

        assert response.status_code == 401

        product = Products.objects.get(
            pk=product_id,
        )

        assert product.name == created_product["name"]


# ============================================================
# Product Delete Errors
# ============================================================


@pytest.mark.django_db
class TestProductDeleteErrorsE2E:
    def test_delete_nonexistent_product(
        self,
        admin_client,
    ):
        response = admin_client.delete(
            "/product/999999/",
        )

        assert response.status_code == 404

    def test_delete_product_as_non_staff_user(
        self,
        created_product,
        regular_client,
    ):
        product_id = created_product["id"]

        response = regular_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 403

        assert Products.objects.filter(pk=product_id).exists()

    def test_delete_product_without_authentication(
        self,
        created_product,
        api_client,
    ):
        product_id = created_product["id"]

        # api_client is intentionally unauthenticated.
        # It never receives an Authorization header.
        assert api_client.headers.get("Authorization") is None

        response = api_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 401

        # Product must NOT be deleted.
        assert Products.objects.filter(pk=product_id).exists()

    def test_delete_product_with_invalid_token(
        self,
        created_product,
        live_server,
    ):
        product_id = created_product["id"]

        with httpx.Client(
            base_url=live_server.url,
            timeout=10.0,
            headers={
                "Authorization": "Bearer invalid-token",
            },
        ) as client:
            response = client.delete(
                f"/product/{product_id}/",
            )

        assert response.status_code == 401

        assert Products.objects.filter(pk=product_id).exists()


# ============================================================
# Product Delete Success
# ============================================================


@pytest.mark.django_db
class TestProductDeleteSuccessE2E:
    def test_delete_product_as_admin(
        self,
        created_product,
        admin_client,
    ):
        product_id = created_product["id"]

        response = admin_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 204

        assert not Products.objects.filter(pk=product_id).exists()

    def test_delete_product_returns_empty_response(
        self,
        created_product,
        admin_client,
    ):
        product_id = created_product["id"]

        response = admin_client.delete(
            f"/product/{product_id}/",
        )

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_only_target_product(
        self,
        admin_client,
        product_data,
    ):
        first_response = admin_client.post(
            "/product/",
            json={
                **product_data,
                "name": "First Product",
            },
        )

        second_response = admin_client.post(
            "/product/",
            json={
                **product_data,
                "name": "Second Product",
            },
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 201

        first_product_id = first_response.json()["id"]
        second_product_id = second_response.json()["id"]

        response = admin_client.delete(
            f"/product/{first_product_id}/",
        )

        assert response.status_code == 204

        assert not Products.objects.filter(pk=first_product_id).exists()

        assert Products.objects.filter(pk=second_product_id).exists()
