"""
Сохранение и загрузка результатов
"""
import asyncio
import gzip
import json
import logging
import os
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import tempfile
from concurrent.futures import ThreadPoolExecutor

from cryptography.fernet import Fernet
import pandas as pd

from .models import (
    DetectionResult, MultiTierResult, StorageConfig
)
from .exceptions import StorageError

logger = logging.getLogger(__name__)


class ResultsStorage:
    """Базовый класс для сохранения результатов"""
    
    def __init__(self, storage_dir: Path, config: StorageConfig):
        self.storage_dir = Path(storage_dir)
        self.config = config
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self) -> None:
        """Создание директории для хранения"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results: DetectionResult) -> Path:
        """Сохранение результатов"""
        raise NotImplementedError
    
    def load_results(self, file_path: Path) -> DetectionResult:
        """Загрузка результатов"""
        raise NotImplementedError


class JSONResultsStorage(ResultsStorage):
    """Сохранение результатов в JSON формате"""
    
    def __init__(
        self, 
        storage_dir: Path, 
        config: StorageConfig,
        enable_encryption: bool = False
    ):
        super().__init__(storage_dir, config)
        self.enable_encryption = enable_encryption
        self._encryption_key = None
        self._batch_results: List[DetectionResult] = []
        self._lock = threading.Lock() if config.thread_safe else None
        
        if enable_encryption and config.encryption_enabled:
            self._setup_encryption()
    
    def _setup_encryption(self) -> None:
        """Настройка шифрования"""
        
        if self.config.encryption_key:
            # Используем предоставленный ключ
            key = self.config.encryption_key.encode()
            # Дополняем до 32 байт если нужно
            if len(key) < 32:
                key = key.ljust(32, b'0')
            elif len(key) > 32:
                key = key[:32]
            
            self._encryption_key = Fernet(Fernet.generate_key())
        else:
            # Генерируем новый ключ
            self._encryption_key = Fernet(Fernet.generate_key())
            logger.warning("Сгенерирован новый ключ шифрования. Сохраните его для расшифровки данных.")
    
    def save_results(self, results: DetectionResult) -> Path:
        """Сохранение результатов в JSON"""
        
        if self._lock:
            with self._lock:
                return self._save_results_impl(results)
        else:
            return self._save_results_impl(results)
    
    def _save_results_impl(self, results: DetectionResult) -> Path:
        """Внутренняя реализация сохранения"""
        
        try:
            # Генерируем имя файла
            file_path = self._generate_file_path()
            
            # Проверяем размер файла если он существует
            if file_path.exists() and self._should_rotate_file(file_path):
                file_path = self._rotate_file(file_path)
            
            # Сериализуем результаты
            data = results.model_dump(mode='json')
            
            # Конвертируем datetime объекты в строки
            json_data = json.dumps(data, default=str, ensure_ascii=False, indent=2)
            
            # Шифруем если нужно
            if self.enable_encryption and self._encryption_key:
                json_data = self._encrypt_data(json_data)
            
            # Сохраняем в файл
            if isinstance(json_data, bytes):
                file_path.write_bytes(json_data)
            else:
                file_path.write_text(json_data, encoding='utf-8')
            
            logger.info(f"Результаты сохранены в {file_path}")
            return file_path
            
        except Exception as e:
            raise StorageError(f"Ошибка сохранения результатов: {e}")
    
    def load_results(self, file_path: Path) -> DetectionResult:
        """Загрузка результатов из JSON"""
        
        try:
            if not file_path.exists():
                raise StorageError(f"Файл не найден: {file_path}")
            
            # Читаем данные
            if self.enable_encryption and self._encryption_key:
                data = file_path.read_bytes()
                json_data = self._decrypt_data(data)
            else:
                json_data = file_path.read_text(encoding='utf-8')
            
            # Парсим JSON
            data_dict = json.loads(json_data)
            
            # Создаем объект результатов
            return DetectionResult(**data_dict)
            
        except json.JSONDecodeError as e:
            raise StorageError(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            raise StorageError(f"Ошибка загрузки результатов: {e}")
    
    def _generate_file_path(self) -> Path:
        """Генерация пути к файлу"""
        
        filename = self.config.output_file
        
        if self.config.append_timestamp:
            # Добавляем timestamp к имени файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                filename = f"{filename}_{timestamp}"
        
        return self.storage_dir / filename
    
    def _should_rotate_file(self, file_path: Path) -> bool:
        """Проверка необходимости ротации файла"""
        
        if not file_path.exists():
            return False
        
        # Проверяем размер файла
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        return file_size_mb >= self.config.max_file_size_mb
    
    def _rotate_file(self, file_path: Path) -> Path:
        """Ротация файла"""
        
        # Создаем новое имя с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = file_path.name.rsplit('.', 1)
        
        if len(name_parts) == 2:
            new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            new_name = f"{file_path.name}_{timestamp}"
        
        new_path = file_path.parent / new_name
        
        # Переименовываем существующий файл
        file_path.rename(new_path)
        
        # Очищаем старые файлы если нужно
        if self.config.cleanup_old_files:
            self._cleanup_old_files()
        
        return file_path  # Возвращаем оригинальный путь для нового файла
    
    def _cleanup_old_files(self) -> None:
        """Очистка старых файлов"""
        
        try:
            # Находим все файлы результатов
            pattern = self.config.output_file.replace('.json', '*.json')
            files = list(self.storage_dir.glob(pattern))
            
            # Сортируем по времени модификации
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Удаляем файлы превышающие лимит
            files_to_delete = files[self.config.max_files_count:]
            
            for file_path in files_to_delete:
                # Создаем бэкап если нужно
                if self.config.backup_before_cleanup:
                    backup_path = file_path.with_suffix('.backup')
                    shutil.copy2(file_path, backup_path)
                
                file_path.unlink()
                logger.info(f"Удален старый файл: {file_path}")
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых файлов: {e}")
    
    def _encrypt_data(self, data: str) -> bytes:
        """Шифрование данных"""
        
        if not self._encryption_key:
            raise StorageError("Ключ шифрования не настроен")
        
        return self._encryption_key.encrypt(data.encode('utf-8'))
    
    def _decrypt_data(self, data: bytes) -> str:
        """Расшифровка данных"""
        
        if not self._encryption_key:
            raise StorageError("Ключ шифрования не настроен")
        
        return self._encryption_key.decrypt(data).decode('utf-8')
    
    def add_to_batch(self, results: DetectionResult) -> None:
        """Добавление результатов в батч"""
        
        if self._lock:
            with self._lock:
                self._batch_results.append(results)
                
                if len(self._batch_results) >= self.config.batch_size:
                    self._flush_batch_impl()
        else:
            self._batch_results.append(results)
            
            if len(self._batch_results) >= self.config.batch_size:
                self._flush_batch_impl()
    
    def flush_batch(self) -> None:
        """Принудительное сохранение батча"""
        
        if self._lock:
            with self._lock:
                self._flush_batch_impl()
        else:
            self._flush_batch_impl()
    
    def _flush_batch_impl(self) -> None:
        """Внутренняя реализация сохранения батча"""
        
        if not self._batch_results:
            return
        
        try:
            # Создаем файл для батча
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_filename = f"batch_{timestamp}.json"
            batch_path = self.storage_dir / batch_filename
            
            # Сериализуем все результаты
            batch_data = [result.model_dump(mode='json') for result in self._batch_results]
            json_data = json.dumps(batch_data, default=str, ensure_ascii=False, indent=2)
            
            # Сохраняем
            batch_path.write_text(json_data, encoding='utf-8')
            
            logger.info(f"Сохранен батч из {len(self._batch_results)} результатов в {batch_path}")
            
            # Очищаем батч
            self._batch_results.clear()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения батча: {e}")
    
    def load_batch_results(self, file_path: Path) -> List[DetectionResult]:
        """Загрузка батча результатов"""
        
        try:
            json_data = file_path.read_text(encoding='utf-8')
            batch_data = json.loads(json_data)
            
            results = []
            for item_data in batch_data:
                results.append(DetectionResult(**item_data))
            
            return results
            
        except Exception as e:
            raise StorageError(f"Ошибка загрузки батча: {e}")
    
    def cleanup_old_files(self) -> Dict[str, Any]:
        """Очистка старых файлов с возвратом статистики"""
        
        try:
            files_cleaned = 0
            space_freed_mb = 0.0
            
            # Находим файлы старше указанного возраста
            cutoff_time = datetime.now() - timedelta(days=self.config.max_age_days)
            
            for file_path in self.storage_dir.glob("*.json"):
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    
                    # Создаем бэкап если нужно
                    if self.config.backup_before_cleanup:
                        backup_path = self.storage_dir / f"backup_{file_path.name}"
                        shutil.copy2(file_path, backup_path)
                    
                    # Удаляем файл
                    file_path.unlink()
                    
                    files_cleaned += 1
                    space_freed_mb += file_size_mb
            
            return {
                "files_cleaned": files_cleaned,
                "space_freed_mb": space_freed_mb
            }
            
        except Exception as e:
            logger.error(f"Ошибка очистки файлов: {e}")
            return {"files_cleaned": 0, "space_freed_mb": 0.0}


class CompressedResultsStorage(JSONResultsStorage):
    """Сохранение результатов с сжатием"""
    
    def _save_results_impl(self, results: DetectionResult) -> Path:
        """Сохранение с сжатием"""
        
        try:
            # Генерируем имя файла с расширением .gz
            file_path = self._generate_file_path()
            if not file_path.name.endswith('.gz'):
                file_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            # Сериализуем результаты
            data = results.model_dump(mode='json')
            json_data = json.dumps(data, default=str, ensure_ascii=False, indent=2)
            
            # Сжимаем и сохраняем
            with gzip.open(file_path, 'wt', encoding='utf-8', compresslevel=self.config.compression_level) as f:
                f.write(json_data)
            
            logger.info(f"Сжатые результаты сохранены в {file_path}")
            return file_path
            
        except Exception as e:
            raise StorageError(f"Ошибка сохранения сжатых результатов: {e}")
    
    def load_results(self, file_path: Path) -> DetectionResult:
        """Загрузка сжатых результатов"""
        
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                json_data = f.read()
            
            data_dict = json.loads(json_data)
            return DetectionResult(**data_dict)
            
        except Exception as e:
            raise StorageError(f"Ошибка загрузки сжатых результатов: {e}")


class RotatingResultsStorage(JSONResultsStorage):
    """Сохранение с автоматической ротацией файлов"""
    
    def _save_results_impl(self, results: DetectionResult) -> Path:
        """Сохранение с ротацией"""
        
        # Проверяем нужна ли ротация
        current_file = self.storage_dir / self.config.output_file
        
        if current_file.exists() and self._should_rotate_file(current_file):
            self._rotate_file(current_file)
        
        return super()._save_results_impl(results)


class ResultsExporter:
    """Экспорт результатов в различные форматы"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_results(
        self,
        results: List[DetectionResult],
        format: str,
        filename: str
    ) -> Path:
        """Экспорт результатов в указанный формат"""
        
        if format == "json":
            return self._export_json(results, filename)
        elif format == "csv":
            return self._export_csv(results, filename)
        elif format == "xlsx":
            return self._export_xlsx(results, filename)
        elif format == "yaml":
            return self._export_yaml(results, filename)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
    
    def _export_json(self, results: List[DetectionResult], filename: str) -> Path:
        """Экспорт в JSON"""
        
        file_path = self.output_dir / filename
        
        data = [result.model_dump(mode='json') for result in results]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=str, ensure_ascii=False, indent=2)
        
        return file_path
    
    def _export_csv(self, results: List[DetectionResult], filename: str) -> Path:
        """Экспорт в CSV"""
        
        file_path = self.output_dir / filename
        
        # Преобразуем в плоскую структуру для CSV
        rows = []
        for result in results:
            row = {
                'site_name': result.site_name,
                'detection_strategy': result.detection_strategy,
                'total_test_duration_hours': result.total_test_duration_hours,
                'success_rate': result.success_rate,
                'most_restrictive': result.detection_results.most_restrictive,
                'recommended_rate': result.detection_results.recommended_rate,
                'limits_found': result.detection_results.limits_found,
                'confidence_score': result.detection_results.confidence_score,
            }
            
            # Добавляем информацию о лимитах
            if result.detection_results.minute_limit:
                row['minute_limit'] = result.detection_results.minute_limit.limit
            if result.detection_results.hour_limit:
                row['hour_limit'] = result.detection_results.hour_limit.limit
            if result.detection_results.day_limit:
                row['day_limit'] = result.detection_results.day_limit.limit
            
            # Добавляем AI рекомендации если есть
            if result.ai_recommendations:
                row['ai_confidence'] = result.ai_recommendations.confidence_score
                row['ai_risk_assessment'] = result.ai_recommendations.risk_assessment
            
            rows.append(row)
        
        # Создаем DataFrame и сохраняем
        df = pd.DataFrame(rows)
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        return file_path
    
    def _export_xlsx(self, results: List[DetectionResult], filename: str) -> Path:
        """Экспорт в Excel"""
        
        file_path = self.output_dir / filename
        
        # Создаем несколько листов
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Основная информация
            main_data = []
            for result in results:
                main_data.append({
                    'Site Name': result.site_name,
                    'Strategy': result.detection_strategy,
                    'Duration (hours)': result.total_test_duration_hours,
                    'Success Rate': result.success_rate,
                    'Most Restrictive': result.detection_results.most_restrictive,
                    'Recommended Rate': result.detection_results.recommended_rate,
                    'Confidence': result.detection_results.confidence_score
                })
            
            df_main = pd.DataFrame(main_data)
            df_main.to_excel(writer, sheet_name='Summary', index=False)
            
            # Детальная информация о лимитах
            limits_data = []
            for result in results:
                for limit_name, limit_obj in [
                    ('10_seconds', result.detection_results.ten_second_limit),
                    ('minute', result.detection_results.minute_limit),
                    ('hour', result.detection_results.hour_limit),
                    ('day', result.detection_results.day_limit)
                ]:
                    if limit_obj:
                        limits_data.append({
                            'Site': result.site_name,
                            'Tier': limit_name,
                            'Limit': limit_obj.limit,
                            'Window (seconds)': limit_obj.window_seconds,
                            'Detected Via': limit_obj.detected_via,
                            'Usage %': limit_obj.usage_percent
                        })
            
            if limits_data:
                df_limits = pd.DataFrame(limits_data)
                df_limits.to_excel(writer, sheet_name='Limits Detail', index=False)
        
        return file_path
    
    def _export_yaml(self, results: List[DetectionResult], filename: str) -> Path:
        """Экспорт в YAML"""
        
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML не установлен. Установите: pip install PyYAML")
        
        file_path = self.output_dir / filename
        
        data = [result.model_dump(mode='json') for result in results]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        return file_path


class ResultsImporter:
    """Импорт результатов из различных форматов"""
    
    def import_results(self, file_path: Path, validate: bool = True) -> DetectionResult:
        """Импорт результатов из файла"""
        
        if not file_path.exists():
            raise StorageError(f"Файл не найден: {file_path}")
        
        try:
            if file_path.suffix.lower() == '.json':
                return self._import_json(file_path, validate)
            elif file_path.suffix.lower() == '.gz':
                return self._import_compressed_json(file_path, validate)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_path.suffix}")
                
        except Exception as e:
            if validate:
                raise StorageError(f"Ошибка импорта: {e}")
            else:
                # Возвращаем сырые данные без валидации
                return self._import_raw(file_path)
    
    def _import_json(self, file_path: Path, validate: bool) -> DetectionResult:
        """Импорт из JSON"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if validate:
            return DetectionResult(**data)
        else:
            return data
    
    def _import_compressed_json(self, file_path: Path, validate: bool) -> DetectionResult:
        """Импорт из сжатого JSON"""
        
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        if validate:
            return DetectionResult(**data)
        else:
            return data
    
    def _import_raw(self, file_path: Path) -> Any:
        """Импорт сырых данных без валидации"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
