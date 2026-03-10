"""
Tests for the forms app: Form CRUD, field management, conditional rules.
"""
import uuid

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, Workspace, WorkspaceMembership
from apps.forms.models import (
    ConditionalRule,
    FieldOption,
    Form,
    FormField,
    FormSettings,
)
from apps.forms.services import duplicate_form, evaluate_condition


class FormModelTests(TestCase):
    """Unit tests for the Form model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="builder@formcraft.io", password="TestPass123!"
        )

    def test_create_form_generates_slug(self):
        form = Form.objects.create(
            created_by=self.user, title="Customer Feedback"
        )
        self.assertTrue(form.slug.startswith("customer-feedback-"))
        self.assertEqual(len(form.slug.split("-")[-1]), 8)

    def test_is_accepting_responses_draft(self):
        form = Form.objects.create(
            created_by=self.user, title="Draft Form", status=Form.Status.DRAFT
        )
        self.assertFalse(form.is_accepting_responses)

    def test_is_accepting_responses_published(self):
        form = Form.objects.create(
            created_by=self.user, title="Live Form", status=Form.Status.PUBLISHED
        )
        self.assertTrue(form.is_accepting_responses)

    def test_max_submissions_limit(self):
        form = Form.objects.create(
            created_by=self.user,
            title="Limited Form",
            status=Form.Status.PUBLISHED,
            max_submissions=0,
        )
        self.assertFalse(form.is_accepting_responses)

    def test_submission_count_property(self):
        form = Form.objects.create(
            created_by=self.user, title="Count Test", status=Form.Status.PUBLISHED
        )
        self.assertEqual(form.submission_count, 0)


class FormFieldModelTests(TestCase):
    """Unit tests for FormField and FieldOption models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="fieldtest@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(created_by=self.user, title="Field Test Form")

    def test_create_text_field(self):
        field = FormField.objects.create(
            form=self.form,
            field_type=FormField.FieldType.TEXT,
            label="Full Name",
            required=True,
            order=1,
        )
        self.assertEqual(str(field), "Field Test Form - Full Name")

    def test_create_select_with_options(self):
        field = FormField.objects.create(
            form=self.form,
            field_type=FormField.FieldType.SELECT,
            label="Country",
            order=2,
        )
        FieldOption.objects.create(field=field, label="USA", value="us", order=0)
        FieldOption.objects.create(field=field, label="Canada", value="ca", order=1)
        FieldOption.objects.create(field=field, label="UK", value="uk", order=2)
        self.assertEqual(field.options.count(), 3)

    def test_field_ordering(self):
        FormField.objects.create(
            form=self.form, field_type="text", label="Second", order=2, page=1
        )
        FormField.objects.create(
            form=self.form, field_type="text", label="First", order=1, page=1
        )
        fields = list(self.form.fields.all())
        self.assertEqual(fields[0].label, "First")
        self.assertEqual(fields[1].label, "Second")


