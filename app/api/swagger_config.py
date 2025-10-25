"""
Конфигурация Flask-RESTX для Swagger UI
Настройки OpenAPI 3.0 и интеграция с Pydantic схемами
"""

from flask_restx import Api, fields
from typing import Dict, Any, Type
from pydantic import BaseModel
from flask import jsonify
import inspect


def pydantic_to_restx_model(api: Api, pydantic_model: Type[BaseModel], name: str = None) -> fields.Raw:
    """
    Конвертирует Pydantic модель в Flask-RESTX модель
    
    Args:
        api: Flask-RESTX Api объект
        pydantic_model: Pydantic модель
        name: Имя модели (если не указано, берется из класса)
    
    Returns:
        Flask-RESTX модель
    """
    if name is None:
        name = pydantic_model.__name__
    
    # Получаем схему Pydantic
    schema = pydantic_model.model_json_schema()
    
    # Конвертируем в Flask-RESTX поля
    restx_fields = {}
    
    for field_name, field_info in schema.get('properties', {}).items():
        field_type = field_info.get('type')
        field_description = field_info.get('description', '')
        
        # Определяем тип поля Flask-RESTX
        if field_type == 'string':
            restx_fields[field_name] = fields.String(description=field_description)
        elif field_type == 'integer':
            restx_fields[field_name] = fields.Integer(description=field_description)
        elif field_type == 'number':
            restx_fields[field_name] = fields.Float(description=field_description)
        elif field_type == 'boolean':
            restx_fields[field_name] = fields.Boolean(description=field_description)
        elif field_type == 'array':
            items = field_info.get('items', {})
            if items.get('type') == 'string':
                restx_fields[field_name] = fields.List(fields.String, description=field_description)
            elif items.get('type') == 'integer':
                restx_fields[field_name] = fields.List(fields.Integer, description=field_description)
            else:
                restx_fields[field_name] = fields.List(fields.Raw, description=field_description)
        elif field_type == 'object':
            restx_fields[field_name] = fields.Raw(description=field_description)
        else:
            restx_fields[field_name] = fields.Raw(description=field_description)
    
    # Создаем модель Flask-RESTX
    return api.model(name, restx_fields)


def create_swagger_api(app) -> Api:
    """
    Создает и настраивает Flask-RESTX Api объект
    
    Args:
        app: Flask приложение
    
    Returns:
        Настроенный Api объект
    """
    # Настройка JWT авторизации для Swagger UI (OpenAPI 2.0 / Swagger 2.0)
    authorizations = {
        'BearerAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT токен с префиксом Bearer. Формат: "Bearer {ваш_токен}"'
        }
    }
    
    api = Api(
        app,
        version='1.0.0',
        title='AI Content Orchestrator API',
        description='''
        API для управления AI агентами создания контента.
        
        ## Возможности:
        - Создание контента через AI агентов
        - Управление workflow и задачами
        - Мониторинг статуса агентов
        - Анализ трендов и вирусного контента
        - Публикация на различных платформах
        
        ## Аутентификация:
        API использует JWT токены для аутентификации.
        
        ### Как получить токен:
        1. Зарегистрируйтесь через `/auth/register`
        2. Войдите через `/auth/login` и получите `access_token`
        3. Нажмите кнопку "Authorize" вверху страницы
        4. Введите токен в формате: `Bearer <ваш_токен>`
        5. Нажмите "Authorize" и "Close"
        
        ## Примеры использования:
        Смотрите разделы ниже для примеров запросов и ответов.
        ''',
        doc='/api/docs/',
        prefix='/api/v1',
        contact='support@content-orchestrator.ai',
        contact_url='https://content-orchestrator.ai/support',
        license='MIT',
        license_url='https://opensource.org/licenses/MIT',
        authorizations=authorizations,
        security='BearerAuth',
        tags=[
            {'name': 'auth', 'description': 'Аутентификация и авторизация'},
            {'name': 'billing', 'description': 'Биллинг и подписки'},
            {'name': 'webhook', 'description': 'Webhooks'},
            {'name': 'health', 'description': 'Health Check'},
            {'name': 'social-media', 'description': 'Управление социальными сетями (Telegram, Instagram, Twitter)'}
        ]
    )
    
    return api


