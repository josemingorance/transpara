"""URL configuration for analytics API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.analytics.views import AnalyticsViewSet

router = DefaultRouter()
router.register(r"", AnalyticsViewSet, basename="analytics")

urlpatterns = [
    path("", include(router.urls)),
]
