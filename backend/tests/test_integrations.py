"""
Tests for the integrations app: webhooks, third-party integrations.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.forms.models import Form, FormField
from apps.integrations.models import Integration, Webhook, WebhookDelivery
from apps.integrations.services import test_webhook


class WebhookModelTests(TestCase):
    """Unit tests for the Webhook model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="whmodel@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Webhook Form", status=Form.Status.PUBLISHED
        )
        self.webhook = Webhook.objects.create(
            form=self.form,
            created_by=self.user,
            url="https://hooks.example.com/endpoint",
            events=["submission.created"],
        )

    def test_webhook_str(self):
        self.assertIn("hooks.example.com", str(self.webhook))

    def test_increment_failure(self):
        for _ in range(9):
            self.webhook.increment_failure()
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.failure_count, 9)
        self.assertTrue(self.webhook.is_active)

        self.webhook.increment_failure()
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.failure_count, 10)
        self.assertFalse(self.webhook.is_active)

    def test_reset_failure_count(self):
        self.webhook.failure_count = 5
        self.webhook.save()
        self.webhook.reset_failure_count()
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.failure_count, 0)


class WebhookServiceTests(TestCase):
    """Tests for the webhook test delivery service."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="whservice@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Service Test Form"
        )
        self.webhook = Webhook.objects.create(
            form=self.form,
            created_by=self.user,
            url="https://hooks.example.com/test",
            secret="test-secret-key",
        )

    @patch("apps.integrations.services.requests.post")
    def test_successful_test_delivery(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"received": true}'
        mock_post.return_value = mock_response

        success, status_code, body = test_webhook(self.webhook)
        self.assertTrue(success)
        self.assertEqual(status_code, 200)
        self.assertEqual(WebhookDelivery.objects.count(), 1)

        delivery = WebhookDelivery.objects.first()
        self.assertTrue(delivery.success)
        self.assertEqual(delivery.event_type, "webhook.test")

    @patch("apps.integrations.services.requests.post")
    def test_failed_test_delivery(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        success, status_code, body = test_webhook(self.webhook)
        self.assertFalse(success)
        self.assertEqual(status_code, 500)


class IntegrationModelTests(TestCase):
    """Unit tests for the Integration model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="intmodel@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Integration Form"
        )

    def test_create_slack_integration(self):
        integration = Integration.objects.create(
            form=self.form,
            created_by=self.user,
            provider=Integration.Provider.SLACK,
            name="Dev Channel Notifications",
            config={"webhook_url": "https://hooks.slack.com/services/T00/B00/xxx"},
        )
        self.assertEqual(str(integration), "Slack - Dev Channel Notifications")

    def test_create_integration_with_field_mapping(self):
        field = FormField.objects.create(
            form=self.form, field_type="email", label="Email", order=1
        )
        integration = Integration.objects.create(
            form=self.form,
            created_by=self.user,
            provider=Integration.Provider.MAILCHIMP,
            name="Newsletter Sync",
            config={"api_key": "key-us1", "list_id": "abc123"},
            field_mapping={"email": str(field.id)},
        )
        self.assertEqual(integration.field_mapping["email"], str(field.id))


class WebhookAPITests(TestCase):
    """Integration tests for webhook API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="whapi@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="API Webhook Form"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_webhook(self):
        response = self.client.post(
            "/api/integrations/webhooks/",
            {
                "form": str(self.form.id),
                "url": "https://api.example.com/hook",
                "events": ["submission.created"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Webhook.objects.count(), 1)

    def test_list_webhooks(self):
        Webhook.objects.create(
            form=self.form,
            created_by=self.user,
            url="https://hooks.example.com/1",
        )
        response = self.client.get("/api/integrations/webhooks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_failures(self):
        wh = Webhook.objects.create(
            form=self.form,
            created_by=self.user,
            url="https://hooks.example.com/2",
            failure_count=8,
        )
        response = self.client.post(
            f"/api/integrations/webhooks/{wh.id}/reset-failures/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wh.refresh_from_db()
        self.assertEqual(wh.failure_count, 0)
        self.assertTrue(wh.is_active)
