# User Guide & Features Documentation

> **Project:** Project Falcon - Airport Operations Management System
> **Version:** 1.0
> **Last Updated:** March 24, 2026

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Flight Management](#flight-management)
4. [Gate Management](#gate-management)
5. [Passenger Management](#passenger-management)
6. [Staff Management](#staff-management)
7. [Fiscal Assessments](#fiscal-assessments)
8. [Reports & Documents](#reports--documents)
9. [Analytics](#analytics)
10. [Activity Logs](#activity-logs)
11. [Public Portals](#public-portals)
12. [Keyboard Shortcuts](#keyboard-shortcuts)
13. [Notifications](#notifications)

---

## Getting Started

### Login

1. Navigate to the application URL
2. Click "Login" in the top navigation
3. Enter your username and password
4. If 2FA is enabled, enter your verification code

### User Roles

Your access level depends on your assigned role:

| Role | Access Level | Capabilities |
|------|-------------|--------------|
| **Viewer** | Read-Only | View dashboards, reports, flight status |
| **Editor** | Create/Edit | Create and edit operational data |
| **Approver** | Elevated | Approve fiscal assessments, generate reports |
| **Admin** | Full Access | All features including user management |

### First Login Checklist

- [ ] Review the dashboard overview
- [ ] Check your profile settings
- [ ] Familiarize yourself with navigation
- [ ] Review activity logs for recent changes
- [ ] Set up notification preferences

---

## Dashboard Overview

The dashboard is your central hub for airport operations monitoring.

### Dashboard Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Main Dashboard                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │ Total Gates │ │Active Flights│ │  Available  │ │  Delayed    │  │
│  │     50      │ │     45      │ │    Gates    │ │   Flights   │  │
│  │             │ │             │ │     12      │ │      3      │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                                     │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐  │
│  │     Flight Status Chart     │ │    Gate Utilization Chart   │  │
│  │                             │ │                             │  │
│  │   [Bar Chart Visualization] │ │   [Pie Chart Visualization] │  │
│  │                             │ │                             │  │
│  └─────────────────────────────┘ └─────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Recent Activity Log                       │  │
│  │  • Flight BA123 status changed to delayed (14:30)           │  │
│  │  • Gate A5 assigned to flight BA456 (14:25)                 │  │
│  │  • New fiscal assessment created for March (14:20)          │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Metrics

| Metric | Description | Update Frequency |
|--------|-------------|------------------|
| Total Gates | Total number of gates across all airports | Real-time |
| Active Flights | Flights currently in operation | Real-time |
| Available Gates | Gates ready for assignment | Real-time |
| Delayed Flights | Flights with delays | Real-time |
| Passengers Today | Total passengers processed today | Every 5 minutes |
| Gate Utilization | Percentage of gates in use | Every 5 minutes |
| On-Time Performance | Percentage of flights on time | Every 5 minutes |

### Interactive Features

- **Click on metrics** to view detailed lists
- **Hover over charts** for detailed tooltips
- **Refresh button** to manually update data
- **Time range selector** for historical data

---

## Flight Management

### Viewing Flights

Navigate to: **Flights → Flight List**

#### Flight List Features

- **Search:** Find flights by flight number, airline, or route
- **Filter:** Filter by status, airline, date range
- **Sort:** Click column headers to sort
- **Pagination:** Navigate through pages

#### Flight Status Colors

| Status | Color | Description |
|--------|-------|-------------|
| Scheduled | Blue | Flight is scheduled |
| Boarding | Green | Boarding in progress |
| Departed | Gray | Flight has departed |
| Arrived | Green | Flight has arrived |
| Delayed | Yellow | Flight is delayed |
| Cancelled | Red | Flight was cancelled |

### Creating a New Flight

1. Click **"New Flight"** button
2. Fill in flight details:
   - Flight Number (e.g., BA123)
   - Airline
   - Origin and Destination airports
   - Scheduled departure and arrival times
   - Aircraft type
3. Optionally assign a gate
4. Click **"Create Flight"**

### Editing a Flight

1. Click on the flight number in the list
2. Click **"Edit"** button
3. Update flight details
4. Click **"Save Changes"**

### Flight Status Updates

Update flight status as the flight progresses:

1. **Scheduled** → Initial status when created
2. **Boarding** → When boarding begins
3. **Departed** → When flight takes off
4. **Arrived** → When flight lands

For delays:
1. Change status to **Delayed**
2. Enter delay minutes
3. Add notes explaining the delay

### Flight Details Page

The flight details page shows:

- Flight information
- Assigned gate
- Passenger list
- Staff assignments
- Status history
- Related event logs

---

## Gate Management

### Viewing Gates

Navigate to: **Gates → Gate List**

#### Gate Status

| Status | Color | Description |
|--------|-------|-------------|
| Available | Green | Ready for assignment |
| Occupied | Blue | Currently in use |
| Maintenance | Yellow | Under maintenance |
| Closed | Red | Closed for operations |

### Gate Assignment

#### Manual Assignment

1. Go to flight details page
2. Click **"Assign Gate"**
3. Select available gate
4. Click **"Assign"**

#### Auto-Assignment

The system suggests gates based on:
- Aircraft size compatibility
- Terminal preferences
- Connection times
- Maintenance schedules

### Gate Utilization

View gate utilization metrics:

- **Occupancy Rate:** Percentage of time gates are occupied
- **Turnover Time:** Average time between flights
- **Terminal Distribution:** Flights per terminal

### Maintenance Scheduling

1. Change gate status to **Maintenance**
2. Add maintenance notes
3. Set expected completion time
4. Create maintenance log entry

---

## Passenger Management

### Viewing Passengers

Navigate to: **Passengers → Passenger List**

#### Passenger Status

| Status | Description |
|--------|-------------|
| Checked In | Passenger has checked in |
| Boarded | Passenger has boarded the flight |
| Arrived | Passenger has arrived at destination |
| No Show | Passenger did not show up |

### Adding a Passenger

1. Click **"New Passenger"**
2. Enter passenger details:
   - First and last name
   - Passport number
   - Email and phone
   - Flight assignment
   - Seat number
   - Checked bags count
3. Click **"Create Passenger"**

### Passenger Check-In

1. Find the passenger in the list
2. Click on passenger name
3. Click **"Check In"**
4. Update seat assignment if needed
5. Record checked baggage

### Boarding Process

1. Filter passengers by flight
2. Mark passengers as **Boarded** as they board
3. Monitor boarding progress
4. Identify no-shows before departure

---

## Staff Management

### Viewing Staff

Navigate to: **Staff → Staff List**

#### Staff Roles

| Role | Description |
|------|-------------|
| Pilot | Aircraft pilot |
| Co-Pilot | Assistant pilot |
| Cabin Crew | Flight attendant |
| Ground Crew | Ground operations |
| Security | Security personnel |
| Cleaning | Cleaning staff |
| Maintenance | Maintenance personnel |

### Adding Staff Members

1. Click **"New Staff"**
2. Enter staff details:
   - First and last name
   - Employee number
   - Role
   - Certifications
   - Contact information
3. Set availability status
4. Click **"Create Staff"**

### Staff Assignments

Assign staff to flights:

1. Go to flight details page
2. Click **"Assign Staff"**
3. Select staff member
4. Choose assignment type
5. Click **"Assign"**

**Conflict Detection:** The system automatically detects and prevents:
- Double-booking of staff
- Overlapping flight assignments
- Certification mismatches

### Availability Management

Update staff availability:

1. Click on staff member
2. Toggle **"Available"** status
3. Add notes for unavailability
4. Set return date if temporary

---

## Fiscal Assessments

### Overview

Fiscal assessments track airport financial performance over specific periods.

### Creating an Assessment

1. Navigate to: **Finance → Fiscal Assessments**
2. Click **"New Assessment"**
3. Fill in assessment details:

**Basic Information:**
- Airport
- Period Type (daily, weekly, monthly, quarterly, yearly)
- Start and End dates
- Status (Draft, In Progress, Completed, Approved, Rejected)

**Revenue Fields:**
- Fuel Revenue
- Parking Revenue
- Retail Revenue
- Landing Fees
- Cargo Revenue
- Other Revenue

**Expense Fields:**
- Security Costs
- Maintenance Costs
- Operational Costs
- Staff Costs
- Utility Costs
- Other Expenses

**Operational Metrics:**
- Passenger Count
- Flight Count

4. Click **"Create Assessment"**

### Assessment Workflow

```
┌─────────┐    ┌─────────────┐    ┌───────────┐    ┌──────────┐
│  Draft  │───>│ In Progress │───>│ Completed │───>│ Approved │
└─────────┘    └─────────────┘    └───────────┘    └──────────┘
                                       │
                                       ▼
                                   ┌──────────┐
                                   │ Rejected │
                                   └──────────┘
```

### Editing Assessments

1. Click on assessment in the list
2. Click **"Edit"** (Editor role or above required)
3. Update fields as needed
4. Click **"Save Changes"**

**Note:** Totals are automatically calculated when you save.

### Approval Process

Approvers can approve or reject assessments:

1. Open the assessment
2. Click **"Approve/Reject"**
3. Select decision
4. Add comments (optional)
5. Click **"Submit"**

**Permissions:** Only users with Approver role or above can approve.

### Print View

Generate a printable version:

1. Open the assessment
2. Click **"Print"**
3. Use browser print function

---

## Reports & Documents

### Report Types

| Type | Description |
|------|-------------|
| Fiscal Summary | Financial performance summary |
| Operational | Flight operations report |
| Passenger | Passenger statistics |
| Financial | Detailed financial breakdown |
| Performance | KPI and metrics report |
| Compliance | Regulatory compliance report |

### Creating a Report

1. Navigate to: **Reports → Reports**
2. Click **"New Report"**
3. Fill in report details:
   - Title
   - Report Type
   - Airport
   - Period (start and end dates)
   - Output Format (HTML, PDF, CSV, JSON)
   - Description
4. Click **"Create Report"**

**Background Processing:** Reports are generated in the background. You'll be notified when complete.

### Report Scheduling

Automate report generation:

1. Navigate to: **Reports → Scheduled Reports**
2. Click **"New Schedule"**
3. Configure schedule:
   - Name
   - Report Type
   - Airport
   - Frequency (daily, weekly, monthly)
   - Day/Time
   - Recipients (comma-separated emails)
   - Format
4. Click **"Create Schedule"**

### Scheduled Report Management

| Action | Description |
|--------|-------------|
| **Edit** | Modify schedule settings |
| **Run Now** | Generate report immediately |
| **Delete** | Remove the schedule |
| **Toggle Active** | Enable/disable schedule |

### Document Management

Create and manage document templates:

1. Navigate to: **Documents → Documents**
2. Click **"New Document"**
3. Fill in document details:
   - Name
   - Document Type (invoice, receipt, certificate, etc.)
   - Associated Airport
   - Content (JSON format)
   - Template flag
4. Click **"Create Document"**

### Document Export

Export documents in various formats:

1. Open the document
2. Click **"Export"**
3. Select format
4. Download or email

---

## Analytics

### Analytics Dashboard

Navigate to: **Analytics**

#### Available Metrics

- **Revenue Trends:** Revenue over time
- **Passenger Trends:** Passenger counts over time
- **Flight Statistics:** Flight volume and performance
- **Gate Utilization:** Gate usage patterns
- **Delay Analysis:** Delay causes and patterns

### Interactive Charts

- **Time Range Selector:** Choose date range
- **Metric Toggle:** Switch between metrics
- **Zoom:** Click and drag to zoom
- **Export:** Download chart as image

### Airport Comparison

Compare multiple airports:

1. Navigate to: **Analytics → Airport Comparison**
2. Select airports to compare
3. Choose metrics
4. View side-by-side comparison

### Trend Analysis

View historical trends:

1. Select metric
2. Choose time period
3. View trend chart with:
   - Historical data
   - Trend line
   - Year-over-year comparison

---

## Activity Logs

### Viewing Activity Logs

Navigate to: **Activity Logs**

#### Log Entries

Each log entry shows:
- Timestamp
- Event type
- Action performed
- User who performed it
- Affected object
- Severity level
- IP address

### Filtering Logs

Filter by:
- **Event Type:** flight, gate, fiscal_assessment, etc.
- **Action:** create, update, delete, approve, etc.
- **Severity:** info, warning, error
- **Date Range:** From/to dates
- **User:** Specific user

### Log Severity Levels

| Level | Description |
|-------|-------------|
| Info | Normal operations |
| Warning | Potential issues |
| Error | Errors requiring attention |

### Export Logs

Export activity logs:
1. Apply desired filters
2. Click **"Export"**
3. Choose format (CSV, JSON)
4. Download file

---

## Public Portals

### Flight Status Portal

Access: `/core/flights/status/` (no login required)

**Features:**
- Search by flight number
- View all flights by date
- Real-time status updates
- Gate information
- Departure/arrival times

### Baggage Tracking

Access: `/core/baggage/track/` (no login required)

**Features:**
- Track baggage by ID
- View baggage status
- Claim information
- Lost baggage reporting

---

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Open search |
| `Ctrl + R` | Refresh current page |
| `Ctrl + /` | Show keyboard shortcuts |
| `Esc` | Close modal/dialog |
| `?` | Show help |

### Navigation Shortcuts

| Shortcut | Action |
|----------|--------|
| `G then D` | Go to Dashboard |
| `G then F` | Go to Flights |
| `G then G` | Go to Gates |
| `G then A` | Go to Analytics |

### Form Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save form |
| `Ctrl + Enter` | Submit form |
| `Tab` | Next field |
| `Shift + Tab` | Previous field |

---

## Notifications

### Browser Notifications

The application can send browser notifications for:

- Flight status changes
- Gate assignments
- Approval requests
- Report completion
- System alerts

### Enabling Notifications

1. Click the notification bell icon
2. Click **"Enable Notifications"**
3. Grant browser permission
4. Configure notification preferences

### Notification Settings

Configure what notifications you receive:

1. Go to **Profile → Settings**
2. Navigate to **Notifications** tab
3. Toggle notification types:
   - Flight updates
   - Gate changes
   - Approval requests
   - Report completions
   - System alerts
4. Click **"Save Preferences"**

### WebSocket Connection

Real-time notifications require WebSocket connection:

- **Connected:** Real-time updates enabled
- **Disconnected:** Check connection, refresh page

---

## Mobile Usage

### Responsive Design

The application is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones

### Mobile Features

- Touch-friendly interface
- Swipe gestures for navigation
- Mobile-optimized forms
- Responsive charts

### Best Practices

- Use landscape mode for data entry
- Pinch to zoom on charts
- Use search for quick access
- Enable notifications for updates

---

## Accessibility

### WCAG 2.1 AA Compliance

The application meets WCAG 2.1 AA standards:

- **Keyboard Navigation:** All features accessible via keyboard
- **Screen Reader Support:** Proper ARIA labels
- **Color Contrast:** Minimum 4.5:1 contrast ratio
- **Focus Indicators:** Visible focus on all interactive elements
- **Skip Links:** Skip to main content

### Accessibility Features

| Feature | Description |
|---------|-------------|
| Skip Navigation | Skip to main content link |
| High Contrast | Theme with enhanced contrast |
| Reduced Motion | Reduced animations option |
| Text Resizing | Text resizable up to 200% |
| Screen Reader | Optimized for screen readers |

---

## Tips & Best Practices

### General Tips

1. **Use Search:** Quick access to flights, passengers, staff
2. **Bookmark Frequently Used Pages:** Save time on navigation
3. **Set Up Notifications:** Stay informed of important changes
4. **Use Keyboard Shortcuts:** Faster workflow
5. **Review Activity Logs:** Monitor system changes

### Data Entry Best Practices

1. **Complete All Required Fields:** Avoid validation errors
2. **Use Consistent Formats:** Especially for names and codes
3. **Add Notes:** Document important changes
4. **Review Before Saving:** Double-check entries
5. **Save Frequently:** Avoid data loss

### Performance Tips

1. **Use Filters:** Reduce data load on lists
2. **Limit Date Ranges:** Shorter ranges load faster
3. **Clear Browser Cache:** If experiencing issues
4. **Use Wired Connection:** For stable WebSocket

---

*Last Updated: March 24, 2026*
*Version: 1.0*
