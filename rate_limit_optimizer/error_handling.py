"""
Обработка ошибок и retry логика
"""
import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type
from enum import Enum

import aiohttp
from aiohttp import ClientError

from .models import (
    RetryPolicy, RequestError, RetryResult, ErrorStats, CircuitBreakerState
)
from .exceptions import (
    RateLimitExceeded, NetworkError, ServerError, AuthenticationError
)

logger = logging.getLogger(__name__)


class ErrorClassifier:
    """Классификатор ошибок HTTP"""
    
    def __init__(self):
        self.error_mappings = {
            401: (AuthenticationError, False),  # Не повторяем
            403: (AuthenticationError, False),  # Не повторяем
            404: (None, False),                 # Не повторяем
            429: (RateLimitExceeded, True),     # Повторяем
            500: (ServerError, True),           # Повторяем
            502: (NetworkError, True),          # Повторяем
            503: (ServerError, True),           # Повторяем
            504: (NetworkError, True),          # Повторяем
        }
    
    def classify_http_error(self, status_code: int, message: str) -> Dict[str, Any]:
        """Классификация HTTP ошибки"""
        
        exception_type, should_retry = self.error_mappings.get(status_code, (None, False))
        
        return {
            "status_code": status_code,
            "exception_type": exception_type,
            "should_retry": should_retry,
            "message": message,
            "category": self._get_error_category(status_code)
        }
    
    def _get_error_category(self, status_code: int) -> str:
        """Получение категории ошибки"""
        
        if status_code == 429:
            return "rate_limit"
        elif 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "unknown"


class CircuitBreaker:
    """Circuit Breaker для защиты от каскадных сбоев"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
        half_open_max_calls: int = 5
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Выполнение функции через circuit breaker"""
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._move_to_half_open()
            else:
                raise Exception("Circuit breaker is OPEN")
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise Exception("Circuit breaker HALF_OPEN max calls exceeded")
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Проверка возможности сброса circuit breaker"""
        
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def _move_to_half_open(self) -> None:
        """Переход в состояние HALF_OPEN"""
        
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0
        logger.info("Circuit breaker moved to HALF_OPEN")
    
    def _on_success(self) -> None:
        """Обработка успешного вызова"""
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._move_to_closed()
        else:
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Обработка неудачного вызова"""
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._move_to_open()
        elif self.failure_count >= self.failure_threshold:
            self._move_to_open()
    
    def _move_to_closed(self) -> None:
        """Переход в состояние CLOSED"""
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker moved to CLOSED")
    
    def _move_to_open(self) -> None:
        """Переход в состояние OPEN"""
        
        self.state = CircuitBreakerState.OPEN
        self.success_count = 0
        logger.warning("Circuit breaker moved to OPEN")


