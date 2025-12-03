"""
API Routes для AI Content Orchestrator
RESTful endpoints для работы с контентом и агентами
Интегрировано с Flask-RESTX для Swagger UI
"""

import asyncio
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from ..orchestrator.main_orchestrator import orchestrator
from ..database.connection import get_db_session
from ..auth.services.auth_service import AuthService
from ..auth.utils.email import EmailService
from .schemas import (
    ContentRequestSchema,
    ContentResponseSchema,
    WorkflowStatusSchema,
    AgentStatusSchema,
    SystemStatusSchema,
    ErrorResponseSchema,
    HealthCheckSchema,
    PlatformStatsSchema,
    ExampleData
)
from .swagger_config import create_common_models, get_example_data

# Настройка логирования
logger = logging.getLogger(__name__)

# ==================== JWT HELPERS ====================

def verify_jwt_token(token):
    """Проверка JWT токена"""
    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY', 'dev-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        return None

def jwt_required(f):
    """Декоратор для проверки JWT токена"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Извлечь токен из Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except:
                return {"error": "Invalid token format. Use: Bearer <token>"}, 401

        if not token:
            return {"error": "Authorization token is missing"}, 401

        # Проверить токен
        payload = verify_jwt_token(token)
        if not payload:
            return {"error": "Invalid or expired token"}, 401

        # Set user_id in Flask global object (like JWTMiddleware does)
        g.current_user_id = payload.get('user_id')
        g.current_user_email = payload.get('email')
        g.current_user_role = payload.get('role')

        # BACKWARD COMPATIBILITY: Pass current_user as parameter for existing endpoints
        # while also setting g.current_user_id for new code
        return f(*args, current_user=payload, **kwargs)

    return decorated_function

# Создаем namespaces для API
api = Namespace('api', description='AI Content Orchestrator API')
auth_ns = Namespace('auth', description='Authentication API')
billing_ns = Namespace('billing', description='Billing API')
webhook_ns = Namespace('webhook', description='Webhook API')
health_ns = Namespace('health', description='Health Check API')
ai_ns = Namespace('ai', description='AI Generation API')

# Создаем общие модели
common_models = create_common_models(api)

# ==================== CONTENT MODELS ====================

content_request_model = api.model('ContentRequest', {
    'title': fields.String(required=True, min_length=1, max_length=200, description='Заголовок контента'),
    'description': fields.String(required=True, min_length=10, max_length=2000, description='Описание контента'),
    'target_audience': fields.String(required=True, min_length=1, max_length=1000, description='Целевая аудитория'),
    'business_goals': fields.List(fields.String, required=True, min_items=1, max_items=10, description='Бизнес-цели'),
    'call_to_action': fields.List(fields.String, max_items=10, description='Призывы к действию'),
    'tone': fields.String(description='Тон контента', enum=['professional', 'casual', 'friendly', 'authoritative'], default='professional'),
    'keywords': fields.List(fields.String, description='Ключевые слова', max_items=20),
    'platforms': fields.List(fields.String, required=False, max_items=5, description='Платформы для публикации'),
    'content_types': fields.List(fields.String, description='Типы контента', default=['post']),
    'constraints': fields.Raw(description='Дополнительные ограничения'),
    'test_mode': fields.Boolean(description='Тестовый режим', default=False),
    'channel_id': fields.Integer(description='ID канала для публикации'),
    'publish_immediately': fields.Boolean(description='Публиковать сразу', default=True),
    'project_id': fields.Integer(description='ID проекта'),
    'uploaded_files': fields.List(fields.String, description='IDs загруженных файлов', max_items=10),
    'reference_urls': fields.List(fields.String, description='URLs референсов', max_items=5),
    'generate_image': fields.Boolean(description='Генерировать изображение', default=False),
    'image_source': fields.String(description='Источник изображения', enum=['stock', 'ai']),
    'variants_count': fields.Integer(description='Количество вариантов', default=1),
    'add_ai_hashtags': fields.Boolean(description='Добавить AI хештеги', default=False)
})

content_response_model = api.model('ContentResponse', {
    'success': fields.Boolean(required=True, description='Успешность операции'),
    'workflow_id': fields.String(required=True, description='ID созданного workflow'),
    'brief_id': fields.String(required=True, description='ID созданного брифа'),
    'result': fields.Raw(description='Результат выполнения'),
    'timestamp': fields.String(required=True, description='Время создания')
})

# ==================== WORKFLOW MODELS ====================

workflow_status_model = api.model('WorkflowStatus', {
    'workflow_id': fields.String(required=True, description='ID workflow'),
    'name': fields.String(description='Название workflow'),
    'status': fields.String(description='Статус', enum=['created', 'running', 'paused', 'completed', 'failed', 'cancelled']),
    'created_at': fields.String(description='Время создания'),
    'total_tasks': fields.Integer(description='Общее количество задач'),
    'completed_tasks': fields.Integer(description='Выполненные задачи'),
    'failed_tasks': fields.Integer(description='Проваленные задачи'),
    'in_progress_tasks': fields.Integer(description='Задачи в процессе'),
    'progress_percentage': fields.Float(description='Процент выполнения')
})

# ==================== AGENT MODELS ====================

agent_capability_model = api.model('AgentCapability', {
    'task_types': fields.List(fields.String, description='Типы задач'),
    'max_concurrent_tasks': fields.Integer(description='Максимум одновременных задач'),
    'specializations': fields.List(fields.String, description='Специализации'),
    'performance_score': fields.Float(description='Оценка производительности')
})

agent_status_model = api.model('AgentStatus', {
    'agent_id': fields.String(required=True, description='ID агента'),
    'name': fields.String(description='Название агента'),
    'status': fields.String(description='Статус агента', enum=['idle', 'busy', 'error', 'offline']),
    'current_tasks': fields.Integer(description='Текущие задачи'),
    'completed_tasks': fields.Integer(description='Выполненные задачи'),
    'error_count': fields.Integer(description='Количество ошибок'),
    'last_activity': fields.String(description='Последняя активность'),
    'capabilities': fields.Nested(agent_capability_model, description='Возможности агента')
})

# ==================== SYSTEM MODELS ====================

system_status_model = api.model('SystemStatus', {
    'orchestrator': fields.Raw(description='Статус оркестратора'),
    'workflows': fields.Raw(description='Статус workflow'),
    'agents': fields.Raw(description='Статус агентов'),
    'timestamp': fields.String(description='Время получения статуса')
})

platform_config_model = api.model('PlatformConfig', {
    'platform': fields.String(description='Название платформы'),
    'supported': fields.Boolean(description='Поддерживается ли платформа'),
    'max_text_length': fields.Integer(description='Максимальная длина текста'),
    'rate_limits': fields.Raw(description='Лимиты API'),
    'supported_formats': fields.List(fields.String, description='Поддерживаемые форматы')
})

platform_stats_model = api.model('PlatformStats', {
    'platforms': fields.Raw(description='Конфигурации платформ'),
    'timestamp': fields.String(description='Время получения статистики')
})

# ==================== TRENDS MODELS ====================

trends_analysis_request_model = api.model('TrendsAnalysisRequest', {
    'analysis_type': fields.String(description='Тип анализа', default='general'),
    'time_period': fields.String(description='Временной период', default='1h'),
    'target_audience': fields.String(description='Целевая аудитория', default='general_audience')
})

trends_analysis_response_model = api.model('TrendsAnalysisResponse', {
    'status': fields.String(description='Статус анализа'),
    'task_id': fields.String(description='ID задачи'),
    'agent_id': fields.String(description='ID агента'),
    'analysis_result': fields.Raw(description='Результат анализа'),
    'execution_time': fields.Float(description='Время выполнения')
})

viral_trends_response_model = api.model('ViralTrendsResponse', {
    'status': fields.String(description='Статус'),
    'viral_trends': fields.Raw(description='Вирусные тренды'),
    'timestamp': fields.String(description='Время получения')
})

# ==================== AUTH MODELS ====================

register_model = auth_ns.model('RegisterRequest', {
    'email': fields.String(required=True, description='Email пользователя'),
    'password': fields.String(required=True, min_length=8, max_length=128, description='Пароль'),
    'username': fields.String(required=True, min_length=3, max_length=100, description='Имя пользователя'),
    'first_name': fields.String(description='Имя'),
    'last_name': fields.String(description='Фамилия'),
    'company': fields.String(description='Компания'),
    'phone': fields.String(description='Телефон')
})

login_model = auth_ns.model('LoginRequest', {
    'email': fields.String(required=True, description='Email пользователя'),
    'password': fields.String(required=True, description='Пароль')
})

user_model = auth_ns.model('User', {
    'id': fields.Integer(description='ID пользователя'),
    'email': fields.String(description='Email'),
    'username': fields.String(description='Имя пользователя'),
    'first_name': fields.String(description='Имя'),
    'last_name': fields.String(description='Фамилия'),
    'company': fields.String(description='Компания'),
    'phone': fields.String(description='Телефон'),
    'role': fields.String(description='Роль'),
    'is_verified': fields.Boolean(description='Email подтвержден'),
    'created_at': fields.String(description='Дата создания'),
    'updated_at': fields.String(description='Дата обновления')
})

auth_response_model = auth_ns.model('AuthResponse', {
    'message': fields.String(description='Сообщение'),
    'access_token': fields.String(description='Access токен'),
    'refresh_token': fields.String(description='Refresh токен'),
    'expires_in': fields.Integer(description='Время жизни токена'),
    'user': fields.Nested(user_model, description='Данные пользователя')
})

session_model = auth_ns.model('Session', {
    'id': fields.Integer(description='ID сессии'),
    'device_info': fields.String(description='Информация об устройстве'),
    'ip_address': fields.String(description='IP адрес'),
    'created_at': fields.String(description='Дата создания'),
    'last_activity': fields.String(description='Последняя активность'),
    'is_active': fields.Boolean(description='Активна ли сессия')
})

change_password_model = auth_ns.model('ChangePasswordRequest', {
    'current_password': fields.String(required=True, description='Текущий пароль'),
    'new_password': fields.String(required=True, min_length=8, max_length=128, description='Новый пароль')
})

update_profile_model = auth_ns.model('UpdateProfileRequest', {
    'first_name': fields.String(description='Имя'),
    'last_name': fields.String(description='Фамилия'),
    'phone': fields.String(description='Телефон'),
    'company': fields.String(description='Компания'),
    'position': fields.String(description='Должность'),
    'timezone': fields.String(description='Часовой пояс'),
    'language': fields.String(description='Язык'),
    'notifications_enabled': fields.Boolean(description='Уведомления включены'),
    'marketing_emails': fields.Boolean(description='Маркетинговые письма')
})

verify_email_model = auth_ns.model('VerifyEmailRequest', {
    'token': fields.String(required=True, description='Токен верификации')
})

password_reset_request_model = auth_ns.model('PasswordResetRequest', {
    'email': fields.String(required=True, description='Email для сброса пароля')
})

password_reset_model = auth_ns.model('PasswordReset', {
    'token': fields.String(required=True, description='Токен сброса'),
    'new_password': fields.String(required=True, min_length=8, max_length=128, description='Новый пароль')
})

refresh_token_model = auth_ns.model('RefreshTokenRequest', {
    'refresh_token': fields.String(required=True, description='Refresh токен')
})

# ==================== BILLING MODELS ====================

plan_limits_model = billing_ns.model('PlanLimits', {
    'posts_per_month': fields.Integer(description='Постов в месяц'),
    'max_agents': fields.Integer(description='Максимум агентов'),
    'platforms': fields.List(fields.String, description='Доступные платформы'),
    'api_calls_per_day': fields.Integer(description='API вызовов в день'),
    'storage_gb': fields.Float(description='Хранилище в ГБ'),
    'support_level': fields.String(description='Уровень поддержки')
})

plan_model = billing_ns.model('Plan', {
    'id': fields.String(description='ID плана'),
    'name': fields.String(description='Название плана'),
    'description': fields.String(description='Описание плана'),
    'price_monthly': fields.Float(description='Цена в месяц'),
    'price_yearly': fields.Float(description='Цена в год'),
    'plan_type': fields.String(description='Тип плана'),
    'limits': fields.Nested(plan_limits_model, description='Лимиты плана'),
    'features': fields.List(fields.String, description='Возможности'),
    'is_popular': fields.Boolean(description='Популярный план'),
    'trial_days': fields.Integer(description='Дни пробного периода')
})

subscription_model = billing_ns.model('Subscription', {
    'id': fields.Integer(description='ID подписки'),
    'plan_id': fields.String(description='ID плана'),
    'status': fields.String(description='Статус подписки'),
    'starts_at': fields.String(description='Дата начала'),
    'expires_at': fields.String(description='Дата окончания'),
    'trial_ends_at': fields.String(description='Дата окончания пробного периода'),
    'auto_renew': fields.Boolean(description='Автопродление'),
    'last_payment_at': fields.String(description='Последний платеж'),
    'next_payment_at': fields.String(description='Следующий платеж')
})

create_subscription_model = billing_ns.model('CreateSubscriptionRequest', {
    'plan_id': fields.String(required=True, description='ID плана'),
    'billing_period': fields.String(description='Период оплаты', enum=['monthly', 'yearly'], default='monthly')
})

payment_model = billing_ns.model('Payment', {
    'id': fields.String(description='ID платежа'),
    'url': fields.String(description='URL для оплаты'),
    'amount': fields.Float(description='Сумма'),
    'currency': fields.String(description='Валюта'),
    'expires_at': fields.String(description='Дата истечения'),
    'status': fields.String(description='Статус платежа')
})

usage_stats_model = billing_ns.model('UsageStats', {
    'posts_used': fields.Integer(description='Использовано постов'),
    'posts_limit': fields.Integer(description='Лимит постов'),
    'api_calls_used': fields.Integer(description='Использовано API вызовов'),
    'api_calls_limit': fields.Integer(description='Лимит API вызовов'),
    'storage_used_gb': fields.Float(description='Использовано хранилища'),
    'storage_limit_gb': fields.Float(description='Лимит хранилища'),
    'agents_used': fields.Integer(description='Использовано агентов'),
    'agents_limit': fields.Integer(description='Лимит агентов'),
    'period_start': fields.String(description='Начало периода'),
    'period_end': fields.String(description='Конец периода')
})

billing_event_model = billing_ns.model('BillingEvent', {
    'id': fields.Integer(description='ID события'),
    'event_type': fields.String(description='Тип события'),
    'event_data': fields.Raw(description='Данные события'),
    'created_at': fields.String(description='Дата создания')
})

cancel_subscription_model = billing_ns.model('CancelSubscriptionRequest', {
    'reason': fields.String(description='Причина отмены', default='user_request')
})

# ==================== WEBHOOK MODELS ====================

webhook_model = webhook_ns.model('WebhookRequest', {
    'event_type': fields.String(description='Тип события'),
    'payment_id': fields.String(description='ID платежа'),
    'metadata': fields.Raw(description='Метаданные')
})

webhook_response_model = webhook_ns.model('WebhookResponse', {
    'status': fields.String(description='Статус обработки'),
    'message': fields.String(description='Сообщение')
})

# ==================== HEALTH MODELS ====================

health_model = health_ns.model('HealthResponse', {
    'status': fields.String(description='Статус системы'),
    'timestamp': fields.String(description='Время проверки'),
    'version': fields.String(description='Версия'),
    'service': fields.String(description='Название сервиса'),
    'details': fields.Raw(description='Детали состояния')
})

# ==================== UTILITY FUNCTIONS ====================

def run_async(coro):
    """Запускает асинхронную функцию в синхронном контексте"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def handle_validation_error(e: ValidationError) -> tuple:
    """Обрабатывает ошибки валидации Pydantic"""
    errors = []
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    # Логируем ошибку валидации для отладки
    logger.error(f"Validation error: {errors}")

    return {
        "error": "Validation Error",
        "message": "Некорректные данные запроса",
        "status_code": 400,
        "timestamp": datetime.now().isoformat(),
        "details": errors
    }, 400


