from django.urls import path

from products.views import (
    approve_category,
    classify_product,
    dashboard,
    product_api,
    product_detail,
    search_categories
)


urlpatterns = [
    path(
        "",
        dashboard,
        name="dashboard",
    ),
    path(
        "products/<int:product_id>/",
        product_detail,
        name="product-detail",
    ),
    path(
        "products/<int:product_id>/api/",
        product_api,
        name="product-api",
    ),
    path(
        "products/<int:product_id>/classify/",
        classify_product,
        name="classify-product",
    ),
    path(
        "products/<int:product_id>/approve-category/",
        approve_category,
        name="approve-category",
    ),
    path(
        "categories/search/",
        search_categories,
        name="search-categories",
    ),
]