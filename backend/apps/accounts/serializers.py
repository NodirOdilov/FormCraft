from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from rest_framework import serializers

from .models import Plan, Workspace, WorkspaceMembership

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "password_confirm")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        # Create a default workspace for the user
        workspace_name = f"{user.first_name or 'My'}'s Workspace"
        base_slug = slugify(workspace_name)
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        workspace = Workspace.objects.create(
            name=workspace_name,
            slug=slug,
            owner=user,
        )
        WorkspaceMembership.objects.create(
            user=user,
            workspace=workspace,
            role=WorkspaceMembership.Role.OWNER,
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "full_name", "avatar", "created_at")
        read_only_fields = ("id", "email", "created_at")


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "avatar")


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans."""

    class Meta:
        model = Plan
        fields = "__all__"


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    """Serializer for workspace membership."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = ("id", "user", "role", "joined_at")
        read_only_fields = ("id", "joined_at")


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for workspaces."""

    owner = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ("id", "name", "slug", "owner", "plan", "member_count", "created_at", "updated_at")
        read_only_fields = ("id", "slug", "owner", "created_at", "updated_at")

    def get_member_count(self, obj):
        return obj.memberships.count()


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workspaces."""

    class Meta:
        model = Workspace
        fields = ("name",)

    def create(self, validated_data):
        user = self.context["request"].user
        base_slug = slugify(validated_data["name"])
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        workspace = Workspace.objects.create(
            name=validated_data["name"],
            slug=slug,
            owner=user,
        )
        WorkspaceMembership.objects.create(
            user=user,
            workspace=workspace,
            role=WorkspaceMembership.Role.OWNER,
        )
        return workspace
