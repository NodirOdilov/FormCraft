from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"webhooks", views.WebhookViewSet, basename="webhook")
router.register(r"", views.IntegrationViewSet, basename="integration")

urlpatterns = [
    path("", include(router.urls)),
]
