import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken

# Adjust the imports to your app name, e.g. `from shop.views import ...`
from django_ecommers.apps.products.models import Category, Products
from django_ecommers.apps.products.views import (
    CategoryPublicView,
    ProductsPrivateAdminView,
    ProductsPublicView,
    ProductUpdateView,
)

pytestmark = pytest.mark.django_db

User = get_user_model()
factory = APIRequestFactory()


# ---------- helpers & fixtures ----------


def get_items(response):
    """Support both paginated and non-paginated list responses."""
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


@pytest.fixture
def staff_user():
    return User.objects.create_user(
        username="staff", password="pass1234", is_staff=True
    )


@pytest.fixture
def normal_user():
    return User.objects.create_user(username="normal", password="pass1234")


@pytest.fixture
def category():
    return Category.objects.create(name="Electronics")


@pytest.fixture
def product(category):
    return Products.objects.create(
        name="Laptop", description="Fast", price=1000.0, category=category
    )


def jwt_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ---------- CategoryPublicView ----------


class TestCategoryPublicView:
    def test_no_auth_required(self, category):
        request = factory.get("/categories/")
        response = CategoryPublicView.as_view()(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_not_allowed(self):
        request = factory.post("/categories/", {"name": "X"}, format="json")
        response = CategoryPublicView.as_view()(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------- ProductsPublicView ----------


class TestProductsPublicView:
    def test_empty_list(self):
        request = factory.get("/products/")
        response = ProductsPublicView.as_view()(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_lists_all_products(self, category):
        Products.objects.create(name="A", price=1, category=category)
        Products.objects.create(name="B", price=2, category=category)
        request = factory.get("/products/")
        response = ProductsPublicView.as_view()(request)
        assert response.status_code == status.HTTP_200_OK
        assert {item["name"] for item in response.data} == {"A", "B"}

    def test_post_not_allowed(self):
        request = factory.post("/products/", {}, format="json")
        response = ProductsPublicView.as_view()(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------- ProductsPrivateAdminView (POST) ----------


class TestProductsPrivateAdminView:
    view = staticmethod(ProductsPrivateAdminView.as_view())

    def payload(self, category):
        return {
            "name": "Phone",
            "description": "Nice phone",
            "price": 500.5,
            "category": category.pk,
        }

    def test_staff_can_create_product(self, staff_user, category):
        request = factory.post(
            "/admin/products/", self.payload(category), format="json"
        )
        force_authenticate(request, user=staff_user)
        response = self.view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Phone"
        assert Products.objects.filter(name="Phone").count() == 1

    def test_staff_with_real_jwt_token(self, staff_user, category):
        request = factory.post(
            "/admin/products/",
            self.payload(category),
            format="json",
            **jwt_header(staff_user),
        )
        response = self.view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_is_rejected(self, category):
        request = factory.post(
            "/admin/products/", self.payload(category), format="json"
        )
        response = self.view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Products.objects.count() == 0

    def test_non_staff_is_forbidden(self, normal_user, category):
        request = factory.post(
            "/admin/products/", self.payload(category), format="json"
        )
        force_authenticate(request, user=normal_user)
        response = self.view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Products.objects.count() == 0

    def test_invalid_data_returns_400(self, staff_user):
        request = factory.post("/admin/products/", {"name": ""}, format="json")
        force_authenticate(request, user=staff_user)
        response = self.view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Products.objects.count() == 0

    def test_missing_price_returns_400(self, staff_user):
        request = factory.post("/admin/products/", {"name": "NoPrice"}, format="json")
        force_authenticate(request, user=staff_user)
        response = self.view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "price" in response.data

    def test_get_not_allowed(self, staff_user):
        request = factory.get("/admin/products/")
        force_authenticate(request, user=staff_user)
        response = self.view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------- ProductUpdateView (PATCH / DELETE) ----------


class TestProductUpdateView:
    view = staticmethod(ProductUpdateView.as_view())

    # PATCH
    def test_staff_can_partially_update(self, staff_user, product):
        request = factory.patch(
            f"/admin/products/{product.pk}/", {"price": 750}, format="json"
        )
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.price == 750
        assert product.name == "Laptop"  # untouched

    def test_patch_deactivate_product(self, staff_user, product):
        request = factory.patch(
            f"/admin/products/{product.pk}/", {"active": False}, format="json"
        )
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.active is False

    def test_patch_invalid_data_returns_400(self, staff_user, product):
        request = factory.patch(
            f"/admin/products/{product.pk}/", {"price": "not-a-number"}, format="json"
        )
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        product.refresh_from_db()
        assert product.price == 1000.0

    def test_patch_nonexistent_returns_404(self, staff_user):
        request = factory.patch("/admin/products/999/", {"price": 1}, format="json")
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_unauthenticated(self, product):
        request = factory.patch(
            f"/admin/products/{product.pk}/", {"price": 1}, format="json"
        )
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_non_staff_forbidden(self, normal_user, product):
        request = factory.patch(
            f"/admin/products/{product.pk}/", {"price": 1}, format="json"
        )
        force_authenticate(request, user=normal_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        product.refresh_from_db()
        assert product.price == 1000.0

    # DELETE
    def test_staff_can_delete(self, staff_user, product):
        request = factory.delete(f"/admin/products/{product.pk}/")
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Products.objects.filter(pk=product.pk).exists()

    def test_delete_nonexistent_returns_404(self, staff_user):
        request = factory.delete("/admin/products/999/")
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_unauthenticated(self, product):
        request = factory.delete(f"/admin/products/{product.pk}/")
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Products.objects.filter(pk=product.pk).exists()

    def test_delete_non_staff_forbidden(self, normal_user, product):
        request = factory.delete(f"/admin/products/{product.pk}/")
        force_authenticate(request, user=normal_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Products.objects.filter(pk=product.pk).exists()

    def test_get_not_allowed(self, staff_user, product):
        request = factory.get(f"/admin/products/{product.pk}/")
        force_authenticate(request, user=staff_user)
        response = self.view(request, pk=product.pk)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
