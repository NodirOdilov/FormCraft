"""
Celery tasks for submission processing, webhook delivery, and notifications.
"""
import json
import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 30
WEBHOOK_MAX_RETRIES = 3


@shared_task(
    bind=True,
    max_retries=WEBHOOK_MAX_RETRIES,
    default_retry_delay=60,
    acks_late=True,
)
def send_webhook_notifications(self, submission_id: str):
    """
    Send webhook notifications to all active webhooks configured for the form
    associated with the given submission.
    """
    from .models import Submission
    from apps.integrations.models import Webhook

    try:
        submission = (
            Submission.objects.select_related("form", "respondent")
            .prefetch_related("answers__field")
            .get(id=submission_id)
        )
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found for webhook delivery")
        return

    webhooks = Webhook.objects.filter(form=submission.form, is_active=True)
    if not webhooks.exists():
        logger.debug(f"No active webhooks for form {submission.form.id}")
        return

    # Build payload
    answers_data = []
    for answer in submission.answers.select_related("field").all():
        answers_data.append(
            {
                "field_id": str(answer.field.id),
                "field_label": answer.field.label,
                "field_type": answer.field.field_type,
                "value": answer.value,
            }
        )

    payload = {
        "event": "submission.created",
        "form_id": str(submission.form.id),
        "form_title": submission.form.title,
        "submission_id": str(submission.id),
        "submitted_at": submission.created_at.isoformat(),
        "respondent_email": (
            submission.respondent.email if submission.respondent else None
        ),
        "duration_seconds": submission.duration_seconds,
        "answers": answers_data,
    }

    for webhook in webhooks:
        try:
            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                import hashlib
                import hmac

                signature = hmac.new(
                    webhook.secret.encode("utf-8"),
                    json.dumps(payload, sort_keys=True).encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-FormCraft-Signature"] = signature

            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=WEBHOOK_TIMEOUT,
            )

            # Log the delivery
            from apps.integrations.models import WebhookDelivery

            WebhookDelivery.objects.create(
                webhook=webhook,
                submission=submission,
                payload=payload,
                response_status=response.status_code,
                response_body=response.text[:2000],
                success=200 <= response.status_code < 300,
            )

            if response.status_code >= 400:
                logger.warning(
                    f"Webhook {webhook.id} returned status {response.status_code} "
                    f"for submission {submission_id}"
                )

        except requests.RequestException as exc:
            logger.error(
                f"Webhook delivery failed for webhook {webhook.id}: {exc}"
            )
            from apps.integrations.models import WebhookDelivery

            WebhookDelivery.objects.create(
                webhook=webhook,
                submission=submission,
                payload=payload,
                response_status=0,
                response_body=str(exc)[:2000],
                success=False,
            )
            # Retry on failure
            raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_submission_notification_email(self, submission_id: str):
    """
    Send email notification to form owner when a new submission is received.
    """
    from .models import Submission

    try:
        submission = (
            Submission.objects.select_related("form__created_by")
            .prefetch_related("answers__field")
            .get(id=submission_id)
        )
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found for email notification")
        return

    form = submission.form
    form_settings = getattr(form, "settings", None)

    # Determine recipients
    recipients = []
    if form_settings and form_settings.notification_emails:
        recipients = [
            e.strip()
            for e in form_settings.notification_emails.split(",")
            if e.strip()
        ]

    if not recipients:
        # Fall back to form creator
        recipients = [form.created_by.email]

    # Build email body
    answers_text = []
    for answer in submission.answers.select_related("field").all():
        answers_text.append(f"  {answer.field.label}: {answer.value}")

    body = (
        f"New submission received for '{form.title}'\n\n"
        f"Submission ID: {submission.id}\n"
        f"Submitted at: {submission.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"IP Address: {submission.ip_address or 'N/A'}\n\n"
        f"Answers:\n" + "\n".join(answers_text)
    )

    try:
        send_mail(
            subject=f"New submission: {form.title}",
            message=body,
            from_email=settings.EMAIL_HOST_USER or "noreply@formcraft.io",
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(
            f"Notification email sent for submission {submission_id} to {recipients}"
        )
    except Exception as exc:
        logger.error(f"Failed to send notification email: {exc}")
        raise self.retry(exc=exc)
