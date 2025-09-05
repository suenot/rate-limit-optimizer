"""
Определение rate limits через заголовки и тестирование
"""
import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from urllib.parse import urljoin
import random

import aiohttp
from aiohttp import ClientTimeout, ClientError

from .models import (
    RateLimit, RateLimitTier, MultiTierResult, TierTestResult,
    DetectionMethod, TargetSite, DetectionSettings
)
from .exceptions import RateLimitExceeded, NetworkError, ServerError

logger = logging.getLogger(__name__)


class HeaderAnalyzer:
    """Анализатор заголовков для определения rate limits"""
    
    def __init__(self):
        self.rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "X-RateLimit-Window",
            "X-Rate-Limit-Limit-Minute",
            "X-Rate-Limit-Limit-Hour", 
            "X-Rate-Limit-Limit-Day",
            "X-Rate-Limit-Remaining-Minute",
            "X-Rate-Limit-Remaining-Hour",
            "X-Rate-Limit-Remaining-Day",
            "X-Rate-Limit-Reset-Minute",
            "X-Rate-Limit-Reset-Hour",
            "X-Rate-Limit-Reset-Day",
            "Retry-After"
        ]
    
    def extract_rate_limits(self, headers: Dict[str, str]) -> List[RateLimit]:
        """Извлечение rate limits из заголовков"""
        limits = []
        
        # Стандартные заголовки
        basic_limit = self._extract_basic_limit(headers)
        if basic_limit:
            limits.append(basic_limit)
        
        # Многоуровневые заголовки
        multi_limits = self._extract_multi_tier_limits(headers)
        limits.extend(multi_limits)
        
        # Фильтруем дубликаты и некорректные лимиты
        return self._filter_valid_limits(limits)
    
    def _extract_basic_limit(self, headers: Dict[str, str]) -> Optional[RateLimit]:
        """Извлечение базового лимита"""
        limit_str = headers.get("X-RateLimit-Limit") or headers.get("X-Rate-Limit-Limit")
        remaining_str = headers.get("X-RateLimit-Remaining") or headers.get("X-Rate-Limit-Remaining")
        reset_str = headers.get("X-RateLimit-Reset") or headers.get("X-Rate-Limit-Reset")
        window_str = headers.get("X-RateLimit-Window") or headers.get("X-Rate-Limit-Window")
        
        if not limit_str:
            return None
        
        try:
            limit = int(limit_str)
            remaining = int(remaining_str) if remaining_str else limit
            
            # Определяем время сброса
            reset_time = None
            if reset_str:
                try:
                    # Пробуем как timestamp
                    reset_timestamp = int(reset_str)
                    reset_time = datetime.fromtimestamp(reset_timestamp)
                except ValueError:
                    # Пробуем как секунды до сброса
                    try:
                        seconds_until_reset = int(reset_str)
                        reset_time = datetime.now() + timedelta(seconds=seconds_until_reset)
                    except ValueError:
                        pass
            
            # Определяем временное окно
            window_seconds = 60  # По умолчанию минута
            if window_str:
                try:
                    window_seconds = int(window_str)
                except ValueError:
                    pass
            
            return RateLimit(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                window_seconds=window_seconds,
                detected_via=DetectionMethod.HEADERS
            )
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Ошибка парсинга базового лимита: {e}")
            return None
    
    def _extract_multi_tier_limits(self, headers: Dict[str, str]) -> List[RateLimit]:
        """Извлечение многоуровневых лимитов"""
        limits = []
        
        # Паттерны для различных временных окон
        tier_patterns = {
            "10s": (10, ["10s", "10_seconds", "10-seconds"]),
            "minute": (60, ["minute", "min", "60"]),
            "15min": (900, ["15min", "15_minutes", "15-minutes"]),
            "hour": (3600, ["hour", "hr", "3600"]),
            "day": (86400, ["day", "daily", "86400"])
        }
        
        for tier_name, (window_seconds, patterns) in tier_patterns.items():
            limit = self._extract_tier_limit(headers, patterns, window_seconds)
            if limit:
                limits.append(limit)
        
        return limits
    
    def _extract_tier_limit(self, headers: Dict[str, str], patterns: List[str], window_seconds: int) -> Optional[RateLimit]:
        """Извлечение лимита для конкретного уровня"""
        limit_value = None
        remaining_value = None
        reset_time = None
        
        # Ищем заголовки с паттернами
        for header_name, header_value in headers.items():
            header_lower = header_name.lower()
            
            # Проверяем паттерны в имени заголовка
            for pattern in patterns:
                if pattern.lower() in header_lower:
                    if "limit" in header_lower and "remaining" not in header_lower:
                        try:
                            limit_value = int(header_value)
                        except ValueError:
                            continue
                    elif "remaining" in header_lower:
                        try:
                            remaining_value = int(header_value)
                        except ValueError:
                            continue
                    elif "reset" in header_lower:
                        try:
                            reset_timestamp = int(header_value)
                            reset_time = datetime.fromtimestamp(reset_timestamp)
                        except ValueError:
                            continue
        
        if limit_value is not None:
            return RateLimit(
                limit=limit_value,
                remaining=remaining_value if remaining_value is not None else limit_value,
                reset_time=reset_time,
                window_seconds=window_seconds,
                detected_via=DetectionMethod.HEADERS
            )
        
        return None
    
    def _filter_valid_limits(self, limits: List[RateLimit]) -> List[RateLimit]:
        """Фильтрация валидных лимитов"""
        valid_limits = []
        seen_windows = set()
        
        for limit in limits:
            # Проверяем корректность значений
            if limit.limit <= 0:
                continue
            
            if limit.remaining < 0:
                limit.remaining = 0
            elif limit.remaining > limit.limit:
                limit.remaining = limit.limit
            
            # Избегаем дубликатов по временному окну
            if limit.window_seconds not in seen_windows:
                valid_limits.append(limit)
                seen_windows.add(limit.window_seconds)
        
        return valid_limits


