"""
API endpoints для управления источниками контента
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from datetime import datetime

from app.services.content_source_service import ContentSourceService, MonitoredItemService
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

# Namespace
content_sources_ns = Namespace('content-sources', description='Управление источниками контента')


# Models
source_config_model = content_sources_ns.model('SourceConfig', {
    'selectors': fields.Raw(description='CSS selectors для извлечения контента'),
    'api_params': fields.Raw(description='Параметры API'),
})

content_source_create_model = content_sources_ns.model('ContentSourceCreate', {
    'name': fields.String(required=True, description='Название источника', example='Новостной сайт'),
    'description': fields.String(description='Описание источника', example='Мониторинг новостей о технологиях'),
    'source_type': fields.String(required=True, description='Тип источника', example='website', enum=['website', 'rss', 'news_api', 'social']),
    'url': fields.String(required=True, description='URL источника', example='https://example.com/news'),
    'config': fields.Nested(source_config_model, description='Конфигурация источника'),
    'extraction_method': fields.String(description='Метод извлечения', example='ai', enum=['ai', 'selectors', 'rss']),
    'keywords': fields.List(fields.String, description='Ключевые слова для фильтрации', example=['технологии', 'AI']),
    'exclude_keywords': fields.List(fields.String, description='Исключающие слова', example=['спорт', 'политика']),
    'categories': fields.List(fields.String, description='Категории контента', example=['tech', 'business']),
    'auto_post_enabled': fields.Boolean(description='Включен автопостинг', default=True),
    'post_delay_minutes': fields.Integer(description='Задержка перед публикацией (минуты)', default=0),
    'post_template': fields.String(description='Шаблон поста', example='{title}\n\n{description}\n\n{url}'),
    'auto_posting_rule_id': fields.Integer(description='ID правила автопостинга'),
    'check_interval_minutes': fields.Integer(description='Интервал проверки (минуты)', default=60),
    'is_active': fields.Boolean(description='Активен', default=True),
})

content_source_update_model = content_sources_ns.model('ContentSourceUpdate', {
    'name': fields.String(description='Название источника'),
    'description': fields.String(description='Описание источника'),
    'url': fields.String(description='URL источника'),
    'config': fields.Nested(source_config_model, description='Конфигурация источника'),
    'extraction_method': fields.String(description='Метод извлечения'),
    'keywords': fields.List(fields.String, description='Ключевые слова'),
    'exclude_keywords': fields.List(fields.String, description='Исключающие слова'),
    'categories': fields.List(fields.String, description='Категории'),
    'auto_post_enabled': fields.Boolean(description='Включен автопостинг'),
    'post_delay_minutes': fields.Integer(description='Задержка перед публикацией'),
    'post_template': fields.String(description='Шаблон поста'),
    'auto_posting_rule_id': fields.Integer(description='ID правила автопостинга'),
    'check_interval_minutes': fields.Integer(description='Интервал проверки'),
    'is_active': fields.Boolean(description='Активен'),
})

content_source_response_model = content_sources_ns.model('ContentSourceResponse', {
    'id': fields.Integer(description='ID источника'),
    'user_id': fields.Integer(description='ID пользователя'),
    'name': fields.String(description='Название'),
    'description': fields.String(description='Описание'),
    'source_type': fields.String(description='Тип источника'),
    'url': fields.String(description='URL'),
    'config': fields.Raw(description='Конфигурация'),
    'extraction_method': fields.String(description='Метод извлечения'),
    'keywords': fields.List(fields.String, description='Ключевые слова'),
    'exclude_keywords': fields.List(fields.String, description='Исключающие слова'),
    'categories': fields.List(fields.String, description='Категории'),
    'auto_post_enabled': fields.Boolean(description='Автопостинг включен'),
    'post_delay_minutes': fields.Integer(description='Задержка публикации'),
    'post_template': fields.String(description='Шаблон поста'),
    'auto_posting_rule_id': fields.Integer(description='ID правила автопостинга'),
    'check_interval_minutes': fields.Integer(description='Интервал проверки'),
    'next_check_at': fields.String(description='Следующая проверка'),
    'last_check_at': fields.String(description='Последняя проверка'),
    'last_check_status': fields.String(description='Статус последней проверки'),
    'last_error_message': fields.String(description='Сообщение об ошибке'),
    'is_active': fields.Boolean(description='Активен'),
    'total_checks': fields.Integer(description='Всего проверок'),
    'total_items_found': fields.Integer(description='Всего найдено элементов'),
    'total_items_new': fields.Integer(description='Новых элементов'),
    'total_posts_created': fields.Integer(description='Создано постов'),
    'created_at': fields.String(description='Дата создания'),
    'updated_at': fields.String(description='Дата обновления'),
})

monitored_item_response_model = content_sources_ns.model('MonitoredItemResponse', {
    'id': fields.Integer(description='ID элемента'),
    'source_id': fields.Integer(description='ID источника'),
    'user_id': fields.Integer(description='ID пользователя'),
    'external_id': fields.String(description='Внешний ID'),
    'title': fields.String(description='Заголовок'),
    'content': fields.String(description='Контент'),
    'summary': fields.String(description='Краткое описание'),
    'url': fields.String(description='URL'),
    'image_url': fields.String(description='URL изображения'),
    'author': fields.String(description='Автор'),
    'published_at': fields.String(description='Дата публикации'),
    'status': fields.String(description='Статус'),
    'duplicate_of': fields.Integer(description='ID дубликата'),
    'relevance_score': fields.Float(description='Оценка релевантности'),
    'ai_summary': fields.String(description='AI резюме'),
    'ai_sentiment': fields.String(description='Тональность'),
    'ai_category': fields.String(description='Категория'),
    'ai_keywords': fields.List(fields.String, description='AI ключевые слова'),
    'content_id': fields.String(description='ID созданного контента'),
    'scheduled_post_id': fields.Integer(description='ID отложенного поста'),
    'created_at': fields.String(description='Дата создания'),
    'processed_at': fields.String(description='Дата обработки'),
    'posted_at': fields.String(description='Дата публикации'),
})


@content_sources_ns.route('/')
class ContentSourcesList(Resource):
    """Список источников контента и создание нового"""
    
    @content_sources_ns.doc(
        'list_content_sources',
        security='BearerAuth',
        params={
            'source_type': 'Фильтр по типу источника',
            'is_active': 'Фильтр по активности (true/false)'
        }
    )
    @jwt_required
    def get(self, current_user):
        """Получение списка источников контента"""
        try:
            user_id = current_user.get('user_id')
            source_type = request.args.get('source_type')
            is_active = request.args.get('is_active')
            
            if is_active is not None:
                is_active = is_active.lower() == 'true'
            
            sources = ContentSourceService.get_user_sources(
                user_id=user_id,
                source_type=source_type,
                is_active=is_active
            )
            
            return {
                'sources': [source.to_dict() for source in sources],
                'total': len(sources)
            }, 200
            
        except Exception as e:
            logger.error(f"Error listing content sources: {e}")
            return {'error': 'Internal server error'}, 500
    
    @content_sources_ns.doc(
        'create_content_source',
        security='BearerAuth'
    )
    @content_sources_ns.expect(content_source_create_model)
    @jwt_required
    def post(self, current_user):
        """Создание нового источника контента"""
        try:
            user_id = current_user.get('user_id')
            data = request.json
            
            # Валидация обязательных полей
            if not data.get('name'):
                return {'error': 'Name is required'}, 400
            
            if not data.get('source_type'):
                return {'error': 'Source type is required'}, 400
            
            if not data.get('url'):
                return {'error': 'URL is required'}, 400
            
            # Создаем источник
            source = ContentSourceService.create_source(
                user_id=user_id,
                name=data['name'],
                source_type=data['source_type'],
                url=data['url'],
                description=data.get('description'),
                config=data.get('config', {}),
                extraction_method=data.get('extraction_method', 'ai'),
                keywords=data.get('keywords', []),
                exclude_keywords=data.get('exclude_keywords', []),
                categories=data.get('categories', []),
                auto_post_enabled=data.get('auto_post_enabled', True),
                post_delay_minutes=data.get('post_delay_minutes', 0),
                post_template=data.get('post_template'),
                auto_posting_rule_id=data.get('auto_posting_rule_id'),
                check_interval_minutes=data.get('check_interval_minutes', 60),
                is_active=data.get('is_active', True)
            )
            
            if not source:
                return {'error': 'Failed to create content source'}, 500
            
            return source.to_dict(), 201
            
        except Exception as e:
            logger.error(f"Error creating content source: {e}")
            return {'error': 'Internal server error'}, 500


@content_sources_ns.route('/<int:source_id>')
class ContentSourceDetail(Resource):
    """Управление конкретным источником контента"""
    
    @content_sources_ns.doc(
        'get_content_source',
        security='BearerAuth'
    )
    @jwt_required
    def get(self, current_user, source_id):
        """Получение информации об источнике"""
        try:
            user_id = current_user.get('user_id')
            source = ContentSourceService.get_source(source_id, user_id)
            
            if not source:
                return {'error': 'Content source not found'}, 404
            
            return source.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error getting content source: {e}")
            return {'error': 'Internal server error'}, 500
    
    @content_sources_ns.doc(
        'update_content_source',
        security='BearerAuth'
    )
    @content_sources_ns.expect(content_source_update_model)
    @jwt_required
    def put(self, current_user, source_id):
        """Обновление источника"""
        try:
            user_id = current_user.get('user_id')
            data = request.json
            
            source = ContentSourceService.update_source(
                source_id=source_id,
                user_id=user_id,
                **data
            )
            
            if not source:
                return {'error': 'Content source not found'}, 404
            
            return source.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error updating content source: {e}")
            return {'error': 'Internal server error'}, 500
    
    @content_sources_ns.doc(
        'delete_content_source',
        security='BearerAuth'
    )
    @jwt_required
    def delete(self, current_user, source_id):
        """Удаление источника"""
        try:
            user_id = current_user.get('user_id')
            success = ContentSourceService.delete_source(source_id, user_id)
            
            if not success:
                return {'error': 'Content source not found'}, 404
            
            return {'message': 'Content source deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting content source: {e}")
            return {'error': 'Internal server error'}, 500


@content_sources_ns.route('/<int:source_id>/items')
class ContentSourceItems(Resource):
    """Найденные элементы из источника"""
    
    @content_sources_ns.doc(
        'get_source_items',
        security='BearerAuth',
        params={
            'status': 'Фильтр по статусу (new, approved, posted, ignored, duplicate)',
            'limit': 'Количество элементов (по умолчанию 100)'
        }
    )
    @jwt_required
    def get(self, current_user, source_id):
        """Получение элементов из источника"""
        try:
            user_id = current_user.get('user_id')
            status = request.args.get('status')
            limit = int(request.args.get('limit', 100))
            
            items = MonitoredItemService.get_items_by_source(
                source_id=source_id,
                user_id=user_id,
                status=status,
                limit=limit
            )
            
            return {
                'items': [item.to_dict() for item in items],
                'total': len(items)
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting source items: {e}")
            return {'error': 'Internal server error'}, 500


@content_sources_ns.route('/items/new')
class NewMonitoredItems(Resource):
    """Новые необработанные элементы"""
    
    @content_sources_ns.doc(
        'get_new_items',
        security='BearerAuth',
        params={
            'limit': 'Количество элементов (по умолчанию 50)'
        }
    )
    @jwt_required
    def get(self, current_user):
        """Получение новых необработанных элементов"""
        try:
            user_id = current_user.get('user_id')
            limit = int(request.args.get('limit', 50))
            
            items = MonitoredItemService.get_new_items(
                user_id=user_id,
                limit=limit
            )
            
            return {
                'items': [item.to_dict() for item in items],
                'total': len(items)
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting new items: {e}")
            return {'error': 'Internal server error'}, 500


@content_sources_ns.route('/items/<int:item_id>/approve')
class ApproveMonitoredItem(Resource):
    """Утверждение элемента для публикации"""
    
    @content_sources_ns.doc(
        'approve_item',
        security='BearerAuth'
    )
    @jwt_required
    def post(self, current_user, item_id):
        """Утверждение элемента"""
        try:
            item = MonitoredItemService.update_item_status(
                item_id=item_id,
                status='approved'
            )
            
            if not item:
                return {'error': 'Item not found'}, 404
            
            return item.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error approving item: {e}")
            return {'error': 'Internal server error'}, 500


@content_sources_ns.route('/items/<int:item_id>/ignore')
class IgnoreMonitoredItem(Resource):
    """Игнорирование элемента"""
    
    @content_sources_ns.doc(
        'ignore_item',
        security='BearerAuth'
    )
    @jwt_required
    def post(self, current_user, item_id):
        """Игнорирование элемента"""
        try:
            item = MonitoredItemService.update_item_status(
                item_id=item_id,
                status='ignored'
            )
            
            if not item:
                return {'error': 'Item not found'}, 404
            
            return item.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error ignoring item: {e}")
            return {'error': 'Internal server error'}, 500

