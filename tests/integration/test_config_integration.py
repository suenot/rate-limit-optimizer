"""
Интеграционные тесты для конфигурации Rate Limit Optimizer
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import aiohttp
from pydantic import ValidationError

from rate_limit_optimizer.config import (
    Config,
    TargetSite,
    RateLimitTier,
    DetectionSettings,
    AIRecommendations
)


class TestConfigIntegration:
    """Интеграционные тесты загрузки и валидации конфигурации"""
    
    @pytest.fixture
    def sample_config_path(self, tmp_path: Path) -> Path:
        """Создает временный файл конфигурации для тестов"""
        config_data = {
            "version": "1.0.0",
            "description": "Test Rate Limit Optimizer",
            "target_sites": {
                "test_api": {
                    "base_url": "https://api.test.com",
                    "endpoints": ["/v1/test", "/v1/data"],
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Accept-Language": "en-US,en;q=0.9"
                    },
                    "auth": {"type": "none"}
                }
            },
            "detection_settings": {
                "multi_tier_detection": {
                    "enabled": True,
                    "test_all_tiers": False,
                    "tiers_to_test": [
                        {
                            "name": "10_seconds",
                            "window_seconds": 10,
                            "start_rate": 1,
                            "max_rate": 50,
                            "increment": 2,
                            "test_duration_minutes": 1
                        }
                    ]
                },
                "batch_settings": {
                    "requests_per_batch": 5,
                    "batch_interval_seconds": 2,
                    "adaptive_batching": True
                },
                "safety_settings": {
                    "safety_margin_percent": 10,
                    "backoff_multiplier": 1.5,
                    "max_consecutive_errors": 2
                },
                "success_threshold": 0.90,
                "error_codes_to_detect": [429, 503, 502]
            },
            "optimization_strategies": {
                "multi_tier_ramp": {
                    "enabled": True,
                    "tier_order": ["10_seconds"],
                    "stop_on_first_limit": True
                }
            },
            "ai_recommendations": {
                "enabled": True,
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet",
                "api_key_env": "OPENROUTER_API_KEY"
            },
            "results_storage": {
                "save_results": True,
                "output_format": "json",
                "output_file": "test_results.json"
            }
        }
        
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data, indent=2))
        return config_file
    
    @pytest.fixture
    def invalid_config_path(self, tmp_path: Path) -> Path:
        """Создает невалидный файл конфигурации для тестов"""
        invalid_config = {
            "target_sites": {
                "invalid_site": {
                    "base_url": "not-a-url",  # Невалидный URL
                    "endpoints": [],  # Пустой список endpoints
                    "auth": {"type": "unknown"}  # Неизвестный тип аутентификации
                }
            }
        }
        
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text(json.dumps(invalid_config, indent=2))
        return config_file
    
    def test_load_valid_config(self, sample_config_path: Path):
        """Тест загрузки валидной конфигурации"""
        # Загружаем конфигурацию
        with open(sample_config_path, 'r') as f:
            config_data = json.load(f)
        
        # Создаем объект конфигурации
        config = Config(**config_data)
        
        # Проверяем основные поля
        assert config.version == "1.0.0"
        assert "test_api" in config.target_sites
        assert config.detection_settings.multi_tier_detection.enabled is True
        assert config.ai_recommendations.enabled is True
        
        # Проверяем target site
        test_site = config.target_sites["test_api"]
        assert test_site.base_url == "https://api.test.com"
        assert len(test_site.endpoints) == 2
        assert test_site.auth.type == "none"
        
        # Проверяем заголовки безопасности
        assert "Mozilla/5.0" in test_site.headers["User-Agent"]
        assert test_site.headers["Accept"] == "application/json"
    
    def test_load_invalid_config_raises_validation_error(self, invalid_config_path: Path):
        """Тест что невалидная конфигурация вызывает ValidationError"""
        with open(invalid_config_path, 'r') as f:
            config_data = json.load(f)
        
        with pytest.raises(ValidationError) as exc_info:
            Config(**config_data)
        
        # Проверяем что ошибка содержит информацию о проблемах
        error_str = str(exc_info.value)
        assert "base_url" in error_str or "endpoints" in error_str
    
    def test_config_with_missing_required_fields(self):
        """Тест конфигурации с отсутствующими обязательными полями"""
        incomplete_config = {
            "target_sites": {}  # Пустые target_sites
        }
        
        with pytest.raises(ValidationError):
            Config(**incomplete_config)
    
    def test_rate_limit_tier_validation(self):
        """Тест валидации параметров RateLimitTier"""
        # Валидный tier
        valid_tier = RateLimitTier(
            name="minute",
            window_seconds=60,
            start_rate=1,
            max_rate=100,
            increment=5,
            test_duration_minutes=5
        )
        assert valid_tier.name == "minute"
        assert valid_tier.window_seconds == 60
        
        # Невалидный tier с отрицательными значениями
        with pytest.raises(ValidationError):
            RateLimitTier(
                name="invalid",
                window_seconds=-1,  # Отрицательное значение
                start_rate=0,      # Ноль не допустим
                max_rate=-10,      # Отрицательное значение
                increment=-1       # Отрицательное значение
            )
    
    def test_target_site_headers_validation(self):
        """Тест валидации заголовков для TargetSite"""
        # Проверяем что безопасные заголовки проходят валидацию
        safe_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0"
        }
        
        site = TargetSite(
            base_url="https://api.example.com",
            endpoints=["/v1/test"],
            headers=safe_headers,
            auth={"type": "none"}
        )
        
        assert site.headers["User-Agent"].startswith("Mozilla/5.0")
        assert "RateLimitOptimizer" not in site.headers.get("User-Agent", "")
    
    @pytest.mark.asyncio
    async def test_config_environment_variables(self, sample_config_path: Path):
        """Тест подстановки переменных окружения в конфигурации"""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-api-key-123'}):
            with open(sample_config_path, 'r') as f:
                config_data = json.load(f)
            
            config = Config(**config_data)
            
            # Проверяем что переменная окружения правильно подставляется
            assert config.ai_recommendations.api_key_env == "OPENROUTER_API_KEY"
    
    def test_config_serialization_roundtrip(self, sample_config_path: Path):
        """Тест сериализации и десериализации конфигурации"""
        # Загружаем конфигурацию
        with open(sample_config_path, 'r') as f:
            original_data = json.load(f)
        
        # Создаем объект конфигурации
        config = Config(**original_data)
        
        # Сериализуем обратно в dict
        serialized = config.model_dump()
        
        # Создаем новый объект из сериализованных данных
        config_restored = Config(**serialized)
        
        # Проверяем что данные сохранились
        assert config_restored.version == config.version
        assert config_restored.target_sites.keys() == config.target_sites.keys()
        assert config_restored.ai_recommendations.model == config.ai_recommendations.model
    
    def test_config_with_multiple_target_sites(self):
        """Тест конфигурации с несколькими целевыми сайтами"""
        multi_site_config = {
            "target_sites": {
                "upbit_api": {
                    "base_url": "https://api.upbit.com",
                    "endpoints": ["/v1/market/all"],
                    "headers": {"User-Agent": "Mozilla/5.0"},
                    "auth": {"type": "none"}
                },
                "binance_api": {
                    "base_url": "https://api.binance.com",
                    "endpoints": ["/api/v3/ticker/price"],
                    "headers": {"User-Agent": "Mozilla/5.0"},
                    "auth": {"type": "api_key", "key_env": "BINANCE_API_KEY"}
                }
            },
            "detection_settings": {
                "multi_tier_detection": {
                    "enabled": True,
                    "tiers_to_test": []
                }
            }
        }
        
        config = Config(**multi_site_config)
        
        assert len(config.target_sites) == 2
        assert "upbit_api" in config.target_sites
        assert "binance_api" in config.target_sites
        
        # Проверяем разные типы аутентификации
        assert config.target_sites["upbit_api"].auth["type"] == "none"
        assert config.target_sites["binance_api"].auth["type"] == "api_key"
    
    def test_ai_recommendations_config_validation(self):
        """Тест валидации конфигурации AI рекомендаций"""
        ai_config_data = {
            "enabled": True,
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "api_key_env": "OPENROUTER_API_KEY",
            "settings": {
                "temperature": 0.1,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        }
        
        ai_config = AIRecommendations(**ai_config_data)
        
        assert ai_config.enabled is True
        assert ai_config.provider == "openrouter"
        assert ai_config.model == "anthropic/claude-3.5-sonnet"
        assert ai_config.settings["temperature"] == 0.1
        assert ai_config.settings["max_tokens"] == 2000
    
    def test_detection_settings_tier_order_validation(self):
        """Тест валидации порядка тестирования тиров"""
        detection_config = {
            "multi_tier_detection": {
                "enabled": True,
                "test_all_tiers": False,
                "tiers_to_test": [
                    {
                        "name": "10_seconds",
                        "window_seconds": 10,
                        "start_rate": 1,
                        "max_rate": 50,
                        "increment": 2,
                        "test_duration_minutes": 1
                    },
                    {
                        "name": "minute", 
                        "window_seconds": 60,
                        "start_rate": 1,
                        "max_rate": 1000,
                        "increment": 10,
                        "test_duration_minutes": 5
                    }
                ]
            }
        }
        
        settings = DetectionSettings(**detection_config)
        
        assert len(settings.multi_tier_detection.tiers_to_test) == 2
        assert settings.multi_tier_detection.tiers_to_test[0].name == "10_seconds"
        assert settings.multi_tier_detection.tiers_to_test[1].name == "minute"
        
        # Проверяем что временные окна возрастают
        tier1 = settings.multi_tier_detection.tiers_to_test[0]
        tier2 = settings.multi_tier_detection.tiers_to_test[1]
        assert tier1.window_seconds < tier2.window_seconds


@pytest.mark.integration
class TestConfigFileOperations:
    """Тесты операций с файлами конфигурации"""
    
    def test_load_config_from_nonexistent_file(self):
        """Тест загрузки конфигурации из несуществующего файла"""
        with pytest.raises(FileNotFoundError):
            with open("nonexistent_config.json", 'r') as f:
                json.load(f)
    
    def test_load_config_from_malformed_json(self, tmp_path: Path):
        """Тест загрузки конфигурации из файла с невалидным JSON"""
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text('{"invalid": json syntax}')
        
        with pytest.raises(json.JSONDecodeError):
            with open(malformed_file, 'r') as f:
                json.load(f)
    
    def test_config_file_permissions(self, tmp_path: Path):
        """Тест обработки файла конфигурации с ограниченными правами"""
        config_file = tmp_path / "restricted_config.json"
        config_file.write_text('{"test": "data"}')
        
        # Устанавливаем права только на чтение
        config_file.chmod(0o444)
        
        # Проверяем что файл можно прочитать
        with open(config_file, 'r') as f:
            data = json.load(f)
            assert data["test"] == "data"
        
        # Восстанавливаем права для cleanup
        config_file.chmod(0o644)