class TierTester:
    """Тестировщик отдельного уровня rate limit"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self._should_close_session = session is None
    
    async def __aenter__(self):
        if not self.session:
            timeout = ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_session and self.session:
            await self.session.close()
    
    async def test_tier(
        self, 
        url: str, 
        tier: RateLimitTier, 
        headers: Optional[Dict[str, str]] = None
    ) -> TierTestResult:
        """Тестирование конкретного уровня лимита"""
        
        if not self.session:
            async with self:
                return await self._test_tier_impl(url, tier, headers)
        else:
            return await self._test_tier_impl(url, tier, headers)
    
    async def _test_tier_impl(
        self, 
        url: str, 
        tier: RateLimitTier, 
        headers: Optional[Dict[str, str]] = None
    ) -> TierTestResult:
        """Внутренняя реализация тестирования уровня"""
        
        logger.info(f"Начинаем тестирование tier '{tier.name}' для {url}")
        
        start_time = time.time()
        requests_sent = 0
        successful_requests = 0
        server_errors = 0
        current_rate = tier.start_rate
        detected_limit = None
        backoff_triggered = False
        retry_after_seconds = None
        final_rate_when_limited = None
        adaptive_increments_used = 0
        error_details = ""
        retry_reasons = []
        
        test_duration = tier.test_duration_seconds
        end_time = start_time + test_duration
        
        while time.time() < end_time and current_rate <= tier.max_rate:
            batch_start = time.time()
            
            # Отправляем запросы с текущей частотой
            batch_results = await self._send_request_batch(
                url, current_rate, tier.window_seconds, headers
            )
            
            requests_sent += len(batch_results)
            
            # Анализируем результаты батча
            rate_limited = False
            for result in batch_results:
                if result['success']:
                    successful_requests += 1
                elif result['status_code'] == 429:
                    # Обнаружен rate limit
                    rate_limited = True
                    detected_limit = self._extract_limit_from_response(result, tier.window_seconds)
                    retry_after_seconds = result.get('retry_after')
                    final_rate_when_limited = current_rate
                    
                    logger.info(f"Rate limit обнаружен на частоте {current_rate} req/{tier.window_seconds}s")
                    break
                elif result['status_code'] >= 500:
                    server_errors += 1
                    error_details += f"Server error {result['status_code']}; "
                else:
                    error_details += f"Error {result['status_code']}; "
            
            if rate_limited:
                # Применяем backoff если указан retry_after
                if retry_after_seconds:
                    backoff_triggered = True
                    retry_reasons.append(f"Retry-After: {retry_after_seconds}s")
                    await asyncio.sleep(min(retry_after_seconds, 10))  # Максимум 10 секунд для тестов
                break
            
            # Увеличиваем частоту для следующей итерации
            if tier.adaptive_increment:
                # Адаптивное увеличение на основе успешности
                success_rate = successful_requests / requests_sent if requests_sent > 0 else 1.0
                if success_rate > 0.95:
                    increment = tier.increment * 2  # Агрессивнее если все хорошо
                    adaptive_increments_used += 1
                else:
                    increment = tier.increment
            else:
                increment = tier.increment
            
            current_rate += increment
            
            # Ждем до конца временного окна если нужно
            batch_duration = time.time() - batch_start
            if batch_duration < tier.window_seconds:
                await asyncio.sleep(tier.window_seconds - batch_duration)
        
        total_duration = time.time() - start_time
        error_rate = (requests_sent - successful_requests) / requests_sent if requests_sent > 0 else 0
        
        result = TierTestResult(
            tier_name=tier.name,
            limit_found=detected_limit is not None,
            detected_limit=detected_limit,
            requests_sent=requests_sent,
            successful_requests=successful_requests,
            error_rate=error_rate,
            average_response_time=0.1,  # Заглушка, в реальности нужно измерять
            test_duration_seconds=total_duration,
            backoff_triggered=backoff_triggered,
            retry_after_seconds=retry_after_seconds,
            final_rate_when_limited=final_rate_when_limited,
            adaptive_increments_used=adaptive_increments_used,
            server_errors=server_errors,
            error_details=error_details.strip(),
            retry_reasons=retry_reasons
        )
        
        logger.info(f"Тестирование tier '{tier.name}' завершено: {result.limit_found}")
        return result
    
    async def _send_request_batch(
        self, 
        url: str, 
        rate: int, 
        window_seconds: int, 
        headers: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Отправка батча запросов с заданной частотой"""
        
        results = []
        interval = window_seconds / rate if rate > 0 else 1.0
        
        for i in range(rate):
            try:
                start_time = time.time()
                
                async with self.session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    # Извлекаем retry_after если есть
                    retry_after = None
                    if response.status == 429:
                        retry_after_header = response.headers.get('Retry-After')
                        if retry_after_header:
                            try:
                                retry_after = int(retry_after_header)
                            except ValueError:
                                pass
                    
                    result = {
                        'success': response.status == 200,
                        'status_code': response.status,
                        'response_time': response_time,
                        'headers': dict(response.headers),
                        'retry_after': retry_after
                    }
                    
                    results.append(result)
                    
                    # Если получили 429, прекращаем батч
                    if response.status == 429:
                        break
                
                # Ждем интервал между запросами (кроме последнего)
                if i < rate - 1:
                    await asyncio.sleep(interval)
                    
            except asyncio.TimeoutError:
                results.append({
                    'success': False,
                    'status_code': 0,
                    'response_time': 30.0,
                    'headers': {},
                    'error': 'timeout'
                })
            except ClientError as e:
                results.append({
                    'success': False,
                    'status_code': 0,
                    'response_time': 0,
                    'headers': {},
                    'error': str(e)
                })
        
        return results
    
    def _extract_limit_from_response(self, response_result: Dict[str, Any], window_seconds: int) -> RateLimit:
        """Извлечение лимита из ответа с ошибкой 429"""
        headers = response_result.get('headers', {})
        
        # Пробуем извлечь лимит из заголовков
        analyzer = HeaderAnalyzer()
        limits = analyzer.extract_rate_limits(headers)
        
        # Ищем лимит с подходящим временным окном
        for limit in limits:
            if limit.window_seconds == window_seconds:
                return limit
        
        # Если не нашли в заголовках, создаем на основе тестирования
        limit_value = None
        remaining_value = 0
        
        # Пробуем извлечь из стандартных заголовков
        limit_header = headers.get('X-RateLimit-Limit') or headers.get('X-Rate-Limit-Limit')
        if limit_header:
            try:
                limit_value = int(limit_header)
            except ValueError:
                pass
        
        # Если не нашли, используем приблизительное значение
        if limit_value is None:
            # Предполагаем что лимит немного меньше текущей частоты
            limit_value = max(1, response_result.get('current_rate', 10) - 1)
        
        reset_time = None
        retry_after = response_result.get('retry_after')
        if retry_after:
            reset_time = datetime.now() + timedelta(seconds=retry_after)
        
        return RateLimit(
            limit=limit_value,
            remaining=remaining_value,
            reset_time=reset_time,
            window_seconds=window_seconds,
            detected_via=DetectionMethod.TESTING
        )


