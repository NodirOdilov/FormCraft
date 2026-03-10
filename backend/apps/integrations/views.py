import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Integration, Webhook, WebhookDelivery
from .serializers import (
    IntegrationDetailSerializer,
    IntegrationListSerializer,
    WebhookDeliverySerializer,
    WebhookSerializer,
)
from .services import test_webhook, trigger_integration_sync

logger = logging.getLogger(__name__)


class WebhookViewSet(viewsets.ModelViewSet):
    """CRUD operations for webhooks scoped to the authenticated user."""

    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["form", "is_active"]

    def get_queryset(self):
        return (
            Webhook.objects.filter(created_by=self.request.user)
            .select_related("form")
            .prefetch_related("deliveries")
        )

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Send a test payload to the webhook endpoint."""
        webhook = self.get_object()
        success, response_status, body = test_webhook(webhook)
        return Response(
            {
                "success": success,
                "response_status": response_status,
                "response_body": body[:500],
            }
        )

    @action(detail=True, methods=["post"], url_path="reset-failures")
    def reset_failures(self, request, pk=None):
        """Reset the failure count and re-activate the webhook."""
        webhook = self.get_object()
        webhook.failure_count = 0
        webhook.is_active = True
        webhook.save(update_fields=["failure_count", "is_active", "updated_at"])
        return Response({"success": True})

    @action(detail=True, methods=["get"])
    def deliveries(self, request, pk=None):
        """List recent delivery attempts for this webhook."""
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()[:50]
        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


class IntegrationViewSet(viewsets.ModelViewSet):
    """CRUD operations for third-party integrations."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["form", "provider", "is_active"]

    def get_serializer_class(self):
        if self.action == "list":
            return IntegrationListSerializer
        return IntegrationDetailSerializer

    def get_queryset(self):
        return Integration.objects.filter(
            created_by=self.request.user
        ).select_related("form")

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Manually trigger a sync for this integration."""
        integration = self.get_object()
        success, message = trigger_integration_sync(integration)
        return Response({"success": success, "message": message})

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle integration active state."""
        integration = self.get_object()
        integration.is_active = not integration.is_active
        integration.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"success": True, "is_active": integration.is_active}
        )
