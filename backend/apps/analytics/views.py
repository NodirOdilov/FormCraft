import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.models import Form

from .serializers import (
    FieldDropoffSerializer,
    FormAnalyticsSnapshotSerializer,
    FormOverviewSerializer,
    FormViewCreateSerializer,
)
from .services import get_field_dropoff_report, get_form_overview, record_form_view

logger = logging.getLogger(__name__)


class RecordFormViewAPIView(APIView):
    """Public endpoint to record a form view event."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        form_id = request.data.get("form_id")
        if not form_id:
            return Response(
                {"error": "form_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            form = Form.objects.get(id=form_id, status=Form.Status.PUBLISHED)
        except Form.DoesNotExist:
            return Response(
                {"error": "Form not found."}, status=status.HTTP_404_NOT_FOUND
            )

        view = record_form_view(form, request)
        return Response({"success": True, "view_id": str(view.id)}, status=status.HTTP_201_CREATED)


class FormOverviewAPIView(APIView):
    """Dashboard overview analytics for a form."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, form_id):
        try:
            form = Form.objects.get(id=form_id, created_by=request.user)
        except Form.DoesNotExist:
            return Response(
                {"error": "Form not found."}, status=status.HTTP_404_NOT_FOUND
            )

        days = int(request.query_params.get("days", 30))
        days = min(max(days, 1), 365)

        overview = get_form_overview(form, days=days)
        serializer = FormOverviewSerializer(overview)
        return Response(serializer.data)


class FieldDropoffAPIView(APIView):
    """Field-level dropoff analytics for a form."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, form_id):
        try:
            form = Form.objects.get(id=form_id, created_by=request.user)
        except Form.DoesNotExist:
            return Response(
                {"error": "Form not found."}, status=status.HTTP_404_NOT_FOUND
            )

        days = int(request.query_params.get("days", 30))
        days = min(max(days, 1), 365)

        report = get_field_dropoff_report(form, days=days)
        return Response(report)
