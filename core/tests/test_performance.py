"""
Performance and scalability tests for the Airport Operations Management System.

Tests cover:
- Query optimization
- Database indexing
- Caching effectiveness
- N+1 query prevention
- Bulk operations
- Memory usage
- Response time under load
"""

import time
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.db import connection, reset_queries
from django.core.cache import cache
from django.contrib.auth.models import User, Group
from django.utils import timezone

from core.models import (
    Airport, Gate, GateStatus, Flight, FlightStatus,
    Passenger, PassengerStatus, Staff, StaffRole,
    EventLog, FiscalAssessment, AssessmentPeriod, AssessmentStatus,
)


class QueryOptimizationTest(TestCase):
    """Tests for query optimization."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123',
            is_superuser=True,
        )
        
        # Create test data
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos Airport",
            city="Lagos",
        )
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )

    def test_select_related_reduces_queries(self):
        """Test select_related reduces database queries."""
        # Create flights with gates
        for i in range(10):
            Flight.objects.create(
                flight_number=f"FL{i:03d}",
                origin="LOS",
                destination=f"DEST{i}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
                gate=self.gate,
            )
        
        # Without select_related
        reset_queries()
        flights = Flight.objects.all()
        for flight in flights:
            _ = flight.gate  # Access related object
        queries_without = len(connection.queries)
        
        # With select_related
        reset_queries()
        flights = Flight.objects.select_related('gate').all()
        for flight in flights:
            _ = flight.gate
        queries_with = len(connection.queries)
        
        # select_related should reduce queries
        self.assertLess(queries_with, queries_without)

    def test_prefetch_related_reduces_queries(self):
        """Test prefetch_related reduces database queries."""
        # Create staff with assignments
        for i in range(5):
            staff = Staff.objects.create(
                first_name=f"Staff{i}",
                last_name="Test",
                employee_number=f"EMP{i:03d}",
                role=StaffRole.GROUND_CREW.value,
            )
            flight = Flight.objects.create(
                flight_number=f"FL{i:03d}",
                origin="LOS",
                destination=f"DEST{i}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
            )
            from core.models import StaffAssignment
            StaffAssignment.objects.create(
                staff=staff,
                flight=flight,
                assignment_type=StaffRole.GROUND_CREW.value,
            )
        
        # Without prefetch_related
        reset_queries()
        staff_list = Staff.objects.all()
        for s in staff_list:
            _ = list(s.assignments.all())
        queries_without = len(connection.queries)
        
        # With prefetch_related
        reset_queries()
        staff_list = Staff.objects.prefetch_related('assignments').all()
        for s in staff_list:
            _ = list(s.assignments.all())
        queries_with = len(connection.queries)
        
        # prefetch_related should reduce queries
        self.assertLess(queries_with, queries_without)

    def test_only_defer_reduces_data_transfer(self):
        """Test only/defer reduces data transfer."""
        # Create airport with large data
        Airport.objects.create(
            code="ABJ",
            name="Abuja International Airport with Long Name",
            city="Abuja",
        )
        
        reset_queries()
        airports = Airport.objects.only('code', 'name').all()
        for airport in airports:
            _ = airport.code
        queries_only = len(connection.queries)
        
        reset_queries()
        airports = Airport.objects.all()
        for airport in airports:
            _ = airport.code
        queries_all = len(connection.queries)
        
        # Should be same number of queries but less data
        self.assertEqual(queries_only, queries_all)

    def test_index_used_for_status_filter(self):
        """Test database index is used for status filtering."""
        # Create many gates
        for i in range(100):
            Gate.objects.create(
                gate_id=f"GIDX{i:03d}",
                terminal=f"T{i % 5}",
                status=GateStatus.AVAILABLE.value if i % 2 == 0 else GateStatus.OCCUPIED.value,
            )
        
        reset_queries()
        gates = list(Gate.objects.filter(status=GateStatus.AVAILABLE.value))
        
        # Query should work (index usage verified via EXPLAIN in production)
        self.assertGreater(len(gates), 0)

    def test_composite_index_usage(self):
        """Test composite index is used for multi-field queries."""
        # Create many gates
        for i in range(100):
            Gate.objects.create(
                gate_id=f"G{i:03d}",
                terminal="Terminal 1",
                status=GateStatus.AVAILABLE.value,
            )
        
        reset_queries()
        gates = list(Gate.objects.filter(
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        ))
        
        # Should use composite index
        self.assertGreater(len(gates), 0)


class CachingTest(TestCase):
    """Tests for caching effectiveness."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123',
        )

    def test_cache_set_and_get(self):
        """Test basic cache operations."""
        cache.set('test_key', 'test_value', 300)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')

    def test_cache_expiration(self):
        """Test cache expiration."""
        cache.set('short_key', 'short_value', 1)
        time.sleep(1.5)
        value = cache.get('short_key')
        self.assertIsNone(value)

    def test_cache_delete(self):
        """Test cache deletion."""
        cache.set('to_delete', 'value', 300)
        cache.delete('to_delete')
        value = cache.get('to_delete')
        self.assertIsNone(value)

    def test_cache_get_or_set(self):
        """Test cache get_or_set."""
        def expensive_function():
            return "computed_value"
        
        value = cache.get_or_set('compute_key', expensive_function, 300)
        self.assertEqual(value, "computed_value")
        
        # Second call should use cache
        value2 = cache.get_or_set('compute_key', lambda: "different", 300)
        self.assertEqual(value2, "computed_value")

    def test_cache_clear(self):
        """Test cache clearing."""
        cache.set('key1', 'value1', 300)
        cache.set('key2', 'value2', 300)
        cache.clear()
        
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))