# Общие модели для всех endpoints
def create_common_models(api: Api) -> Dict[str, fields.Raw]:
    """
    Создает общие модели для API
    
    Args:
        api: Flask-RESTX Api объект
    
    Returns:
        Словарь с общими моделями
    """
    models = {}
    
    # Модель ошибки
    models['error'] = api.model('Error', {
        'error': fields.String(required=True, description='Тип ошибки'),
        'message': fields.String(required=True, description='Сообщение об ошибке'),
        'status_code': fields.Integer(required=True, description='HTTP статус код'),
        'timestamp': fields.String(required=True, description='Время ошибки'),
        'details': fields.Raw(description='Дополнительные детали')
    })
    
    # Модель успешного ответа
    models['success'] = api.model('Success', {
        'success': fields.Boolean(required=True, description='Успешность операции'),
        'message': fields.String(description='Сообщение'),
        'timestamp': fields.String(required=True, description='Время выполнения')
    })
    
    # Модель health check
    models['health'] = api.model('Health', {
        'status': fields.String(required=True, description='Статус сервиса'),
        'timestamp': fields.String(required=True, description='Время проверки'),
        'version': fields.String(required=True, description='Версия сервиса'),
        'service': fields.String(required=True, description='Название сервиса'),
        'details': fields.Raw(description='Дополнительные детали')
    })
    
    # Модель пагинации
    models['pagination'] = api.model('Pagination', {
        'page': fields.Integer(description='Номер страницы', default=1),
        'per_page': fields.Integer(description='Элементов на странице', default=10),
        'total': fields.Integer(description='Общее количество элементов'),
        'pages': fields.Integer(description='Общее количество страниц')
    })
    
    return models


# Примеры данных для документации
EXAMPLE_DATA = {
    'content_request': {
        "title": "Революция в AI: как искусственный интеллект меняет бизнес",
        "description": "Глубокий анализ влияния AI на современный бизнес и перспективы развития",
        "target_audience": "IT-специалисты и бизнес-лидеры",
        "business_goals": [
            "привлечение внимания к инновациям",
            "образование аудитории о возможностях AI",
            "установление экспертного авторитета"
        ],
        "call_to_action": "Подписывайтесь на наш канал для получения экспертных инсайтов",
        "tone": "professional",
        "keywords": ["AI", "искусственный интеллект", "бизнес", "инновации"],
        "platforms": ["telegram", "vk", "twitter"],
        "content_types": ["post", "thread"],
        "test_mode": True
    },
    
    'content_response': {
        "success": True,
        "workflow_id": "47fa6a19-6050-4707-a716-0f2260700b4e",
        "brief_id": "8aa7317b-548a-45dd-871a-f0c130fbc7e3",
        "result": {
            "workflow_id": "47fa6a19-6050-4707-a716-0f2260700b4e",
            "status": "completed",
            "completed_tasks": 6,
            "failed_tasks": 0,
            "total_tasks": 6
        },
        "timestamp": "2024-01-01T12:00:00Z"
    },
    
    'workflow_status': {
        "workflow_id": "47fa6a19-6050-4707-a716-0f2260700b4e",
        "name": "Content Creation Workflow",
        "status": "running",
        "created_at": "2024-01-01T12:00:00Z",
        "total_tasks": 6,
        "completed_tasks": 3,
        "failed_tasks": 0,
        "in_progress_tasks": 1,
        "progress_percentage": 50.0
    },
    
    'agent_status': {
        "agent_id": "chief_001",
        "name": "Chief Content Agent",
        "status": "busy",
        "current_tasks": 2,
        "completed_tasks": 15,
        "error_count": 0,
        "last_activity": "2024-01-01T12:00:00Z",
        "capabilities": {
            "task_types": ["strategy", "planning"],
            "max_concurrent_tasks": 5,
            "specializations": ["content strategy", "audience analysis"],
            "performance_score": 0.95
        }
    },
    
    'system_status': {
        "orchestrator": {
            "status": "running",
            "active_workflows": 3,
            "total_workflows": 25
        },
        "workflows": {
            "total_workflows": 25,
            "pending_tasks": 5,
            "running_tasks": 8,
            "completed_tasks": 12
        },
        "agents": {
            "total_agents": 10,
            "idle_agents": 3,
            "busy_agents": 6,
            "error_agents": 1,
            "active_tasks": 8,
            "completed_tasks": 45,
            "task_assignments": {
                "chief_001": 2,
                "drafting_001": 1,
                "publisher_001": 3
            }
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
}


def get_example_data(endpoint_name: str) -> Dict[str, Any]:
    """
    Получает пример данных для endpoint
    
    Args:
        endpoint_name: Имя endpoint
    
    Returns:
        Пример данных
    """
    return EXAMPLE_DATA.get(endpoint_name, {})
