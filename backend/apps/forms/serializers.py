from rest_framework import serializers

from .models import ConditionalRule, FieldOption, Form, FormField, FormSettings


class FieldOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldOption
        fields = ("id", "label", "value", "order", "is_default")
        read_only_fields = ("id",)


class ConditionalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionalRule
        fields = (
            "id",
            "field",
            "action",
            "source_field",
            "operator",
            "value",
            "target_field",
        )
        read_only_fields = ("id",)


class FormFieldSerializer(serializers.ModelSerializer):
    options = FieldOptionSerializer(many=True, required=False)
    conditional_rules = ConditionalRuleSerializer(many=True, read_only=True)

    class Meta:
        model = FormField
        fields = (
            "id",
            "form",
            "field_type",
            "label",
            "description",
            "placeholder",
            "required",
            "order",
            "page",
            "min_length",
            "max_length",
            "min_value",
            "max_value",
            "pattern",
            "config",
            "default_value",
            "options",
            "conditional_rules",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        field = FormField.objects.create(**validated_data)
        for option_data in options_data:
            FieldOption.objects.create(field=field, **option_data)
        return field

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            # Replace all options
            instance.options.all().delete()
            for option_data in options_data:
                FieldOption.objects.create(field=instance, **option_data)

        return instance


class FormSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSettings
        fields = (
            "id",
            "notification_emails",
            "send_confirmation_email",
            "confirmation_email_subject",
            "confirmation_email_body",
            "custom_css",
            "custom_js",
            "meta_title",
            "meta_description",
            "google_analytics_id",
            "facebook_pixel_id",
            "embed_allowed_domains",
        )
        read_only_fields = ("id",)


class FormListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing forms."""

    submission_count = serializers.ReadOnlyField()
    is_accepting_responses = serializers.ReadOnlyField()
    field_count = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = (
            "id",
            "title",
            "slug",
            "status",
            "submission_count",
            "is_accepting_responses",
            "field_count",
            "created_at",
            "updated_at",
        )

    def get_field_count(self, obj):
        return obj.fields.count()


class FormDetailSerializer(serializers.ModelSerializer):
    """Full serializer for form detail including all fields and settings."""

    fields_data = FormFieldSerializer(source="fields", many=True, read_only=True)
    settings = FormSettingsSerializer(read_only=True)
    submission_count = serializers.ReadOnlyField()
    is_accepting_responses = serializers.ReadOnlyField()
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Form
        fields = (
            "id",
            "workspace",
            "created_by_email",
            "title",
            "slug",
            "description",
            "status",
            "cover_image",
            "primary_color",
            "background_color",
            "submit_button_text",
            "success_message",
            "redirect_url",
            "is_multi_page",
            "allow_multiple_submissions",
            "requires_login",
            "closes_at",
            "max_submissions",
            "submission_count",
            "is_accepting_responses",
            "fields_data",
            "settings",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class FormCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating forms."""

    class Meta:
        model = Form
        fields = (
            "title",
            "description",
            "workspace",
            "status",
            "cover_image",
            "primary_color",
            "background_color",
            "submit_button_text",
            "success_message",
            "redirect_url",
            "is_multi_page",
            "allow_multiple_submissions",
            "requires_login",
            "closes_at",
            "max_submissions",
        )

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        form = Form.objects.create(**validated_data)
        FormSettings.objects.create(form=form)
        return form


class PublicFormSerializer(serializers.ModelSerializer):
    """Serializer for rendering a published form publicly."""

    fields_data = FormFieldSerializer(source="fields", many=True, read_only=True)
    settings = FormSettingsSerializer(read_only=True)

    class Meta:
        model = Form
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "cover_image",
            "primary_color",
            "background_color",
            "submit_button_text",
            "success_message",
            "redirect_url",
            "is_multi_page",
            "fields_data",
            "settings",
        )


class FormBulkFieldUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating form field order and pages."""

    fields = serializers.ListField(child=serializers.DictField())

    def validate_fields(self, value):
        for item in value:
            if "id" not in item:
                raise serializers.ValidationError("Each field must have an 'id'.")
            if "order" not in item:
                raise serializers.ValidationError("Each field must have an 'order'.")
        return value
