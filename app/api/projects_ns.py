"""
Flask-RESTX namespace: Projects API
Управление проектами пользователя для группировки соц.сетей и контента
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging

from app.database.connection import get_db_session
from app.models.project import Project
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

projects_ns = Namespace(
    'projects',
    description='Управление проектами пользователя',
    path='/projects'
)

# ===== Swagger models =====

project_settings_model = projects_ns.model('ProjectSettings', {
    'tone_of_voice': fields.String(description='Тон коммуникации: professional, casual, friendly'),
    'target_audience': fields.String(description='Целевая аудитория'),
    'brand_name': fields.String(description='Название бренда'),
    'brand_description': fields.String(description='Описание бренда'),
    'keywords': fields.List(fields.String, description='Ключевые слова'),
    'hashtags': fields.List(fields.String, description='Хештеги по умолчанию'),
    'default_cta': fields.String(description='Призыв к действию по умолчанию'),
})

project_ai_settings_model = projects_ns.model('ProjectAISettings', {
    'preferred_style': fields.String(description='Предпочитаемый стиль: informative, entertaining, promotional'),
    'content_length': fields.String(description='Длина контента: short, medium, long'),
    'emoji_usage': fields.String(description='Использование эмодзи: none, minimal, moderate, heavy'),
    'formality_level': fields.String(description='Уровень формальности: formal, semi-formal, informal'),
})

project_model = projects_ns.model('Project', {
    'id': fields.Integer(description='ID проекта'),
    'user_id': fields.Integer(description='ID владельца'),
    'name': fields.String(description='Название проекта'),
    'description': fields.String(description='Описание проекта'),
    'is_active': fields.Boolean(description='Активен ли проект'),
    'is_default': fields.Boolean(description='Проект по умолчанию'),
    'settings': fields.Nested(project_settings_model, description='Настройки проекта'),
    'ai_settings': fields.Nested(project_ai_settings_model, description='AI настройки'),
    'channels_count': fields.Integer(description='Количество каналов'),
    'content_count': fields.Integer(description='Количество контента'),
    'created_at': fields.String(description='Дата создания'),
    'updated_at': fields.String(description='Дата обновления'),
})

create_project_request = projects_ns.model('CreateProjectRequest', {
    'name': fields.String(required=True, description='Название проекта'),
    'description': fields.String(required=False, description='Описание проекта'),
    'settings': fields.Raw(required=False, description='Настройки проекта (JSON)'),
    'ai_settings': fields.Raw(required=False, description='AI настройки (JSON)'),
    'is_default': fields.Boolean(required=False, description='Сделать проектом по умолчанию'),
})

update_project_request = projects_ns.model('UpdateProjectRequest', {
    'name': fields.String(required=False, description='Название проекта'),
    'description': fields.String(required=False, description='Описание проекта'),
    'settings': fields.Raw(required=False, description='Настройки проекта (JSON)'),
    'ai_settings': fields.Raw(required=False, description='AI настройки (JSON)'),
    'is_active': fields.Boolean(required=False, description='Активность проекта'),
    'is_default': fields.Boolean(required=False, description='Сделать проектом по умолчанию'),
})

list_response = projects_ns.model('ProjectsList', {
    'success': fields.Boolean,
    'projects': fields.List(fields.Nested(project_model)),
    'count': fields.Integer
})

single_response = projects_ns.model('ProjectResponse', {
    'success': fields.Boolean,
    'project': fields.Nested(project_model)
})

error_model = projects_ns.model('ErrorResponseProjects', {
    'success': fields.Boolean,
    'error': fields.String
})


@projects_ns.route('')
class ProjectsList(Resource):
    @jwt_required
    @projects_ns.doc('list_projects', security='BearerAuth', params={
        'active_only': 'Возвращать только активные (true/false)'
    })
    @projects_ns.response(200, 'OK', list_response)
    def get(self, current_user):
        """Получить список проектов пользователя"""
        db = None
        try:
            user_id = current_user.get('user_id')
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            
            db = get_db_session()
            
            query = db.query(Project).filter(Project.user_id == user_id)
            if active_only:
                query = query.filter(Project.is_active == True)
            
            projects = query.order_by(Project.is_default.desc(), Project.created_at.desc()).all()
            
            return {
                'success': True,
                'projects': [p.to_dict() for p in projects],
                'count': len(projects)
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения проектов: {e}")
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()

    @jwt_required
    @projects_ns.doc('create_project', security='BearerAuth')
    @projects_ns.expect(create_project_request)
    @projects_ns.response(201, 'Created', single_response)
    @projects_ns.response(400, 'Bad Request', error_model)
    def post(self, current_user):
        """Создать новый проект"""
        db = None
        try:
            user_id = current_user.get('user_id')
            data = request.get_json()
            
            if not data.get('name'):
                return {'success': False, 'error': 'Название проекта обязательно'}, 400
            
            db = get_db_session()
            
            # Если это первый проект или запрошено is_default, сбрасываем флаг у других
            is_default = data.get('is_default', False)
            existing_count = db.query(Project).filter(Project.user_id == user_id).count()
            
            if existing_count == 0:
                is_default = True  # Первый проект всегда default
            elif is_default:
                # Сбрасываем default у других проектов
                db.query(Project).filter(
                    Project.user_id == user_id,
                    Project.is_default == True
                ).update({'is_default': False})
            
            project = Project(
                user_id=user_id,
                name=data['name'],
                description=data.get('description'),
                settings=data.get('settings', {}),
                ai_settings=data.get('ai_settings', {}),
                is_default=is_default,
                is_active=True
            )
            
            db.add(project)
            db.commit()
            db.refresh(project)
            
            logger.info(f"Создан проект {project.id} для пользователя {user_id}")
            
            return {
                'success': True,
                'project': project.to_dict()
            }, 201
            
        except Exception as e:
            logger.error(f"Ошибка создания проекта: {e}")
            if db:
                db.rollback()
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()


@projects_ns.route('/<int:project_id>')
@projects_ns.param('project_id', 'ID проекта')
class ProjectResource(Resource):
    @jwt_required
    @projects_ns.doc('get_project', security='BearerAuth')
    @projects_ns.response(200, 'OK', single_response)
    @projects_ns.response(404, 'Not Found', error_model)
    def get(self, current_user, project_id):
        """Получить проект по ID"""
        db = None
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id
            ).first()
            
            if not project:
                return {'success': False, 'error': 'Проект не найден'}, 404
            
            return {
                'success': True,
                'project': project.to_dict()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения проекта: {e}")
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()

    @jwt_required
    @projects_ns.doc('update_project', security='BearerAuth')
    @projects_ns.expect(update_project_request)
    @projects_ns.response(200, 'OK', single_response)
    @projects_ns.response(404, 'Not Found', error_model)
    def put(self, current_user, project_id):
        """Обновить проект"""
        db = None
        try:
            user_id = current_user.get('user_id')
            data = request.get_json()
            
            db = get_db_session()
            
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id
            ).first()
            
            if not project:
                return {'success': False, 'error': 'Проект не найден'}, 404
            
            # Обновляем поля
            if 'name' in data:
                project.name = data['name']
            if 'description' in data:
                project.description = data['description']
            if 'settings' in data:
                # Merge settings
                current_settings = project.settings or {}
                current_settings.update(data['settings'])
                project.settings = current_settings
            if 'ai_settings' in data:
                # Merge ai_settings
                current_ai = project.ai_settings or {}
                current_ai.update(data['ai_settings'])
                project.ai_settings = current_ai
            if 'is_active' in data:
                project.is_active = data['is_active']
            if data.get('is_default'):
                # Сбрасываем default у других проектов
                db.query(Project).filter(
                    Project.user_id == user_id,
                    Project.id != project_id,
                    Project.is_default == True
                ).update({'is_default': False})
                project.is_default = True
            
            db.commit()
            db.refresh(project)
            
            logger.info(f"Обновлен проект {project_id}")
            
            return {
                'success': True,
                'project': project.to_dict()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка обновления проекта: {e}")
            if db:
                db.rollback()
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()

    @jwt_required
    @projects_ns.doc('delete_project', security='BearerAuth')
    @projects_ns.response(200, 'OK')
    @projects_ns.response(404, 'Not Found', error_model)
    @projects_ns.response(400, 'Bad Request', error_model)
    def delete(self, current_user, project_id):
        """Удалить проект"""
        db = None
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id
            ).first()
            
            if not project:
                return {'success': False, 'error': 'Проект не найден'}, 404
            
            # Проверяем, что это не единственный проект
            projects_count = db.query(Project).filter(Project.user_id == user_id).count()
            if projects_count <= 1:
                return {'success': False, 'error': 'Нельзя удалить единственный проект'}, 400
            
            # Если удаляем default проект, назначаем другой
            if project.is_default:
                other_project = db.query(Project).filter(
                    Project.user_id == user_id,
                    Project.id != project_id
                ).first()
                if other_project:
                    other_project.is_default = True
            
            db.delete(project)
            db.commit()
            
            logger.info(f"Удален проект {project_id}")
            
            return {'success': True, 'message': 'Проект удален'}, 200
            
        except Exception as e:
            logger.error(f"Ошибка удаления проекта: {e}")
            if db:
                db.rollback()
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()


@projects_ns.route('/default')
class DefaultProject(Resource):
    @jwt_required
    @projects_ns.doc('get_default_project', security='BearerAuth')
    @projects_ns.response(200, 'OK', single_response)
    @projects_ns.response(404, 'Not Found', error_model)
    def get(self, current_user):
        """Получить проект по умолчанию"""
        db = None
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            
            project = db.query(Project).filter(
                Project.user_id == user_id,
                Project.is_default == True
            ).first()
            
            if not project:
                # Если нет default, возвращаем первый активный
                project = db.query(Project).filter(
                    Project.user_id == user_id,
                    Project.is_active == True
                ).first()
            
            if not project:
                return {'success': False, 'error': 'У вас нет проектов'}, 404
            
            return {
                'success': True,
                'project': project.to_dict()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения default проекта: {e}")
            return {'success': False, 'error': str(e)}, 500
        finally:
            if db:
                db.close()



