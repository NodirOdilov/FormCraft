import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ConditionalRule, Form, FormField, FormSettings
from .serializers import (
    ConditionalRuleSerializer,
    FormBulkFieldUpdateSerializer,
    FormCreateUpdateSerializer,
    FormDetailSerializer,
    FormFieldSerializer,
    FormListSerializer,
    FormSettingsSerializer,
    PublicFormSerializer,
)
from .services import duplicate_form

logger = logging.getLogger(__name__)


class FormViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for forms.
    List returns lightweight data; detail returns full form with fields.
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "title"]
    filterset_fields = ["status", "workspace"]

    def get_permissions(self):
        if self.action in ("public", "public_by_slug"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return FormListSerializer
        if self.action in ("create", "update", "partial_update"):
            return FormCreateUpdateSerializer
        if self.action in ("public", "public_by_slug"):
            return PublicFormSerializer
        return FormDetailSerializer

    def get_queryset(self):
        if self.action in ("public", "public_by_slug"):
            return Form.objects.filter(status=Form.Status.PUBLISHED).prefetch_related(
                "fields__options", "fields__conditional_rules"
            )
        return (
            Form.objects.filter(created_by=self.request.user)
            .prefetch_related("fields__options", "fields__conditional_rules")
            .select_related("settings", "workspace")
        )

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Duplicate a form with all its fields and settings."""
        form = self.get_object()
        new_form = duplicate_form(form, request.user)
        serializer = FormDetailSerializer(new_form)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish a draft form."""
        form = self.get_object()
        if form.fields.count() == 0:
            return Response(
                {"error": "Cannot publish a form with no fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        form.status = Form.Status.PUBLISHED
        form.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "status": form.status})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Close a published form."""
        form = self.get_object()
        form.status = Form.Status.CLOSED
        form.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "status": form.status})

    @action(detail=True, methods=["get", "put"], url_path="settings")
    def form_settings(self, request, pk=None):
        """Get or update form settings."""
        form = self.get_object()
        settings_obj, _ = FormSettings.objects.get_or_create(form=form)
        if request.method == "GET":
            serializer = FormSettingsSerializer(settings_obj)
            return Response(serializer.data)
        serializer = FormSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="reorder-fields")
    def reorder_fields(self, request, pk=None):
        """Bulk update field order and page assignments."""
        form = self.get_object()
        serializer = FormBulkFieldUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        field_updates = serializer.validated_data["fields"]
        for item in field_updates:
            FormField.objects.filter(id=item["id"], form=form).update(
                order=item["order"], page=item.get("page", 1)
            )
        return Response({"success": True})

    @action(
        detail=False,
        methods=["get"],
        url_path="by-slug/(?P<slug>[^/.]+)",
        permission_classes=[permissions.AllowAny],
    )
    def public_by_slug(self, request, slug=None):
        """Retrieve a published form by its slug (public endpoint)."""
        try:
            form = Form.objects.prefetch_related(
                "fields__options", "fields__conditional_rules"
            ).select_related("settings").get(slug=slug, status=Form.Status.PUBLISHED)
        except Form.DoesNotExist:
            return Response(
                {"error": "Form not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = PublicFormSerializer(form)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="embed-code")
    def embed_code(self, request, pk=None):
        """Generate embed code snippets for the form."""
        form = self.get_object()
        base_url = request.build_absolute_uri("/").rstrip("/")
        form_url = f"{base_url}/f/{form.slug}"

        iframe_code = (
            f'<iframe src="{form_url}" width="100%" height="600" '
            f'frameborder="0" style="border:none;"></iframe>'
        )
        script_code = (
            f'<div id="formcraft-{form.id}"></div>\n'
            f'<script src="{base_url}/embed.js" '
            f'data-form-id="{form.id}" data-form-slug="{form.slug}"></script>'
        )
        link = form_url

        return Response(
            {"iframe": iframe_code, "script": script_code, "link": link}
        )


class FormFieldViewSet(viewsets.ModelViewSet):
    """CRUD operations for form fields, scoped to a specific form."""

    serializer_class = FormFieldSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        form_id = self.kwargs.get("form_pk")
        return (
            FormField.objects.filter(form_id=form_id, form__created_by=self.request.user)
            .prefetch_related("options", "conditional_rules")
        )

    def perform_create(self, serializer):
        form_id = self.kwargs.get("form_pk")
        form = Form.objects.get(id=form_id, created_by=self.request.user)
        serializer.save(form=form)


class ConditionalRuleViewSet(viewsets.ModelViewSet):
    """CRUD operations for conditional rules within a form."""

    serializer_class = ConditionalRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        form_id = self.kwargs.get("form_pk")
        return ConditionalRule.objects.filter(
            field__form_id=form_id,
            field__form__created_by=self.request.user,
        )
