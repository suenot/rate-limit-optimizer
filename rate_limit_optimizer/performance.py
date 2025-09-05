"""
Мониторинг производительности и нагрузочное тестирование
"""
import asyncio
import logging
import statistics
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
import psutil
import gc

from .models import (
    PerformanceMetrics, LoadTestResult, BenchmarkResult, ResourceUsage
)

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(
        self,
        collect_detailed_metrics: bool = True,
        sampling_interval: float = 1.0,
        memory_profiling: bool = False
    ):
        self.collect_detailed_metrics = collect_detailed_metrics
        self.sampling_interval = sampling_interval
        self.memory_profiling = memory_profiling
        
        # Метрики запросов
        self.request_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Метрики операций
        self.operation_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Системные метрики
        self.system_metrics: List[Dict[str, Any]] = []
        
        # Активные измерения
        self._active_measurements: Dict[str, float] = {}
    
    @asynccontextmanager
    async def measure_request(self, request_name: str):
        """Контекстный менеджер для измерения запроса"""
        
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage() if self.memory_profiling else 0
        
        try:
            yield
            
            # Успешное выполнение
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage() if self.memory_profiling else 0
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self._record_request_metric(request_name, duration, True, memory_delta)
            
        except Exception as e:
            # Ошибка выполнения
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self._record_request_metric(request_name, duration, False, 0)
            raise
    
    @asynccontextmanager
    async def measure_operation(self, operation_name: str):
        """Контекстный менеджер для измерения операции"""
        
        start_time = time.perf_counter()
        
        try:
            yield
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self._record_operation_metric(operation_name, duration, True)
            
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self._record_operation_metric(operation_name, duration, False)
            raise
    
    @asynccontextmanager
    async def measure_concurrent_requests(self, operation_name: str):
        """Контекстный менеджер для измерения параллельных запросов"""
        
        start_time = time.perf_counter()
        
        try:
            yield
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Записываем как операцию с пометкой о параллельности
            self._record_operation_metric(f"{operation_name}_concurrent", duration, True)
            
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self._record_operation_metric(f"{operation_name}_concurrent", duration, False)
            raise
    
    def _record_request_metric(
        self, 
        request_name: str, 
        duration: float, 
        success: bool,
        memory_delta: float = 0
    ) -> None:
        """Запись метрики запроса"""
        
        if request_name not in self.request_metrics:
            self.request_metrics[request_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': [],
                'memory_deltas': [],
                'min_response_time': float('inf'),
                'max_response_time': 0,
                'total_duration': 0
            }
        
        metrics = self.request_metrics[request_name]
        metrics['total_requests'] += 1
        metrics['response_times'].append(duration)
        metrics['total_duration'] += duration
        
        if success:
            metrics['successful_requests'] += 1
        else:
            metrics['failed_requests'] += 1
        
        # Обновляем min/max
        metrics['min_response_time'] = min(metrics['min_response_time'], duration)
        metrics['max_response_time'] = max(metrics['max_response_time'], duration)
        
        if self.memory_profiling:
            metrics['memory_deltas'].append(memory_delta)
    
    def _record_operation_metric(
        self, 
        operation_name: str, 
        duration: float, 
        success: bool
    ) -> None:
        """Запись метрики операции"""
        
        if operation_name not in self.operation_metrics:
            self.operation_metrics[operation_name] = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'durations': [],
                'min_duration': float('inf'),
                'max_duration': 0,
                'total_duration': 0
            }
        
        metrics = self.operation_metrics[operation_name]
        metrics['total_operations'] += 1
        metrics['durations'].append(duration)
        metrics['total_duration'] += duration
        
        if success:
            metrics['successful_operations'] += 1
        else:
            metrics['failed_operations'] += 1
        
        # Обновляем min/max
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        metrics['max_duration'] = max(metrics['max_duration'], duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        
        # Вычисляем агрегированные метрики для запросов
        processed_request_metrics = {}
        for name, raw_metrics in self.request_metrics.items():
            if raw_metrics['response_times']:
                response_times = raw_metrics['response_times']
                processed_request_metrics[name] = {
                    'total_requests': raw_metrics['total_requests'],
                    'successful_requests': raw_metrics['successful_requests'],
                    'failed_requests': raw_metrics['failed_requests'],
                    'success_rate': raw_metrics['successful_requests'] / raw_metrics['total_requests'],
                    'average_response_time': statistics.mean(response_times),
                    'median_response_time': statistics.median(response_times),
                    'min_response_time': raw_metrics['min_response_time'],
                    'max_response_time': raw_metrics['max_response_time'],
                    'p95_response_time': self._percentile(response_times, 95),
                    'p99_response_time': self._percentile(response_times, 99)
                }
        
        # Вычисляем агрегированные метрики для операций
        processed_operation_metrics = {}
        for name, raw_metrics in self.operation_metrics.items():
            if raw_metrics['durations']:
                durations = raw_metrics['durations']
                processed_operation_metrics[name] = {
                    'total_operations': raw_metrics['total_operations'],
                    'successful_operations': raw_metrics['successful_operations'],
                    'failed_operations': raw_metrics['failed_operations'],
                    'success_rate': raw_metrics['successful_operations'] / raw_metrics['total_operations'],
                    'average_duration': statistics.mean(durations),
                    'median_duration': statistics.median(durations),
                    'min_duration': raw_metrics['min_duration'],
                    'max_duration': raw_metrics['max_duration']
                }
        
        return {
            'request_metrics': processed_request_metrics,
            'operation_metrics': processed_operation_metrics,
            'system_metrics': self.system_metrics[-10:] if self.system_metrics else []  # Последние 10
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Вычисление перцентиля"""
        
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index < len(sorted_data):
                return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
            else:
                return sorted_data[lower_index]
    
    def _get_memory_usage(self) -> float:
        """Получение текущего использования памяти в MB"""
        
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def detect_performance_regression(
        self,
        baseline: PerformanceMetrics,
        current: PerformanceMetrics,
        threshold_percent: float = 20.0
    ) -> Dict[str, Any]:
        """Обнаружение регрессии производительности"""
        
        regressed_metrics = []
        
        # Проверяем время ответа
        if current.average_response_time > baseline.average_response_time * (1 + threshold_percent / 100):
            regressed_metrics.append("average_response_time")
        
        # Проверяем пропускную способность
        if current.requests_per_second < baseline.requests_per_second * (1 - threshold_percent / 100):
            regressed_metrics.append("requests_per_second")
        
        # Проверяем процент ошибок
        if current.error_rate > baseline.error_rate * (1 + threshold_percent / 100):
            regressed_metrics.append("error_rate")
        
        # Проверяем использование памяти
        if current.memory_usage_mb > baseline.memory_usage_mb * (1 + threshold_percent / 100):
            regressed_metrics.append("memory_usage_mb")
        
        return {
            "has_regression": len(regressed_metrics) > 0,
            "regressed_metrics": regressed_metrics,
            "threshold_percent": threshold_percent,
            "baseline": baseline.model_dump(),
            "current": current.model_dump()
        }
    
    def generate_optimization_suggestions(self, metrics: PerformanceMetrics) -> List[str]:
        """Генерация предложений по оптимизации"""
        
        suggestions = []
        
        # Анализ времени ответа
        if metrics.average_response_time > 1.0:  # Более 1 секунды
            suggestions.append(
                "Среднее время ответа превышает 1 секунду. "
                "Рассмотрите оптимизацию запросов, добавление кэширования или использование CDN."
            )
        
        if metrics.p95_response_time > metrics.average_response_time * 3:
            suggestions.append(
                "95-й перцентиль времени ответа значительно выше среднего. "
                "Проверьте наличие медленных запросов и оптимизируйте их."
            )
        
        # Анализ пропускной способности
        if metrics.requests_per_second < 10:
            suggestions.append(
                "Низкая пропускная способность. "
                "Рассмотрите увеличение параллельности, оптимизацию алгоритмов или масштабирование."
            )
        
        # Анализ ошибок
        if metrics.error_rate > 0.05:  # Более 5% ошибок
            suggestions.append(
                "Высокий процент ошибок. "
                "Проверьте логику обработки ошибок, retry политики и стабильность внешних сервисов."
            )
        
        # Анализ памяти
        if metrics.memory_usage_mb > 500:  # Более 500 MB
            suggestions.append(
                "Высокое потребление памяти. "
                "Проверьте наличие утечек памяти, оптимизируйте структуры данных и добавьте garbage collection."
            )
        
        # Анализ CPU
        if hasattr(metrics, 'cpu_usage_percent') and metrics.cpu_usage_percent > 80:
            suggestions.append(
                "Высокая нагрузка на CPU. "
                "Оптимизируйте алгоритмы, добавьте кэширование вычислений или увеличьте количество ядер."
            )
        
        return suggestions


class LoadTester:
    """Нагрузочное тестирование"""
    
    def __init__(
        self,
        max_concurrent_requests: int = 50,
        ramp_up_duration: float = 10.0,
        test_duration: float = 60.0,
        target_rps: float = 10.0,
        stress_test_mode: bool = False
    ):
        self.max_concurrent_requests = max_concurrent_requests
        self.ramp_up_duration = ramp_up_duration
        self.test_duration = test_duration
        self.target_rps = target_rps
        self.stress_test_mode = stress_test_mode
    
    async def run_load_test(
        self,
        request_func: Callable,
        target_url: str
    ) -> LoadTestResult:
        """Запуск нагрузочного тестирования"""
        
        logger.info(f"Начинаем нагрузочное тестирование: {self.target_rps} RPS, {self.test_duration}s")
        
        start_time = time.perf_counter()
        end_time = start_time + self.test_duration
        
        # Результаты
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        # Семафор для ограничения параллельности
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def make_request():
            nonlocal total_requests, successful_requests, failed_requests
            
            async with semaphore:
                request_start = time.perf_counter()
                
                try:
                    await request_func()
                    successful_requests += 1
                    
                except Exception as e:
                    failed_requests += 1
                    logger.debug(f"Request failed: {e}")
                
                finally:
                    request_end = time.perf_counter()
                    response_times.append(request_end - request_start)
                    total_requests += 1
        
        # Постепенное увеличение нагрузки
        tasks = []
        current_time = start_time
        
        while current_time < end_time:
            # Вычисляем текущую частоту на основе ramp-up
            elapsed = current_time - start_time
            if elapsed < self.ramp_up_duration:
                # Постепенное увеличение
                ramp_progress = elapsed / self.ramp_up_duration
                current_rps = self.target_rps * ramp_progress
            else:
                # Полная нагрузка
                current_rps = self.target_rps
            
            if current_rps > 0:
                # Интервал между запросами
                interval = 1.0 / current_rps
                
                # Запускаем запрос
                task = asyncio.create_task(make_request())
                tasks.append(task)
                
                # Ждем интервал
                await asyncio.sleep(interval)
            
            current_time = time.perf_counter()
        
        # Ждем завершения всех запросов
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        actual_duration = time.perf_counter() - start_time
        
        # Вычисляем метрики
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p50_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        actual_rps = total_requests / actual_duration if actual_duration > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        result = LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            requests_per_second=actual_rps,
            error_rate=error_rate,
            test_duration_seconds=actual_duration,
            max_concurrent_requests=self.max_concurrent_requests
        )
        
        logger.info(f"Нагрузочное тестирование завершено: {total_requests} запросов, {actual_rps:.1f} RPS")
        return result
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Вычисление перцентиля"""
        
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index < len(sorted_data):
                return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
            else:
                return sorted_data[lower_index]


class BenchmarkRunner:
    """Запуск бенчмарков"""
    
    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
    
    async def run_benchmark(
        self,
        name: str,
        test_func: Callable,
        iterations: int = 10,
        warmup_iterations: int = 3
    ) -> BenchmarkResult:
        """Запуск бенчмарка"""
        
        logger.info(f"Запуск бенчмарка '{name}': {iterations} итераций")
        
        # Прогрев
        for i in range(warmup_iterations):
            try:
                await test_func()
            except Exception as e:
                logger.warning(f"Ошибка в прогреве {i+1}: {e}")
        
        # Основные измерения
        durations = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                await test_func()
                end_time = time.perf_counter()
                durations.append(end_time - start_time)
                
            except Exception as e:
                logger.error(f"Ошибка в итерации {i+1}: {e}")
                # Записываем максимальное время как штраф за ошибку
                durations.append(10.0)
        
        # Вычисляем статистики
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            if len(durations) > 1:
                std_deviation = statistics.stdev(durations)
            else:
                std_deviation = 0.0
            
            ops_per_second = 1.0 / avg_duration if avg_duration > 0 else 0
        else:
            avg_duration = min_duration = max_duration = std_deviation = ops_per_second = 0
        
        result = BenchmarkResult(
            name=name,
            total_iterations=iterations,
            average_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            standard_deviation=std_deviation,
            operations_per_second=ops_per_second
        )
        
        self.results[name] = result
        
        logger.info(f"Бенчмарк '{name}' завершен: {avg_duration:.3f}s среднее, {ops_per_second:.1f} ops/s")
        return result
    
    def get_results(self) -> Dict[str, BenchmarkResult]:
        """Получение всех результатов бенчмарков"""
        return self.results.copy()
    
    def compare_results(self, baseline_name: str, current_name: str) -> Dict[str, Any]:
        """Сравнение результатов бенчмарков"""
        
        if baseline_name not in self.results or current_name not in self.results:
            raise ValueError("Один из бенчмарков не найден")
        
        baseline = self.results[baseline_name]
        current = self.results[current_name]
        
        # Вычисляем изменения
        duration_change = (current.average_duration - baseline.average_duration) / baseline.average_duration * 100
        ops_change = (current.operations_per_second - baseline.operations_per_second) / baseline.operations_per_second * 100
        
        return {
            "baseline": baseline.model_dump(),
            "current": current.model_dump(),
            "duration_change_percent": duration_change,
            "operations_change_percent": ops_change,
            "is_improvement": duration_change < 0,  # Меньше время = лучше
            "significant_change": abs(duration_change) > 5  # Более 5% считаем значимым
        }


class ResourceMonitor:
    """Мониторинг ресурсов системы"""
    
    def __init__(
        self,
        monitor_memory: bool = True,
        monitor_cpu: bool = True,
        sampling_interval: float = 1.0
    ):
        self.monitor_memory = monitor_memory
        self.monitor_cpu = monitor_cpu
        self.sampling_interval = sampling_interval
        
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._samples: List[Dict[str, float]] = []
        self._initial_memory = 0.0
    
    def start_monitoring(self) -> None:
        """Начало мониторинга"""
        
        if self._monitoring:
            return
        
        self._monitoring = True
        self._initial_memory = self._get_memory_usage()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("Мониторинг ресурсов запущен")
    
    def stop_monitoring(self) -> None:
        """Остановка мониторинга"""
        
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
        
        logger.info("Мониторинг ресурсов остановлен")
    
    async def _monitor_loop(self) -> None:
        """Цикл мониторинга"""
        
        while self._monitoring:
            try:
                sample = {}
                
                if self.monitor_memory:
                    sample['memory_mb'] = self._get_memory_usage()
                
                if self.monitor_cpu:
                    sample['cpu_percent'] = self._get_cpu_usage()
                
                sample['timestamp'] = time.time()
                self._samples.append(sample)
                
                # Ограничиваем количество сэмплов
                if len(self._samples) > 1000:
                    self._samples = self._samples[-500:]  # Оставляем последние 500
                
                await asyncio.sleep(self.sampling_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка мониторинга ресурсов: {e}")
                await asyncio.sleep(self.sampling_interval)
    
    def get_resource_usage(self) -> ResourceUsage:
        """Получение статистики использования ресурсов"""
        
        if not self._samples:
            return ResourceUsage(
                initial_memory_mb=self._initial_memory,
                peak_memory_mb=self._initial_memory,
                average_memory_mb=self._initial_memory,
                peak_cpu_percent=0,
                average_cpu_percent=0,
                test_duration_seconds=0
            )
        
        # Извлекаем данные
        memory_values = [s['memory_mb'] for s in self._samples if 'memory_mb' in s]
        cpu_values = [s['cpu_percent'] for s in self._samples if 'cpu_percent' in s]
        
        # Вычисляем статистики
        peak_memory = max(memory_values) if memory_values else self._initial_memory
        avg_memory = statistics.mean(memory_values) if memory_values else self._initial_memory
        
        peak_cpu = max(cpu_values) if cpu_values else 0
        avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
        
        # Длительность мониторинга
        if len(self._samples) >= 2:
            duration = self._samples[-1]['timestamp'] - self._samples[0]['timestamp']
        else:
            duration = 0
        
        return ResourceUsage(
            initial_memory_mb=self._initial_memory,
            peak_memory_mb=peak_memory,
            average_memory_mb=avg_memory,
            peak_cpu_percent=peak_cpu,
            average_cpu_percent=avg_cpu,
            test_duration_seconds=duration
        )
    
    def _get_memory_usage(self) -> float:
        """Получение использования памяти в MB"""
        
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def _get_cpu_usage(self) -> float:
        """Получение использования CPU в процентах"""
        
        return psutil.cpu_percent(interval=None)


class MetricsCollector:
    """Сборщик метрик производительности"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: float) -> None:
        """Запись метрики"""
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(value)
        
        # Ограничиваем размер истории
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-500:]
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Увеличение счетчика"""
        
        if name not in self.counters:
            self.counters[name] = 0
        
        self.counters[name] += value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Установка значения gauge"""
        
        self.gauges[name] = value
    
    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Получение статистики по метрике"""
        
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        
        return {
            'metrics': {name: self.get_metric_stats(name) for name in self.metrics},
            'counters': self.counters.copy(),
            'gauges': self.gauges.copy()
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Вычисление перцентиля"""
        
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index < len(sorted_data):
                return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
            else:
                return sorted_data[lower_index]
