# 🚀 DocTender Deployment Guide

## Quick Start with Docker

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/OlegKarenkikh/DocTender.git
cd DocTender

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Option 2: Single Docker Container

```bash
# Build image
docker build -t doctender:1.0.0 .

# Run container
docker run -d \
  --name doctender-api \
  -p 8000:8000 \
  -v $(pwd)/documents:/app/documents \
  doctender:1.0.0

# Test API
curl http://localhost:8000/health
```

### Option 3: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml doctender

# Check services
docker service ls
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Single Document Classification
```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "/documents/invoice.pdf",
    "document_type": "auto",
    "validate_document": true
  }'
```

### Batch Processing
```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["/documents/doc1.pdf", "/documents/doc2.pdf"],
    "validate": true
  }'
```

### Get Batch Results
```bash
curl http://localhost:8000/api/v1/batch/{job_id}/results
```

## Production Deployment

### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doctender-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: doctender
  template:
    metadata:
      labels:
        app: doctender
    spec:
      containers:
      - name: api
        image: doctender:1.0.0
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

```bash
kubectl apply -f k8s-deployment.yaml
```

### AWS ECS

```bash
# Create ECR repository
aws ecr create-repository --repository-name doctender

# Tag and push image
docker tag doctender:1.0.0 {account}.dkr.ecr.{region}.amazonaws.com/doctender:1.0.0
docker push {account}.dkr.ecr.{region}.amazonaws.com/doctender:1.0.0

# Deploy to ECS
# Use AWS Console or CLI
```

## Performance Optimization

### Uvicorn Workers
```bash
# In docker-compose.yml or Dockerfile
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Load Balancing with Nginx
```nginx
upstream doctender {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://doctender;
        proxy_set_header Host $host;
    }
}
```

## Monitoring

### Prometheus

Add to api/main.py:
```python
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentor().instrument(app).expose(app)
```

### Grafana Dashboard

Import dashboard ID: 14323 (for FastAPI)

## Environment Variables

```bash
PYTHONUNBUFFERABLE=1
LOG_LEVEL=INFO
WORKERS=4
MAX_BATCH_SIZE=1000
CACHE_ENABLED=true
CACHE_TTL=3600
```

## Troubleshooting

### Container fails to start
```bash
docker logs doctender-api
```

### API returns 500 error
```bash
# Check classifier initialization
curl http://localhost:8000/health
```

### High memory usage
```bash
# Limit memory in docker-compose.yml
mem_limit: 4g
mem_reservation: 2g
```

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker rmi doctender:1.0.0
```

---

**For more details, see:** [README.md](README.md)