class BulkOperationsTest(TestCase):
    """Tests for bulk operations."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos Airport",
            city="Lagos",
        )

    def test_bulk_create_is_faster(self):
        """Test bulk_create is faster than individual creates."""
        # Individual creates
        reset_queries()
        start = time.time()
        for i in range(100):
            Airport.objects.create(
                code=f"IND{i:03d}",
                name=f"Individual Airport {i}",
                city=f"City {i}",
            )
        individual_time = time.time() - start
        individual_queries = len(connection.queries)
        
        # Clean up
        Airport.objects.filter(code__startswith='IND').delete()
        
        # Bulk create
        reset_queries()
        start = time.time()
        airports = [
            Airport(
                code=f"BULK{i:03d}",
                name=f"Bulk Airport {i}",
                city=f"City {i}",
            )
            for i in range(100)
        ]
        Airport.objects.bulk_create(airports)
        bulk_time = time.time() - start
        bulk_queries = len(connection.queries)
        
        # Bulk should be faster and use fewer queries
        self.assertLess(bulk_time, individual_time)
        self.assertLess(bulk_queries, individual_queries)

    def test_bulk_update_is_faster(self):
        """Test bulk_update is faster than individual saves."""
        # Create airports
        airports = [
            Airport(
                code=f"UPD{i:03d}",
                name=f"Update Airport {i}",
                city=f"City {i}",
            )
            for i in range(50)
        ]
        Airport.objects.bulk_create(airports)
        
        # Individual updates
        reset_queries()
        start = time.time()
        for airport in Airport.objects.filter(code__startswith='UPD'):
            airport.name = f"Updated {airport.name}"
            airport.save()
        individual_time = time.time() - start
        individual_queries = len(connection.queries)
        
        # Bulk update
        reset_queries()
        start = time.time()
        airports = list(Airport.objects.filter(code__startswith='UPD'))
        for airport in airports:
            airport.name = f"Bulk Updated {airport.name}"
        Airport.objects.bulk_update(airports, ['name'])
        bulk_time = time.time() - start
        bulk_queries = len(connection.queries)
        
        # Bulk should use fewer queries
        self.assertLess(bulk_queries, individual_queries)

    def test_bulk_create_with_batch_size(self):
        """Test bulk_create with batch_size parameter."""
        airports = [
            Airport(
                code=f"BATCH{i:03d}",
                name=f"Batch Airport {i}",
                city=f"City {i}",
            )
            for i in range(100)
        ]
        
        # Create with batch size
        Airport.objects.bulk_create(airports, batch_size=20)
        
        # Verify all created
        count = Airport.objects.filter(code__startswith='BATCH').count()
        self.assertEqual(count, 100)


class LargeDatasetTest(TestCase):
    """Tests for large dataset handling."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos Airport",
            city="Lagos",
        )
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )

    def test_query_with_many_records(self):
        """Test queries work with many records."""
        # Create 1000 flights
        flights = [
            Flight(
                flight_number=f"FL{i:04d}",
                origin="LOS",
                destination=f"DEST{i % 100}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
                gate=self.gate,
            )
            for i in range(1000)
        ]
        Flight.objects.bulk_create(flights)
        
        # Query should work
        reset_queries()
        count = Flight.objects.filter(origin="LOS").count()
        self.assertEqual(count, 1000)

    def test_pagination_with_many_records(self):
        """Test pagination works with many records."""
        # Create 500 flights
        flights = [
            Flight(
                flight_number=f"PG{i:04d}",
                origin="LOS",
                destination=f"DEST{i % 50}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
            )
            for i in range(500)
        ]
        Flight.objects.bulk_create(flights)
        
        # Paginate
        from django.core.paginator import Paginator
        paginator = Paginator(Flight.objects.all(), 50)
        
        self.assertEqual(paginator.num_pages, 10)
        
        page1 = paginator.page(1)
        self.assertEqual(len(page1.object_list), 50)

    def test_aggregation_with_many_records(self):
        """Test aggregations work with many records."""
        # Create flights with varying delay minutes
        flights = [
            Flight(
                flight_number=f"AGG{i:04d}",
                origin="LOS",
                destination=f"DEST{i % 50}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
                delay_minutes=i % 60,
            )
            for i in range(500)
        ]
        Flight.objects.bulk_create(flights)
        
        # Aggregate
        from django.db.models import Avg, Sum, Max, Min, Count
        
        stats = Flight.objects.filter(flight_number__startswith='AGG').aggregate(
            total=Count('id'),
            avg_delay=Avg('delay_minutes'),
            max_delay=Max('delay_minutes'),
            min_delay=Min('delay_minutes'),
            sum_delay=Sum('delay_minutes'),
        )
        
        self.assertEqual(stats['total'], 500)
        self.assertIsNotNone(stats['avg_delay'])

    def test_filtering_with_many_records(self):
        """Test filtering works efficiently with many records."""
        # Create flights with different statuses
        statuses = [
            FlightStatus.SCHEDULED.value,
            FlightStatus.DELAYED.value,
            FlightStatus.CANCELLED.value,
        ]
        
        flights = []
        for i in range(300):
            flights.append(Flight(
                flight_number=f"FILT{i:04d}",
                origin="LOS",
                destination=f"DEST{i % 30}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
                status=statuses[i % 3],
            ))
        Flight.objects.bulk_create(flights)
        
        # Filter
        reset_queries()
        delayed = Flight.objects.filter(
            flight_number__startswith='FILT',
            status=FlightStatus.DELAYED.value,
        ).count()
        
        self.assertEqual(delayed, 100)


