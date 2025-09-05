"""
Интеграционные тесты для определения rate limits через заголовки и тестирование
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.detection import (
    RateLimitDetector,
    HeaderAnalyzer,
    MultiTierDetector,
    TierTester
)
from rate_limit_optimizer.models import (
    RateLimit,
    RateLimitTier,
    MultiTierResult,
    TierTestResult,
    DetectionResult
)


class TestRateLimitDetectionIntegration:
    """Интеграционные тесты определения rate limits"""
    
    @pytest.fixture
    def sample_headers_with_limits(self) -> Dict[str, str]:
        """Заголовки ответа с информацией о rate limits"""
        return {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "95",
            "X-RateLimit-Reset": str(int((datetime.now() + timedelta(minutes=1)).timestamp())),
            "X-RateLimit-Window": "60",
            "X-Rate-Limit-Limit-Minute": "100",
            "X-Rate-Limit-Limit-Hour": "5000",
            "X-Rate-Limit-Limit-Day": "100000",
            "X-Rate-Limit-Remaining-Minute": "95",
            "X-Rate-Limit-Remaining-Hour": "4950",
            "X-Rate-Limit-Remaining-Day": "99900",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def sample_headers_no_limits(self) -> Dict[str, str]:
        """Заголовки ответа без информации о rate limits"""
        return {
            "Content-Type": "application/json",
            "Server": "nginx/1.18.0",
            "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        }
    
    @pytest.fixture
    def rate_limit_tier_10s(self) -> RateLimitTier:
        """Тестовый tier для 10-секундного окна"""
        return RateLimitTier(
            name="10_seconds",
            window_seconds=10,
            start_rate=1,
            max_rate=50,
            increment=2,
            test_duration_minutes=1,
            aggressive_testing=True
        )
    
    @pytest.fixture
    def rate_limit_tier_minute(self) -> RateLimitTier:
        """Тестовый tier для минутного окна"""
        return RateLimitTier(
            name="minute",
            window_seconds=60,
            start_rate=1,
            max_rate=1000,
            increment=10,
            test_duration_minutes=5
        )
    
    @pytest.mark.asyncio
    async def test_header_analyzer_extract_multiple_limits(self, sample_headers_with_limits):
        """Тест извлечения множественных лимитов из заголовков"""
        analyzer = HeaderAnalyzer()
        
        limits = analyzer.extract_rate_limits(sample_headers_with_limits)
        
        # Проверяем что найдены все уровни лимитов
        assert len(limits) >= 3  # minute, hour, day
        
        # Проверяем минутный лимит
        minute_limit = next((l for l in limits if l.window_seconds == 60), None)
        assert minute_limit is not None
        assert minute_limit.limit == 100
        assert minute_limit.remaining == 95
        
        # Проверяем часовой лимит
        hour_limit = next((l for l in limits if l.window_seconds == 3600), None)
        assert hour_limit is not None
        assert hour_limit.limit == 5000
        assert hour_limit.remaining == 4950
        
        # Проверяем дневной лимит
        day_limit = next((l for l in limits if l.window_seconds == 86400), None)
        assert day_limit is not None
        assert day_limit.limit == 100000
        assert day_limit.remaining == 99900
    
    @pytest.mark.asyncio
    async def test_header_analyzer_no_limits_found(self, sample_headers_no_limits):
        """Тест когда в заголовках нет информации о лимитах"""
        analyzer = HeaderAnalyzer()
        
        limits = analyzer.extract_rate_limits(sample_headers_no_limits)
        
        assert len(limits) == 0
    
    @pytest.mark.asyncio
    async def test_tier_tester_successful_detection(self, rate_limit_tier_10s):
        """Тест успешного определения лимита через тестирование"""
        tester = TierTester()
        
        # Мокаем HTTP запросы
        with aioresponses() as m:
            # Первые запросы успешные (200)
            for i in range(10):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True},
                    headers={"X-RateLimit-Remaining": str(50-i)}
                )
            
            # Запрос превышающий лимит (429)
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                payload={"error": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Limit": "10",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=10)).timestamp())),
                    "Retry-After": "10"
                }
            )
            
            result = await tester.test_tier(
                url="https://api.test.com/v1/test",
                tier=rate_limit_tier_10s,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            assert result.limit_found is True
            assert result.detected_limit is not None
            assert result.detected_limit.limit == 10
            assert result.detected_limit.window_seconds == 10
            assert result.requests_sent > 0
            assert result.error_rate < 1.0  # Не все запросы должны быть ошибочными
    
    @pytest.mark.asyncio
    async def test_tier_tester_no_limit_detected(self, rate_limit_tier_10s):
        """Тест когда лимит не обнаружен в течение тестового периода"""
        tester = TierTester()
        
        # Мокаем только успешные запросы
        with aioresponses() as m:
            # Все запросы успешные
            for i in range(100):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True},
                    headers={"X-RateLimit-Remaining": "999"}
                )
            
            # Ограничиваем время тестирования для ускорения теста
            tier_short = RateLimitTier(
                name="10_seconds",
                window_seconds=10,
                start_rate=1,
                max_rate=20,  # Небольшой максимум
                increment=5,
                test_duration_minutes=0.1  # 6 секунд
            )
            
            result = await tester.test_tier(
                url="https://api.test.com/v1/test",
                tier=tier_short,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            assert result.limit_found is False
            assert result.detected_limit is None
            assert result.requests_sent > 0
            assert result.error_rate == 0.0  # Все запросы успешные
    
    @pytest.mark.asyncio
    async def test_multi_tier_detector_header_analysis_first(self, sample_headers_with_limits):
        """Тест что MultiTierDetector сначала анализирует заголовки"""
        detector = MultiTierDetector()
        
        with aioresponses() as m:
            # Первый запрос для анализа заголовков
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                payload={"success": True},
                headers=sample_headers_with_limits
            )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            assert result.limits_found > 0
            assert result.minute_limit is not None
            assert result.hour_limit is not None
            assert result.day_limit is not None
            
            # Проверяем что самый строгий лимит определен правильно
            assert result.most_restrictive in ["minute", "hour", "day"]
            assert result.recommended_rate > 0
    
    @pytest.mark.asyncio
    async def test_multi_tier_detector_fallback_to_testing(self, sample_headers_no_limits):
        """Тест что MultiTierDetector переходит к тестированию если заголовки не содержат лимитов"""
        detector = MultiTierDetector()
        
        with aioresponses() as m:
            # Первый запрос без лимитов в заголовках
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                payload={"success": True},
                headers=sample_headers_no_limits
            )
            
            # Запросы для тестирования 10-секундного лимита
            for i in range(5):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True}
                )
            
            # Запрос превышающий лимит
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                payload={"error": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Limit": "5",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=10)).timestamp()))
                }
            )
            
            # Настраиваем только тестирование 10-секундного tier
            tiers_to_test = [
                RateLimitTier(
                    name="10_seconds",
                    window_seconds=10,
                    start_rate=1,
                    max_rate=10,
                    increment=1,
                    test_duration_minutes=0.1
                )
            ]
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                tiers_to_test=tiers_to_test
            )
            
            # Должен быть найден лимит через тестирование
            assert result.limits_found > 0
    
    @pytest.mark.asyncio
    async def test_endpoint_rotation_during_detection(self):
        """Тест ротации endpoints во время определения лимитов"""
        detector = MultiTierDetector()
        
        endpoints = ["/v1/test", "/v1/data", "/v1/info"]
        
        with aioresponses() as m:
            # Мокаем ответы для всех endpoints
            for endpoint in endpoints:
                for i in range(10):
                    m.get(
                        f"https://api.test.com{endpoint}",
                        status=200,
                        payload={"success": True, "endpoint": endpoint},
                        headers={"X-RateLimit-Remaining": str(100-i)}
                    )
            
            # Тестируем с ротацией endpoints
            result = await detector.detect_with_endpoint_rotation(
                base_url="https://api.test.com",
                endpoints=endpoints,
                headers={"User-Agent": "Mozilla/5.0"},
                rotation_interval=3
            )
            
            # Проверяем что использовались разные endpoints
            assert len(result.endpoints_tested) == len(endpoints)
            assert result.total_requests > len(endpoints)
    
    @pytest.mark.asyncio
    async def test_rate_limit_detection_with_retry_after(self):
        """Тест обработки заголовка Retry-After при превышении лимита"""
        tester = TierTester()
        
        with aioresponses() as m:
            # Успешные запросы
            for i in range(3):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True}
                )
            
            # Запрос с 429 и Retry-After
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                payload={"error": "Rate limit exceeded"},
                headers={
                    "Retry-After": "30",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=30)).timestamp()))
                }
            )
            
            tier = RateLimitTier(
                name="test",
                window_seconds=60,
                start_rate=1,
                max_rate=10,
                increment=1,
                test_duration_minutes=0.1
            )
            
            start_time = datetime.now()
            result = await tester.test_tier(
                url="https://api.test.com/v1/test",
                tier=tier,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            end_time = datetime.now()
            
            # Проверяем что лимит обнаружен
            assert result.limit_found is True
            assert result.detected_limit is not None
            
            # Проверяем что учтен Retry-After (но не ждем полные 30 секунд в тесте)
            assert result.retry_after_seconds == 30
    
    @pytest.mark.asyncio
    async def test_concurrent_tier_testing(self):
        """Тест параллельного тестирования нескольких tiers"""
        detector = MultiTierDetector()
        
        tiers = [
            RateLimitTier(
                name="10_seconds",
                window_seconds=10,
                start_rate=1,
                max_rate=5,
                increment=1,
                test_duration_minutes=0.05
            ),
            RateLimitTier(
                name="minute",
                window_seconds=60,
                start_rate=1,
                max_rate=10,
                increment=2,
                test_duration_minutes=0.05
            )
        ]
        
        with aioresponses() as m:
            # Мокаем ответы для обоих tiers
            for i in range(20):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True}
                )
            
            start_time = datetime.now()
            
            # Запускаем параллельное тестирование
            tasks = []
            for tier in tiers:
                task = asyncio.create_task(
                    TierTester().test_tier(
                        url="https://api.test.com/v1/test",
                        tier=tier,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = datetime.now()
            
            # Проверяем что тестирование выполнилось параллельно (быстрее чем последовательно)
            total_time = (end_time - start_time).total_seconds()
            assert total_time < 10  # Должно быть быстрее чем сумма времен тестирования
            
            # Проверяем результаты
            assert len(results) == 2
            for result in results:
                assert isinstance(result, TierTestResult)
                assert result.requests_sent > 0


@pytest.mark.integration
class TestRateLimitDetectionEdgeCases:
    """Тесты граничных случаев определения rate limits"""
    
    @pytest.mark.asyncio
    async def test_malformed_rate_limit_headers(self):
        """Тест обработки некорректных заголовков rate limit"""
        analyzer = HeaderAnalyzer()
        
        malformed_headers = {
            "X-RateLimit-Limit": "not-a-number",
            "X-RateLimit-Remaining": "-5",
            "X-RateLimit-Reset": "invalid-timestamp",
            "X-Rate-Limit-Limit-Minute": "",
            "X-Rate-Limit-Limit-Hour": "999999999999999999999"  # Слишком большое число
        }
        
        # Должен корректно обработать некорректные заголовки
        limits = analyzer.extract_rate_limits(malformed_headers)
        
        # Некорректные заголовки должны быть проигнорированы
        assert len(limits) == 0 or all(l.limit > 0 for l in limits)
    
    @pytest.mark.asyncio
    async def test_network_timeout_during_detection(self):
        """Тест обработки таймаутов сети во время определения лимитов"""
        tester = TierTester()
        
        with aioresponses() as m:
            # Мокаем таймаут
            m.get(
                "https://api.test.com/v1/test",
                exception=asyncio.TimeoutError("Request timeout")
            )
            
            tier = RateLimitTier(
                name="test",
                window_seconds=10,
                start_rate=1,
                max_rate=5,
                increment=1,
                test_duration_minutes=0.05
            )
            
            result = await tester.test_tier(
                url="https://api.test.com/v1/test",
                tier=tier,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            # Должен корректно обработать таймаут
            assert result.limit_found is False
            assert result.error_rate > 0
            assert "timeout" in result.error_details.lower()
    
    @pytest.mark.asyncio
    async def test_server_error_responses(self):
        """Тест обработки серверных ошибок (5xx) во время определения лимитов"""
        tester = TierTester()
        
        with aioresponses() as m:
            # Мокаем серверные ошибки
            m.get("https://api.test.com/v1/test", status=500, payload={"error": "Internal Server Error"})
            m.get("https://api.test.com/v1/test", status=502, payload={"error": "Bad Gateway"})
            m.get("https://api.test.com/v1/test", status=503, payload={"error": "Service Unavailable"})
            
            tier = RateLimitTier(
                name="test",
                window_seconds=10,
                start_rate=1,
                max_rate=5,
                increment=1,
                test_duration_minutes=0.05
            )
            
            result = await tester.test_tier(
                url="https://api.test.com/v1/test",
                tier=tier,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            # Серверные ошибки не должны считаться rate limit
            assert result.limit_found is False
            assert result.error_rate > 0
            assert result.server_errors > 0
    
    @pytest.mark.asyncio
    async def test_inconsistent_rate_limit_headers(self):
        """Тест обработки противоречивых заголовков rate limit"""
        analyzer = HeaderAnalyzer()
        
        inconsistent_headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "150",  # Больше чем лимит
            "X-Rate-Limit-Limit-Minute": "100",
            "X-Rate-Limit-Remaining-Minute": "50",
            "X-Rate-Limit-Limit-Hour": "50",  # Меньше чем минутный лимит
            "X-Rate-Limit-Remaining-Hour": "25"
        }
        
        limits = analyzer.extract_rate_limits(inconsistent_headers)
        
        # Должен корректно обработать противоречия
        for limit in limits:
            assert limit.remaining <= limit.limit  # Remaining не может быть больше лимита
            assert limit.limit > 0
            assert limit.remaining >= 0
