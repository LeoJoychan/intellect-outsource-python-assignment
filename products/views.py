from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from products.models import Product, ProductClassification
from products.services.classifier import ProductClassifier
from taxonomy.models import ShopifyCategory


def dashboard(request):
    """
    Display the product classification dashboard.
    """

    total_products = Product.objects.count()

    classified_products = ProductClassification.objects.filter(
        status="classified"
    ).count()

    manual_review_products = ProductClassification.objects.filter(
        status="manual_review"
    ).count()

    unclassified_products = total_products - (
        classified_products + manual_review_products
    )

    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)

    products_queryset = (
        Product.objects
        .select_related("classification", "classification__category")
        .order_by("product_number")
    )

    if search_query:
        from django.db.models import Q

        products_queryset = products_queryset.filter(
            Q(product_number__icontains=search_query)
            | Q(name__icontains=search_query)
        )

    if status_filter == "classified":
        products_queryset = products_queryset.filter(
            classification__status="classified"
        )

    elif status_filter == "manual_review":
        products_queryset = products_queryset.filter(
            classification__status="manual_review"
        )

    elif status_filter == "unclassified":
        products_queryset = products_queryset.filter(
            classification__isnull=True
        )

    paginator = Paginator(products_queryset, 25)
    products = paginator.get_page(page_number)

    context = {
        "total_products": total_products,
        "classified_products": classified_products,
        "manual_review_products": manual_review_products,
        "unclassified_products": unclassified_products,
        "products": products,
        "status_filter": status_filter,
        "search_query": search_query,
        "page_obj": products,
    }

    return render(
        request,
        "products/dashboard.html",
        context,
    )


def classify_product(request, product_id):
    """
    Classify a product and persist the classification result.
    """

    product = get_object_or_404(Product, id=product_id)

    result = ProductClassifier().classify(product)

    category = None

    if result["category"]:
        category = ShopifyCategory.objects.filter(
            full_name=result["category"]
        ).first()

    classification, created = ProductClassification.objects.update_or_create(
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

    result["classification_id"] = classification.id
    result["status"] = classification.status

    return JsonResponse(result)

def product_detail(request, product_id):
    """
    Display product classification details.
    """

    product = get_object_or_404(
        Product.objects.select_related(
            "classification",
            "classification__category",
        ),
        id=product_id,
    )

    classification = getattr(
        product,
        "classification",
        None,
    )

    context = {
        "product": product,
        "classification": classification,
    }

    return render(
        request,
        "products/product_detail.html",
        context,
    )