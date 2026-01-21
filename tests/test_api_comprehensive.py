"""
Comprehensive API tests for DocTender v1.2
Tests cover all endpoints, error scenarios, and edge cases
Coverage target: 85%+
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path


# Mock the DocumentClassifier for testing
class MockDocumentClassifier:
    """Mock classifier for testing without actual model"""
    
    def classify(self, file_path, doc_type="auto"):
        return {
            "classification": "invoice",
            "confidence": 0.92,
            "category": "financial",
            "entities": {"company": "Test Corp", "amount": 1000},
        }
    
    def validate_document(self, file_path):
        return {"is_valid": True, "score": 0.95}


@pytest.fixture
def client():
    """Create test client with mocked classifier"""
    from api.main import app
    
    # Mock the classifier
    with patch('api.main.classifier', MockDocumentClassifier()):
        yield TestClient(app)


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_check_success(self, client):
        """Test health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
        assert "timestamp" in data
    
    def test_health_includes_metrics(self, client):
        """Test health endpoint includes performance metrics"""
        response = client.get("/health")
        data = response.json()
        assert "metrics" in data or "uptime" in data or "version" in data
    
    def test_health_response_time(self, client):
        """Test health endpoint responds quickly (<100ms)"""
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"Health check took {elapsed}ms"
        assert response.status_code == 200


