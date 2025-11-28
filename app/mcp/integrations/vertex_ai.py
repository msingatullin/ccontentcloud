"""
Google Vertex AI MCP интеграция
Генерация контента через Gemini и изображений через Imagen
"""

import os
import io
import logging
import tempfile
from typing import Any, Dict, List, Optional, Union
from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)


class VertexAIIntegration(BaseMCPIntegration):
    """
    MCP интеграция для Google Vertex AI
    Поддерживает Gemini (текст) и Imagen (изображения)
    """
    
    def __init__(self):
        config = get_mcp_config('vertex_ai')
        if not config:
            # Создаем дефолтную конфигурацию если не найдена
            config_dict = {
                'enabled': True,
                'timeout': 60,
                'max_retries': 3,
                'retry_delay': 2.0,
                'fallback_enabled': True,
                'test_mode': os.getenv('TEST_MODE', 'False').lower() == 'true'
            }
        else:
            config_dict = {
                'enabled': config.enabled,
                'timeout': config.timeout,
                'max_retries': config.max_retries,
                'retry_delay': config.retry_delay,
                'fallback_enabled': config.fallback_enabled,
                'test_mode': config.test_mode
            }
        
        super().__init__('vertex_ai', config_dict)
        
        # Параметры Vertex AI
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', os.getenv('GCP_PROJECT_ID'))
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # Модели по умолчанию
        self.default_text_model = os.getenv('VERTEX_AI_TEXT_MODEL', 'gemini-2.5-flash')
        self.default_image_model = os.getenv('VERTEX_AI_IMAGE_MODEL', 'gemini-2.5-flash-image')
        
        # Флаг инициализации
        self._initialized = False
        self._client = None
        
        logger.info(f"VertexAIIntegration создана: project={self.project_id}, location={self.location}")
    
    def _ensure_initialized(self) -> bool:
        """Инициализация Vertex AI SDK"""
        if self._initialized:
            return True
        
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Инициализация с Application Default Credentials
            # В Cloud Run авторизация происходит автоматически через Service Account
            vertexai.init(
                project=self.project_id,
                location=self.location
            )
            
            self._initialized = True
            logger.info(f"Vertex AI инициализирован: project={self.project_id}, location={self.location}")
            return True
            
        except ImportError as e:
            logger.error(f"Vertex AI SDK не установлен: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка инициализации Vertex AI: {e}")
            return False
    
    async def connect(self) -> MCPResponse:
        """Подключение к Vertex AI"""
        if self._ensure_initialized():
            self.status = MCPStatus.CONNECTED
            return MCPResponse.success_response(
                data={"status": "connected", "project": self.project_id, "location": self.location}
            )
        else:
            self.status = MCPStatus.ERROR
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="initialization_error",
                    message="Не удалось инициализировать Vertex AI"
                )
            )
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Vertex AI"""
        self._initialized = False
        self.status = MCPStatus.DISCONNECTED
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Vertex AI"""
        if not self._ensure_initialized():
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="not_initialized",
                    message="Vertex AI не инициализирован"
                )
            )
        
        try:
            from vertexai.generative_models import GenerativeModel
            
            # Простой тест - создание модели
            model = GenerativeModel(self.default_text_model)
            
            return MCPResponse.success_response(
                data={
                    "status": "healthy",
                    "project": self.project_id,
                    "location": self.location,
                    "text_model": self.default_text_model,
                    "image_model": self.default_image_model
                }
            )
        except Exception as e:
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="health_check_failed",
                    message=str(e)
                )
            )
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_grounding: bool = False,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        system_instruction: Optional[str] = None
    ) -> MCPResponse:
        """
        Генерация текста через Gemini
        
        Args:
            prompt: Текст запроса
            model: Название модели (по умолчанию gemini-1.5-flash-001)
            use_grounding: Использовать Google Search Grounding для фактчекинга
            temperature: Температура генерации (0.0 - 1.0)
            max_output_tokens: Максимальное количество токенов в ответе
            system_instruction: Системная инструкция для модели
        
        Returns:
            MCPResponse с сгенерированным текстом
        """
        if not self._ensure_initialized():
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="not_initialized",
                    message="Vertex AI не инициализирован"
                )
            )
        
        model_name = model or self.default_text_model
        
        try:
            from vertexai.generative_models import (
                GenerativeModel,
                GenerationConfig,
                Tool,
                grounding
            )
            from google.api_core.exceptions import GoogleAPICallError, RetryError
            
            # Конфигурация генерации
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=0.95,
                top_k=40
            )
            
            # Создаем модель
            model_kwargs = {
                "model_name": model_name,
                "generation_config": generation_config
            }
            
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction
            
            gemini_model = GenerativeModel(**model_kwargs)
            
            # Настройка Grounding (Google Search / Enterprise Web Search)
            tools = None
            if use_grounding:
                try:
                    # Для Gemini 2.0+ используем EnterpriseWebSearch через gapic types
                    from google.cloud.aiplatform_v1beta1.types import Tool as ToolProto
                    from google.cloud.aiplatform_v1beta1.types import EnterpriseWebSearch
                    
                    tool_proto = ToolProto(
                        enterprise_web_search=EnterpriseWebSearch()
                    )
                    tools = [Tool._from_gapic(tool_proto)]
                    logger.info("Grounding через Enterprise Web Search включен")
                except ImportError:
                    # Fallback на старый метод для legacy моделей
                    try:
                        tools = [
                            Tool.from_google_search_retrieval(
                                grounding.GoogleSearchRetrieval()
                            )
                        ]
                        logger.info("Grounding через Google Search Retrieval включен (legacy)")
                    except Exception as e2:
                        logger.warning(f"Не удалось включить Grounding (legacy): {e2}")
                except Exception as e:
                    logger.warning(f"Не удалось включить Grounding: {e}")
            
            # Генерация
            if tools:
                try:
                    response = gemini_model.generate_content(
                        prompt,
                        tools=tools
                    )
                except Exception as grounding_err:
                    # Если Grounding не работает - пробуем без него
                    logger.warning(f"Grounding не сработал, пробуем без него: {grounding_err}")
                    response = gemini_model.generate_content(prompt)
            else:
                response = gemini_model.generate_content(prompt)
            
            # Извлекаем текст
            generated_text = response.text if hasattr(response, 'text') else str(response)
            
            # Метаданные ответа
            metadata = {
                "model": model_name,
                "grounding_used": use_grounding,
                "temperature": temperature,
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None
            }
            
            # Добавляем информацию о grounding если есть
            if use_grounding and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata["grounding_sources"] = len(
                        candidate.grounding_metadata.grounding_chunks or []
                    )
            
            logger.info(f"Gemini сгенерировал {len(generated_text)} символов")
            
            return MCPResponse.success_response(
                data={"generated_text": generated_text},
                metadata=metadata
            )
            
        except GoogleAPICallError as e:
            logger.error(f"Google API ошибка: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="api_error",
                    message=f"Google API ошибка: {str(e)}",
                    details={"model": model_name, "grounding": use_grounding}
                )
            )
        except RetryError as e:
            logger.error(f"Retry ошибка: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="retry_error",
                    message=f"Превышено количество попыток: {str(e)}"
                )
            )
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="generation_error",
                    message=str(e),
                    details={"model": model_name}
                )
            )
    
    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        number_of_images: int = 1,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> MCPResponse:
        """
        Генерация изображения через Gemini или Imagen
        
        Args:
            prompt: Описание изображения
            aspect_ratio: Соотношение сторон ("1:1", "16:9", "9:16", "4:3", "3:4")
            number_of_images: Количество изображений (1-4)
            negative_prompt: Что НЕ должно быть на изображении
            model: Название модели (по умолчанию gemini-2.5-flash-image)
        
        Returns:
            MCPResponse с байтами изображения или путем к файлу
        """
        if not self._ensure_initialized():
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="not_initialized",
                    message="Vertex AI не инициализирован"
                )
            )
        
        model_name = model or self.default_image_model
        
        # Определяем тип модели
        is_gemini_image = 'gemini' in model_name.lower()
        
        try:
            from google.api_core.exceptions import GoogleAPICallError, RetryError
            
            if is_gemini_image:
                # Используем Gemini для генерации изображений (gemini-2.5-flash-image)
                return await self._generate_image_gemini(prompt, model_name, negative_prompt)
            else:
                # Используем Imagen (imagegeneration@006 и т.д.)
                return await self._generate_image_imagen(
                    prompt, model_name, aspect_ratio, number_of_images, negative_prompt
                )
                
        except GoogleAPICallError as e:
            logger.error(f"Google API ошибка при генерации изображения: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="api_error",
                    message=f"Image API ошибка: {str(e)}",
                    details={"model": model_name}
                )
            )
        except RetryError as e:
            logger.error(f"Retry ошибка при генерации изображения: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="retry_error",
                    message=f"Превышено количество попыток: {str(e)}"
                )
            )
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="image_generation_error",
                    message=str(e),
                    details={"model": model_name, "prompt": prompt[:50]}
                )
            )
    
    async def _generate_image_gemini(
        self,
        prompt: str,
        model_name: str,
        negative_prompt: Optional[str] = None
    ) -> MCPResponse:
        """Генерация изображения через Gemini (gemini-2.5-flash-image)"""
        from vertexai.generative_models import GenerativeModel
        
        # Формируем промпт
        full_prompt = f"Generate an image: {prompt}"
        if negative_prompt:
            full_prompt += f". Avoid: {negative_prompt}"
        
        model = GenerativeModel(model_name)
        
        response = model.generate_content(
            full_prompt,
            generation_config={'response_modalities': ['IMAGE', 'TEXT']}
        )
        
        images_data = []
        for candidate in response.candidates:
            for idx, part in enumerate(candidate.content.parts):
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    
                    # Определяем расширение
                    ext = '.png' if 'png' in mime_type else '.jpg'
                    
                    # Сохраняем во временный файл
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=ext,
                        prefix=f"gemini_img_{idx}_"
                    )
                    temp_file.write(image_bytes)
                    temp_file.close()
                    
                    images_data.append({
                        "index": idx,
                        "file_path": temp_file.name,
                        "bytes_length": len(image_bytes),
                        "format": ext.replace('.', ''),
                        "mime_type": mime_type
                    })
        
        if not images_data:
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="no_images_generated",
                    message="Gemini не сгенерировал изображения"
                )
            )
        
        logger.info(f"Gemini сгенерировал {len(images_data)} изображений")
        
        # Получаем байты первого изображения
        primary_bytes = None
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    primary_bytes = part.inline_data.data
                    break
            if primary_bytes:
                break
        
        return MCPResponse.success_response(
            data={
                "images": images_data,
                "primary_image_path": images_data[0]["file_path"] if images_data else None,
                "primary_image_bytes": primary_bytes
            },
            metadata={
                "model": model_name,
                "prompt": prompt[:100],
                "count": len(images_data),
                "generator": "gemini"
            }
        )
    
    async def _generate_image_imagen(
        self,
        prompt: str,
        model_name: str,
        aspect_ratio: str,
        number_of_images: int,
        negative_prompt: Optional[str]
    ) -> MCPResponse:
        """Генерация изображения через Imagen (legacy)"""
        from vertexai.preview.vision_models import ImageGenerationModel
        
        # Загружаем модель Imagen
        imagen_model = ImageGenerationModel.from_pretrained(model_name)
        
        # Генерируем изображения
        response = imagen_model.generate_images(
            prompt=prompt,
            number_of_images=min(number_of_images, 4),
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
        )
        
        if not response.images:
            return MCPResponse.error_response(
                MCPError(
                    service="vertex_ai",
                    error_type="no_images_generated",
                    message="Imagen не сгенерировал изображения"
                )
            )
        
        # Сохраняем изображения
        images_data = []
        for idx, image in enumerate(response.images):
            image_bytes = image._image_bytes
            
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".png",
                prefix=f"imagen_{idx}_"
            )
            temp_file.write(image_bytes)
            temp_file.close()
            
            images_data.append({
                "index": idx,
                "file_path": temp_file.name,
                "bytes_length": len(image_bytes),
                "format": "png"
            })
        
        logger.info(f"Imagen сгенерировал {len(images_data)} изображений")
        
        return MCPResponse.success_response(
            data={
                "images": images_data,
                "primary_image_path": images_data[0]["file_path"] if images_data else None,
                "primary_image_bytes": response.images[0]._image_bytes if response.images else None
            },
            metadata={
                "model": model_name,
                "aspect_ratio": aspect_ratio,
                "prompt": prompt[:100],
                "count": len(images_data),
                "generator": "imagen"
            }
        )
    
    async def fact_check(
        self,
        claim: str,
        context: Optional[str] = None
    ) -> MCPResponse:
        """
        Проверка факта с использованием Grounding
        
        Args:
            claim: Утверждение для проверки
            context: Дополнительный контекст
        
        Returns:
            MCPResponse с результатом фактчека
        """
        prompt = f"""Проверь следующее утверждение на достоверность, используя актуальную информацию из интернета.

УТВЕРЖДЕНИЕ: {claim}

{f'КОНТЕКСТ: {context}' if context else ''}

Ответь в формате:
1. ВЕРДИКТ: (Правда / Ложь / Частично правда / Невозможно проверить)
2. ОБЪЯСНЕНИЕ: Краткое объяснение почему
3. ИСТОЧНИКИ: Укажи источники информации если есть
"""
        
        return await self.generate_text(
            prompt=prompt,
            use_grounding=True,  # Критически важно для фактчека
            temperature=0.3,  # Низкая температура для точности
            system_instruction="Ты - эксперт по проверке фактов. Будь объективен и опирайся только на проверенные источники."
        )
    
    async def generate_content(self, prompt: str, **kwargs) -> MCPResponse:
        """
        Универсальный метод генерации контента (для совместимости с базовым классом)
        """
        return await self.generate_text(prompt, **kwargs)
    
    def get_supported_models(self) -> Dict[str, List[str]]:
        """Возвращает список поддерживаемых моделей"""
        return {
            "text": [
                "gemini-2.5-flash",      # Gemini 2.5 Flash (рекомендуемая)
                "gemini-2.5-pro",        # Gemini 2.5 Pro (более мощная)
                "gemini-2.0-flash-001",  # Gemini 2.0 Flash
            ],
            "image": [
                "gemini-2.5-flash-image",  # Gemini для изображений (рекомендуемая)
                "imagegeneration@006",     # Imagen 3 (legacy)
                "imagegeneration@005",     # Imagen 2 (legacy)
            ],
            "embedding": [
                "textembedding-gecko@003",
                "textembedding-gecko-multilingual@001"
            ]
        }

