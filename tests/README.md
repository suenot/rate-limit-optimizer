# 🧪 Интеграционные тесты Rate Limit Optimizer

## 📋 Обзор

Комплексный набор интеграционных тестов для проверки всех компонентов системы определения и оптимизации rate limits. Тесты покрывают реальные сценарии использования и граничные случаи.

## 🏗️ Структура тестов

```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py                    # Конфигурация и фикстуры
│   ├── test_config_integration.py     # Тесты конфигурации
│   ├── test_rate_limit_detection.py   # Тесты определения лимитов
│   ├── test_multi_tier_detection.py   # Тесты многоуровневого определения
│   ├── test_ai_integration.py         # Тесты AI рекомендаций
│   ├── test_endpoint_rotation.py      # Тесты ротации endpoints
│   ├── test_error_handling.py         # Тесты обработки ошибок
│   ├── test_results_storage.py        # Тесты сохранения результатов
│   └── test_performance.py            # Тесты производительности
├── requirements.txt                   # Зависимости для тестирования
└── README.md                         # Этот файл
```

## 🚀 Запуск тестов

### Установка зависимостей

```bash
# Установка зависимостей для тестирования
pip install -r tests/requirements.txt

# Или установка основных зависимостей проекта
pip install -r requirements.txt
```

### Базовые команды

```bash
# Запуск всех интеграционных тестов
pytest tests/integration/ -v

# Запуск с покрытием кода
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html

# Запуск конкретного файла тестов
pytest tests/integration/test_config_integration.py -v

# Запуск конкретного теста
pytest tests/integration/test_config_integration.py::TestConfigIntegration::test_load_valid_config -v
```

### Параллельный запуск

```bash
# Запуск тестов в несколько потоков
pytest tests/integration/ -n 4 -v

# Автоматическое определение количества потоков
pytest tests/integration/ -n auto
```

### Фильтрация по маркерам

```bash
# Только быстрые тесты
pytest tests/integration/ -m "not slow" -v

# Только тесты производительности
pytest tests/integration/ -m "performance" -v

# Исключить тесты требующие сеть
pytest tests/integration/ -m "not network" -v

# Только AI тесты
pytest tests/integration/ -m "ai" -v
```

## 🔧 Конфигурация тестов

### Переменные окружения

```bash
# Обязательные для AI тестов
export OPENROUTER_API_KEY="your_openrouter_api_key"

# Опциональные
export RATE_LIMIT_LOG_LEVEL="DEBUG"
export REDIS_URL="redis://localhost:6379/1"
export PROMETHEUS_PORT="9091"
```

### Конфигурационный файл

Создайте `tests/test_config.json` для кастомной конфигурации:

```json
{
  "test_timeout": 30,
  "mock_external_apis": true,
  "enable_performance_tests": true,
  "ai_tests_enabled": false
}
```

## 📊 Типы тестов

### 1. Тесты конфигурации (`test_config_integration.py`)

- ✅ Загрузка и валидация config.json
- ✅ Обработка переменных окружения
- ✅ Валидация моделей Pydantic
- ✅ Сериализация/десериализация
- ✅ Обработка некорректных конфигураций

```bash
# Запуск тестов конфигурации
pytest tests/integration/test_config_integration.py -v
```

### 2. Тесты определения лимитов (`test_rate_limit_detection.py`)

- ✅ Извлечение лимитов из заголовков
- ✅ Тестирование через 429 ошибки
- ✅ Обработка Retry-After заголовков
- ✅ Параллельное тестирование
- ✅ Граничные случаи и ошибки

```bash
# Запуск тестов определения лимитов
pytest tests/integration/test_rate_limit_detection.py -v
```

### 3. Тесты многоуровневого определения (`test_multi_tier_detection.py`)

- ✅ Multi-Tier Ramp стратегия
- ✅ Intelligent Probing стратегия
- ✅ Header Analysis стратегия
- ✅ Кросс-валидация между уровнями
- ✅ Адаптивное увеличение частоты
- ✅ Параллельное тестирование уровней

```bash
# Запуск многоуровневых тестов
pytest tests/integration/test_multi_tier_detection.py -v
```

### 4. Тесты AI интеграции (`test_ai_integration.py`)

- ✅ Интеграция с OpenRouter API
- ✅ Генерация AI рекомендаций
- ✅ Обработка ошибок API
- ✅ Кэширование рекомендаций
- ✅ Fallback при недоступности AI
- ✅ Консенсус между моделями

```bash
# Запуск AI тестов (требует API ключ)
pytest tests/integration/test_ai_integration.py -v -m ai
```

### 5. Тесты ротации endpoints (`test_endpoint_rotation.py`)

- ✅ Случайная ротация
- ✅ Последовательная ротация
- ✅ Взвешенная ротация
- ✅ Избежание паттернов
- ✅ Обработка сбоев endpoints
- ✅ Адаптивная ротация по производительности

```bash
# Запуск тестов ротации
pytest tests/integration/test_endpoint_rotation.py -v
```

