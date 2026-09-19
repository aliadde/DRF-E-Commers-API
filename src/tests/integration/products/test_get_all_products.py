import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.products.models import Products


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def url():
    return reverse("get_all_products")


@pytest.mark.django_db
def test_get_products(api_client, url):
    """Get all products."""
    response = api_client.get(url)

    assert response.status_code == 200
