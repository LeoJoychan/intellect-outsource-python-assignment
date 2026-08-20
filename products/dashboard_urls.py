from django.urls import path

from products.views import dashboard


urlpatterns = [
    path("", dashboard, name="dashboard"),
]