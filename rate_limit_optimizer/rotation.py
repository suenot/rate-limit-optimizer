"""
Ротация endpoints для имитации реального трафика
"""
import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin
from collections import defaultdict, deque

import aiohttp
from aiohttp import ClientTimeout, ClientError

from .models import (
    EndpointConfig, RotationMetrics, RotationResult, RateLimit
)
from .exceptions import NetworkError

logger = logging.getLogger(__name__)


class RotationStrategy:
    """Базовая стратегия ротации"""
    
    def __init__(self, rotation_interval_requests: int = 5):
        self.rotation_interval_requests = rotation_interval_requests
        self.request_count = 0
    
    def get_next_endpoint(self, endpoints: List[str], **kwargs) -> str:
        """Получение следующего endpoint"""
        raise NotImplementedError
    
    def should_rotate(self) -> bool:
        """Проверка необходимости ротации"""
        self.request_count += 1
        return self.request_count % self.rotation_interval_requests == 0


class RandomRotationStrategy(RotationStrategy):
    """Случайная ротация endpoints"""
    
    def __init__(
        self, 
        rotation_interval_requests: int = 5,
        avoid_consecutive_repeats: bool = True
    ):
        super().__init__(rotation_interval_requests)
        self.avoid_consecutive_repeats = avoid_consecutive_repeats
        self.last_endpoint: Optional[str] = None
    
    def get_next_endpoint(self, endpoints: List[str], **kwargs) -> str:
        """Случайный выбор endpoint"""
        
        if len(endpoints) == 1:
            return endpoints[0]
        
        if self.avoid_consecutive_repeats and self.last_endpoint:
            # Исключаем последний использованный endpoint
            available = [ep for ep in endpoints if ep != self.last_endpoint]
            if available:
                endpoint = random.choice(available)
            else:
                endpoint = random.choice(endpoints)
        else:
            endpoint = random.choice(endpoints)
        
        self.last_endpoint = endpoint
        return endpoint


class SequentialRotationStrategy(RotationStrategy):
    """Последовательная ротация endpoints"""
    
    def __init__(
        self, 
        rotation_interval_requests: int = 2,
        cycle_through_all: bool = True
    ):
        super().__init__(rotation_interval_requests)
        self.cycle_through_all = cycle_through_all
        self.current_index = 0
    
    def get_next_endpoint(self, endpoints: List[str], **kwargs) -> str:
        """Последовательный выбор endpoint"""
        
        if not endpoints:
            raise ValueError("Список endpoints пуст")
        
        if self.should_rotate():
            self.current_index = (self.current_index + 1) % len(endpoints)
        
        return endpoints[self.current_index]


