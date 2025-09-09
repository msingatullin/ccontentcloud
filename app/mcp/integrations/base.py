"""
Базовый класс для всех MCP интеграций
Обеспечивает единообразный интерфейс и обработку ошибок
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class MCPStatus(Enum):
    """Статусы MCP интеграции"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


@dataclass
class MCPError(Exception):
    """Ошибка MCP интеграции"""
    service: str
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"[{self.service}] {self.error_type}: {self.message}"


@dataclass
class MCPResponse:
    """Стандартный ответ MCP интеграции"""
    success: bool
    data: Optional[Any] = None
    error: Optional[MCPError] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def success_response(cls, data: Any, metadata: Optional[Dict[str, Any]] = None) -> 'MCPResponse':
        """Создает успешный ответ"""
        return cls(
            success=True,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_response(cls, error: MCPError, metadata: Optional[Dict[str, Any]] = None) -> 'MCPResponse':
        """Создает ответ с ошибкой"""
        return cls(
            success=False,
            error=error,
            metadata=metadata or {}
        )


class BaseMCPIntegration(ABC):
    """
    Базовый класс для всех MCP интеграций
    Обеспечивает единообразный интерфейс, обработку ошибок и fallback
    """
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.config = config
        self.status = MCPStatus.DISCONNECTED
        self.last_error: Optional[MCPError] = None
        self.retry_count = 0
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        self.timeout = config.get('timeout', 30.0)
        self.use_fallback = config.get('use_fallback', True)
        self.fallback_enabled = config.get('fallback_enabled', True)
        
        # Метрики
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_request_time: Optional[datetime] = None
        
        logger.info(f"Инициализирована MCP интеграция: {service_name}")
    
    @abstractmethod
    async def connect(self) -> MCPResponse:
        """Подключение к сервису"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> MCPResponse:
        """Отключение от сервиса"""
        pass
    
    @abstractmethod
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья сервиса"""
        pass
    
    async def execute_with_retry(self, operation: str, *args, **kwargs) -> MCPResponse:
        """
        Выполняет операцию с повторными попытками и fallback
        """
        self.request_count += 1
        self.last_request_time = datetime.now()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Выполняем операцию
                result = await self._execute_operation(operation, *args, **kwargs)
                
                if result.success:
                    self.success_count += 1
                    self.retry_count = 0
                    self.status = MCPStatus.CONNECTED
                    return result
                else:
                    self.error_count += 1
                    self.last_error = result.error
                    
                    # Если это последняя попытка, используем fallback
                    if attempt == self.max_retries:
                        if self.fallback_enabled and self.use_fallback:
                            logger.warning(f"Все попытки исчерпаны для {operation}, используем fallback")
                            return await self._fallback_operation(operation, *args, **kwargs)
                        else:
                            self.status = MCPStatus.ERROR
                            return result
                    
                    # Ждем перед следующей попыткой
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    
            except Exception as e:
                self.error_count += 1
                error = MCPError(
                    service=self.service_name,
                    error_type="execution_error",
                    message=str(e),
                    details={"operation": operation, "attempt": attempt + 1}
                )
                self.last_error = error
                
                if attempt == self.max_retries:
                    if self.fallback_enabled and self.use_fallback:
                        logger.warning(f"Критическая ошибка в {operation}, используем fallback: {e}")
                        return await self._fallback_operation(operation, *args, **kwargs)
                    else:
                        self.status = MCPStatus.ERROR
                        return MCPResponse.error_response(error)
                
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        # Не должно дойти до этой точки
        return MCPResponse.error_response(
            MCPError(
                service=self.service_name,
                error_type="max_retries_exceeded",
                message=f"Превышено максимальное количество попыток для {operation}"
            )
        )
    
    async def _execute_operation(self, operation: str, *args, **kwargs) -> MCPResponse:
        """Выполняет конкретную операцию"""
        try:
            # Проверяем подключение
            if self.status != MCPStatus.CONNECTED:
                connect_result = await self.connect()
                if not connect_result.success:
                    return connect_result
            
            # Выполняем операцию
            method = getattr(self, operation, None)
            if method is None:
                raise MCPError(
                    service=self.service_name,
                    error_type="method_not_found",
                    message=f"Метод {operation} не найден"
                )
            
            # Добавляем timeout
            result = await asyncio.wait_for(
                method(*args, **kwargs),
                timeout=self.timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise MCPError(
                service=self.service_name,
                error_type="timeout",
                message=f"Таймаут выполнения операции {operation}"
            )
        except Exception as e:
            raise MCPError(
                service=self.service_name,
                error_type="execution_error",
                message=f"Ошибка выполнения {operation}: {str(e)}"
            )
    
    async def _fallback_operation(self, operation: str, *args, **kwargs) -> MCPResponse:
        """
        Fallback операция - возвращает мок данные или базовую функциональность
        """
        logger.info(f"Выполняем fallback для {operation} в {self.service_name}")
        
        # Базовый fallback - возвращаем ошибку с информацией о fallback
        return MCPResponse.error_response(
            MCPError(
                service=self.service_name,
                error_type="fallback_used",
                message=f"Используется fallback для {operation}",
                details={
                    "original_operation": operation,
                    "fallback_reason": "service_unavailable",
                    "last_error": str(self.last_error) if self.last_error else None
                }
            )
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает метрики интеграции"""
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "last_error": str(self.last_error) if self.last_error else None,
            "retry_count": self.retry_count,
            "fallback_enabled": self.fallback_enabled
        }
    
    def reset_metrics(self):
        """Сбрасывает метрики"""
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.retry_count = 0
        self.last_request_time = None
        self.last_error = None
        logger.info(f"Метрики сброшены для {self.service_name}")
    
    def __str__(self):
        return f"MCPIntegration({self.service_name}, status={self.status.value})"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}({self.service_name})>"