class DuplicateFormServiceTests(TestCase):
    """Tests for the form duplication service."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="dup@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user,
            title="Original Form",
            primary_color="#FF0000",
        )
        FormSettings.objects.create(
            form=self.form, notification_emails="admin@test.com"
        )
        self.field1 = FormField.objects.create(
            form=self.form, field_type="text", label="Name", order=1, required=True
        )
        self.field2 = FormField.objects.create(
            form=self.form, field_type="email", label="Email", order=2
        )
        FieldOption.objects.create(
            field=self.field1, label="Opt1", value="opt1", order=0
        )

    def test_duplicate_creates_new_form(self):
        new_form = duplicate_form(self.form, self.user)
        self.assertNotEqual(new_form.id, self.form.id)
        self.assertEqual(new_form.title, "Original Form (Copy)")
        self.assertEqual(new_form.status, Form.Status.DRAFT)
        self.assertEqual(new_form.primary_color, "#FF0000")

    def test_duplicate_copies_fields(self):
        new_form = duplicate_form(self.form, self.user)
        self.assertEqual(new_form.fields.count(), 2)
        labels = set(new_form.fields.values_list("label", flat=True))
        self.assertIn("Name", labels)
        self.assertIn("Email", labels)

    def test_duplicate_copies_settings(self):
        new_form = duplicate_form(self.form, self.user)
        self.assertTrue(hasattr(new_form, "settings"))
        self.assertEqual(new_form.settings.notification_emails, "admin@test.com")

    def test_duplicate_copies_options(self):
        new_form = duplicate_form(self.form, self.user)
        name_field = new_form.fields.get(label="Name")
        self.assertEqual(name_field.options.count(), 1)


class EvaluateConditionTests(TestCase):
    """Tests for the condition evaluation logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cond@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(created_by=self.user, title="Condition Form")
        self.source = FormField.objects.create(
            form=self.form, field_type="text", label="Source", order=1
        )
        self.target = FormField.objects.create(
            form=self.form, field_type="text", label="Target", order=2
        )

    def _make_rule(self, operator, value=""):
        return ConditionalRule.objects.create(
            field=self.target,
            source_field=self.source,
            operator=operator,
            value=value,
        )

    def test_equals(self):
        rule = self._make_rule(ConditionalRule.Operator.EQUALS, "yes")
        self.assertTrue(evaluate_condition(rule, "Yes"))
        self.assertFalse(evaluate_condition(rule, "No"))

    def test_not_equals(self):
        rule = self._make_rule(ConditionalRule.Operator.NOT_EQUALS, "yes")
        self.assertTrue(evaluate_condition(rule, "No"))
        self.assertFalse(evaluate_condition(rule, "yes"))

    def test_contains(self):
        rule = self._make_rule(ConditionalRule.Operator.CONTAINS, "hello")
        self.assertTrue(evaluate_condition(rule, "say hello world"))
        self.assertFalse(evaluate_condition(rule, "goodbye"))

    def test_greater_than(self):
        rule = self._make_rule(ConditionalRule.Operator.GREATER_THAN, "10")
        self.assertTrue(evaluate_condition(rule, "15"))
        self.assertFalse(evaluate_condition(rule, "5"))

    def test_is_empty(self):
        rule = self._make_rule(ConditionalRule.Operator.IS_EMPTY)
        self.assertTrue(evaluate_condition(rule, ""))
        self.assertFalse(evaluate_condition(rule, "something"))

    def test_is_not_empty(self):
        rule = self._make_rule(ConditionalRule.Operator.IS_NOT_EMPTY)
        self.assertTrue(evaluate_condition(rule, "something"))
        self.assertFalse(evaluate_condition(rule, ""))


class FormAPITests(TestCase):
    """Integration tests for form API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="api@formcraft.io", password="TestPass123!"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_form(self):
        response = self.client.post(
            "/api/forms/",
            {"title": "New Survey", "description": "A test survey"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Survey")

    def test_list_forms(self):
        Form.objects.create(created_by=self.user, title="Form A")
        Form.objects.create(created_by=self.user, title="Form B")
        response = self.client.get("/api/forms/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_publish_form_without_fields(self):
        form = Form.objects.create(created_by=self.user, title="Empty Form")
        response = self.client.post(f"/api/forms/{form.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_publish_form_with_fields(self):
        form = Form.objects.create(created_by=self.user, title="Ready Form")
        FormField.objects.create(
            form=form, field_type="text", label="Name", order=1
        )
        response = self.client.post(f"/api/forms/{form.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.status, Form.Status.PUBLISHED)

    def test_close_form(self):
        form = Form.objects.create(
            created_by=self.user, title="To Close", status=Form.Status.PUBLISHED
        )
        response = self.client.post(f"/api/forms/{form.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.status, Form.Status.CLOSED)

    def test_duplicate_form(self):
        form = Form.objects.create(created_by=self.user, title="To Duplicate")
        FormField.objects.create(
            form=form, field_type="email", label="Email", order=1
        )
        response = self.client.post(f"/api/forms/{form.id}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("(Copy)", response.data["title"])

    def test_unauthenticated_cannot_create(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/forms/", {"title": "Should Fail"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
