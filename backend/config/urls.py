"""URL configuration for PublicWorks AI."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # API Endpoints
    path("api/v1/contracts/", include("apps.contracts.urls")),
    path("api/v1/providers/", include("apps.providers.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
]
