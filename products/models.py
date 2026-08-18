from django.db import models


class Product(models.Model):
    product_number = models.CharField(max_length=100, unique=True)
    model_number = models.CharField(max_length=100, blank=True)

    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    bullets = models.TextField(blank=True)
    set_includes = models.TextField(blank=True)

    product_category = models.CharField(max_length=200, blank=True)
    product_sub_category = models.CharField(max_length=200, blank=True)
    collection_name = models.CharField(max_length=200, blank=True)

    color_collection = models.CharField(max_length=100, blank=True)
    product_color = models.CharField(max_length=200, blank=True)
    materials = models.CharField(max_length=500, blank=True)

    product_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    product_dimensions = models.TextField(blank=True)

    assembly_required = models.CharField(max_length=20, blank=True)
    is_a_set = models.CharField(max_length=20, blank=True)
    stackable = models.CharField(max_length=20, blank=True)

    country_of_origin = models.CharField(max_length=100, blank=True)

    item_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    map_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    msrp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    image_urls = models.JSONField(default=list, blank=True)

    shipping_method = models.CharField(max_length=100, blank=True)

    total_box_count = models.IntegerField(null=True, blank=True)
    pallet_count = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    shipping_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    total_cbm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )

    package_dimensions = models.TextField(blank=True)
    product_url = models.URLField(max_length=1000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_number} - {self.name}"