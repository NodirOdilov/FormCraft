from django.contrib import admin

from .models import FileUpload, Submission, SubmissionAnswer


class SubmissionAnswerInline(admin.TabularInline):
    model = SubmissionAnswer
    extra = 0
    readonly_fields = ("id", "field", "value", "file_upload", "created_at")
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "form", "respondent", "status", "ip_address", "duration_seconds", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("form__title", "respondent__email", "ip_address")
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [SubmissionAnswerInline]


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "form", "file_size", "content_type", "created_at")
    list_filter = ("content_type",)
    search_fields = ("original_filename", "form__title")
    readonly_fields = ("id", "created_at")
