from django.core.management import call_command
from django.test import TestCase

from taxonomy.models import (
    ShopifyAttribute,
    ShopifyAttributeValue,
    ShopifyCategory,
)


class TaxonomyImportTest(TestCase):
    def test_import_taxonomy_is_safe_to_run_twice(self):
        call_command("import_taxonomy")

        first_counts = (
            ShopifyAttribute.objects.count(),
            ShopifyAttributeValue.objects.count(),
            ShopifyCategory.objects.count(),
        )

        call_command("import_taxonomy")

        second_counts = (
            ShopifyAttribute.objects.count(),
            ShopifyAttributeValue.objects.count(),
            ShopifyCategory.objects.count(),
        )

        self.assertEqual(first_counts, second_counts)
        