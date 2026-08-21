from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from products.models import Product, ProductClassification
from products.services.classifier import ProductClassifier
from taxonomy.models import (
    ShopifyAttribute,
    ShopifyAttributeValue,
    ShopifyCategory,
)


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

        color = ShopifyAttribute.objects.create(
            shopify_id="test-color",
            name="Color",
            handle="test-color",
        )

        white = ShopifyAttributeValue.objects.create(
            shopify_id="test-white",
            name="White",
            attribute=color,
        )

        material = ShopifyAttribute.objects.create(
            shopify_id="test-material",
            name="Material",
            handle="test-material",
        )

        leather = ShopifyAttributeValue.objects.create(
            shopify_id="test-leather",
            name="Leather",
            attribute=material,
        )

        sofa_category = ShopifyCategory.objects.get(
            shopify_id="test-sofa"
        )

        sofa_category.attributes.add(
            color,
            material,
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

        ShopifyCategory.objects.create(
            shopify_id="test-sectional-sofas",
            name="Sectional Sofas",
            full_name="Furniture > Sofas > Sectional Sofas",
            level=2,
            vertical="Furniture",
            vertical_prefix="fr",
        )

        ShopifyCategory.objects.create(
            shopify_id="test-loveseat-sofas",
            name="Loveseat Sofas",
            full_name="Furniture > Sofas > Loveseat Sofas",
            level=2,
            vertical="Furniture",
            vertical_prefix="fr",
        )

        ShopifyCategory.objects.create(
            shopify_id="test-chaise-sofas",
            name="Chaise Longue Sofas",
            full_name="Furniture > Sofas > Chaise Longue Sofas",
            level=2,
            vertical="Furniture",
            vertical_prefix="fr",
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

    def test_sectional_is_classified_as_sectional_sofa(self):
        product = Product.objects.create(
            product_number="TEST-SECTIONAL",
            name="Modern Fabric Sectional Sofa",
            product_category="Living Room",
            product_sub_category="Sectional Sofas",
            materials="Fabric",
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas > Sectional Sofas",
        )

    def test_loveseat_is_classified_as_loveseat_sofa(self):
        product = Product.objects.create(
            product_number="TEST-LOVESEAT",
            name="Modern Fabric Loveseat Sofa",
            product_category="Living Room",
            product_sub_category="Loveseats",
            materials="Fabric",
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas > Loveseat Sofas",
        )

    def test_chaise_is_classified_as_chaise_sofa(self):
        product = Product.objects.create(
            product_number="TEST-CHAISE",
            name="Marina Outdoor Patio Teak Single Chaise",
            product_category="Outdoor Furniture",
            product_sub_category="Outdoor Seating",
            materials="Teak",
            description=(
                "Luxurious solid teak wood outdoor seating "
                "for relaxing with friends and family."
            ),
        )

        result = ProductClassifier().classify(product)

        self.assertIn(
            result["category"],
            {
                "Furniture > Chairs > Chaises > Chaise Longues",
                "Furniture > Sofas > Chaise Longue Sofas",
            },
        )

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

    def test_product_name_is_used_for_classification(self):
        product = Product.objects.create(
            product_number="TEST-NAME-CLASSIFICATION",
            name="Modern Leather Sofa",
            product_category="",
            product_sub_category="",
            description="",
            materials="",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas",
        )

    def test_description_is_used_for_classification(self):
        product = Product.objects.create(
            product_number="TEST-DESCRIPTION-CLASSIFICATION",
            name="Modern Home Furniture",
            product_category="",
            product_sub_category="",
            description=(
                "A comfortable upholstered sofa for a living room."
            ),
            materials="",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas",
        )

    def test_product_category_is_used_for_classification(self):
        product = Product.objects.create(
            product_number="TEST-CATEGORY-CLASSIFICATION",
            name="Modern Home Furniture",
            product_category="",
            product_sub_category="Sectional Sofas",
            description="",
            materials="",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas > Sectional Sofas",
        )

    def test_low_confidence_requires_manual_review(self):
        product = Product.objects.create(
            product_number="TEST-MANUAL-REVIEW",
            name="Generic Furniture Product",
            product_category="Furniture",
            description="A simple piece of furniture.",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertLess(result["confidence"], 0.8)
        self.assertEqual(
            result["status"],
            "manual_review",
        )

    def test_high_confidence_is_classified(self):
        product = Product.objects.create(
            product_number="TEST-HIGH-CONFIDENCE",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
        )

        result = ProductClassifier().classify(product)

        # Verify the classifier's status follows the 0.8 threshold.
        if result["confidence"] >= 0.8:
            self.assertEqual(
                result["status"],
                "classified",
            )
        else:
            self.assertEqual(
                result["status"],
                "manual_review",
            )

    def test_classifier_detects_product_attributes(self):
        product = Product.objects.create(
            product_number="TEST-ATTRIBUTES",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
            product_color="White",
            description="A modern leather sofa.",
        )

        result = ProductClassifier().classify(product)

        self.assertTrue(result["attributes"])

        attribute_names = {
            attribute["attribute"]
            for attribute in result["attributes"]
        }

        self.assertIn("Color", attribute_names)
        self.assertIn("Material", attribute_names)

    def test_classifier_returns_alternative_categories(self):
        product = Product.objects.create(
            product_number="TEST-ALTERNATIVES",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
        )

        result = ProductClassifier().classify(product)

        self.assertTrue(result["candidates"])

        if len(result["candidates"]) > 1:
            self.assertTrue(result["alternatives"])

            self.assertEqual(
                result["alternatives"],
                result["candidates"][1:],
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

    def test_classifier_handles_missing_description(self):
        product = Product.objects.create(
            product_number="TEST-CLASSIFIER-NO-DESCRIPTION",
            name="Modern Leather Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Leather",
            description="",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertEqual(
            result["category"],
            "Furniture > Sofas",
        )
        self.assertGreater(
            result["confidence"],
            0,
        )

    def test_classifier_handles_incomplete_product_information(self):
        product = Product.objects.create(
            product_number="TEST-INCOMPLETE",
            name="Basic Leather Sofa",
            product_category="Living Room",
            description="",
            materials="",
            product_color="",
            bullets="",
            set_includes="",
            image_urls=[],
        )

        result = ProductClassifier().classify(product)

        self.assertIsNotNone(result)
        self.assertIn("category", result)
        self.assertIn("confidence", result)
        self.assertIn("status", result)


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

    def test_product_detail_handles_invalid_image_url(self):
        product = Product.objects.create(
            product_number="TEST-BROKEN-IMAGE",
            name="Product With Broken Image",
            image_urls=[
                "https://invalid.example.com/nonexistent-image.jpg"
            ],
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
            "Product With Broken Image",
        )
        self.assertContains(
            response,
            "invalid.example.com",
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