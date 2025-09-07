"""
MCP интеграции для Multimedia Producer Agent
Обеспечивает взаимодействие с внешними сервисами генерации изображений
"""

import asyncio
import base64
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import aiofiles

from app.core.logging import logger


@dataclass
class ImageGenerationConfig:
    """Конфигурация для генерации изображений"""
    model: str
    quality: str = "standard"
    size: str = "1024x1024"
    style: str = "vivid"
    n: int = 1
    response_format: str = "url"


@dataclass
class GenerationResult:
    """Результат генерации изображения"""
    success: bool
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    error: Optional[str] = None
    generation_time: float = 0.0
    model_used: str = ""
    cost_estimate: float = 0.0


class DalleMCPClient:
    """MCP клиент для DALL-E 3"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/images/generations"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("OpenAI API key не найден. DALL-E интеграция недоступна.")
    
    async def __aenter__(self):
        if self.api_key:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_image(
        self, 
        prompt: str, 
        config: ImageGenerationConfig
    ) -> GenerationResult:
        """Генерирует изображение с помощью DALL-E 3"""
        if not self.api_key or not self.session:
            return GenerationResult(
                success=False,
                error="DALL-E API key не настроен"
            )
        
        start_time = datetime.now()
        
        try:
            payload = {
                "model": config.model,
                "prompt": prompt,
                "n": config.n,
                "size": config.size,
                "quality": config.quality,
                "style": config.style,
                "response_format": config.response_format
            }
            
            logger.info(f"DALL-E генерация: {prompt[:50]}...")
            
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "data" in data and len(data["data"]) > 0:
                        image_url = data["data"][0]["url"]
                        
                        # Загружаем изображение
                        image_data = await self._download_image(image_url)
                        
                        generation_time = (datetime.now() - start_time).total_seconds()
                        
                        return GenerationResult(
                            success=True,
                            image_url=image_url,
                            image_data=image_data,
                            generation_time=generation_time,
                            model_used=config.model,
                            cost_estimate=self._calculate_cost(config)
                        )
                    else:
                        return GenerationResult(
                            success=False,
                            error="Нет данных в ответе DALL-E"
                        )
                else:
                    error_text = await response.text()
                    return GenerationResult(
                        success=False,
                        error=f"DALL-E API ошибка {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка DALL-E генерации: {e}")
            return GenerationResult(
                success=False,
                error=str(e)
            )
    
    async def _download_image(self, image_url: str) -> bytes:
        """Загружает изображение по URL"""
        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Ошибка загрузки изображения: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка загрузки изображения {image_url}: {e}")
            raise
    
    def _calculate_cost(self, config: ImageGenerationConfig) -> float:
        """Рассчитывает примерную стоимость генерации"""
        # DALL-E 3 цены (примерные)
        cost_per_image = 0.04  # $0.04 за стандартное качество
        if config.quality == "hd":
            cost_per_image = 0.08  # $0.08 за HD качество
        
        return cost_per_image * config.n


class StableDiffusionMCPClient:
    """MCP клиент для Stable Diffusion"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('STABLE_DIFFUSION_API_KEY')
        self.base_url = base_url or os.getenv('STABLE_DIFFUSION_BASE_URL', 'https://api.stability.ai')
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Stable Diffusion API key не найден. Интеграция недоступна.")
    
    async def __aenter__(self):
        if self.api_key:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_image(
        self, 
        prompt: str, 
        config: ImageGenerationConfig
    ) -> GenerationResult:
        """Генерирует изображение с помощью Stable Diffusion"""
        if not self.api_key or not self.session:
            return GenerationResult(
                success=False,
                error="Stable Diffusion API key не настроен"
            )
        
        start_time = datetime.now()
        
        try:
            # Конвертируем размер в формат Stable Diffusion
            width, height = self._parse_size(config.size)
            
            payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": config.n,
                "steps": 20
            }
            
            logger.info(f"Stable Diffusion генерация: {prompt[:50]}...")
            
            url = f"{self.base_url}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "artifacts" in data and len(data["artifacts"]) > 0:
                        # Stable Diffusion возвращает base64 изображения
                        image_base64 = data["artifacts"][0]["base64"]
                        image_data = base64.b64decode(image_base64)
                        
                        generation_time = (datetime.now() - start_time).total_seconds()
                        
                        return GenerationResult(
                            success=True,
                            image_data=image_data,
                            generation_time=generation_time,
                            model_used=config.model,
                            cost_estimate=self._calculate_cost(config)
                        )
                    else:
                        return GenerationResult(
                            success=False,
                            error="Нет данных в ответе Stable Diffusion"
                        )
                else:
                    error_text = await response.text()
                    return GenerationResult(
                        success=False,
                        error=f"Stable Diffusion API ошибка {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка Stable Diffusion генерации: {e}")
            return GenerationResult(
                success=False,
                error=str(e)
            )
    
    def _parse_size(self, size: str) -> Tuple[int, int]:
        """Парсит размер в формат width x height"""
        try:
            width, height = map(int, size.split('x'))
            return width, height
        except:
            return 1024, 1024  # По умолчанию
    
    def _calculate_cost(self, config: ImageGenerationConfig) -> float:
        """Рассчитывает примерную стоимость генерации"""
        # Stable Diffusion цены (примерные)
        cost_per_image = 0.01  # $0.01 за изображение
        return cost_per_image * config.n


