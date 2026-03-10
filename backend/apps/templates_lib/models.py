import uuid

from django.db import models


class TemplateCategory(models.Model):
    """Category for organizing form templates."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=50, blank=True, default="", help_text="Icon class name")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Template categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class FormTemplate(models.Model):
    """Pre-built form template that users can clone."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        TemplateCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="templates",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    preview_image = models.ImageField(upload_to="template_previews/", null=True, blank=True)
    form_data = models.JSONField(
        help_text="Complete form structure including fields, options, and settings"
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    use_count = models.IntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True, default="", help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-use_count"]

    def __str__(self):
        return self.name
