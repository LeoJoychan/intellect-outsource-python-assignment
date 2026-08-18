from django.db import models


class ShopifyAttribute(models.Model):
    shopify_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    handle = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    extended_attributes = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name


class ShopifyAttributeValue(models.Model):
    shopify_id = models.CharField(max_length=100, unique=True)
    attribute = models.ForeignKey(
        ShopifyAttribute,
        on_delete=models.CASCADE,
        related_name="values",
    )
    name = models.CharField(max_length=255)
    handle = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "handle"],
                name="unique_attribute_value_handle",
            )
        ]

    def __str__(self):
        return f"{self.attribute.name}: {self.name}"


class ShopifyCategory(models.Model):
    shopify_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    full_name = models.TextField()
    level = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    vertical = models.CharField(max_length=255, blank=True)
    vertical_prefix = models.CharField(max_length=50, blank=True)

    attributes = models.ManyToManyField(
        ShopifyAttribute,
        related_name="categories",
        blank=True,
    )

    def __str__(self):
        return self.full_name