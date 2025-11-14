"""
API endpoints для правил автопостинга
"""

import logging
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from app.database.connection import get_db_session
from app.services.auto_posting_service import AutoPostingService
from app.api.routes import jwt_required
from app.api.schemas import (
    AutoPostingRuleCreateSchema,
    AutoPostingRuleUpdateSchema,
    AutoPostingRuleResponseSchema
)

logger = logging.getLogger(__name__)

# Создаем namespace
auto_posting_ns = Namespace('auto-posting', description='Автопостинг API')

# Swagger модели
auto_posting_rule_model = auto_posting_ns.model('AutoPostingRule', {
    'id': fields.Integer(description='ID правила'),
    'name': fields.String(description='Название'),
    'schedule_type': fields.String(description='Тип расписания'),
    'is_active': fields.Boolean(description='Активно'),
    'next_execution_at': fields.String(description='Следующее выполнение')
})


@auto_posting_ns.route('/rules')
class AutoPostingRulesList(Resource):
    @jwt_required
    @auto_posting_ns.doc('list_auto_posting_rules', security='BearerAuth')
    def get(self, current_user):
        """Получить список правил автопостинга"""
        try:
            user_id = current_user.get('user_id')
            is_active = request.args.get('is_active')
            if is_active is not None:
                is_active = is_active.lower() == 'true'
            
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            db = get_db_session()
            service = AutoPostingService(db)
            
            rules = service.list_rules(
                user_id=user_id,
                is_active=is_active,
                limit=limit,
                offset=offset
            )
            
            db.close()
            
            return {
                'success': True,
                'data': [rule.to_dict() for rule in rules],
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения списка правил: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @auto_posting_ns.doc('create_auto_posting_rule', security='BearerAuth')
    @auto_posting_ns.expect(auto_posting_rule_model)
    def post(self, current_user):
        """Создать правило автопостинга"""
        try:
            user_id = current_user.get('user_id')
            
            # Валидация
            try:
                data = AutoPostingRuleCreateSchema(**request.json)
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
            service = AutoPostingService(db)
            
            rule = service.create_rule(
                user_id=user_id,
                name=data.name,
                description=data.description,
                schedule_type=data.schedule_type,
                schedule_config=data.schedule_config.dict(),
                content_config=data.content_config,
                platforms=[p.value for p in data.platforms],
                accounts=data.accounts,
                content_types=[ct.value for ct in data.content_types] if data.content_types else None,
                max_posts_per_day=data.max_posts_per_day,
                max_posts_per_week=data.max_posts_per_week
            )
            
            db.close()
            
            return {
                'success': True,
                'data': rule.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 201
            
        except Exception as e:
            logger.error(f"Ошибка создания правила: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500


@auto_posting_ns.route('/rules/<int:rule_id>')
class AutoPostingRuleDetail(Resource):
    @jwt_required
    @auto_posting_ns.doc('get_auto_posting_rule', security='BearerAuth')
    def get(self, current_user, rule_id):
        """Получить правило автопостинга"""
        try:
            user_id = current_user.get('user_id')
            
            db = get_db_session()
            service = AutoPostingService(db)
            
            rule = service.get_rule(user_id, rule_id)
            db.close()
            
            if not rule:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Правило {rule_id} не найдено',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'data': rule.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения правила: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @auto_posting_ns.doc('update_auto_posting_rule', security='BearerAuth')
    def put(self, current_user, rule_id):
        """Обновить правило автопостинга"""
        try:
            user_id = current_user.get('user_id')
            
            # Валидация
            try:
                data = AutoPostingRuleUpdateSchema(**request.json)
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
            service = AutoPostingService(db)
            
            update_data = {}
            if data.name is not None:
                update_data['name'] = data.name
            if data.description is not None:
                update_data['description'] = data.description
            if data.schedule_type is not None:
                update_data['schedule_type'] = data.schedule_type
            if data.schedule_config is not None:
                update_data['schedule_config'] = data.schedule_config.dict()
            if data.content_config is not None:
                update_data['content_config'] = data.content_config
            if data.platforms is not None:
                update_data['platforms'] = [p.value for p in data.platforms]
            if data.accounts is not None:
                update_data['accounts'] = data.accounts
            if data.content_types is not None:
                update_data['content_types'] = [ct.value for ct in data.content_types]
            if data.is_active is not None:
                update_data['is_active'] = data.is_active
            if data.is_paused is not None:
                update_data['is_paused'] = data.is_paused
            if data.max_posts_per_day is not None:
                update_data['max_posts_per_day'] = data.max_posts_per_day
            if data.max_posts_per_week is not None:
                update_data['max_posts_per_week'] = data.max_posts_per_week
            
            rule = service.update_rule(user_id, rule_id, **update_data)
            db.close()
            
            if not rule:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Правило {rule_id} не найдено',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'data': rule.to_dict(),
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка обновления правила: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500
    
    @jwt_required
    @auto_posting_ns.doc('delete_auto_posting_rule', security='BearerAuth')
    def delete(self, current_user, rule_id):
        """Удалить правило автопостинга"""
        try:
            user_id = current_user.get('user_id')
            
            db = get_db_session()
            service = AutoPostingService(db)
            
            success = service.delete_rule(user_id, rule_id)
            db.close()
            
            if not success:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Правило {rule_id} не найдено',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'message': 'Правило успешно удалено',
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка удаления правила: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500


@auto_posting_ns.route('/rules/<int:rule_id>/toggle')
class AutoPostingRuleToggle(Resource):
    @jwt_required
    @auto_posting_ns.doc('toggle_auto_posting_rule', security='BearerAuth')
    def post(self, current_user, rule_id):
        """Включить/выключить правило"""
        try:
            user_id = current_user.get('user_id')
            is_active = request.json.get('is_active', True)
            
            db = get_db_session()
            service = AutoPostingService(db)
            
            success = service.toggle_active(user_id, rule_id, is_active)
            db.close()
            
            if not success:
                return {
                    'success': False,
                    'error': 'Not Found',
                    'message': f'Правило {rule_id} не найдено',
                    'status_code': 404,
                    'timestamp': datetime.now().isoformat()
                }, 404
            
            return {
                'success': True,
                'message': f'Правило {"включено" if is_active else "выключено"}',
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка переключения правила: {e}")
            return {
                'success': False,
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }, 500

