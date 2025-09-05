# 📋 Rate Limit Optimizer - Команды

## 🚀 Основные команды для разработки

### Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка в режиме разработки
pip install -e .
```

### Запуск системы
```bash
# Основной запуск через модуль
python -m rate_limit_optimizer.main --config config.json --site example_api

# Через установленную команду
rate-limit-optimizer --config config.json --site example_api

# Короткая команда
rlo --config config.json --site example_api

# С дополнительными опциями
rlo --config config.json --site example_api --strategy multi_tier_ramp --output results.json --verbose --no-ai

# Установка пакета
pip install -e .

# Установка с зависимостями для разработки
pip install -e ".[dev]"

# Установка всех зависимостей
pip install -e ".[all]"
```

### Мониторинг и метрики
```bash
# Запуск Prometheus метрик
python -m rate_limit_optimizer.monitoring --port 8090

# Проверка здоровья системы
curl http://localhost:8080/health

# Получение текущих метрик
curl http://localhost:8090/metrics

# Просмотр статистики кэша
python -m rate_limit_optimizer.cache --stats
```

### Тестирование
```bash
# Установка зависимостей для тестирования
pip install -r tests/requirements.txt

# Запуск всех интеграционных тестов
pytest tests/integration/ -v

# Тесты с покрытием кода
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html

# Параллельный запуск тестов
pytest tests/integration/ -n auto -v

# Конкретные категории тестов
pytest tests/integration/test_config_integration.py -v          # Конфигурация
pytest tests/integration/test_rate_limit_detection.py -v       # Определение лимитов
pytest tests/integration/test_multi_tier_detection.py -v       # Многоуровневое определение
pytest tests/integration/test_ai_integration.py -v -m ai       # AI рекомендации
pytest tests/integration/test_endpoint_rotation.py -v          # Ротация endpoints
pytest tests/integration/test_error_handling.py -v             # Обработка ошибок
pytest tests/integration/test_results_storage.py -v            # Сохранение результатов
pytest tests/integration/test_performance.py -v -m performance # Производительность

# Фильтрация по маркерам
pytest tests/integration/ -m "not slow" -v                     # Быстрые тесты
pytest tests/integration/ -m "performance" -v                  # Тесты производительности
pytest tests/integration/ -m "not network" -v                  # Без сети
pytest tests/integration/ -m "ai" -v                           # AI тесты

# Отчеты
pytest tests/integration/ --cov=rate_limit_optimizer --cov-report=html
pytest tests/integration/ --json-report --json-report-file=test_report.json
pytest tests/integration/test_performance.py --benchmark-only --benchmark-json=benchmark.json
```

### Линтинг и форматирование
```bash
# Проверка типов
mypy rate_limit_optimizer/ --strict

# Форматирование кода
black rate_limit_optimizer/ tests/
isort rate_limit_optimizer/ tests/

# Проверка стиля кода
flake8 rate_limit_optimizer/ tests/

# Проверка безопасности
bandit -r rate_limit_optimizer/

# Комплексная проверка
pre-commit run --all-files
```

### Профилирование и отладка
```bash
# Профилирование памяти
python -m memory_profiler rate_limit_optimizer/main.py

# Профилирование производительности
python -m cProfile -o profile.stats rate_limit_optimizer/main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Мониторинг async операций
python -m aiomonitor rate_limit_optimizer/main.py
```

### Docker команды
```bash
# Сборка образа
docker build -t rate-limit-optimizer:latest .

# Запуск контейнера
docker run -d \
  --name rate-limit-optimizer \
  -p 8080:8080 \
  -p 8090:8090 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/logs:/app/logs \
  rate-limit-optimizer:latest

# Просмотр логов
docker logs -f rate-limit-optimizer

# Остановка и удаление
docker stop rate-limit-optimizer
docker rm rate-limit-optimizer
```

### Redis команды
```bash
# Запуск Redis в Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# Подключение к Redis CLI
docker exec -it redis redis-cli

# Просмотр ключей кэша
redis-cli KEYS "rate_limit:*"

# Очистка кэша
redis-cli FLUSHDB

# Мониторинг Redis
redis-cli MONITOR
```

### Утилиты конфигурации
```bash
# Валидация конфигурации
python -m rate_limit_optimizer.config --validate config.json

# Генерация примера конфигурации
python -m rate_limit_optimizer.config --generate-example > example_config.json

# Миграция конфигурации
python -m rate_limit_optimizer.config --migrate old_config.json new_config.json

# Проверка совместимости
python -m rate_limit_optimizer.config --check-compatibility config.json

# Обновление заголовков для маскировки (замена палевных User-Agent)
python -m rate_limit_optimizer.config --update-headers config.json
```

### Симуляция и тестирование нагрузки
```bash
# Симуляция нагрузки
python -m rate_limit_optimizer.simulation \
  --scenario normal_load \
  --duration 3600 \
  --request-rate 10.0

# Стресс-тестирование
python -m rate_limit_optimizer.simulation \
  --scenario high_load \
  --duration 1800 \
  --request-rate 50.0

# Тестирование отказоустойчивости
python -m rate_limit_optimizer.simulation \
  --scenario failure_recovery \
  --duration 900
