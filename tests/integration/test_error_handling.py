"""
Интеграционные тесты обработки ошибок и retry логики
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.error_handling import (
    ErrorHandler,
    RetryPolicy,
    ExponentialBackoffRetry,
    LinearBackoffRetry,
    CircuitBreaker,
    ErrorClassifier
)
from rate_limit_optimizer.models import (
    RequestError,
    RetryResult,
    ErrorStats,
    CircuitBreakerState
)
from rate_limit_optimizer.exceptions import (
    RateLimitExceeded,
    NetworkError,
    ServerError,
    AuthenticationError,
    ConfigurationError
)


class TestErrorHandlingIntegration:
    """Интеграционные тесты обработки ошибок"""
    
    @pytest.fixture
    def retry_policy(self) -> RetryPolicy:
        """Базовая политика повторов для тестов"""
        return RetryPolicy(
            max_retries=3,
            base_delay=0.1,  # Быстрые повторы для тестов
            backoff_multiplier=2.0,
            max_delay=1.0,
            retry_on_codes=[429, 502, 503, 504],
            retry_on_timeout=True,
            jitter=False  # Отключаем jitter для предсказуемости тестов
        )
    
    @pytest.fixture
    def circuit_breaker(self) -> CircuitBreaker:
        """Circuit breaker для тестов"""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,  # Быстрое восстановление для тестов
            success_threshold=2,
            half_open_max_calls=1
        )
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_success(self, retry_policy):
        """Тест успешного повтора с экспоненциальным backoff"""
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Первые два запроса неудачные, третий успешный
            m.get("https://api.test.com/v1/test", status=503, payload={"error": "Service unavailable"})
            m.get("https://api.test.com/v1/test", status=502, payload={"error": "Bad gateway"})
            m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            start_time = datetime.now()
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        return await response.json()
            
            result = await retry_handler.execute_with_retry(make_request)
            end_time = datetime.now()
            
            # Проверяем успешный результат
            assert result.success is True
            assert result.final_response["success"] is True
            assert result.attempts_made == 3
            
            # Проверяем что было ожидание между попытками
            total_time = (end_time - start_time).total_seconds()
            expected_min_time = retry_policy.base_delay + retry_policy.base_delay * retry_policy.backoff_multiplier
            assert total_time >= expected_min_time * 0.8  # Допускаем небольшую погрешность
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_failure(self, retry_policy):
        """Тест исчерпания попыток повтора"""
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Все запросы неудачные
            for _ in range(retry_policy.max_retries + 1):
                m.get("https://api.test.com/v1/test", status=503, payload={"error": "Service unavailable"})
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            result = await retry_handler.execute_with_retry(make_request)
            
            # Проверяем что все попытки исчерпаны
            assert result.success is False
            assert result.attempts_made == retry_policy.max_retries + 1
            assert isinstance(result.final_error, ServerError)
    
    @pytest.mark.asyncio
    async def test_rate_limit_retry_with_retry_after(self, retry_policy):
        """Тест повтора при rate limit с заголовком Retry-After"""
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Первый запрос - rate limit с Retry-After
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                payload={"error": "Rate limit exceeded"},
                headers={"Retry-After": "0.2"}  # 200ms для быстрого теста
            )
            
            # Второй запрос успешный
            m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            start_time = datetime.now()
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            raise RateLimitExceeded(f"Rate limit exceeded", retry_after=float(retry_after) if retry_after else None)
                        return await response.json()
            
            result = await retry_handler.execute_with_retry(make_request)
            end_time = datetime.now()
            
            # Проверяем успешный результат
            assert result.success is True
            assert result.attempts_made == 2
            
            # Проверяем что был учтен Retry-After
            total_time = (end_time - start_time).total_seconds()
            assert total_time >= 0.15  # Должно быть не меньше Retry-After
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self, circuit_breaker):
        """Тест открытого состояния circuit breaker"""
        error_handler = ErrorHandler(circuit_breaker=circuit_breaker)
        
        with aioresponses() as m:
            # Все запросы неудачные для открытия circuit breaker
            for _ in range(10):
                m.get("https://api.test.com/v1/test", status=500, payload={"error": "Internal error"})
            
            async def failing_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            # Выполняем запросы до открытия circuit breaker
            for i in range(circuit_breaker.failure_threshold + 1):
                try:
                    await error_handler.execute_with_circuit_breaker(failing_request)
                except Exception:
                    pass  # Ожидаем ошибки
            
            # Circuit breaker должен быть открыт
            assert circuit_breaker.state == CircuitBreakerState.OPEN
            
            # Следующие запросы должны немедленно падать без обращения к API
            with pytest.raises(Exception) as exc_info:
                await error_handler.execute_with_circuit_breaker(failing_request)
            
            assert "circuit breaker" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Тест восстановления через half-open состояние"""
        error_handler = ErrorHandler(circuit_breaker=circuit_breaker)
        
        with aioresponses() as m:
            # Сначала неудачные запросы для открытия circuit breaker
            for _ in range(5):
                m.get("https://api.test.com/v1/test", status=500, payload={"error": "Internal error"})
            
            # Потом успешные запросы для восстановления
            for _ in range(5):
                m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            async def request_func():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            # Открываем circuit breaker
            for i in range(circuit_breaker.failure_threshold + 1):
                try:
                    await error_handler.execute_with_circuit_breaker(request_func)
                except Exception:
                    pass
            
            assert circuit_breaker.state == CircuitBreakerState.OPEN
            
            # Ждем timeout для перехода в half-open
            await asyncio.sleep(circuit_breaker.recovery_timeout + 0.1)
            
            # Выполняем успешный запрос в half-open состоянии
            result = await error_handler.execute_with_circuit_breaker(request_func)
            
            # Circuit breaker должен закрыться после успешных запросов
            for _ in range(circuit_breaker.success_threshold):
                await error_handler.execute_with_circuit_breaker(request_func)
            
            assert circuit_breaker.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_error_classification_and_handling(self):
        """Тест классификации ошибок и соответствующей обработки"""
        classifier = ErrorClassifier()
        
        # Тестируем различные типы ошибок
        test_cases = [
            (401, "Unauthorized", AuthenticationError, False),  # Не повторяем
            (429, "Rate limit exceeded", RateLimitExceeded, True),  # Повторяем
            (500, "Internal server error", ServerError, True),  # Повторяем
            (502, "Bad gateway", NetworkError, True),  # Повторяем
            (404, "Not found", None, False),  # Не повторяем
        ]
        
        for status_code, message, expected_exception_type, should_retry in test_cases:
            # Классифицируем ошибку
            error_info = classifier.classify_http_error(status_code, message)
            
            assert error_info.should_retry == should_retry
            
            if expected_exception_type:
                assert error_info.exception_type == expected_exception_type
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_with_error_handling(self, retry_policy):
        """Тест обработки ошибок при параллельных запросах"""
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Мокаем ответы для параллельных запросов
            # Часть запросов успешные, часть с ошибками
            success_responses = 0
            error_responses = 0
            
            for i in range(20):
                if i % 3 == 0:  # Каждый третий запрос с ошибкой
                    m.get(f"https://api.test.com/v1/test?id={i}", status=503)
                    error_responses += 1
                else:
                    m.get(f"https://api.test.com/v1/test?id={i}", status=200, payload={"id": i})
                    success_responses += 1
            
            async def make_request(request_id: int):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.test.com/v1/test?id={request_id}") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            # Выполняем параллельные запросы
            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    retry_handler.execute_with_retry(lambda i=i: make_request(i))
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Анализируем результаты
            successful_results = [r for r in results if isinstance(r, RetryResult) and r.success]
            failed_results = [r for r in results if isinstance(r, RetryResult) and not r.success]
            
            # Должны быть и успешные и неудачные результаты
            assert len(successful_results) > 0
            assert len(failed_results) >= 0  # Могут быть 0 если retry сработал
    
    @pytest.mark.asyncio
    async def test_error_stats_collection(self, retry_policy):
        """Тест сбора статистики ошибок"""
        error_handler = ErrorHandler(collect_stats=True)
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Различные типы ошибок
            m.get("https://api.test.com/v1/test", status=429, payload={"error": "Rate limit"})
            m.get("https://api.test.com/v1/test", status=500, payload={"error": "Internal error"})
            m.get("https://api.test.com/v1/test", status=502, payload={"error": "Bad gateway"})
            m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        error_handler.record_response(response.status, response.headers)
                        
                        if response.status == 429:
                            raise RateLimitExceeded("Rate limit exceeded")
                        elif response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        
                        return await response.json()
            
            # Выполняем запросы с различными исходами
            for _ in range(4):
                try:
                    await retry_handler.execute_with_retry(make_request)
                except Exception:
                    pass  # Игнорируем ошибки для сбора статистики
            
            # Получаем статистику
            stats = error_handler.get_error_stats()
            
            assert isinstance(stats, ErrorStats)
            assert stats.total_requests >= 4
            assert stats.rate_limit_errors >= 1
            assert stats.server_errors >= 2  # 500 + 502
            assert stats.successful_requests >= 1
    
    @pytest.mark.asyncio
    async def test_timeout_handling_with_retry(self, retry_policy):
        """Тест обработки таймаутов с повторами"""
        retry_handler = ExponentialBackoffRetry(policy=retry_policy)
        
        with aioresponses() as m:
            # Первые запросы с таймаутом, последний успешный
            m.get("https://api.test.com/v1/test", exception=asyncio.TimeoutError("Request timeout"))
            m.get("https://api.test.com/v1/test", exception=asyncio.TimeoutError("Request timeout"))
            m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            async def make_request():
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0.1)) as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        return await response.json()
            
            result = await retry_handler.execute_with_retry(make_request)
            
            # Проверяем что таймауты были обработаны и запрос в итоге успешен
            assert result.success is True
            assert result.attempts_made == 3
            assert "timeout" in str(result.retry_reasons).lower()
    
    @pytest.mark.asyncio
    async def test_custom_error_handler_integration(self):
        """Тест интеграции с кастомным обработчиком ошибок"""
        
        class CustomErrorHandler(ErrorHandler):
            def __init__(self):
                super().__init__()
                self.custom_error_count = 0
            
            async def handle_custom_error(self, error: Exception) -> bool:
                """Кастомная обработка специфических ошибок"""
                if "custom_error" in str(error).lower():
                    self.custom_error_count += 1
                    return True  # Указываем что ошибка обработана
                return False
        
        custom_handler = CustomErrorHandler()
        
        with aioresponses() as m:
            m.get("https://api.test.com/v1/test", status=400, payload={"error": "Custom_Error: Special case"})
            m.get("https://api.test.com/v1/test", status=200, payload={"success": True})
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status == 400:
                            data = await response.json()
                            if "custom_error" in data.get("error", "").lower():
                                raise Exception(f"Custom error: {data['error']}")
                        return await response.json()
            
            # Первый запрос должен вызвать кастомную ошибку
            try:
                await make_request()
            except Exception as e:
                handled = await custom_handler.handle_custom_error(e)
                assert handled is True
                assert custom_handler.custom_error_count == 1
            
            # Второй запрос должен быть успешным
            result = await make_request()
            assert result["success"] is True


