import uuid

from django.conf import settings
from django.db import models


class Submission(models.Model):
    """A single completed submission of a form."""

    class Status(models.TextChoices):
        COMPLETE = "complete", "Complete"
        PARTIAL = "partial", "Partial"
        SPAM = "spam", "Spam"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="submissions"
    )
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.COMPLETE
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    referrer = models.URLField(blank=True, default="")
    duration_seconds = models.IntegerField(
        null=True, blank=True, help_text="Time taken to complete the form in seconds"
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Submission {self.id} for {self.form.title}"


class SubmissionAnswer(models.Model):
    """An individual answer to a form field within a submission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="answers"
    )
    field = models.ForeignKey(
        "forms.FormField", on_delete=models.CASCADE, related_name="answers"
    )
    value = models.TextField(blank=True, default="")
    file_upload = models.ForeignKey(
        "FileUpload",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="answers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["field__order"]

    def __str__(self):
        return f"{self.field.label}: {self.value[:50]}"


class FileUpload(models.Model):
    """Uploaded file associated with a form submission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="file_uploads"
    )
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="file_uploads",
    )
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    original_filename = models.CharField(max_length=500)
    file_size = models.IntegerField(help_text="File size in bytes")
    content_type = models.CharField(max_length=200)
    uploaded_by_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_filename