```

### Экспорт и импорт данных
```bash
# Экспорт метрик
python -m rate_limit_optimizer.export \
  --format json \
  --output metrics_export.json \
  --start-date 2024-01-01 \
  --end-date 2024-01-31

# Экспорт конфигурации
python -m rate_limit_optimizer.export \
  --type config \
  --output config_backup.json

# Импорт исторических данных
python -m rate_limit_optimizer.import \
  --file historical_data.json \
  --type metrics
```

### Обслуживание и очистка
```bash
# Очистка старых логов
find logs/ -name "*.log" -mtime +30 -delete

# Очистка кэша
python -m rate_limit_optimizer.maintenance --clear-cache

# Ротация логов
python -m rate_limit_optimizer.maintenance --rotate-logs

# Проверка целостности данных
python -m rate_limit_optimizer.maintenance --check-integrity

# Оптимизация базы данных
python -m rate_limit_optimizer.maintenance --optimize-db
```

### CI/CD команды
```bash
# Подготовка к релизу
python -m rate_limit_optimizer.release --prepare

# Создание релиза
python -m rate_limit_optimizer.release --create --version 1.0.0

# Развертывание
python -m rate_limit_optimizer.deploy --environment production

# Откат версии
python -m rate_limit_optimizer.deploy --rollback --version 0.9.0
```

## 🔧 Переменные окружения

```bash
# Основные настройки
export RATE_LIMIT_CONFIG_PATH="/path/to/config.json"
export RATE_LIMIT_LOG_LEVEL="INFO"
export RATE_LIMIT_DEBUG="false"

# AI рекомендации
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export AI_RECOMMENDATIONS_ENABLED="true"
export AI_MODEL="anthropic/claude-3.5-sonnet"
export AI_TEMPERATURE="0.1"
export AI_MAX_TOKENS="2000"

# Redis настройки
export REDIS_URL="redis://localhost:6379/0"
export REDIS_PASSWORD=""
export REDIS_SSL="false"

# Мониторинг
export PROMETHEUS_PORT="8090"
export METRICS_ENABLED="true"
export HEALTH_CHECK_PORT="8080"

# Производительность
export MAX_CONCURRENT_REQUESTS="100"
export CONNECTION_TIMEOUT="30"
export READ_TIMEOUT="60"

# Безопасность
export API_KEY_ENCRYPTION="true"
export SSL_VERIFY="true"
export CERT_PATH=""
```

## 📊 Полезные алиасы

```bash
# Проверка валидности JSON конфигурации
python -m json.tool config.json > /dev/null && echo "JSON is valid" || echo "JSON is invalid"
```

## 🔧 Последние изменения

```bash
# БЫСТРОЕ ТЕСТИРОВАНИЕ: Настроено для тестирования только 10_seconds tier
# Конфигурация оптимизирована для определения лимита за 1 минуту:
# - test_all_tiers: false (тестируем только 10_seconds)
# - tier_order: ["10_seconds"] (только один tier)
# - stop_on_first_limit: true (останавливаемся при первом найденном лимите)
# - max_rate: 100 (увеличен для более агрессивного тестирования)
# - increment: 2 (быстрее наращиваем нагрузку)
# - batch_interval_seconds: 2 (быстрее между батчами)
# - safety_margin_percent: 10 (меньше запас безопасности)
# - timeout: 10 (быстрее таймаут)
# - max_concurrent_requests: 3 (меньше конкурентных запросов)
```

## 🚀 Команды для быстрого тестирования

```bash
# Запуск быстрого тестирования 10-секундного лимита
python -m rate_limit_optimizer --config config.json --site upbit_api

# Запуск с подробными логами для отслеживания процесса
python -m rate_limit_optimizer --config config.json --site upbit_api --debug

# Мониторинг результатов в реальном времени
tail -f rate_limit_optimizer.log
```

## 📊 Полезные алиасы

```bash
# Добавить в ~/.bashrc или ~/.zshrc
alias rlo-start="python -m rate_limit_optimizer --config config.json"
alias rlo-debug="python -m rate_limit_optimizer --config config.json --debug"
alias rlo-test="pytest tests/ -v"
alias rlo-lint="mypy rate_limit_optimizer/ && flake8 rate_limit_optimizer/"
alias rlo-format="black rate_limit_optimizer/ && isort rate_limit_optimizer/"
alias rlo-metrics="curl -s http://localhost:8090/metrics"
alias rlo-health="curl -s http://localhost:8080/health | jq"
alias rlo-logs="tail -f logs/rate_limit_optimizer.log"
```

## 🚨 Команды для экстренных ситуаций

```bash
# Экстренная остановка
pkill -f "rate_limit_optimizer"

# Сброс всех лимитов
python -m rate_limit_optimizer.emergency --reset-all-limits

# Включение аварийного режима
python -m rate_limit_optimizer.emergency --enable-emergency-mode

# Отключение всех стратегий кроме базовой
python -m rate_limit_optimizer.emergency --fallback-mode

# Создание дампа состояния системы
python -m rate_limit_optimizer.emergency --create-dump

# Восстановление из резервной копии
python -m rate_limit_optimizer.emergency --restore-from-backup backup.json
```
