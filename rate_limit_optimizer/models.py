"""
Модели данных для Rate Limit Optimizer
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


class AuthType(str, Enum):
    """Типы аутентификации"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class DetectionMethod(str, Enum):
    """Методы определения лимитов"""
    HEADERS = "headers"
    TESTING = "testing"
    COMBINED = "combined"


class CircuitBreakerState(str, Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class RateLimit(BaseModel):
    """Модель rate limit"""
    limit: int = Field(..., gt=0, description="Максимальное количество запросов")
    remaining: int = Field(..., ge=0, description="Оставшееся количество запросов")
    reset_time: Optional[datetime] = Field(None, description="Время сброса лимита")
    window_seconds: int = Field(..., gt=0, description="Временное окно в секундах")
    detected_via: DetectionMethod = Field(..., description="Метод определения лимита")
    
    @validator('remaining')
    def remaining_not_greater_than_limit(cls, v, values):
        if 'limit' in values and v > values['limit']:
            return values['limit']  # Исправляем противоречие
        return v
    
    @property
    def requests_per_second(self) -> float:
        """Количество запросов в секунду"""
        return self.limit / self.window_seconds
    
    @property
    def is_exhausted(self) -> bool:
        """Проверка исчерпания лимита"""
        return self.remaining == 0
    
    @property
    def usage_percent(self) -> float:
        """Процент использования лимита"""
        return ((self.limit - self.remaining) / self.limit) * 100


class RateLimitTier(BaseModel):
    """Конфигурация уровня тестирования rate limit"""
    name: str = Field(..., regex=r'^(10_seconds|minute|15_minutes|hour|day)$')
    window_seconds: int = Field(..., gt=0)
    start_rate: int = Field(..., gt=0)
    max_rate: int = Field(..., gt=0)
    increment: int = Field(..., gt=0)
    test_duration_minutes: Optional[float] = Field(None, gt=0)
    test_duration_hours: Optional[float] = Field(None, gt=0)
    aggressive_testing: bool = Field(False)
    adaptive_increment: bool = Field(False)
    
    @validator('max_rate')
    def max_rate_greater_than_start_rate(cls, v, values):
        if 'start_rate' in values and v <= values['start_rate']:
            raise ValueError('max_rate должен быть больше start_rate')
        return v
    
    @root_validator
    def duration_specified(cls, values):
        duration_minutes = values.get('test_duration_minutes')
        duration_hours = values.get('test_duration_hours')
        
        if not duration_minutes and not duration_hours:
            raise ValueError('Должна быть указана длительность тестирования')
        
        return values
    
    @property
    def test_duration_seconds(self) -> float:
        """Длительность тестирования в секундах"""
        if self.test_duration_hours:
            return self.test_duration_hours * 3600
        elif self.test_duration_minutes:
            return self.test_duration_minutes * 60
        return 0


class TierTestResult(BaseModel):
    """Результат тестирования одного уровня"""
    tier_name: str
    limit_found: bool
    detected_limit: Optional[RateLimit] = None
    requests_sent: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    average_response_time: float = Field(ge=0)
    test_duration_seconds: float = Field(ge=0)
    backoff_triggered: bool = False
    retry_after_seconds: Optional[int] = None
    final_rate_when_limited: Optional[int] = None
    adaptive_increments_used: int = Field(ge=0, default=0)
    server_errors: int = Field(ge=0, default=0)
    error_details: str = Field(default="")
    retry_reasons: List[str] = Field(default_factory=list)


class MultiTierResult(BaseModel):
    """Результат многоуровневого определения лимитов"""
    timestamp: datetime = Field(default_factory=datetime.now)
    base_url: str
    endpoint: str
    
    # Лимиты по уровням
    ten_second_limit: Optional[RateLimit] = None
    minute_limit: Optional[RateLimit] = None
    fifteen_minute_limit: Optional[RateLimit] = None
    hour_limit: Optional[RateLimit] = None
    day_limit: Optional[RateLimit] = None
    
    # Общие результаты
    most_restrictive: str
    recommended_rate: int = Field(gt=0)
    limits_found: int = Field(ge=0)
    total_requests: int = Field(ge=0)
    test_duration_seconds: float = Field(ge=0)
    
    # Дополнительная информация
    headers_found: Dict[str, str] = Field(default_factory=dict)
    error_patterns: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    detection_method: DetectionMethod = Field(default=DetectionMethod.COMBINED)
    
    # Результаты по уровням
    tier_results: List[TierTestResult] = Field(default_factory=list)
    
    # Валидация и предупреждения
    consistency_warnings: Optional[List[str]] = None
    most_restrictive_validated: Optional[str] = None
    
    # Метрики тестирования
    endpoints_tested: List[str] = Field(default_factory=list)
    parallel_execution: bool = False
    
    @property
    def all_detected_limits(self) -> List[RateLimit]:
        """Все обнаруженные лимиты"""
        limits = []
        for limit in [self.ten_second_limit, self.minute_limit, 
                     self.fifteen_minute_limit, self.hour_limit, self.day_limit]:
            if limit:
                limits.append(limit)
        return limits
    
    @property
    def success_rate(self) -> float:
        """Общий процент успешности запросов"""
        if self.total_requests == 0:
            return 0.0
        
        successful = sum(result.successful_requests for result in self.tier_results)
        return successful / self.total_requests


class RecommendationAnalysis(BaseModel):
    """Анализ и рекомендации от AI"""
    optimal_usage_strategy: str
    implementation_patterns: List[str] = Field(min_items=1)
    error_handling_advice: List[str] = Field(min_items=1)
    monitoring_suggestions: List[str] = Field(min_items=1)
    scaling_recommendations: List[str] = Field(min_items=1)


class AIRecommendations(BaseModel):
    """AI рекомендации для оптимизации"""
    generated_by: str
    timestamp: datetime = Field(default_factory=datetime.now)
    analysis: RecommendationAnalysis
    confidence_score: float = Field(ge=0, le=1)
    risk_assessment: str
    estimated_cost_impact: str
    model_responses: Optional[List[Dict[str, Any]]] = None
    error_details: str = Field(default="")


class DetectionResult(BaseModel):
    """Полный результат определения лимитов с AI рекомендациями"""
    site_name: str
    detection_results: MultiTierResult
    ai_recommendations: Optional[AIRecommendations] = None
    detection_strategy: str
    total_test_duration_hours: float = Field(ge=0)
    endpoints_tested: List[str] = Field(min_items=1)
    success_rate: float = Field(ge=0, le=1)
    detection_methods: List[str] = Field(default_factory=list)


# Модели для конфигурации
class AuthConfig(BaseModel):
    """Конфигурация аутентификации"""
    type: AuthType
    key_env: Optional[str] = None
    username_env: Optional[str] = None
    password_env: Optional[str] = None
    token_env: Optional[str] = None


class TargetSite(BaseModel):
    """Конфигурация целевого сайта"""
    base_url: str = Field(..., regex=r'^https?://')
    endpoints: List[str] = Field(min_items=1)
    headers: Dict[str, str] = Field(default_factory=dict)
    auth: AuthConfig
    
    @validator('headers')
    def validate_safe_headers(cls, v):
        """Проверка безопасности заголовков"""
        user_agent = v.get('User-Agent', '')
        if 'RateLimitOptimizer' in user_agent or 'bot' in user_agent.lower():
            raise ValueError('User-Agent не должен содержать палевные значения')
        return v


class BatchSettings(BaseModel):
    """Настройки батчевой обработки"""
    requests_per_batch: int = Field(gt=0, default=5)
    batch_interval_seconds: float = Field(gt=0, default=2.0)
    adaptive_batching: bool = Field(default=True)
    fast_mode: bool = Field(default=False)


class SafetySettings(BaseModel):
    """Настройки безопасности тестирования"""
    safety_margin_percent: int = Field(ge=0, le=50, default=10)
    backoff_multiplier: float = Field(gt=1, default=1.5)
    max_consecutive_errors: int = Field(gt=0, default=3)
    cooldown_after_limit_seconds: int = Field(ge=0, default=30)
    fast_detection_mode: bool = Field(default=False)


class EndpointRotation(BaseModel):
    """Настройки ротации endpoints"""
    enabled: bool = Field(default=True)
    strategy: str = Field(default="random")
    rotation_interval_requests: int = Field(gt=0, default=5)
    weight_distribution: str = Field(default="equal")
    avoid_patterns: bool = Field(default=True)
    description: str = Field(default="")


class MultiTierDetection(BaseModel):
    """Настройки многоуровневого определения"""
    enabled: bool = Field(default=True)
    test_all_tiers: bool = Field(default=False)
    tiers_to_test: List[RateLimitTier] = Field(min_items=1)


class DetectionSettings(BaseModel):
    """Настройки определения лимитов"""
    multi_tier_detection: MultiTierDetection
    batch_settings: BatchSettings = Field(default_factory=BatchSettings)
    endpoint_rotation: EndpointRotation = Field(default_factory=EndpointRotation)
    safety_settings: SafetySettings = Field(default_factory=SafetySettings)
    success_threshold: float = Field(ge=0, le=1, default=0.90)
    error_codes_to_detect: List[int] = Field(default=[429, 503, 502, 420])
    rate_limit_headers: List[str] = Field(default_factory=list)


class OptimizationStrategy(BaseModel):
    """Базовая стратегия оптимизации"""
    enabled: bool = Field(default=True)
    description: str = Field(default="")


class MultiTierRampStrategy(OptimizationStrategy):
    """Стратегия многоуровневого тестирования"""
    tier_order: List[str] = Field(min_items=1)
    parallel_testing: bool = Field(default=False)
    stop_on_first_limit: bool = Field(default=True)
    adaptive_increment: bool = Field(default=True)


class HeaderAnalysisStrategy(OptimizationStrategy):
    """Стратегия анализа заголовков"""
    trust_headers: bool = Field(default=True)
    verify_with_testing: bool = Field(default=True)
    safety_margin_percent: int = Field(ge=0, le=50, default=20)
    parse_multiple_limits: bool = Field(default=True)
    header_patterns: Dict[str, List[str]] = Field(default_factory=dict)


class IntelligentProbingStrategy(OptimizationStrategy):
    """Стратегия умного зондирования"""
    start_with_shortest_window: bool = Field(default=True)
    respect_discovered_limits: bool = Field(default=True)
    cross_tier_validation: bool = Field(default=True)


class AISettings(BaseModel):
    """Настройки AI рекомендаций"""
    enabled: bool = Field(default=True)
    provider: str = Field(default="openrouter")
    model: str = Field(default="anthropic/claude-3.5-sonnet")
    api_key_env: str = Field(default="OPENROUTER_API_KEY")
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    settings: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Dict[str, Any] = Field(default_factory=dict)
    recommendation_types: List[str] = Field(default_factory=list)
    fallback_on_error: bool = Field(default=True)
    cache_recommendations: bool = Field(default=True)
    cache_ttl_hours: int = Field(gt=0, default=24)


class ResultsStorage(BaseModel):
    """Настройки сохранения результатов"""
    save_results: bool = Field(default=True)
    output_format: str = Field(default="json")
    output_file: str = Field(default="rate_limit_results.json")
    append_timestamp: bool = Field(default=False)
    save_detailed_logs: bool = Field(default=True)


class MonitoringConfig(BaseModel):
    """Настройки мониторинга"""
    log_requests: bool = Field(default=True)
    log_responses: bool = Field(default=True)
    log_rate_changes: bool = Field(default=True)
    verbose_output: bool = Field(default=True)
    progress_updates: bool = Field(default=True)
    real_time_stats: bool = Field(default=True)
    fast_mode_logging: bool = Field(default=False)
    log_every_n_requests: int = Field(gt=0, default=10)


class RetryPolicy(BaseModel):
    """Политика повторных попыток"""
    max_retries: int = Field(ge=0, default=3)
    base_delay: float = Field(gt=0, default=1.0)
    backoff_multiplier: float = Field(gt=1, default=2.0)
    max_delay: float = Field(gt=0, default=60.0)
    retry_on_codes: List[int] = Field(default=[429, 502, 503, 504])
    retry_on_timeout: bool = Field(default=True)
    jitter: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Настройки логирования"""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file: str = Field(default="rate_limit_optimizer.log")
    console_output: bool = Field(default=True)


class NetworkConfig(BaseModel):
    """Настройки сети"""
    timeout: int = Field(gt=0, default=30)
    max_concurrent_requests: int = Field(gt=0, default=10)
    user_agent: str = Field(default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    verify_ssl: bool = Field(default=True)
    follow_redirects: bool = Field(default=True)


# Модели для обработки ошибок
class RequestError(BaseModel):
    """Ошибка запроса"""
    timestamp: datetime = Field(default_factory=datetime.now)
    error_type: str
    error_message: str
    status_code: Optional[int] = None
    retry_after: Optional[int] = None
    request_url: str
    should_retry: bool = Field(default=False)


class RetryResult(BaseModel):
    """Результат выполнения с повторами"""
    success: bool
    attempts_made: int = Field(ge=1)
    final_response: Optional[Dict[str, Any]] = None
    final_error: Optional[Exception] = None
    total_duration: float = Field(ge=0)
    retry_reasons: List[str] = Field(default_factory=list)


class ErrorStats(BaseModel):
    """Статистика ошибок"""
    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    rate_limit_errors: int = Field(ge=0)
    server_errors: int = Field(ge=0)
    network_errors: int = Field(ge=0)
    timeout_errors: int = Field(ge=0)
    other_errors: int = Field(ge=0)
    
    @property
    def error_rate(self) -> float:
        """Общий процент ошибок"""
        if self.total_requests == 0:
            return 0.0
        errors = self.total_requests - self.successful_requests
        return errors / self.total_requests


# Модели для производительности
class PerformanceMetrics(BaseModel):
    """Метрики производительности"""
    average_response_time: float = Field(ge=0)
    p50_response_time: float = Field(ge=0)
    p95_response_time: float = Field(ge=0)
    p99_response_time: float = Field(ge=0)
    requests_per_second: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    memory_usage_mb: float = Field(ge=0)
    cpu_usage_percent: float = Field(ge=0, le=100)


class LoadTestResult(BaseModel):
    """Результат нагрузочного тестирования"""
    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    average_response_time: float = Field(ge=0)
    p50_response_time: float = Field(ge=0)
    p95_response_time: float = Field(ge=0)
    p99_response_time: float = Field(ge=0)
    max_response_time: float = Field(ge=0)
    min_response_time: float = Field(ge=0)
    requests_per_second: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    test_duration_seconds: float = Field(gt=0)
    max_concurrent_requests: int = Field(gt=0)


class BenchmarkResult(BaseModel):
    """Результат бенчмарка"""
    name: str
    total_iterations: int = Field(gt=0)
    average_duration: float = Field(ge=0)
    min_duration: float = Field(ge=0)
    max_duration: float = Field(ge=0)
    standard_deviation: float = Field(ge=0)
    operations_per_second: float = Field(ge=0)


class ResourceUsage(BaseModel):
    """Использование ресурсов"""
    initial_memory_mb: float = Field(ge=0)
    peak_memory_mb: float = Field(ge=0)
    average_memory_mb: float = Field(ge=0)
    peak_cpu_percent: float = Field(ge=0, le=100)
    average_cpu_percent: float = Field(ge=0, le=100)
    test_duration_seconds: float = Field(gt=0)


# Модели для хранения данных
class StorageConfig(BaseModel):
    """Конфигурация хранения"""
    save_results: bool = Field(default=True)
    output_format: str = Field(default="json")
    output_file: str = Field(default="results.json")
    append_timestamp: bool = Field(default=False)
    save_detailed_logs: bool = Field(default=True)
    compression_enabled: bool = Field(default=False)
    compression_level: int = Field(ge=1, le=9, default=6)
    max_file_size_mb: float = Field(gt=0, default=100.0)
    max_files_count: int = Field(gt=0, default=10)
    cleanup_old_files: bool = Field(default=False)
    max_age_days: float = Field(gt=0, default=30.0)
    backup_before_cleanup: bool = Field(default=True)
    encryption_enabled: bool = Field(default=False)
    encryption_key: Optional[str] = None
    batch_size: int = Field(gt=0, default=100)
    auto_flush: bool = Field(default=True)
    thread_safe: bool = Field(default=True)


# Модели для ротации endpoints
class EndpointConfig(BaseModel):
    """Конфигурация endpoint"""
    path: str
    weight: float = Field(gt=0, default=1.0)
    method: str = Field(default="GET")
    expected_response_time_ms: int = Field(gt=0, default=500)
    rate_limit_shared: bool = Field(default=True)
    priority: str = Field(default="normal")


class RotationMetrics(BaseModel):
    """Метрики ротации endpoints"""
    total_requests: int = Field(ge=0)
    unique_endpoints_used: int = Field(ge=0)
    endpoint_usage_stats: Dict[str, Any] = Field(default_factory=dict)
    rotation_efficiency: float = Field(ge=0, le=1)
    average_response_time: float = Field(ge=0)


class RotationResult(BaseModel):
    """Результат ротации endpoints"""
    endpoints_tested: List[str]
    total_requests: int = Field(ge=0)
    rotation_changes: int = Field(ge=0)
    average_requests_per_endpoint: float = Field(ge=0)
    rotation_strategy_used: str
    performance_metrics: RotationMetrics


# Модели для контекста API
class APIContext(BaseModel):
    """Контекст API для AI анализа"""
    api_name: str
    base_url: str
    api_type: str = Field(default="REST")
    authentication_type: str = Field(default="none")
    primary_use_case: str = Field(default="general")
    business_criticality: str = Field(default="medium")
    expected_load: str = Field(default="medium")
