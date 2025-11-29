"""
Сервис для анализа изображений через AI
Использует OpenAI GPT-4 Vision для описания изображений
"""

import os
import logging
from typing import Dict, Any, List, Optional
import base64

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class VisionService:
    """Сервис для AI анализа изображений"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - Vision Service will not work")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Шаблоны промптов
        self.prompts = {
            "describe": """Опиши это изображение детально на русском языке.
Укажи:
- Что изображено на фото
- Настроение и атмосферу
- Основные объекты и люди
- Подходящий контекст использования

Будь кратким но информативным.""",
            
            "caption": """Создай короткую подпись для этого изображения (1-2 предложения) на русском языке.
Подпись должна быть:
- Цепляющей
- Описательной
- Подходящей для соцсетей""",
            
            "safety": """Проанализируй это изображение на предмет безопасности контента.
Проверь наличие:
- Неприемлемого контента (насилие, NSFW)
- Оскорбительных элементов
- Спам или фейковый контент

Ответь в формате JSON:
{
  "safe": true/false,
  "flags": ["список проблем если есть"],
  "confidence": 0.0-1.0
}""",
            
            "objects": """Перечисли все основные объекты на этом изображении.
Ответь списком на русском языке, через запятую.
Только объекты, без описаний.""",
            
            "mood": """Определи настроение этого изображения одним словом на русском:
professional, casual, happy, serious, energetic, calm, creative, minimal"""
        }
    
    async def analyze_image(
        self,
        image_url: str,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Анализирует изображение через GPT-4 Vision
        
        Args:
            image_url: URL изображения
            analysis_type: Тип анализа (full, describe, caption, safety)
        
        Returns:
            Dict с результатами анализа
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }
        
        try:
            if analysis_type == "full":
                # Полный анализ - все в одном запросе
                return await self._full_analysis(image_url)
            elif analysis_type in self.prompts:
                # Специфический анализ
                return await self._single_analysis(image_url, analysis_type)
            else:
                return {
                    "success": False,
                    "error": f"Unknown analysis type: {analysis_type}"
                }
        
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _full_analysis(self, image_url: str) -> Dict[str, Any]:
        """Полный анализ изображения"""
        
        prompt = """Проанализируй это изображение и предоставь:

1. ОПИСАНИЕ: Детальное описание того, что изображено (2-3 предложения)
2. ОБЪЕКТЫ: Список основных объектов через запятую
3. НАСТРОЕНИЕ: Одно слово - настроение изображения (professional/casual/happy/serious/energetic/calm)
4. ПОДПИСЬ: Короткая цепляющая подпись для соцсетей (1 предложение)
5. ИСПОЛЬЗОВАНИЕ: Где лучше использовать это изображение (header/thumbnail/content/background)
6. БЕЗОПАСНОСТЬ: Безопасно ли для публикации (да/нет)

Отвечай на русском языке в точно таком формате:
ОПИСАНИЕ: ...
ОБЪЕКТЫ: ...
НАСТРОЕНИЕ: ...
ПОДПИСЬ: ...
ИСПОЛЬЗОВАНИЕ: ...
БЕЗОПАСНОСТЬ: ..."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Используем более быструю модель
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Парсим ответ
        content = response.choices[0].message.content
        parsed = self._parse_full_analysis(content)
        
        return {
            "success": True,
            "image_url": image_url,
            "analysis": parsed,
            "raw_response": content,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }
    
    def _parse_full_analysis(self, content: str) -> Dict[str, Any]:
        """Парсит результат полного анализа"""
        lines = content.split('\n')
        result = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'описание' in key or 'description' in key:
                    result['description'] = value
                elif 'объекты' in key or 'objects' in key:
                    result['objects'] = [obj.strip() for obj in value.split(',')]
                elif 'настроение' in key or 'mood' in key:
                    result['mood'] = value
                elif 'подпись' in key or 'caption' in key:
                    result['caption'] = value
                elif 'использование' in key or 'usage' in key:
                    result['suggested_use'] = value
                elif 'безопасность' in key or 'safety' in key:
                    result['safe'] = 'да' in value.lower() or 'yes' in value.lower()
        
        return result
    
    async def _single_analysis(self, image_url: str, analysis_type: str) -> Dict[str, Any]:
        """Выполняет специфический тип анализа"""
        
        prompt = self.prompts[analysis_type]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        
        return {
            "success": True,
            "image_url": image_url,
            "type": analysis_type,
            "result": content,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }
    
    async def batch_analyze(
        self,
        image_urls: List[str],
        analysis_type: str = "describe"
    ) -> List[Dict[str, Any]]:
        """
        Анализирует несколько изображений
        
        Args:
            image_urls: Список URL изображений
            analysis_type: Тип анализа для всех изображений
        
        Returns:
            Список результатов анализа
        """
        results = []
        
        for image_url in image_urls:
            try:
                result = await self.analyze_image(image_url, analysis_type)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze image {image_url}: {e}")
                results.append({
                    "success": False,
                    "image_url": image_url,
                    "error": str(e)
                })
        
        return results
    
    async def generate_alt_text(self, image_url: str) -> str:
        """
        Генерирует alt text для изображения (для доступности)
        
        Args:
            image_url: URL изображения
        
        Returns:
            Alt text
        """
        result = await self._single_analysis(image_url, "describe")
        
        if result.get("success"):
            # Берем первое предложение как alt text
            description = result.get("result", "")
            alt_text = description.split('.')[0] if description else "Изображение"
            return alt_text
        
        return "Изображение"
    
    async def suggest_hashtags(self, image_url: str, count: int = 5) -> List[str]:
        """
        Предлагает хэштеги для изображения
        
        Args:
            image_url: URL изображения
            count: Количество хэштегов
        
        Returns:
            Список хэштегов
        """
        if not self.client:
            return []
        
        try:
            prompt = f"""Предложи {count} релевантных хэштегов для этого изображения.
Хэштеги должны быть:
- На русском языке
- Популярными и трендовыми
- Релевантными контенту

Ответь только хэштеги через запятую, с символом #"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            
            # Парсим хэштеги
            hashtags = [tag.strip() for tag in content.split(',')]
            hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
            
            return hashtags[:count]
        
        except Exception as e:
            logger.error(f"Failed to suggest hashtags: {e}")
            return []


# Singleton instance
_vision_service = None


def get_vision_service() -> VisionService:
    """Получить singleton instance Vision Service"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service

