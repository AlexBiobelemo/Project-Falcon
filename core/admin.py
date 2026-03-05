"""Admin configuration for the Airport Operations Management System.

ADMIN ACCESS CONTROL - Least Privilege Principle:
The Django admin panel is restricted to superusers only.
Regular users (including editors and approvers) cannot access admin.
This follows the principle of least privilege.
"""

import csv
import io
import logging
from datetime import datetime
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path


from .models import (
    Airport,
    Document,
    EventLog,
    FiscalAssessment,
    Flight,
    Gate,
    Passenger,
    Report,
    Staff,
    StaffAssignment,
)


def validate_csv_file(csv_file, max_size_mb=2):
    """Validate CSV file for import using whitelist approach.
    
    Args:
        csv_file: The uploaded file to validate.
        max_size_mb: Maximum file size in megabytes.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Get whitelist from settings - only allow specific extensions
    from django.conf import settings
    allowed_extensions = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', ['.csv'])
    
    # Check file extension against whitelist
    file_ext = '.' + csv_file.name.split('.')[-1].lower() if '.' in csv_file.name else ''
    if file_ext not in allowed_extensions:
        return False, f"Invalid file type. Only {', '.join(allowed_extensions)} files are allowed."
    
    # Check file size (max by parameter or settings default)
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', max_size_mb * 1024 * 1024)
    if csv_file.size > max_size:
        return False, f"File too large. Maximum size is {max_size // (1024*1024)}MB."
    
    return True, None


def sanitize_import_error(row_num: int, exception: Exception, logger: logging.Logger = None) -> str:
    """Sanitize error messages from CSV imports to prevent information disclosure.
    
    This function creates safe error messages for users while logging the actual
    errors for debugging purposes.
    
    Args:
        row_num: The row number where the error occurred.
        exception: The original exception.
        logger: Optional logger for recording actual errors.
    
    Returns:
        A sanitized error message safe to display to users.
    """
    # Log the actual error for debugging 
    if logger:
        logger.warning(f"CSV import error at row {row_num}: {type(exception).__name__}: {str(exception)}")
    
    # Return sanitized generic message
    return f"Row {row_num}: Invalid data format"


# Get logger for CSV import operations
csv_import_logger = logging.getLogger('csv_import')


# MIXINS - Reusable functionality for admin classes
class CSVImportMixin:
    """Mixin that provides common CSV import functionality.
    
    Subclasses must implement:
    - get_model(): Returns the model class
    - process_row(row, row_num): Process a single CSV row, returns (object, error_msg)
    - get_model_name(): Returns lowercase model name for templates
    """
    
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('import-csv/', self.import_csv, name='import_csv'),
        ] + urls
    
    def _check_superuser(self, request: HttpRequest) -> bool:
        """Check if user is superuser, return True if authorized."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can import CSV data.", level='error')
            return False
        return True
    
    def _process_csv_file(self, csv_file, process_row_func):
        """Process CSV file and return created_count and errors."""
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string)
        
        # Skip header
        next(reader)
        
        created_count = 0
        errors = []
        for row_num, row in enumerate(reader, start=2):
            try:
                obj, error_msg = process_row_func(row, row_num)
                if obj:
                    created_count += 1
                if error_msg:
                    errors.append(error_msg)
            except Exception as e:
                errors.append(sanitize_import_error(row_num, e, csv_import_logger))
        
        return created_count, errors
    
    def import_csv(self, request: HttpRequest):
        """Handle CSV import request."""
        # RBAC: Only superusers can import CSV
        if not self._check_superuser(request):
            return HttpResponseRedirect('../')
        
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            
            # Validate file
            is_valid, error_message = validate_csv_file(csv_file)
            if not is_valid:
                self.message_user(request, error_message, level='error')
                return HttpResponseRedirect('../')
            
            # Process CSV using subclass implementation
            created_count, errors = self._process_csv_file(csv_file, self.process_row)
            
            model_name = self.get_model_name()
            if errors:
                self.message_user(request, f"Imported {created_count} {model_name}. Errors: {'; '.join(errors[:5])}", level='warning')
            else:
                self.message_user(request, f'Imported {created_count} {model_name} successfully!')
            return HttpResponseRedirect('../')
        
        return render(request, 'admin/csv_form.html', {
            'title': 'Import CSV',
            'app_label': 'core',
            'model_name': self.get_model_name()
        })
    
    def process_row(self, row, row_num):
        """Process a single CSV row. Must be implemented by subclass."""
        raise NotImplementedError("Subclasses must implement process_row()")
    
    def get_model_name(self):
        """Return lowercase model name. Must be implemented by subclass."""
        raise NotImplementedError("Subclasses must implement get_model_name()")


