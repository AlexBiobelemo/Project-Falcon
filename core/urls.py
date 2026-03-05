"""URL configuration for core app.

This module defines URL patterns for fiscal assessments, reports, and documents.
"""

from django.urls import path

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
    
    # Activity Logs URL
    path(
        "activity-logs/",
        views.EventLogListView.as_view(),
        name="activity_log_list"
    ),
]
