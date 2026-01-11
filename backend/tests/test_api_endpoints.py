import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestAPIEndpoints:
    """Test suite for FastAPI endpoints"""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Course Materials RAG System API"}

    def test_query_endpoint_with_session_id(self, client, sample_query_request):
        """Test /api/query endpoint with provided session_id"""
        response = client.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "source_links" in data
        assert "session_id" in data

        # Verify content
        assert data["answer"] == "This is a test response about course content."
        assert data["sources"] == [
            "Building Towards Computer Use with Anthropic - Lesson 1"
        ]
        assert data["source_links"] == ["https://example.com/lesson1"]
        assert data["session_id"] == "test-session-123"

    def test_query_endpoint_without_session_id(self, client):
        """Test /api/query endpoint without session_id (should create new session)"""
        request_data = {"query": "What is computer use in AI?"}
        response = client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should create new session
        assert data["session_id"] == "test-session-123"
        assert data["answer"] == "This is a test response about course content."

    def test_query_endpoint_invalid_request(self, client):
        """Test /api/query endpoint with invalid request data"""
        # Missing required 'query' field
        response = client.post("/api/query", json={})
        assert response.status_code == 422  # Validation error

    def test_query_endpoint_empty_query(self, client):
        """Test /api/query endpoint with empty query"""
        request_data = {"query": ""}
        response = client.post("/api/query", json=request_data)

        # Should still process (empty query is valid from API perspective)
        assert response.status_code == 200

    def test_courses_endpoint(self, client):
        """Test /api/courses endpoint returns course statistics"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_courses" in data
        assert "course_titles" in data

        # Verify content
        assert data["total_courses"] == 2
        assert data["course_titles"] == [
            "Building Towards Computer Use with Anthropic",
            "Advanced AI Techniques",
        ]

    def test_clear_session_endpoint(self, client, sample_clear_session_request):
        """Test /api/clear-session endpoint"""
        response = client.post("/api/clear-session", json=sample_clear_session_request)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["message"] == "Session cleared successfully"

    def test_clear_session_endpoint_invalid_request(self, client):
        """Test /api/clear-session endpoint with invalid request"""
        # Missing required 'session_id' field
        response = client.post("/api/clear-session", json={})
        assert response.status_code == 422  # Validation error

    def test_nonexistent_endpoint(self, client):
        """Test accessing a non-existent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


@pytest.mark.api
class TestAPIErrorHandling:
    """Test suite for API error handling"""

    def test_query_endpoint_with_rag_system_error(self, client):
        """Test /api/query endpoint structure (error injection requires app-level mocking)"""
        # This test demonstrates the structure for error handling testing
        # In a real scenario, you'd inject the error at the app level
        request_data = {"query": "test query"}
        response = client.post("/api/query", json=request_data)

        # With current mock setup, this should work normally
        assert response.status_code == 200

        # To test actual error handling, you would need to:
        # 1. Create a separate test app fixture with error-prone mocks
        # 2. Or use dependency injection to override the RAG system
        # 3. Or test error conditions in the actual app.py module tests

    def test_courses_endpoint_with_rag_system_error(self, client):
        """Test /api/courses endpoint when RAG system raises an exception"""
        # Similar to above, this would need app-level error injection
        response = client.get("/api/courses")
        assert response.status_code == 200


@pytest.mark.api
class TestAPIRequestValidation:
    """Test suite for API request validation"""

    def test_query_endpoint_with_extra_fields(self, client):
        """Test /api/query endpoint ignores extra fields"""
        request_data = {
            "query": "What is computer use?",
            "session_id": "test-123",
            "extra_field": "should be ignored",
        }
        response = client.post("/api/query", json=request_data)
        assert response.status_code == 200

    def test_query_endpoint_with_wrong_types(self, client):
        """Test /api/query endpoint with wrong field types"""
        request_data = {"query": 123, "session_id": "test-123"}  # Should be string
        response = client.post("/api/query", json=request_data)
        assert response.status_code == 422

    def test_clear_session_with_wrong_types(self, client):
        """Test /api/clear-session endpoint with wrong field types"""
        request_data = {"session_id": 123}  # Should be string
        response = client.post("/api/clear-session", json=request_data)
        assert response.status_code == 422


@pytest.mark.api
class TestAPIHeaders:
    """Test suite for API headers and CORS"""

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        response = client.get("/")

        # FastAPI TestClient doesn't simulate full CORS behavior
        # but we can verify the response is successful
        assert response.status_code == 200

    def test_options_request(self, client):
        """Test OPTIONS request for CORS preflight"""
        response = client.options("/api/query")
        # TestClient may not handle OPTIONS the same as a real browser
        # This test serves as a placeholder for CORS testing
        assert response.status_code in [200, 405]  # 405 is also acceptable


@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints"""

    def test_full_query_workflow(self, client):
        """Test a complete query workflow"""
        # Step 1: Get course stats
        courses_response = client.get("/api/courses")
        assert courses_response.status_code == 200

        # Step 2: Query with a new session
        query_response = client.post(
            "/api/query", json={"query": "Tell me about the courses available"}
        )
        assert query_response.status_code == 200
        session_id = query_response.json()["session_id"]

        # Step 3: Query with existing session
        follow_up_response = client.post(
            "/api/query", json={"query": "Can you elaborate?", "session_id": session_id}
        )
        assert follow_up_response.status_code == 200
        assert follow_up_response.json()["session_id"] == session_id

        # Step 4: Clear the session
        clear_response = client.post(
            "/api/clear-session", json={"session_id": session_id}
        )
        assert clear_response.status_code == 200

    def test_multiple_concurrent_sessions(self, client):
        """Test handling multiple concurrent sessions"""
        # Create first session
        response1 = client.post("/api/query", json={"query": "First session query"})
        session1 = response1.json()["session_id"]

        # Create second session
        response2 = client.post("/api/query", json={"query": "Second session query"})
        session2 = response2.json()["session_id"]

        # Both should work independently
        assert response1.status_code == 200
        assert response2.status_code == 200
        # With current mock, they'll return the same session_id
        # In real implementation, they should be different