class CSVExportMixin:
    """Mixin that provides common CSV export functionality.
    
    Subclasses must implement:
    - get_export_fields(): Returns list of field names for CSV header
    - get_export_row(obj): Returns list of field values for a single object
    """
    
    def export_to_csv(self, request, queryset):
        """Export selected objects to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(
            self.model._meta.model_name
        )
        
        writer = csv.writer(response)
        writer.writerow(self.get_export_fields())
        
        for obj in queryset:
            writer.writerow(self.get_export_row(obj))
        
        return response
    
    export_to_csv.short_description = "Export selected to CSV"
    
    def get_export_fields(self):
        """Return list of field names for CSV header. Must be implemented by subclass."""
        raise NotImplementedError("Subclasses must implement get_export_fields()")
    
    def get_export_row(self, obj):
        """Return list of field values for a single object. Must be implemented by subclass."""
        raise NotImplementedError("Subclasses must implement get_export_row()")


# ADMIN CLASSES
class PassengerInline(admin.TabularInline):
    """Inline admin for passengers."""
    model = Passenger
    extra = 0
    readonly_fields = ["passenger_id", "created_at", "updated_at"]


@admin.register(Airport)
class AirportAdmin(CSVImportMixin, admin.ModelAdmin):
    """Admin for Airport model."""
    list_display = ["code", "name", "city", "is_active"]
    search_fields = ["code", "name", "city"]
    list_filter = ["is_active"]
    
    def process_row(self, row, row_num):
        if len(row) >= 3:
            Airport.objects.get_or_create(
                code=row[0].strip().upper(),
                defaults={
                    'name': row[1].strip(),
                    'city': row[2].strip(),
                    'timezone': row[3].strip() if len(row) > 3 else 'UTC',
                }
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "airports"


@admin.register(Gate)
class GateAdmin(CSVImportMixin, admin.ModelAdmin):
    """Admin for Gate model."""
    list_display = ["gate_id", "terminal", "capacity", "status", "updated_at"]
    list_filter = ["status", "terminal", "capacity"]
    search_fields = ["gate_id", "terminal"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["gate_id"]
    
    def process_row(self, row, row_num):
        if len(row) >= 4:
            Gate.objects.get_or_create(
                gate_id=row[0].strip(),
                defaults={
                    'terminal': row[1].strip(),
                    'capacity': row[2].strip(),
                    'status': row[3].strip()
                }
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "gates"


@admin.register(Flight)
class FlightAdmin(CSVImportMixin, admin.ModelAdmin):
    """Admin for Flight model."""
    list_display = [
        "flight_number", "origin", "destination",
        "scheduled_departure", "gate", "status", "delay_minutes"
    ]
    list_filter = ["status", "origin", "destination"]
    search_fields = ["flight_number", "origin", "destination"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [PassengerInline]
    ordering = ["scheduled_departure"]
    
    def process_row(self, row, row_num):
        if len(row) >= 8:
            # Get gate if provided
            gate = None
            if len(row) > 6 and row[6].strip():
                gate = Gate.objects.filter(gate_id=row[6].strip()).first()
            
            # Parse datetime
            scheduled_departure = row[4].strip()
            scheduled_arrival = row[5].strip()
            
            Flight.objects.get_or_create(
                flight_number=row[0].strip().upper(),
                defaults={
                    'airline': row[1].strip() if len(row) > 1 else '',
                    'origin': row[2].strip().upper(),
                    'destination': row[3].strip().upper(),
                    'scheduled_departure': scheduled_departure,
                    'scheduled_arrival': scheduled_arrival,
                    'gate': gate,
                    'status': row[7].strip().lower() if len(row) > 7 else 'scheduled',
                    'delay_minutes': int(row[8].strip()) if len(row) > 8 and row[8].strip().isdigit() else 0
                }
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "flights"


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    """Admin for Passenger model."""
    list_display = ["last_name", "first_name", "passport_number", "flight", "seat_number", "status"]
    list_filter = ["status", "flight"]
    search_fields = ["first_name", "last_name", "passport_number", "seat_number"]
    readonly_fields = ["passenger_id", "created_at", "updated_at"]
    ordering = ["last_name", "first_name"]


@admin.register(Staff)
class StaffAdmin(CSVImportMixin, admin.ModelAdmin):
    """Admin for Staff model."""
    list_display = ["last_name", "first_name", "employee_number", "role", "is_available"]
    list_filter = ["role", "is_available"]
    search_fields = ["first_name", "last_name", "employee_number"]
    readonly_fields = ["staff_id", "created_at", "updated_at"]
    ordering = ["last_name", "first_name"]
    
    def process_row(self, row, row_num):
        if len(row) >= 5:
            Staff.objects.get_or_create(
                employee_number=row[2].strip(),
                defaults={
                    'first_name': row[0].strip(),
                    'last_name': row[1].strip(),
                    'role': row[3].strip(),
                    'certification': row[4].strip() if len(row) > 4 else '',
                    'is_available': row[5].strip().lower() == 'true' if len(row) > 5 else True,
                }
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "staff"


@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    """Admin for StaffAssignment model."""
    list_display = ["staff", "flight", "assignment_type", "assigned_at"]
    list_filter = ["assignment_type", "assigned_at"]
    search_fields = ["staff__first_name", "staff__last_name", "flight__flight_number"]
    readonly_fields = ["assigned_at"]
    raw_id_fields = ["staff", "flight"]
    ordering = ["-assigned_at"]


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    """Admin for EventLog model."""
    list_display = ["timestamp", "event_type", "action", "user", "description", "severity"]
    list_filter = ["severity", "event_type", "action", "timestamp"]
    search_fields = ["description", "event_type", "user__username"]
    readonly_fields = ["event_id", "created_at", "timestamp"]
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"
    raw_id_fields = ["user", "flight"]
    list_per_page = 50


@admin.register(FiscalAssessment)
class FiscalAssessmentAdmin(CSVImportMixin, CSVExportMixin, admin.ModelAdmin):
    """Admin for FiscalAssessment model."""
    list_display = ["airport", "period_type", "start_date", "end_date", "status", "total_revenue", "total_expenses", "net_profit"]
    list_filter = ["status", "period_type", "airport"]
    search_fields = ["airport__code", "airport__name"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-start_date"]
    date_hierarchy = "start_date"
    fieldsets = (
        ("Airport & Period", {
            "fields": ("airport", "period_type", "start_date", "end_date", "status")
        }),
        ("Financial Metrics", {
            "fields": ("total_revenue", "total_expenses", "net_profit")
        }),
        ("Operational Metrics", {
            "fields": ("passenger_count", "flight_count")
        }),
        ("Revenue Breakdown", {
            "fields": ("fuel_revenue", "parking_revenue", "retail_revenue", "landing_fees", "cargo_revenue", "other_revenue")
        }),
        ("Expense Breakdown", {
            "fields": ("security_costs", "maintenance_costs", "operational_costs", "staff_costs", "utility_costs", "other_expenses")
        }),
        ("Approval", {
            "fields": ("assessment_notes", "assessed_by", "approved_by", "approved_at")
        }),
    )
    actions = ["export_to_csv", "approve_selected"]
    
    def process_row(self, row, row_num):
        if len(row) >= 10:
            from core.models import AssessmentStatus
            
            # Get airport
            airport = None
            if row[0].strip():
                airport = Airport.objects.filter(code=row[0].strip().upper()).first()
            
            if not airport:
                return False, f"Row {row_num}: Airport not found"
            
            # Parse dates
            start_date = datetime.strptime(row[2].strip(), '%Y-%m-%d').date() if row[2].strip() else None
            end_date = datetime.strptime(row[3].strip(), '%Y-%m-%d').date() if row[3].strip() else None
            
            # Parse numeric fields
            def parse_decimal(val, default=0):
                try:
                    return float(val.strip()) if val.strip() else default
                except:
                    return default
            
            def parse_int(val, default=0):
                try:
                    return int(val.strip()) if val.strip() else default
                except:
                    return default
            
            FiscalAssessment.objects.create(
                airport=airport,
                period_type=row[1].strip().lower(),
                start_date=start_date,
                end_date=end_date,
                status=row[4].strip().lower() if len(row) > 4 else 'draft',
                total_revenue=parse_decimal(row[5]) if len(row) > 5 else 0,
                total_expenses=parse_decimal(row[6]) if len(row) > 6 else 0,
                net_profit=parse_decimal(row[7]) if len(row) > 7 else 0,
                passenger_count=parse_int(row[8]) if len(row) > 8 else 0,
                flight_count=parse_int(row[9]) if len(row) > 9 else 0,
                assessed_by=self.request.user.username,
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "fiscal assessments"
    
    def _check_superuser(self, request: HttpRequest) -> bool:
        """Check if user is superuser, return True if authorized."""
        # Store request for use in process_row
        self.request = request
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can import CSV data.", level='error')
            return False
        return True
    
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('import-csv/', self.import_csv, name='import_csv'),
        ] + urls
    
    def get_export_fields(self):
        return [
            'Airport', 'Period Type', 'Start Date', 'End Date', 'Status',
            'Total Revenue', 'Total Expenses', 'Net Profit',
            'Passenger Count', 'Flight Count'
        ]
    
    def get_export_row(self, obj):
        return [
            obj.airport.code,
            obj.period_type,
            obj.start_date,
            obj.end_date,
            obj.status,
            obj.total_revenue,
            obj.total_expenses,
            obj.net_profit,
            obj.passenger_count,
            obj.flight_count,
        ]
    
    def export_to_csv(self, request, queryset):
        """Export selected assessments to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fiscal_assessments.csv"'
        
        writer = csv.writer(response)
        writer.writerow(self.get_export_fields())
        
        for obj in queryset:
            writer.writerow(self.get_export_row(obj))
        
        return response
    
    def approve_selected(self, request, queryset):
        """Approve selected assessments."""
        from django.utils import timezone
        from core.models import AssessmentStatus
        
        count = 0
        for obj in queryset:
            if obj.status != AssessmentStatus.APPROVED.value:
                obj.status = AssessmentStatus.APPROVED.value
                obj.approved_by = request.user.username
                obj.approved_at = timezone.now()
                obj.save()
                count += 1
        
        self.message_user(request, f"{count} assessments approved.")
    
    approve_selected.short_description = "Approve selected assessments"


