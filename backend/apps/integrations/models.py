import uuid

from django.conf import settings
from django.db import models


class Webhook(models.Model):
    """Webhook endpoint that receives POST notifications on form submission."""

    class EventType(models.TextChoices):
        SUBMISSION_CREATED = "submission.created", "Submission Created"
        SUBMISSION_UPDATED = "submission.updated", "Submission Updated"
        FORM_PUBLISHED = "form.published", "Form Published"
        FORM_CLOSED = "form.closed", "Form Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="webhooks"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webhooks",
    )
    url = models.URLField(max_length=2000, help_text="Endpoint URL to POST events to")
    secret = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="HMAC secret for request signing",
    )
    events = models.JSONField(
        default=list,
        help_text="List of event types this webhook subscribes to",
    )
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=500, blank=True, default="")
    failure_count = models.IntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Webhook {self.url} for {self.form.title}"

    def increment_failure(self):
        self.failure_count += 1
        if self.failure_count >= 10:
            self.is_active = False
        self.save(update_fields=["failure_count", "is_active", "updated_at"])

    def reset_failure_count(self):
        if self.failure_count > 0:
            self.failure_count = 0
            self.save(update_fields=["failure_count", "updated_at"])


class WebhookDelivery(models.Model):
    """Log of each webhook delivery attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(
        Webhook, on_delete=models.CASCADE, related_name="deliveries"
    )
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="webhook_deliveries",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=50, default="submission.created")
    payload = models.JSONField(default=dict)
    response_status = models.IntegerField(default=0)
    response_body = models.TextField(blank=True, default="")
    success = models.BooleanField(default=False)
    duration_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status_label = "OK" if self.success else "FAILED"
        return f"Delivery {status_label} -> {self.webhook.url}"


class Integration(models.Model):
    """Third-party integration configuration (Slack, Zapier, Google Sheets, etc.)."""

    class Provider(models.TextChoices):
        SLACK = "slack", "Slack"
        ZAPIER = "zapier", "Zapier"
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        MAILCHIMP = "mailchimp", "Mailchimp"
        HUBSPOT = "hubspot", "HubSpot"
        AIRTABLE = "airtable", "Airtable"
        NOTION = "notion", "Notion"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="integrations"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    provider = models.CharField(max_length=30, choices=Provider.choices)
    name = models.CharField(max_length=255, help_text="User-friendly label")
    config = models.JSONField(
        default=dict,
        help_text="Provider-specific configuration (API keys, channel IDs, etc.)",
    )
    field_mapping = models.JSONField(
        default=dict,
        help_text="Mapping of form field IDs to provider-specific field names",
    )
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_provider_display()} - {self.name}"
