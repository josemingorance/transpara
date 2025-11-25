"""URL configuration for providers API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.providers.views import ProviderAlertViewSet, ProviderViewSet

router = DefaultRouter()
router.register(r"", ProviderViewSet, basename="provider")
router.register(r"alerts", ProviderAlertViewSet, basename="provider-alert")

urlpatterns = [
    path("", include(router.urls)),
]
