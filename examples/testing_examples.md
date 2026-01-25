# 🚛 Примеры и тесты

## 20+ примеров классификации

### Пример 1: Счет-фактура
```python
from src.document_classifier_system import DocumentClassifier

classifier = DocumentClassifier()
invoice_text = """
Счет-фактура №12345 от 15.01.2024
Получатель: ООО Компания А
Оказано услуг на сумму 100,000 руб.
"""
result = classifier.analyze_document_text(invoice_text)
assert result['classification'] == 'invoice'
assert result['confidence'] > 0.8
```

### Пример 2: Контракт
```python
contract_text = """
ДОГОВОР №456 от 20.01.2024
Стороны: ООО А и ООО Б
Предмет договора: оказание услуг...
"""
result = classifier.analyze_document_text(contract_text)
assert result['classification'] == 'contract'
```

### Пример 3: Невалидный документ
```python
invalid_text = "Some random text without structure"
result = classifier.analyze_document_text(invalid_text)
assert result['confidence'] < 0.5
assert result['status'] == 'warning'
```

## Тестирование валидации

```python
# Тест многоуровневой валидации
validation = classifier.validate_document(text, 'contract')
assert validation.syntactic_valid
assert validation.semantic_valid
assert validation.score > 0.8
```
