from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Plan, Workspace, WorkspaceMembership
from .serializers import (
    PlanSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    WorkspaceCreateSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_data = UserSerializer(user).data
        return Response(
            {"success": True, "user": user_data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Obtain JWT token pair (access + refresh)."""

    permission_classes = (permissions.AllowAny,)


class TokenRefreshAPIView(TokenRefreshView):
    """Refresh an access token using a refresh token."""

    permission_classes = (permissions.AllowAny,)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve and update the authenticated user's profile."""

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class PlanListView(generics.ListAPIView):
    """List all available subscription plans."""

    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class WorkspaceViewSet(viewsets.ModelViewSet):
    """CRUD operations for workspaces."""

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "create":
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def get_queryset(self):
        return Workspace.objects.filter(
            memberships__user=self.request.user
        ).select_related("owner", "plan").distinct()

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """List all members of a workspace."""
        workspace = self.get_object()
        memberships = workspace.memberships.select_related("user").all()
        serializer = WorkspaceMemberSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Invite a user to the workspace by email."""
        workspace = self.get_object()
        membership = workspace.memberships.filter(
            user=request.user, role__in=["owner", "admin"]
        ).first()
        if not membership:
            return Response(
                {"error": "You do not have permission to invite members."},
                status=status.HTTP_403_FORBIDDEN,
            )
        email = request.data.get("email")
        role = request.data.get("role", WorkspaceMembership.Role.EDITOR)
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if workspace.memberships.filter(user=user).exists():
            return Response(
                {"error": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST
            )
        WorkspaceMembership.objects.create(user=user, workspace=workspace, role=role)
        return Response({"success": True, "message": f"{email} has been invited."})