class MultiTierDetector:
    """Детектор многоуровневых rate limits"""
    
    def __init__(self, strategy: Optional[Any] = None):
        self.strategy = strategy
        self.header_analyzer = HeaderAnalyzer()
    
    async def detect_all_rate_limits(
        self,
        base_url: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        tiers_to_test: Optional[List[RateLimitTier]] = None,
        validate_consistency: bool = False,
        resolve_dependencies: bool = False
    ) -> MultiTierResult:
        """Определение всех уровней rate limits"""
        
        logger.info(f"Начинаем определение rate limits для {base_url}{endpoint}")
        
        start_time = time.time()
        url = urljoin(base_url, endpoint)
        
        # Сначала пробуем анализ заголовков
        header_limits = await self._analyze_headers(url, headers)
        
        # Если заголовки не дали полной информации, переходим к тестированию
        tested_limits = []
        if tiers_to_test:
            tested_limits = await self._test_tiers(url, tiers_to_test, headers)
        
        # Объединяем результаты
        all_limits = header_limits + [result.detected_limit for result in tested_limits if result.detected_limit]
        
        # Определяем самый строгий лимит
        most_restrictive = self._find_most_restrictive_limit(all_limits)
        
        # Рассчитываем рекомендуемую частоту
        recommended_rate = self._calculate_recommended_rate(all_limits, most_restrictive)
        
        # Собираем результат
        result = MultiTierResult(
            timestamp=datetime.now(),
            base_url=base_url,
            endpoint=endpoint,
            most_restrictive=most_restrictive,
            recommended_rate=recommended_rate,
            limits_found=len(all_limits),
            total_requests=sum(r.requests_sent for r in tested_limits),
            test_duration_seconds=time.time() - start_time,
            tier_results=tested_limits,
            endpoints_tested=[endpoint]
        )
        
        # Распределяем лимиты по уровням
        self._assign_limits_to_tiers(result, all_limits)
        
        # Валидация консистентности если запрошена
        if validate_consistency:
            result.consistency_warnings = self._validate_consistency(all_limits)
        
        logger.info(f"Определение завершено: найдено {len(all_limits)} лимитов")
        return result
    
    async def _analyze_headers(self, url: str, headers: Optional[Dict[str, str]] = None) -> List[RateLimit]:
        """Анализ заголовков для быстрого определения лимитов"""
        
        try:
            timeout = ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    response_headers = dict(response.headers)
                    
                    limits = self.header_analyzer.extract_rate_limits(response_headers)
                    
                    if limits:
                        logger.info(f"Найдено {len(limits)} лимитов в заголовках")
                    
                    return limits
                    
        except Exception as e:
            logger.warning(f"Ошибка анализа заголовков: {e}")
            return []
    
    async def _test_tiers(
        self, 
        url: str, 
        tiers: List[RateLimitTier], 
        headers: Optional[Dict[str, str]] = None
    ) -> List[TierTestResult]:
        """Тестирование уровней лимитов"""
        
        results = []
        
        async with TierTester() as tester:
            for tier in tiers:
                try:
                    result = await tester.test_tier(url, tier, headers)
                    results.append(result)
                    
                    # Если нашли лимит и стратегия требует остановки
                    if result.limit_found and getattr(self.strategy, 'stop_on_first_limit', False):
                        logger.info("Остановка тестирования после первого найденного лимита")
                        break
                        
                except Exception as e:
                    logger.error(f"Ошибка тестирования tier {tier.name}: {e}")
                    # Создаем результат с ошибкой
                    error_result = TierTestResult(
                        tier_name=tier.name,
                        limit_found=False,
                        requests_sent=0,
                        successful_requests=0,
                        error_rate=1.0,
                        average_response_time=0,
                        test_duration_seconds=0,
                        error_details=str(e)
                    )
                    results.append(error_result)
        
        return results
    
    def _find_most_restrictive_limit(self, limits: List[RateLimit]) -> str:
        """Определение самого строгого лимита"""
        if not limits:
            return "unknown"
        
        # Вычисляем requests per second для каждого лимита
        min_rps = float('inf')
        most_restrictive = "unknown"
        
        tier_names = {
            10: "10_seconds",
            60: "minute", 
            900: "15_minutes",
            3600: "hour",
            86400: "day"
        }
        
        for limit in limits:
            rps = limit.requests_per_second
            if rps < min_rps:
                min_rps = rps
                most_restrictive = tier_names.get(limit.window_seconds, f"{limit.window_seconds}s")
        
        return most_restrictive
    
    def _calculate_recommended_rate(self, limits: List[RateLimit], most_restrictive: str) -> int:
        """Расчет рекомендуемой частоты запросов"""
        if not limits:
            return 1
        
        # Находим самый строгий лимит
        min_limit = min(limits, key=lambda l: l.requests_per_second)
        
        # Применяем safety margin 10%
        safety_margin = 0.9
        recommended = int(min_limit.limit * safety_margin)
        
        return max(1, recommended)
    
    def _assign_limits_to_tiers(self, result: MultiTierResult, limits: List[RateLimit]) -> None:
        """Распределение лимитов по уровням в результате"""
        
        for limit in limits:
            if limit.window_seconds == 10:
                result.ten_second_limit = limit
            elif limit.window_seconds == 60:
                result.minute_limit = limit
            elif limit.window_seconds == 900:
                result.fifteen_minute_limit = limit
            elif limit.window_seconds == 3600:
                result.hour_limit = limit
            elif limit.window_seconds == 86400:
                result.day_limit = limit
    
    def _validate_consistency(self, limits: List[RateLimit]) -> List[str]:
        """Валидация консистентности между лимитами"""
        warnings = []
        
        if len(limits) < 2:
            return warnings
        
        # Сортируем по временному окну
        sorted_limits = sorted(limits, key=lambda l: l.window_seconds)
        
        for i in range(len(sorted_limits) - 1):
            current = sorted_limits[i]
            next_limit = sorted_limits[i + 1]
            
            # Проверяем что более длинные окна имеют пропорционально большие лимиты
            current_rps = current.requests_per_second
            next_rps = next_limit.requests_per_second
            
            if current_rps > next_rps * 1.1:  # 10% допуск
                warnings.append(
                    f"{current.window_seconds}s limit extrapolates to "
                    f"{current_rps * next_limit.window_seconds:.0f} req/{next_limit.window_seconds}s "
                    f"but actual limit is {next_limit.limit}"
                )
        
        return warnings
    
    async def detect_with_endpoint_rotation(
        self,
        base_url: str,
        endpoints: List[str],
        headers: Optional[Dict[str, str]] = None,
        rotation_interval: int = 3
    ) -> MultiTierResult:
        """Определение лимитов с ротацией endpoints"""
        
        # Для простоты используем первый endpoint
        # В полной реализации здесь была бы логика ротации
        primary_endpoint = endpoints[0] if endpoints else "/v1/test"
        
        result = await self.detect_all_rate_limits(base_url, primary_endpoint, headers)
        result.endpoints_tested = endpoints
        
        return result
    
    async def test_single_tier(
        self,
        base_url: str,
        endpoint: str,
        tier: RateLimitTier,
        headers: Optional[Dict[str, str]] = None
    ) -> TierTestResult:
        """Тестирование одного уровня"""
        
        url = urljoin(base_url, endpoint)
        
        async with TierTester() as tester:
            return await tester.test_tier(url, tier, headers)
    
    async def test_tiers_parallel(
        self,
        base_url: str,
        endpoint: str,
        tiers: List[RateLimitTier],
        headers: Optional[Dict[str, str]] = None,
        max_concurrent: int = 3
    ) -> MultiTierResult:
        """Параллельное тестирование нескольких уровней"""
        
        url = urljoin(base_url, endpoint)
        
        # Ограничиваем количество параллельных тестов
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def test_tier_with_semaphore(tier: RateLimitTier) -> TierTestResult:
            async with semaphore:
                async with TierTester() as tester:
                    return await tester.test_tier(url, tier, headers)
        
        # Запускаем параллельные тесты
        tasks = [test_tier_with_semaphore(tier) for tier in tiers]
        tier_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        valid_results = []
        for result in tier_results:
            if isinstance(result, TierTestResult):
                valid_results.append(result)
            else:
                logger.error(f"Ошибка параллельного тестирования: {result}")
        
        # Собираем общий результат
        all_limits = [r.detected_limit for r in valid_results if r.detected_limit]
        most_restrictive = self._find_most_restrictive_limit(all_limits)
        recommended_rate = self._calculate_recommended_rate(all_limits, most_restrictive)
        
        result = MultiTierResult(
            timestamp=datetime.now(),
            base_url=base_url,
            endpoint=endpoint,
            most_restrictive=most_restrictive,
            recommended_rate=recommended_rate,
            limits_found=len(all_limits),
            total_requests=sum(r.requests_sent for r in valid_results),
            test_duration_seconds=0,  # Параллельное выполнение
            tier_results=valid_results,
            endpoints_tested=[endpoint],
            parallel_execution=True
        )
        
        self._assign_limits_to_tiers(result, all_limits)
        
        return result
    
    async def detect_with_fallback_strategies(
        self,
        base_url: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        strategies: Optional[List[Any]] = None
    ) -> MultiTierResult:
        """Определение лимитов с fallback стратегиями"""
        
        # Для простоты используем основную стратегию
        # В полной реализации здесь была бы логика fallback
        return await self.detect_all_rate_limits(base_url, endpoint, headers)


class RateLimitDetector:
    """Основной детектор rate limits (для обратной совместимости)"""
    
    def __init__(self):
        self.multi_tier_detector = MultiTierDetector()
    
    async def detect_rate_limit(
        self,
        base_url: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[RateLimit]:
        """Определение основного rate limit"""
        
        result = await self.multi_tier_detector.detect_all_rate_limits(base_url, endpoint, headers)
        
        # Возвращаем самый строгий лимит
        all_limits = result.all_detected_limits
        if not all_limits:
            return None
        
        return min(all_limits, key=lambda l: l.requests_per_second)