class WeightedRotationStrategy(RotationStrategy):
    """Взвешенная ротация endpoints"""
    
    def __init__(
        self,
        respect_weights: bool = True,
        normalize_weights: bool = True,
        adapt_weights_based_on_performance: bool = False,
        performance_window_requests: int = 10,
        weight_adjustment_factor: float = 0.1
    ):
        super().__init__(1)  # Каждый запрос может менять endpoint
        self.respect_weights = respect_weights
        self.normalize_weights = normalize_weights
        self.adapt_weights_based_on_performance = adapt_weights_based_on_performance
        self.performance_window_requests = performance_window_requests
        self.weight_adjustment_factor = weight_adjustment_factor
        
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=performance_window_requests))
        self.current_weights: Dict[str, float] = {}
    
    def get_next_endpoint(self, endpoints: List[str], endpoint_configs: List[EndpointConfig] = None, **kwargs) -> str:
        """Взвешенный выбор endpoint"""
        
        if not endpoints:
            raise ValueError("Список endpoints пуст")
        
        if len(endpoints) == 1:
            return endpoints[0]
        
        # Получаем веса
        weights = self._get_weights(endpoints, endpoint_configs)
        
        # Нормализуем веса если нужно
        if self.normalize_weights:
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {ep: w / total_weight for ep, w in weights.items()}
        
        # Выбираем endpoint на основе весов
        return self._weighted_choice(endpoints, weights)
    
    def _get_weights(self, endpoints: List[str], endpoint_configs: List[EndpointConfig] = None) -> Dict[str, float]:
        """Получение весов для endpoints"""
        
        weights = {}
        
        # Базовые веса из конфигурации
        if endpoint_configs and self.respect_weights:
            config_map = {config.path: config for config in endpoint_configs}
            for endpoint in endpoints:
                config = config_map.get(endpoint)
                weights[endpoint] = config.weight if config else 1.0
        else:
            # Равные веса по умолчанию
            weights = {ep: 1.0 for ep in endpoints}
        
        # Адаптация весов на основе производительности
        if self.adapt_weights_based_on_performance:
            weights = self._adapt_weights_by_performance(weights)
        
        return weights
    
    def _adapt_weights_by_performance(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """Адаптация весов на основе производительности"""
        
        adapted_weights = base_weights.copy()
        
        for endpoint, history in self.performance_history.items():
            if len(history) < 3:  # Недостаточно данных
                continue
            
            # Вычисляем среднее время ответа
            avg_response_time = sum(history) / len(history)
            
            # Адаптируем вес (быстрые endpoints получают больший вес)
            if avg_response_time > 0:
                performance_factor = 1.0 / avg_response_time
                adjustment = performance_factor * self.weight_adjustment_factor
                
                if endpoint in adapted_weights:
                    adapted_weights[endpoint] *= (1.0 + adjustment)
        
        return adapted_weights
    
    def _weighted_choice(self, endpoints: List[str], weights: Dict[str, float]) -> str:
        """Взвешенный выбор endpoint"""
        
        # Создаем список кумулятивных весов
        cumulative_weights = []
        cumulative_sum = 0
        
        for endpoint in endpoints:
            weight = weights.get(endpoint, 1.0)
            cumulative_sum += weight
            cumulative_weights.append((endpoint, cumulative_sum))
        
        if cumulative_sum == 0:
            return random.choice(endpoints)
        
        # Выбираем случайное число
        rand_value = random.uniform(0, cumulative_sum)
        
        # Находим соответствующий endpoint
        for endpoint, cum_weight in cumulative_weights:
            if rand_value <= cum_weight:
                return endpoint
        
        # Fallback
        return endpoints[-1]
    
    def record_performance(self, endpoint: str, response_time: float) -> None:
        """Запись производительности endpoint"""
        self.performance_history[endpoint].append(response_time)
    
    def get_current_weights(self) -> Dict[str, float]:
        """Получение текущих весов"""
        return self.current_weights.copy()


class PatternAvoidanceRotationStrategy(RotationStrategy):
    """Ротация с избежанием паттернов"""
    
    def __init__(
        self,
        avoid_patterns: bool = True,
        max_consecutive_same: int = 2,
        pattern_detection_window: int = 5,
        randomization_factor: float = 0.3
    ):
        super().__init__(1)
        self.avoid_patterns = avoid_patterns
        self.max_consecutive_same = max_consecutive_same
        self.pattern_detection_window = pattern_detection_window
        self.randomization_factor = randomization_factor
        
        self.history: deque = deque(maxlen=pattern_detection_window)
    
    def get_next_endpoint(self, endpoints: List[str], **kwargs) -> str:
        """Выбор endpoint с избежанием паттернов"""
        
        if not endpoints:
            raise ValueError("Список endpoints пуст")
        
        if len(endpoints) == 1:
            return endpoints[0]
        
        # Проверяем последовательные повторения
        available_endpoints = self._filter_consecutive_repeats(endpoints)
        
        # Проверяем паттерны если включено
        if self.avoid_patterns and len(self.history) >= 2:
            available_endpoints = self._filter_patterns(available_endpoints)
        
        # Если после фильтрации не осталось вариантов, используем все
        if not available_endpoints:
            available_endpoints = endpoints
        
        # Добавляем рандомизацию
        if random.random() < self.randomization_factor:
            endpoint = random.choice(endpoints)
        else:
            endpoint = random.choice(available_endpoints)
        
        # Записываем в историю
        self.history.append(endpoint)
        
        return endpoint
    
    def _filter_consecutive_repeats(self, endpoints: List[str]) -> List[str]:
        """Фильтрация последовательных повторений"""
        
        if len(self.history) < self.max_consecutive_same:
            return endpoints
        
        # Проверяем последние N записей
        recent_history = list(self.history)[-self.max_consecutive_same:]
        
        # Если все последние записи одинаковые, исключаем этот endpoint
        if len(set(recent_history)) == 1:
            last_endpoint = recent_history[0]
            return [ep for ep in endpoints if ep != last_endpoint]
        
        return endpoints
    
    def _filter_patterns(self, endpoints: List[str]) -> List[str]:
        """Фильтрация паттернов"""
        
        if len(self.history) < 4:
            return endpoints
        
        history_list = list(self.history)
        
        # Ищем простые паттерны (AB-AB)
        for i in range(len(history_list) - 3):
            pattern = history_list[i:i+2]
            next_pattern = history_list[i+2:i+4]
            
            if pattern == next_pattern:
                # Найден повторяющийся паттерн, избегаем его продолжения
                expected_next = pattern[0]  # Следующий в паттерне
                return [ep for ep in endpoints if ep != expected_next]
        
        return endpoints


class EndpointRotator:
    """Основной класс для ротации endpoints"""
    
    def __init__(
        self,
        endpoints: List[str] = None,
        endpoint_configs: List[EndpointConfig] = None,
        strategy: RotationStrategy = None,
        base_url: str = "",
        handle_failures: bool = True,
        failure_retry_delay: float = 1.0,
        collect_metrics: bool = True,
        detect_per_endpoint_limits: bool = False,
        max_retries_per_endpoint: int = 3,
        allow_dynamic_endpoints: bool = False
    ):
        self.endpoints = endpoints or []
        self.endpoint_configs = endpoint_configs or []
        self.strategy = strategy or RandomRotationStrategy()
        self.base_url = base_url
        self.handle_failures = handle_failures
        self.failure_retry_delay = failure_retry_delay
        self.collect_metrics = collect_metrics
        self.detect_per_endpoint_limits = detect_per_endpoint_limits
        self.max_retries_per_endpoint = max_retries_per_endpoint
        self.allow_dynamic_endpoints = allow_dynamic_endpoints
        
        # Метрики
        self.request_count = 0
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'response_times': [],
            'last_used': None
        })
        
        # Обнаруженные лимиты по endpoints
        self.detected_limits: Dict[str, RateLimit] = {}
        
        # Состояние здоровья endpoints
        self.endpoint_health: Dict[str, bool] = {ep: True for ep in self.endpoints}
        
        # Сессия HTTP
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_next_endpoint(self) -> str:
        """Получение следующего endpoint для использования"""
        
        if not self.endpoints:
            raise ValueError("Нет доступных endpoints")
        
        # Фильтруем здоровые endpoints если включена обработка сбоев
        if self.handle_failures:
            healthy_endpoints = [ep for ep in self.endpoints if self.endpoint_health.get(ep, True)]
            if healthy_endpoints:
                endpoints_to_use = healthy_endpoints
            else:
                # Если все endpoints нездоровы, используем все
                endpoints_to_use = self.endpoints
                logger.warning("Все endpoints помечены как нездоровые, используем все")
        else:
            endpoints_to_use = self.endpoints
        
        # Получаем endpoint от стратегии
        endpoint = self.strategy.get_next_endpoint(
            endpoints_to_use,
            endpoint_configs=self.endpoint_configs
        )
        
        return endpoint
    
    async def make_request(
        self, 
        endpoint: str, 
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Выполнение запроса к endpoint"""
        
        if not self.session:
            async with self:
                return await self._make_request_impl(endpoint, headers, method, **kwargs)
        else:
            return await self._make_request_impl(endpoint, headers, method, **kwargs)
    
    async def _make_request_impl(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Внутренняя реализация запроса"""
        
        url = urljoin(self.base_url, endpoint)
        start_time = time.time()
        
        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                response_time = time.time() - start_time
                
                # Записываем метрики
                if self.collect_metrics:
                    self._record_request_metrics(endpoint, response.status, response_time)
                
                # Записываем производительность для адаптивной стратегии
                if isinstance(self.strategy, WeightedRotationStrategy):
                    self.strategy.record_performance(endpoint, response_time)
                
                # Обнаружение лимитов по endpoint
                if self.detect_per_endpoint_limits and response.status == 429:
                    self._detect_endpoint_limit(endpoint, response.headers)
                
                # Обновляем здоровье endpoint
                if self.handle_failures:
                    self.endpoint_health[endpoint] = response.status < 500
                
                return response
                
        except Exception as e:
            response_time = time.time() - start_time
            
            # Записываем ошибку в метрики
            if self.collect_metrics:
                self._record_request_metrics(endpoint, 0, response_time, error=str(e))
            
            # Помечаем endpoint как нездоровый
            if self.handle_failures:
                self.endpoint_health[endpoint] = False
                
                # Ждем перед следующей попыткой
                if self.failure_retry_delay > 0:
                    await asyncio.sleep(self.failure_retry_delay)
            
            raise NetworkError(f"Ошибка запроса к {endpoint}: {e}")
    
    def _record_request_metrics(
        self, 
        endpoint: str, 
        status_code: int, 
        response_time: float,
        error: Optional[str] = None
    ) -> None:
        """Запись метрик запроса"""
        
        stats = self.endpoint_stats[endpoint]
        stats['requests'] += 1
        stats['last_used'] = datetime.now()
        stats['response_times'].append(response_time)
        
        if error or status_code >= 400:
            stats['failures'] += 1
        else:
            stats['successes'] += 1
        
        self.request_count += 1
    
    def _detect_endpoint_limit(self, endpoint: str, headers: Dict[str, str]) -> None:
        """Обнаружение лимита для конкретного endpoint"""
        
        # Простое извлечение лимита из заголовков
        limit_header = headers.get('X-RateLimit-Limit')
        remaining_header = headers.get('X-RateLimit-Remaining')
        
        if limit_header:
            try:
                limit_value = int(limit_header)
                remaining_value = int(remaining_header) if remaining_header else 0
                
                rate_limit = RateLimit(
                    limit=limit_value,
                    remaining=remaining_value,
                    window_seconds=60,  # Предполагаем минутное окно
                    detected_via="testing"
                )
                
                self.detected_limits[endpoint] = rate_limit
                logger.info(f"Обнаружен лимит для {endpoint}: {limit_value} req/min")
                
            except ValueError:
                pass
    
    def get_metrics(self) -> RotationMetrics:
        """Получение метрик ротации"""
        
        unique_endpoints = len([ep for ep in self.endpoint_stats.keys() if self.endpoint_stats[ep]['requests'] > 0])
        
        # Вычисляем эффективность ротации
        if self.request_count > 0 and len(self.endpoints) > 1:
            ideal_distribution = self.request_count / len(self.endpoints)
            actual_distribution = [stats['requests'] for stats in self.endpoint_stats.values()]
            
            # Коэффициент вариации как мера равномерности
            if actual_distribution:
                mean_requests = sum(actual_distribution) / len(actual_distribution)
                if mean_requests > 0:
                    variance = sum((x - mean_requests) ** 2 for x in actual_distribution) / len(actual_distribution)
                    cv = (variance ** 0.5) / mean_requests
                    efficiency = max(0, 1 - cv)  # Меньше вариации = больше эффективности
                else:
                    efficiency = 0
            else:
                efficiency = 0
        else:
            efficiency = 1.0
        
        # Средний response time
        all_response_times = []
        for stats in self.endpoint_stats.values():
            all_response_times.extend(stats['response_times'])
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        return RotationMetrics(
            total_requests=self.request_count,
            unique_endpoints_used=unique_endpoints,
            endpoint_usage_stats=dict(self.endpoint_stats),
            rotation_efficiency=efficiency,
            average_response_time=avg_response_time
        )
    
    def get_detected_limits(self) -> Dict[str, RateLimit]:
        """Получение обнаруженных лимитов по endpoints"""
        return self.detected_limits.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение состояния здоровья endpoints"""
        healthy_count = sum(1 for health in self.endpoint_health.values() if health)
        
        return {
            "all_endpoints_healthy": healthy_count == len(self.endpoints),
            "healthy_endpoints": healthy_count,
            "total_endpoints": len(self.endpoints),
            "endpoint_health": self.endpoint_health.copy()
        }
    
    def get_normalized_weights(self) -> Dict[str, float]:
        """Получение нормализованных весов endpoints"""
        
        if not self.endpoint_configs:
            return {ep: 1.0 / len(self.endpoints) for ep in self.endpoints}
        
        # Собираем веса из конфигурации
        weights = {}
        config_map = {config.path: config for config in self.endpoint_configs}
        
        for endpoint in self.endpoints:
            config = config_map.get(endpoint)
            weights[endpoint] = config.weight if config else 1.0
        
        # Нормализуем
        total_weight = sum(weights.values())
        if total_weight > 0:
            return {ep: w / total_weight for ep, w in weights.items()}
        else:
            return {ep: 1.0 / len(self.endpoints) for ep in self.endpoints}
    
    def add_endpoint(self, endpoint: str, weight: float = 1.0) -> None:
        """Динамическое добавление endpoint"""
        
        if not self.allow_dynamic_endpoints:
            raise ValueError("Динамическое добавление endpoints отключено")
        
        if endpoint not in self.endpoints:
            self.endpoints.append(endpoint)
            self.endpoint_health[endpoint] = True
            
            # Добавляем конфигурацию если нужно
            config = EndpointConfig(path=endpoint, weight=weight)
            self.endpoint_configs.append(config)
            
            logger.info(f"Добавлен endpoint: {endpoint} с весом {weight}")
    
    def remove_endpoint(self, endpoint: str) -> bool:
        """Удаление endpoint"""
        
        if endpoint in self.endpoints:
            self.endpoints.remove(endpoint)
            
            if endpoint in self.endpoint_health:
                del self.endpoint_health[endpoint]
            
            if endpoint in self.endpoint_stats:
                del self.endpoint_stats[endpoint]
            
            # Удаляем из конфигурации
            self.endpoint_configs = [config for config in self.endpoint_configs if config.path != endpoint]
            
            logger.info(f"Удален endpoint: {endpoint}")
            return True
        
        return False
