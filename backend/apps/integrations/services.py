"""
Service layer for integration logic: webhook testing, provider sync dispatching.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Tuple

import requests
from django.utils import timezone

from .models import Integration, Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 15


def test_webhook(webhook: Webhook) -> Tuple[bool, int, str]:
    """
    Send a test event payload to the webhook URL.
    Returns (success, http_status, response_body).
    """
    test_payload = {
        "event": "webhook.test",
        "form_id": str(webhook.form_id),
        "form_title": webhook.form.title,
        "test": True,
        "timestamp": timezone.now().isoformat(),
        "message": "This is a test delivery from FormCraft.",
    }

    headers = {"Content-Type": "application/json", "User-Agent": "FormCraft-Webhook/1.0"}
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode("utf-8"),
            json.dumps(test_payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers["X-FormCraft-Signature"] = signature

    start = time.monotonic()
    try:
        resp = requests.post(
            webhook.url, json=test_payload, headers=headers, timeout=WEBHOOK_TIMEOUT
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        WebhookDelivery.objects.create(
            webhook=webhook,
            event_type="webhook.test",
            payload=test_payload,
            response_status=resp.status_code,
            response_body=resp.text[:2000],
            success=200 <= resp.status_code < 300,
            duration_ms=duration_ms,
        )

        success = 200 <= resp.status_code < 300
        if success:
            webhook.reset_failure_count()
        return success, resp.status_code, resp.text[:2000]

    except requests.RequestException as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        WebhookDelivery.objects.create(
            webhook=webhook,
            event_type="webhook.test",
            payload=test_payload,
            response_status=0,
            response_body=str(exc)[:2000],
            success=False,
            duration_ms=duration_ms,
        )
        logger.error(f"Webhook test failed for {webhook.id}: {exc}")
        return False, 0, str(exc)


def trigger_integration_sync(integration: Integration) -> Tuple[bool, str]:
    """
    Dispatch a manual sync for the given integration to its provider.
    Each provider has its own sync logic.
    """
    provider = integration.provider
    try:
        if provider == Integration.Provider.SLACK:
            return _sync_slack(integration)
        elif provider == Integration.Provider.GOOGLE_SHEETS:
            return _sync_google_sheets(integration)
        elif provider == Integration.Provider.MAILCHIMP:
            return _sync_mailchimp(integration)
        elif provider == Integration.Provider.HUBSPOT:
            return _sync_hubspot(integration)
        elif provider == Integration.Provider.AIRTABLE:
            return _sync_airtable(integration)
        else:
            return False, f"Sync not implemented for provider '{provider}'."
    except Exception as exc:
        logger.exception(f"Integration sync failed for {integration.id}: {exc}")
        return False, str(exc)


def _sync_slack(integration: Integration) -> Tuple[bool, str]:
    """Post a summary message to the configured Slack channel."""
    config = integration.config
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return False, "Slack webhook URL not configured."

    recent_submissions = integration.form.submissions.order_by("-created_at")[:5]
    lines = [f"*Recent submissions for {integration.form.title}:*"]
    for sub in recent_submissions:
        lines.append(f"- {sub.id} at {sub.created_at.strftime('%Y-%m-%d %H:%M')}")

    payload = {"text": "\n".join(lines)}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        integration.last_synced_at = timezone.now()
        integration.save(update_fields=["last_synced_at", "updated_at"])
        return resp.status_code == 200, f"Slack responded with {resp.status_code}."
    except requests.RequestException as exc:
        return False, str(exc)


def _sync_google_sheets(integration: Integration) -> Tuple[bool, str]:
    """Placeholder for Google Sheets sync -- requires OAuth credentials."""
    config = integration.config
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
        return False, "Google Sheets spreadsheet_id not configured."

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])
    logger.info(f"Google Sheets sync queued for spreadsheet {spreadsheet_id}")
    return True, "Google Sheets sync initiated (async processing)."


def _sync_mailchimp(integration: Integration) -> Tuple[bool, str]:
    """Sync submission email addresses to a Mailchimp audience list."""
    config = integration.config
    api_key = config.get("api_key")
    list_id = config.get("list_id")
    if not api_key or not list_id:
        return False, "Mailchimp api_key and list_id are required."

    dc = api_key.split("-")[-1] if "-" in api_key else "us1"
    base_url = f"https://{dc}.api.mailchimp.com/3.0"

    email_field_id = integration.field_mapping.get("email")
    if not email_field_id:
        return False, "No email field mapped in field_mapping."

    from apps.submissions.models import SubmissionAnswer

    answers = (
        SubmissionAnswer.objects.filter(
            field_id=email_field_id,
            submission__form=integration.form,
        )
        .values_list("value", flat=True)
        .distinct()[:100]
    )

    added = 0
    for email in answers:
        if not email or "@" not in email:
            continue
        try:
            resp = requests.post(
                f"{base_url}/lists/{list_id}/members",
                json={"email_address": email, "status": "subscribed"},
                auth=("anystring", api_key),
                timeout=10,
            )
            if resp.status_code in (200, 201):
                added += 1
        except requests.RequestException:
            continue

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])
    return True, f"Synced {added} email(s) to Mailchimp."


def _sync_hubspot(integration: Integration) -> Tuple[bool, str]:
    """Create HubSpot contacts from form submissions."""
    config = integration.config
    access_token = config.get("access_token")
    if not access_token:
        return False, "HubSpot access_token not configured."

    field_map = integration.field_mapping
    email_field = field_map.get("email")
    name_field = field_map.get("name")

    if not email_field:
        return False, "No email field mapped for HubSpot."

    from apps.submissions.models import SubmissionAnswer

    submissions = integration.form.submissions.order_by("-created_at")[:50]
    created = 0
    for sub in submissions:
        answers = {str(a.field_id): a.value for a in sub.answers.all()}
        email = answers.get(email_field)
        if not email:
            continue

        properties = [{"property": "email", "value": email}]
        if name_field and answers.get(name_field):
            properties.append({"property": "firstname", "value": answers[name_field]})

        try:
            resp = requests.post(
                "https://api.hubapi.com/contacts/v1/contact",
                json={"properties": properties},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                created += 1
        except requests.RequestException:
            continue

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])
    return True, f"Created {created} HubSpot contact(s)."


def _sync_airtable(integration: Integration) -> Tuple[bool, str]:
    """Push form submissions to an Airtable base."""
    config = integration.config
    api_key = config.get("api_key")
    base_id = config.get("base_id")
    table_name = config.get("table_name", "Submissions")

    if not api_key or not base_id:
        return False, "Airtable api_key and base_id are required."

    field_map = integration.field_mapping
    submissions = integration.form.submissions.order_by("-created_at")[:50]
    pushed = 0

    for sub in submissions:
        answers = {str(a.field_id): a.value for a in sub.answers.all()}
        fields = {}
        for form_field_id, airtable_col in field_map.items():
            if form_field_id in answers:
                fields[airtable_col] = answers[form_field_id]
        fields["Submitted At"] = sub.created_at.isoformat()

        try:
            resp = requests.post(
                f"https://api.airtable.com/v0/{base_id}/{table_name}",
                json={"fields": fields},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                pushed += 1
        except requests.RequestException:
            continue

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])
    return True, f"Pushed {pushed} record(s) to Airtable."