@admin.register(Report)
class ReportAdmin(CSVImportMixin, CSVExportMixin, admin.ModelAdmin):
    """Admin for Report model."""
    list_display = ["title", "airport", "report_type", "period_start", "period_end", "format", "is_generated", "generated_at"]
    list_filter = ["report_type", "format", "is_generated", "airport"]
    search_fields = ["title", "airport__code", "airport__name"]
    readonly_fields = ["report_id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    actions = ["export_to_csv", "regenerate_reports"]
    
    def process_row(self, row, row_num):
        if len(row) >= 6:
            # Get airport
            airport = None
            if row[1].strip():
                airport = Airport.objects.filter(code=row[1].strip().upper()).first()
            
            if not airport:
                return False, f"Row {row_num}: Airport not found"
            
            # Parse dates
            period_start = datetime.strptime(row[3].strip(), '%Y-%m-%d').date() if row[3].strip() else None
            period_end = datetime.strptime(row[4].strip(), '%Y-%m-%d').date() if row[4].strip() else None
            
            Report.objects.create(
                title=row[0].strip(),
                airport=airport,
                report_type=row[2].strip().lower(),
                period_start=period_start,
                period_end=period_end,
                format=row[5].strip().lower() if len(row) > 5 else 'html',
                description=row[6].strip() if len(row) > 6 else '',
                generated_by=self.request.user.username,
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "reports"
    
    def _check_superuser(self, request: HttpRequest) -> bool:
        """Check if user is superuser, return True if authorized."""
        # Store request for use in process_row
        self.request = request
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can import CSV data.", level='error')
            return False
        return True
    
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('import-csv/', self.import_csv, name='import_csv'),
        ] + urls
    
    def get_export_fields(self):
        return [
            'Title', 'Airport', 'Type', 'Period Start', 'Period End',
            'Format', 'Generated', 'Generated At'
        ]
    
    def get_export_row(self, obj):
        return [
            obj.title,
            obj.airport.code,
            obj.report_type,
            obj.period_start,
            obj.period_end,
            obj.format,
            obj.is_generated,
            obj.generated_at,
        ]
    
    def export_to_csv(self, request, queryset):
        """Export selected reports to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports.csv"'
        
        writer = csv.writer(response)
        writer.writerow(self.get_export_fields())
        
        for obj in queryset:
            writer.writerow(self.get_export_row(obj))
        
        return response
    
    def regenerate_reports(self, request, queryset):
        """Regenerate selected reports."""
        from core.views import ReportCreateView
        
        count = 0
        for obj in queryset:
            # Re-generate the report content
            view = ReportCreateView()
            new_content = view._generate_report_content(obj)
            obj.content = new_content
            obj.is_generated = True
            obj.save()
            count += 1
        
        self.message_user(request, f"{count} reports regenerated.")
    
    regenerate_reports.short_description = "Regenerate selected reports"


@admin.register(Document)
class DocumentAdmin(CSVImportMixin, CSVExportMixin, admin.ModelAdmin):
    """Admin for Document model."""
    list_display = ["name", "document_type", "airport", "is_template", "created_by", "created_at"]
    list_filter = ["document_type", "is_template", "airport"]
    search_fields = ["name", "airport__code", "airport__name"]
    readonly_fields = ["document_id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    actions = ["export_to_csv", "mark_as_template", "mark_as_document"]
    
    def process_row(self, row, row_num):
        if len(row) >= 4:
            # Get airport if provided
            airport = None
            if len(row) > 2 and row[2].strip():
                airport = Airport.objects.filter(code=row[2].strip().upper()).first()
            
            Document.objects.create(
                name=row[0].strip(),
                document_type=row[1].strip().lower(),
                airport=airport,
                content=row[3].strip() if len(row) > 3 else '',
                created_by=self.request.user.username,
            )
            return True, None
        return False, f"Row {row_num}: Invalid data format"
    
    def get_model_name(self):
        return "documents"
    
    def _check_superuser(self, request: HttpRequest) -> bool:
        """Check if user is superuser, return True if authorized."""
        # Store request for use in process_row
        self.request = request
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can import CSV data.", level='error')
            return False
        return True
    
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('import-csv/', self.import_csv, name='import_csv'),
        ] + urls
    
    def get_export_fields(self):
        return [
            'Name', 'Type', 'Airport', 'Template', 'Created By', 'Created At'
        ]
    
    def get_export_row(self, obj):
        return [
            obj.name,
            obj.document_type,
            obj.airport.code if obj.airport else '',
            obj.is_template,
            obj.created_by,
            obj.created_at,
        ]
    
    def export_to_csv(self, request, queryset):
        """Export selected documents to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="documents.csv"'
        
        writer = csv.writer(response)
        writer.writerow(self.get_export_fields())
        
        for obj in queryset:
            writer.writerow(self.get_export_row(obj))
        
        return response
    
    def mark_as_template(self, request, queryset):
        """Mark selected documents as templates."""
        count = queryset.update(is_template=True)
        self.message_user(request, f"{count} documents marked as templates.")
    
    mark_as_template.short_description = "Mark as template"
    
    def mark_as_document(self, request, queryset):
        """Mark selected documents as regular documents."""
        count = queryset.update(is_template=False)
        self.message_user(request, f"{count} documents marked as regular documents.")
    
    mark_as_document.short_description = "Mark as document"


# CUSTOM ADMIN SITE - Restrict Access to Superusers Only
class RestrictedAdminSite(admin.AdminSite):
    """Custom admin site that restricts access to superusers only."""
    
    def has_permission(self, request):
        """Check if user has permission to access admin."""
        return request.user.is_active and request.user.is_superuser
    
    def admin_view(self, view, cacheable=False):
        """Wrap the admin view to check for superuser status."""
        def wrapper(request, *args, **kwargs):
            if not request.user.is_superuser:
                return HttpResponseForbidden(
                    "Access denied. Only superusers can access the admin panel."
                )
            return view(request, *args, **kwargs)
        return wrapper
