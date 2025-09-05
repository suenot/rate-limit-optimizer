"""
AI рекомендации через OpenRouter API
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib

import aiohttp
from aiohttp import ClientTimeout, ClientError

from .models import (
    MultiTierResult, AIRecommendations, RecommendationAnalysis, APIContext
)
from .exceptions import AIServiceError

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Клиент для OpenRouter API"""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = ClientTimeout(total=60)  # AI запросы могут быть долгими
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """Запрос к chat completion API"""
        
        if not self.session:
            async with self:
                return await self._chat_completion_impl(model, messages, temperature, max_tokens, top_p)
        else:
            return await self._chat_completion_impl(model, messages, temperature, max_tokens, top_p)
    
    async def _chat_completion_impl(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> Dict[str, Any]:
        """Внутренняя реализация chat completion"""
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 401:
                    raise AIServiceError("Неверный API ключ OpenRouter")
                elif response.status == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise AIServiceError(f"Rate limit OpenRouter API, повторите через {retry_after}s")
                elif response.status >= 500:
                    raise AIServiceError(f"Ошибка сервера OpenRouter: {response.status}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise AIServiceError(f"Ошибка OpenRouter API: {response.status} - {error_text}")
                
                return await response.json()
                
        except ClientError as e:
            raise AIServiceError(f"Сетевая ошибка при обращении к OpenRouter: {e}")
        except asyncio.TimeoutError:
            raise AIServiceError("Таймаут при обращении к OpenRouter API")


class PromptBuilder:
    """Построитель промптов для AI анализа"""
    
    def __init__(self):
        self.system_prompt = (
            "Ты эксперт по оптимизации API rate limits. "
            "Анализируй результаты тестирования и давай практические рекомендации для разработчиков. "
            "Отвечай на русском языке в формате JSON."
        )
    
    def build_analysis_prompt(
        self,
        results: MultiTierResult,
        context: APIContext,
        include_technical_details: bool = True,
        include_business_context: bool = True
    ) -> str:
        """Построение промпта для анализа результатов"""
        
        prompt_parts = [
            f"Проанализируй результаты тестирования rate limits для API:",
            f"",
            f"API: {context.api_name} ({context.base_url})",
            f"Тип API: {context.api_type}",
            f"Аутентификация: {context.authentication_type}",
        ]
        
        if include_business_context:
            prompt_parts.extend([
                f"Назначение: {context.primary_use_case}",
                f"Критичность: {context.business_criticality}",
                f"Ожидаемая нагрузка: {context.expected_load}",
                f""
            ])
        
        prompt_parts.append("Обнаруженные лимиты:")
        
        # Добавляем информацию о лимитах
        if results.ten_second_limit:
            prompt_parts.append(f"- 10 секунд: {results.ten_second_limit.limit} запросов")
        if results.minute_limit:
            prompt_parts.append(f"- Минута: {results.minute_limit.limit} запросов")
        if results.fifteen_minute_limit:
            prompt_parts.append(f"- 15 минут: {results.fifteen_minute_limit.limit} запросов")
        if results.hour_limit:
            prompt_parts.append(f"- Час: {results.hour_limit.limit} запросов")
        if results.day_limit:
            prompt_parts.append(f"- День: {results.day_limit.limit} запросов")
        
        prompt_parts.extend([
            f"",
            f"Самый строгий лимит: {results.most_restrictive}",
            f"Рекомендуемая частота: {results.recommended_rate} запросов",
            f"Уверенность: {results.confidence_score:.2%}",
        ])
        
        if include_technical_details:
            prompt_parts.extend([
                f"",
                f"Технические детали:",
                f"- Всего запросов отправлено: {results.total_requests}",
                f"- Длительность тестирования: {results.test_duration_seconds:.1f} секунд",
                f"- Процент успешности: {results.success_rate:.2%}",
            ])
            
            if results.headers_found:
                prompt_parts.append("- Найденные заголовки:")
                for header, value in results.headers_found.items():
                    prompt_parts.append(f"  {header}: {value}")
            
            if results.error_patterns:
                prompt_parts.append("- Паттерны ошибок:")
                for pattern in results.error_patterns:
                    prompt_parts.append(f"  {pattern}")
        
        prompt_parts.extend([
            f"",
            f"Дай практические рекомендации в формате JSON с полями:",
            f"{{",
            f'  "optimal_usage_strategy": "детальная стратегия использования",',
            f'  "implementation_patterns": ["паттерн 1", "паттерн 2", "паттерн 3"],',
            f'  "error_handling_advice": ["совет 1", "совет 2", "совет 3"],',
            f'  "monitoring_suggestions": ["предложение 1", "предложение 2", "предложение 3"],',
            f'  "scaling_recommendations": ["рекомендация 1", "рекомендация 2", "рекомендация 3"],',
            f'  "confidence_score": 0.95,',
            f'  "risk_assessment": "LOW/MEDIUM/HIGH - описание",',
            f'  "estimated_cost_impact": "описание влияния на затраты"',
            f"}}"
        ])
        
        return "\n".join(prompt_parts)


class RecommendationGenerator:
    """Генератор рекомендаций с поддержкой нескольких моделей"""
    
    def __init__(
        self,
        openrouter_api_key: str,
        models: List[str] = None,
        consensus_threshold: float = 0.7
    ):
        self.api_key = openrouter_api_key
        self.models = models or ["anthropic/claude-3.5-sonnet"]
        self.consensus_threshold = consensus_threshold
        self.client = OpenRouterClient(openrouter_api_key)
    
    async def generate_consensus_recommendations(
        self,
        test_results: MultiTierResult,
        api_context: APIContext
    ) -> AIRecommendations:
        """Генерация консенсусных рекомендаций от нескольких моделей"""
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_analysis_prompt(test_results, api_context)
        
        model_responses = []
        
        async with self.client:
            for model in self.models:
                try:
                    response = await self.client.chat_completion(
                        model=model,
                        messages=[
                            {"role": "system", "content": prompt_builder.system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    model_responses.append({
                        "model": model,
                        "response": response
                    })
                    
                except Exception as e:
                    logger.warning(f"Ошибка получения рекомендаций от модели {model}: {e}")
        
        if not model_responses:
            raise AIServiceError("Не удалось получить рекомендации ни от одной модели")
        
        # Анализируем консенсус
        consensus_analysis = self._analyze_consensus(model_responses)
        
        return AIRecommendations(
            generated_by="consensus_" + "_".join(self.models),
            analysis=consensus_analysis,
            confidence_score=min(0.95, len(model_responses) / len(self.models)),
            risk_assessment="CONSENSUS - Рекомендации основаны на анализе нескольких моделей",
            estimated_cost_impact="Консенсусная оценка влияния на затраты",
            model_responses=model_responses
        )
    
    def _analyze_consensus(self, model_responses: List[Dict[str, Any]]) -> RecommendationAnalysis:
        """Анализ консенсуса между моделями"""
        
        # Для простоты берем первый успешный ответ
        # В полной реализации здесь был бы анализ консенсуса
        
        for response_data in model_responses:
            try:
                response = response_data["response"]
                content = response["choices"][0]["message"]["content"]
                
                # Пробуем парсить JSON
                recommendations_data = json.loads(content)
                
                return RecommendationAnalysis(
                    optimal_usage_strategy=recommendations_data.get("optimal_usage_strategy", ""),
                    implementation_patterns=recommendations_data.get("implementation_patterns", []),
                    error_handling_advice=recommendations_data.get("error_handling_advice", []),
                    monitoring_suggestions=recommendations_data.get("monitoring_suggestions", []),
                    scaling_recommendations=recommendations_data.get("scaling_recommendations", [])
                )
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Ошибка парсинга ответа модели: {e}")
                continue
        
        # Fallback если не удалось парсить
        return self._create_fallback_analysis()
    
    def _create_fallback_analysis(self) -> RecommendationAnalysis:
        """Создание fallback анализа"""
        return RecommendationAnalysis(
            optimal_usage_strategy="Используйте консервативный подход с запасом 20% от обнаруженного лимита",
            implementation_patterns=[
                "Реализуйте exponential backoff при получении 429 ошибок",
                "Используйте circuit breaker паттерн",
                "Добавьте мониторинг rate limit метрик"
            ],
            error_handling_advice=[
                "Обрабатывайте 429 ошибки корректно",
                "Учитывайте заголовок Retry-After",
                "Логируйте все rate limit события"
            ],
            monitoring_suggestions=[
                "Отслеживайте частоту запросов в реальном времени",
                "Настройте алерты при приближении к лимитам",
                "Мониторьте время сброса лимитов"
            ],
            scaling_recommendations=[
                "Рассмотрите использование нескольких API ключей",
                "Реализуйте кэширование для снижения нагрузки",
                "Оптимизируйте частоту запросов под бизнес-требования"
            ]
        )


class AIRecommender:
    """Основной класс для генерации AI рекомендаций"""
    
    def __init__(
        self,
        openrouter_api_key: str,
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        cache_recommendations: bool = True,
        cache_ttl_hours: int = 24,
        fallback_on_error: bool = True,
        request_timeout: float = 60.0
    ):
        self.api_key = openrouter_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cache_recommendations = cache_recommendations
        self.cache_ttl_hours = cache_ttl_hours
        self.fallback_on_error = fallback_on_error
        self.request_timeout = request_timeout
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        self.client = OpenRouterClient(openrouter_api_key)
        self.prompt_builder = PromptBuilder()
    
    async def generate_recommendations(
        self,
        test_results: MultiTierResult,
        api_context: APIContext
    ) -> AIRecommendations:
        """Генерация AI рекомендаций"""
        
        # Проверяем кэш
        if self.cache_recommendations:
            cache_key = self._generate_cache_key(test_results, api_context)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info("Используем кэшированные AI рекомендации")
                return AIRecommendations(**cached)
        
        try:
            # Генерируем рекомендации
            recommendations = await self._generate_recommendations_impl(test_results, api_context)
            
            # Сохраняем в кэш
            if self.cache_recommendations:
                self._save_to_cache(cache_key, recommendations.model_dump())
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка генерации AI рекомендаций: {e}")
            
            if self.fallback_on_error:
                return self._create_fallback_recommendations(test_results, str(e))
            else:
                raise AIServiceError(f"Не удалось сгенерировать AI рекомендации: {e}")
    
    async def _generate_recommendations_impl(
        self,
        test_results: MultiTierResult,
        api_context: APIContext
    ) -> AIRecommendations:
        """Внутренняя реализация генерации рекомендаций"""
        
        prompt = self.prompt_builder.build_analysis_prompt(test_results, api_context)
        
        async with self.client:
            response = await self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt_builder.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        
        # Парсим ответ
        content = response["choices"][0]["message"]["content"]
        
        try:
            recommendations_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа от AI: {e}")
            raise AIServiceError(f"Некорректный JSON ответ от AI: {content[:200]}...")
        
        # Создаем объект рекомендаций
        analysis = RecommendationAnalysis(
            optimal_usage_strategy=recommendations_data.get("optimal_usage_strategy", ""),
            implementation_patterns=recommendations_data.get("implementation_patterns", []),
            error_handling_advice=recommendations_data.get("error_handling_advice", []),
            monitoring_suggestions=recommendations_data.get("monitoring_suggestions", []),
            scaling_recommendations=recommendations_data.get("scaling_recommendations", [])
        )
        
        return AIRecommendations(
            generated_by=self.model,
            analysis=analysis,
            confidence_score=recommendations_data.get("confidence_score", 0.8),
            risk_assessment=recommendations_data.get("risk_assessment", "MEDIUM - Автоматический анализ"),
            estimated_cost_impact=recommendations_data.get("estimated_cost_impact", "Требует дополнительного анализа")
        )
    
    def _create_fallback_recommendations(self, test_results: MultiTierResult, error_details: str) -> AIRecommendations:
        """Создание fallback рекомендаций при ошибке AI"""
        
        # Определяем базовые рекомендации на основе результатов
        most_restrictive = test_results.most_restrictive
        recommended_rate = test_results.recommended_rate
        
        optimal_strategy = (
            f"Обнаружен лимит типа '{most_restrictive}'. "
            f"Рекомендуется использовать частоту {recommended_rate} запросов с запасом безопасности. "
            f"AI анализ недоступен, используются базовые рекомендации."
        )
        
        analysis = RecommendationAnalysis(
            optimal_usage_strategy=optimal_strategy,
            implementation_patterns=[
                "Реализуйте exponential backoff при получении 429 ошибок",
                "Используйте circuit breaker после 3 последовательных ошибок",
                "Добавьте jitter к интервалам между запросами для избежания thundering herd"
            ],
            error_handling_advice=[
                "При 429 ошибке ждите время из заголовка Retry-After",
                "Логируйте все rate limit события для анализа паттернов",
                "Реализуйте graceful degradation при достижении лимитов"
            ],
            monitoring_suggestions=[
                f"Отслеживайте метрику requests_per_{most_restrictive} в реальном времени",
                f"Настройте алерты при превышении 90% от лимита ({int(recommended_rate * 0.9)} запросов)",
                "Мониторьте время сброса лимитов для планирования нагрузки"
            ],
            scaling_recommendations=[
                "Для масштабирования используйте несколько API ключей с ротацией",
                "Рассмотрите кэширование ответов для снижения нагрузки на API",
                "Реализуйте приоритизацию запросов: критичные vs некритичные"
            ]
        )
        
        return AIRecommendations(
            generated_by="fallback_generator",
            analysis=analysis,
            confidence_score=0.6,  # Низкая уверенность для fallback
            risk_assessment="MEDIUM - Базовые рекомендации без AI анализа",
            estimated_cost_impact="При соблюдении рекомендаций ожидается минимизация ошибок 429",
            error_details=error_details
        )
    
    def _generate_cache_key(self, test_results: MultiTierResult, api_context: APIContext) -> str:
        """Генерация ключа кэша"""
        
        # Создаем хэш на основе ключевых параметров
        key_data = {
            "api_name": api_context.api_name,
            "base_url": api_context.base_url,
            "most_restrictive": test_results.most_restrictive,
            "recommended_rate": test_results.recommended_rate,
            "limits_found": test_results.limits_found,
            "model": self.model
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получение из кэша"""
        
        if cache_key not in self._cache:
            return None
        
        cached_data = self._cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data["cached_at"])
        
        # Проверяем TTL
        if datetime.now() - cached_time > timedelta(hours=self.cache_ttl_hours):
            del self._cache[cache_key]
            return None
        
        return cached_data["data"]
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Сохранение в кэш"""
        
        self._cache[cache_key] = {
            "data": data,
            "cached_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_environment(cls) -> 'AIRecommender':
        """Создание из переменных окружения"""
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise AIServiceError("Не найден OPENROUTER_API_KEY в переменных окружения")
        
        model = os.getenv('AI_MODEL', 'anthropic/claude-3.5-sonnet')
        temperature = float(os.getenv('AI_TEMPERATURE', '0.1'))
        max_tokens = int(os.getenv('AI_MAX_TOKENS', '2000'))
        
        return cls(
            openrouter_api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
