#!/usr/bin/env python3
"""
Простой тестовый HTTP сервер для демонстрации rate limit detection
Имитирует API с rate limits для тестирования
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
from aiohttp import web, web_request
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitServer:
    def __init__(self):
        # Счетчики запросов по IP и временным окнам
        self.request_counts: Dict[str, Dict[str, List[float]]] = {}
        
        # Настройки rate limits (запросов в секунду)
        self.rate_limits = {
            "10_seconds": 20,    # 20 запросов за 10 секунд
            "minute": 100,       # 100 запросов в минуту  
            "hour": 5000,        # 5000 запросов в час
        }
        
        # Временные окна в секундах
        self.windows = {
            "10_seconds": 10,
            "minute": 60,
            "hour": 3600,
        }
        
    def _get_client_ip(self, request: web_request.Request) -> str:
        """Получить IP клиента"""
        return request.remote or "127.0.0.1"
    
    def _cleanup_old_requests(self, client_ip: str, window: str, current_time: float):
        """Очистить старые запросы вне временного окна"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        if window not in self.request_counts[client_ip]:
            self.request_counts[client_ip][window] = []
        
        window_size = self.windows[window]
        cutoff_time = current_time - window_size
        
        # Удаляем запросы старше временного окна
        self.request_counts[client_ip][window] = [
            req_time for req_time in self.request_counts[client_ip][window]
            if req_time > cutoff_time
        ]
    
    def _check_rate_limit(self, client_ip: str) -> tuple[bool, str, int]:
        """
        Проверить rate limit для клиента
        Возвращает: (is_limited, limit_type, remaining_requests)
        """
        current_time = time.time()
        
        for window, limit in self.rate_limits.items():
            self._cleanup_old_requests(client_ip, window, current_time)
            
            current_count = len(self.request_counts[client_ip][window])
            
            if current_count >= limit:
                return True, window, 0
        
        # Если не превышен лимит, возвращаем минимальное количество оставшихся запросов
        min_remaining = float('inf')
        for window, limit in self.rate_limits.items():
            current_count = len(self.request_counts[client_ip][window])
            remaining = limit - current_count
            min_remaining = min(min_remaining, remaining)
        
        return False, "", int(min_remaining)
    
    def _record_request(self, client_ip: str):
        """Записать запрос в счетчики"""
        current_time = time.time()
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        for window in self.windows:
            if window not in self.request_counts[client_ip]:
                self.request_counts[client_ip][window] = []
            
            self.request_counts[client_ip][window].append(current_time)
    
    async def handle_request(self, request: web_request.Request) -> web.Response:
        """Обработать HTTP запрос с проверкой rate limit"""
        client_ip = self._get_client_ip(request)
        
        # Проверяем rate limit
        is_limited, limit_type, remaining = self._check_rate_limit(client_ip)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_ip}: {limit_type}")
            
            # Возвращаем 429 Too Many Requests
            headers = {
                "X-RateLimit-Limit": str(self.rate_limits[limit_type]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + self.windows[limit_type])),
                "Retry-After": str(self.windows[limit_type]),
            }
            
            return web.json_response(
                {"error": "Rate limit exceeded", "limit_type": limit_type},
                status=429,
                headers=headers
            )
        
        # Записываем успешный запрос
        self._record_request(client_ip)
        
        # Добавляем заголовки rate limit в ответ
        headers = {
            "X-RateLimit-Limit-10s": str(self.rate_limits["10_seconds"]),
            "X-RateLimit-Remaining-10s": str(self.rate_limits["10_seconds"] - len(self.request_counts[client_ip].get("10_seconds", []))),
            "X-RateLimit-Limit-1m": str(self.rate_limits["minute"]),
            "X-RateLimit-Remaining-1m": str(self.rate_limits["minute"] - len(self.request_counts[client_ip].get("minute", []))),
            "X-RateLimit-Limit-1h": str(self.rate_limits["hour"]),
            "X-RateLimit-Remaining-1h": str(self.rate_limits["hour"] - len(self.request_counts[client_ip].get("hour", []))),
        }
        
        # Возвращаем успешный ответ
        response_data = {
            "message": "Success",
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "endpoint": str(request.url),
            "method": request.method,
            "rate_limits": {
                "10_seconds": {
                    "limit": self.rate_limits["10_seconds"],
                    "used": len(self.request_counts[client_ip].get("10_seconds", [])),
                    "remaining": self.rate_limits["10_seconds"] - len(self.request_counts[client_ip].get("10_seconds", []))
                },
                "minute": {
                    "limit": self.rate_limits["minute"],
                    "used": len(self.request_counts[client_ip].get("minute", [])),
                    "remaining": self.rate_limits["minute"] - len(self.request_counts[client_ip].get("minute", []))
                }
            }
        }
        
        logger.info(f"Request from {client_ip}: {remaining} requests remaining")
        
        return web.json_response(response_data, headers=headers)

async def create_app() -> web.Application:
    """Создать aiohttp приложение"""
    server = RateLimitServer()
    
    app = web.Application()
    
    # Добавляем маршруты для разных endpoints
    app.router.add_get('/get', server.handle_request)
    app.router.add_get('/status/200', server.handle_request)
    app.router.add_get('/delay/1', server.handle_request)
    app.router.add_get('/api/v1/test', server.handle_request)
    app.router.add_get('/user', server.handle_request)
    app.router.add_get('/', server.handle_request)
    
    return app

async def main():
    """Запустить тестовый сервер"""
    app = await create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '127.0.0.1', 8888)
    await site.start()
    
    logger.info("🚀 Тестовый сервер запущен на http://127.0.0.1:8888")
    logger.info("📊 Rate limits:")
    logger.info("   • 10 секунд: 20 запросов")
    logger.info("   • 1 минута: 100 запросов")
    logger.info("   • 1 час: 5000 запросов")
    logger.info("🔗 Доступные endpoints:")
    logger.info("   • GET /get")
    logger.info("   • GET /status/200")
    logger.info("   • GET /delay/1")
    logger.info("   • GET /api/v1/test")
    logger.info("   • GET /user")
    logger.info("💡 Для остановки нажмите Ctrl+C")
    
    try:
        # Держим сервер запущенным
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Остановка сервера...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
