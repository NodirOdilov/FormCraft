import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Form(models.Model):
    """A user-created form with configurable fields."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        related_name="forms",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forms",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    cover_image = models.ImageField(upload_to="form_covers/", null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#4F46E5")
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    submit_button_text = models.CharField(max_length=100, default="Submit")
    success_message = models.TextField(default="Thank you for your submission!")
    redirect_url = models.URLField(blank=True, default="")
    is_multi_page = models.BooleanField(default=False)
    allow_multiple_submissions = models.BooleanField(default=True)
    requires_login = models.BooleanField(default=False)
    closes_at = models.DateTimeField(null=True, blank=True)
    max_submissions = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "form"
            slug = f"{base_slug}-{get_random_string(8)}"
            while Form.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{get_random_string(8)}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def submission_count(self):
        return self.submissions.count()

    @property
    def is_accepting_responses(self):
        if self.status != self.Status.PUBLISHED:
            return False
        if self.max_submissions and self.submission_count >= self.max_submissions:
            return False
        from django.utils import timezone

        if self.closes_at and timezone.now() > self.closes_at:
            return False
        return True


class FormField(models.Model):
    """A single field within a form."""

    class FieldType(models.TextChoices):
        TEXT = "text", "Short Text"
        TEXTAREA = "textarea", "Long Text"
        EMAIL = "email", "Email"
        NUMBER = "number", "Number"
        PHONE = "phone", "Phone"
        URL = "url", "URL"
        SELECT = "select", "Dropdown"
        MULTI_SELECT = "multi_select", "Multi Select"
        RADIO = "radio", "Radio Buttons"
        CHECKBOX = "checkbox", "Checkboxes"
        DATE = "date", "Date"
        TIME = "time", "Time"
        FILE_UPLOAD = "file_upload", "File Upload"
        RATING = "rating", "Rating"
        SCALE = "scale", "Linear Scale"
        HEADING = "heading", "Section Heading"
        PARAGRAPH = "paragraph", "Paragraph Text"
        DIVIDER = "divider", "Divider"
        HIDDEN = "hidden", "Hidden Field"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="fields")
    field_type = models.CharField(max_length=30, choices=FieldType.choices)
    label = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    placeholder = models.CharField(max_length=500, blank=True, default="")
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    page = models.IntegerField(default=1, help_text="Page number for multi-page forms")

    # Validation constraints
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    pattern = models.CharField(max_length=500, blank=True, default="", help_text="Regex pattern")

    # Field-type specific configuration stored as JSON
    config = models.JSONField(default=dict, blank=True, help_text="Type-specific config")
    default_value = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page", "order"]

    def __str__(self):
        return f"{self.form.title} - {self.label}"


class FieldOption(models.Model):
    """Option for select, radio, checkbox, and multi_select fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=500)
    value = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.field.label} - {self.label}"


class ConditionalRule(models.Model):
    """Rule for showing/hiding a field based on another field's value."""

    class Action(models.TextChoices):
        SHOW = "show", "Show"
        HIDE = "hide", "Hide"
        SKIP_TO = "skip_to", "Skip To"

    class Operator(models.TextChoices):
        EQUALS = "equals", "Equals"
        NOT_EQUALS = "not_equals", "Not Equals"
        CONTAINS = "contains", "Contains"
        NOT_CONTAINS = "not_contains", "Not Contains"
        GREATER_THAN = "greater_than", "Greater Than"
        LESS_THAN = "less_than", "Less Than"
        IS_EMPTY = "is_empty", "Is Empty"
        IS_NOT_EMPTY = "is_not_empty", "Is Not Empty"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="conditional_rules"
    )
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.SHOW)
    source_field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name="triggers_rules",
        help_text="The field whose value determines the action",
    )
    operator = models.CharField(max_length=20, choices=Operator.choices)
    value = models.TextField(blank=True, default="", help_text="Value to compare against")
    target_field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name="skip_targets",
        null=True,
        blank=True,
        help_text="Target field for skip_to action",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.action} {self.field.label} when {self.source_field.label} {self.operator} {self.value}"


class FormSettings(models.Model):
    """Extended settings for a form."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.OneToOneField(Form, on_delete=models.CASCADE, related_name="settings")
    notification_emails = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated list of emails to notify on submission",
    )
    send_confirmation_email = models.BooleanField(default=False)
    confirmation_email_subject = models.CharField(max_length=255, blank=True, default="")
    confirmation_email_body = models.TextField(blank=True, default="")
    custom_css = models.TextField(blank=True, default="")
    custom_js = models.TextField(blank=True, default="")
    meta_title = models.CharField(max_length=255, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    google_analytics_id = models.CharField(max_length=50, blank=True, default="")
    facebook_pixel_id = models.CharField(max_length=50, blank=True, default="")
    embed_allowed_domains = models.TextField(
        blank=True,
        default="*",
        help_text="Comma-separated domains allowed to embed, or * for all",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Form settings"

    def __str__(self):
        return f"Settings for {self.form.title}"
