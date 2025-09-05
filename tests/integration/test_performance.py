"""
Интеграционные тесты производительности и нагрузки
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import statistics
import psutil
import gc

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.performance import (
    PerformanceMonitor,
    LoadTester,
    BenchmarkRunner,
    MetricsCollector,
    ResourceMonitor
)
from rate_limit_optimizer.detection import MultiTierDetector
from rate_limit_optimizer.models import (
    PerformanceMetrics,
    LoadTestResult,
    BenchmarkResult,
    ResourceUsage
)


class TestPerformanceIntegration:
    """Интеграционные тесты производительности"""
    
    @pytest.fixture
    def performance_monitor(self) -> PerformanceMonitor:
        """Монитор производительности для тестов"""
        return PerformanceMonitor(
            collect_detailed_metrics=True,
            sampling_interval=0.1,  # Быстрая выборка для тестов
            memory_profiling=True
        )
    
    @pytest.fixture
    def load_tester(self) -> LoadTester:
        """Load tester для тестов"""
        return LoadTester(
            max_concurrent_requests=50,
            ramp_up_duration=1.0,  # Быстрый ramp-up для тестов
            test_duration=5.0,     # Короткие тесты
            target_rps=10.0
        )
    
    @pytest.mark.asyncio
    async def test_single_request_performance(self, performance_monitor):
        """Тест производительности одиночного запроса"""
        with aioresponses() as m:
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                payload={"success": True},
                headers={"X-RateLimit-Remaining": "99"}
            )
            
            async with performance_monitor.measure_request("single_request"):
                async with aiohttp.ClientSession() as session:
                    start_time = time.perf_counter()
                    async with session.get("https://api.test.com/v1/test") as response:
                        await response.json()
                    end_time = time.perf_counter()
            
            metrics = performance_monitor.get_metrics()
            
            # Проверяем базовые метрики
            assert "single_request" in metrics.request_metrics
            request_stats = metrics.request_metrics["single_request"]
            
            assert request_stats.total_requests == 1
            assert request_stats.average_response_time > 0
            assert request_stats.success_rate == 1.0
            assert request_stats.min_response_time > 0
            assert request_stats.max_response_time >= request_stats.min_response_time
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, performance_monitor):
        """Тест производительности параллельных запросов"""
        concurrent_requests = 20
        
        with aioresponses() as m:
            # Мокаем ответы для всех запросов
            for i in range(concurrent_requests):
                m.get(
                    f"https://api.test.com/v1/test?id={i}",
                    status=200,
                    payload={"success": True, "id": i},
                    headers={"X-RateLimit-Remaining": str(100-i)}
                )
            
            async def make_request(request_id: int):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.test.com/v1/test?id={request_id}") as response:
                        return await response.json()
            
            # Запускаем параллельные запросы с мониторингом
            start_time = time.perf_counter()
            
            async with performance_monitor.measure_concurrent_requests("concurrent_test"):
                tasks = [make_request(i) for i in range(concurrent_requests)]
                results = await asyncio.gather(*tasks)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Проверяем результаты
            assert len(results) == concurrent_requests
            
            metrics = performance_monitor.get_metrics()
            concurrent_stats = metrics.request_metrics["concurrent_test"]
            
            assert concurrent_stats.total_requests == concurrent_requests
            assert concurrent_stats.success_rate == 1.0
            
            # Параллельные запросы должны выполняться быстрее последовательных
            theoretical_sequential_time = concurrent_stats.average_response_time * concurrent_requests
            assert total_time < theoretical_sequential_time * 0.8  # Значительное ускорение
    
    @pytest.mark.asyncio
    async def test_rate_limit_detection_performance(self, performance_monitor):
        """Тест производительности определения rate limits"""
        detector = MultiTierDetector()
        
        with aioresponses() as m:
            # Мокаем быстрые ответы для тестирования производительности
            for i in range(100):
                if i < 50:
                    m.get(
                        "https://api.test.com/v1/test",
                        status=200,
                        headers={"X-RateLimit-Remaining": str(50-i)}
                    )
                else:
                    # Имитируем достижение лимита
                    m.get(
                        "https://api.test.com/v1/test",
                        status=429,
                        headers={
                            "X-RateLimit-Limit": "50",
                            "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=60)).timestamp()))
                        }
                    )
            
            # Измеряем производительность определения лимитов
            start_time = time.perf_counter()
            
            async with performance_monitor.measure_operation("rate_limit_detection"):
                result = await detector.detect_all_rate_limits(
                    base_url="https://api.test.com",
                    endpoint="/v1/test",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
            
            end_time = time.perf_counter()
            detection_time = end_time - start_time
            
            # Проверяем что определение выполнилось быстро
            assert detection_time < 10.0  # Не более 10 секунд
            assert result.limits_found > 0
            
            metrics = performance_monitor.get_metrics()
            detection_stats = metrics.operation_metrics["rate_limit_detection"]
            
            assert detection_stats.total_operations == 1
            assert detection_stats.average_duration > 0
    
    @pytest.mark.asyncio
    async def test_load_testing_with_gradual_ramp_up(self, load_tester):
        """Тест нагрузочного тестирования с постепенным увеличением нагрузки"""
        with aioresponses() as m:
            # Мокаем ответы для нагрузочного тестирования
            for i in range(200):  # Достаточно для 5-секундного теста на 10 RPS
                m.get(
                    "https://api.test.com/v1/load-test",
                    status=200,
                    payload={"success": True, "request_id": i},
                    headers={"X-RateLimit-Remaining": str(1000-i)}
                )
            
            async def test_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/load-test") as response:
                        return await response.json()
            
            # Запускаем нагрузочный тест
            load_result = await load_tester.run_load_test(
                request_func=test_request,
                target_url="https://api.test.com/v1/load-test"
            )
            
            # Проверяем результаты нагрузочного тестирования
            assert isinstance(load_result, LoadTestResult)
            assert load_result.total_requests > 0
            assert load_result.successful_requests > 0
            assert load_result.average_response_time > 0
            assert load_result.requests_per_second > 0
            
            # Проверяем что достигнута целевая производительность
            assert load_result.requests_per_second >= load_tester.target_rps * 0.8  # 80% от цели
            
            # Проверяем распределение времени ответа
            assert load_result.p95_response_time > load_result.p50_response_time
            assert load_result.p99_response_time >= load_result.p95_response_time
    
    @pytest.mark.asyncio
    async def test_stress_testing_with_high_concurrency(self):
        """Тест стресс-тестирования с высокой конкурентностью"""
        stress_tester = LoadTester(
            max_concurrent_requests=100,
            test_duration=3.0,
            target_rps=50.0,
            stress_test_mode=True
        )
        
        with aioresponses() as m:
            # Мокаем ответы для стресс-тестирования
            for i in range(500):
                if i % 10 == 0:  # 10% ошибок для реалистичности
                    m.get(
                        "https://api.test.com/v1/stress-test",
                        status=503,
                        payload={"error": "Service temporarily unavailable"}
                    )
                else:
                    m.get(
                        "https://api.test.com/v1/stress-test",
                        status=200,
                        payload={"success": True}
                    )
            
            async def stress_request():
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.test.com/v1/stress-test") as response:
                        if response.status >= 500:
                            raise aiohttp.ClientError(f"Server error: {response.status}")
                        return await response.json()
            
            # Запускаем стресс-тест
            stress_result = await stress_tester.run_load_test(
                request_func=stress_request,
                target_url="https://api.test.com/v1/stress-test"
            )
            
            # Проверяем что система выдержала нагрузку
            assert stress_result.total_requests > 100  # Значительное количество запросов
            assert stress_result.error_rate < 0.2  # Не более 20% ошибок
            
            # Проверяем метрики производительности под нагрузкой
            assert stress_result.average_response_time < 1.0  # Разумное время ответа
            assert stress_result.max_concurrent_requests == 100
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Тест мониторинга использования памяти"""
        resource_monitor = ResourceMonitor(
            monitor_memory=True,
            monitor_cpu=True,
            sampling_interval=0.1
        )
        
        # Запускаем мониторинг
        resource_monitor.start_monitoring()
        
        # Выполняем операции, потребляющие память
        large_data = []
        for i in range(1000):
            # Создаем объекты для увеличения потребления памяти
            data = {
                "id": i,
                "data": "x" * 1000,  # 1KB строка
                "nested": {"value": i * 2, "list": list(range(100))}
            }
            large_data.append(data)
            
            if i % 100 == 0:
                await asyncio.sleep(0.1)  # Даем время для сэмплирования
        
        # Останавливаем мониторинг
        resource_monitor.stop_monitoring()
        
        # Получаем статистику использования ресурсов
        resource_stats = resource_monitor.get_resource_usage()
        
        assert isinstance(resource_stats, ResourceUsage)
        assert resource_stats.peak_memory_mb > 0
        assert resource_stats.average_memory_mb > 0
        assert resource_stats.peak_cpu_percent >= 0
        
        # Память должна была увеличиться во время теста
        assert resource_stats.peak_memory_mb > resource_stats.initial_memory_mb
        
        # Очищаем память
        del large_data
        gc.collect()
    
    @pytest.mark.asyncio
    async def test_benchmark_comparison(self):
        """Тест сравнительного бенчмарка различных стратегий"""
        benchmark_runner = BenchmarkRunner()
        
        # Определяем различные стратегии для сравнения
        strategies = {
            "sequential": self._sequential_strategy,
            "concurrent_10": lambda: self._concurrent_strategy(10),
            "concurrent_20": lambda: self._concurrent_strategy(20),
            "batch_processing": self._batch_strategy
        }
        
        benchmark_results = {}
        
        for strategy_name, strategy_func in strategies.items():
            with aioresponses() as m:
                # Мокаем ответы для каждой стратегии
                for i in range(100):
                    m.get(
                        f"https://api.test.com/v1/benchmark?strategy={strategy_name}&id={i}",
                        status=200,
                        payload={"success": True, "strategy": strategy_name, "id": i}
                    )
                
                # Запускаем бенчмарк
                result = await benchmark_runner.run_benchmark(
                    name=strategy_name,
                    test_func=strategy_func,
                    iterations=3,  # Несколько итераций для усреднения
                    warmup_iterations=1
                )
                
                benchmark_results[strategy_name] = result
        
        # Анализируем результаты бенчмарка
        for strategy_name, result in benchmark_results.items():
            assert isinstance(result, BenchmarkResult)
            assert result.total_iterations == 3
            assert result.average_duration > 0
            assert result.min_duration <= result.average_duration <= result.max_duration
        
        # Параллельные стратегии должны быть быстрее последовательной
        sequential_time = benchmark_results["sequential"].average_duration
        concurrent_10_time = benchmark_results["concurrent_10"].average_duration
        
        assert concurrent_10_time < sequential_time * 0.8  # Значительное ускорение
    
    async def _sequential_strategy(self):
        """Последовательная стратегия для бенчмарка"""
        async with aiohttp.ClientSession() as session:
            for i in range(20):
                async with session.get(f"https://api.test.com/v1/benchmark?strategy=sequential&id={i}") as response:
                    await response.json()
    
    async def _concurrent_strategy(self, concurrency: int):
        """Параллельная стратегия для бенчмарка"""
        async def make_request(request_id: int):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.test.com/v1/benchmark?strategy=concurrent_{concurrency}&id={request_id}") as response:
                    return await response.json()
        
        tasks = [make_request(i) for i in range(20)]
        await asyncio.gather(*tasks)
    
    async def _batch_strategy(self):
        """Батчевая стратегия для бенчмарка"""
        batch_size = 5
        async with aiohttp.ClientSession() as session:
            for batch_start in range(0, 20, batch_size):
                batch_tasks = []
                for i in range(batch_start, min(batch_start + batch_size, 20)):
                    task = session.get(f"https://api.test.com/v1/benchmark?strategy=batch_processing&id={i}")
                    batch_tasks.append(task)
                
                responses = await asyncio.gather(*batch_tasks)
                for response in responses:
                    await response.json()
                    response.close()
    
    @pytest.mark.asyncio
    async def test_performance_regression_detection(self):
        """Тест обнаружения регрессии производительности"""
        baseline_metrics = PerformanceMetrics(
            average_response_time=100.0,  # ms
            p95_response_time=200.0,
            requests_per_second=50.0,
            error_rate=0.01,
            memory_usage_mb=100.0
        )
        
        # Текущие метрики с регрессией
        current_metrics = PerformanceMetrics(
            average_response_time=150.0,  # +50% регрессия
            p95_response_time=300.0,      # +50% регрессия
            requests_per_second=35.0,     # -30% регрессия
            error_rate=0.05,              # +400% регрессия
            memory_usage_mb=150.0         # +50% регрессия
        )
        
        performance_monitor = PerformanceMonitor()
        
        # Проверяем обнаружение регрессии
        regression_report = performance_monitor.detect_performance_regression(
            baseline=baseline_metrics,
            current=current_metrics,
            threshold_percent=20.0  # 20% порог для регрессии
        )
        
        # Должны быть обнаружены регрессии
        assert regression_report.has_regression is True
        assert len(regression_report.regressed_metrics) >= 4  # Все метрики кроме памяти возможно
        
        # Проверяем детали регрессии
        assert "average_response_time" in regression_report.regressed_metrics
        assert "requests_per_second" in regression_report.regressed_metrics
        assert "error_rate" in regression_report.regressed_metrics
    
    @pytest.mark.asyncio
    async def test_performance_optimization_suggestions(self):
        """Тест генерации предложений по оптимизации производительности"""
        # Метрики с проблемами производительности
        problematic_metrics = PerformanceMetrics(
            average_response_time=500.0,  # Медленные ответы
            p95_response_time=1000.0,     # Очень медленные в 95 перцентиле
            requests_per_second=5.0,      # Низкая пропускная способность
            error_rate=0.1,               # Высокий процент ошибок
            memory_usage_mb=500.0,        # Высокое потребление памяти
            cpu_usage_percent=85.0        # Высокая нагрузка на CPU
        )
        
        performance_monitor = PerformanceMonitor()
        
        # Генерируем предложения по оптимизации
        optimization_suggestions = performance_monitor.generate_optimization_suggestions(
            metrics=problematic_metrics
        )
        
        # Проверяем что предложения содержат релевантные рекомендации
        suggestions_text = " ".join(optimization_suggestions)
        
        assert "response time" in suggestions_text.lower() or "время ответа" in suggestions_text.lower()
        assert "memory" in suggestions_text.lower() or "память" in suggestions_text.lower()
        assert "cpu" in suggestions_text.lower() or "процессор" in suggestions_text.lower()
        assert len(optimization_suggestions) >= 3  # Минимум 3 предложения


