"""
Tests for the submissions app: creating, listing, exporting, spam marking.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.forms.models import Form, FormField
from apps.submissions.models import FileUpload, Submission, SubmissionAnswer


class SubmissionModelTests(TestCase):
    """Unit tests for Submission and SubmissionAnswer models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="submodel@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Feedback", status=Form.Status.PUBLISHED
        )
        self.name_field = FormField.objects.create(
            form=self.form, field_type="text", label="Name", order=1, required=True
        )
        self.email_field = FormField.objects.create(
            form=self.form, field_type="email", label="Email", order=2
        )

    def test_create_submission(self):
        sub = Submission.objects.create(
            form=self.form, ip_address="192.168.1.1", duration_seconds=45
        )
        SubmissionAnswer.objects.create(
            submission=sub, field=self.name_field, value="Alice"
        )
        SubmissionAnswer.objects.create(
            submission=sub, field=self.email_field, value="alice@example.com"
        )
        self.assertEqual(sub.answers.count(), 2)
        self.assertEqual(sub.status, Submission.Status.COMPLETE)

    def test_submission_str(self):
        sub = Submission.objects.create(form=self.form)
        self.assertIn("Feedback", str(sub))

    def test_answer_ordering_by_field_order(self):
        sub = Submission.objects.create(form=self.form)
        a2 = SubmissionAnswer.objects.create(
            submission=sub, field=self.email_field, value="bob@example.com"
        )
        a1 = SubmissionAnswer.objects.create(
            submission=sub, field=self.name_field, value="Bob"
        )
        answers = list(sub.answers.all())
        self.assertEqual(answers[0].field.label, "Name")
        self.assertEqual(answers[1].field.label, "Email")


class SubmissionAPITests(TestCase):
    """Integration tests for submission API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="subapi@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user,
            title="Contact Us",
            status=Form.Status.PUBLISHED,
        )
        self.name_field = FormField.objects.create(
            form=self.form, field_type="text", label="Name", order=1, required=True
        )
        self.msg_field = FormField.objects.create(
            form=self.form, field_type="textarea", label="Message", order=2
        )

    def test_create_submission_public(self):
        """Anyone can submit to a published form."""
        response = self.client.post(
            "/api/submissions/",
            {
                "form_id": str(self.form.id),
                "answers": [
                    {"field_id": str(self.name_field.id), "value": "Charlie"},
                    {"field_id": str(self.msg_field.id), "value": "Hello there!"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)

    def test_create_submission_missing_required(self):
        """Submitting without a required field should fail."""
        response = self.client.post(
            "/api/submissions/",
            {
                "form_id": str(self.form.id),
                "answers": [
                    {"field_id": str(self.msg_field.id), "value": "Only message"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_submission_closed_form(self):
        """Cannot submit to a closed form."""
        self.form.status = Form.Status.CLOSED
        self.form.save()
        response = self.client.post(
            "/api/submissions/",
            {
                "form_id": str(self.form.id),
                "answers": [
                    {"field_id": str(self.name_field.id), "value": "Dave"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_submissions_authenticated(self):
        """Only form owner can list submissions."""
        Submission.objects.create(form=self.form)
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/submissions/", {"form": str(self.form.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_submissions_unauthenticated(self):
        """Anonymous users cannot list submissions."""
        response = self.client.get("/api/submissions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_submission_as_spam(self):
        sub = Submission.objects.create(form=self.form)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/submissions/{sub.id}/mark-spam/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sub.refresh_from_db()
        self.assertEqual(sub.status, Submission.Status.SPAM)

    def test_export_csv(self):
        sub = Submission.objects.create(form=self.form, ip_address="10.0.0.1")
        SubmissionAnswer.objects.create(
            submission=sub, field=self.name_field, value="Eve"
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/submissions/export/", {"form": str(self.form.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("Eve", content)
        self.assertIn("Submission ID", content)
