"""
Analytics computation services: snapshot generation, aggregation queries.
"""
import logging
from collections import Counter
from datetime import date, timedelta
from typing import Any, Dict, Optional

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.forms.models import Form
from apps.submissions.models import Submission

from .models import FieldDropoff, FormAnalyticsSnapshot, FormView

logger = logging.getLogger(__name__)


def generate_daily_snapshot(form: Form, snapshot_date: Optional[date] = None) -> FormAnalyticsSnapshot:
    """
    Generate or update the analytics snapshot for a form on a given date.
    Aggregates views, submissions, device breakdown, referrers, and countries.
    """
    if snapshot_date is None:
        snapshot_date = timezone.now().date() - timedelta(days=1)

    day_start = timezone.make_aware(
        timezone.datetime.combine(snapshot_date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    views_qs = FormView.objects.filter(
        form=form, created_at__gte=day_start, created_at__lt=day_end
    )
    submissions_qs = Submission.objects.filter(
        form=form, created_at__gte=day_start, created_at__lt=day_end
    )

    total_views = views_qs.count()
    unique_views = views_qs.values("ip_address").distinct().count()
    total_submissions = submissions_qs.count()

    completion_rate = 0.0
    if unique_views > 0:
        completion_rate = round((total_submissions / unique_views) * 100, 2)

    avg_duration = submissions_qs.aggregate(avg=Avg("duration_seconds"))["avg"] or 0.0

    device_counts = views_qs.values("device_type").annotate(count=Count("id"))
    desktop = 0
    mobile = 0
    tablet = 0
    for entry in device_counts:
        if entry["device_type"] == "desktop":
            desktop = entry["count"]
        elif entry["device_type"] == "mobile":
            mobile = entry["count"]
        elif entry["device_type"] == "tablet":
            tablet = entry["count"]

    # Top referrers
    referrer_counts = (
        views_qs.exclude(referrer="")
        .values("referrer")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    top_referrers = [{"referrer": r["referrer"], "count": r["count"]} for r in referrer_counts]

    # Top countries
    country_counts = (
        views_qs.exclude(country="")
        .values("country")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    top_countries = [{"country": c["country"], "count": c["count"]} for c in country_counts]

    snapshot, _ = FormAnalyticsSnapshot.objects.update_or_create(
        form=form,
        date=snapshot_date,
        defaults={
            "views_count": total_views,
            "unique_views_count": unique_views,
            "submissions_count": total_submissions,
            "completion_rate": completion_rate,
            "avg_duration_seconds": round(avg_duration, 1),
            "desktop_views": desktop,
            "mobile_views": mobile,
            "tablet_views": tablet,
            "top_referrers": top_referrers,
            "top_countries": top_countries,
        },
    )

    logger.info(f"Snapshot generated for form {form.id} on {snapshot_date}")
    return snapshot


def get_form_overview(form: Form, days: int = 30) -> Dict[str, Any]:
    """
    Build an overview dictionary for the analytics dashboard covering the
    last N days. Combines snapshot data into trends and aggregates.
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    snapshots = FormAnalyticsSnapshot.objects.filter(
        form=form, date__gte=start_date, date__lte=end_date
    ).order_by("date")

    total_views = 0
    unique_views = 0
    total_submissions = 0
    total_duration = 0.0
    duration_count = 0
    device_totals = {"desktop": 0, "mobile": 0, "tablet": 0}
    referrer_counter = Counter()
    country_counter = Counter()

    views_trend = []
    submissions_trend = []

    for snap in snapshots:
        total_views += snap.views_count
        unique_views += snap.unique_views_count
        total_submissions += snap.submissions_count
        if snap.avg_duration_seconds > 0:
            total_duration += snap.avg_duration_seconds * snap.submissions_count
            duration_count += snap.submissions_count

        device_totals["desktop"] += snap.desktop_views
        device_totals["mobile"] += snap.mobile_views
        device_totals["tablet"] += snap.tablet_views

        for ref in snap.top_referrers:
            referrer_counter[ref.get("referrer", "")] += ref.get("count", 0)
        for cty in snap.top_countries:
            country_counter[cty.get("country", "")] += cty.get("count", 0)

        views_trend.append({"date": snap.date.isoformat(), "count": snap.views_count})
        submissions_trend.append({"date": snap.date.isoformat(), "count": snap.submissions_count})

    avg_duration = round(total_duration / duration_count, 1) if duration_count else 0.0
    completion_rate = round((total_submissions / unique_views) * 100, 2) if unique_views else 0.0

    top_referrers = [
        {"referrer": ref, "count": cnt}
        for ref, cnt in referrer_counter.most_common(10)
    ]
    top_countries = [
        {"country": cty, "count": cnt}
        for cty, cnt in country_counter.most_common(10)
    ]

    return {
        "total_views": total_views,
        "unique_views": unique_views,
        "total_submissions": total_submissions,
        "completion_rate": completion_rate,
        "avg_duration_seconds": avg_duration,
        "views_trend": views_trend,
        "submissions_trend": submissions_trend,
        "device_breakdown": device_totals,
        "top_referrers": top_referrers,
        "top_countries": top_countries,
    }


def get_field_dropoff_report(form: Form, days: int = 30):
    """
    Return an ordered list of fields with their total dropoff counts
    over the given period. Useful for identifying problematic fields.
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    dropoffs = (
        FieldDropoff.objects.filter(
            form=form, date__gte=start_date, date__lte=end_date
        )
        .values("field__id", "field__label", "field__order")
        .annotate(total_dropoffs=Sum("dropoff_count"))
        .order_by("field__order")
    )

    return list(dropoffs)


def record_form_view(form: Form, request) -> FormView:
    """
    Record a form view event, extracting device and geo information
    from the request headers.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    referrer = request.META.get("HTTP_REFERER", "")

    device_type = _detect_device_type(user_agent)
    browser = _detect_browser(user_agent)
    os_name = _detect_os(user_agent)

    return FormView.objects.create(
        form=form,
        ip_address=ip,
        user_agent=user_agent,
        referrer=referrer[:2000] if referrer else "",
        device_type=device_type,
        browser=browser,
        os=os_name,
    )


def _detect_device_type(user_agent: str) -> str:
    ua_lower = user_agent.lower()
    if any(kw in ua_lower for kw in ("ipad", "tablet", "kindle", "silk")):
        return "tablet"
    if any(kw in ua_lower for kw in ("mobile", "iphone", "android", "windows phone")):
        return "mobile"
    return "desktop"


def _detect_browser(user_agent: str) -> str:
    ua = user_agent.lower()
    if "edg/" in ua or "edge/" in ua:
        return "Edge"
    if "opr/" in ua or "opera" in ua:
        return "Opera"
    if "chrome" in ua and "chromium" not in ua:
        return "Chrome"
    if "firefox" in ua:
        return "Firefox"
    if "safari" in ua:
        return "Safari"
    return "Other"


def _detect_os(user_agent: str) -> str:
    ua = user_agent.lower()
    if "windows" in ua:
        return "Windows"
    if "macintosh" in ua or "mac os" in ua:
        return "macOS"
    if "linux" in ua and "android" not in ua:
        return "Linux"
    if "android" in ua:
        return "Android"
    if "iphone" in ua or "ipad" in ua:
        return "iOS"
    return "Other"