@pytest.mark.integration
class TestPerformanceEdgeCases:
    """Тесты граничных случаев производительности"""
    
    @pytest.mark.asyncio
    async def test_performance_under_memory_pressure(self):
        """Тест производительности при нехватке памяти"""
        # Создаем условия нехватки памяти
        memory_hog = []
        try:
            # Выделяем большое количество памяти
            for i in range(1000):
                memory_hog.append(bytearray(1024 * 1024))  # 1MB блоки
                
                # Проверяем использование памяти
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 80:  # Останавливаемся при 80% использования
                    break
            
            # Тестируем производительность при высоком потреблении памяти
            performance_monitor = PerformanceMonitor()
            
            with aioresponses() as m:
                for i in range(10):
                    m.get(f"https://api.test.com/v1/memory-test?id={i}", status=200, payload={"id": i})
                
                start_time = time.perf_counter()
                
                async with performance_monitor.measure_operation("memory_pressure_test"):
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for i in range(10):
                            task = session.get(f"https://api.test.com/v1/memory-test?id={i}")
                            tasks.append(task)
                        
                        responses = await asyncio.gather(*tasks)
                        for response in responses:
                            await response.json()
                            response.close()
                
                end_time = time.perf_counter()
                
                # Производительность может снизиться, но не должна полностью деградировать
                total_time = end_time - start_time
                assert total_time < 30.0  # Разумное время даже при нехватке памяти
                
        finally:
            # Освобождаем память
            del memory_hog
            gc.collect()
    
    @pytest.mark.asyncio
    async def test_performance_with_network_latency(self):
        """Тест производительности при высокой задержке сети"""
        
        async def slow_callback(url, **kwargs):
            # Имитируем высокую задержку сети
            await asyncio.sleep(0.5)  # 500ms задержка
            return aiohttp.web.Response(
                status=200,
                body='{"success": true}',
                content_type='application/json'
            )
        
        with aioresponses() as m:
            for i in range(5):
                m.get(f"https://api.test.com/v1/slow?id={i}", callback=slow_callback)
            
            performance_monitor = PerformanceMonitor()
            
            start_time = time.perf_counter()
            
            async with performance_monitor.measure_operation("high_latency_test"):
                async with aiohttp.ClientSession() as session:
                    # Последовательные запросы при высокой задержке
                    for i in range(3):  # Меньше запросов из-за задержки
                        async with session.get(f"https://api.test.com/v1/slow?id={i}") as response:
                            await response.json()
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Время должно отражать задержку сети
            expected_min_time = 3 * 0.5  # 3 запроса * 500ms
            assert total_time >= expected_min_time * 0.8  # Учитываем погрешность
            
            metrics = performance_monitor.get_metrics()
            latency_stats = metrics.operation_metrics["high_latency_test"]
            
            # Средняя длительность должна отражать высокую задержку
            assert latency_stats.average_duration >= 0.4  # Близко к 500ms
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_overhead(self):
        """Тест накладных расходов мониторинга производительности"""
        
        # Тест без мониторинга
        with aioresponses() as m:
            for i in range(100):
                m.get(f"https://api.test.com/v1/overhead-test?id={i}", status=200, payload={"id": i})
            
            start_time = time.perf_counter()
            
            async with aiohttp.ClientSession() as session:
                for i in range(50):
                    async with session.get(f"https://api.test.com/v1/overhead-test?id={i}") as response:
                        await response.json()
            
            time_without_monitoring = time.perf_counter() - start_time
        
        # Тест с мониторингом
        performance_monitor = PerformanceMonitor(collect_detailed_metrics=True)
        
        with aioresponses() as m:
            for i in range(100):
                m.get(f"https://api.test.com/v1/overhead-test?id={i}", status=200, payload={"id": i})
            
            start_time = time.perf_counter()
            
            async with performance_monitor.measure_operation("overhead_test"):
                async with aiohttp.ClientSession() as session:
                    for i in range(50):
                        async with session.get(f"https://api.test.com/v1/overhead-test?id={i}") as response:
                            await response.json()
            
            time_with_monitoring = time.perf_counter() - start_time
        
        # Накладные расходы мониторинга должны быть минимальными
        overhead_percent = (time_with_monitoring - time_without_monitoring) / time_without_monitoring * 100
        assert overhead_percent < 20.0  # Не более 20% накладных расходов
    
    @pytest.mark.asyncio
    async def test_performance_with_connection_pool_exhaustion(self):
        """Тест производительности при исчерпании пула соединений"""
        # Создаем сессию с ограниченным пулом соединений
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        
        with aioresponses() as m:
            for i in range(20):
                m.get(f"https://api.test.com/v1/pool-test?id={i}", status=200, payload={"id": i})
            
            performance_monitor = PerformanceMonitor()
            
            async with aiohttp.ClientSession(connector=connector) as session:
                start_time = time.perf_counter()
                
                async with performance_monitor.measure_operation("pool_exhaustion_test"):
                    # Запускаем больше запросов чем доступно соединений
                    tasks = []
                    for i in range(10):  # 10 запросов при лимите 2 на хост
                        task = session.get(f"https://api.test.com/v1/pool-test?id={i}")
                        tasks.append(task)
                    
                    responses = await asyncio.gather(*tasks)
                    for response in responses:
                        await response.json()
                        response.close()
                
                end_time = time.perf_counter()
                
                # Запросы должны выполниться, но могут быть медленнее из-за ожидания соединений
                total_time = end_time - start_time
                assert total_time < 10.0  # Разумное время даже при ограничениях пула
                
                metrics = performance_monitor.get_metrics()
                pool_stats = metrics.operation_metrics["pool_exhaustion_test"]
                
                # Все запросы должны завершиться успешно
                assert pool_stats.total_operations == 1
                assert pool_stats.success_rate == 1.0
