"""
AI Assistant Service для помощи в заполнении опросника и настроек проекта
Анализирует ресурсы (сайты, телеграм-каналы) и извлекает информацию
"""

import logging
import json
import requests
import re
from html import unescape
from typing import Dict, Optional, Any, List
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
    
    def _parse_telegram_channel_posts(self, url: str, max_posts: int = 20) -> List[str]:
        """
        Парсит последние посты из публичного Telegram канала через веб-скрапинг
        
        Args:
            url: URL канала (например, https://t.me/Go_Investing)
            max_posts: Максимальное количество постов для парсинга
        
        Returns:
            Список текстов постов
        """
        try:
            # Извлекаем username канала из URL
            username_match = re.search(r't\.me/([a-zA-Z0-9_]+)', url)
            if not username_match:
                logger.warning(f"Не удалось извлечь username из URL: {url}")
                return []
            
            username = username_match.group(1)
            channel_url = f"https://t.me/s/{username}"
            
            logger.info(f"Парсинг постов из Telegram канала: {channel_url}")
            
            # Загружаем HTML страницы канала
            response = requests.get(channel_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
            })
            response.raise_for_status()
            
            html = response.text
            
            # Ищем посты в HTML - Telegram использует определенную структуру
            # Посты обычно в div с классом tgme_widget_message или в структуре с data-post
            posts = []
            
            # Метод 1: Ищем JSON данные в скриптах (Telegram загружает данные через JS)
            json_pattern = r'window\.__initialData__\s*=\s*({.+?});'
            json_match = re.search(json_pattern, html, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Извлекаем посты из JSON структуры
                    # Структура может быть разной, пробуем разные пути
                    messages = []
                    if 'messages' in data:
                        messages = data['messages']
                    elif 'posts' in data:
                        messages = data['posts']
                    elif isinstance(data, dict):
                        # Ищем вложенные структуры
                        for key in ['messages', 'posts', 'items']:
                            if key in data and isinstance(data[key], list):
                                messages = data[key]
                                break
                    
                    for msg in messages[:max_posts]:
                        if isinstance(msg, dict):
                            # Извлекаем текст поста
                            text = msg.get('message', '') or msg.get('text', '') or msg.get('content', '')
                            if text and text.strip():
                                # Очищаем от HTML тегов если есть
                                text = re.sub(r'<[^>]+>', '', text)
                                posts.append(text.strip())
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Ошибка парсинга JSON данных: {e}")
            
            # Метод 2: Если JSON не сработал, парсим HTML напрямую
            if not posts:
                # Ищем div с сообщениями - Telegram использует класс tgme_widget_message_text
                # Улучшенный паттерн: ищем полную структуру сообщения
                post_pattern = r'<div[^>]*class="[^"]*tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
                post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
                
                logger.info(f"Найдено {len(post_matches)} совпадений по паттерну tgme_widget_message_text")
                
                for match in post_matches[:max_posts]:
                    # Очищаем от HTML тегов
                    text = re.sub(r'<[^>]+>', '', match)
                    # Декодируем HTML entities
                    text = unescape(text)
                    # Заменяем множественные пробелы на один
                    text = re.sub(r'\s+', ' ', text).strip()
                    # Убираем пустые строки и очень короткие тексты
                    if text and len(text) > 10:  # Минимум 10 символов
                        posts.append(text)
                        logger.debug(f"Извлечен пост длиной {len(text)} символов: {text[:100]}...")
            
            # Метод 3: Альтернативный паттерн - ищем структуру с data-post
            if not posts:
                logger.info("Пробуем альтернативный паттерн data-post")
                post_pattern = r'data-post="[^"]*"[^>]*>.*?<div[^>]*class="[^"]*message[^"]*"[^>]*>(.*?)</div>'
                post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
                
                logger.info(f"Найдено {len(post_matches)} совпадений по паттерну data-post")
                
                for match in post_matches[:max_posts]:
                    text = re.sub(r'<[^>]+>', '', match)
                    text = unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text and len(text) > 10:
                        posts.append(text)
            
            # Метод 4: Если ничего не нашли, пробуем более широкий поиск
            if not posts:
                logger.warning("Стандартные паттерны не сработали, пробуем широкий поиск")
                # Ищем любые div с классом содержащим "message"
                wide_pattern = r'<div[^>]*class="[^"]*message[^"]*"[^>]*>(.*?)</div>'
                wide_matches = re.findall(wide_pattern, html, re.DOTALL | re.IGNORECASE)
                
                logger.info(f"Найдено {len(wide_matches)} совпадений по широкому паттерну")
                
                for match in wide_matches[:max_posts * 2]:  # Берем больше, потом отфильтруем
                    text = re.sub(r'<[^>]+>', '', match)
                    text = unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    # Более строгая фильтрация для широкого поиска
                    if text and len(text) > 50:  # Минимум 50 символов для широкого поиска
                        posts.append(text)
                        if len(posts) >= max_posts:
                            break
            
            logger.info(f"✅ Извлечено {len(posts)} постов из канала {username}")
            return posts[:max_posts]
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка при загрузке Telegram канала {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка парсинга Telegram канала {url}: {e}", exc_info=True)
            return []
    
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
                # Для сайтов получаем HTML с таймаутом 5 секунд
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                return {
                    'type': 'html',
                    'content': response.text,
                    'url': url
                }
            elif resource_type == 'telegram':
                # Парсим посты из Telegram канала
                posts = self._parse_telegram_channel_posts(url, max_posts=20)
                
                if posts:
                    # Объединяем посты в один текст для анализа
                    posts_text = "\n\n---\n\n".join(posts)
                    logger.info(f"✅ Получено {len(posts)} постов из Telegram канала {url}")
                    return {
                        'type': 'telegram',
                        'url': url,
                        'content': f'Последние посты из Telegram канала:\n\n{posts_text}',
                        'posts_count': len(posts)
                    }
                else:
                    # Если не удалось получить посты, возвращаем базовую информацию
                    logger.warning(f"⚠️ Не удалось получить посты из Telegram канала {url}, используем базовую информацию")
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
        except requests.exceptions.Timeout:
            logger.warning(f"Таймаут при получении контента из {url}")
            return {
                'type': resource_type,
                'url': url,
                'content': '',
                'error': 'Timeout: сайт не ответил за 5 секунд'
            }
        except requests.exceptions.SSLError as e:
            logger.warning(f"Ошибка SSL при получении контента из {url}: {e}")
            return {
                'type': resource_type,
                'url': url,
                'content': '',
                'error': 'SSL Error: ошибка сертификата'
            }
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка запроса к {url}: {e}")
            return {
                'type': resource_type,
                'url': url,
                'content': '',
                'error': f'Request Error: {str(e)}'
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
    
    def _determine_business_types(self, analysis_data: Dict[str, Any]) -> List[str]:
        """
        Определяет типы бизнеса на основе анализа контента
        
        Args:
            analysis_data: Результат анализа с полями product_service, brand_description, insights
        
        Returns:
            Список ID типов бизнеса: ['product', 'service', 'personal_brand', 'company_brand']
        """
        business_types = []
        
        # Собираем весь текст для анализа
        text_to_analyze = ""
        if analysis_data.get('product_service'):
            text_to_analyze += analysis_data['product_service'].lower() + " "
        if analysis_data.get('brand_description'):
            text_to_analyze += analysis_data['brand_description'].lower() + " "
        if analysis_data.get('insights'):
            insights_text = " ".join([str(insight).lower() for insight in analysis_data['insights']])
            text_to_analyze += insights_text + " "
        if analysis_data.get('keywords'):
            keywords_text = " ".join([str(kw).lower() for kw in analysis_data['keywords']])
            text_to_analyze += keywords_text + " "
        
        text_to_analyze = text_to_analyze.lower()
        
        # Ключевые слова для каждого типа
        product_keywords = ['товар', 'продажа', 'магазин', 'купить', 'заказать товар', 'e-commerce', 
                           'интернет-магазин', 'товары', 'продукт для продажи', 'доставка товара']
        service_keywords = ['услуга', 'консультация', 'помощь', 'заказать услугу', 'сервис', 
                          'услуги', 'консультирование', 'помощь в', 'оказываем услуги']
        personal_brand_keywords = ['я', 'мой опыт', 'личный', 'эксперт', 'блогер', 'канал автора',
                                  'мой канал', 'личный бренд', 'я рекомендую', 'мой совет',
                                  'я считаю', 'по моему мнению', 'я думаю']
        company_brand_keywords = ['компания', 'бренд', 'корпоратив', 'бизнес', 'аналитика', 
                                'новости', 'корпоративный', 'компания предоставляет',
                                'наша компания', 'бизнес-аналитика']
        
        # Подсчитываем совпадения
        product_score = sum(1 for keyword in product_keywords if keyword in text_to_analyze)
        service_score = sum(1 for keyword in service_keywords if keyword in text_to_analyze)
        personal_score = sum(1 for keyword in personal_brand_keywords if keyword in text_to_analyze)
        company_score = sum(1 for keyword in company_brand_keywords if keyword in text_to_analyze)
        
        # Определяем типы (если score > 0, добавляем тип)
        if product_score > 0:
            business_types.append('product')
        if service_score > 0:
            business_types.append('service')
        if personal_score > 0:
            business_types.append('personal_brand')
        if company_score > 0:
            business_types.append('company_brand')
        
        # Если ничего не определили, используем дефолт
        if not business_types:
            # Пытаемся определить по контексту
            if 'канал' in text_to_analyze or 'telegram' in text_to_analyze:
                # Для Telegram каналов чаще всего personal_brand или company_brand
                business_types.append('personal_brand')
            else:
                # Дефолт для остальных случаев
                business_types.append('company_brand')
        
        logger.info(f"Определены типы бизнеса: {business_types} (scores: product={product_score}, service={service_score}, personal={personal_score}, company={company_score})")
        return business_types
    
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
        - Типы бизнеса
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
            
            # Для Telegram каналов контент может быть минимальным - добавляем специальную обработку
            if resource_type == 'telegram' and (not content or content.startswith('Telegram канал:')):
                # Извлекаем username из URL
                channel_username = url.split('/')[-1].replace('@', '')
                content = f"Telegram канал: {channel_username}. Для полного анализа необходимо получить посты из канала. Проанализируй на основе названия канала и URL."
                logger.info(f"Telegram канал с минимальным контентом: {url}, username: {channel_username}")
            
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
  "brand_description": "Краткое описание бренда (1-2 предложения)",
  "insights": [
    "О чём аудитория говорит чаще всего (темы, вопросы, обсуждения)",
    "Какие темы вызывают эмоции (страх, радость, интерес, беспокойство)",
    "Какие формулировки аудитория использует сама (язык, термины, выражения)",
    "Что они хотят, но прямо не говорят (скрытые потребности, невысказанные желания)"
  ]
}}

ВАЖНО для insights:
- Пиши конкретно, как живой человек, а не как отчёт
- Используй формулировки, которые аудитория использует сама
- Фокусируйся на эмоциях и смыслах, а не на сухих фактах
- Пример хорошего инсайта: "Аудитория боится потерять деньги, но не говорит об этом прямо"
- Пример плохого инсайта: "Целевая аудитория имеет финансовые риски"

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
            
            # Определяем типы бизнеса на основе анализа
            suggested_business_types = self._determine_business_types(result)
            result['suggestedBusinessTypes'] = suggested_business_types
            
            logger.info(f"Успешно проанализирован ресурс {url}, определены типы бизнеса: {suggested_business_types}")
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
    
    async def recommend_tone(
        self,
        business_type: list,
        niche: str,
        answers: list,
        website_url: Optional[str] = None,
        telegram_links: Optional[list] = None,
        selected_post_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Генерирует рекомендацию тональности на основе анализа данных пользователя
        
        Args:
            business_type: Массив типов бизнеса (product, service, personal_brand, company_brand)
            niche: Ниша бизнеса
            answers: Массив ответов на вопросы опросника
            website_url: URL сайта (опционально)
            telegram_links: Массив ссылок на Telegram каналы (опционально)
            selected_post_style: Выбранный стиль поста (опционально)
        
        Returns:
            Словарь с рекомендацией тональности
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, returning fallback recommendation")
            return self._fallback_tone_recommendation(business_type, niche, answers)
        
        try:
            # Собираем данные для анализа
            analysis_data = {
                'website_analysis': None,
                'telegram_analysis': None,
                'answers_analysis': self._analyze_answers(answers, business_type, niche)
            }
            
            # Анализ сайта (если указан)
            if website_url:
                try:
                    website_content = await self.fetch_resource_content(website_url, 'website')
                    if website_content.get('content') and not website_content.get('error'):
                        analysis_data['website_analysis'] = await self._analyze_website_tone(website_content)
                except Exception as e:
                    logger.warning(f"Ошибка анализа сайта {website_url}: {e}, продолжаем без него")
            
            # Анализ Telegram каналов (если указаны)
            if telegram_links and len(telegram_links) > 0:
                try:
                    telegram_posts = await self._fetch_telegram_posts(telegram_links)
                    if telegram_posts:
                        analysis_data['telegram_analysis'] = await self._analyze_telegram_tone(telegram_posts)
                except Exception as e:
                    logger.warning(f"Ошибка анализа Telegram каналов: {e}, продолжаем без них")
            
            # Генерируем рекомендацию через AI
            recommendation = await self._generate_tone_recommendation(analysis_data, selected_post_style)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендации тональности: {e}")
            return self._fallback_tone_recommendation(business_type, niche, answers)
    
    def _analyze_answers(self, answers: list, business_type: list, niche: str) -> Dict[str, Any]:
        """Анализирует ответы пользователя и извлекает ключевую информацию"""
        result = {
            'business_type': business_type,
            'niche': niche,
            'goals': [],
            'target_audience': None,
            'cta': None
        }
        
        for answer in answers:
            question_id = answer.get('questionId', '')
            answer_text = answer.get('answer', '')
            
            if 'goal' in question_id.lower() or 'цел' in question_id.lower():
                result['goals'].append(answer_text)
            elif 'audience' in question_id.lower() or 'аудитор' in question_id.lower():
                result['target_audience'] = answer_text
            elif 'cta' in question_id.lower() or 'призыв' in question_id.lower():
                result['cta'] = answer_text
        
        return result
    
    async def _analyze_website_tone(self, website_content: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует тональность контента сайта"""
        if not self.openai_client:
            return {}
        
        try:
            content = website_content.get('content', '')
            if website_content.get('type') == 'html':
                content = self._clean_html(content)
                if len(content) > 8000:
                    content = content[:8000] + "..."
            
            prompt = f"""
Проанализируй стиль написания на этом сайте и определи тональность контента.

Контент сайта: {content[:5000] if len(content) > 5000 else content}

Определи:
1. Формальность (формальный/неформальный)
2. Использование личных местоимений (мы, наша команда, я)
3. Наличие эмодзи или восклицательных знаков
4. Длина предложений (короткие/длинные)
5. Специфическая терминология (простая/экспертная)
6. Общий тон общения (professional/casual/friendly/expert)

ВАЖНО: Это анализ для сайта. Для Telegram постов нужен другой стиль - более живой и человеческий.

Ответь в формате JSON:
{{
  "formality": "formal/informal",
  "uses_personal_pronouns": true/false,
  "has_emojis": true/false,
  "sentence_length": "short/medium/long",
  "terminology": "simple/expert",
  "detected_tone": "professional/casual/friendly/expert/motivational/humorous",
  "reasoning": "Краткое объяснение (1-2 предложения)",
  "telegram_translation": "Рекомендация для Telegram: как адаптировать этот стиль для живых постов (1 предложение)"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа тональности сайта: {e}")
            return {}
    
    async def _fetch_telegram_posts(self, telegram_links: list) -> list:
        """
        Получает посты из Telegram каналов
        
        Примечание: Telegram Bot API не позволяет получать историю сообщений напрямую.
        Для публичных каналов можно использовать веб-скрапинг или другие методы.
        Пока возвращаем пустой список - в будущем можно реализовать через веб-скрапинг.
        """
        # TODO: Реализовать получение постов через веб-скрапинг t.me или другие методы
        # Для публичных каналов можно использовать библиотеки типа telethon или веб-скрапинг
        logger.info(f"Получение постов из Telegram каналов пока не реализовано: {telegram_links}")
        return []
    
    async def _analyze_telegram_tone(self, posts: list) -> Dict[str, Any]:
        """Анализирует тональность постов из Telegram каналов"""
        if not self.openai_client or not posts:
            return {}
        
        try:
            # Объединяем тексты постов
            posts_text = "\n\n".join([post.get('text', '') for post in posts[:20]])  # Берем последние 20 постов
            
            if len(posts_text) > 5000:
                posts_text = posts_text[:5000] + "..."
            
            prompt = f"""
Проанализируй стиль написания постов в Telegram канале и определи преобладающую тональность.

Посты из канала:
{posts_text}

Определи:
1. Преобладающий тон (professional/casual/friendly/expert/motivational/humorous)
2. Использование эмодзи
3. Длина постов (короткие/средние/длинные)
4. Стиль общения с аудиторией
5. Что делает посты живыми (конкретные приёмы, формулировки, структура)

Ответь в формате JSON:
{{
  "detected_tone": "professional/casual/friendly/expert/motivational/humorous",
  "uses_emojis": true/false,
  "post_length": "short/medium/long",
  "communication_style": "formal/informal/personal",
  "reasoning": "Краткое объяснение (1-2 предложения)",
  "what_makes_it_alive": "Конкретные приёмы, которые делают посты живыми (2-3 пункта)"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=400
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа тональности Telegram: {e}")
            return {}
    
    async def _generate_tone_recommendation(
        self,
        analysis_data: Dict[str, Any],
        selected_post_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """Генерирует финальную рекомендацию тональности через AI"""
        if not self.openai_client:
            return self._fallback_tone_recommendation(
                analysis_data.get('answers_analysis', {}).get('business_type', []),
                analysis_data.get('answers_analysis', {}).get('niche', ''),
                []
            )
        
        try:
            # Формируем промпт для AI
            website_info = ""
            if analysis_data.get('website_analysis'):
                website_analysis = analysis_data['website_analysis']
                website_info = f"""
Анализ сайта:
- Тональность: {website_analysis.get('detected_tone', 'не определена')}
- Формальность: {website_analysis.get('formality', 'не определена')}
- Объяснение: {website_analysis.get('reasoning', '')}
"""
            
            telegram_info = ""
            if analysis_data.get('telegram_analysis'):
                telegram_analysis = analysis_data['telegram_analysis']
                telegram_info = f"""
Анализ Telegram каналов:
- Тональность: {telegram_analysis.get('detected_tone', 'не определена')}
- Стиль общения: {telegram_analysis.get('communication_style', 'не определен')}
- Объяснение: {telegram_analysis.get('reasoning', '')}
"""
            
            answers = analysis_data.get('answers_analysis', {})
            business_type = answers.get('business_type', [])
            niche = answers.get('niche', '')
            goals = answers.get('goals', [])
            target_audience = answers.get('target_audience', '')
            cta = answers.get('cta', '')
            
            # Извлекаем информацию о переводе тональности для Telegram
            website_tone_translation = ""
            if analysis_data.get('website_analysis'):
                website_analysis = analysis_data['website_analysis']
                if website_analysis.get('telegram_translation'):
                    website_tone_translation = f"\nВАЖНО: {website_analysis['telegram_translation']}"
            
            prompt = f"""
Ты - эксперт по контент-маркетингу. Проанализируй данные и порекомендуй оптимальную тональность для Telegram постов.

Тип бизнеса: {', '.join(business_type) if business_type else 'не указан'}
Ниша: {niche}
Цели: {', '.join(goals) if goals else 'не указаны'}
Целевая аудитория: {target_audience if target_audience else 'не указана'}
Призыв к действию: {cta if cta else 'не указан'}
{website_info}
{telegram_info}
{website_tone_translation}
Выбранный стиль поста: {selected_post_style if selected_post_style else 'не выбран'}

ВАЖНО: Telegram посты должны быть живыми и человеческими, даже если сайт формальный.
Если сайт формальный → для Telegram рекомендовать "informal professional" (умный, но без канцелярита)
Если сайт экспертный → для Telegram рекомендовать "легкий экспертный тон" (знания без занудства)
Если сайт эмоциональный → для Telegram оставить эмоции, но убрать воду

Создай гибридный tone_profile вместо одного слова:

Ответь в формате JSON:
{{
  "suggestedTone": "professional/friendly/casual/expert/motivational/humorous",
  "tone_profile": {{
    "base": "expert/professional/friendly/casual/motivational/humorous",
    "flavor": "friendly/casual/professional/expert (дополнительный оттенок)",
    "rhythm": "short/medium/long (длина предложений)",
    "energy": "low/medium/high (энергетика текста)"
  }},
  "reasoning": "Краткое объяснение с конкретными фактами (максимум 200-300 символов)",
  "alternatives": ["expert", "friendly"]
}}

Пример tone_profile:
- base: "expert", flavor: "friendly", rhythm: "short", energy: "medium" → умный, ёмкий, без канцелярита, но и без TikTok-стиля
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Валидируем результат
            valid_tones = ['professional', 'friendly', 'casual', 'expert', 'motivational', 'humorous']
            if result.get('suggestedTone') not in valid_tones:
                result['suggestedTone'] = 'professional'
            
            # Валидируем и создаем tone_profile если его нет
            if not result.get('tone_profile') or not isinstance(result.get('tone_profile'), dict):
                # Создаем tone_profile на основе suggestedTone
                base_tone = result.get('suggestedTone', 'professional')
                result['tone_profile'] = {
                    'base': base_tone,
                    'flavor': 'friendly' if base_tone in ['professional', 'expert'] else base_tone,
                    'rhythm': 'short',  # Для Telegram рекомендуется short
                    'energy': 'medium'
                }
            else:
                # Валидируем поля tone_profile
                profile = result['tone_profile']
                valid_bases = ['professional', 'friendly', 'casual', 'expert', 'motivational', 'humorous']
                valid_flavors = ['friendly', 'casual', 'expert', 'professional']
                valid_rhythms = ['short', 'medium', 'long']
                valid_energies = ['low', 'medium', 'high']
                
                if profile.get('base') not in valid_bases:
                    profile['base'] = result.get('suggestedTone', 'professional')
                if profile.get('flavor') not in valid_flavors:
                    profile['flavor'] = 'friendly'
                if profile.get('rhythm') not in valid_rhythms:
                    profile['rhythm'] = 'short'
                if profile.get('energy') not in valid_energies:
                    profile['energy'] = 'medium'
            
            # Ограничиваем reasoning до 300 символов
            if result.get('reasoning'):
                result['reasoning'] = result['reasoning'][:300]
            
            return {
                'recommendation': result
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендации: {e}")
            return self._fallback_tone_recommendation(
                analysis_data.get('answers_analysis', {}).get('business_type', []),
                analysis_data.get('answers_analysis', {}).get('niche', ''),
                []
            )
    
    def _fallback_tone_recommendation(
        self,
        business_type: list,
        niche: str,
        answers: list
    ) -> Dict[str, Any]:
        """Fallback рекомендация на основе простой логики"""
        # Простая логика на основе типа бизнеса
        suggested_tone = 'professional'
        reasoning = "На основе вашего типа бизнеса рекомендуем профессиональный тон. Это универсальный выбор, который создает доверие у широкой аудитории."
        
        if business_type:
            if 'personal_brand' in business_type:
                suggested_tone = 'friendly'
                reasoning = "Для личного бренда рекомендуем дружелюбный тон. Это поможет создать более близкие отношения с аудиторией."
            elif 'service' in business_type and 'B2B' not in niche:
                suggested_tone = 'friendly'
                reasoning = "Для сервисного бизнеса в B2C нише рекомендуем дружелюбный тон для лучшего взаимодействия с клиентами."
        
        # Создаем tone_profile для fallback
        tone_profile = {
            'base': suggested_tone,
            'flavor': 'friendly' if suggested_tone in ['professional', 'expert'] else suggested_tone,
            'rhythm': 'short',
            'energy': 'medium'
        }
        
        return {
            'recommendation': {
                'suggestedTone': suggested_tone,
                'tone_profile': tone_profile,
                'reasoning': reasoning,
                'alternatives': ['expert', 'friendly'] if suggested_tone == 'professional' else ['professional', 'expert']
            }
        }
    
    async def generate_adaptive_questions(
        self,
        business_type: list,
        niche: str,
        previous_answers: list,
        parsed_resources: Optional[Dict[str, Any]] = None
    ) -> list:
        """
        Генерирует адаптивные вопросы на основе предыдущих ответов и проанализированных ресурсов
        
        Args:
            business_type: Массив типов бизнеса
            niche: Ниша бизнеса
            previous_answers: Массив предыдущих ответов
            parsed_resources: Результаты парсинга ресурсов (сайт, каналы)
        
        Returns:
            Массив вопросов с id, text, type, options
        """
        if not self.openai_client:
            # Fallback вопросы
            return [
                {'id': 'audience', 'text': 'Кто ваша целевая аудитория?', 'type': 'text', 'options': []},
                {'id': 'goals', 'text': 'Какие у вас бизнес-цели?', 'type': 'text', 'options': []},
                {'id': 'cta', 'text': 'Какой призыв к действию?', 'type': 'text', 'options': []}
            ]
        
        try:
            # Формируем контекст из предыдущих ответов
            context = f"Тип бизнеса: {', '.join(business_type)}\nНиша: {niche}\n"
            
            if previous_answers:
                context += "Предыдущие ответы:\n"
                for answer in previous_answers:
                    context += f"- {answer.get('questionId', '')}: {answer.get('answer', '')}\n"
            
            if parsed_resources:
                context += "\nПроанализированные ресурсы:\n"
                if parsed_resources.get('website'):
                    context += f"Сайт: {parsed_resources['website'].get('summary', '')[:200]}\n"
                if parsed_resources.get('telegram'):
                    context += f"Telegram: {parsed_resources['telegram'].get('summary', '')[:200]}\n"
            
            prompt = f"""
На основе следующей информации сгенерируй 1-2 следующих вопроса для опросника по созданию контента.

{context}

Сгенерируй вопросы, которые:
1. Логически следуют из предыдущих ответов
2. Помогают лучше понять бизнес и аудиторию
3. Не повторяют уже заданные вопросы

Верни JSON массив с вопросами в формате:
[
  {{"id": "question_id", "text": "Текст вопроса", "type": "text|select", "options": []}}
]

Если это select вопрос, укажи варианты в options.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты помощник для создания опросника по контент-маркетингу. Генерируй только валидный JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            # Извлекаем JSON из ответа
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            questions = json.loads(content)
            return questions if isinstance(questions, list) else [questions]
            
        except Exception as e:
            logger.error(f"Ошибка генерации адаптивных вопросов: {e}")
            # Fallback
            return [
                {'id': 'audience', 'text': 'Кто ваша целевая аудитория?', 'type': 'text', 'options': []},
                {'id': 'goals', 'text': 'Какие у вас бизнес-цели?', 'type': 'text', 'options': []}
            ]
    
    async def generate_sample_posts(
        self,
        business_type: list,
        niche: str,
        count: int = 3,
        link_analysis_result: Optional[Dict[str, Any]] = None,
        answers: Optional[List[Dict[str, Any]]] = None
    ) -> list:
        """
        Генерирует примеры постов на основе ниши и типа бизнеса
        
        Args:
            business_type: Массив типов бизнеса
            niche: Ниша бизнеса
            count: Количество примеров (по умолчанию 3)
            link_analysis_result: Результаты анализа ссылок (опционально)
            answers: Ответы пользователя из онбординга (опционально)
        
        Returns:
            Массив примеров постов с id, text, style, hashtags, image_prompt
        """
        if not self.openai_client:
            # Fallback примеры
            return [
                {
                    'id': '1',
                    'text': f'Информационный пост про {niche}',
                    'style': 'informative',
                    'hashtags': [niche.replace(' ', '_')],
                    'image_prompt': f'Профессиональное изображение для поста про {niche}'
                }
            ]
        
        try:
            # Собираем контекст из linkAnalysisResult
            context_parts = []
            if link_analysis_result:
                if link_analysis_result.get('target_audience'):
                    context_parts.append(f"Целевая аудитория: {link_analysis_result['target_audience']}")
                if link_analysis_result.get('pain_points'):
                    pain_points_text = ", ".join(link_analysis_result['pain_points'][:3])
                    context_parts.append(f"Болевые точки: {pain_points_text}")
                if link_analysis_result.get('insights'):
                    insights_text = " | ".join(link_analysis_result['insights'][:2])
                    context_parts.append(f"Инсайты: {insights_text}")
                if link_analysis_result.get('tone'):
                    context_parts.append(f"Тональность: {link_analysis_result['tone']}")
                if link_analysis_result.get('tone_profile') and isinstance(link_analysis_result['tone_profile'], dict):
                    tone_profile = link_analysis_result['tone_profile']
                    if tone_profile.get('base'):
                        context_parts.append(f"Базовый тон: {tone_profile['base']}")
            
            context_text = "\n".join(context_parts) if context_parts else "Контекст не указан"
            
            prompt = f"""
Сгенерируй {count} примеров постов для бизнеса в нише «{niche}».

Тип бизнеса: {', '.join(business_type)}

Контекст для создания постов:
{context_text}

Требования к постам:

— Пиши на русском, как живой автор: минимум канцелярита, активный голос и простые слова.

— Начинай каждый пост с яркой зацепки: вопрос, смелое утверждение или неожиданный факт — чтобы сразу привлечь внимание.

— В основной части дай 1–2 конкретных факта, вывод или мини‑пример, который показывает пользу.

— Заверши одним призывом к действию: приглашай обсудить, поделиться мнением, сохранить пост или перейти по ссылке. Вариируй формулировки — не всегда «оставьте +».

— Длина поста 250–500 символов (допустимы небольшие отклонения, если это усиливает историю).

— Используй 1–2 эмодзи, только по делу.

— Избегай клише и повторов темы/ниши в начале.

Сгенерируй посты в трёх стилях:

1. Информационный — конкретная польза без воды.

2. Продающий — мягко через ценность.

3. Вовлекающий — вопрос или интрига, которая побуждает к диалогу.

Для каждого поста также создай промпт для генерации изображения (image_prompt) — короткое описание визуала, который подходит к тексту поста.

Верни JSON массив:

[
  {{
    "id": "1",
    "text": "Текст поста. Сильная зацепка, затем 2–3 предложения пользы и мягкий призыв к действию.",
    "style": "informative|selling|engaging",
    "hashtags": ["#хештег1", "#хештег2"],
    "image_prompt": "Краткое описание изображения для этого поста (на русском, 10-15 слов)"
  }},
  ...
]
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по контент-маркетингу. Генерируй только валидный JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            # Извлекаем JSON из ответа
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            posts = json.loads(content)
            if not isinstance(posts, list):
                posts = [posts]
            
            # Убеждаемся, что у каждого поста есть image_prompt
            for post in posts:
                if 'image_prompt' not in post or not post.get('image_prompt'):
                    post['image_prompt'] = f"Профессиональное изображение для поста: {post.get('text', '')[:50]}..."
            
            return posts
            
        except Exception as e:
            logger.error(f"Ошибка генерации примеров постов: {e}", exc_info=True)
            # Fallback
            return [
                {
                    'id': '1',
                    'text': f'Информационный пост про {niche}',
                    'style': 'informative',
                    'hashtags': [niche.replace(' ', '_')],
                    'image_prompt': f'Профессиональное изображение для поста про {niche}'
                }
            ]


