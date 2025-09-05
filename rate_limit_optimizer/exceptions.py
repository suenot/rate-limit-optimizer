"""
Исключения для Rate Limit Optimizer
"""


class RateLimitOptimizerError(Exception):
    """Базовое исключение для Rate Limit Optimizer"""
    pass


class ConfigurationError(RateLimitOptimizerError):
    """Ошибка конфигурации"""
    pass


class NetworkError(RateLimitOptimizerError):
    """Сетевая ошибка"""
    pass


class ServerError(RateLimitOptimizerError):
    """Серверная ошибка (5xx)"""
    pass


class AuthenticationError(RateLimitOptimizerError):
    """Ошибка аутентификации"""
    pass


class RateLimitExceeded(RateLimitOptimizerError):
    """Превышение rate limit"""
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class DetectionError(RateLimitOptimizerError):
    """Ошибка определения лимитов"""
    pass


class AIServiceError(RateLimitOptimizerError):
    """Ошибка AI сервиса"""
    pass


class StorageError(RateLimitOptimizerError):
    """Ошибка хранения данных"""
    pass
