from django.urls import path

from . import views

urlpatterns = [
    path("view/", views.RecordFormViewAPIView.as_view(), name="record-form-view"),
    path(
        "<uuid:form_id>/overview/",
        views.FormOverviewAPIView.as_view(),
        name="form-overview",
    ),
    path(
        "<uuid:form_id>/dropoff/",
        views.FieldDropoffAPIView.as_view(),
        name="field-dropoff",
    ),
]
