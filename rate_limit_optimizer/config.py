"""
Управление конфигурацией Rate Limit Optimizer
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import logging

from .models import (
    TargetSite, DetectionSettings, OptimizationStrategy, AISettings,
    ResultsStorage, MonitoringConfig, RetryPolicy, LoggingConfig, NetworkConfig,
    MultiTierRampStrategy, HeaderAnalysisStrategy, IntelligentProbingStrategy,
    AuthConfig, AuthType
)

logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Основная конфигурация приложения"""
    version: str = Field(default="1.0.0")
    description: str = Field(default="Rate Limit Optimizer Configuration")
    
    target_sites: Dict[str, TargetSite]
    detection_settings: DetectionSettings
    optimization_strategies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    ai_recommendations: AISettings = Field(default_factory=AISettings)
    results_storage: ResultsStorage = Field(default_factory=ResultsStorage)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    retry_policies: RetryPolicy = Field(default_factory=RetryPolicy)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    
    @validator('target_sites')
    def validate_target_sites_not_empty(cls, v):
        if not v:
            raise ValueError('Должен быть указан хотя бы один целевой сайт')
        return v
    
    @validator('optimization_strategies')
    def validate_optimization_strategies(cls, v):
        """Валидация стратегий оптимизации"""
        valid_strategies = ['multi_tier_ramp', 'header_analysis', 'intelligent_probing']
        
        for strategy_name, strategy_config in v.items():
            if strategy_name not in valid_strategies:
                logger.warning(f"Неизвестная стратегия оптимизации: {strategy_name}")
            
            if not isinstance(strategy_config, dict):
                raise ValueError(f"Конфигурация стратегии {strategy_name} должна быть объектом")
            
            if 'enabled' not in strategy_config:
                strategy_config['enabled'] = True
        
        return v
    
    def get_strategy(self, strategy_name: str) -> Optional[OptimizationStrategy]:
        """Получение стратегии оптимизации по имени"""
        strategy_config = self.optimization_strategies.get(strategy_name)
        if not strategy_config:
            return None
        
        if strategy_name == 'multi_tier_ramp':
            return MultiTierRampStrategy(**strategy_config)
        elif strategy_name == 'header_analysis':
            return HeaderAnalysisStrategy(**strategy_config)
        elif strategy_name == 'intelligent_probing':
            return IntelligentProbingStrategy(**strategy_config)
        
        return None
    
    def get_enabled_strategies(self) -> List[str]:
        """Получение списка включенных стратегий"""
        enabled = []
        for name, config in self.optimization_strategies.items():
            if config.get('enabled', True):
                enabled.append(name)
        return enabled


