import csv
import io
import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from .models import FileUpload, Submission
from .serializers import (
    FileUploadSerializer,
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
)
from .tasks import send_webhook_notifications, send_submission_notification_email

logger = logging.getLogger(__name__)


class SubmissionViewSet(viewsets.ModelViewSet):
    """CRUD operations for form submissions."""

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["form", "status"]
    ordering_fields = ["created_at"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        if self.action == "list":
            return SubmissionListSerializer
        return SubmissionDetailSerializer

    def get_queryset(self):
        if self.action == "create":
            return Submission.objects.all()
        return (
            Submission.objects.filter(form__created_by=self.request.user)
            .select_related("form", "respondent")
            .prefetch_related("answers__field", "answers__file_upload")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        # Trigger async tasks
        send_webhook_notifications.delay(str(submission.id))
        send_submission_notification_email.delay(str(submission.id))

        detail_serializer = SubmissionDetailSerializer(submission)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Export submissions as CSV for a given form."""
        form_id = request.query_params.get("form")
        if not form_id:
            return Response(
                {"error": "form query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submissions = (
            Submission.objects.filter(
                form_id=form_id, form__created_by=request.user
            )
            .prefetch_related("answers__field")
            .order_by("created_at")
        )

        if not submissions.exists():
            return Response(
                {"error": "No submissions found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Collect all field labels in order
        first_submission = submissions.first()
        fields = first_submission.form.fields.all().order_by("page", "order")
        field_labels = [f.label for f in fields]
        field_ids = [str(f.id) for f in fields]

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow(
            ["Submission ID", "Submitted At", "IP Address", "Duration (s)"]
            + field_labels
        )

        for submission in submissions:
            answer_map = {
                str(a.field_id): a.value for a in submission.answers.all()
            }
            row = [
                str(submission.id),
                submission.created_at.isoformat(),
                submission.ip_address or "",
                submission.duration_seconds or "",
            ]
            for fid in field_ids:
                row.append(answer_map.get(fid, ""))
            writer.writerow(row)

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="submissions_{form_id}.csv"'
        return response

    @action(detail=True, methods=["post"], url_path="mark-spam")
    def mark_spam(self, request, pk=None):
        """Mark a submission as spam."""
        submission = self.get_object()
        submission.status = Submission.Status.SPAM
        submission.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "status": submission.status})


class FileUploadView(viewsets.GenericViewSet):
    """Handle file uploads for form submissions."""

    serializer_class = FileUploadSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        form_id = request.data.get("form_id")

        if not file:
            return Response(
                {"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not form_id:
            return Response(
                {"error": "form_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        from django.conf import settings as django_settings

        if file.size > django_settings.MAX_UPLOAD_SIZE:
            return Response(
                {"error": f"File size exceeds {django_settings.MAX_UPLOAD_SIZE_MB}MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        upload = FileUpload.objects.create(
            form_id=form_id,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by_ip=ip,
        )

        serializer = self.get_serializer(upload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
