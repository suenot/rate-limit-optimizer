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
# Запуск основного оптимизатора с AI рекомендациями
python -m rate_limit_optimizer --config config.json

# Запуск без AI рекомендаций (быстрее)
python -m rate_limit_optimizer --config config.json --no-ai

# Запуск в debug режиме
python -m rate_limit_optimizer --config config.json --debug

# Запуск с отключенной ротацией endpoints (тестирование только одного)
python -m rate_limit_optimizer --config config.json --single-endpoint

# Запуск с кастомной стратегией ротации
python -m rate_limit_optimizer --config config.json --rotation-strategy sequential

# Запуск с кастомной конфигурацией
python -m rate_limit_optimizer --config custom_config.json --log-level DEBUG

# Запуск только AI анализа для существующих результатов
python -m rate_limit_optimizer --analyze-only results.json
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
# Запуск всех тестов
pytest tests/ -v

# Запуск тестов с покрытием
pytest tests/ --cov=rate_limit_optimizer --cov-report=html

# Запуск интеграционных тестов
pytest tests/integration/ -v

# Запуск тестов производительности
pytest tests/performance/ -v --benchmark-only
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
