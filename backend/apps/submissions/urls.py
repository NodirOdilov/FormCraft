from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.SubmissionViewSet, basename="submission")

urlpatterns = [
    path("upload/", views.FileUploadView.as_view({"post": "create"}), name="file-upload"),
    path("", include(router.urls)),
]