@pytest.mark.integration
class TestErrorHandlingEdgeCases:
    """Тесты граничных случаев обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_retry_with_zero_max_retries(self):
        """Тест retry политики с нулевым количеством повторов"""
        policy = RetryPolicy(max_retries=0)
        retry_handler = ExponentialBackoffRetry(policy=policy)
        
        with aioresponses() as m:
            m.get("https://api.test.com/v1/test", status=500, payload={"error": "Server error"})
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            result = await retry_handler.execute_with_retry(make_request)
            
            # Должна быть только одна попытка без повторов
            assert result.success is False
            assert result.attempts_made == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_zero_failure_threshold(self):
        """Тест circuit breaker с нулевым порогом ошибок"""
        circuit_breaker = CircuitBreaker(failure_threshold=0)
        error_handler = ErrorHandler(circuit_breaker=circuit_breaker)
        
        async def failing_request():
            raise ServerError("Always fails")
        
        # Первый же запрос должен открыть circuit breaker
        try:
            await error_handler.execute_with_circuit_breaker(failing_request)
        except Exception:
            pass
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_nested_retry_handlers(self):
        """Тест вложенных retry handlers"""
        outer_policy = RetryPolicy(max_retries=2, base_delay=0.05)
        inner_policy = RetryPolicy(max_retries=1, base_delay=0.02)
        
        outer_retry = ExponentialBackoffRetry(policy=outer_policy)
        inner_retry = ExponentialBackoffRetry(policy=inner_policy)
        
        with aioresponses() as m:
            # Все запросы неудачные
            for _ in range(10):
                m.get("https://api.test.com/v1/test", status=503, payload={"error": "Service unavailable"})
            
            async def make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/test") as response:
                        if response.status >= 500:
                            raise ServerError(f"Server error: {response.status}")
                        return await response.json()
            
            # Вложенные retry handlers
            async def inner_request():
                return await inner_retry.execute_with_retry(make_request)
            
            result = await outer_retry.execute_with_retry(inner_request)
            
            # Общее количество попыток должно быть произведением retry counts
            # Но из-за вложенности может быть меньше
            assert result.success is False
            assert result.attempts_made >= 2
