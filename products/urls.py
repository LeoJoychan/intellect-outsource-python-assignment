from django.urls import path

from products.views import (
    approve_category,
    classify_product,
    dashboard,
    product_detail,
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
        "products/<int:product_id>/classify/",
        classify_product,
        name="classify-product",
    ),
    path(
        "products/<int:product_id>/approve-category/",
        approve_category,
        name="approve-category",
    ),
]