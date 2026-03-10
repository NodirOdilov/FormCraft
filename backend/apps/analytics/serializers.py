from rest_framework import serializers

from .models import FieldDropoff, FormAnalyticsSnapshot, FormView


class FormViewCreateSerializer(serializers.ModelSerializer):
    """Serializer for recording a new form view (public endpoint)."""

    class Meta:
        model = FormView
        fields = ("form", "referrer")


class FormAnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormAnalyticsSnapshot
        fields = (
            "id",
            "form",
            "date",
            "views_count",
            "unique_views_count",
            "submissions_count",
            "completion_rate",
            "avg_duration_seconds",
            "desktop_views",
            "mobile_views",
            "tablet_views",
            "top_referrers",
            "top_countries",
        )
        read_only_fields = fields


class FieldDropoffSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_order = serializers.IntegerField(source="field.order", read_only=True)

    class Meta:
        model = FieldDropoff
        fields = ("id", "field", "field_label", "field_order", "date", "dropoff_count")
        read_only_fields = fields


class FormOverviewSerializer(serializers.Serializer):
    """Aggregated overview stats returned by the dashboard endpoint."""

    total_views = serializers.IntegerField()
    unique_views = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_duration_seconds = serializers.FloatField()
    views_trend = serializers.ListField(child=serializers.DictField())
    submissions_trend = serializers.ListField(child=serializers.DictField())
    device_breakdown = serializers.DictField()
    top_referrers = serializers.ListField(child=serializers.DictField())
    top_countries = serializers.ListField(child=serializers.DictField())
