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
        Find candidate Shopify categories, match attributes,
        and calculate classification confidence.
        """

        candidates = self.find_candidates(product)

        attribute_matches = []
        category = None
        confidence = 0.0
        explanation = "No suitable category candidates found."

        if candidates:
            top_candidate = candidates[0]

            category = top_candidate["full_name"]

            top_score = top_candidate["score"]

            second_score = (
                candidates[1]["score"]
                if len(candidates) > 1
                else 0
            )

            # Confidence is based on how strong the top candidate is
            # compared with the next-best candidate.
            if top_score > 0:
                if second_score >= top_score:
                    confidence = 0.5
                else:
                    confidence = (
                        (top_score - second_score) / top_score
                    )

            top_category = ShopifyCategory.objects.get(
                shopify_id=top_candidate["category_id"]
            )

            attribute_matches = self.match_attributes(
                product,
                top_category,
            )

            explanation_parts = [
                f"Best category match: {category}.",
                f"Category score: {top_score}.",
            ]

            if second_score:
                explanation_parts.append(
                    f"Second-best candidate score: {second_score}."
                )

            if attribute_matches:
                matched_attributes = ", ".join(
                    f"{match['attribute']}={match['value']}"
                    for match in attribute_matches
                )

                explanation_parts.append(
                    f"Matched attributes: {matched_attributes}."
                )

            explanation = " ".join(explanation_parts)

        return {
            "product_id": product.id,
            "product_number": product.product_number,
            "category": category,
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "candidates": candidates,
            "attributes": attribute_matches,
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

        # Broad supplier categories such as "Decor" or "Living Room"
        # can match thousands of unrelated Shopify categories.
        # Therefore, use explicit product-type terms from the product name
        # as the strongest candidate-discovery signals.
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
            "bin",
            "bins",
            "trash",
            "trashcan",
            "trashcans",
            "wastebasket",
            "wastebaskets",
        }

        name_terms = self.extract_terms(
            normalized_fields.get("name", "")
        )

        name_type_terms = {
            term
            for term in name_terms
            if term in product_type_terms
        }

        search_terms.update(name_type_terms)

        # Use the supplier sub-category only when it contains a useful
        # product-type term. Broad terms such as "decor" and "living"
        # are intentionally ignored for candidate discovery.
        for field in (
            "product_sub_category",
            "product_category",
        ):
            text = normalized_fields.get(field, "")
            field_terms = self.extract_terms(text)

            search_terms.update(
                term
                for term in field_terms
                if term in product_type_terms
            )

        # Search multi-word product types as well.
        product_type_phrases = {
            "trash bin",
            "trash can",
            "wastebasket",
            "sofa bed",
            "sectional sofa",
            "loveseat sofa",
        }

        product_text = " ".join(normalized_fields.values())

        for phrase in product_type_phrases:
            if phrase in product_text:
                search_terms.add(phrase)

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

    def match_attributes(self, product, category):
        """
        Match product information against valid Shopify attribute values
        using the most relevant product field for each attribute.
        """

        attribute_fields = {
            "Color": ["color"],
            "Material": ["materials"],
            "Upholstery material": ["materials"],
            "Pattern": ["name", "description"],
            "Chair/Sofa features": ["name", "description", "bullets"],
            "Assembly required": ["description", "bullets"],
            "Care instructions": ["description", "bullets"],
            "Chaise or sectional orientation": [
                "name",
                "description",
                "bullets",
            ],
            "Firmness": ["description", "bullets"],
            "Reclining mechanism": ["name", "description", "bullets"],
            "Safety certifications": ["description", "bullets"],
            "Seat type": ["description", "bullets"],
        }

        product_fields = {
            "name": product.name,
            "description": product.description,
            "bullets": product.bullets,
            "set_includes": product.set_includes,
            "product_category": product.product_category,
            "product_sub_category": product.product_sub_category,
            "color": product.product_color,
            "materials": product.materials,
        }

        normalized_fields = {
            field: self.normalize_text(value)
            for field, value in product_fields.items()
            if value
        }

        matches = []

        for attribute in category.attributes.prefetch_related("values").all():
            fields_to_check = attribute_fields.get(
                attribute.name,
                ["name", "description", "bullets"],
            )

            for value in attribute.values.all():
                value_text = self.normalize_text(value.name)

                if not value_text:
                    continue

                matched_field = None

                for field in fields_to_check:
                    field_text = normalized_fields.get(field, "")

                    if value_text in field_text:
                        matched_field = field
                        break

                if matched_field:
                    matches.append(
                        {
                            "attribute_id": attribute.shopify_id,
                            "attribute": attribute.name,
                            "value_id": value.shopify_id,
                            "value": value.name,
                            "confidence": 1.0,
                            "matched_field": matched_field,
                            "explanation": (
                                f"Matched '{value.name}' from "
                                f"product {matched_field}."
                            ),
                        }
                    )

        return matches

    def score_category(self, category, product_fields):
        """
        Calculate an explainable category relevance score.
        """

        category_text = self.normalize_text(category.full_name)
        category_lower = category_text.lower()
        category_terms = set(self.extract_terms(category_text))

        score = 0
        matched_terms = set()

        # Combine the product information for qualifier checks.
        product_text = " ".join(
            self.normalize_text(value)
            for value in product_fields.values()
            if value
        )

        # ---------------------------------------------------------
        # 1. Score matches from each product field.
        # ---------------------------------------------------------
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

            # Product name is the strongest evidence.
            if field == "name":
                score += len(matches) * 5

        # ---------------------------------------------------------
        # 2. Exact product-type matching.
        #
        # A product explicitly called an "armchair" should strongly
        # prefer an Armchairs category over a generic Sofas category.
        # ---------------------------------------------------------
        product_type_pairs = {
            "sofa": {"sofa", "sofas"},
            "armchair": {"armchair", "armchairs"},
            "chair": {"chair", "chairs"},
            "table": {"table", "tables"},
            "bed": {"bed", "beds"},
            "desk": {"desk", "desks"},
            "cabinet": {"cabinet", "cabinets"},
            "shelf": {"shelf", "shelves"},
            "trash": {"trash", "trash"},
            "bin": {"bin", "bins"},
            "wastebasket": {"wastebasket", "wastebaskets"},
        }

        name_text = self.normalize_text(
            product_fields.get("name", "")
        )

        detected_product_types = set()

        for product_type, variants in product_type_pairs.items():
            if any(
                re.search(rf"\b{re.escape(variant)}\b", name_text)
                for variant in variants
            ):
                detected_product_types.add(product_type)

        for product_type in detected_product_types:
            variants = product_type_pairs[product_type]

            if any(
                re.search(rf"\b{re.escape(variant)}\b", category_lower)
                for variant in variants
            ):
                score += 30
                matched_terms.add(product_type)

        # ---------------------------------------------------------
        # 3. Specific multi-word product types.
        # ---------------------------------------------------------
        specific_product_types = {
            "trash bin": {
                "trash bin",
                "trash bins",
                "trash can",
                "trash cans",
            },
            "sofa bed": {
                "sofa bed",
                "sofa beds",
                "sleeper sofa",
                "sleeper sofas",
            },
            "sectional": {
                "sectional",
                "sectional sofa",
                "sectional sofas",
            },
            "loveseat": {
                "loveseat",
                "loveseat sofa",
                "loveseat sofas",
            },
            "chaise": {
                "chaise",
                "chaise longue",
            },
        }

        for product_type, category_variants in specific_product_types.items():
            product_has_type = product_type in product_text

            if not product_has_type:
                continue

            if any(
                variant in category_lower
                for variant in category_variants
            ):
                score += 40
                matched_terms.add(product_type)

        # ---------------------------------------------------------
        # 4. Penalize categories that describe a different product.
        # ---------------------------------------------------------
        for excluded_term in self.EXCLUDED_CATEGORY_TERMS:
            if excluded_term in category_lower:
                score -= 25

        # ---------------------------------------------------------
        # 5. Penalize unsupported category qualifiers.
        #
        # Example:
        # "Diaper Trash Cans" should not beat ordinary "Trash Cans"
        # when the product contains no diaper-related information.
        # ---------------------------------------------------------
        unsupported_qualifiers = {
            "diaper",
            "pull out",
            "pull-out",
            "pet",
            "bird",
            "aquarium",
            "medical",
            "industrial",
            "outdoor",
            "baby",
            "toddler",
        }

        for qualifier in unsupported_qualifiers:
            if (
                qualifier in category_lower
                and qualifier not in product_text
            ):
                score -= 30

        # ---------------------------------------------------------
        # 6. Penalize unsupported specific furniture types.
        # ---------------------------------------------------------
        specific_category_terms = {
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
                if specific_term not in product_text:
                    score -= 20

        # ---------------------------------------------------------
        # 7. Do not reward taxonomy depth by itself.
        #
        # A deeper category must have its own product evidence.
        # For example, "Floor Sofas & Loungers" should not beat
        # "Sofas" unless the product actually indicates a floor sofa
        # or lounger.
        # ---------------------------------------------------------

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