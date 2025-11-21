"""
API endpoints для запланированных постов
"""

import logging
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from app.database.connection import get_db_session
from app.services.scheduled_post_service import ScheduledPostService
from app.api.routes import jwt_required
from app.api.schemas import (
    ScheduledPostCreateSchema,
    ScheduledPostUpdateSchema,
    ScheduledPostResponseSchema
)

logger = logging.getLogger(__name__)

# Создаем namespace
scheduled_posts_ns = Namespace('scheduled-posts', description='Запланированные посты API')

# Swagger модели
scheduled_post_model = scheduled_posts_ns.model('ScheduledPost', {
    'id': fields.Integer(description='ID запланированного поста'),
    'content_id': fields.String(description='ID контента'),
    'platform': fields.String(description='Платформа'),
    'account_id': fields.Integer(description='ID аккаунта'),
    'scheduled_time': fields.String(description='Время публикации'),
    'status': fields.String(description='Статус'),
    'created_at': fields.String(description='Дата создания')
})


@scheduled_posts_ns.route('')
class ScheduledPostsList(Resource):
    def options(self):
        """Handle CORS preflight requests"""
        return {}, 200
    
    @jwt_required
    @scheduled_posts_ns.doc('list_scheduled_posts', security='BearerAuth')
    def get(self, current_user):
        """Получить список запланированных постов"""
        try:
            user_id = current_user.get('user_id')
            status = request.args.get('status')
            platform = request.args.get('platform')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            posts = service.list_scheduled_posts(
                user_id=user_id,
                status=status,
                platform=platform,
                limit=limit,
                offset=offset
            )
            
            db.close()
            
            return {
                'success': True,
                'data': [post.to_dict() for post in posts],
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения списка постов: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @scheduled_posts_ns.doc('create_scheduled_post', security='BearerAuth')
    @scheduled_posts_ns.expect(scheduled_post_model)
    def post(self, current_user):
        """Создать запланированный пост"""
        try:
            user_id = current_user.get('user_id')
            
            # Валидация
            try:
                data = ScheduledPostCreateSchema(**request.json)
            except ValidationError as e:
                return {
                    'success': False,
                    'error': 'Validation Error',
                    'message': 'Некорректные данные запроса',
                    'details': e.errors(),
                    'status_code': 400,
                    'timestamp': datetime.now().isoformat()
                }, 400
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            scheduled_time = datetime.fromisoformat(data.scheduled_time.replace('Z', '+00:00'))
            
            post = service.create_scheduled_post(
                user_id=user_id,
                content_id=data.content_id,
                platform=data.platform.value,
                scheduled_time=scheduled_time,
                account_id=data.account_id,
                publish_options=data.publish_options
            )
            
            db.close()
            
            return {
                'success': True,
                'data': post.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 201
            
        except ValueError as e:
            return {
                'success': False,
                'error': 'Bad Request',
                'message': str(e),
                'status_code': 400,
                'timestamp': datetime.now().isoformat()
            }, 400
        except Exception as e:
            logger.error(f"Ошибка создания поста: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500


@scheduled_posts_ns.route('/<int:post_id>')
class ScheduledPostDetail(Resource):
    def options(self, post_id=None):
        """Handle CORS preflight requests"""
        return {}, 200
    
    @jwt_required
    @scheduled_posts_ns.doc('get_scheduled_post', security='BearerAuth')
    def get(self, current_user, post_id):
        """Получить запланированный пост"""
        try:
            user_id = current_user.get('user_id')
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            post = service.get_scheduled_post(user_id, post_id)
            db.close()
            
            if not post:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Пост {post_id} не найден',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'data': post.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения поста: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @scheduled_posts_ns.doc('update_scheduled_post', security='BearerAuth')
    def put(self, current_user, post_id):
        """Обновить запланированный пост"""
        try:
            user_id = current_user.get('user_id')
            
            # Валидация
            try:
                data = ScheduledPostUpdateSchema(**request.json)
            except ValidationError as e:
                return {
                    'success': False,
                    'error': 'Validation Error',
                    'message': 'Некорректные данные запроса',
                    'details': e.errors(),
                    'status_code': 400,
                    'timestamp': datetime.now().isoformat()
                }, 400
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            scheduled_time = None
            if data.scheduled_time:
                scheduled_time = datetime.fromisoformat(data.scheduled_time.replace('Z', '+00:00'))
            
            post = service.update_scheduled_post(
                user_id=user_id,
                post_id=post_id,
                scheduled_time=scheduled_time,
                status=data.status,
                publish_options=data.publish_options
            )
            db.close()
            
            if not post:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Пост {post_id} не найден',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'data': post.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except ValueError as e:
            return {
                'success': False,
                'error': 'Bad Request',
                'message': str(e),
                'status_code': 400,
                'timestamp': datetime.now().isoformat()
            }, 400
        except Exception as e:
            logger.error(f"Ошибка обновления поста: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @scheduled_posts_ns.doc('delete_scheduled_post', security='BearerAuth')
    def delete(self, current_user, post_id):
        """Удалить запланированный пост"""
        try:
            user_id = current_user.get('user_id')
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            try:
                success = service.delete_scheduled_post(user_id, post_id)
            except ValueError as e:
                db.close()
                return {
                    'success': False,
                    'error': 'Bad Request',
                    'message': str(e),
                    'status_code': 400,
                    'timestamp': datetime.now().isoformat()
                }, 400
            
            db.close()
            
            if not success:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Пост {post_id} не найден',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'message': 'Пост успешно удален',
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка удаления поста: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500


@scheduled_posts_ns.route('/<int:post_id>/cancel')
class ScheduledPostCancel(Resource):
    def options(self, post_id=None):
        """Handle CORS preflight requests"""
        return {}, 200
    
    @jwt_required
    @scheduled_posts_ns.doc('cancel_scheduled_post', security='BearerAuth')
    def post(self, current_user, post_id):
        """Отменить запланированный пост"""
        try:
            user_id = current_user.get('user_id')
            
            db = get_db_session()
            service = ScheduledPostService(db)
            
            try:
                success = service.cancel_scheduled_post(user_id, post_id)
            except ValueError as e:
                db.close()
                return {
                    'success': False,
                    'error': 'Bad Request',
                    'message': str(e),
                    'status_code': 400,
                    'timestamp': datetime.now().isoformat()
                }, 400
            
            db.close()
            
            if not success:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Пост {post_id} не найден',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'message': 'Пост успешно отменен',
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка отмены поста: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500