class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config: Optional[Config] = None
    
    def load_config(self, config_path: Optional[Path] = None) -> Config:
        """Загрузка конфигурации из файла"""
        path = config_path or self.config_path
        
        if not path:
            raise ValueError("Не указан путь к файлу конфигурации")
        
        if not path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Подстановка переменных окружения
            config_data = self._substitute_env_vars(config_data)
            
            # Создание объекта конфигурации
            self._config = Config(**config_data)
            
            logger.info(f"Конфигурация успешно загружена из {path}")
            return self._config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON в файле {path}: {e}")
        except Exception as e:
            raise ValueError(f"Ошибка загрузки конфигурации: {e}")
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Подстановка переменных окружения в конфигурации"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # Извлекаем имя переменной окружения
                    env_var = value[2:-1]
                    env_value = os.getenv(env_var)
                    if env_value is not None:
                        result[key] = env_value
                    else:
                        result[key] = value  # Оставляем как есть если переменная не найдена
                else:
                    result[key] = self._substitute_env_vars(value)
            return result
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        else:
            return data
    
    def save_config(self, config: Config, config_path: Optional[Path] = None) -> None:
        """Сохранение конфигурации в файл"""
        path = config_path or self.config_path
        
        if not path:
            raise ValueError("Не указан путь для сохранения конфигурации")
        
        try:
            # Создаем директорию если не существует
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сериализуем конфигурацию
            config_data = config.model_dump(exclude_none=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Конфигурация сохранена в {path}")
            
        except Exception as e:
            raise ValueError(f"Ошибка сохранения конфигурации: {e}")
    
    def validate_config(self, config_path: Optional[Path] = None) -> bool:
        """Валидация конфигурации без загрузки"""
        try:
            self.load_config(config_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
    
    def get_config(self) -> Optional[Config]:
        """Получение текущей конфигурации"""
        return self._config
    
    def create_default_config(self) -> Config:
        """Создание конфигурации по умолчанию"""
        from .models import (
            RateLimitTier, MultiTierDetection, BatchSettings, 
            SafetySettings, EndpointRotation
        )
        
        # Создаем тестовый сайт
        test_site = TargetSite(
            base_url="https://api.test.com",
            endpoints=["/v1/test"],
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9"
            },
            auth=AuthConfig(type=AuthType.NONE)
        )
        
        # Создаем tier для тестирования
        test_tier = RateLimitTier(
            name="10_seconds",
            window_seconds=10,
            start_rate=1,
            max_rate=50,
            increment=2,
            test_duration_minutes=1
        )
        
        # Настройки определения
        detection_settings = DetectionSettings(
            multi_tier_detection=MultiTierDetection(
                enabled=True,
                test_all_tiers=False,
                tiers_to_test=[test_tier]
            ),
            batch_settings=BatchSettings(),
            endpoint_rotation=EndpointRotation(),
            safety_settings=SafetySettings()
        )
        
        # Стратегии оптимизации
        optimization_strategies = {
            "multi_tier_ramp": {
                "enabled": True,
                "tier_order": ["10_seconds"],
                "stop_on_first_limit": True,
                "adaptive_increment": True
            }
        }
        
        config = Config(
            target_sites={"test_site": test_site},
            detection_settings=detection_settings,
            optimization_strategies=optimization_strategies
        )
        
        return config
    
    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> Config:
        """Создание конфигурации из словаря"""
        return Config(**config_dict)
    
    @staticmethod
    def from_json_string(json_string: str) -> Config:
        """Создание конфигурации из JSON строки"""
        config_dict = json.loads(json_string)
        return ConfigManager.from_dict(config_dict)
    
    def merge_configs(self, base_config: Config, override_config: Dict[str, Any]) -> Config:
        """Слияние конфигураций"""
        base_dict = base_config.model_dump()
        
        # Рекурсивное слияние
        merged_dict = self._deep_merge(base_dict, override_config)
        
        return Config(**merged_dict)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Глубокое слияние словарей"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_site_config(self, site_name: str) -> Optional[TargetSite]:
        """Получение конфигурации конкретного сайта"""
        if not self._config:
            return None
        
        return self._config.target_sites.get(site_name)
    
    def add_site_config(self, site_name: str, site_config: TargetSite) -> None:
        """Добавление конфигурации сайта"""
        if not self._config:
            raise ValueError("Конфигурация не загружена")
        
        self._config.target_sites[site_name] = site_config
    
    def remove_site_config(self, site_name: str) -> bool:
        """Удаление конфигурации сайта"""
        if not self._config:
            return False
        
        if site_name in self._config.target_sites:
            del self._config.target_sites[site_name]
            return True
        
        return False
    
    def get_ai_config(self) -> AISettings:
        """Получение конфигурации AI"""
        if not self._config:
            return AISettings()
        
        return self._config.ai_recommendations
    
    def is_ai_enabled(self) -> bool:
        """Проверка включения AI рекомендаций"""
        ai_config = self.get_ai_config()
        return ai_config.enabled and bool(os.getenv(ai_config.api_key_env))
    
    def get_detection_settings(self) -> DetectionSettings:
        """Получение настроек определения лимитов"""
        if not self._config:
            raise ValueError("Конфигурация не загружена")
        
        return self._config.detection_settings
    
    def update_config_from_env(self) -> None:
        """Обновление конфигурации из переменных окружения"""
        if not self._config:
            return
        
        # Обновляем AI настройки
        ai_key_env = self._config.ai_recommendations.api_key_env
        if os.getenv(ai_key_env):
            self._config.ai_recommendations.enabled = True
        
        # Обновляем уровень логирования
        log_level = os.getenv('RATE_LIMIT_LOG_LEVEL')
        if log_level:
            self._config.logging.level = log_level.upper()
        
        # Обновляем настройки сети
        timeout = os.getenv('RATE_LIMIT_TIMEOUT')
        if timeout:
            try:
                self._config.network.timeout = int(timeout)
            except ValueError:
                logger.warning(f"Некорректное значение RATE_LIMIT_TIMEOUT: {timeout}")
    
    def export_config_template(self, output_path: Path) -> None:
        """Экспорт шаблона конфигурации"""
        template_config = self.create_default_config()
        self.save_config(template_config, output_path)
        logger.info(f"Шаблон конфигурации экспортирован в {output_path}")
    
    def check_config_compatibility(self, config_path: Path) -> Dict[str, Any]:
        """Проверка совместимости конфигурации"""
        try:
            config = self.load_config(config_path)
            
            compatibility_report = {
                "compatible": True,
                "version": config.version,
                "warnings": [],
                "errors": []
            }
            
            # Проверяем версию
            if config.version != "1.0.0":
                compatibility_report["warnings"].append(
                    f"Версия конфигурации {config.version} может быть несовместима с текущей версией"
                )
            
            # Проверяем обязательные поля
            if not config.target_sites:
                compatibility_report["errors"].append("Не указаны целевые сайты")
                compatibility_report["compatible"] = False
            
            # Проверяем AI настройки
            if config.ai_recommendations.enabled:
                api_key = os.getenv(config.ai_recommendations.api_key_env)
                if not api_key:
                    compatibility_report["warnings"].append(
                        f"AI рекомендации включены, но не найден API ключ в переменной {config.ai_recommendations.api_key_env}"
                    )
            
            return compatibility_report
            
        except Exception as e:
            return {
                "compatible": False,
                "version": "unknown",
                "warnings": [],
                "errors": [str(e)]
            }
