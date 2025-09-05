"""
Rate Limit Optimizer - автоматическое определение и оптимизация rate limits API
"""

__version__ = "1.0.0"
__author__ = "Rate Limit Optimizer Team"
__description__ = "Инструмент для автоматического определения rate limit'ов любого сайта или API"

from .models import (
    RateLimit,
    RateLimitTier,
    MultiTierResult,
    AIRecommendations,
    DetectionResult
)

from .config import Config, ConfigManager
from .detection import MultiTierDetector, RateLimitDetector
from .ai import AIRecommender
from .storage import JSONResultsStorage

__all__ = [
    "RateLimit",
    "RateLimitTier", 
    "MultiTierResult",
    "AIRecommendations",
    "DetectionResult",
    "Config",
    "ConfigManager",
    "MultiTierDetector",
    "RateLimitDetector",
    "AIRecommender",
    "JSONResultsStorage",
]
