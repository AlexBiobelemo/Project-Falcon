# Summary of Changes - March 8, 2026

This document summarizes the security fixes, performance optimizations, and new features implemented in the Blue Falcon project.

## 1. Security Enhancements

### Authentication & Configuration
- **Password Hashing:** Removed `MD5PasswordHasher` from `DEBUG` mode. The system now uses strong hashers (PBKDF2, Argon2, BCrypt) in all environments.
- **Secret Key Management:** Removed insecure `SECRET_KEY` fallback in `settings.py`. The application now "fails fast" if the `SECRET_KEY` environment variable is not provided.

### CSRF & Form Security
- **CSRF Protection:** Re-enabled CSRF protection on `FiscalAssessmentAPIView`, `ReportAPIView`, and `DocumentAPIView` by removing `@csrf_exempt`. These endpoints now require a valid CSRF token when accessed via session authentication.
- **Honeypot Protection:** Integrated `HoneypotFieldMixin` into all critical forms (`FiscalAssessment`, `Report`, `Document`). Updated the honeypot module to ensure fields are initialized and rendered correctly.

### Input Validation & Access Control
- **View Refactoring:** Refactored `ReportCreateView` and `DocumentCreateView` to use Django Forms instead of manual POST data extraction. This prevents mass-assignment vulnerabilities and ensures strict type validation.
- **JSON Validation:** Added strict JSON schema validation for document content.
- **Admin Enforcement:** Hardened the `delete` operation for fiscal assessments to strictly require superuser (admin) privileges, logging any unauthorized attempts.

## 2. Performance Optimizations

### Database Efficiency
- **Query Optimization:** Optimized `DashboardView` and `DashboardSummaryView` to use database-level aggregation (`Count`, `Sum`, `Q` expressions). This replaces inefficient Python loops with single, high-performance SQL queries.
- **N+1 Query Fixes:** Applied `select_related` and `prefetch_related` across all Django views and DRF ViewSets (Flights, Passengers, Staff, EventLogs, etc.) to minimize database round-trips.
- **Indexing:** Verified and utilized database indexes for frequent query patterns in `EventLog` and `FiscalAssessment`.

### Caching
- **API Caching:** Implemented `cache_page` (5-minute window) for the dashboard summary API to reduce server load on high-traffic data.

## 3. New Features & Infrastructure

### Background Tasks
- **Infrastructure:** Integrated `django-q2` with Redis support for background task management.
- **Async Reports:** Moved report generation from the request-response cycle to background tasks (`core/tasks.py`). Users are notified when a report is queued, and the UI remains responsive.

### Operational Intelligence
- **Conflict Detection:** Added automated conflict detection for `StaffAssignment`. The system now prevents assigning the same staff member to overlapping flights.
- **Trend Data API:** Created a new `TrendDataAPIView` endpoint to provide 6-month historical data for revenue and passenger counts, formatted specifically for Chart.js visualizations.

### Models & Business Logic
- **Financial Logic:** Added `calculate_totals` to the `FiscalAssessment` model to centralize and standardize profit/loss calculations.
