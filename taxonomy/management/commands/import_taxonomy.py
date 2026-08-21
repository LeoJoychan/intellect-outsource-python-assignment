import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from taxonomy.models import (
    ShopifyAttribute,
    ShopifyAttributeValue,
    ShopifyCategory,
)


class Command(BaseCommand):
    help = "Import Shopify taxonomy data from JSON files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing taxonomy data before importing.",
        )

        # parser.add_argument(
        #     "--limit",
        #     type=int,
        #     default=None,
        #     help="Limit the number of attributes and values imported.",
        # )

    def handle(self, *args, **options):
        base_dir = Path("data/shopify_taxonomy")

        categories_file = base_dir / "categories.json"
        attributes_file = base_dir / "attributes.json"
        values_file = base_dir / "attribute_values.json"

        for file_path in (categories_file, attributes_file, values_file):
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Required taxonomy file not found: {file_path}"
                )

        self.stdout.write("Reading Shopify taxonomy files...")

        with open(attributes_file, "r", encoding="utf-8") as file:
            attributes_data = json.load(file)

        with open(values_file, "r", encoding="utf-8") as file:
            values_data = json.load(file)

        with open(categories_file, "r", encoding="utf-8") as file:
            categories_data = json.load(file)

        attributes = attributes_data.get("attributes", [])
        values = values_data.get("values", [])
        verticals = categories_data.get("verticals", [])

        # limit = options["limit"]

        # if limit:
        #     attributes = attributes[:limit]
        #     values = values[:limit]

        self.stdout.write(
            f"Found {len(attributes)} attributes, "
            f"{len(values)} attribute values, "
            f"and {len(verticals)} verticals."
        )

        with transaction.atomic():
            if options["clear"]:
                self.stdout.write("Clearing existing taxonomy data...")

                ShopifyCategory.objects.all().delete()
                ShopifyAttributeValue.objects.all().delete()
                ShopifyAttribute.objects.all().delete()

            self.import_attributes(attributes)
            self.import_values(values)
            self.import_categories(verticals)

        self.stdout.write(
            self.style.SUCCESS("Shopify taxonomy import completed successfully.")
        )

    def import_attributes(self, attributes):
        objects = []

        for item in attributes:
            objects.append(
                ShopifyAttribute(
                    shopify_id=item["id"],
                    name=item["name"],
                    handle=item["handle"],
                    description=item.get("description", ""),
                    extended_attributes=item.get(
                        "extended_attributes", []
                    ),
                )
            )

        ShopifyAttribute.objects.bulk_create(
            objects,
            batch_size=1000,
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported/updated {len(objects)} attributes."
            )
        )

    def import_values(self, values):
        attribute_map = {}

        for attribute in ShopifyAttribute.objects.only(
            "id", "handle"
        ):
            attribute_map[attribute.handle] = attribute.id

        objects = []
        skipped = 0

        for item in values:
            handle = item["handle"]

            if "__" not in handle:
                skipped += 1
                continue

            attribute_handle = handle.split("__", 1)[0]
            attribute_pk = attribute_map.get(attribute_handle)

            if attribute_pk is None:
                skipped += 1
                continue

            objects.append(
                ShopifyAttributeValue(
                    shopify_id=item["id"],
                    attribute_id=attribute_pk,
                    name=item["name"],
                    handle=item["handle"],
                )
            )

        ShopifyAttributeValue.objects.bulk_create(
            objects,
            batch_size=1000,
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported/updated {len(objects)} attribute values. "
                f"Skipped: {skipped}."
            )
        )

    def import_categories(self, verticals):
        category_data = {}
        category_attributes = {}

        for vertical in verticals:
            vertical_name = vertical.get("name", "")
            vertical_prefix = vertical.get("prefix", "")

            for category in self.flatten_categories(
                vertical.get("categories", [])
            ):
                category_id = category["id"]

                # Keep only one copy of each Shopify category.
                category_data[category_id] = {
                    "name": category["name"],
                    "full_name": category.get(
                        "full_name",
                        category["name"],
                    ),
                    "level": category.get("level", 0),
                    "parent_id": category.get("parent_id"),
                    "vertical": vertical_name,
                    "vertical_prefix": vertical_prefix,
                }

                category_attributes[category_id] = [
                    attribute["id"]
                    for attribute in category.get("attributes", [])
                ]

        category_objects = [
            ShopifyCategory(
                shopify_id=category_id,
                name=data["name"],
                full_name=data["full_name"],
                level=data["level"],
                vertical=data["vertical"],
                vertical_prefix=data["vertical_prefix"],
            )
            for category_id, data in category_data.items()
        ]

        ShopifyCategory.objects.bulk_create(
            category_objects,
            batch_size=1000,
            ignore_conflicts=True,
        )
        category_map = {
            category.shopify_id: category
            for category in ShopifyCategory.objects.all()
        }

        # Set parent relationships.
        update_categories = []

        for category_id, data in category_data.items():
            category_obj = category_map.get(category_id)

            if not category_obj:
                continue

            parent_id = data["parent_id"]

            if parent_id and parent_id in category_map:
                category_obj.parent_id = category_map[parent_id].id
            else:
                category_obj.parent_id = None

            update_categories.append(category_obj)

        ShopifyCategory.objects.bulk_update(
            update_categories,
            ["parent"],
            batch_size=1000,
        )

        # Set category → attribute relationships.
        through_model = ShopifyCategory.attributes.through

        through_objects = []

        attribute_map = {
            attribute.shopify_id: attribute.id
            for attribute in ShopifyAttribute.objects.only(
                "id",
                "shopify_id",
            )
        }

        for category_id, attribute_ids in category_attributes.items():
            category_obj = category_map.get(category_id)

            if not category_obj:
                continue

            for attribute_id in attribute_ids:
                attribute_pk = attribute_map.get(attribute_id)

                if attribute_pk:
                    through_objects.append(
                        through_model(
                            shopifycategory_id=category_obj.id,
                            shopifyattribute_id=attribute_pk,
                        )
                    )

        through_model.objects.bulk_create(
            through_objects,
            batch_size=2000,
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(category_objects)} unique categories."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(through_objects)} category-attribute relationships."
            )
        )

    @staticmethod
    def flatten_categories(categories):
        for category in categories:
            yield category

            children = category.get("children", [])

            if children:
                yield from Command.flatten_categories(children)