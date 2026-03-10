from django.contrib import admin

from .models import Integration, Webhook, WebhookDelivery


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("url", "form", "is_active", "failure_count", "created_at")
    list_filter = ("is_active",)
    search_fields = ("url", "form__title")
    readonly_fields = ("id", "failure_count", "last_triggered_at", "created_at", "updated_at")


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ("webhook", "event_type", "response_status", "success", "created_at")
    list_filter = ("success", "event_type")
    readonly_fields = ("id", "created_at")


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "form", "is_active", "last_synced_at")
    list_filter = ("provider", "is_active")
    search_fields = ("name", "form__title")
    readonly_fields = ("id", "last_synced_at", "created_at", "updated_at")
