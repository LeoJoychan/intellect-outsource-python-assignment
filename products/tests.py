from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from products.models import Product, ProductClassification
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

    def test_product_detail_returns_404_for_invalid_product(self):
        response = self.client.get(
            reverse(
                "product-detail",
                kwargs={"product_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_product_detail_handles_missing_description(self):
        product = Product.objects.create(
            product_number="TEST-NO-DESCRIPTION",
            name="Product Without Description",
            description="",
            image_urls=[],
        )

        response = self.client.get(
            reverse(
                "product-detail",
                kwargs={"product_id": product.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Product Without Description",
        )
        self.assertContains(
            response,
            "No product images available.",
        )


    def test_product_detail_handles_no_images(self):
        product = Product.objects.create(
            product_number="TEST-NO-IMAGES",
            name="Product Without Images",
            image_urls=[],
        )

        response = self.client.get(
            reverse(
                "product-detail",
                kwargs={"product_id": product.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No product images available.",
        )

    def test_classification_api_returns_404_for_invalid_product(self):
        response = self.client.get(
            reverse(
                "classify-product",
                kwargs={"product_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_approve_category_returns_404_for_invalid_category(self):
        product = Product.objects.create(
            product_number="TEST-INVALID-CATEGORY",
            name="Test Product",
        )

        response = self.client.post(
            reverse(
                "approve-category",
                kwargs={"product_id": product.id},
            ),
            {
                "category_id": "does-not-exist",
            },
        )

        self.assertEqual(response.status_code, 404)

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

    def test_approve_category_updates_classification(self):
        product = Product.objects.create(
            product_number="TEST-APPROVE",
            name="Modern Upholstered Armchair",
            product_category="Living Room",
            product_sub_category="Sofas and Armchairs",
            materials="Upholstered Fabric",
        )

        category = ShopifyCategory.objects.get(
            shopify_id="test-armchairs"
        )

        classification = ProductClassification.objects.create(
            product=product,
            category=ShopifyCategory.objects.get(
                shopify_id="test-sofa"
            ),
            confidence=0.5,
            explanation="Needs manual review.",
            status="manual_review",
            alternatives=[
                {
                    "category_id": category.shopify_id,
                    "full_name": category.full_name,
                    "score": 18,
                }
            ],
        )

        response = self.client.post(
            reverse(
                "approve-category",
                kwargs={"product_id": product.id},
            ),
            {
                "category_id": category.shopify_id,
            },
        )

        self.assertEqual(response.status_code, 200)

        classification.refresh_from_db()

        self.assertEqual(
            classification.category,
            category,
        )
        self.assertEqual(
            classification.status,
            "classified",
        )
        self.assertEqual(
            classification.confidence,
            1.0,
        )


    def test_approve_category_requires_post(self):
        product = Product.objects.create(
            product_number="TEST-APPROVE-GET",
            name="Test Armchair",
        )

        ProductClassification.objects.create(
            product=product,
            status="manual_review",
        )

        response = self.client.get(
            reverse(
                "approve-category",
                kwargs={"product_id": product.id},
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_batch_classification_continues_after_failure(self):
        Product.objects.create(
            product_number="TEST-BATCH-FAIL",
            name="Product That Fails",
        )

        Product.objects.create(
            product_number="TEST-BATCH-SUCCESS",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
        )

        original_classify = ProductClassifier.classify

        def fake_classify(self, product):
            if product.product_number == "TEST-BATCH-FAIL":
                raise Exception("Simulated classification failure")

            return original_classify(self, product)

        ProductClassifier.classify = fake_classify

        try:
            call_command(
                "classify_products",
                limit=2,
            )
        finally:
            ProductClassifier.classify = original_classify

        self.assertFalse(
            ProductClassification.objects.filter(
                product__product_number="TEST-BATCH-FAIL"
            ).exists()
        )

        self.assertTrue(
            ProductClassification.objects.filter(
                product__product_number="TEST-BATCH-SUCCESS"
            ).exists()
        )