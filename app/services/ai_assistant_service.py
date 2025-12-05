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
                # Создаем tone_profile на основе suggestedTone
                base_tone = result.get('suggestedTone', 'professional')
                result['tone_profile'] = {
                    'base': base_tone,
                    'flavor': 'friendly' if base_tone in ['professional', 'expert'] else base_tone,
                    'rhythm': 'short',
                    'energy': 'medium'
                }
            else:
                # Валидируем tone_profile
                profile = result['tone_profile']
                if profile.get('base') not in valid_tones:
                    profile['base'] = result.get('suggestedTone', 'professional')
                if profile.get('flavor') not in valid_tones:
                    profile['flavor'] = 'friendly'
                if profile.get('rhythm') not in ['short', 'medium', 'long']:
                    profile['rhythm'] = 'short'
                if profile.get('energy') not in ['low', 'medium', 'high']:
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
        count: int = 3
    ) -> list:
        """
        Генерирует примеры постов на основе ниши и типа бизнеса
        
        Args:
            business_type: Массив типов бизнеса
            niche: Ниша бизнеса
            count: Количество примеров (по умолчанию 3)
        
        Returns:
            Массив примеров постов с id, text, style, hashtags
        """
        if not self.openai_client:
            # Fallback примеры
            return [
                {
                    'id': '1',
                    'text': f'Информационный пост про {niche}',
                    'style': 'informative',
                    'hashtags': [niche.replace(' ', '_')]
                }
            ]
        
        try:
            prompt = f"""
Сгенерируй {count} примеров постов для бизнеса в нише "{niche}".

Тип бизнеса: {', '.join(business_type)}

ВАЖНО: Пиши как живой автор, который видит проблему изнутри. Без официоза, без штампов. Только живая мысль, настоящая польза и ощущение опыта.

Создай посты в разных стилях:
- Информационный (конкретная польза, без воды)
- Продающий (мягко, через ценность)
- Вовлекающий (вопрос, интрига, инсайт)

Каждый пост должен:
- Читаться как текст от реального человека
- Нести конкретную пользу в каждом предложении
- Быть плотным (250-450 символов)
- Иметь 1-2 эмодзи максимум

Верни JSON массив в формате:
[
  {{
    "id": "1",
    "text": "Живой текст поста, как от автора со своим характером. Плотный, понятный, человеческий. 2-3 предложения с конкретной пользой.",
    "style": "informative|selling|engaging",
    "hashtags": ["хештег1", "хештег2"]
  }}
]

Пример хорошего поста:
"Когда цена падает — новички паникуют, а опытные докупают. Почему? Потому что работают с вероятностями, а не эмоциями. Разбираем логику на примерах."
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по контент-маркетингу. Генерируй только валидный JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
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
            return posts if isinstance(posts, list) else [posts]
            
        except Exception as e:
            logger.error(f"Ошибка генерации примеров постов: {e}")
            # Fallback
            return [
                {
                    'id': '1',
                    'text': f'Информационный пост про {niche}',
                    'style': 'informative',
                    'hashtags': [niche.replace(' ', '_')]
                }
            ]


