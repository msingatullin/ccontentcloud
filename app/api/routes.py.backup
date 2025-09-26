"""
API Routes для AI Content Orchestrator
RESTful endpoints для работы с контентом и агентами
"""

import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
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

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем Blueprint для API
api_bp = Blueprint('api', __name__)


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
    
    return jsonify({
        "error": "Validation Error",
        "message": "Некорректные данные запроса",
        "status_code": 400,
        "timestamp": datetime.now().isoformat(),
        "details": errors
    }), 400


def handle_exception(e: Exception) -> tuple:
    """Обрабатывает общие исключения"""
    logger.error(f"API Error: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "Произошла внутренняя ошибка сервера",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }), 500


# ==================== CONTENT ENDPOINTS ====================

@api_bp.route('/content/create', methods=['POST'])
def create_content():
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
            
            return jsonify(response_data), 201
        else:
            logger.error(f"Ошибка создания контента: {result['error']}")
            return jsonify({
                "error": "Content Creation Failed",
                "message": result["error"],
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/content/example', methods=['GET'])
def get_content_example():
    """
    Возвращает пример запроса на создание контента
    """
    return jsonify({
        "description": "Пример запроса на создание контента",
        "example": ExampleData.CONTENT_REQUEST_EXAMPLE,
        "schema": "ContentRequestSchema"
    })


# ==================== WORKFLOW ENDPOINTS ====================

@api_bp.route('/workflow/<workflow_id>/status', methods=['GET'])
def get_workflow_status(workflow_id: str):
    """
    Получает статус workflow по ID
    """
    try:
        logger.info(f"Запрос статуса workflow: {workflow_id}")
        
        # Получаем статус workflow
        status = orchestrator.get_workflow_status(workflow_id)
        
        if status:
            return jsonify(status), 200
        else:
            return jsonify({
                "error": "Workflow Not Found",
                "message": f"Workflow с ID {workflow_id} не найден",
                "status_code": 404,
                "timestamp": datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/workflow/<workflow_id>/cancel', methods=['POST'])
def cancel_workflow(workflow_id: str):
    """
    Отменяет выполнение workflow
    """
    try:
        logger.info(f"Запрос на отмену workflow: {workflow_id}")
        
        # В реальной реализации здесь была бы логика отмены workflow
        # Пока возвращаем заглушку
        return jsonify({
            "message": f"Workflow {workflow_id} отменен",
            "workflow_id": workflow_id,
            "status": "cancelled",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return handle_exception(e)


# ==================== AGENT ENDPOINTS ====================

@api_bp.route('/agents/status', methods=['GET'])
def get_agents_status():
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
                return jsonify(status), 200
            else:
                return jsonify({
                    "error": "Agent Not Found",
                    "message": f"Агент с ID {agent_id} не найден",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }), 404
        else:
            # Статус всех агентов
            logger.info("Запрос статуса всех агентов")
            status = orchestrator.get_all_agents_status()
            return jsonify(status), 200
            
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/agents/<agent_id>/tasks', methods=['GET'])
def get_agent_tasks(agent_id: str):
    """
    Получает список задач конкретного агента
    """
    try:
        logger.info(f"Запрос задач агента: {agent_id}")
        
        # Получаем статус агента
        agent_status = orchestrator.get_agent_status(agent_id)
        
        if not agent_status:
            return jsonify({
                "error": "Agent Not Found",
                "message": f"Агент с ID {agent_id} не найден",
                "status_code": 404,
                "timestamp": datetime.now().isoformat()
            }), 404
        
        # Формируем ответ с задачами
        response = {
            "agent_id": agent_id,
            "agent_name": agent_status["name"],
            "current_tasks": agent_status["current_tasks"],
            "completed_tasks": agent_status["completed_tasks"],
            "status": agent_status["status"],
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return handle_exception(e)


# ==================== SYSTEM ENDPOINTS ====================

@api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    Получает общий статус системы
    """
    try:
        logger.info("Запрос статуса системы")
        
        status = orchestrator.get_system_status()
        return jsonify(status), 200
        
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/system/health', methods=['GET'])
def get_system_health():
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
        return jsonify(response), status_code
        
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/system/metrics', methods=['GET'])
def get_system_metrics():
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
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return handle_exception(e)


# ==================== PLATFORM ENDPOINTS ====================

@api_bp.route('/platforms', methods=['GET'])
def get_platforms():
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
        
        return jsonify({
            "platforms": platform_stats,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return handle_exception(e)


@api_bp.route('/platforms/<platform>/config', methods=['GET'])
def get_platform_config(platform: str):
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
                return jsonify({
                    "platform": platform,
                    "config": platform_stats[platform],
                    "timestamp": datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    "error": "Platform Not Found",
                    "message": f"Платформа {platform} не поддерживается",
                    "status_code": 404,
                    "timestamp": datetime.now().isoformat()
                }), 404
        else:
            return jsonify({
                "error": "Service Unavailable",
                "message": "Сервис платформ недоступен",
                "status_code": 503,
                "timestamp": datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        return handle_exception(e)


# ==================== TRENDS ANALYSIS ENDPOINTS ====================

@api_bp.route('/trends/analyze', methods=['POST'])
def analyze_trends():
    """Анализ трендов через TrendsScoutAgent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponseSchema(
                error="Invalid request",
                message="Требуется JSON данные",
                timestamp=datetime.now().isoformat()
            ).dict()), 400
        
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
            return jsonify(ErrorResponseSchema(
                error="Agent not available",
                message="TrendsScoutAgent недоступен",
                timestamp=datetime.now().isoformat()
            ).dict()), 503
        
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
            return jsonify({
                'status': 'success',
                'task_id': result['task_id'],
                'agent_id': result['agent_id'],
                'analysis_result': result['result'],
                'execution_time': result['execution_time']
            })
        else:
            return jsonify(ErrorResponseSchema(
                error="Analysis failed",
                message=f"Ошибка анализа трендов: {result.get('error', 'Unknown error')}",
                timestamp=datetime.now().isoformat()
            ).dict()), 500
        
    except Exception as e:
        logger.error(f"Ошибка анализа трендов: {e}")
        return jsonify(ErrorResponseSchema(
            error="Internal server error",
            message=f"Ошибка анализа трендов: {str(e)}",
            timestamp=datetime.now().isoformat()
        ).dict()), 500


@api_bp.route('/trends/viral', methods=['GET'])
def get_viral_trends():
    """Получает вирусные тренды"""
    try:
        # Находим TrendsScoutAgent
        trends_agent = None
        for agent in orchestrator.agent_manager.agents.values():
            if hasattr(agent, 'trend_analyzer'):
                trends_agent = agent
                break
        
        if not trends_agent:
            return jsonify(ErrorResponseSchema(
                error="Agent not available",
                message="TrendsScoutAgent недоступен",
                timestamp=datetime.now().isoformat()
            ).dict()), 503
        
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
            return jsonify({
                'status': 'success',
                'viral_trends': result['result'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify(ErrorResponseSchema(
                error="Analysis failed",
                message=f"Ошибка получения вирусных трендов: {result.get('error', 'Unknown error')}",
                timestamp=datetime.now().isoformat()
            ).dict()), 500
        
    except Exception as e:
        logger.error(f"Ошибка получения вирусных трендов: {e}")
        return jsonify(ErrorResponseSchema(
            error="Internal server error",
            message=f"Ошибка получения вирусных трендов: {str(e)}",
            timestamp=datetime.now().isoformat()
        ).dict()), 500


# ==================== DOCUMENTATION ENDPOINTS ====================

@api_bp.route('/docs', methods=['GET'])
def get_api_docs():
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
            "content_request": ExampleData.CONTENT_REQUEST_EXAMPLE,
            "content_response": ExampleData.CONTENT_RESPONSE_EXAMPLE,
            "error_response": ExampleData.ERROR_RESPONSE_EXAMPLE
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(docs), 200


@api_bp.route('/docs/schemas', methods=['GET'])
def get_schemas():
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
        
        return jsonify(schemas), 200
        
    except Exception as e:
        return handle_exception(e)


# ==================== ERROR HANDLERS ====================

@api_bp.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибок для API"""
    return jsonify({
        "error": "Not Found",
        "message": "API endpoint не найден",
        "status_code": 404,
        "timestamp": datetime.now().isoformat()
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Обработчик 405 ошибок для API"""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "HTTP метод не поддерживается для данного endpoint",
        "status_code": 405,
        "timestamp": datetime.now().isoformat()
    }), 405


@api_bp.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибок для API"""
    logger.error(f"API Internal Error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "Внутренняя ошибка API",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }), 500
