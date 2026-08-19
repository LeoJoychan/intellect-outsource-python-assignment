import re

from django.db.models import Q

from products.models import Product
from taxonomy.models import ShopifyCategory


class ProductClassifier:
    """
    Handles product classification against the Shopify taxonomy.
    """

    FIELD_WEIGHTS = {
        "name": 10,
        "product_sub_category": 8,
        "product_category": 3,
        "bullets": 3,
        "set_includes": 3,
        "materials": 1,
        "description": 2,
    }

    EXCLUDED_CATEGORY_TERMS = {
        "accessories",
        "accessory",
        "cushion",
        "cushions",
        "cover",
        "covers",
        "throw",
        "throws",
        "table",
        "tables",
        "parts",
        "replacement",
        "support",
        "supports",
        "legs",
    }

    def classify(self, product: Product):
        """
        Find candidate Shopify categories for a product.
        """

        candidates = self.find_candidates(product)

        return {
            "product_id": product.id,
            "product_number": product.product_number,
            "category": None,
            "confidence": None,
            "explanation": "Candidate categories generated.",
            "candidates": candidates,
        }

    def find_candidates(self, product: Product, limit=10):
        """
        Find and rank relevant Shopify categories.
        """

        product_fields = {
            "name": product.name,
            "product_sub_category": product.product_sub_category,
            "product_category": product.product_category,
            "bullets": product.bullets,
            "set_includes": product.set_includes,
            "materials": product.materials,
            "description": product.description,
        }

        normalized_fields = {
            field: self.normalize_text(value)
            for field, value in product_fields.items()
            if value
        }

        if not normalized_fields:
            return []

        search_terms = set()

        # Product-type/category fields are used to discover candidates.
        # Material and descriptive words such as "leather" are deliberately
        # excluded from candidate discovery.
        for field in (
            "product_sub_category",
            "product_category",
        ):
            text = normalized_fields.get(field, "")
            search_terms.update(self.extract_terms(text))

        # Add product-type terms from the product name.
        # Only words that represent likely product types are used here.
        product_type_terms = {
            "sofa",
            "sofas",
            "armchair",
            "armchairs",
            "chair",
            "chairs",
            "table",
            "tables",
            "bed",
            "beds",
            "desk",
            "desks",
            "cabinet",
            "cabinets",
            "shelf",
            "shelves",
        }

        name_terms = self.extract_terms(
            normalized_fields.get("name", "")
        )

        search_terms.update(
            term
            for term in name_terms
            if term in product_type_terms
        )

        if not search_terms:
            return []

        query = Q()

        for term in search_terms:
            query |= Q(name__icontains=term)
            query |= Q(full_name__icontains=term)

        categories = ShopifyCategory.objects.filter(query).distinct()

        scored_candidates = []

        for category in categories:
            score, matched_terms = self.score_category(
                category,
                normalized_fields,
            )

            if score > 0:
                scored_candidates.append(
                    {
                        "category_id": category.shopify_id,
                        "name": category.name,
                        "full_name": category.full_name,
                        "score": score,
                        "matched_terms": sorted(matched_terms),
                    }
                )

        scored_candidates.sort(
            key=lambda candidate: candidate["score"],
            reverse=True,
        )

        return scored_candidates[:limit]

    def score_category(self, category, product_fields):
        """
        Calculate an explainable category relevance score.
        """

        category_text = self.normalize_text(category.full_name)
        category_terms = set(self.extract_terms(category_text))

        score = 0
        matched_terms = set()

        for field, weight in self.FIELD_WEIGHTS.items():
            text = product_fields.get(field, "")

            if not text:
                continue

            field_terms = set(self.extract_terms(text))
            matches = field_terms & category_terms

            if not matches:
                continue

            score += len(matches) * weight
            matched_terms.update(matches)

            # Strong boost for product type terms found directly
            # in the product name.
            if field == "name":
                score += len(matches) * 5

                # Product-type words in the name are much stronger
                # than material/descriptive words.
                product_type_terms = {
                    "sofa",
                    "sofas",
                    "armchair",
                    "armchairs",
                    "chair",
                    "chairs",
                    "table",
                    "tables",
                    "bed",
                    "beds",
                    "desk",
                    "desks",
                    "cabinet",
                    "cabinets",
                    "shelf",
                    "shelves",
                }

                type_matches = matches & product_type_terms

                if type_matches:
                    score += len(type_matches) * 15

            # Strong boost for matches against the supplier's
            # existing product sub-category.
            if field == "product_sub_category":
                score += len(matches) * 5

        # Penalize categories that describe accessories or related
        # products instead of the main product.
        category_lower = category_text.lower()

        for excluded_term in self.EXCLUDED_CATEGORY_TERMS:
            if excluded_term in category_lower:
                score -= 25

        # Do not automatically reward deeper categories.
        #
        # A specific category such as "Sofa Beds" should only beat
        # "Sofas" when the product itself contains evidence for it.

        specific_category_terms = {
            "outdoor",
            "sectional",
            "loveseat",
            "chaise",
            "corner",
            "bean bag",
            "sofa bed",
            "sofa beds",
            "sleeper",
        }

        for specific_term in specific_category_terms:
            if specific_term in category_lower:
                product_text = " ".join(product_fields.values())

                if specific_term not in product_text:
                    score -= 20

        return score, matched_terms

    @staticmethod
    def normalize_text(value):
        """
        Normalize product/category text for matching.
        """

        if not value:
            return ""

        value = value.replace("_x000D_", " ")
        value = value.lower()

        value = re.sub(r"[^a-z0-9]+", " ", value)

        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def extract_terms(text):
        """
        Extract meaningful words from normalized text.
        """

        if not text:
            return set()

        stop_words = {
            "and",
            "the",
            "by",
            "for",
            "with",
            "from",
            "one",
            "of",
            "a",
            "an",
            "to",
            "in",
            "on",
        }

        words = text.split()

        return {
            word
            for word in words
            if len(word) >= 3 and word not in stop_words
        }