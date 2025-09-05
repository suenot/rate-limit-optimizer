"""
Интеграционные тесты ротации endpoints для имитации реального трафика
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import random

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.rotation import (
    EndpointRotator,
    RotationStrategy,
    RandomRotationStrategy,
    SequentialRotationStrategy,
    WeightedRotationStrategy,
    PatternAvoidanceRotationStrategy
)
from rate_limit_optimizer.models import (
    EndpointConfig,
    RotationResult,
    TrafficPattern,
    RotationMetrics
)


class TestEndpointRotationIntegration:
    """Интеграционные тесты ротации endpoints"""
    
    @pytest.fixture
    def sample_endpoints(self) -> List[str]:
        """Список тестовых endpoints"""
        return [
            "/v1/market/all",
            "/v1/ticker",
            "/v1/orderbook",
            "/v1/trades",
            "/v1/candles"
        ]
    
    @pytest.fixture
    def endpoint_configs(self, sample_endpoints) -> List[EndpointConfig]:
        """Конфигурации endpoints с различными весами"""
        configs = []
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Разные веса для реалистичности
        
        for endpoint, weight in zip(sample_endpoints, weights):
            config = EndpointConfig(
                path=endpoint,
                weight=weight,
                method="GET",
                expected_response_time_ms=200,
                rate_limit_shared=True,  # Общий rate limit для всех endpoints
                priority="normal"
            )
            configs.append(config)
        
        return configs
    
    @pytest.fixture
    def base_url(self) -> str:
        """Базовый URL для тестирования"""
        return "https://api.upbit.com"
    
    @pytest.mark.asyncio
    async def test_random_rotation_strategy(self, sample_endpoints, base_url):
        """Тест случайной ротации endpoints"""
        strategy = RandomRotationStrategy(
            rotation_interval_requests=3,
            avoid_consecutive_repeats=True
        )
        
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url
        )
        
        with aioresponses() as m:
            # Мокаем ответы для всех endpoints
            for endpoint in sample_endpoints:
                for i in range(10):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        payload={"success": True, "endpoint": endpoint, "request": i},
                        headers={"X-RateLimit-Remaining": str(100-i)}
                    )
            
            # Выполняем серию запросов с ротацией
            used_endpoints = []
            for i in range(15):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.append(endpoint)
                
                # Симулируем запрос
                response = await rotator.make_request(
                    endpoint=endpoint,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                assert response.status == 200
            
            # Проверяем что использовались разные endpoints
            unique_endpoints = set(used_endpoints)
            assert len(unique_endpoints) >= 3  # Минимум 3 разных endpoint
            
            # Проверяем что ротация происходила
            rotation_changes = sum(1 for i in range(1, len(used_endpoints)) 
                                 if used_endpoints[i] != used_endpoints[i-1])
            assert rotation_changes >= 3  # Минимум 3 смены endpoint
    
    @pytest.mark.asyncio
    async def test_sequential_rotation_strategy(self, sample_endpoints, base_url):
        """Тест последовательной ротации endpoints"""
        strategy = SequentialRotationStrategy(
            rotation_interval_requests=2,
            cycle_through_all=True
        )
        
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url
        )
        
        with aioresponses() as m:
            # Мокаем ответы для всех endpoints
            for endpoint in sample_endpoints:
                for i in range(5):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        payload={"success": True, "endpoint": endpoint}
                    )
            
            # Выполняем запросы и проверяем последовательность
            used_endpoints = []
            for i in range(10):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.append(endpoint)
                
                await rotator.make_request(endpoint=endpoint)
            
            # Проверяем что endpoints используются последовательно
            # Каждые 2 запроса должен меняться endpoint
            for i in range(0, len(used_endpoints)-1, 2):
                if i+2 < len(used_endpoints):
                    # Каждые 2 запроса endpoint должен измениться
                    assert used_endpoints[i] == used_endpoints[i+1]  # Первые 2 одинаковые
                    if i+2 < len(used_endpoints):
                        assert used_endpoints[i] != used_endpoints[i+2]  # Следующий другой
    
    @pytest.mark.asyncio
    async def test_weighted_rotation_strategy(self, endpoint_configs, base_url):
        """Тест взвешенной ротации endpoints"""
        strategy = WeightedRotationStrategy(
            respect_weights=True,
            normalize_weights=True
        )
        
        rotator = EndpointRotator(
            endpoint_configs=endpoint_configs,
            strategy=strategy,
            base_url=base_url
        )
        
        with aioresponses() as m:
            # Мокаем ответы для всех endpoints
            for config in endpoint_configs:
                for i in range(20):
                    m.get(
                        f"{base_url}{config.path}",
                        status=200,
                        payload={"success": True, "endpoint": config.path}
                    )
            
            # Выполняем большое количество запросов для проверки распределения
            endpoint_counts = {}
            total_requests = 100
            
            for i in range(total_requests):
                endpoint = await rotator.get_next_endpoint()
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
                
                await rotator.make_request(endpoint=endpoint)
            
            # Проверяем что распределение примерно соответствует весам
            for config in endpoint_configs:
                expected_count = config.weight * total_requests
                actual_count = endpoint_counts.get(config.path, 0)
                
                # Допускаем отклонение ±20% от ожидаемого
                assert abs(actual_count - expected_count) <= expected_count * 0.3
    
    @pytest.mark.asyncio
    async def test_pattern_avoidance_rotation(self, sample_endpoints, base_url):
        """Тест ротации с избежанием паттернов"""
        strategy = PatternAvoidanceRotationStrategy(
            avoid_patterns=True,
            max_consecutive_same=2,
            pattern_detection_window=5,
            randomization_factor=0.3
        )
        
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url
        )
        
        with aioresponses() as m:
            # Мокаем ответы
            for endpoint in sample_endpoints:
                for i in range(15):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        payload={"success": True}
                    )
            
            used_endpoints = []
            for i in range(20):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.append(endpoint)
                
                await rotator.make_request(endpoint=endpoint)
            
            # Проверяем что нет слишком длинных последовательностей одного endpoint
            max_consecutive = 0
            current_consecutive = 1
            
            for i in range(1, len(used_endpoints)):
                if used_endpoints[i] == used_endpoints[i-1]:
                    current_consecutive += 1
                else:
                    max_consecutive = max(max_consecutive, current_consecutive)
                    current_consecutive = 1
            
            max_consecutive = max(max_consecutive, current_consecutive)
            assert max_consecutive <= 2  # Не более 2 подряд одинаковых
            
            # Проверяем отсутствие очевидных паттернов
            pattern_detected = False
            for i in range(len(used_endpoints) - 4):
                # Ищем повторяющиеся паттерны длиной 2
                if (used_endpoints[i] == used_endpoints[i+2] and 
                    used_endpoints[i+1] == used_endpoints[i+3]):
                    pattern_detected = True
                    break
            
            # Паттерны должны быть минимизированы
            assert not pattern_detected or len(set(used_endpoints)) >= 3
    
    @pytest.mark.asyncio
    async def test_rotation_with_endpoint_failures(self, sample_endpoints, base_url):
        """Тест ротации при сбоях отдельных endpoints"""
        strategy = RandomRotationStrategy(rotation_interval_requests=2)
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url,
            handle_failures=True,
            failure_retry_delay=0.1  # Быстрый retry для тестов
        )
        
        with aioresponses() as m:
            # Мокаем ответы: один endpoint всегда падает
            failing_endpoint = sample_endpoints[0]
            working_endpoints = sample_endpoints[1:]
            
            # Failing endpoint возвращает 500
            for i in range(10):
                m.get(
                    f"{base_url}{failing_endpoint}",
                    status=500,
                    payload={"error": "Internal server error"}
                )
            
            # Рабочие endpoints возвращают 200
            for endpoint in working_endpoints:
                for i in range(10):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        payload={"success": True, "endpoint": endpoint}
                    )
            
            successful_requests = 0
            failed_requests = 0
            used_endpoints = []
            
            for i in range(15):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.append(endpoint)
                
                try:
                    response = await rotator.make_request(endpoint=endpoint)
                    if response.status == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                except Exception:
                    failed_requests += 1
            
            # Проверяем что система адаптировалась к сбоям
            assert successful_requests > 0
            
            # Проверяем что failing endpoint использовался реже
            failing_count = used_endpoints.count(failing_endpoint)
            working_count = sum(used_endpoints.count(ep) for ep in working_endpoints)
            
            # Рабочие endpoints должны использоваться чаще
            assert working_count >= failing_count
    
    @pytest.mark.asyncio
    async def test_rotation_metrics_collection(self, sample_endpoints, base_url):
        """Тест сбора метрик ротации endpoints"""
        strategy = RandomRotationStrategy(rotation_interval_requests=3)
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url,
            collect_metrics=True
        )
        
        with aioresponses() as m:
            # Мокаем ответы с разным временем ответа
            response_times = [100, 200, 150, 300, 250]  # ms
            
            for i, endpoint in enumerate(sample_endpoints):
                for j in range(5):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        payload={"success": True},
                        headers={"X-Response-Time": str(response_times[i])}
                    )
            
            # Выполняем запросы
            for i in range(15):
                endpoint = await rotator.get_next_endpoint()
                await rotator.make_request(endpoint=endpoint)
            
            # Получаем метрики
            metrics = rotator.get_metrics()
            
            assert isinstance(metrics, RotationMetrics)
            assert metrics.total_requests == 15
            assert metrics.unique_endpoints_used >= 3
            assert len(metrics.endpoint_usage_stats) >= 3
            
            # Проверяем статистику по endpoints
            for endpoint, stats in metrics.endpoint_usage_stats.items():
                assert stats.request_count > 0
                assert stats.average_response_time > 0
                assert stats.success_rate >= 0
    
    @pytest.mark.asyncio
    async def test_rotation_with_rate_limit_detection(self, sample_endpoints, base_url):
        """Тест ротации с обнаружением rate limits на разных endpoints"""
        strategy = RandomRotationStrategy(rotation_interval_requests=2)
        rotator = EndpointRotator(
            endpoints=sample_endpoints,
            strategy=strategy,
            base_url=base_url,
            detect_per_endpoint_limits=True
        )
        
        with aioresponses() as m:
            # Первый endpoint имеет строгий лимит
            strict_endpoint = sample_endpoints[0]
            for i in range(3):
                m.get(f"{base_url}{strict_endpoint}", status=200)
            m.get(f"{base_url}{strict_endpoint}", status=429, 
                  headers={"Retry-After": "60", "X-RateLimit-Limit": "3"})
            
            # Остальные endpoints имеют более мягкие лимиты
            for endpoint in sample_endpoints[1:]:
                for i in range(10):
                    m.get(
                        f"{base_url}{endpoint}",
                        status=200,
                        headers={"X-RateLimit-Remaining": str(50-i)}
                    )
            
            # Выполняем запросы
            endpoint_limit_hits = {}
            for i in range(20):
                endpoint = await rotator.get_next_endpoint()
                
                try:
                    response = await rotator.make_request(endpoint=endpoint)
                    if response.status == 429:
                        endpoint_limit_hits[endpoint] = endpoint_limit_hits.get(endpoint, 0) + 1
                except Exception as e:
                    if "429" in str(e):
                        endpoint_limit_hits[endpoint] = endpoint_limit_hits.get(endpoint, 0) + 1
            
            # Проверяем что система обнаружила лимиты
            per_endpoint_limits = rotator.get_detected_limits()
            
            # Строгий endpoint должен иметь обнаруженный лимит
            assert strict_endpoint in per_endpoint_limits
            assert per_endpoint_limits[strict_endpoint].limit <= 5
    
    @pytest.mark.asyncio
    async def test_adaptive_rotation_based_on_performance(self, endpoint_configs, base_url):
        """Тест адаптивной ротации на основе производительности endpoints"""
        strategy = WeightedRotationStrategy(
            adapt_weights_based_on_performance=True,
            performance_window_requests=10,
            weight_adjustment_factor=0.1
        )
        
        rotator = EndpointRotator(
            endpoint_configs=endpoint_configs,
            strategy=strategy,
            base_url=base_url
        )
        
        with aioresponses() as m:
            # Мокаем ответы с разной производительностью
            fast_endpoints = endpoint_configs[:2]  # Быстрые endpoints
            slow_endpoints = endpoint_configs[2:]  # Медленные endpoints
            
            # Быстрые endpoints
            for config in fast_endpoints:
                for i in range(20):
                    m.get(
                        f"{base_url}{config.path}",
                        status=200,
                        payload={"success": True},
                        headers={"X-Response-Time": "50"}  # Быстрый ответ
                    )
            
            # Медленные endpoints
            for config in slow_endpoints:
                for i in range(20):
                    # Симулируем задержку через callback
                    async def slow_callback(url, **kwargs):
                        await asyncio.sleep(0.1)  # Имитация медленного ответа
                        return aiohttp.web.Response(
                            status=200,
                            headers={"X-Response-Time": "500"}
                        )
                    
                    m.get(f"{base_url}{config.path}", callback=slow_callback)
            
            # Выполняем запросы для обучения системы
            initial_requests = 30
            for i in range(initial_requests):
                endpoint = await rotator.get_next_endpoint()
                start_time = datetime.now()
                await rotator.make_request(endpoint=endpoint)
                end_time = datetime.now()
                
                # Записываем время ответа для адаптации
                response_time = (end_time - start_time).total_seconds() * 1000
                rotator.record_performance(endpoint, response_time)
            
            # Получаем адаптированные веса
            adapted_weights = rotator.get_current_weights()
            
            # Быстрые endpoints должны получить больший вес
            fast_paths = [config.path for config in fast_endpoints]
            slow_paths = [config.path for config in slow_endpoints]
            
            avg_fast_weight = sum(adapted_weights.get(path, 0) for path in fast_paths) / len(fast_paths)
            avg_slow_weight = sum(adapted_weights.get(path, 0) for path in slow_paths) / len(slow_paths)
            
            # Быстрые endpoints должны иметь больший вес
            assert avg_fast_weight >= avg_slow_weight


@pytest.mark.integration
class TestEndpointRotationEdgeCases:
    """Тесты граничных случаев ротации endpoints"""
    
    @pytest.mark.asyncio
    async def test_rotation_with_single_endpoint(self):
        """Тест ротации с единственным endpoint"""
        strategy = RandomRotationStrategy()
        rotator = EndpointRotator(
            endpoints=["/v1/single"],
            strategy=strategy,
            base_url="https://api.test.com"
        )
        
        with aioresponses() as m:
            for i in range(5):
                m.get(
                    "https://api.test.com/v1/single",
                    status=200,
                    payload={"success": True}
                )
            
            # Все запросы должны идти на единственный endpoint
            for i in range(5):
                endpoint = await rotator.get_next_endpoint()
                assert endpoint == "/v1/single"
                
                response = await rotator.make_request(endpoint=endpoint)
                assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_rotation_with_all_endpoints_failing(self):
        """Тест ротации когда все endpoints недоступны"""
        strategy = RandomRotationStrategy()
        rotator = EndpointRotator(
            endpoints=["/v1/fail1", "/v1/fail2", "/v1/fail3"],
            strategy=strategy,
            base_url="https://api.test.com",
            max_retries_per_endpoint=2
        )
        
        with aioresponses() as m:
            # Все endpoints возвращают ошибки
            for endpoint in ["/v1/fail1", "/v1/fail2", "/v1/fail3"]:
                for i in range(5):
                    m.get(
                        f"https://api.test.com{endpoint}",
                        status=503,
                        payload={"error": "Service unavailable"}
                    )
            
            # Система должна корректно обработать полный отказ
            failed_attempts = 0
            for i in range(6):  # Пробуем больше чем endpoints * retries
                endpoint = await rotator.get_next_endpoint()
                
                try:
                    response = await rotator.make_request(endpoint=endpoint)
                    if response.status >= 500:
                        failed_attempts += 1
                except Exception:
                    failed_attempts += 1
            
            # Все попытки должны завершиться неудачей
            assert failed_attempts >= 3  # Минимум по одной неудаче на endpoint
            
            # Система должна зафиксировать состояние отказа
            health_status = rotator.get_health_status()
            assert health_status.all_endpoints_healthy is False
    
    @pytest.mark.asyncio
    async def test_rotation_weight_normalization(self):
        """Тест нормализации весов endpoints"""
        # Создаем endpoints с ненормализованными весами
        configs = [
            EndpointConfig(path="/v1/heavy", weight=1000),  # Очень большой вес
            EndpointConfig(path="/v1/medium", weight=500),
            EndpointConfig(path="/v1/light", weight=100)
        ]
        
        strategy = WeightedRotationStrategy(normalize_weights=True)
        rotator = EndpointRotator(
            endpoint_configs=configs,
            strategy=strategy,
            base_url="https://api.test.com"
        )
        
        # Получаем нормализованные веса
        normalized_weights = rotator.get_normalized_weights()
        
        # Сумма весов должна быть 1.0
        total_weight = sum(normalized_weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        # Пропорции должны сохраниться
        assert normalized_weights["/v1/heavy"] > normalized_weights["/v1/medium"]
        assert normalized_weights["/v1/medium"] > normalized_weights["/v1/light"]
    
    @pytest.mark.asyncio
    async def test_rotation_with_dynamic_endpoint_addition(self):
        """Тест динамического добавления endpoints во время работы"""
        strategy = RandomRotationStrategy()
        rotator = EndpointRotator(
            endpoints=["/v1/initial"],
            strategy=strategy,
            base_url="https://api.test.com",
            allow_dynamic_endpoints=True
        )
        
        with aioresponses() as m:
            # Мокаем ответы для всех endpoints
            all_endpoints = ["/v1/initial", "/v1/dynamic1", "/v1/dynamic2"]
            for endpoint in all_endpoints:
                for i in range(5):
                    m.get(
                        f"https://api.test.com{endpoint}",
                        status=200,
                        payload={"success": True, "endpoint": endpoint}
                    )
            
            # Начинаем с одного endpoint
            used_endpoints = set()
            
            for i in range(3):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.add(endpoint)
                await rotator.make_request(endpoint=endpoint)
            
            # Добавляем новые endpoints
            rotator.add_endpoint("/v1/dynamic1", weight=0.3)
            rotator.add_endpoint("/v1/dynamic2", weight=0.2)
            
            # Продолжаем запросы
            for i in range(6):
                endpoint = await rotator.get_next_endpoint()
                used_endpoints.add(endpoint)
                await rotator.make_request(endpoint=endpoint)
            
            # Должны использоваться все endpoints включая новые
            assert len(used_endpoints) >= 2  # Минимум исходный + один новый
            assert "/v1/initial" in used_endpoints
