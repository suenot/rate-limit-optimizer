# 🧪 Запуск тестов Rate Limit Optimizer

## Быстрый старт

```bash
# Установка зависимостей для тестирования
pip install -r tests/requirements.txt

# Запуск всех интеграционных тестов
pytest tests/integration/ -v

# Запуск с покрытием кода
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html

# Параллельный запуск (быстрее)
pytest tests/integration/ -n auto -v
```

## Категории тестов

```bash
# Тесты AI интеграции
pytest tests/integration/test_ai_integration.py -v -m ai

# Тесты производительности
pytest tests/integration/test_performance.py -v -m performance

# Медленные тесты (полное тестирование)
pytest tests/integration/ -v -m slow

# Сетевые тесты (требуют интернет)
pytest tests/integration/ -v -m network

# Быстрые тесты (исключая медленные)
pytest tests/integration/ -v -m "not slow"
```

## Отчеты

```bash
# HTML отчет о покрытии
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html
# Результат в htmlcov/index.html

# JSON отчет о тестах
pytest tests/integration/ --json-report --json-report-file=test_report.json

# Бенчмарк производительности
pytest tests/integration/test_performance.py --benchmark-only --benchmark-json=benchmark.json
```

## Переменные окружения для тестов

```bash
# Для тестов AI (опционально)
export OPENROUTER_API_KEY="your_test_key"

# Для отладки тестов
export PYTEST_CURRENT_TEST=1
export LOG_LEVEL=DEBUG
```

## Структура тестов

- `test_config_integration.py` - Тесты конфигурации
- `test_rate_limit_detection.py` - Тесты определения лимитов
- `test_multi_tier_detection.py` - Тесты многоуровневого определения
- `test_ai_integration.py` - Тесты AI рекомендаций
- `test_endpoint_rotation.py` - Тесты ротации endpoints
- `test_error_handling.py` - Тесты обработки ошибок
- `test_results_storage.py` - Тесты сохранения результатов
- `test_performance.py` - Тесты производительности

## Отладка тестов

```bash
# Запуск одного теста с отладкой
pytest tests/integration/test_config_integration.py::test_config_loading -v -s

# Остановка на первой ошибке
pytest tests/integration/ -x

# Показать локальные переменные при ошибке
pytest tests/integration/ -l

# Подробный вывод
pytest tests/integration/ -vv
```

Все тесты написаны с использованием моков и не требуют реальных API ключей для базового функционирования!
