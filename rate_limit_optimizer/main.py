"""
Основной модуль Rate Limit Optimizer
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import ConfigManager
from .detection import MultiTierDetector
from .ai import AIRecommender
from .rotation import EndpointRotator
from .storage import JSONResultsStorage
from .performance import PerformanceMonitor, ResourceMonitor
from .error_handling import ErrorHandler, CircuitBreaker
from .models import (
    DetectionResult, MultiTierResult, APIContext, 
    TargetSite, DetectionSettings, StorageConfig
)
from .exceptions import (
    RateLimitOptimizerError, ConfigurationError, 
    AIServiceError, StorageError
)

logger = logging.getLogger(__name__)


class RateLimitOptimizer:
    """Основной класс Rate Limit Optimizer"""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        enable_ai: bool = True,
        enable_performance_monitoring: bool = True,
        enable_error_handling: bool = True
    ):
        self.config_path = config_path
        self.enable_ai = enable_ai
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_error_handling = enable_error_handling
        
        # Компоненты
        self.config_manager: Optional[ConfigManager] = None
        self.detector: Optional[MultiTierDetector] = None
        self.ai_recommender: Optional[AIRecommender] = None
        self.storage: Optional[JSONResultsStorage] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        self.error_handler: Optional[ErrorHandler] = None
        
        # Состояние
        self._initialized = False
    
    async def initialize(self) -> None:
        """Инициализация компонентов"""
        
        if self._initialized:
            return
        
        logger.info("Инициализация Rate Limit Optimizer...")
        
        try:
            # Загружаем конфигурацию
            self.config_manager = ConfigManager(self.config_path)
            
            if self.config_path:
                config = self.config_manager.load_config()
            else:
                config = self.config_manager.create_default_config()
            
            # Настраиваем логирование
            self._setup_logging(config.logging)
            
            # Инициализируем детектор
            self.detector = MultiTierDetector()
            
            # Инициализируем AI рекомендации если включены
            if self.enable_ai and config.ai_recommendations.enabled:
                try:
                    self.ai_recommender = AIRecommender.from_environment()
                    logger.info("AI рекомендации включены")
                except Exception as e:
                    logger.warning(f"Не удалось инициализировать AI: {e}")
                    self.ai_recommender = None
            
            # Инициализируем хранилище
            storage_config = StorageConfig(
                save_results=config.results_storage.save_results,
                output_format=config.results_storage.output_format,
                output_file=config.results_storage.output_file
            )
            
            storage_dir = Path("results")
            self.storage = JSONResultsStorage(storage_dir, storage_config)
            
            # Инициализируем мониторинг производительности
            if self.enable_performance_monitoring:
                self.performance_monitor = PerformanceMonitor()
                self.resource_monitor = ResourceMonitor()
                logger.info("Мониторинг производительности включен")
            
            # Инициализируем обработку ошибок
            if self.enable_error_handling:
                circuit_breaker = CircuitBreaker(
                    failure_threshold=5,
                    recovery_timeout=60.0
                )
                self.error_handler = ErrorHandler(circuit_breaker=circuit_breaker)
                logger.info("Обработка ошибок включена")
            
            self._initialized = True
            logger.info("Rate Limit Optimizer успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise ConfigurationError(f"Не удалось инициализировать Rate Limit Optimizer: {e}")
    
    async def detect_rate_limits(
        self,
        site_name: str,
        strategy: str = "multi_tier_ramp",
        validate_consistency: bool = True,
        generate_ai_recommendations: bool = True
    ) -> DetectionResult:
        """Определение rate limits для сайта"""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Начинаем определение rate limits для {site_name}")
        
        # Получаем конфигурацию сайта
        config = self.config_manager.get_config()
        if not config:
            raise ConfigurationError("Конфигурация не загружена")
        
        site_config = config.target_sites.get(site_name)
        if not site_config:
            raise ConfigurationError(f"Конфигурация для сайта {site_name} не найдена")
        
        # Запускаем мониторинг ресурсов
        if self.resource_monitor:
            self.resource_monitor.start_monitoring()
        
        try:
            # Определяем лимиты
            detection_result = await self._detect_limits_impl(
                site_config, 
                config.detection_settings,
                strategy,
                validate_consistency
            )
            
            # Генерируем AI рекомендации
            ai_recommendations = None
            if generate_ai_recommendations and self.ai_recommender:
                ai_recommendations = await self._generate_ai_recommendations(
                    detection_result,
                    site_config
                )
            
            # Создаем итоговый результат
            result = DetectionResult(
                site_name=site_name,
                detection_results=detection_result,
                ai_recommendations=ai_recommendations,
                detection_strategy=strategy,
                total_test_duration_hours=detection_result.test_duration_seconds / 3600,
                endpoints_tested=detection_result.endpoints_tested,
                success_rate=detection_result.success_rate,
                detection_methods=["headers", "testing"]
            )
            
            # Сохраняем результаты
            if self.storage:
                await self._save_results(result)
            
            logger.info(f"Определение rate limits для {site_name} завершено")
            return result
            
        finally:
            # Останавливаем мониторинг ресурсов
            if self.resource_monitor:
                self.resource_monitor.stop_monitoring()
    
    async def _detect_limits_impl(
        self,
        site_config: TargetSite,
        detection_settings: DetectionSettings,
        strategy: str,
        validate_consistency: bool
    ) -> MultiTierResult:
        """Внутренняя реализация определения лимитов"""
        
        # Выбираем первый endpoint для тестирования
        primary_endpoint = site_config.endpoints[0] if site_config.endpoints else "/v1/test"
        
        # Подготавливаем заголовки
        headers = site_config.headers.copy()
        
        # Добавляем аутентификацию если нужно
        if site_config.auth.type.value != "none":
            auth_headers = self._prepare_auth_headers(site_config.auth)
            headers.update(auth_headers)
        
        # Получаем tiers для тестирования
        tiers_to_test = detection_settings.multi_tier_detection.tiers_to_test
        
        # Используем мониторинг производительности если доступен
        if self.performance_monitor:
            async with self.performance_monitor.measure_operation("rate_limit_detection"):
                return await self.detector.detect_all_rate_limits(
                    base_url=site_config.base_url,
                    endpoint=primary_endpoint,
                    headers=headers,
                    tiers_to_test=tiers_to_test,
                    validate_consistency=validate_consistency
                )
        else:
            return await self.detector.detect_all_rate_limits(
                base_url=site_config.base_url,
                endpoint=primary_endpoint,
                headers=headers,
                tiers_to_test=tiers_to_test,
                validate_consistency=validate_consistency
            )
    
    def _prepare_auth_headers(self, auth_config) -> Dict[str, str]:
        """Подготовка заголовков аутентификации"""
        
        headers = {}
        
        if auth_config.type.value == "api_key" and auth_config.key_env:
            import os
            api_key = os.getenv(auth_config.key_env)
            if api_key:
                headers["X-API-Key"] = api_key
        
        elif auth_config.type.value == "bearer_token" and auth_config.token_env:
            import os
            token = os.getenv(auth_config.token_env)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif auth_config.type.value == "basic_auth":
            import os
            import base64
            username = os.getenv(auth_config.username_env) if auth_config.username_env else ""
            password = os.getenv(auth_config.password_env) if auth_config.password_env else ""
            
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    async def _generate_ai_recommendations(
        self,
        detection_result: MultiTierResult,
        site_config: TargetSite
    ) -> Optional[Any]:
        """Генерация AI рекомендаций"""
        
        if not self.ai_recommender:
            return None
        
        try:
            # Создаем контекст API
            api_context = APIContext(
                api_name=site_config.base_url,
                base_url=site_config.base_url,
                api_type="REST",
                authentication_type=site_config.auth.type.value,
                primary_use_case="rate_limit_testing",
                business_criticality="medium",
                expected_load="medium"
            )
            
            # Используем мониторинг если доступен
            if self.performance_monitor:
                async with self.performance_monitor.measure_operation("ai_recommendations"):
                    return await self.ai_recommender.generate_recommendations(
                        detection_result, api_context
                    )
            else:
                return await self.ai_recommender.generate_recommendations(
                    detection_result, api_context
                )
                
        except AIServiceError as e:
            logger.warning(f"Не удалось сгенерировать AI рекомендации: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка генерации AI рекомендаций: {e}")
            return None
    
    async def _save_results(self, result: DetectionResult) -> None:
        """Сохранение результатов"""
        
        if not self.storage:
            return
        
        try:
            if self.performance_monitor:
                async with self.performance_monitor.measure_operation("save_results"):
                    self.storage.save_results(result)
            else:
                self.storage.save_results(result)
                
            logger.info("Результаты сохранены")
            
        except StorageError as e:
            logger.error(f"Ошибка сохранения результатов: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка сохранения: {e}")
    
    def _setup_logging(self, logging_config) -> None:
        """Настройка логирования"""
        
        # Настраиваем уровень логирования
        level = getattr(logging, logging_config.level.upper(), logging.INFO)
        
        # Создаем форматтер
        formatter = logging.Formatter(logging_config.format)
        
        # Настраиваем корневой логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Очищаем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Консольный вывод
        if logging_config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Файловый вывод
        if logging_config.file:
            file_handler = logging.FileHandler(logging_config.file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    async def detect_multiple_sites(
        self,
        site_names: List[str],
        strategy: str = "multi_tier_ramp",
        parallel: bool = False,
        max_concurrent: int = 3
    ) -> List[DetectionResult]:
        """Определение rate limits для нескольких сайтов"""
        
        if not site_names:
            return []
        
        logger.info(f"Определение rate limits для {len(site_names)} сайтов")
        
        if parallel:
            # Параллельное выполнение
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def detect_site(site_name: str) -> DetectionResult:
                async with semaphore:
                    return await self.detect_rate_limits(site_name, strategy)
            
            tasks = [detect_site(site_name) for site_name in site_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Фильтруем успешные результаты
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, DetectionResult):
                    valid_results.append(result)
                else:
                    logger.error(f"Ошибка определения лимитов для {site_names[i]}: {result}")
            
            return valid_results
        else:
            # Последовательное выполнение
            results = []
            for site_name in site_names:
                try:
                    result = await self.detect_rate_limits(site_name, strategy)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка определения лимитов для {site_name}: {e}")
            
            return results
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Получение метрик производительности"""
        
        if not self.performance_monitor:
            return None
        
        metrics = self.performance_monitor.get_metrics()
        
        # Добавляем метрики ресурсов если доступны
        if self.resource_monitor:
            resource_usage = self.resource_monitor.get_resource_usage()
            metrics["resource_usage"] = resource_usage.model_dump()
        
        return metrics
    
    def get_error_stats(self) -> Optional[Dict[str, Any]]:
        """Получение статистики ошибок"""
        
        if not self.error_handler:
            return None
        
        error_stats = self.error_handler.get_error_stats()
        return error_stats.model_dump()
    
    async def cleanup(self) -> None:
        """Очистка ресурсов"""
        
        logger.info("Очистка ресурсов Rate Limit Optimizer...")
        
        # Останавливаем мониторинг
        if self.resource_monitor:
            self.resource_monitor.stop_monitoring()
        
        # Сохраняем батч результатов если есть
        if self.storage and hasattr(self.storage, 'flush_batch'):
            self.storage.flush_batch()
        
        logger.info("Очистка завершена")


