from django.test import TestCase
from django.urls import reverse

from products.models import Product
from products.services.classifier import ProductClassifier
from taxonomy.models import ShopifyCategory


class ProductClassifierTests(TestCase):
    def setUp(self):
        ShopifyCategory.objects.create(
            shopify_id="test-sofa",
            name="Sofas",
            full_name="Furniture > Sofas",
            level=1,
            vertical="Furniture",
            vertical_prefix="fr",
        )

        ShopifyCategory.objects.create(
            shopify_id="test-armchairs",
            name="Armchairs",
            full_name=(
                "Furniture > Chairs > Armchairs, Recliners & "
                "Sleeper Chairs > Armchairs"
            ),
            level=4,
            vertical="Furniture",
            vertical_prefix="fr",
        )

        ShopifyCategory.objects.create(
            shopify_id="test-trash-cans",
            name="Trash Cans",
            full_name=(
                "Home & Garden > Household Supplies > Waste Containment "
                "> Trash Cans & Wastebaskets > Trash Cans"
            ),
            level=5,
            vertical="Home & Garden",
            vertical_prefix="hg",
        )

    def test_sofa_is_classified_as_sofa(self):
        product = Product.objects.create(
            product_number="TEST-SOFA",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas",
        )
        self.assertGreater(result["confidence"], 0)
        self.assertTrue(result["candidates"])

    def test_armchair_is_classified_as_armchair(self):
        product = Product.objects.create(
            product_number="TEST-ARMCHAIR",
            name="Modern Upholstered Fabric Armchair",
            product_category="Living Room",
            product_sub_category="Sofas and Armchairs",
            materials="Upholstered Fabric",
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            (
                "Furniture > Chairs > Armchairs, Recliners & "
                "Sleeper Chairs > Armchairs"
            ),
        )

    def test_trash_bin_is_classified_as_trash_can(self):
        product = Product.objects.create(
            product_number="TEST-TRASH",
            name="Modern Trash Bin",
            product_category="Living Room",
            product_sub_category="Decor",
            materials="Plastic",
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            (
                "Home & Garden > Household Supplies > Waste Containment "
                "> Trash Cans & Wastebaskets > Trash Cans"
            ),
        )

    def test_classification_api_returns_json(self):
        product = Product.objects.create(
            product_number="TEST-API",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
        )

        response = self.client.get(
            reverse(
                "classify-product",
                kwargs={"product_id": product.id},
            )
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["product_id"], product.id)
        self.assertIn("category", data)
        self.assertIn("confidence", data)
        self.assertIn("candidates", data)
        self.assertIn("attributes", data)