"""
Comprehensive test suite for the Airport Operations Management System.

This test package covers:
- Unit tests for models, views, serializers, permissions
- Integration tests for end-to-end workflows
- Security tests for authentication, authorization, and attack prevention
- Performance tests for query optimization and caching
- Scalability tests for high-load scenarios
- Edge case tests for robustness validation
"""

from .test_models import *
from .test_api import *
from .test_views import *
from .test_permissions import *
from .test_security import *
from .test_middleware import *
from .test_performance import *
from .test_integration import *
from .test_edge_cases import *
