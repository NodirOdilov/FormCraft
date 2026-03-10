from rest_framework import serializers

from apps.forms.models import Form, FormField
from .models import FileUpload, Submission, SubmissionAnswer


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ("id", "file", "original_filename", "file_size", "content_type", "created_at")
        read_only_fields = ("id", "file_size", "content_type", "created_at")


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)
    file_upload = FileUploadSerializer(read_only=True)

    class Meta:
        model = SubmissionAnswer
        fields = ("id", "field", "field_label", "field_type", "value", "file_upload", "created_at")
        read_only_fields = ("id", "created_at")


class SubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing submissions."""

    respondent_email = serializers.CharField(
        source="respondent.email", read_only=True, default=None
    )
    answer_count = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = (
            "id",
            "form",
            "respondent_email",
            "status",
            "ip_address",
            "duration_seconds",
            "answer_count",
            "created_at",
        )

    def get_answer_count(self, obj):
        return obj.answers.count()


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Full serializer with all answers."""

    answers = SubmissionAnswerSerializer(many=True, read_only=True)
    respondent_email = serializers.CharField(
        source="respondent.email", read_only=True, default=None
    )
    form_title = serializers.CharField(source="form.title", read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id",
            "form",
            "form_title",
            "respondent_email",
            "status",
            "ip_address",
            "user_agent",
            "referrer",
            "duration_seconds",
            "metadata",
            "answers",
            "created_at",
            "updated_at",
        )


class SubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new submission (public endpoint)."""

    form_id = serializers.UUIDField()
    answers = serializers.ListField(child=serializers.DictField())
    duration_seconds = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, default=dict)

    def validate_form_id(self, value):
        try:
            form = Form.objects.get(id=value, status=Form.Status.PUBLISHED)
        except Form.DoesNotExist:
            raise serializers.ValidationError("Form not found or not published.")
        if not form.is_accepting_responses:
            raise serializers.ValidationError("This form is no longer accepting responses.")
        return value

    def validate_answers(self, value):
        for answer in value:
            if "field_id" not in answer:
                raise serializers.ValidationError("Each answer must include a 'field_id'.")
            if "value" not in answer:
                raise serializers.ValidationError("Each answer must include a 'value'.")
        return value

    def create(self, validated_data):
        form = Form.objects.get(id=validated_data["form_id"])
        request = self.context.get("request")

        # Get client IP
        ip_address = None
        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")

        user_agent = ""
        referrer = ""
        if request:
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            referrer = request.META.get("HTTP_REFERER", "")

        respondent = None
        if request and request.user and request.user.is_authenticated:
            respondent = request.user

        submission = Submission.objects.create(
            form=form,
            respondent=respondent,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            duration_seconds=validated_data.get("duration_seconds"),
            metadata=validated_data.get("metadata", {}),
        )

        # Validate required fields
        required_fields = set(
            form.fields.filter(required=True).values_list("id", flat=True)
        )
        answer_field_ids = {a["field_id"] for a in validated_data["answers"]}

        # Check that all required fields have answers
        missing = required_fields - answer_field_ids
        if missing:
            field_labels = FormField.objects.filter(id__in=missing).values_list(
                "label", flat=True
            )
            raise serializers.ValidationError(
                f"Missing required fields: {', '.join(field_labels)}"
            )

        # Create answers
        for answer_data in validated_data["answers"]:
            try:
                field = FormField.objects.get(
                    id=answer_data["field_id"], form=form
                )
            except FormField.DoesNotExist:
                continue

            file_upload = None
            if answer_data.get("file_upload_id"):
                try:
                    file_upload = FileUpload.objects.get(id=answer_data["file_upload_id"])
                    file_upload.submission = submission
                    file_upload.save(update_fields=["submission"])
                except FileUpload.DoesNotExist:
                    pass

            SubmissionAnswer.objects.create(
                submission=submission,
                field=field,
                value=str(answer_data.get("value", "")),
                file_upload=file_upload,
            )

        return submission
