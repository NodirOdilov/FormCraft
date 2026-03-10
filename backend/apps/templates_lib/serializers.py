from rest_framework import serializers

from .models import FormTemplate, TemplateCategory


class TemplateCategorySerializer(serializers.ModelSerializer):
    template_count = serializers.SerializerMethodField()

    class Meta:
        model = TemplateCategory
        fields = ("id", "name", "slug", "description", "icon", "order", "template_count")

    def get_template_count(self, obj):
        return obj.templates.filter(is_active=True).count()


class FormTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing templates."""

    category_name = serializers.CharField(source="category.name", read_only=True, default=None)

    class Meta:
        model = FormTemplate
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "preview_image",
            "category",
            "category_name",
            "is_featured",
            "use_count",
            "tags",
            "created_at",
        )


class FormTemplateDetailSerializer(serializers.ModelSerializer):
    """Full serializer including the form_data structure."""

    category = TemplateCategorySerializer(read_only=True)

    class Meta:
        model = FormTemplate
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "preview_image",
            "category",
            "form_data",
            "is_featured",
            "use_count",
            "tags",
            "created_at",
            "updated_at",
        )