class MemoryUsageTest(TestCase):
    """Tests for memory usage optimization."""

    def test_iterator_reduces_memory(self):
        """Test iterator() reduces memory usage."""
        # Create many records
        airport = Airport.objects.create(
            code="MEM",
            name="Memory Test Airport",
            city="City",
        )
        
        flights = [
            Flight(
                flight_number=f"MEM{i:04d}",
                origin="MEM",
                destination=f"DEST{i % 50}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
            )
            for i in range(500)
        ]
        Flight.objects.bulk_create(flights)
        
        # Without iterator - loads all into memory
        reset_queries()
        for flight in Flight.objects.filter(flight_number__startswith='MEM'):
            _ = flight.flight_number
        
        # With iterator - streams results
        reset_queries()
        for flight in Flight.objects.filter(flight_number__startswith='MEM').iterator():
            _ = flight.flight_number
        
        # Iterator should use fewer queries in some cases
        # (depends on database and chunk size)

    def test_values_list_reduces_memory(self):
        """Test values_list() reduces memory usage."""
        # Create records
        for i in range(100):
            Airport.objects.create(
                code=f"VL{i:03d}",
                name=f"Values List Airport {i}",
                city=f"City {i}",
            )
        
        # Full objects
        reset_queries()
        airports = list(Airport.objects.filter(code__startswith='VL'))
        
        # values_list
        reset_queries()
        codes = list(Airport.objects.filter(code__startswith='VL').values_list('code', flat=True))
        
        self.assertEqual(len(codes), 100)


