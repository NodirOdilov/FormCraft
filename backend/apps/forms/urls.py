from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.FormViewSet, basename="form")

# We use manual nesting rather than drf-nested-routers to avoid the extra dependency
urlpatterns = [
    path("", include(router.urls)),
    path(
        "<uuid:form_pk>/fields/",
        views.FormFieldViewSet.as_view({"get": "list", "post": "create"}),
        name="form-fields-list",
    ),
    path(
        "<uuid:form_pk>/fields/<uuid:pk>/",
        views.FormFieldViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="form-fields-detail",
    ),
    path(
        "<uuid:form_pk>/rules/",
        views.ConditionalRuleViewSet.as_view({"get": "list", "post": "create"}),
        name="form-rules-list",
    ),
    path(
        "<uuid:form_pk>/rules/<uuid:pk>/",
        views.ConditionalRuleViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="form-rules-detail",
    ),
]
