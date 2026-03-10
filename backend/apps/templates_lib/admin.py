from django.contrib import admin

from .models import FormTemplate, TemplateCategory


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_featured", "is_active", "use_count", "created_at")
    list_filter = ("is_featured", "is_active", "category")
    search_fields = ("name", "description", "tags")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "use_count", "created_at", "updated_at")