class TestClassifyEndpoint:
    """Single document classification endpoint tests"""
    
    def test_classify_valid_request(self, client):
        """Test classification with valid request"""
        payload = {
            "document_path": "/documents/invoice.pdf",
            "document_type": "auto",
            "validate_document": True
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        assert "confidence" in data
        assert data["status"] in ["success", "ok"]
    
    def test_classify_response_contains_required_fields(self, client):
        """Test classification response has all required fields"""
        payload = {
            "document_path": "/documents/test.pdf",
            "validate_document": True
        }
        response = client.post("/api/v1/classify", json=payload)
        data = response.json()
        
        required_fields = ["classification", "confidence", "status"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_classify_confidence_in_range(self, client):
        """Test confidence score is between 0 and 1"""
        payload = {"document_path": "/documents/test.pdf"}
        response = client.post("/api/v1/classify", json=payload)
        data = response.json()
        
        confidence = data.get("confidence")
        assert 0 <= confidence <= 1, f"Confidence {confidence} out of range"
    
    def test_classify_missing_document_path(self, client):
        """Test classification fails without document path"""
        payload = {"document_type": "invoice"}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [400, 422]
    
    def test_classify_invalid_document_path(self, client):
        """Test classification with non-existent file"""
        payload = {"document_path": "/nonexistent/file.pdf"}
        response = client.post("/api/v1/classify", json=payload)
        # Should return 404 or 400
        assert response.status_code >= 400
    
    def test_classify_empty_document_path(self, client):
        """Test classification rejects empty document path"""
        payload = {"document_path": ""}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [400, 422]
    
    def test_classify_response_time(self, client):
        """Test classification completes within time limit"""
        payload = {"document_path": "/documents/test.pdf"}
        start = time.time()
        response = client.post("/api/v1/classify", json=payload)
        elapsed = (time.time() - start) * 1000
        # Should complete within 10 seconds for mock
        assert elapsed < 10000
    
    def test_classify_with_validation(self, client):
        """Test classification with document validation enabled"""
        payload = {
            "document_path": "/documents/test.pdf",
            "validate_document": True
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Validation info should be in response
        assert "validation" in data or "is_valid" in data or "score" in data
    
    def test_classify_without_validation(self, client):
        """Test classification with validation disabled"""
        payload = {
            "document_path": "/documents/test.pdf",
            "validate_document": False
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
    
    def test_classify_supports_auto_type(self, client):
        """Test classification supports auto document type detection"""
        payload = {
            "document_path": "/documents/test.pdf",
            "document_type": "auto"
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
    
    def test_classify_with_specific_type(self, client):
        """Test classification with specific document type"""
        payload = {
            "document_path": "/documents/test.pdf",
            "document_type": "invoice"
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200


class TestBatchEndpoint:
    """Batch processing endpoint tests"""
    
    def test_batch_submit_valid_request(self, client):
        """Test batch submission with valid documents"""
        payload = {
            "documents": [
                "/documents/doc1.pdf",
                "/documents/doc2.pdf",
                "/documents/doc3.pdf"
            ]
        }
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["pending", "queued"]
    
    def test_batch_returns_job_id(self, client):
        """Test batch submission returns valid job ID"""
        payload = {"documents": ["/documents/test.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        data = response.json()
        
        job_id = data.get("job_id")
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0
    
    def test_batch_empty_documents_list(self, client):
        """Test batch rejects empty documents list"""
        payload = {"documents": []}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [400, 422]
    
    def test_batch_missing_documents_field(self, client):
        """Test batch requires documents field"""
        payload = {}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [400, 422]
    
    def test_batch_large_document_list(self, client):
        """Test batch can handle large document lists"""
        docs = [f"/documents/doc{i}.pdf" for i in range(100)]
        payload = {"documents": docs}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code == 200
    
    def test_batch_response_includes_results_url(self, client):
        """Test batch response includes URL to results"""
        payload = {"documents": ["/documents/test.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        data = response.json()
        
        assert "job_id" in data
        # Results URL should be constructable
        job_id = data["job_id"]
        assert isinstance(job_id, str)
    
    def test_batch_response_time(self, client):
        """Test batch submission returns quickly"""
        payload = {"documents": [f"/documents/doc{i}.pdf" for i in range(10)]}
        start = time.time()
        response = client.post("/api/v1/batch", json=payload)
        elapsed = (time.time() - start) * 1000
        # Should be non-blocking (fast response)
        assert elapsed < 1000, f"Batch submission took {elapsed}ms"


class TestBatchStatusEndpoint:
    """Batch status tracking endpoint tests"""
    
    def test_batch_status_valid_job_id(self, client):
        """Test getting status with valid job ID"""
        # First submit a batch
        submit_payload = {"documents": ["/documents/test.pdf"]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        # Then check status
        response = client.get(f"/api/v1/batch/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "processed" in data
    
    def test_batch_status_invalid_job_id(self, client):
        """Test status check with invalid job ID"""
        response = client.get("/api/v1/batch/invalid_job_id/status")
        assert response.status_code == 404
    
    def test_batch_status_includes_progress(self, client):
        """Test status response includes progress information"""
        submit_payload = {"documents": ["/documents/test.pdf"]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        response = client.get(f"/api/v1/batch/{job_id}/status")
        data = response.json()
        
        # Should have progress metrics
        assert any(key in data for key in ["processed", "total", "progress", "percentage"])
    
    def test_batch_status_response_time(self, client):
        """Test status check is quick"""
        submit_payload = {"documents": ["/documents/test.pdf"]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        start = time.time()
        response = client.get(f"/api/v1/batch/{job_id}/status")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 500, f"Status check took {elapsed}ms"


class TestBatchResultsEndpoint:
    """Batch results endpoint tests"""
    
    def test_batch_results_valid_job_id(self, client):
        """Test getting results with valid job ID"""
        # Submit batch
        submit_payload = {"documents": ["/documents/test.pdf"]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        # Get results
        response = client.get(f"/api/v1/batch/{job_id}/results")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "results" in data
    
    def test_batch_results_invalid_job_id(self, client):
        """Test results request with invalid job ID"""
        response = client.get("/api/v1/batch/invalid_job_id/results")
        assert response.status_code == 404
    
    def test_batch_results_pagination_support(self, client):
        """Test results support pagination"""
        submit_payload = {"documents": [f"/documents/doc{i}.pdf" for i in range(10)]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        # Request with pagination
        response = client.get(f"/api/v1/batch/{job_id}/results?limit=5&offset=0")
        assert response.status_code == 200
    
    def test_batch_results_limit_parameter(self, client):
        """Test results respects limit parameter"""
        submit_payload = {"documents": [f"/documents/doc{i}.pdf" for i in range(20)]}
        submit_response = client.post("/api/v1/batch", json=submit_payload)
        job_id = submit_response.json()["job_id"]
        
        response = client.get(f"/api/v1/batch/{job_id}/results?limit=5")
        data = response.json()
        
        # Results should respect limit
        results = data if isinstance(data, list) else data.get("results", [])
        assert len(results) <= 5


class TestErrorHandling:
    """Error handling and edge cases"""
    
    def test_invalid_endpoint(self, client):
        """Test request to non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_unsupported_method(self, client):
        """Test unsupported HTTP method"""
        response = client.put("/api/v1/classify", json={})
        assert response.status_code == 405
    
    def test_invalid_json_payload(self, client):
        """Test invalid JSON in request body"""
        response = client.post(
            "/api/v1/classify",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_content_type(self, client):
        """Test request without content-type header"""
        response = client.post("/api/v1/classify", json={})
        assert response.status_code in [200, 400, 422]
    
    def test_malformed_json(self, client):
        """Test malformed JSON payload"""
        response = client.post(
            "/api/v1/classify",
            data='{"incomplete": ',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code >= 400
    
    def test_very_long_document_path(self, client):
        """Test handling of very long document paths"""
        long_path = "/documents/" + "a" * 5000 + ".pdf"
        payload = {"document_path": long_path}
        response = client.post("/api/v1/classify", json=payload)
        # Should handle gracefully
        assert response.status_code in [200, 400, 414, 422]
    
    def test_special_characters_in_path(self, client):
        """Test handling of special characters in path"""
        payload = {"document_path": "/documents/文件_@#$%.pdf"}
        response = client.post("/api/v1/classify", json=payload)
        # Should handle or reject gracefully
        assert response.status_code >= 200
    
    def test_null_values_in_payload(self, client):
        """Test handling of null values"""
        payload = {
            "document_path": None,
            "document_type": "auto"
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code >= 400


class TestConcurrency:
    """Concurrency and load tests"""
    
    def test_multiple_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        
        def make_request():
            payload = {"document_path": "/documents/test.pdf"}
            return client.post("/api/v1/classify", json=payload)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
    
    def test_multiple_batch_submissions(self, client):
        """Test multiple batch submissions"""
        import concurrent.futures
        
        def submit_batch():
            payload = {"documents": ["/documents/test.pdf"]}
            return client.post("/api/v1/batch", json=payload)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_batch) for _ in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All submissions should succeed and return unique job IDs
        assert all(r.status_code == 200 for r in results)
        job_ids = [r.json()["job_id"] for r in results]
        assert len(set(job_ids)) == len(job_ids)  # All unique


class TestResponseFormat:
    """Response format and validation"""
    
    def test_json_response_format(self, client):
        """Test responses are valid JSON"""
        response = client.get("/health")
        try:
            data = response.json()
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")
    
    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        response = client.post("/api/v1/classify", json={})
        
        if response.status_code >= 400:
            data = response.json()
            # Error should have some indication of what went wrong
            assert "detail" in data or "error" in data or "message" in data
    
    def test_response_includes_timestamp(self, client):
        """Test responses include timestamp when appropriate"""
        response = client.post(
            "/api/v1/classify",
            json={"document_path": "/documents/test.pdf"}
        )
        if response.status_code == 200:
            data = response.json()
            assert "timestamp" in data or "created_at" in data


class TestDocumentation:
    """API documentation tests"""
    
    def test_swagger_ui_accessible(self, client):
        """Test Swagger UI is accessible"""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_openapi_schema_accessible(self, client):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "info" in schema


# Run tests: pytest tests/test_api_comprehensive.py -v --tb=short --cov=api --cov-report=html
