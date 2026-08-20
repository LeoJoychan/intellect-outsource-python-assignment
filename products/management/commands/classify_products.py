from django.core.management.base import BaseCommand

from products.models import Product, ProductClassification
from products.services.classifier import ProductClassifier
from taxonomy.models import ShopifyCategory


class Command(BaseCommand):
    help = "Classify products in batches"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Process only the first N products",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        products = (
            Product.objects
            .exclude(classification__isnull=False)
            .order_by("id")
        )

        if limit:
            products = products[:limit]

        total = products.count()

        self.stdout.write(
            f"Found {total} products to classify."
        )

        classified = 0
        manual_review = 0
        failed = 0

        classifier = ProductClassifier()

        for index, product in enumerate(products, start=1):

            self.stdout.write(
                f"[{index}/{total}] "
                f"Classifying {product.product_number}..."
            )

            try:
                result = classifier.classify(product)

                category = None

                if result["category"]:
                    category = ShopifyCategory.objects.filter(
                        full_name=result["category"]
                    ).first()

                ProductClassification.objects.update_or_create(
                    product=product,
                    defaults={
                        "category": category,
                        "confidence": result["confidence"],
                        "explanation": result["explanation"],
                        "alternatives": result["candidates"][1:],
                        "attributes": result["attributes"],
                        "status": (
                            "manual_review"
                            if result["confidence"] < 0.8
                            else "classified"
                        ),
                    },
                )

                status = (
                    "manual_review"
                    if result["confidence"] < 0.8
                    else "classified"
                )

                if status == "classified":
                    classified += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  OK: {product.product_number} → "
                            f"{result['category']}"
                        )
                    )

                else:
                    manual_review += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"  REVIEW: {product.product_number} → "
                            "Manual review required"
                        )
                    )

            except Exception as exc:
                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"  FAILED: {product.product_number} failed: {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Batch classification complete."
            )
        )
        self.stdout.write(
            f"Classified: {classified}"
        )
        self.stdout.write(
            f"Manual review: {manual_review}"
        )
        self.stdout.write(
            f"Failed: {failed}"
        )