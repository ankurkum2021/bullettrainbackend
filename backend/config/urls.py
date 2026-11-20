import config.admin_branding  # noqa: F401
from django.contrib import admin
from django.urls import include, path

from config import views as config_views

urlpatterns = [
    path("", config_views.health, name="api-root"),
    path("admin/", admin.site.urls),
    path("api/health/", config_views.health, name="api-health"),
    path("api/", include("news.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("places.urls")),
]