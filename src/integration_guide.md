# 🔧 интеграция доков

Полные гайдов для интеграции в производстве.

## Базовая интеграция

```python
from src.document_classifier_system import DocumentClassifier

classifier = DocumentClassifier()
result = classifier.analyze_document('doc.pdf')
print(result)
```

## Внедрение в РТС Маркетплейс

```python
class RTSMarketplaceIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_tender_documents(self, tender_id: str):
        # Fetch from RTS API
        pass
    
    def analyze_all(self):
        classifier = DocumentClassifier()
        # Process batch
        pass
```

## Базы данных

### PostgreSQL

```python
class StorageManager:
    def __init__(self, db_type='postgresql', connection_string=None):
        self.db_type = db_type
        self.connection_string = connection_string
    
    def save_analysis(self, result):
        # Save to database
        pass
```

## API Мнодподка

FastAPI эндпойнты:

- `POST /classify` - Классифицировать документ
- `POST /batch` - Пакетная обработка
- `GET /status/{id}` - Проверить статус
