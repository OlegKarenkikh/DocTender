"""
DocTender REST API with Prometheus Metrics Instrumentation
Version: 1.2.0

Enhanced REST API with:
- All v1.1.0 endpoints (classify, batch, health)
- Prometheus metrics collection
- Metrics endpoint at /metrics
- Enhanced monitoring and observability
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import time
import logging
from datetime import datetime
from prometheus_client import generate_latest, CollectorRegistry

# Import metrics
from api.metrics import (
    metrics,
    track_http_request,
    track_classification,
    set_classifier_ready,
    set_classifier_accuracy,
    update_batch_queue_size,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="DocTender API",
    description="Production-grade Document Classification API with REST, Batch Processing, and Monitoring",
    version="1.2.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Models for request/response validation
class ClassifyRequest(BaseModel):
    """Classification request model"""
    document_path: str = Field(..., description="Path to document file", min_length=1)
    document_type: str = Field("auto", description="Document type (auto/invoice/contract/etc)")
    validate_document: bool = Field(True, description="Enable document validation")


class ClassifyResponse(BaseModel):
    """Classification response model"""
    document_path: str
    classification: str
    confidence: float = Field(..., ge=0, le=1)
    category: str
    entities: Dict[str, Any]
    validation: Optional[Dict[str, Any]] = None
    status: str
    processing_time: float
    timestamp: str


class BatchRequest(BaseModel):
    """Batch processing request model"""
    documents: List[str] = Field(..., min_items=1, max_items=10000)
    validate_documents: bool = Field(True)
    priority: str = Field("normal", description="normal/high/low")


class BatchResponse(BaseModel):
    """Batch job submission response"""
    job_id: str
    status: str
    total_documents: int
    processed: int = 0
    failed: int = 0
    results_url: str
    submitted_at: str


class BatchStatus(BaseModel):
    """Batch job status response"""
    job_id: str
    status: str
    total_documents: int
    processed: int
    failed: int
    progress_percent: float
    estimated_time_remaining: Optional[float]
    updated_at: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    metrics: Dict[str, Any]


# In-memory storage for batch jobs (in production use database)
batch_jobs: Dict[str, Dict[str, Any]] = {}
start_time = time.time()


# === MIDDLEWARE FOR METRICS ===

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to track HTTP metrics"""
    start_time = time.time()
    metrics.active_requests.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        metrics.http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        metrics.http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        return response
    
    except Exception as e:
        metrics.errors_total.labels(error_type=type(e).__name__).inc()
        raise
    
    finally:
        metrics.active_requests.dec()


# === METRICS ENDPOINT ===

@app.get("/metrics", tags=["monitoring"])
async def metrics_endpoint() -> PlainTextResponse:
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format.
    Scrape this endpoint with Prometheus at http://localhost:8000/metrics
    """
    return PlainTextResponse(generate_latest())


# === HEALTH CHECK ===

@app.get("/health", tags=["monitoring"], response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    
    Returns:
    - status: "healthy" or "degraded"
    - API uptime, version, and current metrics
    """
    uptime = time.time() - start_time
    metrics.api_uptime_seconds.set(uptime)
    
    # Simulate model readiness (in production, check actual model state)
    set_classifier_ready(True)
    set_classifier_accuracy(0.91)  # Example accuracy
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.2.0",
        uptime_seconds=uptime,
        metrics={
            "active_requests": int(metrics.active_requests._value.get()),
            "total_requests": int(metrics.http_requests_total._value.get()),
            "classifications_total": int(metrics.classification_total._value.get()),
            "batch_jobs_submitted": int(metrics.batch_jobs_submitted_total._value.get()),
            "queue_size": len(batch_jobs),
        }
    )


# === CLASSIFICATION ENDPOINT ===

