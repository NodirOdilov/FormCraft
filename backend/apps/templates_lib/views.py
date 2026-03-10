import logging

from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.forms.models import FieldOption, Form, FormField, FormSettings
from .models import FormTemplate, TemplateCategory
from .serializers import (
    FormTemplateDetailSerializer,
    FormTemplateListSerializer,
    TemplateCategorySerializer,
)

logger = logging.getLogger(__name__)


class TemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """List template categories."""

    queryset = TemplateCategory.objects.all()
    serializer_class = TemplateCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class FormTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse and use form templates."""

    queryset = FormTemplate.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "tags"]
    filterset_fields = ["category", "is_featured"]
    ordering_fields = ["use_count", "created_at", "name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FormTemplateDetailSerializer
        return FormTemplateListSerializer

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def use(self, request, pk=None):
        """
        Create a new form from this template.
        The template's form_data JSON is used to construct the full form structure.
        """
        template = self.get_object()
        form_data = template.form_data
        user = request.user
        workspace_id = request.data.get("workspace_id")

        # Create the form
        form = Form.objects.create(
            workspace_id=workspace_id,
            created_by=user,
            title=form_data.get("title", template.name),
            description=form_data.get("description", template.description),
            status=Form.Status.DRAFT,
            primary_color=form_data.get("primary_color", "#4F46E5"),
            background_color=form_data.get("background_color", "#FFFFFF"),
            submit_button_text=form_data.get("submit_button_text", "Submit"),
            success_message=form_data.get("success_message", "Thank you for your submission!"),
        )

        # Create settings
        settings_data = form_data.get("settings", {})
        FormSettings.objects.create(
            form=form,
            notification_emails=settings_data.get("notification_emails", ""),
            custom_css=settings_data.get("custom_css", ""),
        )

        # Create fields
        for field_data in form_data.get("fields", []):
            field = FormField.objects.create(
                form=form,
                field_type=field_data.get("field_type", "text"),
                label=field_data.get("label", "Untitled Field"),
                description=field_data.get("description", ""),
                placeholder=field_data.get("placeholder", ""),
                required=field_data.get("required", False),
                order=field_data.get("order", 0),
                page=field_data.get("page", 1),
                min_length=field_data.get("min_length"),
                max_length=field_data.get("max_length"),
                config=field_data.get("config", {}),
            )

            # Create options
            for opt in field_data.get("options", []):
                FieldOption.objects.create(
                    field=field,
                    label=opt.get("label", ""),
                    value=opt.get("value", ""),
                    order=opt.get("order", 0),
                )

        # Increment use count
        FormTemplate.objects.filter(id=template.id).update(use_count=F("use_count") + 1)

        from apps.forms.serializers import FormDetailSerializer

        serializer = FormDetailSerializer(form)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
