"""
Multimedia Producer Agent - агент для создания визуального контента
Специализируется на генерации изображений, инфографики и оптимизации медиа
"""

import asyncio
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import aiofiles

import logging

from app.orchestrator.agent_manager import BaseAgent, AgentCapability, AgentStatus
from app.orchestrator.workflow_engine import TaskType, Task
from .mcp_integrations import (
    MCPIntegrationManager, 
    ImageGenerationConfig, 
    GenerationResult
)
from .multimedia_config import MultimediaAgentConfig, load_config_from_env

# Настройка логирования
logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Форматы изображений для разных платформ"""
    SQUARE = "square"          # 1080x1080 (Instagram, Facebook)
    VERTICAL = "vertical"      # 1080x1350 (Instagram Stories, TikTok)
    HORIZONTAL = "horizontal"  # 1920x1080 (YouTube, Facebook Cover)
    CAROUSEL = "carousel"      # 1080x1080 (Instagram Carousel)
    BANNER = "banner"         # 1200x630 (Facebook, Twitter)


class ContentType(Enum):
    """Типы визуального контента"""
    IMAGE = "image"
    INFOGRAPHIC = "infographic"
    CAROUSEL_POST = "carousel_post"
    VIDEO_COVER = "video_cover"
    BANNER = "banner"


@dataclass
class ImageGenerationRequest:
    """Запрос на генерацию изображения"""
    prompt: str
    content_type: ContentType
    image_format: ImageFormat
    style: Optional[str] = None
    brand_colors: Optional[List[str]] = None
    text_overlay: Optional[str] = None
    template_id: Optional[str] = None


@dataclass
class GeneratedImage:
    """Результат генерации изображения"""
    image_id: str
    image_path: str
    image_url: Optional[str]
    format: ImageFormat
    content_type: ContentType
    prompt: str
    generation_time: float
    file_size: int
    dimensions: Tuple[int, int]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InfographicTemplate:
    """Шаблон для инфографики"""
    template_id: str
    name: str
    description: str
    format: ImageFormat
    layout_type: str  # "statistics", "timeline", "comparison", "process"
    text_areas: List[Dict[str, Any]]
    image_areas: List[Dict[str, Any]]
    brand_elements: List[Dict[str, Any]]


class MultimediaProducerAgent(BaseAgent):
    """Агент для создания визуального контента"""
    
    def __init__(self, agent_id: str = "multimedia_producer_agent", config: Optional[MultimediaAgentConfig] = None):
        # Загружаем конфигурацию
        self.config = config or load_config_from_env()
        
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.COMPLEX],
            max_concurrent_tasks=self.config.max_concurrent_tasks,
            specializations=["image_generation", "infographics", "visual_content", "media_optimization"],
            performance_score=self.config.performance_score
        )
        super().__init__(agent_id, self.config.agent_name, capability)
        
        # Настройки генерации
        self.generation_settings = self._load_generation_settings()
        self.platform_formats = self._load_platform_formats()
        
        # MCP интеграции
        self.mcp_manager = MCPIntegrationManager()
        
        # Кэш изображений
        self.image_cache = {}
        self.cache_ttl = timedelta(hours=self.config.cache.ttl_hours)
        self.cache_dir = Path(self.config.cache.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Шаблоны инфографики
        self.infographic_templates = self._load_infographic_templates()
        
        # Система оптимизации
        self.optimization_settings = self._load_optimization_settings()
        
        # Очередь обработки
        self.processing_queue = asyncio.Queue()
        self.processing_tasks = {}
        
        self._initialize_mcp_integrations()
        logger.info(f"MultimediaProducerAgent {agent_id} инициализирован")
    
    def _load_generation_settings(self) -> Dict[str, Any]:
        """Загружает настройки генерации изображений"""
        return {
            "dalle": {
                "model": "dall-e-3",
                "quality": "standard",
                "size": "1024x1024",
                "style": "vivid"
            },
            "stable_diffusion": {
                "model": "stable-diffusion-xl-base-1.0",
                "steps": 20,
                "guidance_scale": 7.5,
                "scheduler": "DPMSolverMultistepScheduler"
            },
            "default_prompts": {
                "infographic": "Clean, modern infographic design with professional typography and clear data visualization",
                "carousel": "Engaging social media carousel post with vibrant colors and clear messaging",
                "video_cover": "Eye-catching video thumbnail with bold text and compelling visuals",
                "banner": "Professional banner design with clear branding and call-to-action"
            }
        }
    
    def _load_platform_formats(self) -> Dict[str, ImageFormat]:
        """Загружает форматы изображений для платформ"""
        return {
            "instagram": ImageFormat.SQUARE,
            "instagram_stories": ImageFormat.VERTICAL,
            "facebook": ImageFormat.HORIZONTAL,
            "youtube": ImageFormat.HORIZONTAL,
            "tiktok": ImageFormat.VERTICAL,
            "twitter": ImageFormat.HORIZONTAL,
            "linkedin": ImageFormat.HORIZONTAL
        }
    
    def _load_infographic_templates(self) -> Dict[str, InfographicTemplate]:
        """Загружает шаблоны инфографики"""
        templates = {}
        
        # Шаблон статистики
        templates["stats_template"] = InfographicTemplate(
            template_id="stats_template",
            name="Statistics Template",
            description="Шаблон для отображения статистических данных",
            format=ImageFormat.SQUARE,
            layout_type="statistics",
            text_areas=[
                {"id": "title", "x": 50, "y": 50, "width": 980, "height": 100, "font_size": 48},
                {"id": "stat1", "x": 100, "y": 200, "width": 400, "height": 300, "font_size": 36},
                {"id": "stat2", "x": 580, "y": 200, "width": 400, "height": 300, "font_size": 36},
                {"id": "description", "x": 50, "y": 550, "width": 980, "height": 200, "font_size": 24}
            ],
            image_areas=[
                {"id": "icon1", "x": 150, "y": 250, "width": 100, "height": 100},
                {"id": "icon2", "x": 630, "y": 250, "width": 100, "height": 100}
            ],
            brand_elements=[
                {"id": "logo", "x": 50, "y": 950, "width": 100, "height": 50},
                {"id": "brand_color", "type": "background", "color": "#007bff"}
            ]
        )
        
        # Шаблон временной шкалы
        templates["timeline_template"] = InfographicTemplate(
            template_id="timeline_template",
            name="Timeline Template",
            description="Шаблон для отображения временной шкалы событий",
            format=ImageFormat.HORIZONTAL,
            layout_type="timeline",
            text_areas=[
                {"id": "title", "x": 50, "y": 50, "width": 1820, "height": 80, "font_size": 42},
                {"id": "event1", "x": 200, "y": 200, "width": 300, "height": 150, "font_size": 24},
                {"id": "event2", "x": 600, "y": 200, "width": 300, "height": 150, "font_size": 24},
                {"id": "event3", "x": 1000, "y": 200, "width": 300, "height": 150, "font_size": 24},
                {"id": "event4", "x": 1400, "y": 200, "width": 300, "height": 150, "font_size": 24}
            ],
            image_areas=[
                {"id": "timeline_line", "x": 100, "y": 300, "width": 1720, "height": 10}
            ],
            brand_elements=[
                {"id": "logo", "x": 50, "y": 950, "width": 100, "height": 50}
            ]
        )
        
        return templates
    
    def _load_optimization_settings(self) -> Dict[str, Any]:
        """Загружает настройки оптимизации изображений"""
        return {
            "compression": {
                "jpeg_quality": 85,
                "png_optimize": True,
                "webp_quality": 80
            },
            "resize": {
                "max_width": 1920,
                "max_height": 1920,
                "maintain_aspect": True
            },
            "formats": {
                "web": ["jpeg", "webp"],
                "social": ["jpeg", "png"],
                "print": ["png", "tiff"]
            }
        }
    
    def _initialize_mcp_integrations(self):
        """Инициализирует MCP интеграции"""
        try:
            # MCP интеграции уже инициализированы в MCPIntegrationManager
            logger.info("MCP интеграции для MultimediaProducerAgent инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации MCP интеграций: {e}")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу по созданию визуального контента"""
        try:
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            task_data = task.context
            task_name = task.name if hasattr(task, 'name') else ""
            image_source = task_data.get("image_source", "ai")
            
            # Проверяем тип задачи
            if "Find Stock Image" in task_name or image_source == "stock":
                # Поиск стокового изображения
                result = await self._find_stock_image(task_data)
            elif "Generate Image" in task_name or image_source == "ai":
                # Генерация через ИИ
                content_type = ContentType(task_data.get("content_type", "image"))
                if content_type == ContentType.IMAGE:
                    result = await self._generate_image(task_data)
                elif content_type == ContentType.INFOGRAPHIC:
                    result = await self._create_infographic(task_data)
                elif content_type == ContentType.CAROUSEL_POST:
                    result = await self._create_carousel_post(task_data)
                elif content_type == ContentType.VIDEO_COVER:
                    result = await self._create_video_cover(task_data)
                else:
                    raise ValueError(f"Неподдерживаемый тип контента: {content_type}")
            else:
                # Дефолтное поведение - генерация через ИИ
                content_type = ContentType(task_data.get("content_type", "image"))
                if content_type == ContentType.IMAGE:
                    result = await self._generate_image(task_data)
                else:
                    raise ValueError(f"Неподдерживаемый тип задачи: {task_name}")
            
            self.status = AgentStatus.IDLE
            return {
                "success": True,
                "result": result,
                "agent_id": self.agent_id,
                "execution_time": (datetime.now() - self.last_activity).total_seconds()
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.error_count += 1
            logger.error(f"Ошибка выполнения задачи в MultimediaProducerAgent: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _generate_image(self, task_data: Dict[str, Any]) -> GeneratedImage:
        """Генерирует изображение на основе текстового описания"""
        prompt = task_data.get("prompt", "")
        image_format = ImageFormat(task_data.get("format", "square"))
        style = task_data.get("style", "professional")
        
        # Проверяем кэш
        cache_key = self._generate_cache_key(prompt, image_format, style)
        cached_image = await self._get_cached_image(cache_key)
        if cached_image:
            logger.info(f"Использовано кэшированное изображение: {cache_key}")
            return cached_image
        
        # Генерируем новое изображение
        start_time = datetime.now()
        
        try:
            # Используем DALL-E 3 для генерации
            image_data = await self._generate_with_dalle(prompt, image_format, style)
            
            # Сохраняем изображение
            image_path = await self._save_generated_image(image_data, cache_key, image_format)
            
            # Создаем объект результата
            generation_time = (datetime.now() - start_time).total_seconds()
            file_size = os.path.getsize(image_path)
            
            generated_image = GeneratedImage(
                image_id=cache_key,
                image_path=str(image_path),
                image_url=None,  # TODO: Загрузить в CDN
                format=image_format,
                content_type=ContentType.IMAGE,
                prompt=prompt,
                generation_time=generation_time,
                file_size=file_size,
                dimensions=self._get_format_dimensions(image_format)
            )
            
            # Кэшируем результат
            await self._cache_image(cache_key, generated_image)
            
            logger.info(f"Изображение сгенерировано за {generation_time:.2f}с: {image_path}")
            return generated_image
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            raise
    
    async def _generate_with_dalle(self, prompt: str, image_format: ImageFormat, style: str) -> bytes:
        """Генерирует изображение с помощью DALL-E 3 через MCP"""
        logger.info(f"Генерация изображения DALL-E: {prompt[:50]}...")
        
        # Создаем конфигурацию для генерации
        config = ImageGenerationConfig(
            model="dall-e-3",
            quality="standard",
            size=self._format_to_size(image_format),
            style=style
        )
        
        # Генерируем изображение через MCP
        result = await self.mcp_manager.generate_image_with_fallback(
            prompt=prompt,
            config=config,
            preferred_model="dalle"
        )
        
        if result.success and result.image_data:
            return result.image_data
        else:
            # Fallback на заглушку при ошибке
            logger.warning(f"Ошибка генерации DALL-E: {result.error}. Используем заглушку.")
            return self._create_fallback_image(prompt, image_format)
    
    def _format_to_size(self, image_format: ImageFormat) -> str:
        """Конвертирует формат изображения в размер для API"""
        size_mapping = {
            ImageFormat.SQUARE: "1024x1024",
            ImageFormat.VERTICAL: "1024x1792",
            ImageFormat.HORIZONTAL: "1792x1024",
            ImageFormat.CAROUSEL: "1024x1024",
            ImageFormat.BANNER: "1024x1024"
        }
        return size_mapping.get(image_format, "1024x1024")
    
    def _create_fallback_image(self, prompt: str, image_format: ImageFormat) -> bytes:
        """Создает изображение-заглушку при ошибке генерации"""
        dimensions = self._get_format_dimensions(image_format)
        image = Image.new('RGB', dimensions, color='#f0f0f0')
        draw = ImageDraw.Draw(image)
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        text = f"Generated: {prompt[:30]}..."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (dimensions[0] - text_width) // 2
        y = (dimensions[1] - text_height) // 2
        
        draw.text((x, y), text, fill='#333333', font=font)
        
        # Сохраняем в байты
        import io
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    async def _create_infographic(self, task_data: Dict[str, Any]) -> GeneratedImage:
        """Создает инфографику на основе шаблона"""
        template_id = task_data.get("template_id", "stats_template")
        data = task_data.get("data", {})
        image_format = ImageFormat(task_data.get("format", "square"))
        
        template = self.infographic_templates.get(template_id)
        if not template:
            raise ValueError(f"Шаблон не найден: {template_id}")
        
        # Создаем инфографику на основе шаблона
        dimensions = self._get_format_dimensions(image_format)
        image = Image.new('RGB', dimensions, color='#ffffff')
        draw = ImageDraw.Draw(image)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = font_medium = font_small = ImageFont.load_default()
        
        # Заполняем текстовые области
        for text_area in template.text_areas:
            area_id = text_area["id"]
            if area_id in data:
                text = str(data[area_id])
                x, y = text_area["x"], text_area["y"]
                width, height = text_area["width"], text_area["height"]
                
                # Выбираем размер шрифта
                if text_area.get("font_size", 24) >= 40:
                    font = font_large
                elif text_area.get("font_size", 24) >= 30:
                    font = font_medium
                else:
                    font = font_small
                
                # Рисуем текст
                draw.text((x, y), text, fill='#333333', font=font)
        
        # Сохраняем изображение
        cache_key = f"infographic_{template_id}_{hashlib.md5(str(data).encode()).hexdigest()[:8]}"
        image_path = await self._save_generated_image(
            self._image_to_bytes(image), 
            cache_key, 
            image_format
        )
        
        generation_time = 1.0  # Заглушка
        file_size = os.path.getsize(image_path)
        
        return GeneratedImage(
            image_id=cache_key,
            image_path=str(image_path),
            image_url=None,
            format=image_format,
            content_type=ContentType.INFOGRAPHIC,
            prompt=f"Infographic: {template.name}",
            generation_time=generation_time,
            file_size=file_size,
            dimensions=dimensions
        )
    
    async def _create_carousel_post(self, task_data: Dict[str, Any]) -> List[GeneratedImage]:
        """Создает карусельный пост из нескольких изображений"""
        slides_data = task_data.get("slides", [])
        image_format = ImageFormat(task_data.get("format", "square"))
        
        generated_slides = []
        
        for i, slide_data in enumerate(slides_data):
            slide_data["format"] = image_format.value
            slide_data["content_type"] = "image"
            
            slide_image = await self._generate_image(slide_data)
            slide_image.content_type = ContentType.CAROUSEL_POST
            generated_slides.append(slide_image)
        
        return generated_slides
    
    async def _create_video_cover(self, task_data: Dict[str, Any]) -> GeneratedImage:
        """Создает обложку для видео"""
        title = task_data.get("title", "Video Title")
        description = task_data.get("description", "")
        image_format = ImageFormat(task_data.get("format", "horizontal"))
        
        # Создаем обложку с текстом
        dimensions = self._get_format_dimensions(image_format)
        image = Image.new('RGB', dimensions, color='#1a1a1a')
        draw = ImageDraw.Draw(image)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            font_desc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            font_title = font_desc = ImageFont.load_default()
        
        # Рисуем заголовок
        bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = bbox[2] - bbox[0]
        x = (dimensions[0] - text_width) // 2
        y = dimensions[1] // 2 - 50
        
        draw.text((x, y), title, fill='#ffffff', font=font_title)
        
        # Рисуем описание
        if description:
            bbox = draw.textbbox((0, 0), description, font=font_desc)
            text_width = bbox[2] - bbox[0]
            x = (dimensions[0] - text_width) // 2
            y += 100
            
            draw.text((x, y), description, fill='#cccccc', font=font_desc)
        
        # Сохраняем изображение
        cache_key = f"video_cover_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        image_path = await self._save_generated_image(
            self._image_to_bytes(image), 
            cache_key, 
            image_format
        )
        
        generation_time = 0.5  # Заглушка
        file_size = os.path.getsize(image_path)
        
        return GeneratedImage(
            image_id=cache_key,
            image_path=str(image_path),
            image_url=None,
            format=image_format,
            content_type=ContentType.VIDEO_COVER,
            prompt=f"Video cover: {title}",
            generation_time=generation_time,
            file_size=file_size,
            dimensions=dimensions
        )
    
    def _get_format_dimensions(self, image_format: ImageFormat) -> Tuple[int, int]:
        """Возвращает размеры для формата изображения"""
        dimensions = {
            ImageFormat.SQUARE: (1080, 1080),
            ImageFormat.VERTICAL: (1080, 1350),
            ImageFormat.HORIZONTAL: (1920, 1080),
            ImageFormat.CAROUSEL: (1080, 1080),
            ImageFormat.BANNER: (1200, 630)
        }
        return dimensions.get(image_format, (1080, 1080))
    
    def _generate_cache_key(self, prompt: str, image_format: ImageFormat, style: str) -> str:
        """Генерирует ключ кэша для изображения"""
        content = f"{prompt}_{image_format.value}_{style}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _get_cached_image(self, cache_key: str) -> Optional[GeneratedImage]:
        """Получает изображение из кэша"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    cache_data = json.loads(await f.read())
                
                # Проверяем TTL
                created_at = datetime.fromisoformat(cache_data["created_at"])
                if datetime.now() - created_at < self.cache_ttl:
                    return GeneratedImage(**cache_data)
                else:
                    # Удаляем устаревший кэш
                    cache_file.unlink()
                    if (self.cache_dir / f"{cache_key}.png").exists():
                        (self.cache_dir / f"{cache_key}.png").unlink()
            except Exception as e:
                logger.warning(f"Ошибка чтения кэша {cache_key}: {e}")
        
        return None
    
    async def _cache_image(self, cache_key: str, image: GeneratedImage):
        """Сохраняет изображение в кэш"""
        try:
            cache_data = {
                "image_id": image.image_id,
                "image_path": image.image_path,
                "image_url": image.image_url,
                "format": image.format.value,
                "content_type": image.content_type.value,
                "prompt": image.prompt,
                "generation_time": image.generation_time,
                "file_size": image.file_size,
                "dimensions": list(image.dimensions),
                "created_at": image.created_at.isoformat()
            }
            
            cache_file = self.cache_dir / f"{cache_key}.json"
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
                
        except Exception as e:
            logger.warning(f"Ошибка сохранения в кэш {cache_key}: {e}")
    
    async def _save_generated_image(self, image_data: bytes, cache_key: str, image_format: ImageFormat) -> Path:
        """Сохраняет сгенерированное изображение"""
        image_path = self.cache_dir / f"{cache_key}.png"
        
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(image_data)
        
        return image_path
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Конвертирует PIL Image в байты"""
        import io
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    async def optimize_image_for_platform(self, image_path: str, platform: str) -> str:
        """Оптимизирует изображение для конкретной платформы"""
        try:
            # Читаем исходное изображение
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            
            # Оптимизируем через MCP
            optimized_data = await self.mcp_manager.optimize_image_for_platform(
                image_data, platform
            )
            
            # Сохраняем оптимизированное изображение
            optimized_path = image_path.replace('.png', f'_optimized_{platform}.jpg')
            async with aiofiles.open(optimized_path, 'wb') as f:
                await f.write(optimized_data)
            
            logger.info(f"Изображение оптимизировано для {platform}: {optimized_path}")
            return optimized_path
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации изображения: {e}")
            return image_path  # Возвращаем оригинал при ошибке
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных шаблонов"""
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "format": template.format.value,
                "layout_type": template.layout_type
            }
            for template in self.infographic_templates.values()
        ]
    
    def get_platform_formats(self) -> Dict[str, str]:
        """Возвращает форматы изображений для платформ"""
        return {platform: format.value for platform, format in self.platform_formats.items()}
    
    async def search_stock_images(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Ищет стоковые изображения"""
        return await self.mcp_manager.search_stock_images(query, count)
    
    async def _find_stock_image(self, task_data: Dict[str, Any]) -> GeneratedImage:
        """Находит и загружает стоковое изображение для поста"""
        import uuid
        import aiofiles
        from urllib.parse import urlparse
        
        search_query = task_data.get("search_query", task_data.get("prompt", ""))
        brief_id = task_data.get("brief_id", "")
        user_id = task_data.get("user_id")
        image_format = ImageFormat(task_data.get("image_format", "square"))
        
        logger.info(f"Поиск стокового изображения для запроса: {search_query}")
        
        # Ищем изображения через Unsplash
        stock_images = await self.search_stock_images(search_query, count=5)
        
        if not stock_images:
            logger.warning(f"Стоковые изображения не найдены для запроса: {search_query}")
            raise Exception(f"Не удалось найти стоковое изображение для запроса: {search_query}")
        
        # Берем первое подходящее изображение
        selected_image = stock_images[0]
        image_url = selected_image.get("urls", {}).get("regular") or selected_image.get("url", "")
        
        if not image_url:
            logger.error(f"URL изображения не найден в ответе Unsplash: {selected_image}")
            raise Exception("URL изображения не найден")
        
        # Загружаем изображение
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка загрузки изображения: {response.status}")
                image_data = await response.read()
        
        # Сохраняем изображение
        image_id = str(uuid.uuid4())
        cache_key = f"stock_{brief_id}_{hash(search_query)}"
        image_path = await self._save_generated_image(image_data, cache_key, ImageFormat.SQUARE)
        
        # Получаем размеры изображения
        with Image.open(image_path) as img:
            dimensions = img.size
        
        generated_image = GeneratedImage(
            image_id=image_id,
            image_path=str(image_path),
            image_url=image_url,
            format=image_format,
            content_type=ContentType.IMAGE,
            prompt=search_query,
            generation_time=0.0,  # Поиск быстрый
            file_size=len(image_data),
            dimensions=dimensions
        )
        
        # Кэшируем результат
        await self._cache_image(cache_key, generated_image)
        
        logger.info(f"✅ Стоковое изображение найдено и сохранено: {image_path}")
        return generated_image
    
    async def create_image_batch(
        self, 
        requests: List[ImageGenerationRequest]
    ) -> List[GeneratedImage]:
        """Создает пакет изображений асинхронно"""
        tasks = []
        for request in requests:
            task_data = {
                "prompt": request.prompt,
                "content_type": request.content_type.value,
                "format": request.format.value,
                "style": request.style or "professional"
            }
            tasks.append(self._generate_image(task_data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        successful_results = []
        for result in results:
            if isinstance(result, GeneratedImage):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ошибка в пакетной генерации: {result}")
        
        return successful_results
