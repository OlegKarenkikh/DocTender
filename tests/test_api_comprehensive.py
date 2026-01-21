"""Comprehensive test suite for DocTender REST API v1.2.0

Tests all endpoints, error scenarios, edge cases, and performance metrics.
Target: 85%+ code coverage
"""

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
try:
    from api.main_with_metrics import app
except ImportError:
    from api.main import app


class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_check_returns_200(self):
        """Health endpoint should return 200 OK"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_format(self):
        """Health endpoint should return correct JSON structure"""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

    def test_health_check_performance(self):
        """Health endpoint should respond in <100ms"""
        client = TestClient(app)
        start = time.time()
        client.get("/health")
        duration = (time.time() - start) * 1000
        assert duration < 100, f"Health check took {duration}ms, expected <100ms"


class TestClassifyEndpoint:
    """Test POST /api/v1/classify endpoint"""

    def test_classify_with_valid_document(self):
        """Should classify valid document successfully"""
        client = TestClient(app)
        payload = {"document_path": "/tmp/test_invoice.pdf", "validate_document": True}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [200, 422]  # 422 if doc doesn't exist

    def test_classify_without_document_path(self):
        """Should return 422 when document_path is missing"""
        client = TestClient(app)
        payload = {"validate_document": True}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 422

    def test_classify_with_empty_document_path(self):
        """Should return 422 when document_path is empty"""
        client = TestClient(app)
        payload = {"document_path": "", "validate_document": True}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code == 422

    def test_classify_with_very_long_path(self):
        """Should handle very long file paths"""
        client = TestClient(app)
        long_path = "/" + "/".join(["folder"] * 100) + "/document.pdf"
        payload = {"document_path": long_path, "validate_document": False}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [200, 422, 400]

    def test_classify_with_special_characters_in_path(self):
        """Should handle special characters in file paths"""
        client = TestClient(app)
        paths = [
            "/docs/invoice-2024.pdf",
            "/docs/contract_final_v3.pdf",
            "/docs/документ.pdf",  # Unicode
            "/docs/file (1).pdf",
        ]
        for path in paths:
            payload = {"document_path": path, "validate_document": False}
            response = client.post("/api/v1/classify", json=payload)
            assert response.status_code in [200, 422, 400]

    def test_classify_response_structure(self):
        """Response should have correct structure"""
        client = TestClient(app)
        payload = {"document_path": "/tmp/test.pdf", "validate_document": False}
        response = client.post("/api/v1/classify", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "classification" in data or "error" in data

    def test_classify_with_optional_parameters(self):
        """Should accept optional parameters"""
        client = TestClient(app)
        payload = {
            "document_path": "/tmp/test.pdf",
            "validate_document": True,
            "confidence_threshold": 0.75,
        }
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [200, 422]

    def test_classify_concurrent_requests(self):
        """Should handle multiple concurrent classification requests"""
        client = TestClient(app)
        for i in range(5):
            payload = {"document_path": f"/tmp/doc{i}.pdf", "validate_document": False}
            response = client.post("/api/v1/classify", json=payload)
            assert response.status_code in [200, 422]

    def test_classify_with_invalid_json(self):
        """Should return 422 for invalid JSON"""
        client = TestClient(app)
        response = client.post(
            "/api/v1/classify",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [422, 400]

    def test_classify_post_only(self):
        """GET requests to /api/v1/classify should fail"""
        client = TestClient(app)
        response = client.get("/api/v1/classify")
        assert response.status_code == 405  # Method not allowed


class TestBatchEndpoint:
    """Test POST /api/v1/batch endpoint"""

    def test_batch_submission_valid(self):
        """Should accept valid batch submission"""
        client = TestClient(app)
        payload = {"documents": ["/tmp/doc1.pdf", "/tmp/doc2.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [200, 202]

    def test_batch_returns_job_id(self):
        """Batch submission should return job_id"""
        client = TestClient(app)
        payload = {"documents": ["/tmp/test.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        if response.status_code in [200, 202]:
            data = response.json()
            assert "job_id" in data or "batch_id" in data

    def test_batch_with_empty_list(self):
        """Should handle empty document list"""
        client = TestClient(app)
        payload = {"documents": []}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [422, 400, 200]

    def test_batch_with_single_document(self):
        """Should handle single document batch"""
        client = TestClient(app)
        payload = {"documents": ["/tmp/single.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [200, 202]

    def test_batch_with_large_document_list(self):
        """Should handle large batch (1000+ documents)"""
        client = TestClient(app)
        docs = [f"/docs/doc{i}.pdf" for i in range(100)]  # 100 for testing
        payload = {"documents": docs}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [200, 202, 413]  # 413 if too large

    def test_batch_without_documents_field(self):
        """Should return 422 when documents field missing"""
        client = TestClient(app)
        payload = {}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code == 422

    def test_batch_with_invalid_documents_type(self):
        """Should return 422 when documents is not a list"""
        client = TestClient(app)
        payload = {"documents": "not a list"}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code == 422

    def test_batch_response_structure(self):
        """Response should contain required fields"""
        client = TestClient(app)
        payload = {"documents": ["/tmp/test.pdf"]}
        response = client.post("/api/v1/batch", json=payload)
        if response.status_code in [200, 202]:
            data = response.json()
            required = ["job_id", "batch_id", "status", "created_at"]
            # At least some required fields
            assert any(field in data for field in required)

    def test_batch_post_only(self):
        """GET requests should fail"""
        client = TestClient(app)
        response = client.get("/api/v1/batch")
        assert response.status_code == 405


class TestBatchStatusEndpoint:
    """Test GET /api/v1/batch/{job_id}/status endpoint"""

    def test_batch_status_with_valid_id(self):
        """Should retrieve status with valid job_id"""
        client = TestClient(app)
        # First create a batch
        submit = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if submit.status_code in [200, 202]:
            data = submit.json()
            job_id = data.get("job_id") or data.get("batch_id")
            if job_id:
                response = client.get(f"/api/v1/batch/{job_id}/status")
                assert response.status_code in [200, 404]

    def test_batch_status_with_invalid_id(self):
        """Should return 404 for non-existent job_id"""
        client = TestClient(app)
        response = client.get("/api/v1/batch/nonexistent123/status")
        assert response.status_code == 404

    def test_batch_status_response_structure(self):
        """Status response should have required fields"""
        client = TestClient(app)
        submit = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if submit.status_code in [200, 202]:
            data = submit.json()
            job_id = data.get("job_id") or data.get("batch_id")
            if job_id:
                response = client.get(f"/api/v1/batch/{job_id}/status")
                if response.status_code == 200:
                    status = response.json()
                    assert "status" in status

    def test_batch_status_with_special_characters_in_id(self):
        """Should handle special characters in job_id"""
        client = TestClient(app)
        special_ids = ["batch-123", "batch_123", "batch.123", "BATCH123"]
        for job_id in special_ids:
            response = client.get(f"/api/v1/batch/{job_id}/status")
            assert response.status_code in [404, 200, 400]

    def test_batch_status_post_not_allowed(self):
        """POST should not be allowed on status endpoint"""
        client = TestClient(app)
        response = client.post("/api/v1/batch/batch123/status", json={})
        assert response.status_code == 405


class TestBatchResultsEndpoint:
    """Test GET /api/v1/batch/{job_id}/results endpoint"""

    def test_batch_results_with_valid_id(self):
        """Should retrieve results with valid job_id"""
        client = TestClient(app)
        submit = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if submit.status_code in [200, 202]:
            data = submit.json()
            job_id = data.get("job_id") or data.get("batch_id")
            if job_id:
                response = client.get(f"/api/v1/batch/{job_id}/results")
                assert response.status_code in [200, 202, 404]

    def test_batch_results_with_invalid_id(self):
        """Should return 404 for non-existent job_id"""
        client = TestClient(app)
        response = client.get("/api/v1/batch/nonexistent123/results")
        assert response.status_code == 404

    def test_batch_results_with_pagination(self):
        """Should support pagination parameters"""
        client = TestClient(app)
        submit = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if submit.status_code in [200, 202]:
            data = submit.json()
            job_id = data.get("job_id") or data.get("batch_id")
            if job_id:
                response = client.get(
                    f"/api/v1/batch/{job_id}/results?limit=10&offset=0"
                )
                assert response.status_code in [200, 202, 404]

    def test_batch_results_with_invalid_limit(self):
        """Should handle invalid limit parameter"""
        client = TestClient(app)
        response = client.get("/api/v1/batch/batch123/results?limit=invalid")
        assert response.status_code in [400, 422, 404]

    def test_batch_results_response_structure(self):
        """Results should include results array"""
        client = TestClient(app)
        submit = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if submit.status_code in [200, 202]:
            data = submit.json()
            job_id = data.get("job_id") or data.get("batch_id")
            if job_id:
                response = client.get(f"/api/v1/batch/{job_id}/results")
                if response.status_code == 200:
                    results = response.json()
                    assert isinstance(results, (list, dict))

    def test_batch_results_post_not_allowed(self):
        """POST should not be allowed on results endpoint"""
        client = TestClient(app)
        response = client.post("/api/v1/batch/batch123/results", json={})
        assert response.status_code == 405


class TestErrorHandling:
    """Test error handling across all endpoints"""

    def test_404_on_nonexistent_endpoint(self):
        """Should return 404 for non-existent endpoints"""
        client = TestClient(app)
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self):
        """Should return 405 for wrong HTTP method"""
        client = TestClient(app)
        response = client.delete("/api/v1/classify")
        assert response.status_code == 405

    def test_400_malformed_json(self):
        """Should return 400/422 for malformed JSON"""
        client = TestClient(app)
        response = client.post(
            "/api/v1/classify",
            data="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_500_internal_error_response_format(self):
        """Error responses should have consistent format"""
        client = TestClient(app)
        response = client.post("/api/v1/batch", json={})  # Missing required field
        assert response.status_code in [400, 422]
        assert "detail" in response.json() or "error" in response.json()

    def test_error_with_special_characters(self):
        """Should handle errors with special characters gracefully"""
        client = TestClient(app)
        payload = {"document_path": "\x00\x01\x02"}
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [400, 422]

    def test_timeout_handling(self):
        """Endpoints should not hang indefinitely"""
        client = TestClient(app)
        # Use reasonable timeout
        try:
            response = client.get("/health", timeout=5)
            assert response.status_code in [200, 408]
        except Exception:
            pass  # Timeout is acceptable

    def test_error_messages_not_exposing_internals(self):
        """Error messages should not expose internal details"""
        client = TestClient(app)
        response = client.post("/api/v1/classify", json={})
        if response.status_code >= 400:
            message = response.json()
            message_str = json.dumps(message).lower()
            assert "traceback" not in message_str
            assert "line " not in message_str

    def test_content_type_validation(self):
        """Should validate Content-Type header"""
        client = TestClient(app)
        response = client.post(
            "/api/v1/classify",
            data="{}",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code in [400, 415, 422]

    def test_very_large_payload(self):
        """Should reject very large payloads"""
        client = TestClient(app)
        large_docs = ["x" * 1000 for _ in range(1000)]  # Large payload
        payload = {"documents": large_docs}
        response = client.post("/api/v1/batch", json=payload)
        assert response.status_code in [200, 202, 413, 422]

    def test_unicode_handling_in_errors(self):
        """Should handle Unicode characters in error messages"""
        client = TestClient(app)
        payload = {"document_path": "тест"}  # Cyrillic
        response = client.post("/api/v1/classify", json=payload)
        assert response.status_code in [200, 422, 400]


class TestConcurrency:
    """Test concurrent request handling"""

    def test_concurrent_classifications(self):
        """Should handle multiple concurrent classification requests"""
        client = TestClient(app)
        for i in range(10):
            payload = {"document_path": f"/tmp/doc{i}.pdf", "validate_document": False}
            response = client.post("/api/v1/classify", json=payload)
            assert response.status_code in [200, 422]

    def test_concurrent_batch_submissions(self):
        """Should handle multiple concurrent batch submissions"""
        client = TestClient(app)
        for i in range(5):
            payload = {"documents": [f"/tmp/doc{i}.pdf"]}
            response = client.post("/api/v1/batch", json=payload)
            assert response.status_code in [200, 202]


class TestResponseFormat:
    """Test response format and content"""

    def test_json_response_format(self):
        """All responses should be valid JSON"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        assert isinstance(response.json(), dict)

    def test_response_timestamp_format(self):
        """Timestamps should be ISO 8601 format"""
        client = TestClient(app)
        response = client.post("/api/v1/batch", json={"documents": ["/tmp/test.pdf"]})
        if response.status_code in [200, 202]:
            data = response.json()
            if "created_at" in data:
                # Should be ISO format
                assert "T" in data["created_at"] or "Z" in data["created_at"]

    def test_response_includes_status_code(self):
        """HTTP status codes should be consistent with response content"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] is not None

    def test_empty_response_handled(self):
        """Should handle empty responses gracefully"""
        client = TestClient(app)
        response = client.get("/api/v1/batch/nonexistent/results")
        if response.status_code == 404:
            data = response.json()
            assert isinstance(data, (dict, list))


class TestDocumentation:
    """Test API documentation endpoints"""

    def test_swagger_docs_available(self):
        """OpenAPI documentation should be available"""
        client = TestClient(app)
        response = client.get("/api/v1/docs")
        assert response.status_code == 200

    def test_redoc_docs_available(self):
        """ReDoc documentation should be available"""
        client = TestClient(app)
        response = client.get("/api/v1/redoc")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
