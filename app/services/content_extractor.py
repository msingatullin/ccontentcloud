"""
AI-based Content Extractor для извлечения структурированных данных из HTML
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Извлечение контента с помощью AI"""
    
    def __init__(self, openai_client=None):
        """Инициализация с OpenAI клиентом"""
        self.openai_client = openai_client
    
    async def extract_from_html(
        self,
        html: str,
        url: str,
        extraction_hints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Извлечение структурированных данных из HTML с помощью AI
        
        Args:
            html: HTML контент страницы
            url: URL страницы
            extraction_hints: Подсказки для извлечения (категории, ключевые слова)
        
        Returns:
            Словарь с извлеченными данными
        """
        try:
            # Очищаем HTML от скриптов и стилей
            clean_html = self._clean_html(html)
            
            # Если HTML слишком большой, обрезаем
            if len(clean_html) > 15000:
                clean_html = clean_html[:15000] + "..."
            
            # Формируем промпт для AI
            prompt = self._build_extraction_prompt(clean_html, url, extraction_hints)
            
            # Вызываем AI для извлечения
            if self.openai_client:
                extracted_data = await self._call_openai(prompt)
            else:
                # Fallback: простое извлечение без AI
                extracted_data = self._fallback_extraction(clean_html, url)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                'title': url,
                'content': '',
                'summary': '',
                'error': str(e)
            }
    
    def _clean_html(self, html: str) -> str:
        """Очистка HTML от скриптов, стилей и лишних элементов"""
        # Удаляем скрипты
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Удаляем стили
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Удаляем комментарии
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Удаляем множественные пробелы и переносы
        html = re.sub(r'\s+', ' ', html)
        
        return html.strip()
    
    def _build_extraction_prompt(
        self,
        html: str,
        url: str,
        hints: Optional[Dict[str, Any]]
    ) -> str:
        """Формирование промпта для AI"""
        
        hints_text = ""
        if hints:
            if hints.get('keywords'):
                hints_text += f"\nКлючевые слова: {', '.join(hints['keywords'])}"
            if hints.get('categories'):
                hints_text += f"\nКатегории: {', '.join(hints['categories'])}"
        
        prompt = f"""Проанализируй HTML страницы и извлеки структурированную информацию.

URL: {url}
{hints_text}

HTML:
{html}

Извлеки следующую информацию в формате JSON:
{{
  "title": "Заголовок статьи/новости/акции",
  "content": "Полный текст контента",
  "summary": "Краткое описание (2-3 предложения)",
  "author": "Автор (если есть)",
  "published_date": "Дата публикации в ISO формате (если есть)",
  "image_url": "URL главного изображения (если есть)",
  "category": "Категория контента",
  "keywords": ["ключевое слово 1", "ключевое слово 2"],
  "is_promotion": true/false,
  "sentiment": "positive/negative/neutral",
  "relevance_score": 0.0-1.0
}}

Если это промо-акция или специальное предложение, установи is_promotion: true.
Оцени релевантность контента (relevance_score) от 0 до 1.
Определи sentiment (positive, negative, neutral).
"""
        
        return prompt
    
    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Вызов OpenAI API для извлечения"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по извлечению структурированных данных из HTML. Всегда отвечай валидным JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            # Парсим JSON ответ
            extracted = json.loads(result)
            
            # Добавляем метаданные
            extracted['extraction_method'] = 'ai'
            extracted['extracted_at'] = datetime.utcnow().isoformat()
            
            return extracted
            
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            raise
    
    def _fallback_extraction(self, html: str, url: str) -> Dict[str, Any]:
        """Fallback извлечение без AI (простые эвристики)"""
        
        # Пытаемся найти заголовок
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1) if title_match else url
        title = re.sub(r'<[^>]+>', '', title).strip()
        
        # Пытаемся найти контент в параграфах
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
        content = ' '.join([re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs[:10]])
        
        # Краткое описание - первые 200 символов
        summary = content[:200] + "..." if len(content) > 200 else content
        
        # Ищем изображения
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        image_url = img_match.group(1) if img_match else None
        
        return {
            'title': title,
            'content': content,
            'summary': summary,
            'image_url': image_url,
            'author': None,
            'published_date': None,
            'category': 'general',
            'keywords': [],
            'is_promotion': False,
            'sentiment': 'neutral',
            'relevance_score': 0.5,
            'extraction_method': 'fallback',
            'extracted_at': datetime.utcnow().isoformat()
        }
    
    def calculate_content_hash(self, content: str) -> str:
        """Вычисление хеша контента для определения изменений"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def extract_text_from_html(self, html: str) -> str:
        """Извлечение чистого текста из HTML"""
        # Удаляем все теги
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Декодируем HTML entities
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        
        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


class ChangeDetector:
    """Определение изменений на странице"""
    
    def __init__(self):
        self.extractor = ContentExtractor()
    
    def detect_changes(
        self,
        new_html: str,
        old_snapshot: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Определение изменений между текущей версией и снимком
        
        Returns:
            {
                'has_changes': bool,
                'change_type': 'new_content' | 'updated_content' | 'no_changes',
                'new_items': [],
                'updated_items': [],
                'confidence': 0.0-1.0
            }
        """
        
        # Вычисляем хеш нового контента
        new_text = self.extractor.extract_text_from_html(new_html)
        new_hash = self.extractor.calculate_content_hash(new_text)
        
        # Если нет старого снимка - это новый контент
        if not old_snapshot:
            return {
                'has_changes': True,
                'change_type': 'new_content',
                'new_hash': new_hash,
                'confidence': 1.0
            }
        
        # Сравниваем хеши
        old_hash = old_snapshot.get('hash')
        if new_hash == old_hash:
            return {
                'has_changes': False,
                'change_type': 'no_changes',
                'new_hash': new_hash,
                'confidence': 1.0
            }
        
        # Контент изменился
        return {
            'has_changes': True,
            'change_type': 'updated_content',
            'new_hash': new_hash,
            'old_hash': old_hash,
            'confidence': 0.8
        }
    
    def extract_new_items(
        self,
        html: str,
        item_selectors: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Извлечение списка элементов (например, статей) со страницы
        
        Используется для страниц с несколькими новостями/статьями
        """
        items = []
        
        if not item_selectors:
            # Пытаемся найти статьи автоматически
            # Ищем article, div.post, div.news-item и т.д.
            patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*news[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*item[^"]*"[^>]*>(.*?)</div>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches and len(matches) > 1:  # Если нашли несколько элементов
                    for match in matches[:10]:  # Берем первые 10
                        # Извлекаем заголовок
                        title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', match, re.IGNORECASE)
                        if title_match:
                            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                            
                            # Извлекаем ссылку
                            link_match = re.search(r'<a[^>]+href=["\']([^"\']+)["\']', match, re.IGNORECASE)
                            link = link_match.group(1) if link_match else None
                            
                            if title and len(title) > 10:
                                items.append({
                                    'title': title,
                                    'url': link,
                                    'html_snippet': match[:500]
                                })
                    break
        
        return items


class RSSParser:
    """Парсер RSS лент"""
    
    @staticmethod
    def parse_feed(feed_xml: str) -> List[Dict[str, Any]]:
        """Парсинг RSS/Atom ленты"""
        items = []
        
        try:
            # Ищем все <item> или <entry>
            item_pattern = r'<(?:item|entry)[^>]*>(.*?)</(?:item|entry)>'
            item_matches = re.findall(item_pattern, feed_xml, re.IGNORECASE | re.DOTALL)
            
            for item_xml in item_matches:
                item_data = {}
                
                # Заголовок
                title_match = re.search(r'<title[^>]*>(.*?)</title>', item_xml, re.IGNORECASE | re.DOTALL)
                if title_match:
                    item_data['title'] = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title_match.group(1)).strip()
                
                # Ссылка
                link_match = re.search(r'<link[^>]*>([^<]+)</link>', item_xml, re.IGNORECASE)
                if not link_match:
                    link_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\']', item_xml, re.IGNORECASE)
                if link_match:
                    item_data['url'] = link_match.group(1).strip()
                
                # Описание
                desc_match = re.search(r'<(?:description|summary)[^>]*>(.*?)</(?:description|summary)>', item_xml, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    item_data['summary'] = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', desc_match.group(1)).strip()
                    item_data['summary'] = re.sub(r'<[^>]+>', '', item_data['summary'])[:500]
                
                # Контент
                content_match = re.search(r'<(?:content:encoded|content)[^>]*>(.*?)</(?:content:encoded|content)>', item_xml, re.IGNORECASE | re.DOTALL)
                if content_match:
                    item_data['content'] = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', content_match.group(1)).strip()
                    item_data['content'] = re.sub(r'<[^>]+>', '', item_data['content'])
                
                # Дата публикации
                date_match = re.search(r'<(?:pubDate|published|updated)[^>]*>(.*?)</(?:pubDate|published|updated)>', item_xml, re.IGNORECASE)
                if date_match:
                    item_data['published_date'] = date_match.group(1).strip()
                
                # Автор
                author_match = re.search(r'<(?:author|dc:creator)[^>]*>(.*?)</(?:author|dc:creator)>', item_xml, re.IGNORECASE | re.DOTALL)
                if author_match:
                    author_text = author_match.group(1)
                    name_match = re.search(r'<name>(.*?)</name>', author_text, re.IGNORECASE)
                    item_data['author'] = name_match.group(1).strip() if name_match else re.sub(r'<[^>]+>', '', author_text).strip()
                
                # GUID как external_id
                guid_match = re.search(r'<guid[^>]*>(.*?)</guid>', item_xml, re.IGNORECASE)
                if guid_match:
                    item_data['external_id'] = guid_match.group(1).strip()
                elif item_data.get('url'):
                    item_data['external_id'] = item_data['url']
                
                if item_data.get('title'):
                    items.append(item_data)
            
            logger.info(f"Parsed {len(items)} items from RSS feed")
            return items
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []
    
    @staticmethod
    def discover_rss_feed(url: str, html: Optional[str] = None) -> Optional[str]:
        """
        Автоматический поиск RSS ленты на странице
        
        Args:
            url: URL страницы
            html: HTML содержимое страницы (если уже загружено)
        
        Returns:
            URL RSS ленты или None если не найдено
        """
        import requests
        from urllib.parse import urljoin, urlparse
        
        try:
            # Если HTML не передан, загружаем страницу
            if not html:
                # Пробуем загрузить с разными User-Agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (compatible; ContentCurator/1.0)'
                ]
                
                for user_agent in user_agents:
                    try:
                        response = requests.get(
                            url, 
                            timeout=10, 
                            headers={
                                'User-Agent': user_agent,
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
                            },
                            allow_redirects=True
                        )
                        response.raise_for_status()
                        html = response.text
                        break
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 403 and user_agent != user_agents[-1]:
                            continue  # Пробуем следующий User-Agent
                        raise
            
            # 1. Ищем RSS ссылки в <link> тегах
            rss_link_pattern = r'<link[^>]+rel=["\'](?:alternate|feed)["\'][^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']'
            matches = re.findall(rss_link_pattern, html, re.IGNORECASE)
            
            if matches:
                rss_url = matches[0]
                # Преобразуем относительный URL в абсолютный
                if not rss_url.startswith('http'):
                    rss_url = urljoin(url, rss_url)
                logger.info(f"Found RSS feed via <link> tag: {rss_url}")
                return rss_url
            
            # 2. Проверяем стандартные пути RSS
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            standard_paths = [
                '/rss',
                '/feed',
                '/rss.xml',
                '/feed.xml',
                '/rss/',
                '/feed/',
                '/atom.xml',
                '/index.xml',
                f'{parsed_url.path}/rss',
                f'{parsed_url.path}/feed',
            ]
            
            for path in standard_paths:
                test_url = urljoin(base_url, path)
                try:
                    response = requests.head(test_url, timeout=5, allow_redirects=True, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; ContentCurator/1.0)'
                    })
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'xml' in content_type or 'rss' in content_type or 'atom' in content_type:
                        logger.info(f"Found RSS feed at standard path: {test_url}")
                        return test_url
                except:
                    continue
            
            # 3. Ищем упоминания RSS в тексте страницы
            rss_mention_pattern = r'(https?://[^\s<>"\']+\.(?:rss|xml|atom))'
            mentions = re.findall(rss_mention_pattern, html, re.IGNORECASE)
            for mention in mentions[:5]:  # Проверяем первые 5 упоминаний
                try:
                    response = requests.head(mention, timeout=5, allow_redirects=True, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; ContentCurator/1.0)'
                    })
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'xml' in content_type or 'rss' in content_type:
                        logger.info(f"Found RSS feed via text mention: {mention}")
                        return mention
                except:
                    continue
            
            logger.info(f"No RSS feed found for {url}")
            return None
            
        except Exception as e:
            logger.warning(f"Error discovering RSS feed for {url}: {e}")
            return None

