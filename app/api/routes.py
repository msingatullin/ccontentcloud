"""
API Routes для AI Content Orchestrator
RESTful endpoints для работы с контентом и агентами
Интегрировано с Flask-RESTX для Swagger UI
"""

import asyncio
import logging
from datetime import datetime
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

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

# Создаем namespace для API
api = Namespace('api', description='AI Content Orchestrator API')

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
    @api.doc('create_content', description='Создает контент через AI агентов')
    @api.expect(content_request_model, validate=True)
    @api.marshal_with(content_response_model, code=201, description='Контент успешно создан')
    @api.marshal_with(common_models['error'], code=400, description='Ошибка валидации')
    @api.marshal_with(common_models['error'], code=500, description='Внутренняя ошибка сервера')
    def post(self):
        """
        Создает контент через AI агентов
        
        Принимает запрос на создание контента и запускает workflow
        с участием всех необходимых агентов.
        """
        try:
            # Валидируем входные данные
            try:
                content_request = ContentRequestSchema(**request.json)
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