"""
Root URL configuration for FormCraft.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/forms/", include("apps.forms.urls")),
    path("api/submissions/", include("apps.submissions.urls")),
    path("api/templates/", include("apps.templates_lib.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/integrations/", include("apps.integrations.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
