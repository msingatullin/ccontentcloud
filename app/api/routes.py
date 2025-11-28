"""
API Routes для AI Content Orchestrator
RESTful endpoints для работы с контентом и агентами
Интегрировано с Flask-RESTX для Swagger UI
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
import jwt
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from app.auth.services.auth_service import AuthService
from app.auth.utils.email import EmailService
from app.database.connection import get_db_session
from app.orchestrator.main_orchestrator import orchestrator
from app.services.content_source_service import ContentSourceService
from app.models.content_sources import ContentSource
from app.services.production_calendar_service import ProductionCalendarService
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

# ==================== AUTH SERVICE INTEGRATION ====================

# Инициализация AuthService
def get_auth_service():
    """Получить экземпляр AuthService"""
    print("DEBUG: Starting get_auth_service()")
    try:
        print("DEBUG: Calling get_db_session()")
        db_session = get_db_session()
        print(f"DEBUG: DB session created: {type(db_session)}")
        
        print("DEBUG: Getting SECRET_KEY")
        secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
        print(f"DEBUG: SECRET_KEY obtained: {secret_key[:10] if secret_key else 'None'}")
        
        print("DEBUG: Creating EmailService")
        email_service = EmailService()
        print(f"DEBUG: EmailService created: {type(email_service)}")
        
        print("DEBUG: Creating AuthService")
        auth_service = AuthService(db_session, secret_key, email_service)
        print(f"DEBUG: AuthService created: {type(auth_service)}")
        
        return auth_service
    except Exception as e:
        print(f"ERROR in get_auth_service: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

# Создаем namespaces для API
api = Namespace('', description='AI Content Orchestrator API')  # Пустое имя для корневого namespace
auth_ns = Namespace('auth', description='Authentication API')
billing_ns = Namespace('billing', description='Billing API')
webhook_ns = Namespace('webhook', description='Webhook API')
health_ns = Namespace('health', description='Health Check API')
content_sources_ns = Namespace('content-sources', description='Content Sources API')
ai_ns = Namespace('ai', description='AI-powered onboarding and content generation')

# ==================== JWT MIDDLEWARE ====================

from functools import wraps

def jwt_required(f):
    """Декоратор для проверки JWT токена"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: JWT middleware called for endpoint: {request.endpoint}")
        print(f"DEBUG: Request path: {request.path}")
        print(f"DEBUG: Request method: {request.method}")
        logger.error(f"JWT middleware called for endpoint: {request.endpoint}")
        logger.error(f"Request path: {request.path}")
        logger.error(f"Request method: {request.method}")
        
        token = None
        
        # Извлечь токен из Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print(f"DEBUG: Authorization header: {auth_header[:20] if auth_header else 'None'}...")
            logger.info(f"Authorization header: {auth_header[:20] if auth_header else 'None'}...")
            try:
                # Поддерживаем оба формата: "Bearer <token>" и просто "<token>" (для Swagger UI)
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(" ")[1]
                else:
                    # Swagger UI может передавать токен без "Bearer "
                    token = auth_header
                print(f"DEBUG: Extracted token: {token[:20]}...")
                logger.info(f"Extracted token: {token[:20]}...")
            except Exception as e:
                print(f"DEBUG: Invalid token format: {e}")
                logger.warning(f"Invalid token format: {e}")
                return {"error": "Invalid token format. Use: Bearer <token>"}, 401
        
        if not token:
            print(f"DEBUG: Authorization token is missing")
            logger.warning("Authorization token is missing")
            return {"error": "Authorization token is missing"}, 401
        
        # Проверить токен через AuthService
        try:
            print(f"DEBUG: About to call get_auth_service()...")
            auth_service = get_auth_service()
            print(f"DEBUG: get_auth_service() success: {type(auth_service)}")
            print(f"DEBUG: AuthService obtained, calling verify_token...")
            logger.info(f"Verifying token: {token[:20]}...")
            success, payload = auth_service.verify_token(token)  # Распаковываем Tuple
            print(f"DEBUG: Token verification result: success={success}, payload={payload}")
            logger.info(f"Token verification result: success={success}, payload={payload}")
            if not success or not payload:
                print(f"DEBUG: Token verification failed: success={success}, payload={payload}")
                logger.warning(f"Token verification failed: success={success}, payload={payload}")
                return {"error": "Invalid or expired token"}, 401
        except Exception as e:
            print(f"ERROR: get_auth_service() failed: {e}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return jsonify({'error': 'Service initialization failed'}), 500
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            import traceback
            logger.error(f"JWT verification traceback: {traceback.format_exc()}")
            return {"error": "Token verification failed"}, 401
        
        # Установить user_id в request для удобства доступа
        request.user_id = payload.get('user_id') or payload.get('id')
        request.current_user = payload
        
        # Передать user info в функцию
        return f(*args, current_user=payload, **kwargs)
    
    return decorated_function

# Создаем общие модели
common_models = create_common_models(api)

# ==================== CONTENT MODELS ====================

content_request_model = api.model('ContentRequest', {
    'title': fields.String(required=True, min_length=1, max_length=200, description='Заголовок контента'),
    'description': fields.String(required=True, min_length=10, max_length=1000, description='Описание контента'),
    'target_audience': fields.String(required=True, min_length=1, max_length=200, description='Целевая аудитория'),
    'business_goals': fields.List(fields.String, required=True, min_items=1, max_items=10, description='Бизнес-цели'),
    'call_to_action': fields.List(fields.String, description='Призывы к действию (текст, ссылки, действия)', max_items=10),
    'tone': fields.String(description='Тон контента', enum=['professional', 'casual', 'friendly', 'authoritative'], default='professional'),
    'keywords': fields.List(fields.String, description='Ключевые слова', max_items=20),
    'platforms': fields.List(fields.String, max_items=5, description='Платформы для публикации (опционально)', default=[]),
    'content_types': fields.List(fields.String, description='Типы контента', default=['post']),
    'constraints': fields.Raw(description='Дополнительные ограничения'),
    'test_mode': fields.Boolean(description='Тестовый режим (по умолчанию False - реальная публикация)', default=False),
    'uploaded_files': fields.List(fields.String, description='IDs загруженных файлов', max_items=10),
    'reference_urls': fields.List(fields.String, description='URLs референсных материалов', max_items=5)
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

# Модель для ответа со всеми агентами
all_agents_status_model = api.model('AllAgentsStatus', {
    'agents': fields.Raw(description='Словарь всех агентов с их статусами')
})

# Универсальная модель для агентов (может быть один агент или все агенты)
agents_response_model = api.model('AgentsResponse', {
    'data': fields.Raw(description='Данные агентов (один агент или словарь всех агентов)')
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

# ==================== UPLOAD MODELS ====================

uploaded_file_model = api.model('UploadedFile', {
    'file_id': fields.String(required=True, description='ID загруженного файла'),
    'filename': fields.String(required=True, description='Имя файла'),
    'file_type': fields.String(required=True, description='Тип файла (image, video, document)'),
    'file_size': fields.Integer(required=True, description='Размер файла в байтах'),
    'storage_url': fields.String(required=True, description='URL файла в хранилище')
})

upload_error_model = api.model('UploadError', {
    'filename': fields.String(required=True, description='Имя файла'),
    'error': fields.String(required=True, description='Описание ошибки')
})

batch_upload_response_model = api.model('BatchUploadResponse', {
    'success': fields.Boolean(required=True, description='Успешность операции'),
    'message': fields.String(required=True, description='Сообщение о результате'),
    'uploaded_files': fields.List(fields.Nested(uploaded_file_model), description='Успешно загруженные файлы'),
    'errors': fields.List(fields.Nested(upload_error_model), description='Ошибки загрузки')
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
        logger.info("run_async: Getting event loop")
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        logger.info(f"run_async: Creating new event loop (RuntimeError: {e})")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    logger.info("run_async: Running coroutine")
    result = loop.run_until_complete(coro)
    logger.info(f"run_async: Completed with result type: {type(result)}")
    return result


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
    @jwt_required
    @api.doc('create_content', description='Создает контент через AI агентов')
    @api.expect(content_request_model, validate=True)
    @api.response(201, 'Контент успешно создан')
    @api.response(400, 'Ошибка валидации')
    @api.response(500, 'Внутренняя ошибка сервера')
    def post(self, current_user):
        """
        Создает контент через AI агентов
        
        Принимает запрос на создание контента и запускает workflow
        с участием всех необходимых агентов.
        """
        logger.error("=== POST METHOD CALLED IN ContentCreate ===")
        print("DEBUG: POST METHOD CALLED IN ContentCreate")
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            logger.error(f"User info: ID={user_id}, email={email}")
            
            # Валидируем входные данные
            try:
                logger.error(f"Request JSON: {request.json}")
                request_json = request.json or {}
                logger.info(f"📥 Получен запрос: title={request_json.get('title')}, generate_image={request_json.get('generate_image')}, image_source={request_json.get('image_source')}")
                content_request = ContentRequestSchema(**request_json)
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return handle_validation_error(e)
            
            logger.info(f"User {email} (ID: {user_id}) создает контент: {content_request.title}")
            
            # Преобразуем Pydantic модель в словарь
            logger.info("Преобразуем Pydantic модель в словарь")
            request_data = content_request.dict()
            # Добавляем user_id в данные запроса
            request_data['user_id'] = user_id
            logger.info(f"Request data prepared: {request_data}")
            
            # Логируем параметры изображения для отладки
            generate_image_val = request_data.get('generate_image')
            image_source_val = request_data.get('image_source')
            logger.info(f"🖼️ Параметры изображения: generate_image={generate_image_val} (type: {type(generate_image_val)}), image_source={image_source_val} (type: {type(image_source_val)})")
            
            # Получаем персональный оркестратор пользователя
            from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory
            db_session = get_db_session()
            
            logger.info(f"Получаем оркестратор для пользователя {user_id}")
            user_orchestrator = UserOrchestratorFactory.get_orchestrator(user_id, db_session)
            
            # Запускаем обработку через персональный оркестратор
            logger.info(f"Запускаем user_orchestrator.process_content_request для пользователя {user_id}")
            result = run_async(user_orchestrator.process_content_request(request_data))
            logger.info(f"Результат от orchestrator: {result}")
            
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
                
                logger.info(f"Возвращаем ответ: {response_data}")
                return response_data, 201
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


@api.route('/content/history')
class ContentHistory(Resource):
    @jwt_required
    @api.doc('get_content_history', description='Получает историю созданного контента', security='BearerAuth')
    @api.param('page', 'Номер страницы', type='int', default=1)
    @api.param('per_page', 'Элементов на странице', type='int', default=10)
    @api.param('platform', 'Фильтр по платформе', type='string')
    @api.param('date_from', 'Дата начала (ISO format)', type='string')
    @api.param('date_to', 'Дата окончания (ISO format)', type='string')
    def get(self, current_user):
        """
        Получает историю созданного контента пользователя
        """
        try:
            from app.models.content import ContentPieceDB
            from sqlalchemy import desc
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Параметры пагинации
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 100)  # максимум 100
            
            # Фильтры
            platform = request.args.get('platform')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            
            # Базовый запрос
            query = db_session.query(ContentPieceDB).filter(ContentPieceDB.user_id == user_id)
            
            # Применяем фильтры
            if platform:
                query = query.filter(ContentPieceDB.platform == platform)
            if date_from:
                query = query.filter(ContentPieceDB.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.filter(ContentPieceDB.created_at <= datetime.fromisoformat(date_to))
            
            # Сортировка и пагинация
            total = query.count()
            items = query.order_by(desc(ContentPieceDB.created_at)).offset((page - 1) * per_page).limit(per_page).all()
            
            # Форматируем результаты
            formatted_items = []
            for item in items:
                formatted_items.append({
                    "id": item.id,
                    "title": item.title,
                    "platform": item.platform,
                    "content_type": item.content_type,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "created_by_agent": item.created_by_agent,
                    "views": item.views,
                    "likes": item.likes,
                    "engagement_rate": round((item.likes / max(item.views, 1)) * 100, 2) if item.views > 0 else 0
                })
            
            return {
                "success": True,
                "items": formatted_items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                },
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения истории контента: {e}")
            return handle_exception(e)


@api.route('/content/by-brief/<string:brief_id>')
class ContentByBrief(Resource):
    @jwt_required
    @api.doc('get_content_by_brief', description='Получает контент по brief_id', security='BearerAuth')
    def get(self, current_user, brief_id):
        """
        Получает контент по brief_id (для отложенного постинга)
        """
        try:
            from app.models.content import ContentPieceDB
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Находим контент по brief_id
            content = db_session.query(ContentPieceDB).filter(
                ContentPieceDB.brief_id == brief_id,
                ContentPieceDB.user_id == user_id
            ).first()
            
            db_session.close()
            
            if not content:
                return {
                    "success": False,
                    "error": "Content Not Found",
                    "message": f"Контент для brief_id {brief_id} еще не создан или не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            return {
                "success": True,
                "data": {
                    "id": content.id,
                    "brief_id": content.brief_id,
                    "title": content.title,
                    "platform": content.platform,
                    "content_type": content.content_type,
                    "status": content.status,
                    "created_at": content.created_at.isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения контента по brief_id: {e}")
            return handle_exception(e)


@api.route('/content/<string:content_id>')
class ContentDetail(Resource):
    @jwt_required
    @api.doc('get_content_detail', description='Получает детальную информацию о контенте', security='BearerAuth')
    def get(self, current_user, content_id):
        """
        Получает конкретный контент со всеми деталями
        """
        try:
            from app.models.content import ContentPieceDB, TokenUsageDB
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Находим контент
            content = db_session.query(ContentPieceDB).filter(
                ContentPieceDB.id == content_id,
                ContentPieceDB.user_id == user_id
            ).first()
            
            if not content:
                return {
                    "error": "Content Not Found",
                    "message": f"Контент с ID {content_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            # Получаем использование токенов для этого контента
            token_usage = db_session.query(TokenUsageDB).filter(
                TokenUsageDB.content_id == content_id
            ).all()
            
            total_tokens = sum(t.total_tokens for t in token_usage)
            total_cost_rub = sum(t.cost_rub for t in token_usage)
            
            return {
                "success": True,
                "content": {
                    "id": content.id,
                    "title": content.title,
                    "text": content.text,
                    "platform": content.platform,
                    "content_type": content.content_type,
                    "hashtags": content.hashtags,
                    "call_to_action": content.call_to_action,
                    "status": content.status,
                    "created_by_agent": content.created_by_agent,
                    "metadata": content.meta_data,
                    "quality_metrics": {
                        "seo_score": content.seo_score,
                        "engagement_potential": content.engagement_potential,
                        "readability_score": content.readability_score
                    },
                    "performance_metrics": {
                        "views": content.views,
                        "likes": content.likes,
                        "shares": content.shares,
                        "comments": content.comments
                    },
                    "token_usage": {
                        "total_tokens": total_tokens,
                        "total_cost_rub": round(total_cost_rub, 2),
                        "agents_used": [t.agent_id for t in token_usage]
                    },
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка получения контента: {e}")
            return handle_exception(e)
    
    @jwt_required
    @api.doc('delete_content', description='Удаляет контент из истории', security='BearerAuth')
    def delete(self, current_user, content_id):
        """
        Удаляет контент из истории
        """
        try:
            from app.models.content import ContentPieceDB
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Находим контент
            content = db_session.query(ContentPieceDB).filter(
                ContentPieceDB.id == content_id,
                ContentPieceDB.user_id == user_id
            ).first()
            
            if not content:
                return {
                    "error": "Content Not Found",
                    "message": f"Контент с ID {content_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
            
            # Удаляем контент (cascade удалит связанные записи)
            db_session.delete(content)
            db_session.commit()
            
            logger.info(f"Контент {content_id} удален пользователем {user_id}")
            
            return {
                "success": True,
                "message": "Контент успешно удален",
                "timestamp": datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка удаления контента: {e}")
            db_session.rollback()
            return handle_exception(e)


# ==================== FILE UPLOADS ====================

@api.route('/uploads/batch')
class FileUploadBatch(Resource):
    @jwt_required
    @api.doc('upload_files_batch', description='Загрузить несколько файлов за один запрос (до 20 файлов)', security='BearerAuth')
    @api.param('files', 'Файлы для загрузки (multiple)', type='file', required=True, _in='formData')
    @api.param('folder', 'Папка (images/documents/videos)', type='string', _in='formData')
    @api.param('analyze', 'Анализировать через AI', type='boolean', _in='formData')
    @api.response(201, 'Файлы успешно загружены', batch_upload_response_model)
    @api.response(400, 'Ошибка валидации')
    @api.response(500, 'Внутренняя ошибка сервера')
    def post(self, current_user):
        """
        Загружает несколько файлов за один запрос
        
        Возвращает массив file_id для использования в /content/create
        
        Пример ответа:
        {
          "success": true,
          "uploaded_files": [
            {"file_id": "uuid1", "filename": "photo1.jpg"},
            {"file_id": "uuid2", "filename": "doc.pdf"}
          ]
        }
        """
        try:
            from werkzeug.datastructures import FileStorage
            from app.services.storage_service import get_storage_service
            from app.services.vision_service import get_vision_service
            from app.services.document_parser import get_document_parser
            from app.models.uploads import FileUploadDB
            import uuid
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Получаем все файлы из запроса
            files = request.files.getlist('files')
            
            if not files or len(files) == 0:
                return {
                    "error": "No files provided",
                    "message": "Файлы не предоставлены",
                    "status_code": 400
                }, 400
            
            # Лимит на количество файлов
            if len(files) > 20:
                return {
                    "error": "Too many files",
                    "message": "Максимум 20 файлов за раз",
                    "status_code": 400
                }, 400
            
            folder = request.form.get('folder', 'uploads')
            analyze = request.form.get('analyze', 'false').lower() == 'true'
            
            storage_service = get_storage_service()
            vision_service = get_vision_service() if analyze else None
            document_parser = get_document_parser() if analyze else None
            
            uploaded_files = []
            errors = []
            
            # Обрабатываем каждый файл
            for file in files:
                try:
                    if not file.filename:
                        errors.append({"filename": "unknown", "error": "Empty filename"})
                        continue
                    
                    file_id = str(uuid.uuid4())
                    
                    # Читаем содержимое файла
                    file_content = file.read()
                    file.seek(0)  # Возвращаем указатель
                    
                    # Загружаем в облако через async метод
                    upload_result = run_async(storage_service.upload_file(
                        file_content=file_content,
                        filename=file.filename,
                        user_id=str(user_id),
                        folder=folder
                    ))
                    
                    if not upload_result.get('success'):
                        errors.append({
                            "filename": file.filename,
                            "error": upload_result.get('error', 'Upload failed')
                        })
                        continue
                    
                    storage_url = upload_result['url']
                    file_size = upload_result['size_bytes']
                    mime_type = upload_result['content_type']
                    
                    # Определяем тип файла
                    if mime_type.startswith('image/'):
                        file_type = 'image'
                    elif mime_type.startswith('video/'):
                        file_type = 'video'
                    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                        file_type = 'document'
                    else:
                        file_type = 'other'
                    
                    # AI анализ если нужен
                    ai_analysis = None
                    extracted_text = None
                    
                    if analyze:
                        if file_type == 'image' and vision_service:
                            ai_analysis = vision_service.analyze_image(storage_url)
                        elif file_type == 'document' and document_parser:
                            file.seek(0)  # Возвращаем указатель в начало
                            extracted_text = document_parser.parse_file(file, mime_type)
                    
                    # Сохраняем в БД
                    file_upload = FileUploadDB(
                        id=file_id,
                        user_id=user_id,
                        filename=upload_result['filename'],
                        original_filename=upload_result['original_filename'],
                        file_type=file_type,
                        mime_type=mime_type,
                        size_bytes=upload_result['size_bytes'],
                        storage_url=upload_result['url'],
                        storage_bucket=upload_result['bucket'],
                        storage_path=upload_result['path'],
                        ai_description=ai_analysis if isinstance(ai_analysis, str) else None,
                        extracted_text=extracted_text
                    )
                    
                    db_session.add(file_upload)
                    
                    uploaded_files.append({
                        "file_id": file_id,
                        "filename": file.filename,
                        "file_type": file_type,
                        "file_size": file_size,
                        "storage_url": storage_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error uploading file {file.filename}: {e}")
                    errors.append({
                        "filename": file.filename,
                        "error": str(e)
                    })
            
            # Коммитим все успешные загрузки
            db_session.commit()
            
            return {
                "success": True,
                "message": f"Загружено {len(uploaded_files)} из {len(files)} файлов",
                "uploaded_files": uploaded_files,
                "errors": errors if errors else None
            }, 201
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Batch upload error: {e}")
            return handle_exception(e)


@api.route('/uploads/upload')
class FileUpload(Resource):
    @jwt_required
    @api.doc('upload_file', description='Загрузить один файл (для простых случаев)', security='BearerAuth')
    @api.param('file', 'Файл для загрузки', type='file', required=True, _in='formData')
    @api.param('folder', 'Папка (images/documents/videos)', type='string', _in='formData')
    @api.param('analyze', 'Анализировать через AI', type='boolean', _in='formData')
    def post(self, current_user):
        """
        Загружает файл в облако и опционально анализирует через AI
        
        Поддерживаемые типы:
        - Изображения: jpg, jpeg, png, gif, webp
        - Видео: mp4, mov, avi
        - Документы: pdf, docx, xlsx, md, txt
        """
        try:
            from werkzeug.datastructures import FileStorage
            from app.services.storage_service import get_storage_service
            from app.services.vision_service import get_vision_service
            from app.services.document_parser import get_document_parser
            from app.models.uploads import FileUploadDB
            import uuid
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Проверяем наличие файла
            if 'file' not in request.files:
                return {
                    "error": "No file provided",
                    "message": "Файл не предоставлен",
                    "status_code": 400
                }, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {
                    "error": "Empty filename",
                    "message": "Имя файла пустое",
                    "status_code": 400
                }, 400
            
            # Параметры
            folder = request.form.get('folder', 'uploads')
            analyze = request.form.get('analyze', 'true').lower() == 'true'
            
            # Читаем содержимое файла
            file_content = file.read()
            file.seek(0)  # Возвращаем указатель в начало
            
            # Валидация размера (макс 100MB)
            max_size = 100 * 1024 * 1024  # 100 MB
            if len(file_content) > max_size:
                return {
                    "error": "File too large",
                    "message": f"Файл слишком большой. Максимум: {max_size / (1024*1024):.0f}MB",
                    "status_code": 400
                }, 400
            
            # Загружаем в GCS
            storage_service = get_storage_service()
            upload_result = run_async(storage_service.upload_file(
                file_content=file_content,
                filename=file.filename,
                user_id=str(user_id),
                folder=folder
            ))
            
            if not upload_result.get('success'):
                return {
                    "error": "Upload failed",
                    "message": upload_result.get('error', 'Ошибка загрузки'),
                    "status_code": 500
                }, 500
            
            # Определяем тип файла
            mime_type = upload_result['content_type']
            if mime_type.startswith('image/'):
                file_type = 'image'
            elif mime_type.startswith('video/'):
                file_type = 'video'
            elif mime_type in ['application/pdf', 'application/msword', 
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/vnd.ms-excel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                              'text/plain', 'text/markdown']:
                file_type = 'document'
            else:
                file_type = 'other'
            
            # Создаем запись в БД
            file_id = str(uuid.uuid4())
            file_upload = FileUploadDB(
                id=file_id,
                user_id=user_id,
                filename=upload_result['filename'],
                original_filename=upload_result['original_filename'],
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=upload_result['size_bytes'],
                storage_url=upload_result['url'],
                storage_bucket=upload_result['bucket'],
                storage_path=upload_result['path']
            )
            
            db_session.add(file_upload)
            db_session.commit()
            
            # AI анализ если запрошен
            ai_result = None
            if analyze:
                if file_type == 'image':
                    # Анализ изображения
                    vision_service = get_vision_service()
                    ai_result = run_async(vision_service.analyze_image(
                        upload_result['url'],
                        analysis_type='full'
                    ))
                    
                    if ai_result.get('success'):
                        analysis = ai_result.get('analysis', {})
                        file_upload.ai_description = analysis.get('description', '')
                        file_upload.ai_metadata = analysis
                        file_upload.is_processed = True
                        file_upload.processed_at = datetime.utcnow()
                        db_session.commit()
                
                elif file_type == 'document':
                    # Парсинг документа
                    # Сначала скачиваем временно (можно оптимизировать)
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                        tmp_file.write(file_content)
                        tmp_path = tmp_file.name
                    
                    try:
                        doc_parser = get_document_parser()
                        parse_result = run_async(doc_parser.parse_file(tmp_path))
                        
                        if parse_result.get('success'):
                            file_upload.extracted_text = parse_result.get('text', '')
                            file_upload.document_metadata = parse_result
                            file_upload.is_processed = True
                            file_upload.processed_at = datetime.utcnow()
                            db_session.commit()
                            
                            ai_result = parse_result
                    finally:
                        os.unlink(tmp_path)
            
            logger.info(f"File uploaded: {file_id} by user {user_id}")
            
            return {
                "success": True,
                "file": file_upload.to_dict(),
                "ai_analysis": ai_result,
                "timestamp": datetime.now().isoformat()
            }, 201
            
        except Exception as e:
            return handle_exception(e)


@api.route('/uploads/list')
class FileUploadList(Resource):
    @jwt_required
    @api.doc('list_uploads', description='Список загруженных файлов', security='BearerAuth')
    @api.param('page', 'Номер страницы', type='int', default=1)
    @api.param('per_page', 'Файлов на странице', type='int', default=20)
    @api.param('file_type', 'Фильтр по типу (image/document/video)', type='string')
    def get(self, current_user):
        """
        Получает список загруженных файлов пользователя
        """
        try:
            from app.models.uploads import FileUploadDB
            from sqlalchemy import desc, func
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            # Параметры пагинации
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            file_type = request.args.get('file_type')
            
            # Базовый запрос
            query = db_session.query(FileUploadDB).filter(
                FileUploadDB.user_id == user_id,
                FileUploadDB.is_deleted == False
            )
            
            # Фильтр по типу
            if file_type:
                query = query.filter(FileUploadDB.file_type == file_type)
            
            # Сортировка
            query = query.order_by(desc(FileUploadDB.uploaded_at))
            
            # Пагинация
            total = query.count()
            files = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Считаем общий размер
            total_size_bytes = db_session.query(func.sum(FileUploadDB.size_bytes)).filter(
                FileUploadDB.user_id == user_id,
                FileUploadDB.is_deleted == False
            ).scalar() or 0
            
            return {
                "files": [f.to_dict() for f in files],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                },
                "storage": {
                    "total_files": total,
                    "total_size_bytes": total_size_bytes,
                    "total_size_mb": round(total_size_bytes / (1024 * 1024), 2)
                }
            }
            
        except Exception as e:
            return handle_exception(e)


@api.route('/uploads/<string:file_id>')
class FileUploadDetail(Resource):
    @jwt_required
    @api.doc('get_upload_detail', description='Детальная информация о файле', security='BearerAuth')
    def get(self, current_user, file_id):
        """
        Получает полную информацию о загруженном файле
        """
        try:
            from app.models.uploads import FileUploadDB
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            file_upload = db_session.query(FileUploadDB).filter(
                FileUploadDB.id == file_id,
                FileUploadDB.user_id == user_id
            ).first()
            
            if not file_upload:
                return {
                    "error": "File Not Found",
                    "message": f"Файл с ID {file_id} не найден",
                    "status_code": 404
                }, 404
            
            # Обновляем last_accessed_at
            file_upload.last_accessed_at = datetime.utcnow()
            db_session.commit()
            
            return {
                "file": file_upload.to_dict_full()
            }
            
        except Exception as e:
            return handle_exception(e)
    
    @jwt_required
    @api.doc('delete_upload', description='Удалить файл', security='BearerAuth')
    def delete(self, current_user, file_id):
        """
        Удаляет загруженный файл
        """
        try:
            from app.models.uploads import FileUploadDB
            from app.services.storage_service import get_storage_service
            
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            file_upload = db_session.query(FileUploadDB).filter(
                FileUploadDB.id == file_id,
                FileUploadDB.user_id == user_id
            ).first()
            
            if not file_upload:
                return {
                    "error": "File Not Found",
                    "message": f"Файл с ID {file_id} не найден",
                    "status_code": 404
                }, 404
            
            # Мягкое удаление
            file_upload.is_deleted = True
            file_upload.deleted_at = datetime.utcnow()
            db_session.commit()
            
            # Опционально: удалить из GCS (раскомментировать если нужно)
            # storage_service = get_storage_service()
            # run_async(storage_service.delete_file(file_upload.storage_path))
            
            logger.info(f"File {file_id} deleted by user {user_id}")
            
            return {
                "success": True,
                "message": "Файл успешно удален"
            }
            
        except Exception as e:
            return handle_exception(e)


# ==================== WORKFLOW ENDPOINTS ====================

@api.route('/workflow/<string:workflow_id>/status')
class WorkflowStatus(Resource):
    @jwt_required
    @api.doc('get_workflow_status', description='Получает статус workflow по ID')
    @api.marshal_with(workflow_status_model, code=200, description='Статус workflow')
    @api.marshal_with(common_models['error'], code=404, description='Workflow не найден')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, workflow_id, current_user):
        """
        Получает статус workflow по ID
        """
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            logger.info(f"User {email} (ID: {user_id}) запрашивает статус workflow: {workflow_id}")
            
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
    @jwt_required
    @api.doc('get_agents_status', description='Получает статус всех агентов или конкретного агента', security='BearerAuth')
    @api.param('agent_id', 'ID конкретного агента (опционально)', type='string')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ ВСЕ marshal_with для корректного отображения данных
    # @api.marshal_with(agents_response_model, code=200, description='Статус агентов')
    # @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """
        Получает статус всех агентов или конкретного агента
        """
        try:
            # Проверка feature flag DISABLE_AGENTS
            if os.getenv('DISABLE_AGENTS', 'false').lower() == 'true':
                logger.warning("⚠️ Агенты отключены (DISABLE_AGENTS=true)")
                agent_id = request.args.get('agent_id')
                if agent_id:
                    return {
                        "agent_id": agent_id,
                        "status": "disabled",
                        "message": "Система агентов отключена для debugging"
                    }, 200
                else:
                    return {
                        "message": "Система агентов отключена для debugging",
                        "agents": {}
                    }, 200
            
            # Получаем данные пользователя из JWT
            user_id = current_user.get('user_id')
            logger.info(f"Запрос статуса агентов от пользователя: {user_id}")
            
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
                # Статус всех агентов - возвращаем простой JSON без обертки
                logger.info("Запрос статуса всех агентов")
                agents_status = orchestrator.get_all_agents_status()
                logger.info(f"Получен статус агентов: {agents_status}")
                
                # Возвращаем данные напрямую без обертки
                return agents_status, 200
                
        except Exception as e:
            logger.error(f"Ошибка получения статуса агентов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return handle_exception(e)


@api.route('/agents/<string:agent_id>/tasks')
class AgentTasks(Resource):
    @jwt_required
    @api.doc('get_agent_tasks', description='Получает список задач конкретного агента', security='BearerAuth')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user, agent_id):
        """
        Получает список задач конкретного агента
        """
        try:
            user_id = current_user.get('user_id')
            logger.info(f"Запрос задач агента {agent_id} от пользователя: {user_id}")
            # Проверка feature flag DISABLE_AGENTS
            if os.getenv('DISABLE_AGENTS', 'false').lower() == 'true':
                logger.warning("⚠️ Агенты отключены (DISABLE_AGENTS=true)")
                return {
                    "agent_id": agent_id,
                    "message": "Система агентов отключена для debugging",
                    "current_tasks": [],
                    "completed_tasks": 0,
                    "status": "disabled"
                }, 200
            
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


@api.route('/agents/restart-all')
class AgentsRestartAll(Resource):
    @jwt_required
    @api.doc('restart_all_agents', description='Перезапускает все агенты (сбрасывает ошибки)', security='BearerAuth')
    def post(self, current_user):
        """
        Перезапускает все агенты в системе
        
        Сбрасывает статус ERROR у всех агентов и возвращает их в рабочее состояние.
        Полезно при возникновении массовых ошибок или для технического обслуживания.
        """
        try:
            user_id = current_user.get('user_id')
            logger.info(f"🔄 Запрос на перезапуск всех агентов от пользователя: {user_id}")
            # Проверка feature flag DISABLE_AGENTS
            if os.getenv('DISABLE_AGENTS', 'false').lower() == 'true':
                logger.warning("⚠️ Агенты отключены (DISABLE_AGENTS=true)")
                return {
                    "success": False,
                    "message": "Система агентов отключена для debugging",
                    "timestamp": datetime.now().isoformat()
                }, 200
            
            # Вызываем метод перезапуска
            result = orchestrator.restart_all_agents()
            
            return result, 200
            
        except Exception as e:
            logger.error(f"Ошибка при перезапуске агентов: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return handle_exception(e)


# ==================== SYSTEM ENDPOINTS ====================

@api.route('/system/status')
class SystemStatus(Resource):
    @api.doc('get_system_status', description='Получает общий статус системы')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(system_status_model, code=200, description='Статус системы')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Получает общий статус системы
        """
        try:
            # Проверка feature flag DISABLE_AGENTS
            if os.getenv('DISABLE_AGENTS', 'false').lower() == 'true':
                logger.warning("⚠️ Агенты отключены (DISABLE_AGENTS=true)")
                return {
                    "status": "agents_disabled",
                    "message": "Система агентов отключена для debugging",
                    "agents": {
                        "total_agents": 0,
                        "active_agents": 0,
                        "idle_agents": 0,
                        "error_agents": 0
                    },
                    "timestamp": datetime.now().isoformat()
                }, 200
            
            logger.info("Запрос статуса системы")
            
            status = orchestrator.get_system_status()
            return status, 200
            
        except Exception as e:
            return handle_exception(e)


@api.route('/system/health')
class SystemHealth(Resource):
    @api.doc('get_system_health', description='Проверка здоровья системы')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(common_models['health'], code=200, description='Система здорова')
    # @api.marshal_with(common_models['health'], code=503, description='Система нездорова')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """
        Проверка здоровья системы
        """
        try:
            # Проверка feature flag DISABLE_AGENTS
            if os.getenv('DISABLE_AGENTS', 'false').lower() == 'true':
                logger.warning("⚠️ Агенты отключены (DISABLE_AGENTS=true)")
                return {
                    "status": "healthy",
                    "message": "API работает (агенты отключены для debugging)",
                    "timestamp": datetime.now().isoformat(),
                    "checks": {
                        "agents": "disabled"
                    }
                }, 200
            
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
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
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
# Удалены неиспользуемые эндпоинты /platforms и /platforms/<platform>/config
# Информация о платформах доступна через агентов

# ==================== TRENDS ANALYSIS ENDPOINTS ====================
# Удалены дублирующие эндпоинты /trends/analyze и /trends/viral
# Анализ трендов выполняется автоматически через TrendsScoutAgent при создании контента

# ==================== DOCUMENTATION ENDPOINTS ====================
# Удалены эндпоинты /docs и /docs/schemas
# Документация доступна через Swagger UI по адресу /api/docs/

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
    # УБИРАЕМ marshal_with - он вызывает null значения в Swagger UI
    # @auth_ns.marshal_with(auth_response_model, code=201, description='Пользователь успешно зарегистрирован')
    # @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    # @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Регистрация нового пользователя"""
        try:
            logger.info("=== REGISTER ENDPOINT CALLED ===")
            
            data = request.get_json()
            logger.info(f"=== REGISTER DATA: {data} ===")
            
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
            
            # Используем AuthService для регистрации
            auth_service = get_auth_service()
            success, message, user = auth_service.register_user(
                email=data['email'],
                password=data['password'],
                username=data['username'],
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                company=data.get('company'),
                phone=data.get('phone')
            )
            
            if success and user:
                # Генерируем токены через AuthService
                tokens = auth_service._create_tokens(user, None, None, None)
                
                return {
                    "message": "Registration successful",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "company": user.company or "",
                        "phone": user.phone or "",
                        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                        "is_verified": user.is_verified,
                        "created_at": user.created_at.isoformat() if user.created_at else "",
                        "updated_at": user.updated_at.isoformat() if user.updated_at else ""
                    },
                    "access_token": tokens.get('access_token'),
                    "refresh_token": tokens.get('refresh_token', ""),
                    "expires_in": tokens.get('expires_in', 86400)
                }, 201
            else:
                return {
                    "error": "Registration Failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": "Internal server error",
                "message": f"Внутренняя ошибка сервера: {str(e)}",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/login')
class AuthLogin(Resource):
    @auth_ns.doc('login_user', description='Авторизация пользователя')
    @auth_ns.expect(login_model, validate=True)
    # УБИРАЕМ marshal_with - он вызывает null значения в Swagger UI
    # @auth_ns.marshal_with(auth_response_model, code=200, description='Успешная авторизация')
    # @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    # @auth_ns.marshal_with(common_models['error'], code=401, description='Неверные учетные данные')
    # @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Авторизация пользователя"""
        try:
            logger.info("=== LOGIN ENDPOINT CALLED ===")
            
            data = request.get_json()
            logger.info(f"=== LOGIN DATA: {data} ===")
            
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
            
            # Используем AuthService для авторизации
            auth_service = get_auth_service()
            
            # Информация об устройстве для сессии
            device_info = {
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
            
            success, message, tokens = auth_service.login_user(
                email=email,
                password=password,
                device_info=device_info,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            logger.info(f"=== AUTH RESULT: success={success}, message='{message}', tokens={tokens is not None} ===")
            
            if success and tokens:
                # Получаем информацию о пользователе
                user = auth_service.get_user_by_email(email)
                if user:
                    return {
                        "message": "Login successful",
                        "access_token": tokens.get('access_token'),
                        "refresh_token": tokens.get('refresh_token', ""),
                        "expires_in": tokens.get('expires_in', 86400),
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "username": user.username,
                            "first_name": user.first_name or "",
                            "last_name": user.last_name or "",
                            "company": user.company or "",
                            "phone": user.phone or "",
                            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                            "is_verified": user.is_verified,
                            "created_at": user.created_at.isoformat() if user.created_at else "",
                            "updated_at": user.updated_at.isoformat() if user.updated_at else ""
                        }
                    }, 200
            
            return {
                "error": "Authentication Failed",
                "message": message,
                "status_code": 401,
                "timestamp": datetime.now().isoformat()
            }, 401
                
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": "Internal server error",
                "message": f"Внутренняя ошибка сервера: {str(e)}",
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
            auth_service = get_auth_service()
            
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
            auth_service = get_auth_service()
            
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
            auth_service = get_auth_service()
            
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
            auth_service = get_auth_service()
            
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
    # @auth_ns.marshal_with снят для корректного отображения токенов
    def post(self):
        """Обновление токена"""
        try:
            auth_service = get_auth_service()
            
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
                # Возвращаем полную структуру с токенами
                user_data = tokens.get('user', {})
                return {
                    "message": message,
                    "access_token": tokens.get('access_token', ""),
                    "refresh_token": tokens.get('refresh_token', ""),
                    "token_type": tokens.get('token_type', 'bearer'),
                    "expires_in": tokens.get('expires_in', 86400),
                    "user": {
                        "id": user_data.get('id'),
                        "email": user_data.get('email', ""),
                        "username": user_data.get('username', ""),
                        "full_name": user_data.get('full_name', ""),
                        "role": user_data.get('role', "user"),
                        "status": user_data.get('status', "active")
                    }
                }, 200
            else:
                return {
                    "error": "Refresh Failed",
                    "message": message,
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
                
        except Exception as e:
            logger.error(f"Error in refresh endpoint: {e}")
            return {
                "error": "Internal Server Error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/logout')
class AuthLogout(Resource):
    @jwt_required
    @auth_ns.doc('logout_user', description='Выход пользователя (деактивация текущей сессии)')
    # @auth_ns.marshal_with убран для корректного отображения
    def post(self, current_user):
        """Выход пользователя - деактивирует текущую сессию в БД"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            token_jti = current_user.get('jti')  # Получаем JTI из токена
            
            logger.info(f"Logout request from user {email} (ID: {user_id})")
            logger.info(f"Current user data: {current_user}")
            logger.info(f"Token JTI: {token_jti}")
            
            # Используем уже инициализированный AuthService
            auth_service = get_auth_service()
            
            # Деактивируем сессию в БД
            logger.info(f"Calling logout_user with JTI: {token_jti}")
            success, message = auth_service.logout_user(token_jti)
            logger.info(f"Logout result: success={success}, message={message}")
            
            if success:
                logger.info(f"User {email} (ID: {user_id}) logged out successfully")
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                logger.error(f"Logout failed for user {email}: {message}")
                return {
                    "error": "Logout Failed",
                    "message": message,
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
                
        except Exception as e:
            logger.error(f"Ошибка выхода: {e}")
            return {
                "error": "Internal Server Error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/logout-all')
class AuthLogoutAll(Resource):
    @jwt_required
    @auth_ns.doc('logout_all_sessions', description='Выход из всех сессий (деактивация всех сессий пользователя)')
    # @auth_ns.marshal_with убран для корректного отображения
    def post(self, current_user):
        """Выход из всех сессий - деактивирует все активные сессии пользователя в БД"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            logger.info(f"Logout-all request from user {email} (ID: {user_id})")
            
            # Используем уже инициализированный AuthService
            auth_service = get_auth_service()
            
            # Деактивируем ВСЕ сессии пользователя в БД
            success, message = auth_service.logout_all_sessions(user_id)
            
            if success:
                logger.info(f"User {email} (ID: {user_id}) logged out from all sessions")
                return {
                    "success": True,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, 200
            else:
                logger.error(f"Logout-all failed for user {email}: {message}")
                return {
                    "error": "Logout All Failed",
                    "message": message,
                    "status_code": 500,
                    "timestamp": datetime.now().isoformat()
                }, 500
                
        except Exception as e:
            logger.error(f"Error in logout-all: {e}")
            return {
                "error": "Internal Server Error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/me')
class AuthMe(Resource):
    @jwt_required
    @auth_ns.doc('get_current_user', description='Получить информацию о текущем пользователе')
    # @auth_ns.marshal_with убран для корректного отображения
    def get(self, current_user):
        """Получить информацию о текущем пользователе"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            logger.info(f"Profile request from user {email} (ID: {user_id})")
            logger.info(f"Current user data: {current_user}")
            
            # Получить данные пользователя через AuthService
            auth_service = get_auth_service()
            user = auth_service.get_user_by_email(email)
            
            logger.info(f"User found: {user is not None}")
            if user:
                logger.info(f"User data: id={user.id}, email={user.email}, username={user.username}")
            
            # Возвращаем информацию о пользователе
            if user:
                return user.to_dict(), 200
            else:
                logger.error(f"User not found for email: {email}")
                return {
                    "error": "User not found",
                    "message": "Пользователь не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
                
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": "Internal Server Error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/profile')
class AuthProfile(Resource):
    @jwt_required
    @auth_ns.doc('update_profile', description='Обновление профиля пользователя')
    @auth_ns.expect(update_profile_model, validate=True)
    @auth_ns.marshal_with(user_model, code=200, description='Профиль успешно обновлен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def put(self, current_user):
        """Обновление профиля пользователя"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Обновить данные пользователя через AuthService
            auth_service = get_auth_service()
            success, message, updated_user = auth_service.update_user_profile(
                user_id=user_id,
                **data
            )
            
            if success:
                # Используем обновленного пользователя из результата
                user = updated_user
                
                return {
                    "message": "Profile updated successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "company": user.company or "",
                        "phone": user.phone or "",
                        "is_verified": user.is_verified,
                        "created_at": user.created_at.isoformat() if user.created_at else "",
                        "updated_at": user.updated_at.isoformat() if user.updated_at else ""
                    }
                }, 200
            else:
                return {
                    "error": "Profile update failed",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
                
        except Exception as e:
            return handle_exception(e)


@auth_ns.route('/change-password')
class AuthChangePassword(Resource):
    @jwt_required
    @auth_ns.doc('change_password', description='Смена пароля')
    @auth_ns.expect(change_password_model, validate=True)
    @auth_ns.marshal_with(common_models['success'], code=200, description='Пароль успешно изменен')
    @auth_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self, current_user):
        """Смена пароля"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Validation Error",
                    "message": "Данные не предоставлены",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Проверяем обязательные поля
            if 'current_password' not in data or 'new_password' not in data:
                return {
                    "error": "Validation Error",
                    "message": "Требуются current_password и new_password",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Проверяем новый пароль
            if len(data['new_password']) < 8:
                return {
                    "error": "Validation Error",
                    "message": "Новый пароль должен содержать минимум 8 символов",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # Изменяем пароль через AuthService
            auth_service = get_auth_service()
            success, message = auth_service.change_password(
                user_id=user_id,
                current_password=data['current_password'],
                new_password=data['new_password']
            )
            
            if success:
                logger.info(f"User {email} (ID: {user_id}) changed password successfully")
            else:
                return {
                    "error": "Password change failed",
                    "message": message,
                    "status_code": 401,
                    "timestamp": datetime.now().isoformat()
                }, 401
            
                return {
                "success": True,
                "message": "Password changed successfully",
                    "timestamp": datetime.now().isoformat()
            }, 200
                
        except Exception as e:
            logger.error(f"Error in change-password: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/sessions')
class AuthSessions(Resource):
    @jwt_required
    @auth_ns.doc('get_user_sessions', description='Получить активные сессии пользователя')
    @auth_ns.marshal_with(session_model, code=200, description='Список активных сессий')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """Получить активные сессии пользователя"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе возвращаем текущую сессию
            sessions = [
                {
                    "id": 1,
                    "device_info": "Current Session",
                    "ip_address": request.remote_addr,
                    "user_agent": request.headers.get('User-Agent', 'Unknown'),
                    "is_active": True,
                    "created_at": datetime.now().isoformat(),
                    "last_activity": datetime.now().isoformat()
                }
            ]
            
            return {"sessions": sessions}, 200
                
        except Exception as e:
            logger.error(f"Error in sessions: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@auth_ns.route('/sessions/<int:session_id>')
class AuthSession(Resource):
    @jwt_required
    @auth_ns.doc('revoke_session', description='Отозвать конкретную сессию')
    @auth_ns.marshal_with(common_models['success'], code=200, description='Сессия успешно отозвана')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=404, description='Сессия не найдена')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def delete(self, session_id, current_user):
        """Отозвать конкретную сессию"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе просто логируем отзыв сессии
            logger.info(f"User {email} (ID: {user_id}) revoked session {session_id}")
            
            return {
                "success": True,
                "message": "Session revoked successfully",
                "timestamp": datetime.now().isoformat()
            }, 200
                
        except Exception as e:
            logger.error(f"Error in revoke session: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


# ==================== BILLING ENDPOINTS ====================

@billing_ns.route('/plans')
class BillingPlans(Resource):
    @billing_ns.doc('get_plans', description='Получить все доступные тарифные планы')
    @billing_ns.marshal_with(plan_model, code=200, description='Список тарифных планов')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
        """Получить все доступные тарифные планы"""
        try:
            from app.billing.models.subscription import get_all_plans
            
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
            from app.billing.models.subscription import get_plan_by_id
            
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
    @jwt_required
    @billing_ns.doc('get_subscription', description='Получить подписку пользователя')
    @billing_ns.marshal_with(subscription_model, code=200, description='Подписка пользователя')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Не указан ID пользователя')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """Получить подписку пользователя"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе возвращаем базовую подписку
            subscription = {
                "id": 1,
                "user_id": user_id,
                "plan_id": 1,
                "status": "active",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "auto_renew": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "subscription": subscription
            }, 200
            
        except Exception as e:
            logger.error(f"Error in get subscription: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500

    @billing_ns.doc('create_subscription', description='Создать подписку')
    @billing_ns.expect(create_subscription_model, validate=True)
    @billing_ns.marshal_with(subscription_model, code=201, description='Подписка создана')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @billing_ns.marshal_with(common_models['error'], code=404, description='План не найден')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """Создать подписку"""
        try:
            from app.billing.models.subscription import get_plan_by_id
            from app.billing.services.yookassa_service import YooKassaService, PaymentRequest
            
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
    @jwt_required
    @billing_ns.doc('get_usage', description='Получить статистику использования')
    @billing_ns.marshal_with(usage_stats_model, code=200, description='Статистика использования')
    @billing_ns.marshal_with(common_models['error'], code=400, description='Не указан ID пользователя')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """Получить статистику использования"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе возвращаем базовую статистику
            usage_stats = {
                "posts_used": 0,
                "posts_limit": 50,
                "api_calls_used": 0,
                "api_calls_limit": 1000,
                "storage_used_gb": 0,
                "storage_limit_gb": 1,
                "agents_used": 0,
                "agents_limit": 3,
                "period_start": datetime.now().replace(day=1).isoformat() + "Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
            
            return {
                "success": True,
                "usage": usage_stats
            }, 200
            
        except Exception as e:
            logger.error(f"Error in get usage: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@billing_ns.route('/payment-methods')
class BillingPaymentMethods(Resource):
    @jwt_required
    @billing_ns.doc('get_payment_methods', description='Получить доступные способы оплаты')
    @billing_ns.marshal_with(common_models['success'], code=200, description='Способы оплаты')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """Получить доступные способы оплаты"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе возвращаем базовые способы оплаты
            payment_methods = [
                {
                    "id": "card",
                    "name": "Банковская карта",
                    "description": "Visa, MasterCard, МИР",
                    "enabled": True
                },
                {
                    "id": "yoomoney",
                    "name": "ЮMoney",
                    "description": "ЮMoney кошелек",
                    "enabled": True
                },
                {
                    "id": "qiwi",
                    "name": "QIWI",
                    "description": "QIWI кошелек",
                    "enabled": True
                }
            ]
            
            return {
                "success": True,
                "payment_methods": payment_methods
            }, 200
            
        except Exception as e:
            logger.error(f"Error in get payment methods: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


@billing_ns.route('/payment/<string:payment_id>')
class BillingPayment(Resource):
    @jwt_required
    @billing_ns.doc('get_payment_status', description='Получить статус платежа')
    @billing_ns.marshal_with(payment_model, code=200, description='Статус платежа')
    @billing_ns.marshal_with(common_models['error'], code=404, description='Платеж не найден')
    @billing_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, payment_id, current_user):
        """Получить статус платежа"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # В in-memory системе возвращаем базовую информацию о платеже
            payment_info = {
                "id": payment_id,
                "user_id": user_id,
                "amount": 999.00,
                "currency": "RUB",
                "status": "succeeded",
                "description": "Подписка на месяц",
                "created_at": datetime.now().isoformat(),
                "paid_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "payment": payment_info
            }, 200
            
        except Exception as e:
            logger.error(f"Error in get payment: {e}")
            return {
                "error": "Internal server error",
                "message": "Внутренняя ошибка сервера",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }, 500


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


# ==================== AGENT SUBSCRIPTIONS ENDPOINTS ====================

# Модели для agent subscriptions
agent_info_model = billing_ns.model('AgentInfo', {
    'id': fields.String(description='ID агента'),
    'name': fields.String(description='Название агента'),
    'description': fields.String(description='Описание'),
    'price_monthly': fields.Float(description='Цена в рублях'),
    'category': fields.String(description='Категория'),
    'icon': fields.String(description='Иконка'),
    'features': fields.List(fields.String, description='Функции'),
    'popular': fields.Boolean(description='Популярный агент'),
    'recommended_for': fields.List(fields.String, description='Рекомендуется для')
})

bundle_info_model = billing_ns.model('BundleInfo', {
    'id': fields.String(description='ID bundle'),
    'name': fields.String(description='Название'),
    'description': fields.String(description='Описание'),
    'agents': fields.List(fields.String, description='Список agent_id в bundle'),
    'price_monthly': fields.Float(description='Цена bundle в рублях'),
    'regular_price': fields.Float(description='Обычная цена в рублях'),
    'discount_percent': fields.Integer(description='Процент скидки'),
    'discount_amount': fields.Float(description='Сумма скидки в рублях'),
    'popular': fields.Boolean(description='Популярный bundle'),
    'recommended': fields.Boolean(description='Рекомендованный bundle'),
    'icon': fields.String(description='Иконка')
})

agent_subscription_model = billing_ns.model('AgentSubscription', {
    'id': fields.Integer(description='ID подписки'),
    'agent_id': fields.String(description='ID агента'),
    'agent_name': fields.String(description='Название агента'),
    'status': fields.String(description='Статус подписки'),
    'price_monthly_rub': fields.Float(description='Цена в рублях'),
    'starts_at': fields.String(description='Начало подписки'),
    'expires_at': fields.String(description='Окончание подписки'),
    'auto_renew': fields.Boolean(description='Автопродление'),
    'usage': fields.Nested(billing_ns.model('SubscriptionUsage', {
        'requests_this_month': fields.Integer(description='Запросов в этом месяце'),
        'tokens_this_month': fields.Integer(description='Токенов в этом месяце'),
        'cost_this_month_rub': fields.Float(description='Стоимость в рублях')
    })),
    'limits': fields.Nested(billing_ns.model('SubscriptionLimits', {
        'max_requests': fields.Integer(description='Максимум запросов'),
        'max_tokens': fields.Integer(description='Максимум токенов')
    })),
    'is_active': fields.Boolean(description='Активна ли подписка'),
    'can_use': fields.Boolean(description='Можно ли использовать'),
    'last_used_at': fields.String(description='Последнее использование')
})

subscribe_request_model = billing_ns.model('SubscribeRequest', {
    'agent_id': fields.String(required=True, description='ID агента для подписки'),
    'bundle_id': fields.String(description='ID bundle (если подписка через bundle)')
})

@billing_ns.route('/agents/available')
class AvailableAgents(Resource):
    @billing_ns.doc('get_available_agents', description='Получить список всех доступных AI агентов и bundles')
    @billing_ns.marshal_with(billing_ns.model('AvailableAgentsResponse', {
        'agents': fields.List(fields.Nested(agent_info_model)),
        'bundles': fields.List(fields.Nested(bundle_info_model)),
        'categories': fields.Raw(description='Категории агентов')
    }), code=200, description='Список агентов и bundles')
    def get(self):
        """Получить все доступные агенты с ценами"""
        try:
            from app.billing.models.agent_pricing import AGENT_PRICING, AGENT_BUNDLES, AGENT_CATEGORIES
            
            # Формируем список агентов
            agents = []
            for agent_id, agent_data in AGENT_PRICING.items():
                agents.append({
                    'id': agent_id,
                    'name': agent_data.get('name'),
                    'description': agent_data.get('description'),
                    'price_monthly': agent_data.get('price_monthly', 0) / 100,  # В рублях
                    'category': agent_data.get('category'),
                    'icon': agent_data.get('icon'),
                    'features': agent_data.get('features', []),
                    'popular': agent_data.get('popular', False),
                    'recommended_for': agent_data.get('recommended_for', [])
                })
            
            # Формируем список bundles
            bundles = []
            for bundle_id, bundle_data in AGENT_BUNDLES.items():
                from app.billing.models.agent_pricing import get_bundle_agents
                
                bundles.append({
                    'id': bundle_id,
                    'name': bundle_data.get('name'),
                    'description': bundle_data.get('description'),
                    'agents': get_bundle_agents(bundle_id),
                    'price_monthly': bundle_data.get('price_monthly', 0) / 100,
                    'regular_price': bundle_data.get('regular_price', 0) / 100,
                    'discount_percent': bundle_data.get('discount_percent', 0),
                    'discount_amount': bundle_data.get('discount_amount', 0) / 100,
                    'popular': bundle_data.get('popular', False),
                    'recommended': bundle_data.get('recommended', False),
                    'icon': bundle_data.get('icon'),
                    'features': bundle_data.get('features', [])
                })
            
            return {
                'agents': agents,
                'bundles': bundles,
                'categories': AGENT_CATEGORIES
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting available agents: {e}")
            return handle_exception(e)


@billing_ns.route('/agents/my-subscriptions')
class MyAgentSubscriptions(Resource):
    @jwt_required
    @billing_ns.doc('get_my_subscriptions', description='Получить мои подписки на агентов', security='BearerAuth')
    @billing_ns.marshal_with(billing_ns.model('MySubscriptionsResponse', {
        'subscriptions': fields.List(fields.Nested(agent_subscription_model)),
        'total_monthly_cost_rub': fields.Float(description='Общая стоимость в месяц'),
        'active_agents_count': fields.Integer(description='Количество активных агентов')
    }), code=200, description='Мои подписки')
    def get(self, current_user):
        """Получить мои активные подписки на агентов"""
        try:
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            from app.billing.middleware.agent_access_middleware import AgentAccessMiddleware
            
            subscriptions = AgentAccessMiddleware.get_user_subscriptions(user_id, db_session)
            
            # Подсчитываем общую стоимость
            total_cost = sum(
                sub.get('price_monthly_rub', 0) 
                for sub in subscriptions 
                if sub.get('is_active')
            )
            
            active_count = sum(1 for sub in subscriptions if sub.get('is_active'))
            
            return {
                'subscriptions': subscriptions,
                'total_monthly_cost_rub': total_cost,
                'active_agents_count': active_count
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting user subscriptions: {e}")
            return handle_exception(e)


@billing_ns.route('/agents/subscribe')
class SubscribeToAgent(Resource):
    @jwt_required
    @billing_ns.doc('subscribe_to_agent', description='Подписаться на агента', security='BearerAuth')
    @billing_ns.expect(subscribe_request_model, validate=True)
    @billing_ns.marshal_with(billing_ns.model('SubscribeResponse', {
        'success': fields.Boolean(description='Успешность операции'),
        'message': fields.String(description='Сообщение'),
        'subscription': fields.Nested(agent_subscription_model)
    }), code=201, description='Подписка создана')
    def post(self, current_user):
        """Подписаться на агента"""
        try:
            user_id = current_user.get('user_id')
            data = request.json
            agent_id = data.get('agent_id')
            bundle_id = data.get('bundle_id')
            
            db_session = get_db_session()
            from app.billing.models.agent_subscription import AgentSubscription
            from app.billing.models.agent_pricing import AGENT_PRICING, get_bundle_agents, get_bundle_price
            
            # Проверяем существует ли агент
            if agent_id not in AGENT_PRICING:
                return {'error': f'Agent {agent_id} not found'}, 404
            
            # Проверяем нет ли уже активной подписки
            existing = db_session.query(AgentSubscription).filter(
                AgentSubscription.user_id == user_id,
                AgentSubscription.agent_id == agent_id,
                AgentSubscription.status == 'active'
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'message': f'Вы уже подписаны на {agent_id}',
                    'subscription': existing.to_dict()
                }, 400
            
            # Создаем подписку
            agent_data = AGENT_PRICING[agent_id]
            
            subscription = AgentSubscription(
                user_id=user_id,
                agent_id=agent_id,
                agent_name=agent_data.get('name'),
                status='active',
                price_monthly=agent_data.get('price_monthly'),
                starts_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                source='bundle' if bundle_id else 'direct',
                bundle_id=bundle_id
            )
            
            db_session.add(subscription)
            db_session.commit()
            
            # Обновляем оркестратор пользователя
            from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory
            UserOrchestratorFactory.refresh_user_agents(user_id, db_session)
            
            logger.info(f"User {user_id} subscribed to agent {agent_id}")
            
            return {
                'success': True,
                'message': f'Вы успешно подписались на {agent_data.get("name")}',
                'subscription': subscription.to_dict()
            }, 201
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error subscribing to agent: {e}")
            return handle_exception(e)


@billing_ns.route('/agents/unsubscribe')
class UnsubscribeFromAgent(Resource):
    @jwt_required
    @billing_ns.doc('unsubscribe_from_agent', description='Отписаться от агента', security='BearerAuth')
    @billing_ns.expect(billing_ns.model('UnsubscribeRequest', {
        'agent_id': fields.String(required=True, description='ID агента')
    }), validate=True)
    def post(self, current_user):
        """Отписаться от агента"""
        try:
            user_id = current_user.get('user_id')
            data = request.json
            agent_id = data.get('agent_id')
            
            db_session = get_db_session()
            from app.billing.models.agent_subscription import AgentSubscription
            
            # Находим подписку
            subscription = db_session.query(AgentSubscription).filter(
                AgentSubscription.user_id == user_id,
                AgentSubscription.agent_id == agent_id,
                AgentSubscription.status == 'active'
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'message': f'Активная подписка на {agent_id} не найдена'
                }, 404
            
            # Отменяем подписку
            subscription.cancel()
            db_session.commit()
            
            # Обновляем оркестратор пользователя
            from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory
            UserOrchestratorFactory.refresh_user_agents(user_id, db_session)
            
            logger.info(f"User {user_id} unsubscribed from agent {agent_id}")
            
            return {
                'success': True,
                'message': f'Подписка на {subscription.agent_name} отменена'
            }, 200
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error unsubscribing from agent: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens')
class TokenUsageStats(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage', description='Получить статистику использования токенов', security='BearerAuth')
    @billing_ns.param('period', 'Период (day, week, month, year)', _in='query')
    @billing_ns.param('agent_id', 'Фильтр по агенту', _in='query')
    def get(self, current_user):
        """Получить детальную статистику по токенам (LEGACY - используйте /usage/tokens/summary)"""
        try:
            user_id = current_user.get('user_id')
            period = request.args.get('period', 'month')
            agent_id_filter = request.args.get('agent_id')
            
            db_session = get_db_session()
            from app.billing.middleware.agent_access_middleware import AgentAccessMiddleware
            
            usage_stats = AgentAccessMiddleware.get_usage_stats(user_id, db_session)
            
            # Фильтруем по агенту если указан
            if agent_id_filter:
                usage_stats['by_agent'] = [
                    agent for agent in usage_stats.get('by_agent', [])
                    if agent.get('agent_id') == agent_id_filter
                ]
            
            return usage_stats, 200
            
        except Exception as e:
            logger.error(f"Error getting token usage: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens/summary')
class TokenUsageSummary(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage_summary', 
                    description='Получить сводку по использованию токенов (сегодня, месяц, всего)', 
                    security='BearerAuth')
    def get(self, current_user):
        """
        Получить сводку расхода токенов для ЛК клиента
        
        Возвращает:
        - today: статистика за сегодня
        - this_month: статистика за текущий месяц  
        - all_time: статистика за все время
        
        Каждый блок содержит: total_tokens, cost_rub, requests_count
        """
        try:
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            from app.billing.services.token_usage_service import TokenUsageService
            
            token_service = TokenUsageService(db_session)
            summary = token_service.get_user_token_summary(user_id)
            
            return {
                "success": True,
                "data": summary
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting token usage summary: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens/history')
class TokenUsageHistory(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage_history', 
                    description='Получить историю использования токенов по дням для графиков', 
                    security='BearerAuth')
    @billing_ns.param('days', 'Количество дней для отображения (по умолчанию 30)', _in='query', type='integer')
    @billing_ns.param('agent_id', 'Фильтр по конкретному агенту', _in='query')
    def get(self, current_user):
        """
        Получить историю расхода токенов для построения графиков
        
        Параметры:
        - days: количество дней назад (по умолчанию 30)
        - agent_id: опционально, фильтр по агенту
        
        Возвращает массив с данными по каждому дню:
        - date: дата
        - total_tokens: всего токенов
        - prompt_tokens: токены запроса
        - completion_tokens: токены ответа
        - cost_rub: стоимость в рублях
        - requests_count: количество запросов
        """
        try:
            user_id = current_user.get('user_id')
            days = int(request.args.get('days', 30))
            agent_id = request.args.get('agent_id')
            
            db_session = get_db_session()
            from app.billing.services.token_usage_service import TokenUsageService
            
            token_service = TokenUsageService(db_session)
            history = token_service.get_token_history(
                user_id=user_id,
                days=days,
                agent_id=agent_id
            )
            
            return {
                "success": True,
                "data": history,
                "period": {
                    "days": days,
                    "agent_id": agent_id
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting token usage history: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens/by-agent')
class TokenUsageByAgent(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage_by_agent', 
                    description='Получить статистику по агентам - какой агент сколько токенов расходует', 
                    security='BearerAuth')
    @billing_ns.param('period_days', 'Период в днях (по умолчанию 30)', _in='query', type='integer')
    def get(self, current_user):
        """
        Получить статистику расхода токенов по агентам
        
        Показывает:
        - Какой агент сколько токенов использует
        - Стоимость работы каждого агента
        - Среднее время выполнения
        - Количество запросов
        
        Полезно для оптимизации расходов и выбора правильных агентов
        """
        try:
            user_id = current_user.get('user_id')
            period_days = int(request.args.get('period_days', 30))
            
            db_session = get_db_session()
            from app.billing.services.token_usage_service import TokenUsageService
            
            token_service = TokenUsageService(db_session)
            agents_stats = token_service.get_usage_by_agent(
                user_id=user_id,
                period_days=period_days
            )
            
            # Добавляем общую статистику
            total_tokens = sum(agent['total_tokens'] for agent in agents_stats)
            total_cost = sum(agent['cost_rub'] for agent in agents_stats)
            total_requests = sum(agent['requests_count'] for agent in agents_stats)
            
            return {
                "success": True,
                "data": {
                    "agents": agents_stats,
                    "totals": {
                        "total_tokens": total_tokens,
                        "total_cost_rub": total_cost,
                        "total_requests": total_requests
                    },
                    "period_days": period_days
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting token usage by agent: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens/by-model')
class TokenUsageByModel(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage_by_model', 
                    description='Получить статистику по AI моделям (GPT-4, GPT-3.5, Claude и т.д.)', 
                    security='BearerAuth')
    @billing_ns.param('period_days', 'Период в днях (по умолчанию 30)', _in='query', type='integer')
    def get(self, current_user):
        """
        Получить статистику расхода токенов по AI моделям
        
        Показывает:
        - Расход по провайдерам (OpenAI, Anthropic)
        - Расход по конкретным моделям (GPT-4, GPT-3.5-turbo, Claude-3, etc)
        - Стоимость каждой модели
        - Количество запросов
        
        Полезно для понимания какие модели дороже и оптимизации
        """
        try:
            user_id = current_user.get('user_id')
            period_days = int(request.args.get('period_days', 30))
            
            db_session = get_db_session()
            from app.billing.services.token_usage_service import TokenUsageService
            
            token_service = TokenUsageService(db_session)
            models_stats = token_service.get_usage_by_model(
                user_id=user_id,
                period_days=period_days
            )
            
            # Группируем по провайдерам
            by_provider = {}
            for model_stat in models_stats:
                provider = model_stat['ai_provider']
                if provider not in by_provider:
                    by_provider[provider] = {
                        "provider": provider,
                        "total_tokens": 0,
                        "total_cost_rub": 0,
                        "total_requests": 0,
                        "models": []
                    }
                by_provider[provider]["total_tokens"] += model_stat['total_tokens']
                by_provider[provider]["total_cost_rub"] += model_stat['cost_rub']
                by_provider[provider]["total_requests"] += model_stat['requests_count']
                by_provider[provider]["models"].append(model_stat)
            
            return {
                "success": True,
                "data": {
                    "by_model": models_stats,
                    "by_provider": list(by_provider.values()),
                    "period_days": period_days
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting token usage by model: {e}")
            return handle_exception(e)


@billing_ns.route('/usage/tokens/detailed')
class TokenUsageDetailed(Resource):
    @jwt_required
    @billing_ns.doc('get_token_usage_detailed', 
                    description='Получить детальную историю использования токенов с пагинацией', 
                    security='BearerAuth')
    @billing_ns.param('limit', 'Количество записей на странице (по умолчанию 100)', _in='query', type='integer')
    @billing_ns.param('offset', 'Смещение для пагинации (по умолчанию 0)', _in='query', type='integer')
    @billing_ns.param('agent_id', 'Фильтр по агенту', _in='query')
    @billing_ns.param('start_date', 'Начальная дата (ISO формат)', _in='query')
    @billing_ns.param('end_date', 'Конечная дата (ISO формат)', _in='query')
    def get(self, current_user):
        """
        Получить детальную таблицу использования токенов
        
        Параметры:
        - limit: записей на странице (по умолчанию 100, макс 500)
        - offset: смещение для пагинации
        - agent_id: фильтр по конкретному агенту
        - start_date: фильтр с даты (ISO формат)
        - end_date: фильтр по дату (ISO формат)
        
        Возвращает:
        - items: массив записей использования
        - total: общее количество записей
        - has_more: есть ли еще записи
        
        Каждая запись содержит полную информацию о запросе к AI
        """
        try:
            user_id = current_user.get('user_id')
            limit = min(int(request.args.get('limit', 100)), 500)  # макс 500
            offset = int(request.args.get('offset', 0))
            agent_id = request.args.get('agent_id')
            
            # Парсим даты если указаны
            start_date = None
            end_date = None
            if request.args.get('start_date'):
                from datetime import datetime
                start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
            if request.args.get('end_date'):
                from datetime import datetime
                end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
            
            db_session = get_db_session()
            from app.billing.services.token_usage_service import TokenUsageService
            
            token_service = TokenUsageService(db_session)
            detailed = token_service.get_detailed_usage(
                user_id=user_id,
                limit=limit,
                offset=offset,
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "success": True,
                "data": detailed
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting detailed token usage: {e}")
            return handle_exception(e)


@billing_ns.route('/agents/recommendations')
class AgentRecommendations(Resource):
    @jwt_required
    @billing_ns.doc('get_recommendations', description='Получить рекомендации по агентам', security='BearerAuth')
    def get(self, current_user):
        """Получить рекомендации агентов на основе использования"""
        try:
            user_id = current_user.get('user_id')
            db_session = get_db_session()
            
            from app.billing.middleware.agent_access_middleware import AgentAccessMiddleware
            
            recommendations = AgentAccessMiddleware.recommend_agents(user_id, db_session)
            
            return recommendations, 200
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
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
            from app.billing.services.yookassa_service import YooKassaService
            
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


# ==================== CONTENT SOURCES ENDPOINTS ====================

@content_sources_ns.route('')
@content_sources_ns.route('/')
class ContentSourcesList(Resource):
    """Список источников контента пользователя"""
    
    @jwt_required
    @content_sources_ns.doc('list_content_sources', description='Получить список источников контента')
    def get(self, current_user=None):
        """Получить список всех источников контента текущего пользователя"""
        try:
            # Получаем user_id из request (установлен в jwt_required) или из current_user
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            
            sources = ContentSourceService.get_user_sources(user_id)
            
            return {
                'success': True,
                'data': [source.to_dict() for source in sources]
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting content sources: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500
    
    @jwt_required
    @content_sources_ns.doc('create_content_source', description='Создать новый источник контента')
    def post(self, current_user=None):
        """Создать новый источник контента"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            data = request.get_json()
            
            # Валидация обязательных полей
            if not data.get('name'):
                return {'success': False, 'error': 'Название источника обязательно'}, 400
            if not data.get('url'):
                return {'success': False, 'error': 'URL источника обязательно'}, 400
            
            # Преобразуем keywords из строки в список, если нужно
            keywords = data.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split('\n') if k.strip()]
            
            # Сохраняем posting_schedule в config
            config = data.get('posting_schedule', {})
            
            # По умолчанию используем 'auto' для автоматической детекции RSS
            source_type = data.get('source_type', 'auto')
            if source_type not in ['rss', 'website', 'auto']:
                source_type = 'auto'
            
            source = ContentSourceService.create_source(
                user_id=user_id,
                name=data['name'],
                source_type=source_type,
                url=data['url'],
                keywords=keywords,
                exclude_keywords=data.get('exclude_keywords', []),
                check_interval_minutes=data.get('check_interval_minutes', 60),
                config={'posting_schedule': config},
                is_active=data.get('is_active', True),
                auto_post_enabled=True  # По умолчанию включаем автопостинг
            )
            
            if source:
                # Немедленно проверяем источник в фоне, чтобы создать посты из существующих новостей
                try:
                    from app.workers.web_crawler_worker import WebCrawlerWorker
                    import asyncio
                    
                    # Создаем временный worker для немедленной проверки
                    temp_worker = WebCrawlerWorker(check_interval=60)
                    logger.info(f"🚀 Запускаем немедленную проверку источника {source.id} после создания...")
                    
                    # Запускаем проверку в фоне (не блокируем ответ)
                    def check_source_async():
                        try:
                            # Убеждаемся, что источник активен для проверки
                            db = get_db_session()
                            try:
                                source_obj = db.query(ContentSource).filter(ContentSource.id == source.id).first()
                                if source_obj and not source_obj.is_active:
                                    logger.warning(f"⚠️ Источник {source.id} неактивен, активируем для проверки...")
                                    source_obj.is_active = True
                                    db.commit()
                            finally:
                                db.close()
                            
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            result = loop.run_until_complete(temp_worker._check_source(source))
                            logger.info(f"✅ Немедленная проверка источника {source.id} завершена: найдено {result.get('items_new', 0)} новых новостей, создано {result.get('items_posted', 0)} постов")
                        except Exception as e:
                            logger.error(f"❌ Ошибка при немедленной проверке источника {source.id}: {e}", exc_info=True)
                    
                    import threading
                    check_thread = threading.Thread(target=check_source_async, daemon=True)
                    check_thread.start()
                    logger.info(f"⏳ Проверка источника {source.id} запущена в фоне...")
                    
                except Exception as e:
                    # Если не удалось запустить проверку - не критично, источник все равно создан
                    logger.warning(f"⚠️ Не удалось запустить немедленную проверку источника {source.id}: {e}")
                
                return {
                    'success': True,
                    'data': source.to_dict(),
                    'message': 'Источник создан. Запущена проверка для поиска новостей...'
                }, 201
            else:
                return {
                    'success': False,
                    'error': 'Не удалось создать источник'
                }, 500
                
        except Exception as e:
            logger.error(f"Error creating content source: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/<int:source_id>')
class ContentSourceDetail(Resource):
    """Детали источника контента"""
    
    @jwt_required
    @content_sources_ns.doc('get_content_source', description='Получить детали источника')
    def get(self, source_id, current_user=None):
        """Получить детали источника контента"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            
            source = ContentSourceService.get_source(source_id, user_id)
            
            if source:
                return {
                    'success': True,
                    'data': source.to_dict()
                }, 200
            else:
                return {
                    'success': False,
                    'error': 'Источник не найден'
                }, 404
                
        except Exception as e:
            logger.error(f"Error getting content source: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500
    
    @jwt_required
    @content_sources_ns.doc('update_content_source', description='Обновить источник контента')
    def put(self, source_id, current_user=None):
        """Обновить источник контента"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            data = request.get_json()
            
            # Преобразуем keywords из строки в список, если нужно
            if 'keywords' in data and isinstance(data['keywords'], str):
                data['keywords'] = [k.strip() for k in data['keywords'].split('\n') if k.strip()]
            
            # Обновляем posting_schedule в config
            posting_schedule = data.pop('posting_schedule', None)
            if posting_schedule is not None:
                # Получаем текущий config или создаем новый
                db = get_db_session()
                try:
                    source = ContentSourceService.get_source(source_id, user_id)
                    if source:
                        if not source.config:
                            source.config = {}
                        source.config['posting_schedule'] = posting_schedule
                        db.commit()
                finally:
                    db.close()
            
            # Обновляем остальные поля через update_source
            source = ContentSourceService.update_source(source_id, user_id, **data)
            
            if source:
                return {
                    'success': True,
                    'data': source.to_dict()
                }, 200
            else:
                return {
                    'success': False,
                    'error': 'Источник не найден или нет прав на обновление'
                }, 404
                
        except Exception as e:
            logger.error(f"Error updating content source: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500
    
    @jwt_required
    @content_sources_ns.doc('delete_content_source', description='Удалить источник контента')
    def delete(self, source_id, current_user=None):
        """Удалить источник контента"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            
            success = ContentSourceService.delete_source(source_id, user_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Источник удален'
                }, 200
            else:
                return {
                    'success': False,
                    'error': 'Источник не найден или нет прав на удаление'
                }, 404
                
        except Exception as e:
            logger.error(f"Error deleting content source: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/<int:source_id>/toggle')
class ContentSourceToggle(Resource):
    """Включить/выключить источник контента"""
    
    @jwt_required
    @content_sources_ns.doc('toggle_content_source', description='Включить/выключить источник')
    def post(self, source_id, current_user=None):
        """Включить/выключить источник контента"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            data = request.get_json()
            is_active = data.get('is_active', True)
            
            source = ContentSourceService.update_source(
                source_id, 
                user_id, 
                is_active=is_active
            )
            
            if source:
                return {
                    'success': True,
                    'data': source.to_dict()
                }, 200
            else:
                return {
                    'success': False,
                    'error': 'Источник не найден'
                }, 404
                
        except Exception as e:
            logger.error(f"Error toggling content source: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/suggest-keywords')
class SuggestKeywords(Resource):
    """Автогенерация ключевых слов на основе ответов опросника"""
    
    @jwt_required
    @content_sources_ns.doc('suggest_keywords', description='Сгенерировать ключевые слова на основе ответов опросника')
    def post(self, current_user=None):
        """Сгенерировать ключевые слова"""
        try:
            # Получаем user_id из request (установлен в jwt_required) или из current_user
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            
            data = request.get_json()
            
            # Формируем промпт для AI
            business_description = data.get('businessDescription', '')
            topics = data.get('topics', [])
            keywords = data.get('keywords', '')
            audience = data.get('audience', [])
            hashtags = data.get('hashtags', '')
            
            # Если уже есть ключевые слова из формы, используем их как основу
            existing_keywords = []
            if keywords:
                existing_keywords = [k.strip() for k in keywords.split('\n') if k.strip()]
            
            # Формируем промпт для OpenAI
            prompt = f"""
На основе следующей информации о канале, сгенерируй список из 10-15 релевантных ключевых слов для мониторинга новостей:

О канале: {business_description}
Темы интересов: {', '.join(topics) if topics else 'не указаны'}
Указанные слова/бренды: {keywords if keywords else 'не указаны'}
Аудитория: {', '.join(audience) if audience else 'не указана'}
Хэштеги: {hashtags if hashtags else 'не указаны'}

Требования:
1. Включи все указанные пользователем слова/бренды
2. Добавь релевантные ключевые слова на основе описания канала и тем
3. Учти целевую аудиторию
4. Верни только список ключевых слов через запятую, без дополнительных объяснений
5. Каждое ключевое слово должно быть на отдельной строке

Формат ответа (только ключевые слова, каждое с новой строки):
"""
            
            # Вызываем OpenAI для генерации
            try:
                from openai import AsyncOpenAI
                import os
                import asyncio
                import json
                
                api_key = os.environ.get('OPENAI_API_KEY')
                if not api_key:
                    raise Exception("OPENAI_API_KEY not set")
                
                openai_client = AsyncOpenAI(api_key=api_key)
                
                # Формируем промпт для генерации ключевых слов
                system_prompt = "Ты помощник для генерации ключевых слов для мониторинга новостей. Верни только список ключевых слов через запятую, без дополнительных объяснений."
                
                async def generate_keywords():
                    response = await openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=200
                    )
                    return response.choices[0].message.content
                
                # Используем синхронный вызов через asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response_text = loop.run_until_complete(generate_keywords())
                
                # Парсим ответ - извлекаем ключевые слова
                generated_keywords = []
                if response_text:
                    # Разбиваем по строкам и запятым
                    lines = response_text.replace('\n', ',').split(',')
                    for line in lines:
                        keyword = line.strip()
                        if keyword and len(keyword) > 1:
                            generated_keywords.append(keyword)
                
                # Объединяем существующие и сгенерированные, убираем дубликаты
                all_keywords = list(set(existing_keywords + generated_keywords))
                
                # Ограничиваем до 20 ключевых слов
                all_keywords = all_keywords[:20]
                
                logger.info(f"Generated {len(all_keywords)} keywords for user")
                
                return {
                    'success': True,
                    'data': {
                        'keywords': all_keywords
                    }
                }, 200
                
            except Exception as e:
                logger.error(f"Error generating keywords with AI: {e}")
                # Fallback: возвращаем существующие ключевые слова или базовые
                if existing_keywords:
                    return {
                        'success': True,
                        'data': {
                            'keywords': existing_keywords
                        }
                    }, 200
                else:
                    # Генерируем базовые ключевые слова на основе тем
                    basic_keywords = []
                    topic_keywords_map = {
                        'beauty': ['красота', 'маникюр', 'прически', 'стиль'],
                        'finance': ['финансы', 'инвестиции', 'экономика', 'биржа'],
                        'pets': ['собаки', 'кошки', 'домашние животные', 'питомцы'],
                        'cooking': ['кулинария', 'рецепты', 'готовка', 'еда'],
                        'sport': ['спорт', 'здоровье', 'фитнес', 'тренировки'],
                        'tech': ['технологии', 'гаджеты', 'инновации', 'IT'],
                    }
                    
                    for topic in topics:
                        if topic in topic_keywords_map:
                            basic_keywords.extend(topic_keywords_map[topic])
                    
                    if not basic_keywords:
                        basic_keywords = ['новости', 'актуальное']
                    
                    return {
                        'success': True,
                        'data': {
                            'keywords': list(set(basic_keywords))
                        }
                    }, 200
                    
        except Exception as e:
            logger.error(f"Error in suggest_keywords: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/production-calendar/check')
class ProductionCalendarCheck(Resource):
    """Проверка даты через производственный календарь"""
    
    @jwt_required
    @content_sources_ns.doc('check_production_calendar', description='Проверить дату через производственный календарь')
    def post(self, current_user=None):
        """Проверить, является ли дата рабочим днем"""
        try:
            data = request.get_json()
            date_str = data.get('date')
            country = data.get('country', 'ru')
            
            if not date_str:
                return {
                    'success': False,
                    'error': 'Дата не указана'
                }, 400
            
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            is_working = ProductionCalendarService.is_working_day(check_date, country)
            
            return {
                'success': True,
                'data': {
                    'date': date_str,
                    'is_working_day': is_working,
                    'is_weekend': not is_working
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error checking production calendar: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/<int:source_id>/check-now')
class CheckSourceNow(Resource):
    """Немедленная проверка источника"""
    
    @jwt_required
    @content_sources_ns.doc('check_source_now', description='Запустить немедленную проверку источника')
    def post(self, source_id, current_user=None):
        """Запустить немедленную проверку источника"""
        try:
            user_id = request.user_id or (current_user.get('user_id') if current_user else None)
            if not user_id:
                return {'success': False, 'error': 'User not authenticated'}, 401
            
            source = ContentSourceService.get_source(source_id, user_id)
            if not source:
                return {'success': False, 'error': 'Источник не найден'}, 404
            
            # Активируем источник, если он неактивен
            if not source.is_active:
                db = get_db_session()
                try:
                    source.is_active = True
                    db.commit()
                    db.refresh(source)
                finally:
                    db.close()
            
            # Включаем автопостинг, если он выключен
            if not source.auto_post_enabled:
                db = get_db_session()
                try:
                    source.auto_post_enabled = True
                    db.commit()
                    db.refresh(source)
                finally:
                    db.close()
            
            # Запускаем проверку в фоне
            try:
                from app.workers.web_crawler_worker import WebCrawlerWorker
                import asyncio
                import threading
                
                temp_worker = WebCrawlerWorker(check_interval=60)
                logger.info(f"🚀 Запускаем ручную проверку источника {source.id}...")
                
                def check_source_async():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(temp_worker._check_source(source))
                        if result:
                            logger.info(f"✅ Ручная проверка источника {source.id} завершена: найдено {result.get('items_new', 0)} новых новостей, создано {result.get('items_posted', 0)} постов")
                        else:
                            logger.warning(f"⚠️ Ручная проверка источника {source.id} вернула None (возможно, произошла ошибка)")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при ручной проверке источника {source.id}: {e}", exc_info=True)
                
                check_thread = threading.Thread(target=check_source_async, daemon=True)
                check_thread.start()
                
                return {
                    'success': True,
                    'message': 'Проверка источника запущена. Результаты появятся через несколько секунд.'
                }, 200
                
            except Exception as e:
                logger.error(f"Error starting manual check: {e}")
                return {
                    'success': False,
                    'error': f'Не удалось запустить проверку: {str(e)}'
                }, 500
                
        except Exception as e:
            logger.error(f"Error in check_source_now: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500


@content_sources_ns.route('/fetch-metadata')
class FetchWebsiteMetadata(Resource):
    """Получение метаданных сайта (название, описание)"""
    
    @jwt_required
    @content_sources_ns.doc('fetch_metadata', description='Получить метаданные сайта по URL')
    def post(self, current_user=None):
        """Получить название и описание сайта по URL"""
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return {
                    'success': False,
                    'error': 'URL не указан'
                }, 400
            
            # Валидация URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Загружаем страницу
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ContentCurator/1.0; +https://content-curator.com)'
            })
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем title
            title = None
            if soup.title:
                title = soup.title.string.strip() if soup.title.string else None
            
            # Если title не найден, пробуем og:title
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title.get('content').strip()
            
            # Если title все еще не найден, используем домен
            if not title:
                parsed_url = urlparse(url)
                title = parsed_url.netloc.replace('www.', '')
            
            # Извлекаем описание
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content').strip()
            
            # Если description не найден, пробуем og:description
            if not description:
                og_desc = soup.find('meta', property='og:description')
                if og_desc and og_desc.get('content'):
                    description = og_desc.get('content').strip()
            
            return {
                'success': True,
                'data': {
                    'title': title,
                    'description': description,
                    'url': url
                }
            }, 200
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching metadata for {url}: {e}")
            # Не возвращаем ошибку, просто возвращаем домен как название
            try:
                parsed_url = urlparse(url if url else '')
                domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else url
            except:
                domain = url.split('/')[2] if '/' in url else url
            
            return {
                'success': True,
                'data': {
                    'title': domain,
                    'description': None,
                    'url': url
                }
            }, 200
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
            # Не возвращаем ошибку пользователю, всегда возвращаем успех
            try:
                parsed_url = urlparse(url if url else '')
                domain = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else url
            except:
                domain = url.split('/')[2] if '/' in url else url
            
            return {
                'success': True,
                'data': {
                    'title': domain,
                    'description': None,
                    'url': url
                }
            }, 200


# ==================== AI ONBOARDING ENDPOINTS ====================

@ai_ns.route('/generate-questions')
class GenerateOnboardingQuestions(Resource):
    """AI генерация персонализированных вопросов для опросника"""
    
    @jwt_required
    @ai_ns.doc('generate_questions', description='Генерировать персонализированные вопросы на основе типа бизнеса и ниши')
    def post(self, current_user=None):
        """Генерировать персонализированные вопросы"""
        try:
            import openai
            
            data = request.get_json()
            business_type = data.get('businessType', '')
            niche = data.get('niche', '')
            previous_answers = data.get('previousAnswers', [])
            
            if not niche:
                return {
                    'success': False,
                    'error': 'Ниша не указана'
                }, 400
            
            # Проверяем наличие OpenAI API ключа
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY не установлен, используем fallback вопросы")
                return {
                    'success': True,
                    'data': {
                        'questions': get_fallback_questions(business_type)
                    }
                }, 200
            
            # Формируем промпт
            business_type_ru = {
                'product': 'продажа товаров',
                'service': 'оказание услуг',
                'personal_brand': 'личный бренд',
                'company_brand': 'бренд компании'
            }.get(business_type, 'бизнес')
            
            prev_answers_text = ""
            if previous_answers:
                prev_answers_text = "Предыдущие ответы пользователя:\n"
                for ans in previous_answers:
                    prev_answers_text += f"- {ans.get('questionId', '')}: {ans.get('answer', '')}\n"
            
            prompt = f"""Ты - AI-ассистент для создания контент-стратегии.

Контекст пользователя:
- Тип бизнеса: {business_type_ru}
- Ниша: {niche}
{prev_answers_text}

Сгенерируй 5 уточняющих вопросов для создания контент-плана в Telegram.

Требования к вопросам:
1. Вопросы должны быть короткими (до 15 слов)
2. Понятными для человека без маркетингового образования
3. Каждый вопрос должен иметь 4-5 вариантов ответа
4. Последний вариант всегда "Свой вариант"
5. Варианты должны быть конкретными, не абстрактными

Вопросы должны помочь понять:
- Целевую аудиторию и её боли
- Тон общения (деловой, дружелюбный, с юмором)
- Цели канала (продажи, экспертность, вовлечение)
- Предпочтительный формат контента
- Призыв к действию

Ответ ТОЛЬКО в формате JSON без markdown:
{{"questions": [
  {{"id": "tone", "title": "Вопрос?", "hint": "Подсказка", "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Свой вариант"]}}
]}}"""

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты генерируешь вопросы для опросника. Отвечай только валидным JSON без markdown."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                # Очищаем от markdown если есть
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                
                import json
                result = json.loads(content)
                
                logger.info(f"AI сгенерировал {len(result.get('questions', []))} вопросов для {niche}")
                
                return {
                    'success': True,
                    'data': result
                }, 200
            else:
                return {
                    'success': True,
                    'data': {
                        'questions': get_fallback_questions(business_type)
                    }
                }, 200
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {
                'success': True,
                'data': {
                    'questions': get_fallback_questions(business_type)
                }
            }, 200
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return {
                'success': True,
                'data': {
                    'questions': get_fallback_questions(data.get('businessType', ''))
                }
            }, 200


@ai_ns.route('/generate-sample-posts')
class GenerateSamplePosts(Resource):
    """AI генерация примеров постов для выбора стиля"""
    
    @jwt_required
    @ai_ns.doc('generate_sample_posts', description='Генерировать примеры постов в разных стилях')
    def post(self, current_user=None):
        """Генерировать примеры постов"""
        try:
            import openai
            import json
            
            data = request.get_json()
            business_type = data.get('businessType', '')
            niche = data.get('niche', '')
            answers = data.get('answers', [])
            
            if not niche:
                return {
                    'success': False,
                    'error': 'Ниша не указана'
                }, 400
            
            # Проверяем наличие OpenAI API ключа
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY не установлен, используем fallback посты")
                return {
                    'success': True,
                    'data': {
                        'posts': get_fallback_posts(niche)
                    }
                }, 200
            
            # Собираем контекст из ответов
            answers_context = ""
            for ans in answers:
                answers_context += f"- {ans.get('questionId', '')}: {ans.get('answer', '')}\n"
            
            prompt = f"""Ты - копирайтер для Telegram-каналов.

Контекст:
- Ниша: {niche}
- Тип бизнеса: {business_type}
- Ответы пользователя:
{answers_context}

Создай 3 примера постов для Telegram в РАЗНЫХ стилях:

1. Профессиональный - деловой тон, факты, экспертность
2. Дружелюбный - тёплый, эмоциональный, с обращением к читателю
3. История - сторителлинг, конкретный случай, эмоции

Требования к каждому посту:
- Длина 500-800 символов
- Начинается с hook (зацепка)
- Содержит основную мысль
- Заканчивается призывом к действию
- Используй эмодзи умеренно

Ответ ТОЛЬКО в формате JSON без markdown:
{{"posts": [
  {{"id": "professional", "style": "Профессиональный", "content": "Текст поста..."}},
  {{"id": "friendly", "style": "Дружелюбный", "content": "Текст поста..."}},
  {{"id": "story", "style": "История", "content": "Текст поста..."}}
]}}"""

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты генерируешь примеры постов для Telegram. Отвечай только валидным JSON без markdown."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.8
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                # Очищаем от markdown если есть
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                
                result = json.loads(content)
                
                logger.info(f"AI сгенерировал {len(result.get('posts', []))} примеров постов для {niche}")
                
                return {
                    'success': True,
                    'data': result
                }, 200
            else:
                return {
                    'success': True,
                    'data': {
                        'posts': get_fallback_posts(niche)
                    }
                }, 200
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for posts: {e}")
            return {
                'success': True,
                'data': {
                    'posts': get_fallback_posts(niche)
                }
            }, 200
        except Exception as e:
            logger.error(f"Error generating sample posts: {e}")
            return {
                'success': True,
                'data': {
                    'posts': get_fallback_posts(data.get('niche', ''))
                }
            }, 200


@ai_ns.route('/save-progress')
class SaveOnboardingProgress(Resource):
    """Сохранение прогресса опросника"""
    
    @jwt_required
    @ai_ns.doc('save_progress', description='Сохранить прогресс опросника')
    def post(self, current_user=None):
        """Сохранить прогресс опросника"""
        try:
            data = request.get_json()
            user_id = current_user.get('user_id') if current_user else None
            
            if not user_id:
                return {
                    'success': False,
                    'error': 'Пользователь не авторизован'
                }, 401
            
            # Сохраняем в БД (можно использовать отдельную таблицу или JSON поле)
            db = get_db_session()
            from app.models.user import OnboardingProgress
            
            progress = db.query(OnboardingProgress).filter_by(user_id=user_id).first()
            if progress:
                progress.data = data
                progress.updated_at = datetime.now()
            else:
                progress = OnboardingProgress(
                    user_id=user_id,
                    data=data,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(progress)
            
            db.commit()
            
            return {
                'success': True,
                'message': 'Прогресс сохранён'
            }, 200
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
            # Не ломаем UX если БД недоступна
            return {
                'success': True,
                'message': 'Прогресс сохранён локально'
            }, 200


@ai_ns.route('/get-progress')
class GetOnboardingProgress(Resource):
    """Получение сохранённого прогресса опросника"""
    
    @jwt_required
    @ai_ns.doc('get_progress', description='Получить сохранённый прогресс опросника')
    def get(self, current_user=None):
        """Получить сохранённый прогресс"""
        try:
            user_id = current_user.get('user_id') if current_user else None
            
            if not user_id:
                return {
                    'success': False,
                    'error': 'Пользователь не авторизован'
                }, 401
            
            db = get_db_session()
            from app.models.user import OnboardingProgress
            
            progress = db.query(OnboardingProgress).filter_by(user_id=user_id).first()
            
            if progress:
                return {
                    'success': True,
                    'data': progress.data
                }, 200
            else:
                return {
                    'success': True,
                    'data': None
                }, 200
            
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return {
                'success': True,
                'data': None
            }, 200


@ai_ns.route('/enrich-project-profile')
class EnrichProjectProfile(Resource):
    """AI-генератор профиля проекта по короткому описанию или анализу сайта"""
    
    @jwt_required
    @ai_ns.doc('enrich_project_profile', description='Генерировать детальный маркетинговый профиль по короткому описанию бизнеса или URL сайта')
    def post(self, current_user=None):
        """Генерировать профиль проекта"""
        try:
            import openai
            import json
            import requests
            from bs4 import BeautifulSoup
            
            data = request.get_json()
            short_description = data.get('short_description', '').strip()
            url = data.get('url', '').strip()
            
            # Нужен либо URL, либо описание
            if not short_description and not url:
                return {
                    'success': False,
                    'error': 'Укажите описание бизнеса или URL сайта'
                }, 400
            
            # Проверяем наличие OpenAI API ключа
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY не установлен")
                return {
                    'success': False,
                    'error': 'AI-сервис временно недоступен'
                }, 503
            
            # Если есть URL — скачиваем и анализируем сайт
            site_content = ""
            if url:
                try:
                    # Добавляем протокол если нет
                    if not url.startswith('http'):
                        url = 'https://' + url
                    
                    logger.info(f"Загружаем сайт: {url}")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    # Парсим HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Удаляем скрипты и стили
                    for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                        script.decompose()
                    
                    # Извлекаем текст
                    text = soup.get_text(separator=' ', strip=True)
                    
                    # Очищаем и обрезаем
                    import re
                    text = re.sub(r'\s+', ' ', text)
                    site_content = text[:3000]  # Ограничиваем для контекста
                    
                    logger.info(f"Извлечено {len(site_content)} символов с сайта")
                    
                except requests.RequestException as e:
                    logger.warning(f"Не удалось загрузить сайт {url}: {e}")
                    if not short_description:
                        return {
                            'success': False,
                            'error': f'Не удалось загрузить сайт: {str(e)}'
                        }, 400
            
            # Системный промпт
            system_prompt = """Ты опытный маркетолог и копирайтер. Твоя задача - создать детальный профиль бренда для создания контента в социальных сетях.

ВАЖНО: Отвечай на русском языке.

Ты должен вернуть JSON со следующими полями:
- business_description: Развернутое, красивое описание бизнеса на 2-3 абзаца. Опиши уникальность, ценности, миссию.
- target_audience: Детальное описание целевой аудитории (пол, возраст, интересы, боли, мотивации). 3-4 предложения.
- tone_of_voice: Рекомендуемый тон коммуникации (например: "Дружелюбный и экспертный"). Одна фраза.
- keywords: Массив из 8-12 ключевых слов/тегов для контента.
- products_services: Краткий список основных товаров/услуг (если можно определить).
- usp: Уникальное торговое предложение - что отличает от конкурентов.

Отвечай ТОЛЬКО валидным JSON без markdown-разметки."""

            # Формируем user prompt
            if site_content:
                user_prompt = f"""Проанализируй контент с сайта клиента и создай маркетинговый профиль.

КОНТЕНТ САЙТА:
{site_content}

{f'ДОПОЛНИТЕЛЬНОЕ ОПИСАНИЕ: {short_description}' if short_description else ''}

Верни JSON с полями: business_description, target_audience, tone_of_voice, keywords, products_services, usp"""
            else:
                user_prompt = f"""Создай маркетинговый профиль для бизнеса:

"{short_description}"

Верни JSON с полями: business_description, target_audience, tone_of_voice, keywords, products_services, usp"""

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                
                # Очищаем от markdown если есть
                if content.startswith('```'):
                    lines = content.split('\n')
                    # Убираем первую и последнюю строки с ```
                    content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                    if content.startswith('json'):
                        content = content[4:].strip()
                
                result = json.loads(content)
                
                # Валидируем наличие всех полей
                required_fields = ['business_description', 'target_audience', 'tone_of_voice', 'keywords']
                for field in required_fields:
                    if field not in result:
                        result[field] = '' if field != 'keywords' else []
                
                # Убедимся что keywords - это массив
                if isinstance(result.get('keywords'), str):
                    result['keywords'] = [k.strip() for k in result['keywords'].split(',')]
                
                logger.info(f"AI сгенерировал профиль {'по сайту ' + url if url else 'по описанию'}")
                
                return {
                    'success': True,
                    'data': result
                }, 200
            else:
                return {
                    'success': False,
                    'error': 'AI не вернул ответ'
                }, 500
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in enrich-project-profile: {e}")
            return {
                'success': False,
                'error': 'Ошибка парсинга ответа AI'
            }, 500
        except Exception as e:
            logger.error(f"Error in enrich-project-profile: {e}")
            return {
                'success': False,
                'error': f'Ошибка генерации: {str(e)}'
            }, 500


def get_fallback_questions(business_type):
    """Fallback вопросы если AI недоступен"""
    return [
        {
            "id": "tone",
            "title": "Какой тон общения вам ближе?",
            "hint": "Выберите стиль, который отражает вас как автора",
            "options": [
                "Деловой и экспертный",
                "Тёплый и дружелюбный",
                "С юмором и легкостью",
                "Мотивирующий и энергичный",
                "Свой вариант"
            ]
        },
        {
            "id": "content_focus",
            "title": "На чём фокусироваться в постах?",
            "hint": "Выберите приоритет",
            "options": [
                "Кейсы и результаты",
                "Полезные советы и инструкции",
                "Личные истории и опыт",
                "Разбор ошибок и мифов",
                "Свой вариант"
            ]
        },
        {
            "id": "goals",
            "title": "Главная цель вашего канала?",
            "hint": "Выберите одну основную цель",
            "options": [
                "Больше подписчиков и вовлечения",
                "Генерация заявок и лидов",
                "Прямые продажи",
                "Узнаваемость и доверие",
                "Свой вариант"
            ]
        },
        {
            "id": "cta",
            "title": "К какому действию вести аудиторию?",
            "hint": "Основной призыв к действию",
            "options": [
                "Подписка на канал",
                "Переход на сайт",
                "Заявка на консультацию",
                "Покупка товара/услуги",
                "Свой вариант"
            ]
        },
        {
            "id": "post_length",
            "title": "Предпочтительная длина постов?",
            "hint": "Какой формат вам удобнее создавать",
            "options": [
                "Короткие (до 500 символов)",
                "Средние (500-1500 символов)",
                "Длинные (от 1500 символов)",
                "Разные - зависит от темы",
                "Свой вариант"
            ]
        }
    ]


def get_fallback_posts(niche):
    """Fallback посты если AI недоступен"""
    return [
        {
            "id": "professional",
            "style": "Профессиональный",
            "content": f"🎯 {niche or 'Ваш бизнес'}: 5 ключевых ошибок, которые стоят вам клиентов\n\nЗа последний год мы проанализировали более 100 проектов и выявили типичные ошибки:\n\n1. Отсутствие чёткого позиционирования\n2. Игнорирование обратной связи\n3. Сложный путь клиента\n4. Нет системы повторных продаж\n5. Слабая работа с возражениями\n\nКакую ошибку вы замечали у себя? Напишите в комментариях 👇"
        },
        {
            "id": "friendly",
            "style": "Дружелюбный",
            "content": f"Привет! 👋\n\nЗнаете, что меня всегда удивляет в {niche or 'нашей сфере'}?\n\nЛюди часто думают, что это сложно и дорого. А на самом деле...\n\nВчера клиент сказал: \"Почему я не обратился раньше?!\"\n\nИ знаете что? Это самый частый отзыв 😊\n\nРасскажите, что вас останавливает? Может, я смогу помочь разобраться?"
        },
        {
            "id": "story",
            "style": "История",
            "content": f"Это было 3 года назад...\n\nКо мне пришёл клиент с \"безнадёжной\" ситуацией. Все говорили: \"Забудь, ничего не получится\".\n\nНо мы попробовали. И через месяц...\n\nРезультат превзошёл все ожидания. {niche and f'В сфере {niche}' or 'В бизнесе'} нет безвыходных ситуаций — есть недостаток информации.\n\nХотите узнать, что мы сделали? Напишите \"+\" в комментариях, расскажу подробно 💬"
        }
    ]


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