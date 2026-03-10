from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"workspaces", views.WorkspaceViewSet, basename="workspace")

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.TokenRefreshAPIView.as_view(), name="token_refresh"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("plans/", views.PlanListView.as_view(), name="plans"),
    path("", include(router.urls)),
]
