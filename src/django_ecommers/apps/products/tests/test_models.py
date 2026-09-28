import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

# Adjust the import to your app name, e.g. `from shop.models import ...`
from django_ecommers.apps.products.models import Category, Products

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(name="Electronics")


@pytest.fixture
def product(category):
    return Products.objects.create(
        name="Laptop",
        description="A powerful laptop",
        price=999.99,
        category=category,
    )


class TestCategory:
    def test_create_category(self):
        cat = Category.objects.create(name="Books")
        assert cat.pk is not None
        assert cat.name == "Books"

    def test_name_max_length(self):
        assert Category._meta.get_field("name").max_length == 200

    def test_name_too_long_fails_validation(self):
        cat = Category(name="x" * 201)
        with pytest.raises(ValidationError):
            cat.full_clean()

    def test_blank_name_fails_validation(self):
        with pytest.raises(ValidationError):
            Category(name="").full_clean()

    def test_delete_category_without_products(self, category):
        category.delete()
        assert Category.objects.count() == 3


class TestProducts:
    def test_create_product(self, product, category):
        assert product.pk is not None
        assert product.name == "Laptop"
        assert product.description == "A powerful laptop"
        assert product.price == 999.99
        assert product.category == category

    def test_defaults(self):
        p = Products.objects.create(name="Pen", price=1.5)
        assert p.active == 1
        assert p.description is None
        assert p.category is None

    def test_active_can_be_set_false(self):
        p = Products.objects.create(name="Old item", price=5, active=False)
        p.refresh_from_db()
        assert p.active is False

    @pytest.mark.parametrize("price", [0, 0.01, 19.99, 1_000_000.5])
    def test_price_is_stored_as_float(self, price):
        p = Products.objects.create(name="Item", price=price)
        p.refresh_from_db()
        assert isinstance(p.price, float)
        assert p.price == pytest.approx(price)

    def test_price_is_required(self):
        p = Products(name="No price")
        with pytest.raises(ValidationError) as exc:
            p.full_clean()
        assert "price" in exc.value.message_dict

    def test_name_is_required(self):
        p = Products(name="", price=10)
        with pytest.raises(ValidationError) as exc:
            p.full_clean()
        assert "name" in exc.value.message_dict

    def test_description_and_category_are_optional(self):
        p = Products(name="Minimal", price=10)
        p.full_clean()  # should not raise

    def test_category_relation_reverse_access(self, product, category):
        assert list(category.products_set.all()) == [product]

    def test_multiple_products_in_one_category(self, category):
        Products.objects.create(name="A", price=1, category=category)
        Products.objects.create(name="B", price=2, category=category)
        assert category.products_set.count() == 2

    def test_delete_category_with_products_is_protected(self, product, category):
        with pytest.raises(ProtectedError):
            category.delete()
        assert Category.objects.filter(pk=category.pk).exists()
        assert Products.objects.filter(pk=product.pk).exists()

    def test_delete_category_allowed_after_products_removed(self, product, category):
        product.delete()
        category.delete()
        assert Category.objects.count() == 3

    def test_delete_product_keeps_category(self, product, category):
        product.delete()
        assert Category.objects.filter(pk=category.pk).exists()

    def test_filter_active_products(self, category):
        Products.objects.create(name="On", price=1, active=True, category=category)
        Products.objects.create(name="Off", price=1, active=False, category=category)
        names = list(
            Products.objects.filter(active=True).values_list("name", flat=True)
        )
        assert names == ["On"]
