from rest_framework import serializers

from .models import Integration, Webhook, WebhookDelivery


class WebhookSerializer(serializers.ModelSerializer):
    delivery_count = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = (
            "id",
            "form",
            "url",
            "secret",
            "events",
            "is_active",
            "description",
            "failure_count",
            "last_triggered_at",
            "delivery_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "failure_count", "last_triggered_at", "created_at", "updated_at")

    def get_delivery_count(self, obj):
        return obj.deliveries.count()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = (
            "id",
            "webhook",
            "submission",
            "event_type",
            "payload",
            "response_status",
            "response_body",
            "success",
            "duration_ms",
            "created_at",
        )
        read_only_fields = fields


class IntegrationListSerializer(serializers.ModelSerializer):
    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )

    class Meta:
        model = Integration
        fields = (
            "id",
            "form",
            "provider",
            "provider_display",
            "name",
            "is_active",
            "last_synced_at",
            "created_at",
        )


class IntegrationDetailSerializer(serializers.ModelSerializer):
    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )

    class Meta:
        model = Integration
        fields = (
            "id",
            "form",
            "provider",
            "provider_display",
            "name",
            "config",
            "field_mapping",
            "is_active",
            "last_synced_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "last_synced_at", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
