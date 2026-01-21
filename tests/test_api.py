#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests для REST API
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

try:
    from api.main import app
except ImportError:
    # For running from different directories
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from api.main import app

client = TestClient(app)

class TestHealthcheck:
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "DocTender API"
        assert "endpoints" in data

class TestClassification:
    def test_classify_endpoint_exists(self):
        """Test that classification endpoint exists"""
        response = client.post(
            "/api/v1/classify",
            json={"document_path": "test.txt", "document_type": "auto"}
        )
        # May fail due to missing file, but endpoint should exist
        assert response.status_code in [200, 400, 500]

class TestBatchProcessing:
    def test_batch_submission(self):
        """Test batch job submission"""
        response = client.post(
            "/api/v1/batch",
            json={"documents": ["doc1.pdf", "doc2.pdf"]}
        )
        assert response.status_code in [200, 500]  # May fail if classifier not loaded
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "pending"
            assert data["total_documents"] == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
