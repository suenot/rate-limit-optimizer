"""
Интеграционные тесты для AI рекомендаций через OpenRouter API
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import aiohttp
from aioresponses import aioresponses

from rate_limit_optimizer.ai import (
    AIRecommender,
    OpenRouterClient,
    RecommendationGenerator,
    PromptBuilder
)
from rate_limit_optimizer.models import (
    MultiTierResult,
    RateLimit,
    AIRecommendations,
    RecommendationAnalysis,
    APIContext
)


class TestAIIntegrationWithOpenRouter:
    """Интеграционные тесты AI рекомендаций через OpenRouter"""
    
    @pytest.fixture
    def sample_detection_results(self) -> MultiTierResult:
        """Пример результатов определения лимитов для AI анализа"""
        return MultiTierResult(
            timestamp=datetime.now(),
            base_url="https://api.upbit.com",
            endpoint="/v1/market/all",
            ten_second_limit=RateLimit(
                limit=20,
                remaining=15,
                reset_time=datetime.now() + timedelta(seconds=10),
                window_seconds=10,
                detected_via="testing"
            ),
            minute_limit=RateLimit(
                limit=100,
                remaining=85,
                reset_time=datetime.now() + timedelta(minutes=1),
                window_seconds=60,
                detected_via="headers"
            ),
            hour_limit=RateLimit(
                limit=5000,
                remaining=4200,
                reset_time=datetime.now() + timedelta(hours=1),
                window_seconds=3600,
                detected_via="headers"
            ),
            day_limit=RateLimit(
                limit=100000,
                remaining=95000,
                reset_time=datetime.now() + timedelta(days=1),
                window_seconds=86400,
                detected_via="headers"
            ),
            most_restrictive="10_seconds",
            recommended_rate=18,
            limits_found=4,
            total_requests=45,
            test_duration_seconds=120,
            headers_found={
                "X-RateLimit-Limit-Minute": "100",
                "X-RateLimit-Limit-Hour": "5000",
                "X-RateLimit-Limit-Day": "100000"
            },
            error_patterns=["429 after 20 requests in 10 seconds"],
            confidence_score=0.95
        )
    
    @pytest.fixture
    def api_context(self) -> APIContext:
        """Контекст API для AI анализа"""
        return APIContext(
            api_name="Upbit API",
            base_url="https://api.upbit.com",
            api_type="REST",
            authentication_type="none",
            primary_use_case="cryptocurrency_data",
            business_criticality="high",
            expected_load="medium"
        )
    
    @pytest.fixture
    def mock_openrouter_response(self) -> Dict[str, Any]:
        """Мок ответа от OpenRouter API"""
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "optimal_usage_strategy": "10-секундный лимит (18 req/10s) является самым строгим. Рекомендуется использовать частоту 15 req/10s с буферизацией запросов для обработки пиковых нагрузок.",
                            "implementation_patterns": [
                                "Реализуйте token bucket алгоритм с размером bucket = 20 токенов",
                                "Используйте экспоненциальный backoff: 1s, 2s, 4s, 8s при получении 429",
                                "Добавьте jitter (±10%) к интервалам между запросами",
                                "Мониторьте заголовки X-RateLimit-Remaining для предупреждения лимитов"
                            ],
                            "error_handling_advice": [
                                "При 429 ошибке ждите время из заголовка Retry-After",
                                "Реализуйте circuit breaker после 3 последовательных 429 ошибок",
                                "Логируйте все rate limit события для анализа паттернов",
                                "Используйте graceful degradation при достижении лимитов"
                            ],
                            "monitoring_suggestions": [
                                "Отслеживайте метрику requests_per_10_seconds в реальном времени",
                                "Настройте алерты при превышении 90% от лимита (18 req/10s)",
                                "Мониторьте время сброса лимитов для планирования нагрузки",
                                "Ведите статистику успешности запросов по временным окнам"
                            ],
                            "scaling_recommendations": [
                                "Для масштабирования используйте несколько API ключей с ротацией",
                                "Рассмотрите кэширование ответов на 30-60 секунд для снижения нагрузки",
                                "Реализуйте приоритизацию запросов: критичные vs некритичные",
                                "При росте нагрузки рассмотрите переход на более высокий тарифный план API"
                            ],
                            "confidence_score": 0.92,
                            "risk_assessment": "LOW - Лимиты четко определены, API предоставляет полные заголовки",
                            "estimated_cost_impact": "При соблюдении рекомендаций ожидается 0% ошибок 429 и оптимальное использование квоты"
                        })
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
    
    @pytest.mark.asyncio
    async def test_openrouter_client_successful_request(self, mock_openrouter_response):
        """Тест успешного запроса к OpenRouter API"""
        client = OpenRouterClient(api_key="test-api-key")
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_response
            )
            
            response = await client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[
                    {"role": "system", "content": "Ты эксперт по оптимизации API rate limits."},
                    {"role": "user", "content": "Проанализируй результаты тестирования rate limits"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            assert response["model"] == "anthropic/claude-3.5-sonnet"
            assert len(response["choices"]) == 1
            assert response["choices"][0]["message"]["role"] == "assistant"
            
            # Проверяем что контент является валидным JSON
            content = response["choices"][0]["message"]["content"]
            parsed_content = json.loads(content)
            assert "optimal_usage_strategy" in parsed_content
            assert "implementation_patterns" in parsed_content
    
    @pytest.mark.asyncio
    async def test_openrouter_client_authentication_error(self):
        """Тест обработки ошибки аутентификации OpenRouter"""
        client = OpenRouterClient(api_key="invalid-api-key")
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=401,
                payload={"error": {"message": "Invalid API key", "type": "authentication_error"}}
            )
            
            with pytest.raises(Exception) as exc_info:
                await client.chat_completion(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[{"role": "user", "content": "test"}]
                )
            
            assert "authentication" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_openrouter_client_rate_limit_error(self):
        """Тест обработки rate limit ошибки от OpenRouter"""
        client = OpenRouterClient(api_key="test-api-key")
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=429,
                payload={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
                headers={"Retry-After": "60"}
            )
            
            with pytest.raises(Exception) as exc_info:
                await client.chat_completion(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[{"role": "user", "content": "test"}]
                )
            
            assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_ai_recommender_full_flow(self, sample_detection_results, api_context, mock_openrouter_response):
        """Тест полного цикла генерации AI рекомендаций"""
        recommender = AIRecommender(
            openrouter_api_key="test-api-key",
            model="anthropic/claude-3.5-sonnet",
            temperature=0.1,
            max_tokens=2000
        )
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_response
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Проверяем структуру рекомендаций
            assert isinstance(recommendations, AIRecommendations)
            assert recommendations.generated_by == "anthropic/claude-3.5-sonnet"
            assert recommendations.confidence_score >= 0.9
            
            # Проверяем анализ
            analysis = recommendations.analysis
            assert analysis.optimal_usage_strategy is not None
            assert len(analysis.implementation_patterns) >= 3
            assert len(analysis.error_handling_advice) >= 3
            assert len(analysis.monitoring_suggestions) >= 3
            assert len(analysis.scaling_recommendations) >= 3
            
            # Проверяем что рекомендации учитывают самый строгий лимит
            assert "10" in analysis.optimal_usage_strategy  # Должен упоминать 10-секундный лимит
            assert "18" in analysis.optimal_usage_strategy or "15" in analysis.optimal_usage_strategy
    
    @pytest.mark.asyncio
    async def test_prompt_builder_comprehensive_context(self, sample_detection_results, api_context):
        """Тест построения комплексного промпта для AI"""
        builder = PromptBuilder()
        
        prompt = builder.build_analysis_prompt(
            results=sample_detection_results,
            context=api_context,
            include_technical_details=True,
            include_business_context=True
        )
        
        # Проверяем что промпт содержит все необходимые элементы
        assert api_context.api_name in prompt
        assert api_context.base_url in prompt
        assert str(sample_detection_results.ten_second_limit.limit) in prompt
        assert str(sample_detection_results.minute_limit.limit) in prompt
        assert sample_detection_results.most_restrictive in prompt
        
        # Проверяем технические детали
        assert "заголовки" in prompt.lower()
        assert "429" in prompt
        assert str(sample_detection_results.confidence_score) in prompt
        
        # Проверяем бизнес-контекст
        assert api_context.business_criticality in prompt
        assert api_context.expected_load in prompt
    
    @pytest.mark.asyncio
    async def test_ai_recommendations_caching(self, sample_detection_results, api_context, mock_openrouter_response):
        """Тест кэширования AI рекомендаций"""
        recommender = AIRecommender(
            openrouter_api_key="test-api-key",
            cache_recommendations=True,
            cache_ttl_hours=24
        )
        
        with aioresponses() as m:
            # Первый запрос к API
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_response
            )
            
            # Первый вызов - должен обратиться к API
            recommendations1 = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Второй вызов с теми же данными - должен использовать кэш
            recommendations2 = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Проверяем что результаты идентичны (из кэша)
            assert recommendations1.analysis.optimal_usage_strategy == recommendations2.analysis.optimal_usage_strategy
            assert recommendations1.timestamp == recommendations2.timestamp  # Должны быть из кэша
    
    @pytest.mark.asyncio
    async def test_ai_recommendations_fallback_on_error(self, sample_detection_results, api_context):
        """Тест fallback рекомендаций при ошибке AI API"""
        recommender = AIRecommender(
            openrouter_api_key="test-api-key",
            fallback_on_error=True
        )
        
        with aioresponses() as m:
            # Мокаем ошибку API
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=500,
                payload={"error": "Internal server error"}
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Должны получить fallback рекомендации
            assert recommendations is not None
            assert recommendations.generated_by == "fallback_generator"
            assert recommendations.analysis.optimal_usage_strategy is not None
            
            # Fallback должен содержать базовые рекомендации
            assert "лимит" in recommendations.analysis.optimal_usage_strategy.lower()
            assert len(recommendations.analysis.implementation_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_recommendation_generator_multiple_models(self, sample_detection_results, api_context):
        """Тест генерации рекомендаций с несколькими AI моделями"""
        models = [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4-turbo",
            "meta-llama/llama-3.1-70b-instruct"
        ]
        
        generator = RecommendationGenerator(
            openrouter_api_key="test-api-key",
            models=models,
            consensus_threshold=0.7  # Требуем согласие 70% моделей
        )
        
        # Мокаем ответы от разных моделей
        responses = []
        for i, model in enumerate(models):
            response = {
                "model": model,
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "optimal_usage_strategy": f"Стратегия от модели {i+1}: используйте {15+i} req/10s",
                            "implementation_patterns": [f"Паттерн {i+1}: token bucket"],
                            "confidence_score": 0.8 + i*0.05
                        })
                    }
                }]
            }
            responses.append(response)
        
        with aioresponses() as m:
            for response in responses:
                m.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=response
                )
            
            consensus_recommendations = await generator.generate_consensus_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Проверяем что получили консенсус
            assert consensus_recommendations is not None
            assert len(consensus_recommendations.model_responses) == len(models)
            assert consensus_recommendations.consensus_reached is True
            
            # Проверяем что финальные рекомендации учитывают все модели
            final_strategy = consensus_recommendations.final_recommendations.optimal_usage_strategy
            assert "req/10s" in final_strategy
    
    @pytest.mark.asyncio
    async def test_ai_recommendations_with_environment_variables(self, sample_detection_results, api_context):
        """Тест использования переменных окружения для AI настроек"""
        with patch.dict(os.environ, {
            'OPENROUTER_API_KEY': 'env-test-key',
            'AI_MODEL': 'anthropic/claude-3.5-sonnet',
            'AI_TEMPERATURE': '0.2',
            'AI_MAX_TOKENS': '1500'
        }):
            recommender = AIRecommender.from_environment()
            
            # Проверяем что настройки загрузились из переменных окружения
            assert recommender.api_key == 'env-test-key'
            assert recommender.model == 'anthropic/claude-3.5-sonnet'
            assert recommender.temperature == 0.2
            assert recommender.max_tokens == 1500


@pytest.mark.integration
class TestAIIntegrationEdgeCases:
    """Тесты граничных случаев AI интеграции"""
    
    @pytest.mark.asyncio
    async def test_ai_with_incomplete_detection_results(self, api_context):
        """Тест AI рекомендаций с неполными результатами определения лимитов"""
        incomplete_results = MultiTierResult(
            timestamp=datetime.now(),
            base_url="https://api.test.com",
            endpoint="/v1/test",
            minute_limit=RateLimit(
                limit=100,
                remaining=50,
                reset_time=datetime.now() + timedelta(minutes=1),
                window_seconds=60,
                detected_via="headers"
            ),
            # Остальные лимиты не определены
            ten_second_limit=None,
            hour_limit=None,
            day_limit=None,
            most_restrictive="minute",
            recommended_rate=80,
            limits_found=1,
            total_requests=5,
            confidence_score=0.6  # Низкая уверенность
        )
        
        recommender = AIRecommender(openrouter_api_key="test-key")
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "optimal_usage_strategy": "Найден только минутный лимит. Рекомендуется консервативный подход с дополнительным тестированием.",
                        "implementation_patterns": ["Используйте rate limiting с запасом 50%"],
                        "error_handling_advice": ["Мониторьте ответы для обнаружения дополнительных лимитов"],
                        "monitoring_suggestions": ["Отслеживайте паттерны ошибок для выявления скрытых лимитов"],
                        "scaling_recommendations": ["Проведите дополнительное тестирование перед масштабированием"],
                        "confidence_score": 0.5,
                        "risk_assessment": "MEDIUM - Неполная информация о лимитах"
                    })
                }
            }]
        }
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_response
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=incomplete_results,
                api_context=api_context
            )
            
            # AI должен учесть неполноту данных
            assert "консервативный" in recommendations.analysis.optimal_usage_strategy.lower()
            assert recommendations.risk_assessment == "MEDIUM - Неполная информация о лимитах"
            assert recommendations.confidence_score <= 0.6
    
    @pytest.mark.asyncio
    async def test_ai_with_contradictory_limits(self, api_context):
        """Тест AI рекомендаций с противоречивыми лимитами"""
        contradictory_results = MultiTierResult(
            timestamp=datetime.now(),
            base_url="https://api.test.com",
            endpoint="/v1/test",
            ten_second_limit=RateLimit(limit=100, window_seconds=10, detected_via="testing"),  # 600 req/min
            minute_limit=RateLimit(limit=300, window_seconds=60, detected_via="headers"),      # 300 req/min - противоречие!
            hour_limit=RateLimit(limit=10000, window_seconds=3600, detected_via="headers"),   # ~167 req/min
            most_restrictive="hour",  # Неправильно определен
            recommended_rate=150,     # Противоречивая рекомендация
            limits_found=3,
            consistency_warnings=["10-second limit extrapolates to 600 req/min but minute limit is 300 req/min"],
            confidence_score=0.3  # Низкая уверенность из-за противоречий
        )
        
        recommender = AIRecommender(openrouter_api_key="test-key")
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "optimal_usage_strategy": "Обнаружены противоречивые лимиты. Рекомендуется использовать самый строгий лимит (167 req/min из часового лимита) до проведения дополнительной верификации.",
                        "implementation_patterns": [
                            "Используйте самый консервативный лимит из всех обнаруженных",
                            "Реализуйте мониторинг для выявления истинных лимитов"
                        ],
                        "error_handling_advice": [
                            "Проведите дополнительное тестирование для разрешения противоречий",
                            "Мониторьте заголовки ответов для уточнения лимитов"
                        ],
                        "monitoring_suggestions": [
                            "Ведите детальную статистику по временным окнам",
                            "Настройте алерты на несоответствия в заголовках"
                        ],
                        "scaling_recommendations": [
                            "Не масштабируйте до разрешения противоречий в лимитах"
                        ],
                        "confidence_score": 0.4,
                        "risk_assessment": "HIGH - Противоречивые данные о лимитах"
                    })
                }
            }]
        }
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_response
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=contradictory_results,
                api_context=api_context
            )
            
            # AI должен выявить и обработать противоречия
            assert "противоречив" in recommendations.analysis.optimal_usage_strategy.lower()
            assert "консервативный" in recommendations.analysis.optimal_usage_strategy.lower()
            assert recommendations.risk_assessment == "HIGH - Противоречивые данные о лимитах"
            assert recommendations.confidence_score <= 0.5
    
    @pytest.mark.asyncio
    async def test_ai_timeout_handling(self, sample_detection_results, api_context):
        """Тест обработки таймаутов при обращении к AI API"""
        recommender = AIRecommender(
            openrouter_api_key="test-key",
            request_timeout=1.0,  # Короткий таймаут
            fallback_on_error=True
        )
        
        with aioresponses() as m:
            # Мокаем таймаут
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                exception=asyncio.TimeoutError("Request timeout")
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Должны получить fallback рекомендации
            assert recommendations is not None
            assert recommendations.generated_by == "fallback_generator"
            assert "таймаут" in recommendations.error_details.lower() or "timeout" in recommendations.error_details.lower()
    
    @pytest.mark.asyncio
    async def test_ai_malformed_response_handling(self, sample_detection_results, api_context):
        """Тест обработки некорректного ответа от AI API"""
        recommender = AIRecommender(
            openrouter_api_key="test-key",
            fallback_on_error=True
        )
        
        malformed_response = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON for recommendations"  # Некорректный JSON
                }
            }]
        }
        
        with aioresponses() as m:
            m.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=malformed_response
            )
            
            recommendations = await recommender.generate_recommendations(
                test_results=sample_detection_results,
                api_context=api_context
            )
            
            # Должны получить fallback рекомендации из-за некорректного ответа
            assert recommendations is not None
            assert recommendations.generated_by == "fallback_generator"
            assert "parsing" in recommendations.error_details.lower() or "json" in recommendations.error_details.lower()