@app.post("/api/v1/classify", tags=["classification"], response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest) -> ClassifyResponse:
    """
    Classify a single document
    
    Accepts document path and returns classification with confidence,
    category, entities, and optional validation results.
    
    **Parameters:**
    - document_path: Path to the document (required)
    - document_type: Document type hint (auto/invoice/contract/etc)
    - validate_document: Enable validation checks (default: true)
    
    **Returns:**
    - classification: Detected document type
    - confidence: Confidence score (0-1)
    - category: Document category
    - entities: Extracted entities
    - validation: Validation results if enabled
    - processing_time: Time taken in seconds
    """
    
    # Track with decorator-like logic
    start_time_local = time.time()
    
    try:
        # Simulate document processing (in production, use actual classifier)
        # This would call DocumentClassifier().classify(request.document_path)
        await asyncio.sleep(0.1)  # Simulate processing
        
        response = ClassifyResponse(
            document_path=request.document_path,
            classification="invoice",
            confidence=0.92,
            category="financial",
            entities={
                "company": "Example Corp",
                "amount": 1500.50,
                "date": "2024-01-21",
                "invoice_number": "INV-2024-001"
            },
            validation={
                "is_valid": True,
                "score": 0.95,
                "issues": []
            } if request.validate_document else None,
            status="success",
            processing_time=time.time() - start_time_local,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Record metrics
        duration = time.time() - start_time_local
        metrics.classification_duration_seconds.labels(
            document_type=request.document_type
        ).observe(duration)
        
        metrics.classification_total.labels(
            status="success",
            document_type=request.document_type
        ).inc()
        
        metrics.classification_confidence.labels(
            document_type=request.document_type
        ).observe(response.confidence)
        
        logger.info(f"Classification successful: {request.document_path} -> {response.classification}")
        
        return response
    
    except Exception as e:
        metrics.classification_total.labels(
            status="error",
            document_type=request.document_type
        ).inc()
        metrics.errors_total.labels(error_type=type(e).__name__).inc()
        
        logger.error(f"Classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === BATCH PROCESSING ENDPOINTS ===

@app.post("/api/v1/batch", tags=["batch"], response_model=BatchResponse)
async def submit_batch(
    request: BatchRequest,
    background_tasks: BackgroundTasks
) -> BatchResponse:
    """
    Submit a batch of documents for processing
    
    Submits batch asynchronously and returns job ID for tracking.
    
    **Parameters:**
    - documents: List of document paths (1-10000 items)
    - validate_documents: Enable validation for all documents
    - priority: Job priority (normal/high/low)
    
    **Returns:**
    - job_id: Unique job identifier
    - status: Current job status (pending/processing/completed/failed)
    - results_url: URL to get results
    """
    
    job_id = f"batch_{uuid.uuid4().hex[:12]}"
    
    # Create job record
    batch_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_documents": len(request.documents),
        "processed": 0,
        "failed": 0,
        "documents": request.documents,
        "submitted_at": datetime.utcnow().isoformat(),
        "results": []
    }
    
    # Record metrics
    metrics.batch_jobs_submitted_total.inc()
    update_batch_queue_size(len(batch_jobs))
    
    # Add background task to process batch
    background_tasks.add_task(
        process_batch_background,
        job_id,
        request.documents,
        request.validate_documents
    )
    
    logger.info(f"Batch job submitted: {job_id} ({len(request.documents)} documents)")
    
    return BatchResponse(
        job_id=job_id,
        status="pending",
        total_documents=len(request.documents),
        processed=0,
        failed=0,
        results_url=f"/api/v1/batch/{job_id}/results",
        submitted_at=datetime.utcnow().isoformat()
    )


async def process_batch_background(job_id: str, documents: List[str], validate: bool):
    """
    Background task to process batch documents
    """
    job_start = time.time()
    job = batch_jobs[job_id]
    job["status"] = "processing"
    
    try:
        for idx, doc_path in enumerate(documents):
            try:
                # Simulate processing each document
                await asyncio.sleep(0.05)
                
                result = {
                    "document_path": doc_path,
                    "classification": "invoice",
                    "confidence": 0.92,
                    "status": "success"
                }
                
                job["results"].append(result)
                job["processed"] += 1
                
                metrics.batch_documents_processed_total.labels(status="success").inc()
            
            except Exception as e:
                job["failed"] += 1
                metrics.batch_documents_processed_total.labels(status="failed").inc()
                logger.error(f"Document processing failed: {doc_path}: {str(e)}")
        
        job["status"] = "completed"
        duration = time.time() - job_start
        
        metrics.batch_job_duration_seconds.observe(duration)
        metrics.batch_jobs_completed_total.labels(status="success").inc()
    
    except Exception as e:
        job["status"] = "failed"
        metrics.batch_jobs_completed_total.labels(status="failure").inc()
        logger.error(f"Batch processing failed: {job_id}: {str(e)}")
    
    finally:
        update_batch_queue_size(len(batch_jobs))


@app.get("/api/v1/batch/{job_id}/status", tags=["batch"], response_model=BatchStatus)
async def get_batch_status(job_id: str) -> BatchStatus:
    """
    Get batch job status
    
    **Parameters:**
    - job_id: Batch job identifier
    
    **Returns:**
    - Job status, progress, and estimated time remaining
    """
    
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[job_id]
    progress = (job["processed"] / job["total_documents"]) * 100 if job["total_documents"] > 0 else 0
    
    # Estimate time remaining
    if job["processed"] > 0 and job["status"] == "processing":
        elapsed = time.time() - datetime.fromisoformat(job["submitted_at"]).timestamp()
        time_per_doc = elapsed / job["processed"]
        remaining = (job["total_documents"] - job["processed"]) * time_per_doc
    else:
        remaining = None
    
    return BatchStatus(
        job_id=job_id,
        status=job["status"],
        total_documents=job["total_documents"],
        processed=job["processed"],
        failed=job["failed"],
        progress_percent=progress,
        estimated_time_remaining=remaining,
        updated_at=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/batch/{job_id}/results", tags=["batch"])
async def get_batch_results(
    job_id: str,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get batch job results (paginated)
    
    **Parameters:**
    - job_id: Batch job identifier
    - limit: Results per page (max 1000)
    - offset: Starting position
    
    **Returns:**
    - Paginated results with metadata
    """
    
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[job_id]
    total = len(job["results"])
    results = job["results"][offset:offset+limit]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_results": total,
        "returned": len(results),
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
        "results": results
    }


# === ROOT ENDPOINT ===

@app.get("/", tags=["info"])
async def root() -> Dict[str, Any]:
    """
    API information endpoint
    """
    return {
        "name": "DocTender API",
        "version": "1.2.0",
        "description": "Production-grade Document Classification with REST API, Batch Processing, and Monitoring",
        "docs_url": "/api/v1/docs",
        "health_url": "/health",
        "metrics_url": "/metrics",
        "endpoints": {
            "classification": "POST /api/v1/classify",
            "batch_submit": "POST /api/v1/batch",
            "batch_status": "GET /api/v1/batch/{job_id}/status",
            "batch_results": "GET /api/v1/batch/{job_id}/results",
            "health": "GET /health",
            "metrics": "GET /metrics"
        }
    }


# === STARTUP/SHUTDOWN EVENTS ===

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("DocTender API v1.2.0 starting...")
    set_classifier_ready(True)
    set_classifier_accuracy(0.91)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("DocTender API shutting down...")


# Import asyncio at module level
import asyncio


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
