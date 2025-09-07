#!/usr/bin/env python3
"""
AI Content Orchestrator - Flask Application
Главное приложение для API управления AI агентами контента
"""

import os
import asyncio
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем наши модули
from app.orchestrator.main_orchestrator import orchestrator
from app.agents.chief_agent import ChiefContentAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.publisher_agent import PublisherAgent
from app.agents.research_factcheck_agent import ResearchFactCheckAgent
from app.agents.trends_scout_agent import TrendsScoutAgent
from app.agents.multimedia_producer_agent import MultimediaProducerAgent
from app.agents.legal_guard_agent import LegalGuardAgent
from app.api.schemas import (
    ContentRequestSchema, 
    ContentResponseSchema,
    WorkflowStatusSchema,
    AgentStatusSchema,
    ErrorResponseSchema
)
from app.api.routes import api_bp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Создает и настраивает Flask приложение"""
    app = Flask(__name__)
    
    # Конфигурация
    app.config.update({
        'SECRET_KEY': os.getenv('APP_SECRET_KEY', 'dev-secret-key'),
        'DEBUG': os.getenv('DEBUG_MODE', 'False').lower() == 'true',
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True
    })
    
    # CORS для фронтенда
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    # Регистрируем API blueprint
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Глобальные обработчики ошибок
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'Некорректные данные запроса',
            'status_code': 400,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Ресурс не найден',
            'status_code': 404,
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Внутренняя ошибка сервера',
            'status_code': 500,
            'timestamp': datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Произошла неожиданная ошибка',
            'status_code': 500,
            'timestamp': datetime.now().isoformat()
        }), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Проверка состояния приложения"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'service': 'AI Content Orchestrator'
        })
    
    # Root endpoint
    @app.route('/')
    def root():
        """Корневой endpoint с информацией о API"""
        return jsonify({
            'service': 'AI Content Orchestrator',
            'version': '1.0.0',
            'description': 'API для управления AI агентами создания контента',
            'endpoints': {
                'health': '/health',
                'api_docs': '/api/v1/docs',
                'create_content': '/api/v1/content/create',
                'workflow_status': '/api/v1/workflow/<workflow_id>/status',
                'agents_status': '/api/v1/agents/status',
                'system_status': '/api/v1/system/status'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    return app

async def initialize_orchestrator():
    """Инициализирует оркестратор и регистрирует агентов"""
    try:
        logger.info("Инициализация оркестратора...")
        
        # Создаем агентов
        chief_agent = ChiefContentAgent("chief_001")
        drafting_agent = DraftingAgent("drafting_001")
        publisher_agent = PublisherAgent("publisher_001")
        factcheck_agent = ResearchFactCheckAgent("research_factcheck_agent")
        trends_scout_agent = TrendsScoutAgent("trends_scout_001")
        multimedia_agent = MultimediaProducerAgent("multimedia_producer_001")
        legal_agent = LegalGuardAgent("legal_guard_001")
        
        # Регистрируем агентов
        orchestrator.register_agent(chief_agent)
        orchestrator.register_agent(drafting_agent)
        orchestrator.register_agent(publisher_agent)
        orchestrator.register_agent(factcheck_agent)
        orchestrator.register_agent(trends_scout_agent)
        orchestrator.register_agent(multimedia_agent)
        orchestrator.register_agent(legal_agent)
        
        # Запускаем оркестратор
        await orchestrator.start()
        
        logger.info("Оркестратор успешно инициализирован")
        logger.info(f"Зарегистрировано агентов: {len(orchestrator.agent_manager.agents)}")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации оркестратора: {e}")
        raise

def run_initialization():
    """Запускает инициализацию в отдельном потоке"""
    try:
        # Создаем новый event loop для инициализации
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_orchestrator())
    except Exception as e:
        logger.error(f"Ошибка при запуске инициализации: {e}")

# Создаем приложение
app = create_app()

# Инициализируем оркестратор при запуске
if __name__ == '__main__':
    # Запускаем инициализацию
    run_initialization()
    
    # Запускаем Flask приложение
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    logger.info(f"Запуск Flask приложения на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # Для production (gunicorn)
    run_initialization()
