# DocTender v1.2 - Monitoring, Testing, and CI/CD Guide

**Version:** 1.2.0  
**Date:** January 21, 2026  
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Testing](#testing)
3. [Continuous Integration/Deployment](#cicd)
4. [Monitoring Stack](#monitoring-stack)
5. [Quick Start](#quick-start)
6. [Troubleshooting](#troubleshooting)

---

## Overview

DocTender v1.2 adds three critical production features:

### 1. **Comprehensive Testing**
- 85% code coverage
- Unit tests for all endpoints
- Error scenario testing
- Concurrency tests
- Pytest-based with pytest-cov

### 2. **GitHub Actions CI/CD**
- Automated testing on every push/PR
- Code quality checks (flake8, pylint, black, mypy)
- Security scanning (bandit, safety)
- Docker image building and testing
- Coverage reports to Codecov
- Integration tests with services

### 3. **Prometheus Monitoring**
- 30+ custom metrics
- Alerting rules (20+ conditions)
- Grafana dashboards
- Alert management
- System-level monitoring

---

## Testing

### Running Tests Locally

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

#### 2. Run All Tests

```bash
# Run all tests with coverage
pytest tests/test_api_comprehensive.py -v --cov=api --cov-report=html

# Check coverage threshold (80%)
coverage report --fail-under=80

# View HTML coverage report
open htmlcov/index.html  # macOS
# or
firefox htmlcov/index.html  # Linux
```

#### 3. Run Specific Test Classes

```bash
# Health check tests
pytest tests/test_api_comprehensive.py::TestHealthEndpoint -v

# Classification tests
pytest tests/test_api_comprehensive.py::TestClassifyEndpoint -v

# Batch processing tests
pytest tests/test_api_comprehensive.py::TestBatchEndpoint -v

# Error handling tests
pytest tests/test_api_comprehensive.py::TestErrorHandling -v

# Concurrency tests
pytest tests/test_api_comprehensive.py::TestConcurrency -v
```

#### 4. Run with Options

```bash
# Verbose output
pytest tests/test_api_comprehensive.py -vv

# Show print statements
pytest tests/test_api_comprehensive.py -s

# Stop on first failure
pytest tests/test_api_comprehensive.py -x

# Run only failed tests from last run
pytest tests/test_api_comprehensive.py --lf

# Parallel execution (faster)
pytest tests/test_api_comprehensive.py -n auto
```

### Test Coverage

**Current Coverage:** 85%+

**Areas Covered:**
- ✅ All endpoints (/health, /api/v1/classify, /api/v1/batch, etc)
- ✅ Success scenarios
- ✅ Error handling (400, 404, 500, etc)
- ✅ Edge cases (empty input, very long paths, special chars)
- ✅ Concurrency and load
- ✅ Response format validation
- ✅ Request validation (Pydantic)
- ✅ Documentation endpoints

**Not Covered (by design):**
- Actual ML model inference (mocked)
- Database operations (mocked)
- External LLM API calls (mocked)

---

## CI/CD

### GitHub Actions Workflow

**File:** `.github/workflows/ci-cd.yml`

#### Workflow Triggers

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

#### Jobs in Pipeline

1. **quality-checks** (10 min)
   - Black formatting
   - iSort imports
   - Flake8 linting
   - Pylint analysis
   - MyPy type checking

2. **tests** (30 min, parallel on Python 3.9/3.10/3.11)
   - Run pytest suite
   - Generate coverage reports
   - Upload to Codecov
   - Upload test results
   - Upload coverage HTML

3. **security** (15 min)
   - Bandit security scanning
   - Safety dependency check
   - Upload security reports

4. **docker** (30 min)
   - Build Docker image
   - Test health endpoint
   - Verify containerization

5. **integration-tests** (20 min)
   - Run against PostgreSQL
   - Run against Redis
   - Test database integration
   - Test cache integration

6. **build** (15 min)
   - Build Python wheel
   - Build sdist archive
   - Upload artifacts

7. **publish-results** (auto)
   - Publish test results to PR
   - Display coverage

8. **notify** (on failure)
   - Send Slack notification
   - Create GitHub issue

### Workflow Status

View workflow status in GitHub:

```
Repository → Actions tab → CI/CD Pipeline
```

### Local CI Simulation

Run locally what CI runs:

```bash
# Install quality tools
pip install black isort flake8 pylint mypy

# Check formatting
black --check api/ tests/
isort --check-only api/ tests/

# Lint
flake8 api/ tests/
pylint api/

# Type check
mypy api/ --ignore-missing-imports

# Security
pip install bandit safety
bandit -r api/
safety check

# Tests
pytest tests/test_api_comprehensive.py -v --cov=api --cov-report=term-missing

# Docker
docker build -t doctender:test .
docker run -p 8000:8000 doctender:test
```

### Pull Request Checks

Before merging to `main`:

✅ All CI jobs must pass  
✅ Coverage must be ≥80%  
✅ No security issues  
✅ Docker build succeeds  
✅ All tests pass on Python 3.9/3.10/3.11  

---

## Monitoring Stack

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DocTender API v1.2.0                      │
│  (Metrics exported to /metrics endpoint in Prometheus fmt)  │
└────────────────────┬────────────────────────────────────────┘
                     │ scrape every 15-30s
                     ↓
     ┌──────────────────────────┐
     │     PROMETHEUS           │
     │  (Metrics storage)       │
     │  Port: 9090              │
     └───────┬──────────────────┘
             │
    ┌────────┴────────┐
    ↓                 ↓
┌─────────┐      ┌──────────────┐
│ GRAFANA │      │ ALERTMANAGER │
│ Dashboards     │ Notifications│
│ Port: 3000     │ Port: 9093   │
└─────────┘      └──────────────┘
```

### Components

#### 1. **DocTender API** (Port 8000)

```bash
# Health check
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# API documentation
open http://localhost:8000/api/v1/docs
```

#### 2. **Prometheus** (Port 9090)

```bash
# Web UI
open http://localhost:9090

# Query examples:
# - http_requests_total (total requests)
# - http_request_duration_seconds (request duration)
# - classification_total (classifications done)
# - batch_job_duration_seconds (batch processing time)
# - classifier_accuracy (model accuracy)
```

#### 3. **Grafana** (Port 3000)

```bash
# Access dashboard
open http://localhost:3000

# Login: admin / admin (change in production!)

# Pre-configured dashboards:
# - DocTender API Overview
# - Classification Performance
# - Batch Processing
# - System Resources
# - Database Performance
```

#### 4. **Alertmanager** (Port 9093)

```bash
# Alert status
open http://localhost:9093

# View triggered alerts
# Configure notification channels (Slack, Email, etc.)
```

### Metrics Overview

#### HTTP Metrics

```
http_requests_total             # Total requests by method, endpoint, status
http_request_duration_seconds   # Request latency (p50, p95, p99)
http_request_size_bytes         # Request body size
http_response_size_bytes        # Response body size
```

#### Classification Metrics

```
classification_total            # Total classifications
classification_duration_seconds # Time per classification
classification_confidence       # Confidence score distribution
validation_checks_total         # Validation check results
classifier_accuracy             # Model accuracy gauge
classifier_model_ready          # Model availability
```

#### Batch Processing Metrics

```
batch_jobs_submitted_total      # Jobs submitted
batch_jobs_completed_total      # Jobs completed (success/failure)
batch_job_failures_total        # Job failures by type
batch_job_duration_seconds      # Job processing time
batch_queue_size                # Current queue depth
batch_documents_processed_total # Documents processed
batch_processing_rate           # Docs/second processing rate
```

#### LLM Metrics

```
llm_api_calls_total             # LLM API calls
llm_response_time_seconds       # LLM response latency
llm_tokens_used_total           # Tokens consumed
llm_cost_cents_total            # Cost tracking
llm_hallucination_rate          # Hallucination detection
llm_rate_limit_errors_total     # Rate limit hits
llm_timeout_errors_total        # Timeout errors
```

#### System Metrics

```
api_uptime_seconds              # API uptime
active_requests                 # Current active requests
cache_hit_rate                  # Cache efficiency
errors_total                    # Error count by type
db_connection_pool_size         # DB pool status
db_active_connections           # Active DB connections
```

### Alert Rules

**File:** `monitoring/alerts.yml`

Trigger alerts for:

- ❌ API down (2 min)
- ⚠️ High error rate (>5%, 5 min)
- ⚠️ High latency (p99 > 5s, 5 min)
- ⚠️ Slow classification (p95 > 10s, 10 min)
- ⚠️ Batch job failures (>10, 15 min)
- ⚠️ Queue backlog (>1000 items, 10 min)
- ⚠️ High memory (>85%, 5 min)
- ⚠️ High CPU (>80%, 10 min)
- ❌ Database down (2 min)
- ⚠️ Redis down (2 min)
- ❌ Model not ready (2 min)
- ⚠️ Low accuracy (<85%, 15 min)
- ⚠️ High LLM hallucination (>10%, 5 min)
- ⚠️ Disk space critical (<10%, 5 min)

---

## Quick Start

### 1. Run Monitoring Stack

```bash
# Clone repo
git clone https://github.com/OlegKarenkikh/DocTender.git
cd DocTender

# Checkout feature branch
git checkout feature/v1.2-quality-and-ci-cd

# Start all services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services are running
docker-compose -f docker-compose.monitoring.yml ps

# Check logs
docker-compose -f docker-compose.monitoring.yml logs -f api
```

### 2. Access Services

| Service | URL | Login |
|---------|-----|-------|
| API Docs | http://localhost:8000/api/v1/docs | - |
| Health | http://localhost:8000/health | - |
| Metrics | http://localhost:8000/metrics | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Alertmanager | http://localhost:9093 | - |

### 3. Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest tests/test_api_comprehensive.py -v --cov=api

# View coverage
open htmlcov/index.html
```

### 4. Make API Requests

```bash
# Classify document
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "/documents/invoice.pdf",
    "validate_document": true
  }'

# Submit batch
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["/documents/doc1.pdf", "/documents/doc2.pdf"]
  }'

# Check batch status
curl http://localhost:8000/api/v1/batch/batch_abc123/status

# Get batch results
curl http://localhost:8000/api/v1/batch/batch_abc123/results?limit=10
```

### 5. View Metrics in Grafana

1. Open http://localhost:3000
2. Login: admin/admin
3. Go to Dashboards
4. Select "DocTender API Overview"
5. Watch real-time metrics

### 6. Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.monitoring.yml down

# Stop and remove volumes
docker-compose -f docker-compose.monitoring.yml down -v
```

---

## Troubleshooting

### Tests Failing

```bash
# Check test output
pytest tests/test_api_comprehensive.py -vv

# Run single test
pytest tests/test_api_comprehensive.py::TestHealthEndpoint::test_health_check_success -vv

# Debug mode
pytest tests/test_api_comprehensive.py --pdb
```

### Docker Issues

```bash
# Rebuild image
docker-compose -f docker-compose.monitoring.yml build --no-cache

# View logs
docker-compose -f docker-compose.monitoring.yml logs api

# Check health
docker-compose -f docker-compose.monitoring.yml ps

# Test health endpoint
docker exec doctender-api-v1.2 curl http://localhost:8000/health
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
open http://localhost:9090/targets

# View Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus

# Test metrics endpoint
curl http://localhost:8000/metrics | head -20
```

### Grafana Dashboard Empty

```bash
# Ensure Prometheus has data
open http://localhost:9090
# Enter query: http_requests_total
# Should show results

# Refresh Grafana dashboard
# Press Ctrl+Shift+R in browser
```

### High Memory Usage

```bash
# Check metric storage
docker exec doctender-prometheus du -sh /prometheus

# Reduce retention
# Edit docker-compose-monitoring.yml:
# - '--storage.tsdb.retention.time=7d'  # reduce from 30d

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

---

## What's Next (v1.3+)

- [ ] Kubernetes deployment manifests
- [ ] Helm chart for easy K8s deployment
- [ ] Advanced Grafana dashboards
- [ ] Custom alerting channels (Slack, PagerDuty)
- [ ] Distributed tracing (Jaeger)
- [ ] Log aggregation (ELK stack)
- [ ] Performance profiling
- [ ] Load testing suite

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

---

**Questions?** Check the [main documentation](./DEPLOYMENT.md) or open an issue.
