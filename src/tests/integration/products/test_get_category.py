import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.products.models import Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def categories() -> list[dict[str, int | str]]:
    category_list: list[dict[str, int | str]] = []
    categories_objects: list[Category] = Category.objects.all()

    for category in categories_objects:
        object: dict[str, str | int] = {"id": category.id, "name": category.name}
        category_list.append(object)

    return category_list


@pytest.fixture
def url():
    return reverse("category")


@pytest.mark.django_db
def test_get_all_category_success(api_client, url, categories):
    response = api_client.get(url)

    resp_json = response.data

    assert response.status_code == status.HTTP_200_OK
    for category in categories:
        assert category in resp_json
