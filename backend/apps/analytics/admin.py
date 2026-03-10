from django.contrib import admin

from .models import FieldDropoff, FormAnalyticsSnapshot, FormView


@admin.register(FormView)
class FormViewAdmin(admin.ModelAdmin):
    list_display = ("form", "ip_address", "device_type", "browser", "country", "created_at")
    list_filter = ("device_type", "browser")
    search_fields = ("form__title", "ip_address", "country")
    readonly_fields = ("id", "created_at")
    date_hierarchy = "created_at"


@admin.register(FormAnalyticsSnapshot)
class FormAnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "date",
        "views_count",
        "submissions_count",
        "completion_rate",
        "avg_duration_seconds",
    )
    list_filter = ("date",)
    search_fields = ("form__title",)
    readonly_fields = ("id", "created_at")
    date_hierarchy = "date"


@admin.register(FieldDropoff)
class FieldDropoffAdmin(admin.ModelAdmin):
    list_display = ("form", "field", "date", "dropoff_count")
    list_filter = ("date",)
    search_fields = ("form__title", "field__label")
