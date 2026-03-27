"""URL configuration for core app.

This module defines URL patterns for fiscal assessments, reports, and documents.
"""

from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = "core"

urlpatterns = [
    # Dashboard
    path(
        "",
        views.DashboardView.as_view(),
        name="dashboard"
    ),
    # Fiscal Assessment URLs
    path(
        "assessments/",
        views.FiscalAssessmentListView.as_view(),
        name="fiscal_assessment_list"
    ),
    path(
        "assessments/create/",
        views.FiscalAssessmentCreateView.as_view(),
        name="fiscal_assessment_create"
    ),
    path(
        "assessments/<int:assessment_id>/",
        views.FiscalAssessmentDetailView.as_view(),
        name="fiscal_assessment_detail"
    ),
    path(
        "assessments/<int:assessment_id>/edit/",
        views.FiscalAssessmentUpdateView.as_view(),
        name="fiscal_assessment_update"
    ),
    path(
        "assessments/<int:assessment_id>/approve/",
        views.FiscalAssessmentApproveView.as_view(),
        name="fiscal_assessment_approve"
    ),
    path(
        "assessments/<int:assessment_id>/print/",
        views.FiscalAssessmentPrintView.as_view(),
        name="fiscal_assessment_print"
    ),
    
    # Report URLs
    path(
        "reports/",
        views.ReportListView.as_view(),
        name="report_list"
    ),
    path(
        "reports/create/",
        views.ReportCreateView.as_view(),
        name="report_create"
    ),
    path(
        "reports/<int:report_id>/",
        views.ReportDetailView.as_view(),
        name="report_detail"
    ),
    path(
        "reports/<int:report_id>/export/",
        views.ReportExportView.as_view(),
        name="report_export"
    ),
    
    # Document URLs
    path(
        "documents/",
        views.DocumentListView.as_view(),
        name="document_list"
    ),
    path(
        "documents/create/",
        views.DocumentCreateView.as_view(),
        name="document_create"
    ),
    path(
        "documents/<int:document_id>/",
        views.DocumentDetailView.as_view(),
        name="document_detail"
    ),
    path(
        "documents/<int:document_id>/export/",
        views.DocumentExportView.as_view(),
        name="document_export"
    ),
    
    # API URLs
    path(
        "api/assessments/",
        views.FiscalAssessmentAPIView.as_view(),
        name="fiscal_assessment_api"
    ),
    path(
        "api/assessments/<int:assessment_id>/",
        views.FiscalAssessmentAPIView.as_view(),
        name="fiscal_assessment_api_detail"
    ),
    path(
        "api/reports/",
        views.ReportAPIView.as_view(),
        name="report_api"
    ),
    path(
        "api/reports/<int:report_id>/",
        views.ReportAPIView.as_view(),
        name="report_api_detail"
    ),
    path(
        "api/documents/",
        views.DocumentAPIView.as_view(),
        name="document_api"
    ),
    path(
        "api/documents/<int:document_id>/",
        views.DocumentAPIView.as_view(),
        name="document_api_detail"
    ),
    path(
        "api/dashboard-summary/",
        views.DashboardSummaryView.as_view(),
        name="dashboard_summary_api"
    ),
    path(
        "api/trend-data/",
        views.TrendDataAPIView.as_view(),
        name="trend_data_api"
    ),
    
    # Activity Logs URL
    path(
        "activity-logs/",
        views.EventLogListView.as_view(),
        name="activity_log_list"
    ),

    # Analytics Dashboard
    path(
        "analytics/",
        views.AnalyticsDashboardView.as_view(),
        name="analytics_dashboard"
    ),

    # Report Schedule URLs
    path(
        "schedules/",
        views.ReportScheduleListView.as_view(),
        name="report_schedule_list"
    ),
    path(
        "schedules/create/",
        views.ReportScheduleCreateView.as_view(),
        name="report_schedule_create"
    ),
    path(
        "schedules/<int:schedule_id>/edit/",
        views.ReportScheduleUpdateView.as_view(),
        name="report_schedule_update"
    ),
    path(
        "schedules/<int:schedule_id>/delete/",
        views.ReportScheduleDeleteView.as_view(),
        name="report_schedule_delete"
    ),
    path(
        "schedules/<int:schedule_id>/run/",
        views.ReportScheduleRunNowView.as_view(),
        name="report_schedule_run"
    ),

    # Airport Comparison
    path(
        "airports/compare/",
        views.AirportComparisonView.as_view(),
        name="airport_comparison"
    ),

    # Public Portal URLs (no authentication required)
    path(
        "flights/status/",
        views.FlightStatusPortalView.as_view(),
        name="flight_status_portal"
    ),
    path(
        "baggage/track/",
        RedirectView.as_view(url="/baggage/public/", permanent=False, query_string=True),
        name="baggage_tracking"
    ),

    # Data Import Wizard
    path(
        "import/<str:model_name>/",
        views.DataImportWizardView.as_view(),
        name="data_import_wizard"
    ),

    # Health check endpoint for monitoring/self-ping
    path(
        "health/",
        views.health_check,
        name="health_check"
    ),
]
