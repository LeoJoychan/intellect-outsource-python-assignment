from products.models import Product


class ProductClassifier:
    """
    Handles product classification against the Shopify taxonomy.
    """

    def classify(self, product: Product):
        """
        Classify a product and return a classification result.

        The actual category-matching logic will be implemented
        in the next step.
        """

        return {
            "product_id": product.id,
            "product_number": product.product_number,
            "category": None,
            "confidence": None,
            "explanation": "Classification logic not implemented yet.",
        }