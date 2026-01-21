# 📋 DocTender – Начните с этого!

## 🙋 Не знаете, с чего начать?

Это страница – ваша ландинг для быстрого навигирования.

---

## 📑 Выберите свою роль

### 🚀 🔋 Чистый старт (если вы в спешке)

Время: **5 минут**

```bash
git clone https://github.com/OlegKarenkikh/DocTender.git
cd DocTender
pip install -r requirements.txt
python examples/basic_classification.py
```

Где правильно посмотреть: → [`QUICK_START.md`](QUICK_START.md)

---

### 📄 У меня вопросы и сомнения

Время: **10 минут**

Начните с главного README для полного понимания:

→ [`README.md`](README.md)

---

### 📚 Мне нужна полная документация

Время: **1-3 часа**

Основные документы в папке `docs/`:

- **research_notes.md** (371 стр) - Глубокое исследование
- **PROJECT_STATUS.md** - Статус проекта
- **SUMMARY.md** - Полный обзор
- **INDEX.md** - Полный индекс

→ [`docs/`](docs/)

---

### 💻 Я – разработчик и хочу работать с кодом

Время: **2-3 часа**

Исходные коды в папке `src/`:

1. **document_classifier_system.py** (707 стр) - Основной классификатор
2. **integration_guide.md** (673 стр) - Детальные интеграция
3. **qwen3_system_prompt.md** (466 стр) - LLM оптимизация

→ [`src/`](src/)

---

### 🚛 Я – тестировщик / аналитик

Время: **1-2 часа**

Примеры и тесты в папке `examples/`:

- **testing_examples.md** (668 стр) - 20+ готовых сценариев
- **basic_classification.py** - Базовые примеры
- **advanced_validation.py** - Продвинутые тесты

→ [`examples/`](examples/)

---

### 👤 Я – менеджер / заказчик

Время: **30 минут**

Начните с этого:

→ [`docs/SUMMARY.md`](docs/SUMMARY.md) - Полные результаты
→ [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Статус проекта

---

## 📊 Расчет выделенного времени

| Кто | Начать | Время | Результат |
|--------|---------|------|----------|
| **Новичок** | `QUICK_START.md` | 5 мин | Проба работы |
| **Разработчик** | `src/document_classifier_system.py` | 2-3 ч | Полная интеграция |
| **Эксперт** | `docs/research_notes.md` | 30 мин | Полные знания |
| **Менеджер** | `docs/SUMMARY.md` | 30 мин | Понимание |

---

## 📄 Штрих-коды всех папок

```
DocTender/
├─ README.md ........................ МГ документация
├─ 00_START_HERE.md ................. Вы на этой странице!
├─ QUICK_START.md ................... Быстрые примеры
│
├─ docs/ ........................... Прочая документация
│   ├─ research_notes.md
│   ├─ SUMMARY.md
│   ├─ PROJECT_STATUS.md
│   ├─ INDEX.md
│   └─ FILES_GUIDE.md
│
├─ src/ ............................ Исходные коды
│   ├─ document_classifier_system.py
│   ├─ integration_guide.md
│   └─ qwen3_system_prompt.md
│
├─ examples/ ....................... Примеры и тесты
│   ├─ testing_examples.md
│   ├─ basic_classification.py
│   ├─ advanced_validation.py
│   └─ qwen3_integration.py
│
├─ requirements.txt ............... Зависимости Python
└─ LICENSE ......................... MIT
```

---

## 🚀 Пары команд для действия

### Основные
```bash
# Клонировать
git clone https://github.com/OlegKarenkikh/DocTender.git

# Установить зависимости
pip install -r requirements.txt

# Простая классификация
python examples/basic_classification.py
```

---

## 🌟 Ныжна промысленная реализация?

👉 Открыть [`src/integration_guide.md`](src/integration_guide.md)

Данные на вкус:
- PostgreSQL, Oracle, MySQL
- RTS Marketplace API
- Elasticsearch
- Docker

---

## 📞 Помощь!

- 🤔 **Вопросы?** → [`README.md` FAQ секция](README.md#faq)
- 📎 **Ошибка?** → [Issues](https://github.com/OlegKarenkikh/DocTender/issues)
- 🚀 **Предложение?** → [Pull Requests](https://github.com/OlegKarenkikh/DocTender/pulls)

---

## 🎣 Кюсокод всего

**30 секунд до результата:**

```python
from document_classifier_system import DocumentClassifier

# Начать
classifier = DocumentClassifier()

# Анализировать
result = classifier.analyze_document('document.pdf')

# Получить результат
print(result['classification'])  # Тип документа
# Юридические -> Договор

print(result['confidence'])      # Это точно 92%
# 0.92

print(result['validation_report']) # Детальные проверки
```

---

## ✨ Удачи в работе!

🌟 Полученные результаты:
- 🎉 **91% F1-Score**
- 👀 **97% без галлюцинаций LLM**
- ⚡ **2-5 секунд на документ**

🃋 Всего что вам нужно **в этом репозитории**!
