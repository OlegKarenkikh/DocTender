"""
Prometheus Metrics Instrumentation for DocTender API
Version: 1.0.0

Provides comprehensive metrics collection for:
- HTTP requests (duration, count, status codes)
- Classification operations (duration, accuracy, errors)
- Batch processing (job duration, success/failure, queue size)
- LLM operations (hallucination rate, tokens, cost)
- System health (uptime, errors, cache performance)
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    REGISTRY,
)
from typing import Optional
import time
from functools import wraps


class DocTenderMetrics:
    """Central metrics registry for DocTender"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics"""
        self.registry = registry or REGISTRY
        self._init_http_metrics()
        self._init_classification_metrics()
        self._init_batch_metrics()
        self._init_llm_metrics()
        self._init_system_metrics()
    
    def _init_http_metrics(self):
        """HTTP request metrics"""
        
        # Request counter by method, path, status
        self.http_requests_total = Counter(
            name='http_requests_total',
            documentation='Total HTTP requests',
            labelnames=['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        # Request duration histogram (in seconds)
        self.http_request_duration_seconds = Histogram(
            name='http_request_duration_seconds',
            documentation='HTTP request duration in seconds',
            labelnames=['method', 'endpoint'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        # Request size in bytes
        self.http_request_size_bytes = Summary(
            name='http_request_size_bytes',
            documentation='HTTP request size in bytes',
            labelnames=['method', 'endpoint'],
            registry=self.registry
        )
        
        # Response size in bytes
        self.http_response_size_bytes = Summary(
            name='http_response_size_bytes',
            documentation='HTTP response size in bytes',
            labelnames=['method', 'endpoint', 'status'],
            registry=self.registry
        )
    
    def _init_classification_metrics(self):
        """Document classification metrics"""
        
        # Classification operations counter
        self.classification_total = Counter(
            name='classification_total',
            documentation='Total classification operations',
            labelnames=['status', 'document_type'],
            registry=self.registry
        )
        
        # Classification duration histogram
        self.classification_duration_seconds = Histogram(
            name='classification_duration_seconds',
            documentation='Classification duration in seconds',
            labelnames=['document_type'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        # Classification confidence score
        self.classification_confidence = Summary(
            name='classification_confidence',
            documentation='Classification confidence score (0-1)',
            labelnames=['document_type'],
            registry=self.registry
        )
        
        # Validation check results
        self.validation_checks_total = Counter(
            name='validation_checks_total',
            documentation='Total validation checks',
            labelnames=['check_type', 'result'],
            registry=self.registry
        )
        
        # Model accuracy gauge
        self.classifier_accuracy = Gauge(
            name='classifier_accuracy',
            documentation='Current classifier accuracy (0-1)',
            registry=self.registry
        )
        
        # Model readiness
        self.classifier_model_ready = Gauge(
            name='classifier_model_ready',
            documentation='Is classification model ready (0 or 1)',
            registry=self.registry
        )
    
    def _init_batch_metrics(self):
        """Batch processing metrics"""
        
        # Batch job submissions
        self.batch_jobs_submitted_total = Counter(
            name='batch_jobs_submitted_total',
            documentation='Total batch jobs submitted',
            registry=self.registry
        )
        
        # Batch job completions
        self.batch_jobs_completed_total = Counter(
            name='batch_jobs_completed_total',
            documentation='Total batch jobs completed',
            labelnames=['status'],  # success, partial_failure, failure
            registry=self.registry
        )
        
        # Batch job failures
        self.batch_job_failures_total = Counter(
            name='batch_job_failures_total',
            documentation='Total batch job failures',
            labelnames=['failure_type'],
            registry=self.registry
        )
        
        # Batch job duration
        self.batch_job_duration_seconds = Histogram(
            name='batch_job_duration_seconds',
            documentation='Batch job processing duration in seconds',
            buckets=(1, 5, 10, 30, 60, 300, 600, 1800),
            registry=self.registry
        )
        
        # Batch queue size
        self.batch_queue_size = Gauge(
            name='batch_queue_size',
            documentation='Current number of jobs in batch queue',
            registry=self.registry
        )
        
        # Documents processed in batch
        self.batch_documents_processed_total = Counter(
            name='batch_documents_processed_total',
            documentation='Total documents processed in batch mode',
            labelnames=['status'],  # success, failed
            registry=self.registry
        )
        
        # Batch processing rate (docs/sec)
        self.batch_processing_rate = Gauge(
            name='batch_processing_rate',
            documentation='Batch processing rate (documents per second)',
            registry=self.registry
        )
    
    def _init_llm_metrics(self):
        """LLM integration metrics"""
        
        # LLM API calls
        self.llm_api_calls_total = Counter(
            name='llm_api_calls_total',
            documentation='Total LLM API calls',
            labelnames=['model', 'status'],
            registry=self.registry
        )
        
        # LLM response time
        self.llm_response_time_seconds = Histogram(
            name='llm_response_time_seconds',
            documentation='LLM response time in seconds',
            labelnames=['model'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry
        )
        
        # LLM tokens used
        self.llm_tokens_used_total = Counter(
            name='llm_tokens_used_total',
            documentation='Total tokens used in LLM calls',
            labelnames=['model', 'token_type'],  # prompt, completion
            registry=self.registry
        )
        
        # LLM cost (in cents)
        self.llm_cost_cents_total = Counter(
            name='llm_cost_cents_total',
            documentation='Total LLM cost in cents',
            labelnames=['model'],
            registry=self.registry
        )
        
        # LLM hallucination rate
        self.llm_hallucination_rate = Gauge(
            name='llm_hallucination_rate',
            documentation='Current LLM hallucination rate (0-1)',
            registry=self.registry
        )
        
        # LLM rate limit errors
        self.llm_rate_limit_errors_total = Counter(
            name='llm_rate_limit_errors_total',
            documentation='Total LLM rate limit errors',
            labelnames=['model'],
            registry=self.registry
        )
        
        # LLM timeout errors
        self.llm_timeout_errors_total = Counter(
            name='llm_timeout_errors_total',
            documentation='Total LLM timeout errors',
            labelnames=['model'],
            registry=self.registry
        )
    
    def _init_system_metrics(self):
        """System and health metrics"""
        
        # API uptime (seconds)
        self.api_uptime_seconds = Gauge(
            name='api_uptime_seconds',
            documentation='API uptime in seconds',
            registry=self.registry
        )
        
        # Active requests
        self.active_requests = Gauge(
            name='active_requests',
            documentation='Current number of active requests',
            registry=self.registry
        )
        
        # Cache hit rate
        self.cache_hit_rate = Gauge(
            name='cache_hit_rate',
            documentation='Cache hit rate (0-1)',
            registry=self.registry
        )
        
        # Cache size (items)
        self.cache_size_items = Gauge(
            name='cache_size_items',
            documentation='Current cache size in items',
            registry=self.registry
        )
        
        # Errors counter by type
        self.errors_total = Counter(
            name='errors_total',
            documentation='Total errors by type',
            labelnames=['error_type'],
            registry=self.registry
        )
        
        # Database connection pool
        self.db_connection_pool_size = Gauge(
            name='db_connection_pool_size',
            documentation='Database connection pool size',
            registry=self.registry
        )
        
        # Database active connections
        self.db_active_connections = Gauge(
            name='db_active_connections',
            documentation='Active database connections',
            registry=self.registry
        )


# Global metrics instance
metrics = DocTenderMetrics()


def track_http_request(method: str, endpoint: str):
    """Decorator to track HTTP requests"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics.active_requests.inc()
            
            try:
                result = await func(*args, **kwargs)
                status_code = getattr(result, 'status_code', 200)
                
                # Record metrics
                duration = time.time() - start_time
                metrics.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status_code
                ).inc()
                
                return result
            
            except Exception as e:
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()
                metrics.errors_total.labels(error_type=type(e).__name__).inc()
                raise
            
            finally:
                metrics.active_requests.dec()
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics.active_requests.inc()
            
            try:
                result = func(*args, **kwargs)
                status_code = getattr(result, 'status_code', 200)
                
                duration = time.time() - start_time
                metrics.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status_code
                ).inc()
                
                return result
            
            except Exception as e:
                metrics.http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()
                metrics.errors_total.labels(error_type=type(e).__name__).inc()
                raise
            
            finally:
                metrics.active_requests.dec()
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_classification(document_type: str = "unknown"):
    """Decorator to track classification operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                metrics.classification_duration_seconds.labels(
                    document_type=document_type
                ).observe(duration)
                metrics.classification_total.labels(
                    status='success',
                    document_type=document_type
                ).inc()
                
                # Track confidence if available
                if isinstance(result, dict) and 'confidence' in result:
                    metrics.classification_confidence.labels(
                        document_type=document_type
                    ).observe(result['confidence'])
                
                return result
            
            except Exception as e:
                metrics.classification_total.labels(
                    status='error',
                    document_type=document_type
                ).inc()
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.classification_duration_seconds.labels(
                    document_type=document_type
                ).observe(duration)
                metrics.classification_total.labels(
                    status='success',
                    document_type=document_type
                ).inc()
                
                if isinstance(result, dict) and 'confidence' in result:
                    metrics.classification_confidence.labels(
                        document_type=document_type
                    ).observe(result['confidence'])
                
                return result
            
            except Exception as e:
                metrics.classification_total.labels(
                    status='error',
                    document_type=document_type
                ).inc()
                raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Helper functions to update metrics
def set_classifier_accuracy(accuracy: float):
    """Set current classifier accuracy"""
    metrics.classifier_accuracy.set(accuracy)


def set_classifier_ready(ready: bool):
    """Set classifier readiness status"""
    metrics.classifier_model_ready.set(1.0 if ready else 0.0)


def update_batch_queue_size(size: int):
    """Update batch queue size"""
    metrics.batch_queue_size.set(size)


def update_cache_hit_rate(hit_rate: float):
    """Update cache hit rate"""
    metrics.cache_hit_rate.set(hit_rate)


def update_cache_size(size: int):
    """Update cache size"""
    metrics.cache_size_items.set(size)


def set_api_uptime(uptime_seconds: float):
    """Set API uptime"""
    metrics.api_uptime_seconds.set(uptime_seconds)


def set_llm_hallucination_rate(rate: float):
    """Set LLM hallucination rate"""
    metrics.llm_hallucination_rate.set(rate)
