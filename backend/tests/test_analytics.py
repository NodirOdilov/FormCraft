"""
Tests for the analytics app: view recording, snapshot generation, overview.
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.analytics.models import FieldDropoff, FormAnalyticsSnapshot, FormView
from apps.analytics.services import (
    generate_daily_snapshot,
    get_field_dropoff_report,
    get_form_overview,
    record_form_view,
)
from apps.forms.models import Form, FormField
from apps.submissions.models import Submission


class FormViewRecordingTests(TestCase):
    """Tests for recording form view events."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="viewtest@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Viewed Form", status=Form.Status.PUBLISHED
        )
        self.factory = RequestFactory()

    def test_record_desktop_view(self):
        request = self.factory.get("/")
        request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
        )
        request.META["HTTP_REFERER"] = "https://example.com/page"
        view = record_form_view(self.form, request)
        self.assertEqual(view.device_type, "desktop")
        self.assertEqual(view.browser, "Chrome")
        self.assertEqual(view.os, "Windows")
        self.assertEqual(view.referrer, "https://example.com/page")

    def test_record_mobile_view(self):
        request = self.factory.get("/")
        request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1"
        )
        view = record_form_view(self.form, request)
        self.assertEqual(view.device_type, "mobile")
        self.assertEqual(view.os, "iOS")

    def test_record_tablet_view(self):
        request = self.factory.get("/")
        request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) Safari/604.1"
        )
        view = record_form_view(self.form, request)
        self.assertEqual(view.device_type, "tablet")


class SnapshotGenerationTests(TestCase):
    """Tests for daily analytics snapshot generation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="snapshot@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Snapshot Form", status=Form.Status.PUBLISHED
        )

    def test_generate_empty_snapshot(self):
        yesterday = date.today() - timedelta(days=1)
        snapshot = generate_daily_snapshot(self.form, snapshot_date=yesterday)
        self.assertEqual(snapshot.views_count, 0)
        self.assertEqual(snapshot.submissions_count, 0)
        self.assertEqual(snapshot.completion_rate, 0.0)

    def test_snapshot_updates_on_regeneration(self):
        yesterday = date.today() - timedelta(days=1)
        snap1 = generate_daily_snapshot(self.form, snapshot_date=yesterday)
        snap2 = generate_daily_snapshot(self.form, snapshot_date=yesterday)
        self.assertEqual(snap1.id, snap2.id)  # Same record updated


class FormOverviewTests(TestCase):
    """Tests for the overview aggregation service."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="overview@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user, title="Overview Form", status=Form.Status.PUBLISHED
        )
        yesterday = date.today() - timedelta(days=1)
        FormAnalyticsSnapshot.objects.create(
            form=self.form,
            date=yesterday,
            views_count=100,
            unique_views_count=80,
            submissions_count=20,
            completion_rate=25.0,
            avg_duration_seconds=45.0,
            desktop_views=60,
            mobile_views=30,
            tablet_views=10,
            top_referrers=[{"referrer": "https://google.com", "count": 40}],
            top_countries=[{"country": "US", "count": 50}],
        )

    def test_overview_returns_correct_totals(self):
        overview = get_form_overview(self.form, days=7)
        self.assertEqual(overview["total_views"], 100)
        self.assertEqual(overview["unique_views"], 80)
        self.assertEqual(overview["total_submissions"], 20)
        self.assertEqual(overview["device_breakdown"]["desktop"], 60)
        self.assertEqual(len(overview["views_trend"]), 1)

    def test_overview_empty_period(self):
        overview = get_form_overview(self.form, days=0)
        self.assertEqual(overview["total_views"], 0)


class AnalyticsAPITests(TestCase):
    """Integration tests for analytics API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="analyticsapi@formcraft.io", password="TestPass123!"
        )
        self.form = Form.objects.create(
            created_by=self.user,
            title="Analytics API Form",
            status=Form.Status.PUBLISHED,
        )

    def test_record_view_public(self):
        response = self.client.post(
            "/api/analytics/view/",
            {"form_id": str(self.form.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

    def test_record_view_invalid_form(self):
        import uuid

        response = self.client.post(
            "/api/analytics/view/",
            {"form_id": str(uuid.uuid4())},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_overview_requires_auth(self):
        response = self.client.get(f"/api/analytics/{self.form.id}/overview/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/{self.form.id}/overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_views", response.data)
