from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = "Import products from Product List.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Import only the first N products",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        file_path = Path("data") / "Product List.xlsx"

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"Excel file not found: {file_path}"
                )
            )
            return

        self.stdout.write(f"Reading: {file_path}")

        df = pd.read_excel(file_path)

        if limit:
            df = df.head(limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(df)} products to import."
            )
        )

        imported = 0
        skipped = 0

        for _, row in df.iterrows():
            product_number = str(row.get("Product Number", "")).strip()

            if not product_number or product_number == "nan":
                skipped += 1
                continue

            product = Product.objects.update_or_create(
                product_number=product_number,
                defaults={
                    "model_number": self.clean_value(
                        row.get("Model Number")
                    ),
                    "name": self.clean_value(
                        row.get("Product Name")
                    ),
                    "description": self.clean_value(
                        row.get("Product Description")
                    ),
                    "product_category": self.clean_value(
                        row.get("Product Category")
                    ),
                    "product_sub_category": self.clean_value(
                        row.get("Product Sub Category")
                    ),
                    "collection_name": self.clean_value(
                        row.get("Collection Name")
                    ),
                    "color_collection": self.clean_value(
                        row.get("Color Collection")
                    ),
                    "product_color": self.clean_value(
                        row.get("Product Color")
                    ),
                    "bullets": self.clean_value(
                        row.get("Bullets")
                    ),
                    "set_includes": self.clean_value(
                        row.get("Set Includes")
                    ),
                    "materials": self.clean_value(
                        row.get("Materials")
                    ),
                    "product_dimensions": self.clean_value(
                        row.get("Product Dimensions")
                    ),
                    "assembly_required": self.clean_value(
                        row.get("Assembly Required")
                    ),
                    "is_a_set": self.clean_value(
                        row.get("Is a Set")
                    ),
                    "stackable": self.clean_value(
                        row.get("Stackable")
                    ),
                    "country_of_origin": self.clean_value(
                        row.get("Country Of Origin")
                    ),
                    "product_weight": self.clean_number(
                        row.get("Product Weight")
                    ),
                    "item_cost": self.clean_number(
                        row.get("Item Cost")
                    ),
                    "map_price": self.clean_number(
                        row.get("MAP")
                    ),
                    "msrp": self.clean_number(
                        row.get("MSRP")
                    ),
                    "image_urls": self.get_image_urls(row),
                    "shipping_method": self.clean_value(
                        row.get("Shipping Method")
                    ),
                    "total_box_count": self.clean_integer(
                        row.get("Total Box Count")
                    ),
                    "pallet_count": self.clean_number(
                        row.get("Pallet Count")
                    ),
                    "shipping_weight": self.clean_number(
                        row.get("Shipping Weight")
                    ),
                    "total_cbm": self.clean_number(
                        row.get("Total CBM")
                    ),
                    "package_dimensions": self.clean_value(
                        row.get("Package Dimensions")
                    ),
                    "product_url": self.clean_value(
                        row.get("Product URL")
                    ),
                },
            )

            imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Imported/updated: {imported}, "
                f"Skipped: {skipped}"
            )
        )

    @staticmethod
    def clean_value(value):
        if pd.isna(value):
            return ""

        return str(value).strip()

    @staticmethod
    def clean_number(value):
        if pd.isna(value):
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def clean_integer(value):
        if pd.isna(value):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_image_urls(row):
        image_urls = []

        for i in range(1, 21):
            column = f"Image {i}"
            value = row.get(column)

            if pd.notna(value):
                url = str(value).strip()

                if url:
                    image_urls.append(url)

        return image_urls