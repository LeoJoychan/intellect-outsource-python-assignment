from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from products.models import Product
from products.services.classifier import ProductClassifier


def classify_product(request, product_id):
    """
    Return the taxonomy classification for a product.
    """

    product = get_object_or_404(Product, id=product_id)

    result = ProductClassifier().classify(product)

    return JsonResponse(result)