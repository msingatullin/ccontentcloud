"""
Telegram MCP интеграция
Реальная публикация в Telegram через Bot API
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional
import httpx

from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)


class TelegramMCP(BaseMCPIntegration):
    """MCP интеграция для Telegram Bot API"""
    
    def __init__(self):
        config = get_mcp_config('telegram')
        if not config:
            raise ValueError("Telegram конфигурация не найдена")
        
        super().__init__('telegram', {
            'api_key': config.api_key,
            'base_url': config.base_url,
            'timeout': config.timeout,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'fallback_enabled': config.fallback_enabled,
            'test_mode': config.test_mode
        })
        
        self.bot_token = config.api_key
        self.base_url = f"{config.base_url}{self.bot_token}"
        self.chat_id = config.custom_params.get('chat_id', '@your_channel')
        self.parse_mode = config.custom_params.get('parse_mode', 'HTML')
        
        logger.info(f"TelegramMCP инициализирован для чата: {self.chat_id}")
    
    async def connect(self) -> MCPResponse:
        """Подключение к Telegram Bot API"""
        try:
            self.status = MCPStatus.CONNECTING
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/getMe")
                
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get('ok'):
                        self.status = MCPStatus.CONNECTED
                        logger.info(f"Подключен к Telegram Bot: {bot_info['result']['first_name']}")
                        return MCPResponse.success_response(
                            data=bot_info['result'],
                            metadata={'bot_username': bot_info['result'].get('username')}
                        )
                    else:
                        error_msg = bot_info.get('description', 'Неизвестная ошибка')
                        raise MCPError(
                            service=self.service_name,
                            error_type="api_error",
                            message=f"Ошибка Telegram API: {error_msg}"
                        )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="http_error",
                        message=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            self.status = MCPStatus.ERROR
            error = MCPError(
                service=self.service_name,
                error_type="connection_error",
                message=f"Ошибка подключения к Telegram: {str(e)}"
            )
            return MCPResponse.error_response(error)
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Telegram Bot API"""
        self.status = MCPStatus.DISCONNECTED
        logger.info("Отключен от Telegram Bot API")
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Telegram Bot API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/getMe")
                
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get('ok'):
                        return MCPResponse.success_response(
                            data={"status": "healthy", "bot_info": bot_info['result']}
                        )
                    else:
                        return MCPResponse.error_response(
                            MCPError(
                                service=self.service_name,
                                error_type="health_check_failed",
                                message=f"Bot API недоступен: {bot_info.get('description')}"
                            )
                        )
                else:
                    return MCPResponse.error_response(
                        MCPError(
                            service=self.service_name,
                            error_type="health_check_failed",
                            message=f"HTTP {response.status_code}"
                        )
                    )
                    
        except Exception as e:
            return MCPResponse.error_response(
                MCPError(
                    service=self.service_name,
                    error_type="health_check_error",
                    message=str(e)
                )
            )
    
    async def send_message(self, text: str, chat_id: Optional[str] = None, 
                          parse_mode: Optional[str] = None, 
                          disable_web_page_preview: bool = True) -> MCPResponse:
        """Отправка сообщения в Telegram"""
        try:
            target_chat = chat_id or self.chat_id
            target_parse_mode = parse_mode or self.parse_mode
            
            payload = {
                'chat_id': target_chat,
                'text': text,
                'parse_mode': target_parse_mode,
                'disable_web_page_preview': disable_web_page_preview
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        message_data = result['result']
                        logger.info(f"Сообщение отправлено в {target_chat}, ID: {message_data['message_id']}")
                        return MCPResponse.success_response(
                            data=message_data,
                            metadata={
                                'chat_id': target_chat,
                                'message_id': message_data['message_id'],
                                'sent_at': datetime.now().isoformat()
                            }
                        )
                    else:
                        error_msg = result.get('description', 'Неизвестная ошибка')
                        raise MCPError(
                            service=self.service_name,
                            error_type="send_message_failed",
                            message=f"Ошибка отправки: {error_msg}",
                            details=result
                        )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="http_error",
                        message=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="send_message_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def send_photo(self, photo_url: str, caption: str = "", 
                        chat_id: Optional[str] = None) -> MCPResponse:
        """Отправка фото в Telegram"""
        try:
            target_chat = chat_id or self.chat_id
            
            payload = {
                'chat_id': target_chat,
                'photo': photo_url,
                'caption': caption,
                'parse_mode': self.parse_mode
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sendPhoto",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        message_data = result['result']
                        logger.info(f"Фото отправлено в {target_chat}, ID: {message_data['message_id']}")
                        return MCPResponse.success_response(
                            data=message_data,
                            metadata={
                                'chat_id': target_chat,
                                'message_id': message_data['message_id'],
                                'photo_url': photo_url,
                                'sent_at': datetime.now().isoformat()
                            }
                        )
                    else:
                        error_msg = result.get('description', 'Неизвестная ошибка')
                        raise MCPError(
                            service=self.service_name,
                            error_type="send_photo_failed",
                            message=f"Ошибка отправки фото: {error_msg}",
                            details=result
                        )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="http_error",
                        message=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="send_photo_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def get_chat_info(self, chat_id: Optional[str] = None) -> MCPResponse:
        """Получение информации о чате"""
        try:
            target_chat = chat_id or self.chat_id
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/getChat",
                    params={'chat_id': target_chat}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        return MCPResponse.success_response(
                            data=result['result'],
                            metadata={'chat_id': target_chat}
                        )
                    else:
                        error_msg = result.get('description', 'Неизвестная ошибка')
                        raise MCPError(
                            service=self.service_name,
                            error_type="get_chat_failed",
                            message=f"Ошибка получения чата: {error_msg}",
                            details=result
                        )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="http_error",
                        message=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="get_chat_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def _fallback_operation(self, operation: str, *args, **kwargs) -> MCPResponse:
        """Fallback для Telegram операций"""
        logger.info(f"Выполняем fallback для Telegram операции: {operation}")
        
        # Для тестового режима возвращаем мок данные
        if self.config.get('test_mode', True):
            if operation == 'send_message':
                return MCPResponse.success_response(
                    data={
                        'message_id': 12345,
                        'chat': {'id': self.chat_id, 'type': 'channel'},
                        'date': int(datetime.now().timestamp()),
                        'text': args[0] if args else 'Test message'
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation
                    }
                )
            elif operation == 'send_photo':
                return MCPResponse.success_response(
                    data={
                        'message_id': 12346,
                        'chat': {'id': self.chat_id, 'type': 'channel'},
                        'date': int(datetime.now().timestamp()),
                        'photo': [{'file_id': 'test_photo_id'}]
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation
                    }
                )
        
        # Если не тестовый режим, возвращаем ошибку
        return MCPResponse.error_response(
            MCPError(
                service=self.service_name,
                error_type="fallback_used",
                message=f"Telegram API недоступен, fallback для {operation}",
                details={
                    'original_operation': operation,
                    'fallback_reason': 'service_unavailable'
                }
            )
        )
