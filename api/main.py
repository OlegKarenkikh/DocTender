#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocTender Production API
REST API для классификации документов на основе FastAPI

Возможности:
- Single document classification
- Batch processing (async)
- Health checks & monitoring
- Request validation
- Error handling
- Rate limiting ready
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import asyncio
import uuid

try:
    from src.document_classifier_system import DocumentClassifier
except ImportError:
    from document_classifier_system import DocumentClassifier

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models
# ============================================================================

class DocumentClassificationRequest(BaseModel):
    """Request для классификации одного документа"""
    document_path: str = Field(..., description="Путь до документа или содержимое текста")
    document_type: str = Field("auto", description="Явный тип документа или 'auto'")
    extract_entities: bool = Field(True, description="Извлекать ли сущности")
    validate_document: bool = Field(True, description="Выполнять ли валидацию")
    
    class Config:
        schema_extra = {
            "example": {
                "document_path": "/docs/invoice.pdf",
                "document_type": "auto",
                "extract_entities": True,
                "validate_document": True
            }
        }

class DocumentClassificationResponse(BaseModel):
    """Response с результатом классификации"""
    document_path: str
    classification: str = Field(..., description="Тип классифицированного документа")
    confidence: float = Field(..., description="Уверенность классификации (0-1)")
    category: str = Field(..., description="Группа документов")
    entities: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(..., description="'success', 'warning', 'error'")
    processing_time: float = Field(..., description="Время обработки в секундах")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "document_path": "/docs/invoice.pdf",
                "classification": "invoice",
                "confidence": 0.92,
                "category": "financial",
                "status": "success",
                "processing_time": 2.5,
                "timestamp": "2024-01-21T12:30:00"
            }
        }

class BatchClassificationRequest(BaseModel):
    """Request для пакетной обработки"""
    documents: List[str] = Field(..., description="Список путей до документов")
    validate: bool = Field(True)
    extract_entities: bool = Field(True)

class BatchJobResponse(BaseModel):
    """Response для пакетной обработки"""
    job_id: str = Field(..., description="Уникальный ID задачи")
    status: str = Field(..., description="'pending', 'processing', 'completed', 'failed'")
    total_documents: int
    processed: int
    failed: int
    results_url: Optional[str] = None
    created_at: str

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="'healthy', 'degraded', 'unhealthy'")
    version: str
    uptime_seconds: float
    classifier_loaded: bool
    documents_processed: int
    average_processing_time: float
    timestamp: str

# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="DocTender API",
    version="1.0.0",
    description="Production-grade API for procurement document classification",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc"
)

# Global state
class AppState:
    def __init__(self):
        self.classifier = None
        self.startup_time = datetime.now()
        self.documents_processed = 0
        self.total_processing_time = 0.0
        self.batch_jobs = {}

app_state = AppState()

# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Initializing DocTender API...")
    try:
        app_state.classifier = DocumentClassifier()
        logger.info("✅ Classifier loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load classifier: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("Shutting down DocTender API...")
    logger.info(f"📊 Total documents processed: {app_state.documents_processed}")

# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Check API health status"""
    uptime = (datetime.now() - app_state.startup_time).total_seconds()
    avg_time = (app_state.total_processing_time / max(app_state.documents_processed, 1))
    
    return HealthCheckResponse(
        status="healthy" if app_state.classifier else "unhealthy",
        version="1.0.0",
        uptime_seconds=uptime,
        classifier_loaded=app_state.classifier is not None,
        documents_processed=app_state.documents_processed,
        average_processing_time=avg_time,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# Classification Endpoints
# ============================================================================

@app.post("/api/v1/classify", response_model=DocumentClassificationResponse, tags=["Classification"])
async def classify_document(request: DocumentClassificationRequest):
    """Classify a single procurement document"""
    if not app_state.classifier:
        raise HTTPException(status_code=500, detail="Classifier not initialized")
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Classifying document: {request.document_path}")
        
        # Анализ документа
        result = app_state.classifier.analyze_document(
            request.document_path,
            request.document_type
        )
        
        processing_time = time.time() - start_time
        
        # Обновление статистики
        app_state.documents_processed += 1
        app_state.total_processing_time += processing_time
        
        response = DocumentClassificationResponse(
            document_path=request.document_path,
            classification=result.get('classification', 'unknown'),
            confidence=result.get('confidence', 0.0),
            category="financial",
            entities=result.get('entities', {}),
            status=result.get('status', 'success'),
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Classification successful: {response.classification} ({response.confidence:.2%})")
        return response
        
    except FileNotFoundError as e:
        logger.error(f"Document not found: {e}")
        raise HTTPException(status_code=400, detail=f"Document not found: {str(e)}")
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

# ============================================================================
# Batch Processing Endpoints
# ============================================================================

@app.post("/api/v1/batch", response_model=BatchJobResponse, tags=["Batch Processing"])
async def submit_batch(
    request: BatchClassificationRequest,
    background_tasks: BackgroundTasks
):
    """Submit batch of documents for asynchronous processing"""
    if not app_state.classifier:
        raise HTTPException(status_code=500, detail="Classifier not initialized")
    
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    
    # Генерирование ID задачи
    job_id = f"batch_{uuid.uuid4().hex[:8]}"
    
    # Инициализация задачи
    app_state.batch_jobs[job_id] = {
        "status": "pending",
        "total": len(request.documents),
        "processed": 0,
        "failed": 0,
        "results": [],
        "created_at": datetime.now().isoformat()
    }
    
    # Добавить в background tasks
    background_tasks.add_task(
        _process_batch,
        job_id,
        request.documents
    )
    
    logger.info(f"📦 Batch job submitted: {job_id} ({len(request.documents)} documents)")
    
    return BatchJobResponse(
        job_id=job_id,
        status="pending",
        total_documents=len(request.documents),
        processed=0,
        failed=0,
        results_url=f"/api/v1/batch/{job_id}/results",
        created_at=datetime.now().isoformat()
    )

@app.get("/api/v1/batch/{job_id}/status", response_model=BatchJobResponse, tags=["Batch Processing"])
async def get_batch_status(job_id: str):
    """Get status of batch processing job"""
    if job_id not in app_state.batch_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = app_state.batch_jobs[job_id]
    
    return BatchJobResponse(
        job_id=job_id,
        status=job["status"],
        total_documents=job["total"],
        processed=job["processed"],
        failed=job["failed"],
        results_url=f"/api/v1/batch/{job_id}/results",
        created_at=job["created_at"]
    )

@app.get("/api/v1/batch/{job_id}/results", tags=["Batch Processing"])
async def get_batch_results(job_id: str, limit: int = 100, offset: int = 0):
    """Get results of batch processing job"""
    if job_id not in app_state.batch_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = app_state.batch_jobs[job_id]
    results = job["results"][offset:offset+limit]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "total": len(job["results"]),
        "results": results
    }

# ============================================================================
# Background Tasks
# ============================================================================

async def _process_batch(job_id: str, documents: List[str]):
    """Background task для обработки batch"""
    logger.info(f"🔄 Processing batch {job_id}")
    job = app_state.batch_jobs[job_id]
    job["status"] = "processing"
    
    try:
        for doc_path in documents:
            try:
                result = app_state.classifier.analyze_document(doc_path)
                job["results"].append({
                    "document": doc_path,
                    "classification": result.get('classification'),
                    "confidence": result.get('confidence'),
                    "status": "success"
                })
                job["processed"] += 1
            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
                job["results"].append({
                    "document": doc_path,
                    "error": str(e),
                    "status": "failed"
                })
                job["failed"] += 1
            
            await asyncio.sleep(0.01)
        
        job["status"] = "completed"
        logger.info(f"✅ Batch {job_id} completed: {job['processed']} success, {job['failed']} failed")
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        job["status"] = "failed"

# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Get API information"""
    return {
        "name": "DocTender API",
        "version": "1.0.0",
        "description": "Production-grade API for procurement document classification",
        "docs": "/api/v1/docs",
        "health": "/health",
        "endpoints": {
            "classify": "POST /api/v1/classify",
            "batch": "POST /api/v1/batch",
            "batch_status": "GET /api/v1/batch/{job_id}/status",
            "batch_results": "GET /api/v1/batch/{job_id}/results",
            "health": "GET /health"
        }
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
