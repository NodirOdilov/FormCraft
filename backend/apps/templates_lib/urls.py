from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"categories", views.TemplateCategoryViewSet, basename="template-category")
router.register(r"", views.FormTemplateViewSet, basename="form-template")

urlpatterns = [
    path("", include(router.urls)),
]