### 6. Тесты обработки ошибок (`test_error_handling.py`)

- ✅ Экспоненциальный backoff
- ✅ Circuit breaker паттерн
- ✅ Retry политики
- ✅ Обработка таймаутов
- ✅ Классификация ошибок
- ✅ Сбор статистики ошибок

```bash
# Запуск тестов обработки ошибок
pytest tests/integration/test_error_handling.py -v
```

### 7. Тесты сохранения результатов (`test_results_storage.py`)

- ✅ JSON сохранение/загрузка
- ✅ Сжатие результатов
- ✅ Ротация файлов
- ✅ Экспорт в различные форматы
- ✅ Шифрование данных
- ✅ Параллельное сохранение

```bash
# Запуск тестов хранения
pytest tests/integration/test_results_storage.py -v
```

### 8. Тесты производительности (`test_performance.py`)

- ✅ Мониторинг производительности
- ✅ Нагрузочное тестирование
- ✅ Стресс-тестирование
- ✅ Бенчмарки стратегий
- ✅ Мониторинг ресурсов
- ✅ Обнаружение регрессий

```bash
# Запуск тестов производительности
pytest tests/integration/test_performance.py -v -m performance
```

## 📈 Отчеты и метрики

### HTML отчет покрытия

```bash
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html
# Открыть htmlcov/index.html в браузере
```

### JSON отчет тестов

```bash
pytest tests/integration/ --json-report --json-report-file=test_report.json
```

### Бенчмарк отчет

```bash
pytest tests/integration/test_performance.py --benchmark-only --benchmark-json=benchmark.json
```

## 🐛 Отладка тестов

### Подробный вывод

```bash
# Максимально подробный вывод
pytest tests/integration/ -vvv -s

# Показать локальные переменные при ошибках
pytest tests/integration/ --tb=long -vvv

# Остановиться на первой ошибке
pytest tests/integration/ -x
```

### Профилирование

```bash
# Профилирование времени выполнения
pytest tests/integration/ --profile

# Профилирование памяти
pytest tests/integration/ --memray
```

## 🔍 Мокинг и фикстуры

### Основные фикстуры

- `temp_dir` - временная директория для тестов
- `mock_env_vars` - мокинг переменных окружения
- `aiohttp_session` - HTTP сессия для тестов
- `sample_rate_limit_headers` - стандартные заголовки
- `comprehensive_rate_limit_headers` - полный набор заголовков
- `mock_openrouter_success_response` - успешный ответ AI API
- `sample_test_config` - базовая конфигурация
- `test_utils` - утилиты для тестов

### Использование мокинга

```python
# Мокинг HTTP запросов
with aioresponses() as m:
    m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
    # Ваш тест здесь

# Мокинг переменных окружения
with patch.dict(os.environ, {"API_KEY": "test-key"}):
    # Ваш тест здесь
```

## 🚨 Требования к окружению

### Минимальные требования

- Python 3.11+
- pytest 7.4+
- aiohttp 3.8+
- pydantic 2.0+

### Опциональные зависимости

- Redis (для тестов кэширования)
- Docker (для контейнерных тестов)
- OpenRouter API ключ (для AI тестов)

### Системные требования

- RAM: минимум 2GB для полного набора тестов
- Диск: 1GB свободного места для временных файлов
- Сеть: доступ к интернету для некоторых тестов

## 📝 Написание новых тестов

### Шаблон интеграционного теста

```python
import pytest
from aioresponses import aioresponses

class TestNewFeatureIntegration:
    """Интеграционные тесты новой функциональности"""
    
    @pytest.mark.asyncio
    async def test_new_feature_success(self, sample_test_config):
        """Тест успешного выполнения новой функции"""
        with aioresponses() as m:
            m.get("https://api.test.com/v1/new", status=200, payload={"result": "success"})
            
            # Ваш тест здесь
            result = await your_function()
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_new_feature_error_handling(self):
        """Тест обработки ошибок"""
        with aioresponses() as m:
            m.get("https://api.test.com/v1/new", status=500)
            
            with pytest.raises(ExpectedError):
                await your_function()
```

### Лучшие практики

1. **Используйте описательные имена тестов**
2. **Мокайте внешние зависимости**
3. **Тестируйте граничные случаи**
4. **Используйте фикстуры для повторяющихся данных**
5. **Добавляйте маркеры для категоризации**
6. **Документируйте сложные тесты**

## 🔄 CI/CD интеграция

### GitHub Actions

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Локальные pre-commit хуки

```bash
# Установка pre-commit
pip install pre-commit
pre-commit install

# Запуск тестов перед коммитом
pre-commit run --all-files
```

## 📞 Поддержка

При возникновении проблем с тестами:

1. Проверьте переменные окружения
2. Убедитесь что все зависимости установлены
3. Проверьте доступность внешних сервисов
4. Изучите логи тестов с флагом `-vvv`
5. Создайте issue с подробным описанием проблемы
