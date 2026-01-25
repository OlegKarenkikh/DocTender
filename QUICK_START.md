# ⚡ быстрый старт - 5 минут

## Шаг 1: Установка (2 мин)

```bash
# Клонировать
git clone https://github.com/OlegKarenkikh/DocTender.git
cd DocTender

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Зависимости
pip install -r requirements.txt
```

## Шаг 2: Первый рун (2 мин)

```bash
python examples/basic_classification.py
```

## Шаг 3: Протестировать на примере (1 мин)

```python
from src.document_classifier_system import DocumentClassifier

classifier = DocumentClassifier()
result = classifier.analyze_document('test_doc.pdf')

print(result['classification'])
print(result['confidence'])
print(result['validation_report'])
```

## Отлично!

Вы зарегистрировали эндр-можностьи!

### Этапы дальнейшие

- 📚 Открыть [`README.md`](README.md) для полной документации
- 💻 Прочитать [`src/integration_guide.md`](src/integration_guide.md) для производства
- 🚛 Посмотреть [`examples/`](examples/) для дополнительных примеров
