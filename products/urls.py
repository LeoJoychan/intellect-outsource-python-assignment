from django.urls import path

from products.views import classify_product


urlpatterns = [
    path(
        "products/<int:product_id>/classify/",
        classify_product,
        name="classify-product",
    ),
]