class ExponentialBackoffRetry:
    """Retry с экспоненциальным backoff"""
    
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        self.error_classifier = ErrorClassifier()
    
    async def execute_with_retry(self, func: Callable) -> RetryResult:
        """Выполнение функции с повторами"""
        
        attempts = 0
        start_time = time.time()
        retry_reasons = []
        last_exception = None
        
        while attempts <= self.policy.max_retries:
            attempts += 1
            
            try:
                result = await func()
                
                # Успешное выполнение
                return RetryResult(
                    success=True,
                    attempts_made=attempts,
                    final_response=result,
                    total_duration=time.time() - start_time,
                    retry_reasons=retry_reasons
                )
                
            except Exception as e:
                last_exception = e
                
                # Проверяем нужно ли повторять
                should_retry = self._should_retry(e, attempts)
                
                if not should_retry or attempts > self.policy.max_retries:
                    break
                
                # Вычисляем задержку
                delay = self._calculate_delay(attempts, e)
                retry_reasons.append(f"Attempt {attempts}: {type(e).__name__} - retry in {delay:.1f}s")
                
                logger.info(f"Retry attempt {attempts} after {delay:.1f}s due to: {e}")
                
                # Ждем перед повтором
                await asyncio.sleep(delay)
        
        # Все попытки исчерпаны
        return RetryResult(
            success=False,
            attempts_made=attempts,
            final_error=last_exception,
            total_duration=time.time() - start_time,
            retry_reasons=retry_reasons
        )
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Проверка необходимости повтора"""
        
        if attempt > self.policy.max_retries:
            return False
        
        # Проверяем тип исключения
        if isinstance(exception, RateLimitExceeded):
            return True
        elif isinstance(exception, (ServerError, NetworkError)):
            return True
        elif isinstance(exception, (asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
            return self.policy.retry_on_timeout
        elif isinstance(exception, AuthenticationError):
            return False  # Не повторяем ошибки аутентификации
        
        # Проверяем HTTP статус коды если это ClientResponseError
        if hasattr(exception, 'status'):
            return exception.status in self.policy.retry_on_codes
        
        return False
    
    def _calculate_delay(self, attempt: int, exception: Exception) -> float:
        """Вычисление задержки перед повтором"""
        
        # Проверяем Retry-After для rate limit ошибок
        if isinstance(exception, RateLimitExceeded) and exception.retry_after:
            return min(exception.retry_after, self.policy.max_delay)
        
        # Экспоненциальный backoff
        delay = self.policy.base_delay * (self.policy.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.policy.max_delay)
        
        # Добавляем jitter если включен
        if self.policy.jitter:
            jitter = delay * 0.1 * random.random()  # ±10% jitter
            delay += jitter
        
        return delay


class LinearBackoffRetry:
    """Retry с линейным backoff"""
    
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        self.error_classifier = ErrorClassifier()
    
    async def execute_with_retry(self, func: Callable) -> RetryResult:
        """Выполнение функции с линейными повторами"""
        
        attempts = 0
        start_time = time.time()
        retry_reasons = []
        last_exception = None
        
        while attempts <= self.policy.max_retries:
            attempts += 1
            
            try:
                result = await func()
                
                return RetryResult(
                    success=True,
                    attempts_made=attempts,
                    final_response=result,
                    total_duration=time.time() - start_time,
                    retry_reasons=retry_reasons
                )
                
            except Exception as e:
                last_exception = e
                
                if attempts > self.policy.max_retries:
                    break
                
                # Линейное увеличение задержки
                delay = self.policy.base_delay * attempts
                delay = min(delay, self.policy.max_delay)
                
                if self.policy.jitter:
                    jitter = delay * 0.1 * random.random()
                    delay += jitter
                
                retry_reasons.append(f"Attempt {attempts}: {type(e).__name__}")
                
                await asyncio.sleep(delay)
        
        return RetryResult(
            success=False,
            attempts_made=attempts,
            final_error=last_exception,
            total_duration=time.time() - start_time,
            retry_reasons=retry_reasons
        )


class ErrorHandler:
    """Основной обработчик ошибок"""
    
    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        collect_stats: bool = True
    ):
        self.circuit_breaker = circuit_breaker
        self.collect_stats = collect_stats
        
        self.error_classifier = ErrorClassifier()
        self.stats = ErrorStats(
            total_requests=0,
            successful_requests=0,
            rate_limit_errors=0,
            server_errors=0,
            network_errors=0,
            timeout_errors=0,
            other_errors=0
        )
    
    async def execute_with_circuit_breaker(self, func: Callable) -> Any:
        """Выполнение функции через circuit breaker"""
        
        if not self.circuit_breaker:
            return await func()
        
        return await self.circuit_breaker.call(func)
    
    def record_response(self, status_code: int, headers: Dict[str, str]) -> None:
        """Запись ответа для статистики"""
        
        if not self.collect_stats:
            return
        
        self.stats.total_requests += 1
        
        if 200 <= status_code < 300:
            self.stats.successful_requests += 1
        elif status_code == 429:
            self.stats.rate_limit_errors += 1
        elif 500 <= status_code < 600:
            self.stats.server_errors += 1
        else:
            self.stats.other_errors += 1
    
    def record_exception(self, exception: Exception) -> None:
        """Запись исключения для статистики"""
        
        if not self.collect_stats:
            return
        
        self.stats.total_requests += 1
        
        if isinstance(exception, RateLimitExceeded):
            self.stats.rate_limit_errors += 1
        elif isinstance(exception, ServerError):
            self.stats.server_errors += 1
        elif isinstance(exception, NetworkError):
            self.stats.network_errors += 1
        elif isinstance(exception, (asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
            self.stats.timeout_errors += 1
        else:
            self.stats.other_errors += 1
    
    def get_error_stats(self) -> ErrorStats:
        """Получение статистики ошибок"""
        return self.stats
    
    async def handle_custom_error(self, error: Exception) -> bool:
        """Обработка кастомных ошибок (переопределяется в наследниках)"""
        return False
    
    def create_request_error(
        self,
        exception: Exception,
        request_url: str,
        status_code: Optional[int] = None
    ) -> RequestError:
        """Создание объекта ошибки запроса"""
        
        error_info = self.error_classifier.classify_http_error(
            status_code or 0,
            str(exception)
        )
        
        retry_after = None
        if isinstance(exception, RateLimitExceeded):
            retry_after = exception.retry_after
        
        return RequestError(
            error_type=error_info["category"],
            error_message=str(exception),
            status_code=status_code,
            retry_after=retry_after,
            request_url=request_url,
            should_retry=error_info["should_retry"]
        )


class RetryManager:
    """Менеджер retry стратегий"""
    
    def __init__(self):
        self.strategies = {
            "exponential": ExponentialBackoffRetry,
            "linear": LinearBackoffRetry
        }
    
    def get_retry_handler(self, strategy: str, policy: RetryPolicy):
        """Получение обработчика retry"""
        
        if strategy not in self.strategies:
            raise ValueError(f"Неизвестная retry стратегия: {strategy}")
        
        return self.strategies[strategy](policy)
    
    def register_strategy(self, name: str, strategy_class: Type):
        """Регистрация новой retry стратегии"""
        self.strategies[name] = strategy_class


# Декораторы для упрощения использования
def with_retry(policy: RetryPolicy, strategy: str = "exponential"):
    """Декоратор для добавления retry к функции"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retry_manager = RetryManager()
            retry_handler = retry_manager.get_retry_handler(strategy, policy)
            
            async def execute():
                return await func(*args, **kwargs)
            
            result = await retry_handler.execute_with_retry(execute)
            
            if result.success:
                return result.final_response
            else:
                raise result.final_error
        
        return wrapper
    return decorator


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3
):
    """Декоратор для добавления circuit breaker к функции"""
    
    circuit_breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold
    )
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Утилиты для обработки ошибок
async def safe_execute(
    func: Callable,
    default_value: Any = None,
    log_errors: bool = True,
    error_handler: Optional[ErrorHandler] = None
) -> Any:
    """Безопасное выполнение функции с обработкой ошибок"""
    
    try:
        return await func()
    except Exception as e:
        if log_errors:
            logger.error(f"Ошибка выполнения функции {func.__name__}: {e}")
        
        if error_handler:
            error_handler.record_exception(e)
        
        return default_value


def create_default_retry_policy() -> RetryPolicy:
    """Создание retry политики по умолчанию"""
    
    return RetryPolicy(
        max_retries=3,
        base_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0,
        retry_on_codes=[429, 502, 503, 504],
        retry_on_timeout=True,
        jitter=True
    )


def create_aggressive_retry_policy() -> RetryPolicy:
    """Создание агрессивной retry политики"""
    
    return RetryPolicy(
        max_retries=5,
        base_delay=0.5,
        backoff_multiplier=1.5,
        max_delay=30.0,
        retry_on_codes=[429, 500, 502, 503, 504],
        retry_on_timeout=True,
        jitter=True
    )


def create_conservative_retry_policy() -> RetryPolicy:
    """Создание консервативной retry политики"""
    
    return RetryPolicy(
        max_retries=2,
        base_delay=2.0,
        backoff_multiplier=3.0,
        max_delay=120.0,
        retry_on_codes=[429, 503],
        retry_on_timeout=False,
        jitter=False
    )