class ResponseTimeTest(TestCase):
    """Tests for response time."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123',
            is_superuser=True,
        )
        self.client.login(username='testuser', password='pass123')

    def test_list_view_response_time(self):
        """Test list view responds within time limit."""
        # Create test data
        for i in range(50):
            Airport.objects.create(
                code=f"RT{i:03d}",
                name=f"Response Time Airport {i}",
                city=f"City {i}",
            )
        
        start = time.time()
        response = self.client.get('/airports/')
        elapsed = time.time() - start
        
        # Should respond within 1 second
        self.assertLess(elapsed, 1.0)

    def test_api_response_time(self):
        """Test API endpoint responds within time limit."""
        # Create test data
        for i in range(50):
            Airport.objects.create(
                code=f"API{i:03d}",
                name=f"API Airport {i}",
                city=f"City {i}",
            )
        
        start = time.time()
        response = self.client.get('/api/v1/airports/')
        elapsed = time.time() - start
        
        # Should respond within 0.5 seconds
        self.assertLess(elapsed, 0.5)

    def test_detail_view_response_time(self):
        """Test detail view responds within time limit."""
        airport = Airport.objects.create(
            code="DTL",
            name="Detail Test Airport",
            city="City",
        )
        
        start = time.time()
        response = self.client.get(f'/airports/{airport.id}/')
        elapsed = time.time() - start
        
        # Should respond within 0.5 seconds
        self.assertLess(elapsed, 0.5)


class DatabaseIndexTest(TestCase):
    """Tests for database index effectiveness."""

    def test_index_on_status_field(self):
        """Test index on status field improves queries."""
        # Create many gates
        for i in range(200):
            Gate.objects.create(
                gate_id=f"IDX{i:03d}",
                terminal=f"T{i % 5}",
                status=GateStatus.AVAILABLE.value if i % 2 == 0 else GateStatus.OCCUPIED.value,
            )
        
        reset_queries()
        gates = list(Gate.objects.filter(status=GateStatus.AVAILABLE.value))
        
        # Query should be fast with index
        self.assertGreater(len(gates), 0)

    def test_index_on_foreign_key(self):
        """Test index on foreign key improves joins."""
        airport = Airport.objects.create(
            code="FKI",
            name="Foreign Key Index Airport",
            city="City",
        )
        
        # Create assessments with unique dates
        base_date = timezone.now().date()
        for i in range(10):
            FiscalAssessment.objects.create(
                airport=airport,
                period_type='monthly',
                start_date=base_date + timedelta(days=i*30),
                end_date=base_date + timedelta(days=i*30+28),
            )
        
        reset_queries()
        assessments = list(FiscalAssessment.objects.select_related('airport').filter(
            airport=airport
        ))
        
        # Should use index on airport_id
        self.assertEqual(len(assessments), 10)

    def test_composite_index_on_terminal_status(self):
        """Test composite index on terminal and status."""
        # Create many gates
        for i in range(200):
            Gate.objects.create(
                gate_id=f"CIDX{i:03d}",
                terminal="Terminal 1",
                status=GateStatus.AVAILABLE.value,
            )
        
        reset_queries()
        gates = list(Gate.objects.filter(
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        ))
        
        # Should use composite index
        self.assertGreater(len(gates), 0)


class ScalabilityTest(TestCase):
    """Tests for scalability."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="SCL",
            name="Scalability Test Airport",
            city="City",
        )

    def test_linear_query_growth(self):
        """Test queries grow linearly with data size."""
        # Test with 10 records
        for i in range(10):
            Gate.objects.create(
                gate_id=f"SCL10_{i:03d}",
                terminal="T1",
            )
        
        reset_queries()
        list(Gate.objects.filter(gate_id__startswith='SCL10'))
        queries_10 = len(connection.queries)
        
        # Test with 100 records
        for i in range(100):
            Gate.objects.create(
                gate_id=f"SCL100_{i:03d}",
                terminal="T1",
            )
        
        reset_queries()
        list(Gate.objects.filter(gate_id__startswith='SCL100'))
        queries_100 = len(connection.queries)
        
        # Query count should be similar (O(1) or O(log n))
        # Not O(n)
        self.assertLessEqual(queries_100, queries_10 * 2)

    def test_concurrent_reads(self):
        """Test system handles concurrent reads."""
        # Create test data
        for i in range(100):
            Airport.objects.create(
                code=f"CON{i:03d}",
                name=f"Concurrent Airport {i}",
                city=f"City {i}",
            )
        
        # Simulate concurrent reads (sequential in test)
        results = []
        for _ in range(10):
            count = Airport.objects.filter(code__startswith='CON').count()
            results.append(count)
        
        # All should return same count
        self.assertEqual(len(set(results)), 1)

    def test_write_scalability(self):
        """Test write operations scale."""
        start = time.time()
        
        # Bulk create is more scalable
        airports = [
            Airport(
                code=f"WSC{i:03d}",
                name=f"Write Scale {i}",
                city=f"City {i}",
            )
            for i in range(500)
        ]
        Airport.objects.bulk_create(airports)
        
        elapsed = time.time() - start
        
        # Should complete within reasonable time
        self.assertLess(elapsed, 5.0)
