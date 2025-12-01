"""
Vertex AI MCP интеграция
Генерация контента через Google Vertex AI (Gemini для текста, Imagen для изображений)
"""

import os
import logging
import base64
from typing import Any, Dict, Optional
from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    from vertexai.preview.vision_models import ImageGenerationModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.warning("Vertex AI SDK не установлен. Установите: pip install google-cloud-aiplatform")


class VertexAIMCP(BaseMCPIntegration):
    """MCP интеграция для Google Vertex AI"""
    
    def __init__(self):
        config = get_mcp_config('vertex_ai')
        if not config:
            raise ValueError("Vertex AI конфигурация не найдена")
        
        super().__init__('vertex_ai', {
            'project_id': config.custom_params.get('project_id'),
            'location': config.custom_params.get('location', 'us-central1'),
            'api_key': config.api_key,
            'timeout': config.timeout,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'fallback_enabled': config.fallback_enabled,
            'test_mode': config.test_mode
        })
        
        self.project_id = config.custom_params.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = config.custom_params.get('location', 'us-central1')
        self.gemini_model = config.custom_params.get('gemini_model', 'gemini-1.5-pro')
        self.imagen_model = config.custom_params.get('imagen_model', 'imagegeneration@006')
        
        if not VERTEX_AI_AVAILABLE:
            logger.warning("Vertex AI SDK недоступен. Установите: pip install google-cloud-aiplatform")
        elif not self.project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT не установлен. Vertex AI может не работать")
        else:
            try:
                vertexai.init(project=self.project_id, location=self.location)
                logger.info(f"Vertex AI инициализирован: project={self.project_id}, location={self.location}")
            except Exception as e:
                logger.error(f"Ошибка инициализации Vertex AI: {e}")
    
    async def connect(self) -> MCPResponse:
        """Подключение к Vertex AI"""
        if not VERTEX_AI_AVAILABLE:
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='sdk_not_available',
                    message='Vertex AI SDK не установлен'
                )
            )
        
        if not self.project_id:
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='config_error',
                    message='GOOGLE_CLOUD_PROJECT не установлен'
                )
            )
        
        self.status = MCPStatus.CONNECTED
        return MCPResponse.success_response(data={
            "status": "connected",
            "project_id": self.project_id,
            "location": self.location,
            "gemini_model": self.gemini_model,
            "imagen_model": self.imagen_model
        })
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Vertex AI"""
        self.status = MCPStatus.DISCONNECTED
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Vertex AI"""
        if not VERTEX_AI_AVAILABLE or not self.project_id:
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='not_configured',
                    message='Vertex AI не настроен'
                )
            )
        
        return MCPResponse.success_response(data={"status": "healthy"})
    
    async def generate_content(self, prompt: str, **kwargs) -> MCPResponse:
        """Генерация текста через Gemini"""
        if not VERTEX_AI_AVAILABLE:
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='sdk_not_available',
                    message='Vertex AI SDK не установлен'
                )
            )
        
        try:
            model = GenerativeModel(self.gemini_model)
            
            # Параметры генерации
            generation_config = {
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.95),
                "top_k": kwargs.get('top_k', 40),
                "max_output_tokens": kwargs.get('max_tokens', 2000),
            }
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            generated_text = response.text if hasattr(response, 'text') else str(response)
            
            return MCPResponse.success_response(
                data={
                    "generated_text": generated_text,
                    "model": self.gemini_model
                },
                metadata={
                    "model": self.gemini_model,
                    "prompt_length": len(prompt),
                    "response_length": len(generated_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации текста через Gemini: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='generation_error',
                    message=f"Ошибка генерации: {str(e)}"
                )
            )
    
    async def generate_image(self, prompt: str, **kwargs) -> MCPResponse:
        """Генерация изображения через Imagen"""
        if not VERTEX_AI_AVAILABLE:
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='sdk_not_available',
                    message='Vertex AI SDK не установлен'
                )
            )
        
        try:
            model = ImageGenerationModel.from_pretrained(self.imagen_model)
            
            # Параметры генерации
            number_of_images = kwargs.get('n', 1)
            negative_prompt = kwargs.get('negative_prompt', '')
            seed = kwargs.get('seed', None)
            guidance_scale = kwargs.get('guidance_scale', 7.5)
            
            # Размер изображения
            width = kwargs.get('width', 1024)
            height = kwargs.get('height', 1024)
            
            images = model.generate_images(
                prompt=prompt,
                number_of_images=number_of_images,
                negative_prompt=negative_prompt if negative_prompt else None,
                seed=seed,
                guidance_scale=guidance_scale,
                aspect_ratio=f"{width}:{height}"
            )
            
            # Конвертируем изображения в base64
            image_data_list = []
            for image in images:
                # Сохраняем во временный файл и читаем как bytes
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    image.save(tmp_file.name)
                    with open(tmp_file.name, 'rb') as f:
                        image_bytes = f.read()
                    os.unlink(tmp_file.name)
                
                image_data_list.append({
                    "image_data": base64.b64encode(image_bytes).decode('utf-8'),
                    "format": "png"
                })
            
            return MCPResponse.success_response(
                data={
                    "images": image_data_list,
                    "model": self.imagen_model,
                    "count": len(image_data_list)
                },
                metadata={
                    "model": self.imagen_model,
                    "prompt": prompt[:100],
                    "number_of_images": number_of_images
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения через Imagen: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service='vertex_ai',
                    error_type='generation_error',
                    message=f"Ошибка генерации изображения: {str(e)}"
                )
            )
    
    async def generate_text(self, prompt: str, **kwargs) -> MCPResponse:
        """Алиас для generate_content"""
        return await self.generate_content(prompt, **kwargs)


