from django.contrib import admin

from .models import ConditionalRule, FieldOption, Form, FormField, FormSettings


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ("label", "field_type", "required", "order", "page")
    ordering = ("page", "order")


class FormSettingsInline(admin.StackedInline):
    model = FormSettings
    extra = 0


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "created_by", "submission_count", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "slug", "description")
    readonly_fields = ("slug", "created_at", "updated_at")
    inlines = [FormFieldInline, FormSettingsInline]


class FieldOptionInline(admin.TabularInline):
    model = FieldOption
    extra = 0


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ("label", "form", "field_type", "required", "order", "page")
    list_filter = ("field_type", "required")
    search_fields = ("label",)
    inlines = [FieldOptionInline]


@admin.register(ConditionalRule)
class ConditionalRuleAdmin(admin.ModelAdmin):
    list_display = ("field", "action", "source_field", "operator", "value")
    list_filter = ("action", "operator")
