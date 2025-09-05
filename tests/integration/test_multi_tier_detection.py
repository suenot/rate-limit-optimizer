"""
Интеграционные тесты многоуровневого определения rate limits
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.detection import (
    MultiTierDetector,
    TierTester,
    HeaderAnalyzer
)
from rate_limit_optimizer.models import (
    RateLimit,
    RateLimitTier,
    MultiTierResult,
    TierTestResult,
    DetectionStrategy
)
from rate_limit_optimizer.strategies import (
    MultiTierRampStrategy,
    IntelligentProbingStrategy,
    HeaderAnalysisStrategy
)


class TestMultiTierDetectionIntegration:
    """Интеграционные тесты многоуровневого определения лимитов"""
    
    @pytest.fixture
    def multi_tier_config(self) -> List[RateLimitTier]:
        """Конфигурация для тестирования всех уровней лимитов"""
        return [
            RateLimitTier(
                name="10_seconds",
                window_seconds=10,
                start_rate=1,
                max_rate=50,
                increment=2,
                test_duration_minutes=0.1,  # Короткое время для тестов
                aggressive_testing=True
            ),
            RateLimitTier(
                name="minute",
                window_seconds=60,
                start_rate=1,
                max_rate=1000,
                increment=10,
                test_duration_minutes=0.2
            ),
            RateLimitTier(
                name="15_minutes",
                window_seconds=900,
                start_rate=10,
                max_rate=5000,
                increment=50,
                test_duration_minutes=0.3
            ),
            RateLimitTier(
                name="hour",
                window_seconds=3600,
                start_rate=50,
                max_rate=50000,
                increment=100,
                test_duration_minutes=0.4
            ),
            RateLimitTier(
                name="day",
                window_seconds=86400,
                start_rate=1000,
                max_rate=1000000,
                increment=1000,
                test_duration_minutes=0.5
            )
        ]
    
    @pytest.fixture
    def comprehensive_headers(self) -> Dict[str, str]:
        """Заголовки со всеми уровнями лимитов"""
        now = datetime.now()
        return {
            # 10-секундные лимиты
            "X-RateLimit-Limit-10s": "20",
            "X-RateLimit-Remaining-10s": "15",
            "X-RateLimit-Reset-10s": str(int((now + timedelta(seconds=5)).timestamp())),
            
            # Минутные лимиты
            "X-RateLimit-Limit-Minute": "100",
            "X-RateLimit-Remaining-Minute": "85",
            "X-RateLimit-Reset-Minute": str(int((now + timedelta(minutes=1)).timestamp())),
            
            # 15-минутные лимиты
            "X-RateLimit-Limit-15min": "1000",
            "X-RateLimit-Remaining-15min": "850",
            "X-RateLimit-Reset-15min": str(int((now + timedelta(minutes=15)).timestamp())),
            
            # Часовые лимиты
            "X-RateLimit-Limit-Hour": "5000",
            "X-RateLimit-Remaining-Hour": "4200",
            "X-RateLimit-Reset-Hour": str(int((now + timedelta(hours=1)).timestamp())),
            
            # Дневные лимиты
            "X-RateLimit-Limit-Day": "100000",
            "X-RateLimit-Remaining-Day": "95000",
            "X-RateLimit-Reset-Day": str(int((now + timedelta(days=1)).timestamp())),
            
            "Content-Type": "application/json"
        }
    
    @pytest.mark.asyncio
    async def test_multi_tier_ramp_strategy_complete_flow(self, multi_tier_config, comprehensive_headers):
        """Тест полного цикла Multi-Tier Ramp стратегии"""
        strategy = MultiTierRampStrategy(
            tier_order=["10_seconds", "minute", "15_minutes", "hour", "day"],
            stop_on_first_limit=False,  # Тестируем все уровни
            adaptive_increment=True
        )
        
        detector = MultiTierDetector(strategy=strategy)
        
        with aioresponses() as m:
            # Первый запрос для анализа заголовков
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                payload={"success": True},
                headers=comprehensive_headers
            )
            
            # Дополнительные запросы для верификации лимитов
            for i in range(50):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    payload={"success": True},
                    headers={
                        "X-RateLimit-Remaining-10s": str(max(0, 20-i)),
                        "X-RateLimit-Remaining-Minute": str(max(0, 100-i)),
                        "X-RateLimit-Remaining-Hour": str(max(0, 5000-i))
                    }
                )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                tiers_to_test=multi_tier_config
            )
            
            # Проверяем что найдены все уровни лимитов
            assert result.limits_found >= 4  # Минимум 4 уровня
            assert result.ten_second_limit is not None
            assert result.minute_limit is not None
            assert result.fifteen_minute_limit is not None
            assert result.hour_limit is not None
            assert result.day_limit is not None
            
            # Проверяем корректность лимитов
            assert result.ten_second_limit.limit == 20
            assert result.minute_limit.limit == 100
            assert result.hour_limit.limit == 5000
            assert result.day_limit.limit == 100000
            
            # Проверяем определение самого строгого лимита
            assert result.most_restrictive == "10_seconds"  # Самый короткий интервал
            assert result.recommended_rate <= 20  # Не больше самого строгого лимита
    
    @pytest.mark.asyncio
    async def test_intelligent_probing_with_discovered_limits(self, multi_tier_config):
        """Тест умного зондирования с учетом уже найденных лимитов"""
        strategy = IntelligentProbingStrategy(
            start_with_shortest_window=True,
            respect_discovered_limits=True,
            cross_tier_validation=True
        )
        
        detector = MultiTierDetector(strategy=strategy)
        
        with aioresponses() as m:
            # Первый запрос обнаруживает минутный лимит
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                headers={
                    "X-RateLimit-Limit-Minute": "60",
                    "X-RateLimit-Remaining-Minute": "55"
                }
            )
            
            # Тестирование 10-секундного лимита с учетом минутного
            for i in range(10):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={"X-RateLimit-Remaining-10s": str(max(0, 10-i))}
                )
            
            # Превышение 10-секундного лимита
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                headers={
                    "X-RateLimit-Limit-10s": "10",
                    "X-RateLimit-Reset-10s": str(int((datetime.now() + timedelta(seconds=10)).timestamp()))
                }
            )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                tiers_to_test=multi_tier_config[:2]  # Только 10s и minute
            )
            
            # Проверяем что найдены оба лимита
            assert result.ten_second_limit is not None
            assert result.minute_limit is not None
            
            # Проверяем что 10-секундный лимит учитывает минутный
            assert result.ten_second_limit.limit == 10
            assert result.minute_limit.limit == 60
            
            # Самый строгий должен быть 10-секундный (меньше requests/second)
            assert result.most_restrictive == "10_seconds"
    
    @pytest.mark.asyncio
    async def test_tier_testing_with_backoff_on_limits(self, multi_tier_config):
        """Тест тестирования с откатом при обнаружении лимитов"""
        detector = MultiTierDetector()
        
        with aioresponses() as m:
            # Успешные запросы до лимита
            for i in range(5):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={"X-RateLimit-Remaining": str(5-i)}
                )
            
            # Превышение лимита
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                headers={
                    "X-RateLimit-Limit": "5",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=10)).timestamp())),
                    "Retry-After": "10"
                }
            )
            
            # Запросы после отката
            for i in range(3):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={"X-RateLimit-Remaining": str(5-i)}
                )
            
            tier = multi_tier_config[0]  # 10_seconds tier
            tier.max_rate = 10  # Ограничиваем для быстрого тестирования
            
            result = await detector.test_single_tier(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                tier=tier,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            assert result.limit_found is True
            assert result.detected_limit.limit == 5
            assert result.backoff_triggered is True
            assert result.retry_after_seconds == 10
    
    @pytest.mark.asyncio
    async def test_cross_tier_validation(self, multi_tier_config):
        """Тест кросс-валидации между различными уровнями лимитов"""
        detector = MultiTierDetector()
        
        # Симулируем противоречивые лимиты
        contradictory_headers = {
            "X-RateLimit-Limit-10s": "100",      # 100 req/10s = 600 req/min
            "X-RateLimit-Limit-Minute": "300",   # 300 req/min - противоречие!
            "X-RateLimit-Limit-Hour": "10000"    # 10000 req/hour ≈ 167 req/min
        }
        
        with aioresponses() as m:
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                headers=contradictory_headers
            )
            
            # Дополнительные запросы для валидации
            for i in range(20):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={"X-RateLimit-Remaining": str(max(0, 50-i))}
                )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                tiers_to_test=multi_tier_config[:3],
                validate_consistency=True
            )
            
            # Проверяем что детектор выявил противоречия
            assert result.consistency_warnings is not None
            assert len(result.consistency_warnings) > 0
            
            # Проверяем что выбран наиболее консервативный лимит
            assert result.most_restrictive_validated is not None
    
    @pytest.mark.asyncio
    async def test_adaptive_increment_strategy(self, multi_tier_config):
        """Тест адаптивного увеличения частоты запросов"""
        detector = MultiTierDetector()
        
        with aioresponses() as m:
            # Успешные запросы с постепенным увеличением частоты
            request_count = 0
            for rate in [1, 2, 4, 8, 16, 32]:  # Экспоненциальное увеличение
                for _ in range(rate):
                    request_count += 1
                    m.get(
                        "https://api.test.com/v1/test",
                        status=200,
                        headers={"X-RateLimit-Remaining": str(max(0, 50-request_count))}
                    )
            
            # Превышение лимита на высокой частоте
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                headers={
                    "X-RateLimit-Limit": "50",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=10)).timestamp()))
                }
            )
            
            tier = RateLimitTier(
                name="adaptive_test",
                window_seconds=10,
                start_rate=1,
                max_rate=100,
                increment=2,
                test_duration_minutes=0.1,
                adaptive_increment=True
            )
            
            result = await detector.test_single_tier(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                tier=tier,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            assert result.limit_found is True
            assert result.detected_limit.limit == 50
            assert result.adaptive_increments_used > 0
            assert result.final_rate_when_limited >= 32  # Должен достичь высокой частоты
    
    @pytest.mark.asyncio
    async def test_parallel_tier_testing(self, multi_tier_config):
        """Тест параллельного тестирования нескольких уровней"""
        detector = MultiTierDetector()
        
        # Используем только первые 3 tier для ускорения теста
        test_tiers = multi_tier_config[:3]
        
        with aioresponses() as m:
            # Мокаем достаточно запросов для всех tiers
            for i in range(100):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={
                        "X-RateLimit-Remaining-10s": str(max(0, 20-i%20)),
                        "X-RateLimit-Remaining-Minute": str(max(0, 100-i%100)),
                        "X-RateLimit-Remaining-15min": str(max(0, 500-i%500))
                    }
                )
            
            start_time = datetime.now()
            
            # Запускаем параллельное тестирование
            result = await detector.test_tiers_parallel(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                tiers=test_tiers,
                headers={"User-Agent": "Mozilla/5.0"},
                max_concurrent=3
            )
            
            end_time = datetime.now()
            test_duration = (end_time - start_time).total_seconds()
            
            # Проверяем что тестирование выполнилось параллельно
            assert test_duration < 5  # Должно быть быстрее последовательного
            
            # Проверяем результаты
            assert len(result.tier_results) == 3
            assert result.total_requests > 0
            assert result.parallel_execution is True
    
    @pytest.mark.asyncio
    async def test_tier_dependency_resolution(self, multi_tier_config):
        """Тест разрешения зависимостей между уровнями лимитов"""
        detector = MultiTierDetector()
        
        # Создаем ситуацию где часовой лимит влияет на минутный
        with aioresponses() as m:
            # Заголовки показывают что часовой лимит почти исчерпан
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                headers={
                    "X-RateLimit-Limit-Hour": "1000",
                    "X-RateLimit-Remaining-Hour": "50",  # Осталось мало
                    "X-RateLimit-Limit-Minute": "100",
                    "X-RateLimit-Remaining-Minute": "80"
                }
            )
            
            # Дополнительные запросы
            for i in range(30):
                remaining_hour = max(0, 50-i)
                remaining_minute = max(0, 80-i%100)
                
                if remaining_hour == 0:
                    # Часовой лимит исчерпан
                    m.get(
                        "https://api.test.com/v1/test",
                        status=429,
                        headers={
                            "X-RateLimit-Limit-Hour": "1000",
                            "X-RateLimit-Remaining-Hour": "0",
                            "X-RateLimit-Reset-Hour": str(int((datetime.now() + timedelta(hours=1)).timestamp()))
                        }
                    )
                else:
                    m.get(
                        "https://api.test.com/v1/test",
                        status=200,
                        headers={
                            "X-RateLimit-Remaining-Hour": str(remaining_hour),
                            "X-RateLimit-Remaining-Minute": str(remaining_minute)
                        }
                    )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                tiers_to_test=[multi_tier_config[1], multi_tier_config[3]],  # minute и hour
                resolve_dependencies=True
            )
            
            # Проверяем что учтены зависимости
            assert result.minute_limit is not None
            assert result.hour_limit is not None
            
            # Эффективный минутный лимит должен быть ограничен часовым
            effective_minute_limit = min(result.minute_limit.limit, result.hour_limit.remaining)
            assert result.recommended_rate <= effective_minute_limit


@pytest.mark.integration
class TestMultiTierStrategies:
    """Тесты различных стратегий многоуровневого определения"""
    
    @pytest.mark.asyncio
    async def test_header_analysis_strategy_priority(self):
        """Тест приоритета Header Analysis стратегии"""
        strategy = HeaderAnalysisStrategy(
            trust_headers=True,
            verify_with_testing=False,  # Доверяем заголовкам без верификации
            safety_margin_percent=20
        )
        
        detector = MultiTierDetector(strategy=strategy)
        
        headers_with_all_limits = {
            "X-RateLimit-Limit-10s": "50",
            "X-RateLimit-Limit-Minute": "500",
            "X-RateLimit-Limit-Hour": "10000",
            "X-RateLimit-Limit-Day": "200000"
        }
        
        with aioresponses() as m:
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                headers=headers_with_all_limits
            )
            
            result = await detector.detect_all_rate_limits(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            # Все лимиты должны быть определены из заголовков
            assert result.detection_method == "headers"
            assert result.ten_second_limit.limit == 50
            assert result.minute_limit.limit == 500
            assert result.hour_limit.limit == 10000
            assert result.day_limit.limit == 200000
            
            # Проверяем применение safety margin
            assert result.recommended_rate <= 50 * 0.8  # 20% safety margin
    
    @pytest.mark.asyncio
    async def test_combined_strategy_fallback(self):
        """Тест комбинированной стратегии с fallback"""
        # Сначала пробуем заголовки, потом тестирование
        header_strategy = HeaderAnalysisStrategy(trust_headers=True)
        ramp_strategy = MultiTierRampStrategy(tier_order=["10_seconds", "minute"])
        
        detector = MultiTierDetector()
        
        # Заголовки содержат только частичную информацию
        partial_headers = {
            "X-RateLimit-Limit-Hour": "5000",  # Только часовой лимит
            "X-RateLimit-Remaining-Hour": "4500"
        }
        
        with aioresponses() as m:
            # Первый запрос с частичными заголовками
            m.get(
                "https://api.test.com/v1/test",
                status=200,
                headers=partial_headers
            )
            
            # Запросы для тестирования недостающих лимитов
            for i in range(10):
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={"X-RateLimit-Remaining": str(max(0, 20-i))}
                )
            
            # Превышение 10-секундного лимита
            m.get(
                "https://api.test.com/v1/test",
                status=429,
                headers={
                    "X-RateLimit-Limit": "20",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=10)).timestamp()))
                }
            )
            
            result = await detector.detect_with_fallback_strategies(
                base_url="https://api.test.com",
                endpoint="/v1/test",
                headers={"User-Agent": "Mozilla/5.0"},
                strategies=[header_strategy, ramp_strategy]
            )
            
            # Должны быть найдены лимиты из обеих стратегий
            assert result.hour_limit is not None  # Из заголовков
            assert result.ten_second_limit is not None  # Из тестирования
            assert result.detection_methods == ["headers", "testing"]
    
    @pytest.mark.asyncio
    async def test_strategy_performance_comparison(self):
        """Тест сравнения производительности различных стратегий"""
        strategies = [
            ("header_analysis", HeaderAnalysisStrategy()),
            ("multi_tier_ramp", MultiTierRampStrategy()),
            ("intelligent_probing", IntelligentProbingStrategy())
        ]
        
        performance_results = {}
        
        for strategy_name, strategy in strategies:
            detector = MultiTierDetector(strategy=strategy)
            
            with aioresponses() as m:
                # Мокаем одинаковые условия для всех стратегий
                m.get(
                    "https://api.test.com/v1/test",
                    status=200,
                    headers={
                        "X-RateLimit-Limit-Minute": "100",
                        "X-RateLimit-Remaining-Minute": "80"
                    }
                )
                
                for i in range(20):
                    m.get(
                        "https://api.test.com/v1/test",
                        status=200,
                        headers={"X-RateLimit-Remaining": str(max(0, 50-i))}
                    )
                
                start_time = datetime.now()
                
                result = await detector.detect_all_rate_limits(
                    base_url="https://api.test.com",
                    endpoint="/v1/test",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                performance_results[strategy_name] = {
                    "duration": duration,
                    "requests_sent": result.total_requests,
                    "limits_found": result.limits_found,
                    "accuracy": result.confidence_score
                }
        
        # Проверяем что header_analysis самая быстрая
        assert performance_results["header_analysis"]["duration"] <= \
               performance_results["multi_tier_ramp"]["duration"]
        
        # Проверяем что все стратегии нашли лимиты
        for strategy_name, results in performance_results.items():
            assert results["limits_found"] > 0
