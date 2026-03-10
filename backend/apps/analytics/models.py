import uuid

from django.db import models


class FormView(models.Model):
    """Tracks each time a published form is viewed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="views"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    referrer = models.URLField(blank=True, default="", max_length=2000)
    country = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=200, blank=True, default="")
    device_type = models.CharField(
        max_length=20,
        blank=True,
        default="desktop",
        help_text="desktop, mobile, or tablet",
    )
    browser = models.CharField(max_length=100, blank=True, default="")
    os = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["form", "created_at"]),
            models.Index(fields=["form", "device_type"]),
        ]

    def __str__(self):
        return f"View on {self.form.title} from {self.ip_address}"


class FormAnalyticsSnapshot(models.Model):
    """Daily aggregate snapshot of form analytics for fast dashboard queries."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="analytics_snapshots"
    )
    date = models.DateField()
    views_count = models.IntegerField(default=0)
    unique_views_count = models.IntegerField(default=0)
    submissions_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(
        default=0.0, help_text="submissions / unique_views * 100"
    )
    avg_duration_seconds = models.FloatField(default=0.0)
    desktop_views = models.IntegerField(default=0)
    mobile_views = models.IntegerField(default=0)
    tablet_views = models.IntegerField(default=0)
    top_referrers = models.JSONField(default=list, help_text="Top 10 referrers for the day")
    top_countries = models.JSONField(default=list, help_text="Top 10 countries for the day")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("form", "date")
        indexes = [
            models.Index(fields=["form", "date"]),
        ]

    def __str__(self):
        return f"Analytics for {self.form.title} on {self.date}"


class FieldDropoff(models.Model):
    """Tracks where users abandon forms by recording the last field interacted with."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        "forms.Form", on_delete=models.CASCADE, related_name="field_dropoffs"
    )
    field = models.ForeignKey(
        "forms.FormField", on_delete=models.CASCADE, related_name="dropoffs"
    )
    date = models.DateField()
    dropoff_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("form", "field", "date")
        ordering = ["-date", "-dropoff_count"]

    def __str__(self):
        return f"Dropoff at {self.field.label}: {self.dropoff_count}"
