"""
MetOcean Intelligence Platform - Test Suite

Comprehensive test coverage for:
- Authentication and authorization
- Email service
- API endpoints
- Forecasting functionality
- Database operations

To run tests:
    pytest app/tests/ -v                          # All tests
    pytest app/tests/test_auth.py -v              # Auth tests only
    pytest app/tests/ -v -m "unit"                # Unit tests only
    pytest app/tests/ -v -m "integration"         # Integration tests only
    pytest app/tests/ --cov=app.src --cov-report=html  # With coverage
"""

__version__ = "2.1.0"
__author__ = "MetOcean Intelligence Team"
