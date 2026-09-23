import pytest

from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


# ---------------
# Fixtures
# ---------------
@pytest.fixture
def admin_credentials() -> dict[str, str]:
    return {
        "username": "admin_tester",
        "password": "adminpass123",
    }


@pytest.fixture
def admin_user(db, admin_credentials) -> Users:
    """Create a staff user directly in the DB."""
    return Users.objects.create_user(
        username=admin_credentials["username"],
        email="admin_tester@gmail.com",
        password=admin_credentials["password"],
        is_staff=True,
    )


@pytest.fixture
def superuser_credentials() -> dict[str, str]:
    return {
        "username": "superadmin_tester",
        "password": "superadminpass123",
    }


@pytest.fixture
def superuser(db, superuser_credentials) -> Users:
    """Create a superuser directly in the DB."""
    return Users.objects.create_superuser(
        username=superuser_credentials["username"],
        email="superadmin_tester@gmail.com",
        password=superuser_credentials["password"],
    )


@pytest.fixture
def regular_user(db) -> dict[str, str]:
    """Create a non-staff user directly in the DB."""
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
def admin_token(admin_user, admin_credentials, api_client) -> str:
    """Log in as the staff user and return the access token."""
    response = api_client.post(
        "/user/login/",
        json=admin_credentials,
    )

    assert response.status_code == 200

    access_token = response.json().get("access")
    assert access_token

    return access_token


@pytest.fixture
def superuser_token(superuser, superuser_credentials, api_client) -> str:
    """Log in as the superuser and return the access token."""
    response = api_client.post(
        "/user/login/",
        json=superuser_credentials,
    )

    assert response.status_code == 200

    access_token = response.json().get("access")
    assert access_token

    return access_token


@pytest.fixture
def product_data() -> dict[str, str | float]:
    return {
        "name": "Test Product",
        "description": "A product created in e2e test.",
        "price": 19.99,
    }


# ---------------
# E2E: Login → Create → Update
# ---------------
@pytest.mark.django_db
class TestAdminCreateUpdateProductE2E:
    """Admin logs in, creates a product, then updates the same product."""

    def test_admin_login_create_and_update_product(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        # ---------------------------------
        # 1. Authenticate
        # ---------------------------------
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        # ---------------------------------
        # 2. Create product
        # ---------------------------------
        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        created_product = response_create.json()

        assert created_product["name"] == product_data["name"]
        assert created_product["description"] == product_data["description"]
        assert created_product["price"] == product_data["price"]
        assert created_product["active"] is True

        product_id = created_product["id"]
        assert product_id is not None

        # Make sure the product actually exists in DB.
        product = Products.objects.get(pk=product_id)

        assert product.name == product_data["name"]
        assert product.description == product_data["description"]
        assert product.price == product_data["price"]
        assert product.active is True

        # ---------------------------------
        # 3. Update the SAME product
        # ---------------------------------
        update_payload = {
            "name": "Updated Test Product",
            "description": "Updated description.",
            "price": 29.99,
            "active": False,
        }

        response_update = api_client.patch(
            f"/product/{product_id}/",
            json=update_payload,
        )

        assert response_update.status_code == 200

        updated_product = response_update.json()

        # ---------------------------------
        # 4. Check update response
        # ---------------------------------
        assert updated_product["id"] == product_id
        assert updated_product["name"] == update_payload["name"]
        assert updated_product["description"] == update_payload["description"]
        assert updated_product["price"] == update_payload["price"]
        assert updated_product["active"] == update_payload["active"]

        # ---------------------------------
        # 5. Check database
        # ---------------------------------
        product.refresh_from_db()

        assert product.name == update_payload["name"]
        assert product.description == update_payload["description"]
        assert product.price == update_payload["price"]
        assert product.active is False

    def test_admin_partial_update_preserves_other_fields(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        # Create
        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # Only update price.
        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"price": 25.99},
        )

        assert response_update.status_code == 200

        updated_product = response_update.json()

        # Changed field
        assert updated_product["price"] == 25.99

        # Unspecified fields must remain unchanged.
        assert updated_product["name"] == product_data["name"]
        assert updated_product["description"] == product_data["description"]
        assert updated_product["active"] is True

        # Verify DB too.
        product = Products.objects.get(pk=product_id)

        assert product.price == 25.99
        assert product.name == product_data["name"]
        assert product.description == product_data["description"]
        assert product.active is True

    def test_superuser_can_login_create_and_update_product(
        self,
        superuser_token,
        product_data,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {superuser_token}",
        }

        # Create
        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # Update
        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"name": "Updated By Superuser"},
        )

        assert response_update.status_code == 200
        assert response_update.json()["id"] == product_id
        assert response_update.json()["name"] == "Updated By Superuser"

        product = Products.objects.get(pk=product_id)

        assert product.name == "Updated By Superuser"

    def test_updated_product_is_visible_in_public_list(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        # Create
        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # Update
        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"name": "Publicly Updated Product"},
        )

        assert response_update.status_code == 200

        # Public endpoint does not require authentication.
        api_client.headers = {}

        response_list = api_client.get("/product/all/")

        assert response_list.status_code == 200

        products = response_list.json()

        updated_product = next(
            product for product in products if product["id"] == product_id
        )

        assert updated_product["name"] == "Publicly Updated Product"


