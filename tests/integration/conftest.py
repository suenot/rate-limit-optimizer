"""
Конфигурация для интеграционных тестов Rate Limit Optimizer
"""
import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import patch

import aiohttp
from aioresponses import aioresponses


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Создает временную директорию для тестов"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Мокает переменные окружения для тестов"""
    test_env = {
        "OPENROUTER_API_KEY": "test-openrouter-key-123",
        "RATE_LIMIT_CONFIG_PATH": "/tmp/test_config.json",
        "RATE_LIMIT_LOG_LEVEL": "DEBUG",
        "AI_RECOMMENDATIONS_ENABLED": "true",
        "REDIS_URL": "redis://localhost:6379/1",  # Тестовая база
        "PROMETHEUS_PORT": "9091",  # Альтернативный порт для тестов
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
async def aiohttp_session() -> Generator[aiohttp.ClientSession, None, None]:
    """Создает aiohttp сессию для тестов"""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def sample_rate_limit_headers() -> Dict[str, str]:
    """Стандартные заголовки rate limit для тестов"""
    return {
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "95",
        "X-RateLimit-Reset": "1640995200",
        "X-RateLimit-Window": "60",
        "Content-Type": "application/json"
    }


@pytest.fixture
def comprehensive_rate_limit_headers() -> Dict[str, str]:
    """Полный набор заголовков для многоуровневых лимитов"""
    return {
        # 10-секундные лимиты
        "X-RateLimit-Limit-10s": "20",
        "X-RateLimit-Remaining-10s": "15",
        "X-RateLimit-Reset-10s": "1640995210",
        
        # Минутные лимиты
        "X-RateLimit-Limit-Minute": "100",
        "X-RateLimit-Remaining-Minute": "85",
        "X-RateLimit-Reset-Minute": "1640995260",
        
        # 15-минутные лимиты
        "X-RateLimit-Limit-15min": "1000",
        "X-RateLimit-Remaining-15min": "850",
        "X-RateLimit-Reset-15min": "1640996100",
        
        # Часовые лимиты
        "X-RateLimit-Limit-Hour": "5000",
        "X-RateLimit-Remaining-Hour": "4200",
        "X-RateLimit-Reset-Hour": "1640998800",
        
        # Дневные лимиты
        "X-RateLimit-Limit-Day": "100000",
        "X-RateLimit-Remaining-Day": "95000",
        "X-RateLimit-Reset-Day": "1641081600",
        
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_openrouter_success_response() -> Dict[str, Any]:
    """Успешный ответ от OpenRouter API"""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1640995200,
        "model": "anthropic/claude-3.5-sonnet",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """{
                        "optimal_usage_strategy": "Рекомендуется использовать 85 запросов в минуту с буферизацией для пиковых нагрузок",
                        "implementation_patterns": [
                            "Реализуйте token bucket алгоритм с размером bucket = 100 токенов",
                            "Используйте экспоненциальный backoff: 1s, 2s, 4s при получении 429",
                            "Добавьте jitter (±10%) к интервалам между запросами"
                        ],
                        "error_handling_advice": [
                            "При 429 ошибке ждите время из заголовка Retry-After",
                            "Реализуйте circuit breaker после 3 последовательных 429 ошибок",
                            "Логируйте все rate limit события для анализа паттернов"
                        ],
                        "monitoring_suggestions": [
                            "Отслеживайте метрику requests_per_minute в реальном времени",
                            "Настройте алерты при превышении 90% от лимита",
                            "Мониторьте время сброса лимитов для планирования нагрузки"
                        ],
                        "scaling_recommendations": [
                            "Для масштабирования используйте несколько API ключей с ротацией",
                            "Рассмотрите кэширование ответов на 30-60 секунд",
                            "Реализуйте приоритизацию запросов: критичные vs некритичные"
                        ],
                        "confidence_score": 0.92,
                        "risk_assessment": "LOW - Лимиты четко определены, API предоставляет полные заголовки",
                        "estimated_cost_impact": "При соблюдении рекомендаций ожидается 0% ошибок 429"
                    }"""
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 1250,
            "completion_tokens": 850,
            "total_tokens": 2100
        }
    }


@pytest.fixture
def sample_test_config() -> Dict[str, Any]:
    """Базовая конфигурация для тестов"""
    return {
        "version": "1.0.0",
        "description": "Test Rate Limit Optimizer Configuration",
        "target_sites": {
            "test_api": {
                "base_url": "https://api.test.com",
                "endpoints": ["/v1/test", "/v1/data"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9"
                },
                "auth": {"type": "none"}
            }
        },
        "detection_settings": {
            "multi_tier_detection": {
                "enabled": True,
                "test_all_tiers": False,
                "tiers_to_test": [
                    {
                        "name": "10_seconds",
                        "window_seconds": 10,
                        "start_rate": 1,
                        "max_rate": 50,
                        "increment": 2,
                        "test_duration_minutes": 0.1  # Быстрые тесты
                    }
                ]
            },
            "batch_settings": {
                "requests_per_batch": 5,
                "batch_interval_seconds": 0.1,  # Быстрые интервалы для тестов
                "adaptive_batching": True
            },
            "safety_settings": {
                "safety_margin_percent": 10,
                "backoff_multiplier": 1.5,
                "max_consecutive_errors": 2
            }
        },
        "optimization_strategies": {
            "multi_tier_ramp": {
                "enabled": True,
                "tier_order": ["10_seconds"],
                "stop_on_first_limit": True
            }
        },
        "ai_recommendations": {
            "enabled": True,
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "api_key_env": "OPENROUTER_API_KEY"
        },
        "results_storage": {
            "save_results": True,
            "output_format": "json",
            "output_file": "test_results.json"
        }
    }


# Маркеры для различных типов тестов
def pytest_configure(config):
    """Конфигурация pytest с кастомными маркерами"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )
    config.addinivalue_line(
        "markers", "ai: marks tests that use AI services"
    )
    config.addinivalue_line(
        "markers", "performance: marks performance tests"
    )


# Фикстуры для пропуска тестов в определенных условиях
@pytest.fixture(autouse=True)
def skip_if_no_network(request):
    """Пропускает тесты требующие сеть если сеть недоступна"""
    if request.node.get_closest_marker('network'):
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except OSError:
            pytest.skip("Network not available")


@pytest.fixture(autouse=True) 
def skip_if_no_ai_key(request):
    """Пропускает AI тесты если нет API ключа"""
    if request.node.get_closest_marker('ai'):
        if not os.getenv('OPENROUTER_API_KEY') and not os.getenv('TEST_OPENROUTER_API_KEY'):
            pytest.skip("OpenRouter API key not available")


# Утилиты для тестов
class TestUtils:
    """Утилиты для интеграционных тестов"""
    
    @staticmethod
    def create_mock_response(status: int = 200, payload: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Создает мок ответа для aioresponses"""
        return {
            "status": status,
            "payload": payload or {"success": True},
            "headers": headers or {"Content-Type": "application/json"}
        }
    
    @staticmethod
    def create_rate_limit_error_response(limit: int = 100, remaining: int = 0, reset_time: int = None):
        """Создает мок ответа с ошибкой rate limit"""
        if reset_time is None:
            import time
            reset_time = int(time.time() + 60)
        
        return {
            "status": 429,
            "payload": {"error": "Rate limit exceeded"},
            "headers": {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": "60",
                "Content-Type": "application/json"
            }
        }


@pytest.fixture
def test_utils():
    """Предоставляет утилиты для тестов"""
    return TestUtils