class CLIRunner:
    """Запуск через командную строку"""
    
    def __init__(self):
        self.optimizer: Optional[RateLimitOptimizer] = None
    
    async def run_detection(
        self,
        config_path: str,
        site_name: str,
        strategy: str = "multi_tier_ramp",
        output_file: Optional[str] = None,
        enable_ai: bool = True,
        verbose: bool = False
    ) -> None:
        """Запуск определения rate limits через CLI"""
        
        # Настраиваем логирование
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        try:
            # Инициализируем оптимизатор
            self.optimizer = RateLimitOptimizer(
                config_path=Path(config_path),
                enable_ai=enable_ai
            )
            
            await self.optimizer.initialize()
            
            # Запускаем определение
            result = await self.optimizer.detect_rate_limits(
                site_name=site_name,
                strategy=strategy
            )
            
            # Выводим результаты
            self._print_results(result)
            
            # Сохраняем в файл если указан
            if output_file:
                self._save_to_file(result, output_file)
            
            # Выводим метрики производительности
            if verbose:
                self._print_performance_metrics()
            
        except Exception as e:
            logger.error(f"Ошибка выполнения: {e}")
            raise
        finally:
            if self.optimizer:
                await self.optimizer.cleanup()
    
    def _print_results(self, result: DetectionResult) -> None:
        """Вывод результатов в консоль"""
        
        print("\n" + "="*60)
        print(f"РЕЗУЛЬТАТЫ ОПРЕДЕЛЕНИЯ RATE LIMITS")
        print("="*60)
        
        print(f"Сайт: {result.site_name}")
        print(f"Стратегия: {result.detection_strategy}")
        print(f"Длительность тестирования: {result.total_test_duration_hours:.2f} часов")
        print(f"Процент успешности: {result.success_rate:.1%}")
        
        detection = result.detection_results
        print(f"\nСамый строгий лимит: {detection.most_restrictive}")
        print(f"Рекомендуемая частота: {detection.recommended_rate} запросов")
        print(f"Найдено лимитов: {detection.limits_found}")
        print(f"Уверенность: {detection.confidence_score:.1%}")
        
        # Детали лимитов
        print("\nОБНАРУЖЕННЫЕ ЛИМИТЫ:")
        print("-" * 40)
        
        limits = [
            ("10 секунд", detection.ten_second_limit),
            ("Минута", detection.minute_limit),
            ("15 минут", detection.fifteen_minute_limit),
            ("Час", detection.hour_limit),
            ("День", detection.day_limit)
        ]
        
        for name, limit in limits:
            if limit:
                print(f"{name}: {limit.limit} запросов (осталось: {limit.remaining})")
        
        # AI рекомендации
        if result.ai_recommendations:
            ai = result.ai_recommendations
            print(f"\nAI РЕКОМЕНДАЦИИ:")
            print("-" * 40)
            print(f"Уверенность: {ai.confidence_score:.1%}")
            print(f"Оценка рисков: {ai.risk_assessment}")
            print(f"\nСтратегия использования:")
            print(ai.analysis.optimal_usage_strategy)
            
            if ai.analysis.implementation_patterns:
                print(f"\nПаттерны реализации:")
                for pattern in ai.analysis.implementation_patterns:
                    print(f"• {pattern}")
        
        print("\n" + "="*60)
    
    def _save_to_file(self, result: DetectionResult, output_file: str) -> None:
        """Сохранение результатов в файл"""
        
        import json
        
        try:
            data = result.model_dump(mode='json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=str, ensure_ascii=False, indent=2)
            
            print(f"\nРезультаты сохранены в {output_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в файл: {e}")
    
    def _print_performance_metrics(self) -> None:
        """Вывод метрик производительности"""
        
        if not self.optimizer:
            return
        
        metrics = self.optimizer.get_performance_metrics()
        if not metrics:
            return
        
        print(f"\nМЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print("-" * 40)
        
        # Метрики запросов
        if 'request_metrics' in metrics:
            for name, data in metrics['request_metrics'].items():
                print(f"{name}:")
                print(f"  Запросов: {data['total_requests']}")
                print(f"  Успешность: {data['success_rate']:.1%}")
                print(f"  Среднее время: {data['average_response_time']:.3f}s")
        
        # Использование ресурсов
        if 'resource_usage' in metrics:
            usage = metrics['resource_usage']
            print(f"\nИспользование ресурсов:")
            print(f"  Пиковая память: {usage['peak_memory_mb']:.1f} MB")
            print(f"  Средняя память: {usage['average_memory_mb']:.1f} MB")
            print(f"  Пиковый CPU: {usage['peak_cpu_percent']:.1f}%")


# Точка входа для CLI
async def main():
    """Основная функция CLI"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Rate Limit Optimizer")
    parser.add_argument("--config", required=True, help="Путь к файлу конфигурации")
    parser.add_argument("--site", required=True, help="Имя сайта для тестирования")
    parser.add_argument("--strategy", default="multi_tier_ramp", help="Стратегия определения")
    parser.add_argument("--output", help="Файл для сохранения результатов")
    parser.add_argument("--no-ai", action="store_true", help="Отключить AI рекомендации")
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    runner = CLIRunner()
    
    await runner.run_detection(
        config_path=args.config,
        site_name=args.site,
        strategy=args.strategy,
        output_file=args.output,
        enable_ai=not args.no_ai,
        verbose=args.verbose
    )


if __name__ == "__main__":
    asyncio.run(main())
