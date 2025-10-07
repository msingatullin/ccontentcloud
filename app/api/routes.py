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

from app.auth.services.auth_service import AuthService
from app.auth.utils.email import EmailService
from app.database.connection import get_db_session
from ..orchestrator.main_orchestrator import orchestrator
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
    db_session = get_db_session()
    secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
    email_service = EmailService()
    return AuthService(db_session, secret_key, email_service)

# ==================== JWT MIDDLEWARE ====================

from functools import wraps

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
        
        # Проверить токен через AuthService
        try:
            auth_service = get_auth_service()
            success, payload = auth_service.verify_token(token)  # Распаковываем Tuple
            if not success or not payload:
                return {"error": "Invalid or expired token"}, 401
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            return {"error": "Token verification failed"}, 401
        
        # Передать user info в функцию
        return f(*args, current_user=payload, **kwargs)
    
    return decorated_function

# Создаем namespaces для API
api = Namespace('', description='AI Content Orchestrator API')  # Пустое имя для корневого namespace
auth_ns = Namespace('auth', description='Authentication API')
billing_ns = Namespace('billing', description='Billing API')
webhook_ns = Namespace('webhook', description='Webhook API')
health_ns = Namespace('health', description='Health Check API')

# Создаем общие модели
common_models = create_common_models(api)

# ==================== CONTENT MODELS ====================

content_request_model = api.model('ContentRequest', {
    'title': fields.String(required=True, min_length=1, max_length=200, description='Заголовок контента'),
    'description': fields.String(required=True, min_length=10, max_length=1000, description='Описание контента'),
    'target_audience': fields.String(required=True, min_length=1, max_length=200, description='Целевая аудитория'),
    'business_goals': fields.List(fields.String, required=True, min_items=1, max_items=10, description='Бизнес-цели'),
    'call_to_action': fields.String(required=True, min_length=1, max_length=200, description='Призыв к действию'),
    'tone': fields.String(description='Тон контента', enum=['professional', 'casual', 'friendly', 'authoritative'], default='professional'),
    'keywords': fields.List(fields.String, description='Ключевые слова', max_items=20),
    'platforms': fields.List(fields.String, required=True, min_items=1, max_items=5, description='Платформы для публикации'),
    'content_types': fields.List(fields.String, description='Типы контента', default=['post']),
    'constraints': fields.Raw(description='Дополнительные ограничения'),
    'test_mode': fields.Boolean(description='Тестовый режим', default=True)
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
    @api.marshal_with(content_response_model, code=201, description='Контент успешно создан')
    @api.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self, current_user):
        """
        Создает контент через AI агентов
        
        Принимает запрос на создание контента и запускает workflow
        с участием всех необходимых агентов.
        """
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # Валидируем входные данные
            try:
                content_request = ContentRequestSchema(**request.json)
            except ValidationError as e:
                return handle_validation_error(e)
            
            logger.info(f"User {email} (ID: {user_id}) создает контент: {content_request.title}")
            
            # Преобразуем Pydantic модель в словарь
            request_data = content_request.dict()
            # Добавляем user_id в данные запроса
            request_data['user_id'] = user_id
            
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
    # @jwt_required  # ВРЕМЕННО ОТКЛЮЧЕНО ДЛЯ ТЕСТИРОВАНИЯ
    @api.doc('get_agents_status', description='Получает статус всех агентов или конкретного агента')
    @api.param('agent_id', 'ID конкретного агента (опционально)', type='string')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ ВСЕ marshal_with для корректного отображения данных
    # @api.marshal_with(agents_response_model, code=200, description='Статус агентов')
    # @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self):
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
            
            # JWT временно отключен для тестирования
            # user_id = current_user.get('user_id')
            # email = current_user.get('email')
            
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
    @api.doc('get_agent_tasks', description='Получает список задач конкретного агента')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(common_models['error'], code=404, description='Агент не найден')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, agent_id):
        """
        Получает список задач конкретного агента
        """
        try:
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

@api.route('/platforms')
class Platforms(Resource):
    @api.doc('get_platforms', description='Получает список поддерживаемых платформ')
    # ВРЕМЕННО ОТКЛЮЧЕНЫ marshal_with для корректного отображения данных
    # @api.marshal_with(platform_stats_model, code=200, description='Список платформ')
    # @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
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
    @jwt_required
    @api.doc('analyze_trends', description='Анализ трендов через TrendsScoutAgent')
    @api.expect(trends_analysis_request_model, validate=True)
    @api.marshal_with(trends_analysis_response_model, code=200, description='Анализ трендов выполнен')
    @api.marshal_with(common_models['error'], code=400, description='Некорректные данные')
    @api.marshal_with(common_models['error'], code=503, description='Агент недоступен')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self, current_user):
        """Анализ трендов через TrendsScoutAgent"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            data = request.get_json()
            if not data:
                return {
                    "error": "Invalid request",
                    "message": "Требуется JSON данные",
                    "status_code": 400,
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            logger.info(f"User {email} (ID: {user_id}) анализирует тренды")
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
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
    # @auth_ns.marshal_with снят для корректного отображения токенов
    def post(self):
        """Обновление токена"""
        try:
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            token_jti = current_user.get('jti')  # Получаем JTI из токена
            
            logger.info(f"Logout request from user {email} (ID: {user_id})")
            
            # Инициализируем AuthService
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
            # Деактивируем сессию в БД
            success, message = auth_service.logout_user(token_jti)
            
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
            from ...auth.services.auth_service import AuthService
            from ...auth.utils.email import EmailService
            from ...database.connection import get_db_session
            
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            logger.info(f"Logout-all request from user {email} (ID: {user_id})")
            
            # Инициализируем AuthService
            db_session = get_db_session()
            email_service = EmailService()
            auth_service = AuthService(db_session, current_app.config['SECRET_KEY'], email_service)
            
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
    @auth_ns.marshal_with(user_model, code=200, description='Информация о пользователе')
    @auth_ns.marshal_with(common_models['error'], code=401, description='Не авторизован')
    @auth_ns.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def get(self, current_user):
        """Получить информацию о текущем пользователе"""
        try:
            # current_user уже проверен в jwt_required
            user_id = current_user.get('user_id')
            email = current_user.get('email')
            
            # Получить данные пользователя через AuthService
            auth_service = get_auth_service()
            user = auth_service.get_user_by_email(email)
            
            # Возвращаем информацию о пользователе
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "is_verified": user.is_verified,
                        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                        "created_at": user.created_at.isoformat() if user.created_at else "",
                        "updated_at": user.updated_at.isoformat() if user.updated_at else ""
                    },
                    "usage_stats": {
                        "posts_used": 0,
                        "posts_limit": 50,
                        "api_calls_used": 0,
                        "api_calls_limit": 1000
                    }
                }, 200
            else:
                return {
                    "error": "User not found",
                    "message": "Пользователь не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }, 404
                
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}")
            return {
                "error": "Internal server error",
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
            success, message = auth_service.update_user_profile(
                email=email,
                **data
            )
            
            if success:
                # Получаем обновленного пользователя
                user = auth_service.get_user_by_email(email)
                
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
                email=email,
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
            from ...billing.models.subscription import get_all_plans
            
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
            from ...billing.models.subscription import get_plan_by_id
            
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
            from ...billing.models.subscription import get_plan_by_id
            from ...billing.services.yookassa_service import YooKassaService, PaymentRequest
            
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
            from ...billing.services.yookassa_service import YooKassaService
            
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