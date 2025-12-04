"""
Сервис для AI-анализа ссылок (сайты + Telegram каналы)
Извлекает контент из ссылок и генерирует рекомендации через AI
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkAnalysisService:
    """Сервис для анализа ссылок и генерации рекомендаций"""

    def __init__(self):
        self.website_cache = {}  # Кеш для парсинга сайтов (URL -> {content, timestamp})
        self.cache_ttl = timedelta(hours=24)  # TTL для кеша - 24 часа
        self.request_timeout = 5  # Таймаут для HTTP запросов - 5 секунд

    async def analyze_links(
        self,
        website_url: Optional[str] = None,
        telegram_links: List[str] = None
    ) -> Dict[str, Any]:
        """
        Анализирует ссылки и генерирует рекомендации

        Args:
            website_url: URL сайта для анализа
            telegram_links: Список ссылок на Telegram каналы

        Returns:
            Dict с рекомендациями
        """
        try:
            logger.info(f"🔍 Начинаем анализ: сайт={website_url}, telegram={len(telegram_links or [])} каналов")

            # Собираем данные из всех источников
            website_content = None
            telegram_content = []

            # 1. Парсим сайт (если указан)
            if website_url:
                website_content = await self._parse_website(website_url)
                logger.info(f"✅ Сайт спарсен: {len(website_content.get('text', ''))} символов")

            # 2. Анализируем Telegram каналы (если указаны)
            if telegram_links:
                telegram_content = await self._analyze_telegram_channels(telegram_links)
                logger.info(f"✅ Telegram каналов проанализировано: {len(telegram_content)}")

            # 3. Генерируем рекомендации через AI
            analysis_result = await self._generate_ai_recommendations(
                website_content=website_content,
                telegram_content=telegram_content
            )

            logger.info(f"✅ AI-анализ завершен: ниша={analysis_result.get('suggestedNiche')}")

            return {
                "analysis": analysis_result
            }

        except Exception as e:
            logger.error(f"❌ Ошибка анализа ссылок: {e}", exc_info=True)
            raise

    async def _parse_website(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Парсит сайт с кешированием и таймаутом

        Args:
            url: URL сайта

        Returns:
            Dict с контентом сайта или None при ошибке
        """
        try:
            # Проверяем кеш
            if url in self.website_cache:
                cached = self.website_cache[url]
                cache_age = datetime.now() - cached['timestamp']
                if cache_age < self.cache_ttl:
                    logger.info(f"📦 Используем кешированный контент сайта (возраст: {cache_age})")
                    return cached['content']

            logger.info(f"🌐 Парсим сайт: {url}")

            # Делаем HTTP запрос с таймаутом
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Сайт вернул статус {response.status}")
                        return None

                    html = await response.text()

            # Парсим HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Удаляем скрипты и стили
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Извлекаем текст
            text = soup.get_text(separator=' ', strip=True)

            # Очищаем от лишних пробелов
            text = re.sub(r'\s+', ' ', text).strip()

            # Ограничиваем длину (первые 3000 символов)
            text = text[:3000] if len(text) > 3000 else text

            # Извлекаем метатеги
            title = soup.title.string if soup.title else None
            meta_description = None
            meta_keywords = None

            for meta in soup.find_all('meta'):
                if meta.get('name') == 'description':
                    meta_description = meta.get('content')
                elif meta.get('name') == 'keywords':
                    meta_keywords = meta.get('content')

            content = {
                'url': url,
                'title': title,
                'description': meta_description,
                'keywords': meta_keywords,
                'text': text
            }

            # Кешируем результат
            self.website_cache[url] = {
                'content': content,
                'timestamp': datetime.now()
            }

            return content

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Таймаут при парсинге сайта: {url}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга сайта {url}: {e}")
            return None

    async def _analyze_telegram_channels(self, telegram_links: List[str]) -> List[Dict[str, Any]]:
        """
        Анализирует Telegram каналы

        Args:
            telegram_links: Список ссылок на каналы

        Returns:
            Список с информацией о каналах
        """
        results = []

        for link in telegram_links:
            try:
                # Извлекаем username канала из ссылки
                username = self._extract_telegram_username(link)
                if not username:
                    logger.warning(f"⚠️ Не удалось извлечь username из: {link}")
                    continue

                # Здесь можно добавить логику получения информации через TelegramMCP
                # Но для первой версии возвращаем базовую информацию
                results.append({
                    'username': username,
                    'link': link,
                    'accessible': False  # Пока не можем проверить доступность
                })

            except Exception as e:
                logger.warning(f"⚠️ Ошибка анализа Telegram канала {link}: {e}")
                continue

        return results

    def _extract_telegram_username(self, link: str) -> Optional[str]:
        """Извлекает username из Telegram ссылки"""
        # t.me/channel или @channel или https://t.me/channel
        if link.startswith('@'):
            return link[1:]

        # Регулярка для извлечения username
        match = re.search(r't\.me/([a-zA-Z0-9_]+)', link)
        if match:
            return match.group(1)

        return None

    async def _generate_ai_recommendations(
        self,
        website_content: Optional[Dict[str, Any]] = None,
        telegram_content: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерирует рекомендации через AI на основе собранных данных

        Args:
            website_content: Контент сайта
            telegram_content: Информация о Telegram каналах

        Returns:
            Dict с рекомендациями
        """
        try:
            # Формируем промпт для AI
            prompt_parts = []

            prompt_parts.append(
                "Проанализируй следующую информацию о бизнесе и дай рекомендации:\n"
            )

            # Добавляем информацию о сайте
            if website_content:
                prompt_parts.append("\n=== САЙТ ===")
                if website_content.get('title'):
                    prompt_parts.append(f"Заголовок: {website_content['title']}")
                if website_content.get('description'):
                    prompt_parts.append(f"Описание: {website_content['description']}")
                if website_content.get('keywords'):
                    prompt_parts.append(f"Ключевые слова: {website_content['keywords']}")
                if website_content.get('text'):
                    # Берем первые 1000 символов текста
                    text_preview = website_content['text'][:1000]
                    prompt_parts.append(f"Контент сайта: {text_preview}")

            # Добавляем информацию о Telegram каналах
            if telegram_content and len(telegram_content) > 0:
                prompt_parts.append("\n=== TELEGRAM КАНАЛЫ ===")
                for channel in telegram_content:
                    prompt_parts.append(f"Канал: {channel.get('username', 'N/A')}")

            prompt_parts.append(
                "\n=== ЗАДАЧА ===\n"
                "На основе этой информации определи:\n"
                "1. Нишу бизнеса (1-2 предложения, конкретно)\n"
                "2. Целевую аудиторию (1-2 предложения, кто именно)\n"
                "3. Типы бизнеса (выбери из: product, service, education, consulting)\n"
                "4. Бизнес-цели (выбери из: creating_posts, engagement, lead_processing, sales, growth)\n"
                "5. Призывы к действию (выбери из: consultation, purchase, subscribe, read_more)\n"
                "6. Тональность (выбери из: professional, friendly, casual, expert)\n"
                "7. Обоснование (2-3 предложения, почему именно такие рекомендации)\n\n"
                "Отвечай в формате JSON:\n"
                "{\n"
                '  "niche": "...",\n'
                '  "audience": "...",\n'
                '  "businessTypes": ["..."],\n'
                '  "goals": ["..."],\n'
                '  "cta": ["..."],\n'
                '  "tone": "...",\n'
                '  "reasoning": "..."\n'
                "}"
            )

            prompt = "\n".join(prompt_parts)

            # Генерируем рекомендации через Vertex AI
            from app.mcp.integrations.vertex_ai import VertexAIMCP
            from app.mcp.config import is_mcp_enabled

            if is_mcp_enabled('vertex_ai'):
                logger.info("🤖 Vertex AI доступен, вызываем generate_content")
                vertex_ai = VertexAIMCP()
                response = await vertex_ai.generate_content(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=1000
                )

                logger.info(f"🔍 Vertex AI ответ: success={response.success}, data={bool(response.data)}")

                if response.success and response.data:
                    import json
                    ai_text = response.data.get('generated_text', '{}')
                    logger.info(f"📝 AI текст получен: {len(ai_text)} символов")

                    # Пытаемся извлечь JSON из ответа
                    try:
                        # Ищем JSON в ответе (между { и })
                        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                        if json_match:
                            ai_data = json.loads(json_match.group(0))

                            logger.info(f"✅ AI рекомендации успешно получены: {ai_data.get('niche')}")
                            return {
                                'suggestedNiche': ai_data.get('niche'),
                                'suggestedAudience': ai_data.get('audience'),
                                'suggestedBusinessTypes': ai_data.get('businessTypes', []),
                                'suggestedGoals': ai_data.get('goals', []),
                                'suggestedCta': ai_data.get('cta', []),
                                'tone': ai_data.get('tone'),
                                'reasoning': ai_data.get('reasoning')
                            }
                        else:
                            logger.warning(f"⚠️ JSON не найден в ответе AI. Ответ: {ai_text[:200]}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Не удалось распарсить JSON из AI ответа: {e}")
                        logger.warning(f"AI текст был: {ai_text[:200]}")
                else:
                    logger.warning(f"⚠️ Vertex AI вернул ошибку или пустой ответ")
                    if hasattr(response, 'error'):
                        logger.error(f"Ошибка Vertex AI: {response.error}")
            else:
                logger.warning("⚠️ Vertex AI не включен в конфигурации")

            # Fallback: возвращаем базовые рекомендации
            logger.warning("⚠️ AI не доступен, возвращаем базовые рекомендации")
            return self._get_fallback_recommendations(website_content)

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI рекомендаций: {e}", exc_info=True)
            return self._get_fallback_recommendations(website_content)

    def _get_fallback_recommendations(
        self,
        website_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Возвращает базовые рекомендации без AI"""

        niche = "Онлайн-бизнес"
        audience = "Широкая аудитория, заинтересованная в вашем продукте или услуге"

        # Если есть контент сайта - пытаемся извлечь базовую информацию
        if website_content:
            title = website_content.get('title', '')
            description = website_content.get('description', '')
            text = website_content.get('text', '')

            # Простая эвристика для определения ниши
            combined_text = f"{title} {description} {text}".lower()

            if any(word in combined_text for word in ['видеонаблюдение', 'камер', 'охран']):
                niche = "Системы видеонаблюдения и безопасности"
                audience = "Владельцы частных домов и коммерческой недвижимости"
            elif any(word in combined_text for word in ['образование', 'обучение', 'курс']):
                niche = "Онлайн-образование"
                audience = "Люди, желающие получить новые знания и навыки"
            elif any(word in combined_text for word in ['консультац', 'услуг', 'сервис']):
                niche = "Консалтинговые услуги"
                audience = "Бизнес и частные лица, нуждающиеся в профессиональной помощи"

        return {
            'suggestedNiche': niche,
            'suggestedAudience': audience,
            'suggestedBusinessTypes': ['service'],
            'suggestedGoals': ['creating_posts', 'lead_processing'],
            'suggestedCta': ['consultation'],
            'tone': 'professional',
            'reasoning': 'Рекомендации основаны на базовом анализе предоставленных данных. Для более точных рекомендаций требуется AI-анализ.'
        }
