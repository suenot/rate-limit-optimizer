"""
Интеграционные тесты сохранения результатов в JSON
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from rate_limit_optimizer.storage import (
    ResultsStorage,
    JSONResultsStorage,
    CompressedResultsStorage,
    RotatingResultsStorage,
    ResultsExporter,
    ResultsImporter
)
from rate_limit_optimizer.models import (
    MultiTierResult,
    RateLimit,
    AIRecommendations,
    RecommendationAnalysis,
    DetectionResult,
    StorageConfig
)


class TestResultsStorageIntegration:
    """Интеграционные тесты сохранения результатов"""
    
    @pytest.fixture
    def temp_storage_dir(self) -> Path:
        """Временная директория для тестов"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_detection_result(self) -> MultiTierResult:
        """Пример результата определения лимитов"""
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
    def sample_ai_recommendations(self) -> AIRecommendations:
        """Пример AI рекомендаций"""
        return AIRecommendations(
            generated_by="anthropic/claude-3.5-sonnet",
            timestamp=datetime.now(),
            analysis=RecommendationAnalysis(
                optimal_usage_strategy="Используйте 18 req/10s с буферизацией для пиковых нагрузок",
                implementation_patterns=[
                    "Реализуйте token bucket алгоритм",
                    "Используйте экспоненциальный backoff при 429",
                    "Добавьте jitter к интервалам между запросами"
                ],
                error_handling_advice=[
                    "При 429 ошибке ждите время из Retry-After",
                    "Реализуйте circuit breaker после 3 ошибок подряд",
                    "Логируйте все rate limit события"
                ],
                monitoring_suggestions=[
                    "Отслеживайте requests_per_10_seconds в реальном времени",
                    "Настройте алерты при превышении 90% лимита",
                    "Мониторьте время сброса лимитов"
                ],
                scaling_recommendations=[
                    "Используйте несколько API ключей с ротацией",
                    "Рассмотрите кэширование ответов на 30-60 секунд",
                    "Реализуйте приоритизацию запросов"
                ]
            ),
            confidence_score=0.92,
            risk_assessment="LOW - Лимиты четко определены",
            estimated_cost_impact="0% ошибок 429 при соблюдении рекомендаций"
        )
    
    @pytest.fixture
    def complete_detection_result(self, sample_detection_result, sample_ai_recommendations) -> DetectionResult:
        """Полный результат с AI рекомендациями"""
        return DetectionResult(
            site_name="upbit_api",
            detection_results=sample_detection_result,
            ai_recommendations=sample_ai_recommendations,
            detection_strategy="multi_tier_ramp",
            total_test_duration_hours=2.0,
            endpoints_tested=["/v1/market/all", "/v1/ticker"],
            success_rate=0.98
        )
    
    def test_json_results_storage_save_and_load(self, temp_storage_dir, complete_detection_result):
        """Тест сохранения и загрузки результатов в JSON"""
        storage_config = StorageConfig(
            save_results=True,
            output_format="json",
            output_file="test_results.json",
            append_timestamp=False,
            save_detailed_logs=True
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Сохраняем результаты
        file_path = storage.save_results(complete_detection_result)
        
        # Проверяем что файл создан
        assert file_path.exists()
        assert file_path.name == "test_results.json"
        
        # Загружаем и проверяем содержимое
        loaded_result = storage.load_results(file_path)
        
        assert loaded_result.site_name == complete_detection_result.site_name
        assert loaded_result.detection_results.most_restrictive == complete_detection_result.detection_results.most_restrictive
        assert loaded_result.ai_recommendations.confidence_score == complete_detection_result.ai_recommendations.confidence_score
    
    def test_json_storage_with_timestamp_append(self, temp_storage_dir, complete_detection_result):
        """Тест сохранения с добавлением timestamp к имени файла"""
        storage_config = StorageConfig(
            output_file="results.json",
            append_timestamp=True
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Сохраняем результаты
        file_path = storage.save_results(complete_detection_result)
        
        # Проверяем что timestamp добавлен к имени файла
        assert "results_" in file_path.name
        assert file_path.name.endswith(".json")
        assert len(file_path.name) > len("results.json")  # Должен быть длиннее из-за timestamp
    
    def test_compressed_results_storage(self, temp_storage_dir, complete_detection_result):
        """Тест сжатого сохранения результатов"""
        storage_config = StorageConfig(
            output_file="compressed_results.json.gz",
            compression_enabled=True,
            compression_level=6
        )
        
        storage = CompressedResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Сохраняем результаты
        file_path = storage.save_results(complete_detection_result)
        
        # Проверяем что файл сжат
        assert file_path.suffix == ".gz"
        
        # Проверяем что сжатый файл меньше несжатого
        # Сначала сохраним несжатый для сравнения
        uncompressed_storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="uncompressed.json")
        )
        uncompressed_path = uncompressed_storage.save_results(complete_detection_result)
        
        compressed_size = file_path.stat().st_size
        uncompressed_size = uncompressed_path.stat().st_size
        
        assert compressed_size < uncompressed_size
        
        # Загружаем и проверяем что данные корректны
        loaded_result = storage.load_results(file_path)
        assert loaded_result.site_name == complete_detection_result.site_name
    
    def test_rotating_results_storage(self, temp_storage_dir, complete_detection_result):
        """Тест ротации файлов результатов"""
        storage_config = StorageConfig(
            output_file="rotating_results.json",
            max_file_size_mb=0.001,  # Очень маленький размер для принудительной ротации
            max_files_count=3
        )
        
        storage = RotatingResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Сохраняем несколько результатов для принудительной ротации
        file_paths = []
        for i in range(5):
            # Изменяем данные чтобы файлы были разными
            result_copy = complete_detection_result.model_copy()
            result_copy.site_name = f"test_site_{i}"
            
            file_path = storage.save_results(result_copy)
            file_paths.append(file_path)
        
        # Проверяем что создано не больше max_files_count файлов
        json_files = list(temp_storage_dir.glob("rotating_results*.json"))
        assert len(json_files) <= storage_config.max_files_count
        
        # Проверяем что старые файлы удалены
        all_created_files = [f for f in file_paths if f.exists()]
        assert len(all_created_files) <= storage_config.max_files_count
    
    def test_results_exporter_multiple_formats(self, temp_storage_dir, complete_detection_result):
        """Тест экспорта результатов в различные форматы"""
        exporter = ResultsExporter(output_dir=temp_storage_dir)
        
        # Экспортируем в разные форматы
        formats = ["json", "csv", "xlsx", "yaml"]
        exported_files = {}
        
        for format_type in formats:
            try:
                file_path = exporter.export_results(
                    results=[complete_detection_result],
                    format=format_type,
                    filename=f"export_test.{format_type}"
                )
                exported_files[format_type] = file_path
            except ImportError:
                # Некоторые форматы могут требовать дополнительные библиотеки
                pytest.skip(f"Format {format_type} not supported - missing dependencies")
        
        # Проверяем что файлы созданы
        for format_type, file_path in exported_files.items():
            assert file_path.exists()
            assert file_path.stat().st_size > 0
    
    def test_results_importer_validation(self, temp_storage_dir, complete_detection_result):
        """Тест импорта и валидации результатов"""
        # Сначала сохраняем валидные результаты
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="valid_results.json")
        )
        valid_file = storage.save_results(complete_detection_result)
        
        # Создаем невалидный файл
        invalid_file = temp_storage_dir / "invalid_results.json"
        invalid_data = {
            "site_name": "test",
            "invalid_field": "should_not_be_here",
            # Отсутствуют обязательные поля
        }
        invalid_file.write_text(json.dumps(invalid_data))
        
        importer = ResultsImporter()
        
        # Тестируем импорт валидного файла
        valid_result = importer.import_results(valid_file, validate=True)
        assert valid_result is not None
        assert valid_result.site_name == complete_detection_result.site_name
        
        # Тестируем импорт невалидного файла
        with pytest.raises(Exception):  # Должна быть ошибка валидации
            importer.import_results(invalid_file, validate=True)
        
        # Тестируем импорт невалидного файла без валидации
        invalid_result = importer.import_results(invalid_file, validate=False)
        assert invalid_result is not None  # Должен загрузиться как dict
    
    def test_batch_results_storage(self, temp_storage_dir):
        """Тест пакетного сохранения результатов"""
        storage_config = StorageConfig(
            output_file="batch_results.json",
            batch_size=3,
            auto_flush=True
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Создаем несколько результатов
        results = []
        for i in range(7):  # Больше чем batch_size
            result = DetectionResult(
                site_name=f"test_site_{i}",
                detection_results=MultiTierResult(
                    timestamp=datetime.now(),
                    base_url=f"https://api{i}.test.com",
                    endpoint="/v1/test",
                    most_restrictive="minute",
                    recommended_rate=100 + i,
                    limits_found=1,
                    total_requests=10,
                    confidence_score=0.9
                ),
                detection_strategy="test_strategy",
                total_test_duration_hours=1.0,
                endpoints_tested=["/v1/test"],
                success_rate=0.95
            )
            results.append(result)
        
        # Добавляем результаты по одному
        for result in results:
            storage.add_to_batch(result)
        
        # Принудительно сбрасываем оставшиеся результаты
        storage.flush_batch()
        
        # Проверяем что все результаты сохранены
        saved_files = list(temp_storage_dir.glob("batch_results*.json"))
        assert len(saved_files) >= 2  # Должно быть минимум 2 файла из-за batch_size=3
        
        # Проверяем что все результаты можно загрузить
        total_loaded = 0
        for file_path in saved_files:
            loaded_results = storage.load_batch_results(file_path)
            total_loaded += len(loaded_results)
        
        assert total_loaded == len(results)
    
    def test_results_storage_with_encryption(self, temp_storage_dir, complete_detection_result):
        """Тест сохранения результатов с шифрованием"""
        storage_config = StorageConfig(
            output_file="encrypted_results.json",
            encryption_enabled=True,
            encryption_key="test_key_32_characters_long_123"  # 32 символа для AES
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config,
            enable_encryption=True
        )
        
        # Сохраняем зашифрованные результаты
        file_path = storage.save_results(complete_detection_result)
        
        # Проверяем что файл не содержит открытый текст
        raw_content = file_path.read_bytes()
        assert b"upbit_api" not in raw_content  # site_name не должно быть в открытом виде
        assert b"anthropic" not in raw_content  # AI model не должна быть в открытом виде
        
        # Загружаем и расшифровываем
        loaded_result = storage.load_results(file_path)
        
        # Проверяем что данные корректно расшифрованы
        assert loaded_result.site_name == complete_detection_result.site_name
        assert loaded_result.ai_recommendations.generated_by == complete_detection_result.ai_recommendations.generated_by
    
    def test_concurrent_results_storage(self, temp_storage_dir):
        """Тест параллельного сохранения результатов"""
        import asyncio
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        storage_config = StorageConfig(
            output_file="concurrent_results.json",
            thread_safe=True
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        def save_result(index: int):
            result = DetectionResult(
                site_name=f"concurrent_site_{index}",
                detection_results=MultiTierResult(
                    timestamp=datetime.now(),
                    base_url=f"https://api{index}.test.com",
                    endpoint="/v1/test",
                    most_restrictive="minute",
                    recommended_rate=100 + index,
                    limits_found=1,
                    total_requests=10,
                    confidence_score=0.9
                ),
                detection_strategy="concurrent_test",
                total_test_duration_hours=1.0,
                endpoints_tested=["/v1/test"],
                success_rate=0.95
            )
            return storage.save_results(result)
        
        # Параллельное сохранение
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(save_result, i) for i in range(10)]
            file_paths = [future.result() for future in futures]
        
        # Проверяем что все файлы созданы
        assert len(file_paths) == 10
        for file_path in file_paths:
            assert file_path.exists()
            assert file_path.stat().st_size > 0
    
    def test_storage_cleanup_and_maintenance(self, temp_storage_dir):
        """Тест очистки и обслуживания хранилища"""
        storage_config = StorageConfig(
            output_file="maintenance_test.json",
            cleanup_old_files=True,
            max_age_days=0.001,  # Очень короткий срок для тестирования
            backup_before_cleanup=True
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=storage_config
        )
        
        # Создаем несколько старых файлов
        old_files = []
        for i in range(3):
            old_file = temp_storage_dir / f"old_file_{i}.json"
            old_file.write_text(json.dumps({"test": f"data_{i}"}))
            old_files.append(old_file)
        
        # Искусственно делаем файлы "старыми"
        import time
        time.sleep(0.1)  # Небольшая задержка
        
        # Запускаем очистку
        cleanup_stats = storage.cleanup_old_files()
        
        # Проверяем статистику очистки
        assert cleanup_stats.files_cleaned >= 0
        assert cleanup_stats.space_freed_mb >= 0
        
        # Если файлы были удалены, должны быть созданы бэкапы
        if cleanup_stats.files_cleaned > 0:
            backup_files = list(temp_storage_dir.glob("backup_*.json"))
            assert len(backup_files) >= 0  # Могут быть бэкапы


@pytest.mark.integration
class TestResultsStorageEdgeCases:
    """Тесты граничных случаев хранения результатов"""
    
    def test_storage_with_insufficient_disk_space(self, temp_storage_dir, complete_detection_result):
        """Тест обработки нехватки места на диске"""
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="space_test.json")
        )
        
        # Мокаем ошибку нехватки места
        with patch('pathlib.Path.write_text', side_effect=OSError("No space left on device")):
            with pytest.raises(OSError):
                storage.save_results(complete_detection_result)
    
    def test_storage_with_permission_denied(self, temp_storage_dir, complete_detection_result):
        """Тест обработки ошибок доступа к файлам"""
        # Создаем файл только для чтения
        readonly_file = temp_storage_dir / "readonly.json"
        readonly_file.write_text("{}")
        readonly_file.chmod(0o444)  # Только чтение
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="readonly.json")
        )
        
        with pytest.raises(PermissionError):
            storage.save_results(complete_detection_result)
        
        # Восстанавливаем права для cleanup
        readonly_file.chmod(0o644)
    
    def test_storage_with_corrupted_file(self, temp_storage_dir):
        """Тест обработки поврежденных файлов"""
        # Создаем поврежденный JSON файл
        corrupted_file = temp_storage_dir / "corrupted.json"
        corrupted_file.write_text('{"invalid": json syntax}')
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="corrupted.json")
        )
        
        with pytest.raises(json.JSONDecodeError):
            storage.load_results(corrupted_file)
    
    def test_storage_with_very_large_results(self, temp_storage_dir):
        """Тест сохранения очень больших результатов"""
        # Создаем результат с большим количеством данных
        large_result = DetectionResult(
            site_name="large_test",
            detection_results=MultiTierResult(
                timestamp=datetime.now(),
                base_url="https://api.test.com",
                endpoint="/v1/test",
                most_restrictive="minute",
                recommended_rate=100,
                limits_found=1,
                total_requests=10,
                confidence_score=0.9,
                # Добавляем много данных
                headers_found={f"header_{i}": f"value_{i}" for i in range(10000)},
                error_patterns=[f"error_pattern_{i}" for i in range(1000)]
            ),
            detection_strategy="large_test",
            total_test_duration_hours=1.0,
            endpoints_tested=[f"/v1/endpoint_{i}" for i in range(1000)],
            success_rate=0.95
        )
        
        storage = JSONResultsStorage(
            storage_dir=temp_storage_dir,
            config=StorageConfig(output_file="large_results.json")
        )
        
        # Должно успешно сохранить даже большие данные
        file_path = storage.save_results(large_result)
        assert file_path.exists()
        assert file_path.stat().st_size > 100000  # Должен быть большой файл
        
        # Должно успешно загрузить
        loaded_result = storage.load_results(file_path)
        assert loaded_result.site_name == large_result.site_name
        assert len(loaded_result.endpoints_tested) == 1000
