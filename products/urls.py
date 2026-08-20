from django.urls import path

from products.views import classify_product, dashboard, product_detail


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
]