def handle_exception(e: Exception) -> tuple:
    """Обрабатывает общие исключения"""
    logger.error(f"API Error: {str(e)}", exc_info=True)
    return {
        "error": "Internal Server Error",
        "message": "Произошла внутренняя ошибка сервера",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }, 500


# ==================== CONTENT ENDPOINTS ====================

@api.route('/content/create')
class ContentCreate(Resource):
    @api.doc('create_content', description='Создает контент через AI агентов')
    @api.expect(content_request_model, validate=True)
    def post(self):
        """
        Создает контент через AI агентов
        
        Принимает запрос на создание контента и запускает workflow
        с участием всех необходимых агентов.
        """
        try:
            # Получаем данные запроса
            data = request.json or {}
            
            # Преобразуем platforms из строк в PlatformEnum перед валидацией
            if 'platforms' in data and isinstance(data['platforms'], list):
                from app.api.schemas import PlatformEnum
                converted_platforms = []
                for platform in data['platforms']:
                    try:
                        # Преобразуем строку в PlatformEnum
                        if isinstance(platform, str):
                            converted_platforms.append(PlatformEnum(platform.lower()))
                        elif isinstance(platform, PlatformEnum):
                            converted_platforms.append(platform)
                        else:
                            converted_platforms.append(PlatformEnum(str(platform).lower()))
                    except ValueError:
                        return {
                            "error": "Validation Error",
                            "message": f"Некорректная платформа: {platform}. Доступные: {[p.value for p in PlatformEnum]}",
                            "status_code": 400,
                            "timestamp": datetime.now().isoformat()
                        }, 400
                data['platforms'] = converted_platforms
            
            # Объединяем данные из проекта (если указан project_id)
            project_id = data.get('project_id')
            if project_id:
                try:
                    from app.models.project import Project
                    from app.database.connection import get_db_session
                    
                    db = get_db_session()
                    project = db.query(Project).filter(Project.id == project_id).first()
                    
                    if project:
                        project_settings = project.settings or {}
                        project_ai_settings = project.ai_settings or {}
                        
                        # Объединяем настройки проекта с данными запроса
                        # Приоритет у данных запроса (если указаны)
                        
                        # Целевая аудитория
                        if not data.get('target_audience') and project_settings.get('target_audience'):
                            data['target_audience'] = project_settings['target_audience']
                        
                        # Тон (из settings или ai_settings)
                        if not data.get('tone'):
                            tone = project_settings.get('tone_of_voice') or project_ai_settings.get('formality_level')
                            if tone:
                                # Преобразуем formality_level в tone если нужно
                                tone_mapping = {
                                    'formal': 'professional',
                                    'semi-formal': 'professional',
                                    'informal': 'casual'
                                }
                                data['tone'] = tone_mapping.get(tone, tone)
                        
                        # Ключевые слова (объединяем)
                        project_keywords = project_settings.get('keywords', [])
                        survey_keywords = data.get('keywords', [])
                        if isinstance(survey_keywords, list):
                            all_keywords = list(set(project_keywords + survey_keywords))
                            data['keywords'] = all_keywords
                        elif project_keywords:
                            data['keywords'] = project_keywords
                        
                        # CTA (если не указан в запросе)
                        if not data.get('call_to_action') and project_settings.get('default_cta'):
                            data['call_to_action'] = [project_settings['default_cta']]
                        
                        # Сохраняем контекст проекта для промпта
                        data['project_context'] = {
                            'business_description': project_settings.get('business_description', ''),
                            'brand_name': project_settings.get('brand_name', ''),
                            'brand_description': project_settings.get('brand_description', ''),
                            'resource_url': project_settings.get('resource_url', ''),
                            'preferred_style': project_ai_settings.get('preferred_style', ''),
                            'content_length': project_ai_settings.get('content_length', 'medium'),
                            'emoji_usage': project_ai_settings.get('emoji_usage', 'minimal')
                        }
                        
                        logger.info(f"Объединены данные проекта {project_id} с запросом на создание контента")
                    
                    db.close()
                except Exception as e:
                    logger.warning(f"Ошибка загрузки данных проекта {project_id}: {e}. Продолжаем без данных проекта.")
                    # Продолжаем без данных проекта - не ломаем существующий функционал
            
            # Валидируем входные данные
            logger.info(f"Validating content request data: {list(data.keys())}")
            logger.debug(f"Full data: {data}")
            try:
                content_request = ContentRequestSchema(**data)
            except ValidationError as e:
                return handle_validation_error(e)
            
            logger.info(f"Получен запрос на создание контента: {content_request.title}")
            
            # Преобразуем Pydantic модель в словарь
            request_data = content_request.dict()
            
            # Запускаем обработку через оркестратор
            result = run_async(orchestrator.process_content_request(request_data))
            
            if result["success"]:
                logger.info(f"Контент успешно создан: {result['workflow_id']}")

                # Формируем ответ
                response_data = {
                    "success": True,
                    "workflow_id": result["workflow_id"],
                    "brief_id": result["brief_id"],
                    "result": result["result"],
                    "timestamp": datetime.now().isoformat()
                }

                # Возвращаем ответ БЕЗ Flask-RESTX marshalling
                from flask import make_response, jsonify
                response = make_response(jsonify(response_data), 201)
                response.headers['Content-Type'] = 'application/json'
                return response
            else:
                logger.error(f"Ошибка создания контента: {result['error']}")
                return {
                    "error": "Content Creation Failed",
                    "message": result["error"],
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
                
        except Exception as e:
            return handle_exception(e)


@api.route('/content/example')
class ContentExample(Resource):
    @api.doc('get_content_example', description='Возвращает пример запроса на создание контента')
    def get(self):
        """
        Возвращает пример запроса на создание контента
        """
        return {
            "description": "Пример запроса на создание контента",
            "example": get_example_data('content_request'),
            "schema": "ContentRequestSchema"
        }


@api.route('/upload')
class FileUpload(Resource):
    @jwt_required
    @api.doc('upload_file', security='BearerAuth', description='Загружает файл (изображение) на сервер')
    @api.response(200, 'OK')
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    @api.response(500, 'Internal Server Error')
    def post(self, current_user):
        """
        Загружает файл на сервер
        
        Принимает multipart/form-data с полем 'file'
        Возвращает ID загруженного файла для использования в content/create
        """
        try:
            from werkzeug.utils import secure_filename
            from ..services.storage_service import StorageService
            from ..models.uploads import FileUploadDB
            import uuid
            import asyncio
            
            user_id = current_user.get('user_id')
            if not user_id:
                return {
                    "error": "Unauthorized",
                    "message": "Пользователь не авторизован",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Проверяем наличие файла
            if 'file' not in request.files:
                return {
                    "error": "Bad Request",
                    "message": "Файл не предоставлен",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            file = request.files['file']
            if file.filename == '':
                return {
                    "error": "Bad Request",
                    "message": "Имя файла пустое",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Проверяем тип файла (только изображения)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in allowed_extensions:
                return {
                    "error": "Bad Request",
                    "message": f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_extensions)}",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Читаем содержимое файла
            file_content = file.read()
            file_size = len(file_content)
            
            # Проверяем размер (максимум 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                return {
                    "error": "Bad Request",
                    "message": f"Файл слишком большой. Максимальный размер: 10MB",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Загружаем файл в GCS
            storage_service = StorageService()
            upload_result = asyncio.run(
                storage_service.upload_file(
                    file_content=file_content,
                    filename=filename,
                    user_id=str(user_id),
                    folder="content_images",
                    optimize=True
                )
            )
            
            if not upload_result.get('success'):
                return {
                    "error": "Upload Failed",
                    "message": upload_result.get('error', 'Не удалось загрузить файл'),
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
            
            # Сохраняем информацию о файле в БД
            db = get_db_session()
            try:
                file_id = str(uuid.uuid4())
                file_upload = FileUploadDB(
                    id=file_id,
                    user_id=user_id,
                    filename=upload_result['filename'],
                    original_filename=filename,
                    file_type='image',
                    mime_type=upload_result['content_type'],
                    size_bytes=upload_result['size_bytes'],
                    storage_url=upload_result['url'],
                    storage_bucket=upload_result['bucket'],
                    storage_path=upload_result['path'],
                    is_public=True
                )
                
                db.add(file_upload)
                db.commit()
                db.refresh(file_upload)
                
                logger.info(f"Файл {filename} загружен пользователем {user_id}, ID: {file_id}")
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "url": upload_result['url'],
                    "filename": upload_result['filename'],
                    "size_bytes": upload_result['size_bytes'],
                    "timestamp": datetime.now().isoformat()
                }, 200
                
            except Exception as e:
                db.rollback()
                logger.error(f"Ошибка сохранения файла в БД: {e}")
                return {
                    "error": "Database Error",
                    "message": f"Не удалось сохранить информацию о файле: {str(e)}",
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {e}", exc_info=True)
            return {
                "error": "Internal Server Error",
                "message": f"Внутренняя ошибка сервера: {str(e)}",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


# ==================== WORKFLOW ENDPOINTS ====================

@api.route('/workflow/<string:workflow_id>/status')
class WorkflowStatus(Resource):
    @api.doc('get_workflow_status', description='Получает статус workflow по ID')
    @api.marshal_with(workflow_status_model, code=200, description='Статус workflow')
    @api.marshal_with(common_models['error'], code=404, description='Workflow не найден')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, workflow_id):
        """
        Получает статус workflow по ID
        """
        try:
            logger.info(f"Запрос статуса workflow: {workflow_id}")
            
            # Получаем статус workflow
            status = orchestrator.get_workflow_status(workflow_id)
            
            if status:
                return status, 200
            else:
                return {
                    "error": "Workflow Not Found",
                    "message": f"Workflow с ID {workflow_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
                
        except Exception as e:
            return handle_exception(e)


@api.route('/workflow/<string:workflow_id>/cancel')
class WorkflowCancel(Resource):
    @api.doc('cancel_workflow', description='Отменяет выполнение workflow')
    @api.marshal_with(common_models['success'], code=200, description='Workflow отменен')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self, workflow_id):
        """
        Отменяет выполнение workflow
        """
        try:
            logger.info(f"Запрос на отмену workflow: {workflow_id}")
            
            # В реальной реализации здесь была бы логика отмены workflow
            # Пока возвращаем заглушку
            return {
                "success": True,
                "message": f"Workflow {workflow_id} отменен",
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            return handle_exception(e)


# ==================== AGENT ENDPOINTS ====================

@api.route('/agents/status')
class AgentsStatus(Resource):
    @api.doc('get_agents_status', description='Получает статус всех агентов или конкретного агента')
    @api.param('agent_id', 'ID конкретного агента (опционально)', type='string')
    @api.marshal_with(agent_status_model, code=200, description='Статус агента')
    @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Получает статус всех агентов или конкретного агента
        """
        try:
            agent_id = request.args.get('agent_id')
            
            if agent_id:
                # Статус конкретного агента
                logger.info(f"Запрос статуса агента: {agent_id}")
                status = orchestrator.get_agent_status(agent_id)
                
                if status:
                    return status, 200
                else:
                    return {
                        "error": "Agent Not Found",
                        "message": f"Агент с ID {agent_id} не найден",
                        "status_code": 404,
                        "timestamp": datetime.now().isoformat()
                    }, 404
            else:
                # Статус всех агентов
                logger.info("Запрос статуса всех агентов")
                status = orchestrator.get_all_agents_status()
                return status, 200
                
        except Exception as e:
            return handle_exception(e)


@api.route('/agents/<string:agent_id>/tasks')
class AgentTasks(Resource):
    @api.doc('get_agent_tasks', description='Получает список задач конкретного агента')
    @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, agent_id):
        """
        Получает список задач конкретного агента
        """
        try:
            logger.info(f"Запрос задач агента: {agent_id}")
            
            # Получаем статус агента
            agent_status = orchestrator.get_agent_status(agent_id)
            
            if not agent_status:
                return {
                    "error": "Agent Not Found",
                    "message": f"Агент с ID {agent_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            # Формируем ответ с задачами
            response = {
                "agent_id": agent_id,
                "agent_name": agent_status["name"],
                "current_tasks": agent_status["current_tasks"],
                "completed_tasks": agent_status["completed_tasks"],
                "status": agent_status["status"],
                "timestamp": datetime.now().isoformat()
            }
            
            return response, 200
            
        except Exception as e:
            return handle_exception(e)


# ==================== SYSTEM ENDPOINTS ====================

@api.route('/system/status')
class SystemStatus(Resource):
    @api.doc('get_system_status', description='Получает общий статус системы')
    @api.marshal_with(system_status_model, code=200, description='Статус системы')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Получает общий статус системы
        """
        try:
            logger.info("Запрос статуса системы")
            
            status = orchestrator.get_system_status()
            return status, 200
            
        except Exception as e:
            return handle_exception(e)


@api.route('/system/health')
class SystemHealth(Resource):
    @api.doc('get_system_health', description='Проверка здоровья системы')
    @api.marshal_with(common_models['health'], code=200, description='Система здорова')
    @api.marshal_with(common_models['health'], code=503, description='Система нездорова')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Проверка здоровья системы
        """
        try:
            # Получаем базовый статус
            system_status = orchestrator.get_system_status()
            
            # Определяем общее состояние
            total_agents = system_status["agents"]["total_agents"]
            error_agents = system_status["agents"]["error_agents"]
            
            if error_agents == 0 and total_agents > 0:
                health_status = "healthy"
            elif error_agents < total_agents:
                health_status = "degraded"
            else:
                health_status = "unhealthy"
            
            response = {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "AI Content Orchestrator",
                "details": {
                    "total_agents": total_agents,
                    "error_agents": error_agents,
                    "active_tasks": system_status["agents"]["active_tasks"],
                    "completed_tasks": system_status["agents"]["completed_tasks"]
                }
            }
            
            status_code = 200 if health_status == "healthy" else 503
            return response, status_code
            
        except Exception as e:
            return handle_exception(e)


@api.route('/system/metrics')
class SystemMetrics(Resource):
    @api.doc('get_system_metrics', description='Получает метрики системы')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Получает метрики системы
        """
        try:
            logger.info("Запрос метрик системы")
            
            system_status = orchestrator.get_system_status()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "total": system_status["agents"]["total_agents"],
                    "idle": system_status["agents"]["idle_agents"],
                    "busy": system_status["agents"]["busy_agents"],
                    "error": system_status["agents"]["error_agents"]
                },
                "workflows": {
                    "total": system_status["workflows"]["total_workflows"],
                    "pending_tasks": system_status["workflows"]["pending_tasks"],
                    "running_tasks": system_status["workflows"]["running_tasks"],
                    "completed_tasks": system_status["workflows"]["completed_tasks"]
                },
                "performance": {
                    "active_tasks": system_status["agents"]["active_tasks"],
                    "completed_tasks": system_status["agents"]["completed_tasks"],
                    "task_assignments": system_status["agents"]["task_assignments"]
                }
            }
            
            return metrics, 200
            
        except Exception as e:
            return handle_exception(e)


# ==================== PLATFORM ENDPOINTS ====================

@api.route('/platforms')
class Platforms(Resource):
    @api.doc('get_platforms', description='Получает список поддерживаемых платформ')
    @api.marshal_with(platform_stats_model, code=200, description='Список платформ')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Получает список поддерживаемых платформ
        """
        try:
            logger.info("Запрос списка платформ")
            
            # Получаем статистику платформ от PublisherAgent
            publisher_agent = None
            for agent in orchestrator.agent_manager.agents.values():
                if hasattr(agent, 'get_platform_stats'):
                    publisher_agent = agent
                    break
            
            if publisher_agent:
                platform_stats = publisher_agent.get_platform_stats()
            else:
                # Fallback данные
                platform_stats = {
                    "telegram": {
                        "supported": True,
                        "max_text_length": 4096,
                        "rate_limits": {"posts_per_hour": 30},
                        "supported_formats": ["text", "image", "video"]
                    },
                    "vk": {
                        "supported": True,
                        "max_text_length": 1000,
                        "rate_limits": {"posts_per_hour": 100},
                        "supported_formats": ["text", "image", "video"]
                    },
                    "twitter": {
                        "supported": True,
                        "max_text_length": 280,
                        "rate_limits": {"posts_per_hour": 300},
                        "supported_formats": ["text", "image", "video"]
                    }
                }
            
            return {
                "platforms": platform_stats,
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@api.route('/platforms/<string:platform>/config')
class PlatformConfig(Resource):
    @api.doc('get_platform_config', description='Получает конфигурацию конкретной платформы')
    @api.marshal_with(platform_config_model, code=200, description='Конфигурация платформы')
    @api.marshal_with(common_models['error'], code=404, description='Платформа не найдена')
    @api.marshal_with(common_models['error'], code=503, description='Сервис недоступен')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, platform):
        """
        Получает конфигурацию конкретной платформы
        """
        try:
            logger.info(f"Запрос конфигурации платформы: {platform}")
            
            # Получаем конфигурацию платформы
            publisher_agent = None
            for agent in orchestrator.agent_manager.agents.values():
                if hasattr(agent, 'get_platform_stats'):
                    publisher_agent = agent
                    break
            
            if publisher_agent:
                platform_stats = publisher_agent.get_platform_stats()
                if platform in platform_stats:
                    return {
                        "platform": platform,
                        "config": platform_stats[platform],
                        "timestamp": datetime.now().isoformat()
                    }, 200
                else:
                    return {
                        "error": "Platform Not Found",
                        "message": f"Платформа {platform} не поддерживается",
                        "status_code": 404,
                        "timestamp": datetime.now().isoformat()
                    }, 404
            else:
                return {
                    "error": "Service Unavailable",
                    "message": "Сервис платформ недоступен",
                    "status_code": 503,
                    "timestamp": datetime.now().isoformat()
                }, 503
                
        except Exception as e:
            return handle_exception(e)


# ==================== TRENDS ANALYSIS ENDPOINTS ====================

@api.route('/trends/analyze')
class TrendsAnalyze(Resource):
    @api.doc('analyze_trends', description='Анализ трендов через TrendsScoutAgent')
    @api.expect(trends_analysis_request_model, validate=True)
    @api.marshal_with(trends_analysis_response_model, code=200, description='Анализ трендов выполнен')
    @api.marshal_with(common_models['error'], code=400, description='Некорректные данные')
    @api.marshal_with(common_models['error'], code=503, description='Агент недоступен')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Анализ трендов через TrendsScoutAgent"""
        try:
            data = request.get_json()
            if not data:
                return {
                    "error": "Invalid request",
                    "message": "Требуется JSON данные",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Извлекаем параметры
            analysis_type = data.get('analysis_type', 'general')
            time_period = data.get('time_period', '1h')
            target_audience = data.get('target_audience', 'general_audience')
            
            # Находим TrendsScoutAgent
            trends_agent = None
            for agent in orchestrator.agent_manager.agents.values():
                if hasattr(agent, 'trend_analyzer'):  # Проверяем, что это TrendsScoutAgent
                    trends_agent = agent
                    break
            
            if not trends_agent:
                return {
                    "error": "Agent not available",
                    "message": "TrendsScoutAgent недоступен",
                    "status_code": 503,
                    "timestamp": datetime.now().isoformat()
                }, 503
            
            # Создаем задачу для анализа трендов
            from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
            
            task = Task(
                id=f"trends_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name="Trends Analysis",
                task_type=TaskType.REAL_TIME,
                priority=TaskPriority.HIGH,
                context={
                    'analysis_type': analysis_type,
                    'time_period': time_period,
                    'target_audience': target_audience
                }
            )
            
            # Выполняем анализ
            result = run_async(trends_agent.execute_task(task))
            
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'task_id': result['task_id'],
                    'agent_id': result['agent_id'],
                    'analysis_result': result['result'],
                    'execution_time': result['execution_time']
                }, 200
            else:
                return {
                    "error": "Analysis failed",
                    "message": f"Ошибка анализа трендов: {result.get('error', 'Unknown error')}",
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return {
                "error": "Internal server error",
                "message": f"Ошибка анализа трендов: {str(e)}",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


# ==================== PROJECT ENDPOINTS ====================

# project_model, create_project_model, update_project_model removed - use projects_ns.py models instead

# /projects endpoint removed - use projects_ns.py instead with proper JWT auth and validation


# /projects/<int:project_id> endpoint removed - use projects_ns.py instead


@api.route('/projects/<int:project_id>/auto-fill')
class ProjectAutoFill(Resource):
    @api.doc('auto_fill_project', description='Автоматически заполняет настройки проекта на основе Telegram канала')
    @jwt_required
    def post(self, project_id, current_user=None):
        """Автоматически заполняет настройки проекта на основе связанного Telegram канала"""
        try:
            from app.models.project import Project
            from app.models.telegram_channels import TelegramChannel
            from app.database.connection import get_db_session
            from flask import make_response, jsonify

            db = get_db_session()

            # Получаем проект
            project = db.query(Project).filter(
                Project.id == project_id
            ).first()

            if not project:
                db.close()
                return {
                    "error": "Not Found",
                    "message": f"Проект {project_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404

            # Ищем связанный Telegram канал
            telegram_channel = db.query(TelegramChannel).filter(
                TelegramChannel.project_id == project_id,
                TelegramChannel.is_active == True
            ).first()

            if not telegram_channel:
                db.close()
                return {
                    "error": "Not Found",
                    "message": f"Не найден активный Telegram канал для проекта {project_id}",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404

            # Автоматически заполняем настройки проекта на основе данных Telegram канала
            settings = project.settings or {}

            # Обновляем настройки с данными из Telegram
            settings.update({
                'telegram': {
                    'channel_id': telegram_channel.id,
                    'channel_name': telegram_channel.channel_name,
                    'channel_username': telegram_channel.channel_username,
                    'chat_id': telegram_channel.chat_id,
                    'channel_link': f"https://t.me/{telegram_channel.channel_username.lstrip('@')}" if telegram_channel.channel_username else None,
                    'members_count': telegram_channel.members_count,
                    'auto_filled_at': datetime.now().isoformat()
                },
                'content_strategy': {
                    'target_audience': f"Подписчики канала {telegram_channel.channel_name}",
                    'platform': 'telegram',
                    'tone': 'professional' if telegram_channel.members_count and telegram_channel.members_count > 1000 else 'friendly'
                }
            })

            # Если название проекта пустое или дефолтное, обновляем его
            if not project.name or project.name in ['Новый проект', 'New Project']:
                project.name = telegram_channel.channel_name

            # Если описание пустое, добавляем описание на основе канала
            if not project.description:
                project.description = f"Контент-проект для Telegram канала {telegram_channel.channel_name}"
                if telegram_channel.members_count:
                    project.description += f" ({telegram_channel.members_count} подписчиков)"

            project.settings = settings
            db.commit()
            db.refresh(project)

            # Получаем словарь проекта
            result = project.to_dict()
            db.close()

            logger.info(f"Автозаполнение проекта {project_id} выполнено на основе Telegram канала {telegram_channel.id}")

            # Возвращаем ответ БЕЗ Flask-RESTX marshalling
            response = make_response(jsonify(result), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        except Exception as e:
            logger.error(f"Ошибка автозаполнения проекта: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": "Internal server error",
                "message": f"Ошибка автозаполнения проекта: {str(e)}",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@api.route('/trends/viral')
class ViralTrends(Resource):
    @api.doc('get_viral_trends', description='Получает вирусные тренды')
    @api.marshal_with(viral_trends_response_model, code=200, description='Вирусные тренды получены')
    @api.marshal_with(common_models['error'], code=503, description='Агент недоступен')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получает вирусные тренды"""
        try:
            # Находим TrendsScoutAgent
            trends_agent = None
            for agent in orchestrator.agent_manager.agents.values():
                if hasattr(agent, 'trend_analyzer'):
                    trends_agent = agent
                    break
            
            if not trends_agent:
                return {
                    "error": "Agent not available",
                    "message": "TrendsScoutAgent недоступен",
                    "status_code": 503,
                    "timestamp": datetime.now().isoformat()
                }, 503
            
            # Создаем задачу для анализа вирусного контента
            from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
            
            task = Task(
                id=f"viral_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name="Viral Content Analysis",
                task_type=TaskType.REAL_TIME,
                priority=TaskPriority.HIGH,
                context={
                    'analysis_type': 'viral_content',
                    'time_period': '1h',
                    'target_audience': 'general_audience'
                }
            )
            
            # Выполняем анализ
            result = run_async(trends_agent.execute_task(task))
            
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'viral_trends': result['result'],
                    'timestamp': datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Analysis failed",
                    "message": f"Ошибка получения вирусных трендов: {result.get('error', 'Unknown error')}",
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
            
        except Exception as e:
            logger.error(f"Ошибка получения вирусных трендов: {e}")
            return {
                "error": "Internal server error",
                "message": f"Ошибка получения вирусных трендов: {str(e)}",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


# ==================== DOCUMENTATION ENDPOINTS ====================

@api.route('/docs')
class ApiDocs(Resource):
    @api.doc('get_api_docs', description='Возвращает документацию API')
    def get(self):
        """
        Возвращает документацию API
        """
        docs = {
            "title": "AI Content Orchestrator API",
            "version": "1.0.0",
            "description": "API для управления AI агентами создания контента",
            "endpoints": {
                "content": {
                    "POST /content/create": "Создать контент",
                    "GET /content/example": "Пример запроса на создание контента"
                },
                "workflow": {
                    "GET /workflow/{id}/status": "Статус workflow",
                    "POST /workflow/{id}/cancel": "Отменить workflow"
                },
                "agents": {
                    "GET /agents/status": "Статус агентов",
                    "GET /agents/{id}/tasks": "Задачи агента"
                },
                "system": {
                    "GET /system/status": "Статус системы",
                    "GET /system/health": "Здоровье системы",
                    "GET /system/metrics": "Метрики системы"
                },
                "platforms": {
                    "GET /platforms": "Список платформ",
                    "GET /platforms/{name}/config": "Конфигурация платформы"
                },
                "trends": {
                    "POST /trends/analyze": "Анализ трендов",
                    "GET /trends/viral": "Вирусные тренды"
                },
                "projects": {
                    "GET /projects": "Список проектов",
                    "POST /projects": "Создать проект",
                    "GET /projects/{id}": "Получить проект",
                    "PUT /projects/{id}": "Обновить проект",
                    "DELETE /projects/{id}": "Удалить проект"
                }
            },
            "schemas": {
                "ContentRequest": "Схема запроса на создание контента",
                "ContentResponse": "Схема ответа с результатом",
                "WorkflowStatus": "Схема статуса workflow",
                "AgentStatus": "Схема статуса агента",
                "SystemStatus": "Схема статуса системы"
            },
            "examples": {
                "content_request": get_example_data('content_request'),
                "content_response": get_example_data('content_response'),
                "error_response": {
                    "error": "Validation Error",
                    "message": "Некорректные данные запроса",
                    "status_code": 400,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "details": {
                        "field": "title",
                        "issue": "Поле обязательно для заполнения"
                    }
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return docs, 200


@api.route('/docs/schemas')
class ApiSchemas(Resource):
    @api.doc('get_schemas', description='Возвращает JSON схемы для валидации')
    def get(self):
        """
        Возвращает JSON схемы для валидации
        """
        try:
            # В реальной реализации здесь были бы JSON схемы
            # Пока возвращаем описание схем
            schemas = {
                "schemas": {
                    "ContentRequestSchema": {
                        "type": "object",
                        "required": ["title", "description", "target_audience", "business_goals", "call_to_action", "platforms"],
                        "properties": {
                            "title": {"type": "string", "minLength": 1, "maxLength": 200},
                            "description": {"type": "string", "minLength": 10, "maxLength": 1000},
                            "target_audience": {"type": "string", "minLength": 1, "maxLength": 200},
                            "business_goals": {"type": "array", "items": {"type": "string"}},
                            "call_to_action": {"type": "string", "minLength": 1, "maxLength": 200},
                            "tone": {"type": "string", "enum": ["professional", "casual", "friendly", "authoritative"]},
                            "keywords": {"type": "array", "items": {"type": "string"}},
                            "platforms": {"type": "array", "items": {"type": "string"}},
                            "content_types": {"type": "array", "items": {"type": "string"}},
                            "test_mode": {"type": "boolean"}
                        }
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return schemas, 200
            
        except Exception as e:
            return handle_exception(e)


# ==================== AUTH ENDPOINTS ====================

def mock_auth_service():
    """Заглушка для auth сервиса"""
    return {"status": "mock", "message": "Auth service placeholder"}

def validate_auth_data(data, required_fields):
    """Валидация данных аутентификации"""
    if not data:
        return False, "Данные не предоставлены"
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Поле '{field}' обязательно"
    
    return True, "OK"

@auth_ns.route('/register')
class AuthRegister(Resource):
    @auth_ns.doc('register_user', description='Регистрация нового пользователя')
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.marshal_with(auth_response_model, code=201, description='Пользователь успешно зарегистрирован')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Регистрация нового пользователя"""
        try:
            data = request.get_json()
            
            # Валидация обязательных полей
            required_fields = ['email', 'password', 'username']
            is_valid, error_message = validate_auth_data(data, required_fields)
            
            if not is_valid:
                return {
                    "error": "Validation Error",
                    "message": error_message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Дополнительная валидация email
            email = data.get('email', '')
            if '@' not in email or '.' not in email:
                return {
                    "error": "Validation Error",
                    "message": "Некорректный email",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Валидация пароля
            password = data.get('password', '')
            if len(password) < 8:
                return {
                    "error": "Validation Error",
                    "message": "Пароль должен содержать минимум 8 символов",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Валидация username
            username = data.get('username', '')
            if len(username) < 3:
                return {
                    "error": "Validation Error",
                    "message": "Имя пользователя должно содержать минимум 3 символа",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Регистрация через AuthService
            db_session = get_db_session()
            secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY', 'dev-secret-key')
            email_service = EmailService()
            auth_service = AuthService(db_session, secret_key, email_service)
            
            success, message, user = auth_service.register_user(
                email=email,
                password=password,
                username=username,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            
            if not success:
                return {
                    "error": "Registration Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Успешная регистрация
            return {
                "message": message,
                "user": user.to_dict() if hasattr(user, 'to_dict') else user
            }, 201
                
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}", exc_info=True)
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/login')
class AuthLogin(Resource):
    @auth_ns.doc('login_user', description='Авторизация пользователя')
    @auth_ns.expect(login_model, validate=True)
    # ALL marshal_with decorators DISABLED to fix null tokens issue
    # Flask-RESTX marshalling was converting tokens to null
    # @auth_ns.marshal_with(auth_response_model, code=200, description='Успешная авторизация')
    # @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    # @auth_ns.marshal_with(common_models['error'], code=401, description='Неверные учетные данные')
    # @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Авторизация пользователя"""
        try:
            data = request.get_json()
            
            # Валидация обязательных полей
            required_fields = ['email', 'password']
            is_valid, error_message = validate_auth_data(data, required_fields)
            
            if not is_valid:
                return {
                    "error": "Validation Error",
                    "message": error_message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            email = data.get('email', '')
            password = data.get('password', '')
            
            # Валидация email
            if '@' not in email or '.' not in email:
                return {
                    "error": "Validation Error",
                    "message": "Некорректный email",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Получаем сессию БД и инициализируем AuthService
            db_session = get_db_session()
            # Используем JWT_SECRET_KEY если доступен, иначе SECRET_KEY
            secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY', 'dev-secret-key')
            email_service = EmailService()
            auth_service = AuthService(db_session, secret_key, email_service)
            
            # Получение информации об устройстве
            device_info = {
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
            
            # Авторизация через реальный сервис
            success, message, tokens = auth_service.login_user(
                email,
                password,
                device_info=device_info,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            if not success or not tokens:
                return {
                    "error": "Authentication Failed",
                    "message": message or "Неверный email или пароль",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401

            # Логирование полученных токенов
            logger.info(f"=== LOGIN ENDPOINT DEBUG ===")
            logger.info(f"tokens dict keys: {list(tokens.keys()) if tokens else 'NULL'}")
            logger.info(f"access_token type: {type(tokens.get('access_token'))}, value: {tokens.get('access_token', 'NONE')[:20] if tokens.get('access_token') else 'NULL'}...")
            logger.info(f"refresh_token type: {type(tokens.get('refresh_token'))}, value: {tokens.get('refresh_token', 'NONE')[:20] if tokens.get('refresh_token') else 'NULL'}...")
            logger.info(f"expires_in: {tokens.get('expires_in')}")

            # Успешная авторизация
            response_data = {
                "message": message,
                "access_token": tokens.get('access_token'),
                "refresh_token": tokens.get('refresh_token'),
                "expires_in": tokens.get('expires_in', 3600),
                "user": tokens.get('user', {})
            }

            logger.info(f"Response data before marshal: {dict((k, v[:20] + '...' if isinstance(v, str) and len(v) > 20 and k != 'user' else v) for k, v in response_data.items())}")

            # Return response WITHOUT Flask-RESTX marshalling to avoid null tokens issue
            from flask import make_response, jsonify
            response = make_response(jsonify(response_data), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
                
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}", exc_info=True)
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/verify-email')
class AuthVerifyEmail(Resource):
    @auth_ns.doc('verify_email', description='Верификация email')
    @auth_ns.expect(verify_email_model, validate=True)
    @auth_ns.marshal_with(common_models['success'], code=200, description='Email успешно подтвержден')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Верификация email"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            success, message = auth_service.verify_email(data['token'])
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Verification Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/resend-verification')
class AuthResendVerification(Resource):
    @auth_ns.doc('resend_verification', description='Повторная отправка email верификации')
    @auth_ns.marshal_with(common_models['success'], code=200, description='Письмо отправлено')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Повторная отправка email верификации"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            data = request.get_json()
            if not data or 'email' not in data:
                return {
                    "error": "Validation Error",
                    "message": "Email не предоставлен",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            success, message = auth_service.resend_verification_email(data['email'])
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Resend Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/forgot-password')
class AuthForgotPassword(Resource):
    @auth_ns.doc('forgot_password', description='Запрос сброса пароля')
    @auth_ns.expect(password_reset_request_model, validate=True)
    @auth_ns.marshal_with(common_models['success'], code=200, description='Письмо для сброса пароля отправлено')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Запрос сброса пароля"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            success, message = auth_service.request_password_reset(data['email'])
            
            return {
                "success": True,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }, 200
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/reset-password')
class AuthResetPassword(Resource):
    @auth_ns.doc('reset_password', description='Сброс пароля')
    @auth_ns.expect(password_reset_model, validate=True)
    @auth_ns.marshal_with(common_models['success'], code=200, description='Пароль успешно сброшен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Сброс пароля"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            success, message = auth_service.reset_password(
                data['token'],
                data['new_password']
            )
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Reset Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/refresh')
class AuthRefresh(Resource):
    @auth_ns.doc('refresh_token', description='Обновление токена')
    @auth_ns.expect(refresh_token_model, validate=True)
    @auth_ns.marshal_with(auth_response_model, code=200, description='Токен успешно обновлен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Неверный токен')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Обновление токена"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            success, message, tokens = auth_service.refresh_token(data['refresh_token'])
            
            if success:
                return {
                    "message": message,
                    **tokens
                }, 200
            else:
                return {
                    "error": "Refresh Failed",
                    "message": message,
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/logout')
class AuthLogout(Resource):
    @auth_ns.doc('logout_user', description='Выход пользователя')
    @auth_ns.marshal_with(common_models['success'], code=200, description='Успешный выход')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Выход пользователя"""
        try:
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            
            if not token or len(token) < 10:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Проверяем JWT токен
            payload = verify_jwt_token(token)
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный или истекший токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Успешный выход (токен валиден, клиент удалит его на своей стороне)
            return {
                "success": True,
                "message": "Успешный выход из системы",
                "timestamp": datetime.now().isoformat()
            }, 200
                
        except Exception as e:
            logger.error(f"Ошибка выхода: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/logout-all')
class AuthLogoutAll(Resource):
    @auth_ns.doc('logout_all_sessions', description='Выход из всех сессий')
    @auth_ns.marshal_with(common_models['success'], code=200, description='Успешный выход из всех сессий')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Выход из всех сессий"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            from ..auth.middleware.jwt import JWTMiddleware
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            jwt_middleware = JWTMiddleware(auth_service)
            
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_middleware.verify_token(token)
            
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            user_id = payload.get('user_id')
            success, message = auth_service.logout_all_sessions(user_id)
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Logout Failed",
                    "message": message,
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/me')
class AuthMe(Resource):
    @auth_ns.doc('get_current_user', description='Получить информацию о текущем пользователе')
    @auth_ns.marshal_with(user_model, code=200, description='Информация о пользователе')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить информацию о текущем пользователе"""
        try:
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            
            if not token or len(token) < 10:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Проверяем JWT токен
            payload = verify_jwt_token(token)
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный или истекший токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Получаем пользователя из БД
            user_id = payload.get('user_id')
            if not user_id:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            from ..auth.models.user import User
            db_session = get_db_session()
            user = db_session.query(User).filter(User.id == user_id).first()
            
            if not user:
                db_session.close()
                return {
                    "error": "Unauthorized",
                    "message": "Пользователь не найден",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            # Возвращаем информацию о пользователе
            user_data = user.to_dict()
            db_session.close()
            
            return {
                "user": user_data
            }, 200
                
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}", exc_info=True)
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/profile')
class AuthProfile(Resource):
    @auth_ns.doc('update_profile', description='Обновление профиля пользователя')
    @auth_ns.expect(update_profile_model, validate=True)
    @auth_ns.marshal_with(user_model, code=200, description='Профиль успешно обновлен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def put(self):
        """Обновление профиля пользователя"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            from ..auth.middleware.jwt import JWTMiddleware
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            jwt_middleware = JWTMiddleware(auth_service)
            
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_middleware.verify_token(token)
            
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            user_id = payload.get('user_id')
            success, message, user = auth_service.update_user_profile(user_id, **data)
            
            if success:
                return {
                    "message": message,
                    "user": user.to_dict() if user else None
                }, 200
            else:
                return {
                    "error": "Update Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/change-password')
class AuthChangePassword(Resource):
    @auth_ns.doc('change_password', description='Смена пароля')
    @auth_ns.expect(change_password_model, validate=True)
    @auth_ns.marshal_with(common_models['success'], code=200, description='Пароль успешно изменен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Смена пароля"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            from ..auth.middleware.jwt import JWTMiddleware
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            jwt_middleware = JWTMiddleware(auth_service)
            
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_middleware.verify_token(token)
            
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            user_id = payload.get('user_id')
            success, message = auth_service.change_password(
                user_id,
                data['current_password'],
                data['new_password']
            )
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                return {
                    "error": "Change Password Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/sessions')
class AuthSessions(Resource):
    @auth_ns.doc('get_user_sessions', description='Получить активные сессии пользователя')
    @auth_ns.marshal_with(session_model, code=200, description='Список активных сессий')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить активные сессии пользователя"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            from ..auth.middleware.jwt import JWTMiddleware
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            jwt_middleware = JWTMiddleware(auth_service)
            
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_middleware.verify_token(token)
            
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            user_id = payload.get('user_id')
            user = auth_service.get_user_by_id(user_id)
            
            if not user:
                return {
                    "error": "User Not Found",
                    "message": "Пользователь не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            sessions = [
                session.to_dict() for session in user.sessions 
                if session.is_active and not session.is_expired()
            ]
            
            return {"sessions": sessions}, 200
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/sessions/<int:session_id>')
class AuthSession(Resource):
    @auth_ns.doc('revoke_session', description='Отозвать конкретную сессию')
    @auth_ns.marshal_with(common_models['success'], code=200, description='Сессия успешно отозвана')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=404, description='Сессия не найдена')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def delete(self, session_id):
        """Отозвать конкретную сессию"""
        try:
            from ..auth.services.auth_service import AuthService
            from ..auth.utils.email import EmailService
            from ..database.connection import get_db_session
            from ..auth.middleware.jwt import JWTMiddleware
            
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            jwt_middleware = JWTMiddleware(auth_service)
            
            # Проверяем токен
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    "error": "Unauthorized",
                    "message": "Токен не предоставлен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_middleware.verify_token(token)
            
            if not payload:
                return {
                    "error": "Unauthorized",
                    "message": "Неверный токен",
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
            user_id = payload.get('user_id')
            user = auth_service.get_user_by_id(user_id)
            
            if not user:
                return {
                    "error": "User Not Found",
                    "message": "Пользователь не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            session = next(
                (s for s in user.sessions if s.id == session_id), 
                None
            )
            
            if not session:
                return {
                    "error": "Session Not Found",
                    "message": "Сессия не найдена",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            session.is_active = False
            db_session.commit()
            
            return {
                "success": True,
                "message": "Сессия отозвана",
                "timestamp": datetime.now().isoformat()
            }, 200
                
        except Exception as e:
            return handle_exception(e)


# ==================== BILLING ENDPOINTS ====================

@billing_ns.route('/plans')
class BillingPlans(Resource):
    @billing_ns.doc('get_plans', description='Получить все доступные тарифные планы')
    @billing_ns.marshal_with(plan_model, code=200, description='Список тарифных планов')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить все доступные тарифные планы"""
        try:
            from ..billing.models.subscription import get_all_plans
            
            plans = get_all_plans()
            
            # Форматируем планы для API
            formatted_plans = []
            for plan_id, plan in plans.items():
                formatted_plans.append({
                    "id": plan.id,
                    "name": plan.name,
                    "description": plan.description,
                    "price_monthly": plan.price_monthly,
                    "price_yearly": plan.price_yearly,
                    "plan_type": plan.plan_type.value,
                    "limits": {
                        "posts_per_month": plan.limits.posts_per_month,
                        "max_agents": plan.limits.max_agents,
                        "platforms": plan.limits.platforms,
                        "api_calls_per_day": plan.limits.api_calls_per_day,
                        "storage_gb": plan.limits.storage_gb,
                        "support_level": plan.limits.support_level
                    },
                    "features": plan.features,
                    "is_popular": plan.is_popular,
                    "trial_days": plan.trial_days
                })
            
            return {
                "success": True,
                "plans": formatted_plans
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/plans/<string:plan_id>')
class BillingPlan(Resource):
    @billing_ns.doc('get_plan', description='Получить конкретный тарифный план')
    @billing_ns.marshal_with(plan_model, code=200, description='Тарифный план')
    @billing_ns.marshal_with(common_models['error'], code=404, description='План не найден')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, plan_id):
        """Получить конкретный тарифный план"""
        try:
            from ..billing.models.subscription import get_plan_by_id
            
            plan = get_plan_by_id(plan_id)
            if not plan:
                return {
                    "error": "Plan Not Found",
                    "message": "План не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            return {
                "success": True,
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "description": plan.description,
                    "price_monthly": plan.price_monthly,
                    "price_yearly": plan.price_yearly,
                    "plan_type": plan.plan_type.value,
                    "limits": {
                        "posts_per_month": plan.limits.posts_per_month,
                        "max_agents": plan.limits.max_agents,
                        "platforms": plan.limits.platforms,
                        "api_calls_per_day": plan.limits.api_calls_per_day,
                        "storage_gb": plan.limits.storage_gb,
                        "support_level": plan.limits.support_level
                    },
                    "features": plan.features,
                    "is_popular": plan.is_popular,
                    "trial_days": plan.trial_days
                }
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/subscription')
class BillingSubscription(Resource):
    @billing_ns.doc('get_subscription', description='Получить подписку пользователя')
    @billing_ns.marshal_with(subscription_model, code=200, description='Подписка пользователя')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Не указан ID пользователя')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить подписку пользователя"""
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID пользователя",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # TODO: Получить сессию БД из контекста приложения
            # subscription_service = SubscriptionService(db_session)
            # subscription = subscription_service.get_user_subscription(user_id)
            
            # Временная заглушка
            subscription = None
            
            if not subscription:
                return {
                    "success": True,
                    "subscription": None,
                    "message": "У пользователя нет активной подписки"
                }, 200
            
            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "plan_id": subscription.plan_id,
                    "status": subscription.status,
                    "starts_at": subscription.starts_at.isoformat(),
                    "expires_at": subscription.expires_at.isoformat(),
                    "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                    "auto_renew": subscription.auto_renew,
                    "last_payment_at": subscription.last_payment_at.isoformat() if subscription.last_payment_at else None,
                    "next_payment_at": subscription.next_payment_at.isoformat() if subscription.next_payment_at else None
                }
            }, 200
            
        except Exception as e:
            return handle_exception(e)

    @billing_ns.doc('create_subscription', description='Создать подписку')
    @billing_ns.expect(create_subscription_model, validate=True)
    @billing_ns.marshal_with(subscription_model, code=201, description='Подписка создана')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @billing_ns.marshal_with(common_models['error'], code=404, description='План не найден')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Создать подписку"""
        try:
            from ..billing.models.subscription import get_plan_by_id
            from ..billing.services.yookassa_service import YooKassaService, PaymentRequest
            
            data = request.get_json()
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID пользователя",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            plan_id = data.get('plan_id')
            if not plan_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID плана",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            plan = get_plan_by_id(plan_id)
            if not plan:
                return {
                    "error": "Plan Not Found",
                    "message": "План не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            # Если план бесплатный, создаем подписку сразу
            if plan.price_monthly == 0:
                # TODO: Создать бесплатную подписку
                return {
                    "success": True,
                    "subscription": {
                        "id": "temp_free_subscription",
                        "plan_id": plan_id,
                        "status": "active",
                        "message": "Бесплатная подписка активирована"
                    }
                }, 201
            
            # Для платных планов создаем платеж
            yookassa_service = YooKassaService()
            
            # Определяем сумму и период
            billing_period = data.get('billing_period', 'monthly')
            if billing_period == 'yearly':
                amount = plan.price_yearly
                description = f"Подписка {plan.name} на год"
            else:
                amount = plan.price_monthly
                description = f"Подписка {plan.name} на месяц"
            
            # Создаем запрос на платеж
            payment_request = PaymentRequest(
                amount=amount,
                currency="RUB",
                description=description,
                metadata={
                    "plan_id": plan_id,
                    "billing_period": billing_period,
                    "user_id": user_id
                }
            )
            
            # Создаем платеж
            payment_response = yookassa_service.create_payment(
                payment_request=payment_request,
                user_id=user_id
            )
            
            return {
                "success": True,
                "payment": {
                    "id": payment_response.payment_id,
                    "url": payment_response.payment_url,
                    "amount": payment_response.amount,
                    "currency": payment_response.currency,
                    "expires_at": payment_response.expires_at.isoformat()
                },
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "billing_period": billing_period
                }
            }, 201
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/subscription/<int:subscription_id>/cancel')
class BillingCancelSubscription(Resource):
    @billing_ns.doc('cancel_subscription', description='Отменить подписку')
    @billing_ns.expect(cancel_subscription_model, validate=True)
    @billing_ns.marshal_with(common_models['success'], code=200, description='Подписка отменена')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self, subscription_id):
        """Отменить подписку"""
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID пользователя",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            data = request.get_json() or {}
            reason = data.get('reason', 'user_request')
            
            # TODO: Отменить подписку через SubscriptionService
            # subscription_service = SubscriptionService(db_session)
            # success = subscription_service.cancel_subscription(subscription_id, reason)
            
            # Временная заглушка
            success = True
            
            if not success:
                return {
                    "error": "Cancel Failed",
                    "message": "Ошибка отмены подписки",
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
            
            return {
                "success": True,
                "message": "Подписка успешно отменена",
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/usage')
class BillingUsage(Resource):
    @billing_ns.doc('get_usage', description='Получить статистику использования')
    @billing_ns.marshal_with(usage_stats_model, code=200, description='Статистика использования')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Не указан ID пользователя')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить статистику использования"""
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID пользователя",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # TODO: Получить статистику через SubscriptionService
            # subscription_service = SubscriptionService(db_session)
            # usage_stats = subscription_service.get_usage_stats(user_id)
            
            # Временная заглушка
            usage_stats = {
                "posts_used": 15,
                "posts_limit": 50,
                "api_calls_used": 250,
                "api_calls_limit": 100,
                "storage_used_gb": 0.5,
                "storage_limit_gb": 1,
                "agents_used": 2,
                "agents_limit": 3,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
            
            return {
                "success": True,
                "usage": usage_stats
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/payment-methods')
class BillingPaymentMethods(Resource):
    @billing_ns.doc('get_payment_methods', description='Получить доступные способы оплаты')
    @billing_ns.marshal_with(common_models['success'], code=200, description='Способы оплаты')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить доступные способы оплаты"""
        try:
            from ..billing.services.yookassa_service import YooKassaService
            
            yookassa_service = YooKassaService()
            payment_methods = yookassa_service.get_payment_methods()
            
            return {
                "success": True,
                "payment_methods": payment_methods
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/payment/<string:payment_id>')
class BillingPayment(Resource):
    @billing_ns.doc('get_payment_status', description='Получить статус платежа')
    @billing_ns.marshal_with(payment_model, code=200, description='Статус платежа')
    @billing_ns.marshal_with(common_models['error'], code=404, description='Платеж не найден')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, payment_id):
        """Получить статус платежа"""
        try:
            from ..billing.services.yookassa_service import YooKassaService
            
            yookassa_service = YooKassaService()
            payment_info = yookassa_service.get_payment(payment_id)
            
            if not payment_info:
                return {
                    "error": "Payment Not Found",
                    "message": "Платеж не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            return {
                "success": True,
                "payment": payment_info
            }, 200
            
        except Exception as e:
            return handle_exception(e)


@billing_ns.route('/events')
class BillingEvents(Resource):
    @billing_ns.doc('get_billing_events', description='Получить события billing системы')
    @billing_ns.marshal_with(billing_event_model, code=200, description='События billing')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Не указан ID пользователя')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить события billing системы"""
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return {
                    "error": "Validation Error",
                    "message": "Не указан ID пользователя",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # TODO: Получить события через SubscriptionService
            # subscription_service = SubscriptionService(db_session)
            # events = subscription_service.get_billing_events(user_id, limit, offset)
            
            # Временная заглушка
            events = [
                {
                    "id": 1,
                    "event_type": "subscription_created",
                    "event_data": {
                        "plan_id": "free",
                        "trial_days": 7
                    },
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ]
            
            return {
                "success": True,
                "events": events
            }, 200
            
        except Exception as e:
            return handle_exception(e)


# ==================== WEBHOOK ENDPOINTS ====================

@webhook_ns.route('/yookassa')
class WebhookYooKassa(Resource):
    @webhook_ns.doc('yookassa_webhook', description='Обработчик webhook от ЮКассы')
    @webhook_ns.expect(webhook_model, validate=False)
    @webhook_ns.marshal_with(webhook_response_model, code=200, description='Webhook обработан')
    @webhook_ns.marshal_with(common_models['error'], code=400, description='Неверная подпись')
    @webhook_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Обработчик webhook от ЮКассы"""
        try:
            from ..billing.services.yookassa_service import YooKassaService
            
            # Получаем данные запроса
            request_body = request.get_data(as_text=True)
            signature = request.headers.get('X-YooMoney-Signature', '')
            
            logger.info(f"Получен webhook от ЮКассы: {request_body[:200]}...")
            
            # Инициализируем сервисы
            yookassa_service = YooKassaService()
            
            # Проверяем подпись
            if not yookassa_service.verify_webhook(request_body, signature):
                logger.warning("Неверная подпись webhook от ЮКассы")
                return {
                    "error": "Invalid signature",
                    "message": "Неверная подпись webhook",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Парсим webhook
            webhook_data = yookassa_service.parse_webhook(request_body)
            if not webhook_data:
                logger.warning("Не удалось распарсить webhook от ЮКассы")
                return {
                    "error": "Invalid webhook data",
                    "message": "Неверные данные webhook",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Обрабатываем событие
            success = _process_webhook_event(webhook_data)
            
            if success:
                logger.info(f"Webhook успешно обработан: {webhook_data['event_type']}")
                return {
                    "status": "ok",
                    "message": "Webhook обработан успешно"
                }, 200
            else:
                logger.error(f"Ошибка обработки webhook: {webhook_data['event_type']}")
                return {
                    "error": "Processing failed",
                    "message": "Ошибка обработки webhook",
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
                
        except Exception as e:
            logger.error(f"Ошибка обработки webhook от ЮКассы: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@webhook_ns.route('/yookassa/test')
class WebhookYooKassaTest(Resource):
    @webhook_ns.doc('yookassa_test_webhook', description='Тестовый webhook для отладки')
    @webhook_ns.marshal_with(webhook_response_model, code=200, description='Тестовый webhook получен')
    @webhook_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Тестовый webhook для отладки"""
        try:
            request_body = request.get_data(as_text=True)
            headers = dict(request.headers)
            
            logger.info("Получен тестовый webhook от ЮКассы:")
            logger.info(f"Headers: {headers}")
            logger.info(f"Body: {request_body}")
            
            return {
                "status": "ok",
                "message": "Test webhook received",
                "headers": headers,
                "body_length": len(request_body)
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка обработки тестового webhook: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


def _process_webhook_event(webhook_data):
    """Обработать событие webhook"""
    try:
        event_type = webhook_data.get('event_type')
        payment_id = webhook_data.get('payment_id')
        
        logger.info(f"Обработка события {event_type} для платежа {payment_id}")
        
        if event_type == 'payment.succeeded':
            return _handle_payment_succeeded(webhook_data)
        elif event_type == 'payment.canceled':
            return _handle_payment_canceled(webhook_data)
        elif event_type == 'refund.succeeded':
            return _handle_refund_succeeded(webhook_data)
        else:
            logger.warning(f"Неизвестный тип события: {event_type}")
            return True  # Не критичная ошибка
            
    except Exception as e:
        logger.error(f"Ошибка обработки события webhook: {e}")
        return False


def _handle_payment_succeeded(webhook_data):
    """Обработать успешный платеж"""
    try:
        payment_id = webhook_data.get('payment_id')
        metadata = webhook_data.get('metadata', {})
        user_id = metadata.get('user_id')
        subscription_id = metadata.get('subscription_id')
        
        if not user_id:
            logger.error(f"Не указан user_id в метаданных платежа {payment_id}")
            return False
        
        logger.info(f"Обработка успешного платежа {payment_id} для пользователя {user_id}")
        
        # TODO: Получить сессию БД из контекста приложения
        # db_session = current_app.db_session
        # subscription_service = SubscriptionService(db_session)
        # yookassa_service = YooKassaService()
        
        # Получаем информацию о платеже
        # payment_info = yookassa_service.get_payment(payment_id)
        # if not payment_info:
        #     logger.error(f"Не удалось получить информацию о платеже {payment_id}")
        #     return False
        
        # Создаем или обновляем запись платежа
        # payment = Payment(
        #     yookassa_payment_id=payment_id,
        #     user_id=user_id,
        #     subscription_id=int(subscription_id) if subscription_id else None,
        #     amount=payment_info['amount'],
        #     currency=payment_info['currency'],
        #     status=PaymentStatus.SUCCEEDED.value,
        #     description=payment_info.get('description', ''),
        #     paid_at=webhook_data.get('paid_at'),
        #     metadata=metadata
        # )
        # 
        # db_session.add(payment)
        # db_session.commit()
        
        # Если это платеж за подписку, создаем или продлеваем подписку
        if subscription_id:
            # subscription = subscription_service.get_user_subscription(user_id)
            # if subscription:
            #     # Продлеваем существующую подписку
            #     success = subscription_service.renew_subscription(
            #         subscription_id=int(subscription_id),
            #         payment_id=payment_id
            #     )
            # else:
            #     # Создаем новую подписку
            #     plan_id = metadata.get('plan_id', 'free')
            #     success = subscription_service.create_subscription(
            #         user_id=user_id,
            #         plan_id=plan_id,
            #         payment_method='yookassa'
            #     )
            pass
        
        # TODO: Отправить уведомление пользователю
        # _send_payment_notification(user_id, payment_id, 'success')
        
        logger.info(f"Платеж {payment_id} успешно обработан")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка обработки успешного платежа: {e}")
        return False


def _handle_payment_canceled(webhook_data):
    """Обработать отмененный платеж"""
    try:
        payment_id = webhook_data.get('payment_id')
        metadata = webhook_data.get('metadata', {})
        user_id = metadata.get('user_id')
        
        if not user_id:
            logger.error(f"Не указан user_id в метаданных отмененного платежа {payment_id}")
            return False
        
        logger.info(f"Обработка отмененного платежа {payment_id} для пользователя {user_id}")
        
        # TODO: Обновить статус платежа в БД
        # db_session = current_app.db_session
        # payment = db_session.query(Payment).filter(
        #     Payment.yookassa_payment_id == payment_id
        # ).first()
        # 
        # if payment:
        #     payment.status = PaymentStatus.CANCELLED.value
        #     payment.updated_at = datetime.utcnow()
        #     db_session.commit()
        
        # TODO: Отправить уведомление пользователю
        # _send_payment_notification(user_id, payment_id, 'canceled')
        
        logger.info(f"Отмененный платеж {payment_id} успешно обработан")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка обработки отмененного платежа: {e}")
        return False


def _handle_refund_succeeded(webhook_data):
    """Обработать успешный возврат"""
    try:
        refund_id = webhook_data.get('refund_id')
        payment_id = webhook_data.get('payment_id')
        amount = webhook_data.get('amount')
        
        logger.info(f"Обработка возврата {refund_id} для платежа {payment_id}")
        
        # TODO: Обновить информацию о возврате в БД
        # db_session = current_app.db_session
        # payment = db_session.query(Payment).filter(
        #     Payment.yookassa_payment_id == payment_id
        # ).first()
        # 
        # if payment:
        #     # Обновляем статус платежа
        #     payment.status = PaymentStatus.REFUNDED.value
        #     payment.updated_at = datetime.utcnow()
        #     
        #     # Создаем запись о возврате
        #     refund = Refund(
        #         payment_id=payment.id,
        #         yookassa_refund_id=refund_id,
        #         amount=amount,
        #         status=RefundStatus.SUCCEEDED.value,
        #         created_at=webhook_data.get('created_at')
        #     )
        #     
        #     db_session.add(refund)
        #     db_session.commit()
        
        # TODO: Отправить уведомление пользователю
        # _send_payment_notification(payment.user_id, payment_id, 'refunded')
        
        logger.info(f"Возврат {refund_id} успешно обработан")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка обработки возврата: {e}")
        return False


# ==================== HEALTH ENDPOINTS ====================

@health_ns.route('/')
class HealthCheck(Resource):
    @health_ns.doc('health_check', description='Проверка состояния приложения')
    @health_ns.marshal_with(health_model, code=200, description='Система здорова')
    @health_ns.marshal_with(health_model, code=503, description='Система нездорова')
    def get(self):
        """Проверка состояния приложения"""
        try:
            # Получаем базовый статус системы
            system_status = orchestrator.get_system_status()
            
            # Определяем общее состояние
            total_agents = system_status["agents"]["total_agents"]
            error_agents = system_status["agents"]["error_agents"]
            
            if error_agents == 0 and total_agents > 0:
                health_status = "healthy"
                status_code = 200
            elif error_agents < total_agents:
                health_status = "degraded"
                status_code = 503
            else:
                health_status = "unhealthy"
                status_code = 503
            
            response = {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "AI Content Orchestrator",
                "details": {
                    "total_agents": total_agents,
                    "error_agents": error_agents,
                    "active_tasks": system_status["agents"]["active_tasks"],
                    "completed_tasks": system_status["agents"]["completed_tasks"]
                }
            }
            
            return response, status_code
            
        except Exception as e:
            logger.error(f"Ошибка health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "AI Content Orchestrator",
                "details": {
                    "error": str(e)
                }
            }, 503