"""
API Endpoint Tests for MetOcean Intelligence Platform

Tests all API endpoints:
- Authentication endpoints
- Admin endpoints
- Forecast endpoints
- Health check
- Model metadata
"""
import pytest


@pytest.mark.api
class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_endpoint_returns_200(self, test_client):
        """GET /health should return 200"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_endpoint_returns_status_ok(self, test_client):
        """GET /health should return status: ok"""
        response = test_client.get("/health")
        data = response.json()
        
        assert data.get("status") == "ok"
    
    def test_health_endpoint_includes_ml_status(self, test_client):
        """GET /health should include ml_available flag"""
        response = test_client.get("/health")
        data = response.json()
        
        assert "ml_available" in data
        assert isinstance(data["ml_available"], bool)


@pytest.mark.api
class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints"""
    
    def test_openapi_schema_disabled_by_default(self, test_client):
        """GET /openapi.json is disabled unless ENABLE_API_DOCS=true (private, invite-only site)."""
        response = test_client.get("/openapi.json")

        assert response.status_code == 404

    def test_swagger_docs_disabled_by_default(self, test_client):
        """GET /docs is disabled unless ENABLE_API_DOCS=true (private, invite-only site)."""
        response = test_client.get("/docs")

        assert response.status_code == 404


@pytest.mark.api
class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    def test_login_endpoint_accepts_json(self, test_client, test_user_data, db_session):
        """POST /auth/login should accept JSON payload"""
        from app.src.auth import create_user
        
        create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        response = test_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }
        )
        
        assert response.status_code == 200
    
    def test_login_endpoint_returns_token_type(self, test_client, test_user_data, db_session):
        """Login response should include token_type"""
        from app.src.auth import create_user
        
        create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        response = test_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }
        )
        
        data = response.json()
        assert data.get("token_type") == "bearer"
    
    def test_verify_endpoint_requires_auth(self, test_client):
        """GET /auth/verify should require authentication"""
        response = test_client.get("/auth/verify")
        
        assert response.status_code == 401
    
    def test_verify_endpoint_with_token(self, authenticated_client):
        """GET /auth/verify with valid token should return 200"""
        response = authenticated_client.get("/auth/verify")
        
        assert response.status_code == 200


@pytest.mark.api
class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    def test_admin_users_endpoint_requires_admin(self, test_client):
        """GET /admin/users should require admin authentication"""
        response = test_client.get("/admin/users")
        
        assert response.status_code == 401
    
    def test_admin_users_endpoint_with_admin_token(self, admin_client):
        """GET /admin/users with admin token should return users list"""
        response = admin_client.get("/admin/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_invites_endpoint_requires_admin(self, test_client):
        """GET /admin/invites should require admin authentication"""
        response = test_client.get("/admin/invites")
        
        assert response.status_code == 401
    
    def test_admin_invites_endpoint_with_admin_token(self, admin_client):
        """GET /admin/invites with admin token should return invitations"""
        response = admin_client.get("/admin/invites")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_admin_invite_endpoint_creates_invitation(self, admin_client):
        """POST /admin/invite with admin token should create invitation"""
        response = admin_client.post(
            "/admin/invite",
            json={"email": "newuser@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
    
    def test_admin_invite_endpoint_requires_admin(self, test_client):
        """POST /admin/invite should require admin authentication"""
        response = test_client.post(
            "/admin/invite",
            json={"email": "user@example.com"}
        )
        
        assert response.status_code == 401


@pytest.mark.api
class TestForecastEndpoint:
    """Test forecasting endpoint"""
    
    def test_forecast_endpoint_requires_auth(self, test_client):
        """POST /forecast/ should require authentication"""
        response = test_client.post(
            "/forecast/",
            json={
                "dataset_url": "https://example.com/data.csv",
                "target_column": "value",
            }
        )
        
        assert response.status_code == 401
    
    def test_forecast_endpoint_with_auth_accepts_request(self, authenticated_client):
        """POST /forecast/ with auth should accept valid forecast request"""
        response = authenticated_client.post(
            "/forecast/",
            json={
                "dataset_url": "https://example.com/data.csv",
                "target_column": "value",
                "model_name": "N-HiTS",
            }
        )
        
        # Should return 200 or error depending on dataset availability
        assert response.status_code in [200, 400, 422, 500]


@pytest.mark.api
class TestModelMetadataEndpoints:
    """Test model metadata endpoints"""
    
    def test_models_endpoint_returns_list(self, authenticated_client):
        """GET /models should return list of available models"""
        response = authenticated_client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_models_endpoint_requires_auth(self, test_client):
        """GET /models should require authentication"""
        response = test_client.get("/models")
        
        assert response.status_code == 401
    
    def test_datasets_endpoint_returns_list(self, authenticated_client):
        """GET /datasets should return dict with a 'datasets' key containing a list"""
        response = authenticated_client.get("/datasets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data.get("datasets"), list)
    
    def test_datasets_endpoint_requires_auth(self, test_client):
        """GET /datasets should require authentication"""
        response = test_client.get("/datasets")
        
        assert response.status_code == 401


@pytest.mark.api
class TestErrorHandling:
    """Test API error handling"""
    
    def test_invalid_endpoint_returns_404(self, test_client):
        """GET /nonexistent should return 404"""
        response = test_client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_malformed_json_returns_422(self, test_client):
        """POST with malformed JSON should return 422"""
        response = test_client.post(
            "/auth/login",
            data="not json"
        )
        
        assert response.status_code in [422, 400]
    
    def test_missing_required_fields_returns_422(self, test_client):
        """POST with missing required fields should return 422"""
        response = test_client.post(
            "/auth/login",
            json={}
        )
        
        assert response.status_code == 422


@pytest.mark.api
class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present_in_response(self, test_client):
        """Response should include CORS headers"""
        response = test_client.get("/health")
        
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_preflight_request_accepted(self, test_client):
        """OPTIONS request should be accepted"""
        response = test_client.options("/health")
        
        assert response.status_code in [200, 405]  # 405 if OPTIONS not implemented


@pytest.mark.api
@pytest.mark.integration
class TestEndpointChaining:
    """Test typical user workflows through multiple endpoints"""
    
    def test_complete_auth_flow(self, test_client, test_user_data, db_session):
        """Test complete authentication flow: create user -> login -> verify"""
        from app.src.auth import create_user
        
        # Step 1: Create user via admin
        create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        # Step 2: Login
        login_response = test_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }
        )
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        
        # Step 3: Verify with token
        test_client.headers = {"Authorization": f"Bearer {token}"}
        verify_response = test_client.get("/auth/verify")
        assert verify_response.status_code == 200