class UnsplashMCPClient:
    """MCP клиент для Unsplash (стоковые изображения)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('UNSPLASH_API_KEY')
        self.base_url = "https://api.unsplash.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Unsplash API key не найден. Интеграция недоступна.")
    
    async def __aenter__(self):
        if self.api_key:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Client-ID {self.api_key}"
                }
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_images(
        self, 
        query: str, 
        count: int = 10,
        orientation: str = "all"
    ) -> List[Dict[str, Any]]:
        """Ищет изображения на Unsplash"""
        if not self.api_key or not self.session:
            logger.warning("Unsplash API key не настроен")
            return []
        
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": count,
                "orientation": orientation
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Unsplash API ошибка: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка поиска в Unsplash: {e}")
            return []
    
    async def download_image(self, image_url: str) -> bytes:
        """Загружает изображение с Unsplash"""
        if not self.session:
            raise Exception("Unsplash сессия не инициализирована")
        
        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Ошибка загрузки изображения: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка загрузки изображения с Unsplash: {e}")
            raise


class ImageOptimizationMCP:
    """MCP для оптимизации изображений"""
    
    def __init__(self):
        self.optimization_settings = {
            "web": {
                "max_width": 1920,
                "max_height": 1920,
                "quality": 85,
                "format": "jpeg"
            },
            "social": {
                "max_width": 1080,
                "max_height": 1080,
                "quality": 90,
                "format": "jpeg"
            },
            "print": {
                "max_width": 3000,
                "max_height": 3000,
                "quality": 95,
                "format": "png"
            }
        }
    
    async def optimize_image(
        self, 
        image_data: bytes, 
        target_platform: str,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Оптимизирует изображение для платформы"""
        try:
            from PIL import Image
            import io
            
            # Загружаем изображение
            image = Image.open(io.BytesIO(image_data))
            
            # Получаем настройки оптимизации
            settings = self.optimization_settings.get(target_platform, self.optimization_settings["web"])
            if custom_settings:
                settings.update(custom_settings)
            
            # Изменяем размер
            if settings.get("max_width") or settings.get("max_height"):
                image.thumbnail(
                    (settings.get("max_width", image.width), 
                     settings.get("max_height", image.height)),
                    Image.Resampling.LANCZOS
                )
            
            # Конвертируем в нужный формат
            output_format = settings.get("format", "jpeg").upper()
            if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                # Создаем белый фон для JPEG
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            
            # Сохраняем с оптимизацией
            output = io.BytesIO()
            save_kwargs = {"format": output_format}
            
            if output_format == "JPEG":
                save_kwargs["quality"] = settings.get("quality", 85)
                save_kwargs["optimize"] = True
            elif output_format == "PNG":
                save_kwargs["optimize"] = True
            
            image.save(output, **save_kwargs)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации изображения: {e}")
            return image_data  # Возвращаем оригинал при ошибке
    
    def get_platform_settings(self, platform: str) -> Dict[str, Any]:
        """Возвращает настройки оптимизации для платформы"""
        return self.optimization_settings.get(platform, self.optimization_settings["web"])


class MCPIntegrationManager:
    """Менеджер MCP интеграций для Multimedia Producer Agent"""
    
    def __init__(self):
        self.dalle_client = None
        self.stable_diffusion_client = None
        self.unsplash_client = None
        self.optimization_mcp = ImageOptimizationMCP()
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Инициализирует MCP клиенты"""
        try:
            self.dalle_client = DalleMCPClient()
            self.stable_diffusion_client = StableDiffusionMCPClient()
            self.unsplash_client = UnsplashMCPClient()
            logger.info("MCP интеграции инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации MCP интеграций: {e}")
    
    async def generate_image_with_fallback(
        self, 
        prompt: str, 
        config: ImageGenerationConfig,
        preferred_model: str = "dalle"
    ) -> GenerationResult:
        """Генерирует изображение с fallback на другие модели"""
        
        # Пробуем предпочтительную модель
        if preferred_model == "dalle" and self.dalle_client:
            async with self.dalle_client as client:
                result = await client.generate_image(prompt, config)
                if result.success:
                    return result
        
        elif preferred_model == "stable_diffusion" and self.stable_diffusion_client:
            async with self.stable_diffusion_client as client:
                result = await client.generate_image(prompt, config)
                if result.success:
                    return result
        
        # Fallback на другие модели
        if self.dalle_client and preferred_model != "dalle":
            async with self.dalle_client as client:
                result = await client.generate_image(prompt, config)
                if result.success:
                    return result
        
        if self.stable_diffusion_client and preferred_model != "stable_diffusion":
            async with self.stable_diffusion_client as client:
                result = await client.generate_image(prompt, config)
                if result.success:
                    return result
        
        # Если все модели недоступны
        return GenerationResult(
            success=False,
            error="Все модели генерации изображений недоступны"
        )
    
    async def search_stock_images(
        self, 
        query: str, 
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Ищет стоковые изображения"""
        if self.unsplash_client:
            async with self.unsplash_client as client:
                return await client.search_images(query, count)
        return []
    
    async def optimize_image_for_platform(
        self, 
        image_data: bytes, 
        platform: str
    ) -> bytes:
        """Оптимизирует изображение для платформы"""
        return await self.optimization_mcp.optimize_image(image_data, platform)