# ---------------
# E2E: Update permissions
# ---------------
@pytest.mark.django_db
class TestProductUpdatePermissionsE2E:
    """Verify authentication and authorization during product update."""

    def test_regular_user_cannot_update_product(
        self,
        admin_token,
        regular_user,
        product_data,
        api_client,
    ):
        # ---------------------------------
        # 1. Staff creates the product
        # ---------------------------------
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # ---------------------------------
        # 2. Regular user logs in
        # ---------------------------------
        api_client.headers = {}

        response_login = api_client.post(
            "/user/login/",
            json=regular_user,
        )

        assert response_login.status_code == 200

        regular_token = response_login.json().get("access")
        assert regular_token

        # ---------------------------------
        # 3. Regular user tries to update
        # ---------------------------------
        api_client.headers = {
            "Authorization": f"Bearer {regular_token}",
        }

        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"price": 999.99},
        )

        assert response_update.status_code == 403

        # ---------------------------------
        # 4. Product must remain unchanged
        # ---------------------------------
        product = Products.objects.get(pk=product_id)

        assert product.price == product_data["price"]

    def test_unauthenticated_user_cannot_update_product(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        # Staff creates product.
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # Remove authentication.
        api_client.headers = {}

        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"price": 999.99},
        )

        assert response_update.status_code in (401, 403)

        # Product must remain unchanged.
        product = Products.objects.get(pk=product_id)

        assert product.price == product_data["price"]

    def test_invalid_token_cannot_update_product(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        # Staff creates product.
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        # Replace valid token with invalid token.
        api_client.headers = {
            "Authorization": "Bearer invalid-token",
        }

        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"price": 999.99},
        )

        assert response_update.status_code == 401

        product = Products.objects.get(pk=product_id)

        assert product.price == product_data["price"]


# ---------------
# E2E: Update validation / errors
# ---------------
@pytest.mark.django_db
class TestProductUpdateErrorsE2E:
    """Verify invalid product update scenarios."""

    def test_update_non_existing_product(
        self,
        admin_token,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        response = api_client.patch(
            "/product/999999/",
            json={"price": 50.0},
        )

        assert response.status_code == 404

    def test_update_with_invalid_price(
        self,
        admin_token,
        product_data,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        # Create
        response_create = api_client.post(
            "/product/",
            json=product_data,
        )

        assert response_create.status_code == 201

        product_id = response_create.json()["id"]

        original_price = product_data["price"]

        # Invalid PATCH
        response_update = api_client.patch(
            f"/product/{product_id}/",
            json={"price": "not-a-number"},
        )

        assert response_update.status_code == 400

        # Make sure DB was not modified.
        product = Products.objects.get(pk=product_id)

        assert product.price == original_price

    def test_update_missing_product_id(
        self,
        admin_token,
        api_client,
    ):
        api_client.headers = {
            "Authorization": f"Bearer {admin_token}",
        }

        response = api_client.patch(
            "/product/",
            json={"price": 50.0},
        )

        # /product/ belongs to the create-product endpoint,
        # not the update endpoint.
        assert response.status_code == 405
