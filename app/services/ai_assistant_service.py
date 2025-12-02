"""
AI Assistant Service для помощи в заполнении опросника и настроек проекта
Анализирует ресурсы (сайты, телеграм-каналы) и извлекает информацию
"""

import logging
import json
import requests
from typing import Dict, Optional, Any
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)


class AIAssistantService:
    """Сервис для помощи в заполнении опросника через анализ ресурсов"""
    
    def __init__(self, openai_client=None):
        """Инициализация с OpenAI клиентом"""
        if not openai_client:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEY not set, AI analysis will be disabled")
                self.openai_client = None
        else:
            self.openai_client = openai_client
    
    def detect_resource_type(self, url: str) -> str:
        """Определяет тип ресурса по URL"""
        url_lower = url.lower()
        if 't.me' in url_lower or 'telegram' in url_lower:
            return 'telegram'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'vk.com' in url_lower:
            return 'vk'
        else:
            return 'website'
    
    async def fetch_resource_content(self, url: str, resource_type: str) -> Dict[str, Any]:
        """
        Получает контент ресурса для анализа
        
        Args:
            url: URL ресурса
            resource_type: Тип ресурса (website, telegram, instagram)
        
        Returns:
            Словарь с контентом для анализа
        """
        try:
            if resource_type == 'website':
                # Для сайтов получаем HTML
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                return {
                    'type': 'html',
                    'content': response.text,
                    'url': url
                }
            elif resource_type == 'telegram':
                # Для Telegram пока возвращаем URL (в будущем можно парсить через API)
                return {
                    'type': 'telegram',
                    'url': url,
                    'content': f'Telegram канал: {url}'
                }
            else:
                return {
                    'type': resource_type,
                    'url': url,
                    'content': f'Ресурс: {url}'
                }
        except Exception as e:
            logger.error(f"Ошибка получения контента из {url}: {e}")
            return {
                'type': resource_type,
                'url': url,
                'content': '',
                'error': str(e)
            }
    
    def _clean_html(self, html: str) -> str:
        """Очистка HTML от скриптов и стилей"""
        import re
        # Удаляем скрипты
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Удаляем стили
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Удаляем комментарии
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        # Удаляем множественные пробелы
        html = re.sub(r'\s+', ' ', html)
        return html.strip()
    
    async def analyze_for_project_settings(
        self,
        resource_content: Dict[str, Any],
        resource_type: str
    ) -> Dict[str, Any]:
        """
        Анализирует ресурс специально для заполнения настроек проекта
        
        Извлекает:
        - Ниша и продукт/услуга
        - Целевая аудитория
        - Основные боли
        - Стиль контента
        - CTA
        - Ключевые слова
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, returning empty analysis")
            return {}
        
        try:
            # Подготавливаем контент для анализа
            content = resource_content.get('content', '')
            if resource_content.get('type') == 'html':
                content = self._clean_html(content)
                # Ограничиваем размер
                if len(content) > 10000:
                    content = content[:10000] + "..."
            
            url = resource_content.get('url', '')
            
            prompt = f"""
Проанализируй этот ресурс и извлеки информацию для создания контента в социальных сетях.

URL: {url}
Тип ресурса: {resource_type}
Контент: {content[:5000] if len(content) > 5000 else content}

Извлеки следующую информацию в формате JSON:

{{
  "product_service": "Краткое описание ниши и главного продукта/услуги (1-2 предложения)",
  "target_audience": "Описание целевой аудитории: возраст, профессия, мотивация (2-3 предложения)",
  "pain_points": ["Основная боль 1", "Основная боль 2", "Основная боль 3"],
  "tone": "Тон контента: professional/casual/friendly/authoritative",
  "cta": "Призыв к действию по умолчанию (например: 'Оставить заявку', 'Подписаться на канал')",
  "keywords": ["ключевое слово 1", "ключевое слово 2", "ключевое слово 3"],
  "hashtags": ["#хештег1", "#хештег2"],
  "brand_name": "Название бренда/компании",
  "brand_description": "Краткое описание бренда (1-2 предложения)"
}}

Отвечай ТОЛЬКО валидным JSON, без дополнительных комментариев.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Успешно проанализирован ресурс {url}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа от AI: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка анализа ресурса: {e}")
            return {}
    
    async def analyze_for_survey(
        self,
        resource_content: Dict[str, Any],
        resource_type: str,
        question_type: str
    ) -> Dict[str, Any]:
        """
        Анализирует ресурс для помощи в конкретном вопросе опросника
        
        Args:
            resource_content: Контент ресурса
            resource_type: Тип ресурса
            question_type: Тип вопроса (niche, audience, pain_points, etc)
        """
        if not self.openai_client:
            return {}
        
        try:
            content = resource_content.get('content', '')
            if resource_content.get('type') == 'html':
                content = self._clean_html(content)
                if len(content) > 5000:
                    content = content[:5000] + "..."
            
            url = resource_content.get('url', '')
            
            # Адаптируем промпт под тип вопроса
            question_prompts = {
                'niche': 'Извлеки информацию о нише бизнеса и главном продукте/услуге. Ответь 1-2 предложениями.',
                'audience': 'Определи целевую аудиторию: возраст, профессия, мотивация. Ответь 2-3 предложениями.',
                'pain_points': 'Определи основные проблемы и боли целевой аудитории. Перечисли 3-5 пунктов.',
                'tone': 'Определи стиль и тон контента (professional/casual/friendly/authoritative). Ответь одним словом.',
                'cta': 'Определи призыв к действию, который используется. Ответь короткой фразой.',
            }
            
            prompt_text = question_prompts.get(question_type, 'Извлеки релевантную информацию.')
            
            prompt = f"""
Проанализируй этот ресурс и ответь на вопрос:

{prompt_text}

URL: {url}
Контент: {content[:3000] if len(content) > 3000 else content}

Ответь кратко и по делу на русском языке.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            answer = response.choices[0].message.content.strip()
            return {'answer': answer}
            
        except Exception as e:
            logger.error(f"Ошибка анализа для опросника: {e}")
            return {}

