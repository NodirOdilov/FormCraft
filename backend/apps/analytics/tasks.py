"""
Celery periodic tasks for analytics snapshot generation.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.forms.models import Form

from .services import generate_daily_snapshot

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_all_daily_snapshots(self):
    """
    Generate yesterday's analytics snapshot for every published or closed form.
    Intended to be run once per day via Celery Beat.
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    forms = Form.objects.filter(
        status__in=[Form.Status.PUBLISHED, Form.Status.CLOSED]
    )

    success_count = 0
    error_count = 0

    for form in forms.iterator():
        try:
            generate_daily_snapshot(form, snapshot_date=yesterday)
            success_count += 1
        except Exception as exc:
            logger.error(
                f"Failed to generate snapshot for form {form.id}: {exc}",
                exc_info=True,
            )
            error_count += 1

    logger.info(
        f"Daily snapshots complete: {success_count} succeeded, {error_count} failed "
        f"for date {yesterday}"
    )
    return {"success": success_count, "errors": error_count, "date": str(yesterday)}


@shared_task(bind=True, max_retries=1)
def generate_single_form_snapshot(self, form_id: str, date_str: str = None):
    """
    Generate a snapshot for a single form. Can be triggered manually
    for backfilling historical data.
    """
    from datetime import date as date_type

    try:
        form = Form.objects.get(id=form_id)
    except Form.DoesNotExist:
        logger.error(f"Form {form_id} not found for snapshot generation")
        return

    if date_str:
        snapshot_date = date_type.fromisoformat(date_str)
    else:
        snapshot_date = timezone.now().date() - timedelta(days=1)

    snapshot = generate_daily_snapshot(form, snapshot_date=snapshot_date)
    logger.info(f"Snapshot generated for form {form_id} on {snapshot.date}")
    return {"form_id": form_id, "date": str(snapshot.date)}
