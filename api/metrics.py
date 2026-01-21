"""Prometheus metrics instrumentation for DocTender API v1.2.0

Provides 30+ custom metrics for monitoring classification, batch processing,
and system health with automatic collection and Prometheus export.
"""

from datetime import datetime
from typing import Callable, Optional

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry

# Create registry for metrics
registry = CollectorRegistry()

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000),
    registry=registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000),
    registry=registry,
)

# ============================================================================
# CLASSIFICATION METRICS
# ============================================================================

classification_total = Counter(
    "classification_total",
    "Total classification requests",
    ["document_type", "status"],
    registry=registry,
)

classification_duration_seconds = Histogram(
    "classification_duration_seconds",
    "Classification request duration in seconds",
    ["document_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry,
)

classification_confidence = Gauge(
    "classification_confidence",
    "Average classification confidence score",
    ["document_type"],
    registry=registry,
)

validation_checks_total = Counter(
    "validation_checks_total",
    "Total validation checks performed",
    ["check_type", "result"],
    registry=registry,
)

classifier_accuracy = Gauge(
    "classifier_accuracy",
    "Current classifier model accuracy (0-1)",
    registry=registry,
)

classifier_model_ready = Gauge(
    "classifier_model_ready",
    "Is classifier model ready (1=ready, 0=not ready)",
    registry=registry,
)

# ============================================================================
# BATCH PROCESSING METRICS
# ============================================================================

batch_jobs_submitted_total = Counter(
    "batch_jobs_submitted_total",
    "Total batch jobs submitted",
    registry=registry,
)

batch_jobs_completed_total = Counter(
    "batch_jobs_completed_total",
    "Total batch jobs completed",
    ["status"],  # success, failure, partial
    registry=registry,
)

batch_job_failures_total = Counter(
    "batch_job_failures_total",
    "Total batch job failures",
    ["failure_type"],  # timeout, parsing_error, classification_error, etc
    registry=registry,
)

batch_job_duration_seconds = Histogram(
    "batch_job_duration_seconds",
    "Batch job processing time in seconds",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry,
)

batch_queue_size = Gauge(
    "batch_queue_size",
    "Current number of jobs in queue",
    registry=registry,
)

batch_documents_processed_total = Counter(
    "batch_documents_processed_total",
    "Total documents processed in batch jobs",
    registry=registry,
)

batch_processing_rate = Gauge(
    "batch_processing_rate",
    "Current batch processing rate (documents/second)",
    registry=registry,
)

# ============================================================================
# LLM METRICS
# ============================================================================

llm_api_calls_total = Counter(
    "llm_api_calls_total",
    "Total LLM API calls",
    ["model", "status"],
    registry=registry,
)

llm_response_time_seconds = Histogram(
    "llm_response_time_seconds",
    "LLM API response time in seconds",
    ["model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry,
)

llm_tokens_used_total = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens used",
    ["model", "token_type"],  # prompt, completion
    registry=registry,
)

llm_cost_cents_total = Counter(
    "llm_cost_cents_total",
    "Total LLM API cost in cents",
    ["model"],
    registry=registry,
)

llm_hallucination_rate = Gauge(
    "llm_hallucination_rate",
    "Estimated LLM hallucination rate (0-1)",
    ["model"],
    registry=registry,
)

llm_rate_limit_errors_total = Counter(
    "llm_rate_limit_errors_total",
    "Total LLM rate limit errors",
    ["model"],
    registry=registry,
)

llm_timeout_errors_total = Counter(
    "llm_timeout_errors_total",
    "Total LLM timeout errors",
    ["model"],
    registry=registry,
)

# ============================================================================
# SYSTEM METRICS
# ============================================================================

api_uptime_seconds = Gauge(
    "api_uptime_seconds",
    "API uptime in seconds",
    registry=registry,
)

active_requests = Gauge(
    "active_requests",
    "Current number of active HTTP requests",
    registry=registry,
)

cache_hit_rate = Gauge(
    "cache_hit_rate",
    "Cache hit rate (0-1)",
    registry=registry,
)

errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type"],
    registry=registry,
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
    registry=registry,
)

db_active_connections = Gauge(
    "db_active_connections",
    "Number of active database connections",
    registry=registry,
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def track_http_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                active_requests.inc()
                result = await func(*args, **kwargs)
                status = getattr(result, "status_code", 200)
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                return result
            except Exception as e:
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=500
                ).inc()
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
                active_requests.dec()

        return wrapper

    return decorator


def track_classification(document_type: str = "unknown"):
    """Decorator to track classification metrics"""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                classification_total.labels(
                    document_type=document_type, status="success"
                ).inc()
                return result
            except Exception as e:
                classification_total.labels(
                    document_type=document_type, status="error"
                ).inc()
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                classification_duration_seconds.labels(
                    document_type=document_type
                ).observe(duration)

        return wrapper

    return decorator


def get_metrics_summary() -> dict:
    """Get summary of current metrics"""
    return {
        "http_requests": "http_requests_total",
        "classifications": "classification_total",
        "batch_jobs": "batch_jobs_completed_total",
        "active_requests": active_requests._value.get(),
        "uptime_seconds": api_uptime_seconds._value.get(),
    }
