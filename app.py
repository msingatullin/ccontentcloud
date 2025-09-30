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
from app.agents.repurpose_agent import RepurposeAgent
from app.agents.community_concierge_agent import CommunityConciergeAgent
from app.agents.paid_creative_agent import PaidCreativeAgent
from app.billing.api.billing_routes import billing_bp
from app.billing.webhooks.yookassa_webhook import webhook_bp
from app.billing.middleware.usage_middleware import UsageMiddleware
from app.auth.routes.auth import init_auth_routes
from app.auth.models.user import User, UserSession
from app.database.connection import init_database, get_db_session
from app.api.schemas import (
    ContentRequestSchema, 
    ContentResponseSchema,
    WorkflowStatusSchema,
    AgentStatusSchema,
    ErrorResponseSchema
)
from app.api.routes import api, auth_ns, billing_ns, webhook_ns, health_ns
from app.api.swagger_config import create_swagger_api

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
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",  # для локальной разработки
                "https://goinvesting.ai",
                "https://content-curator-frontend-dt3n7kzpwq-uc.a.run.app",
                "https://content-curator-web-1046574462613.europe-west1.run.app"  # новый production frontend
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Инициализируем базу данных
    logger.info("Initializing database...")
    if not init_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    # Получаем сессию базы данных
    db_session = get_db_session()
    
    # Инициализируем auth систему
    auth_bp, jwt_middleware = init_auth_routes(db_session, app.config['SECRET_KEY'])

    # Создаем и регистрируем Flask-RESTX API с Swagger
    swagger_api = create_swagger_api(app)
    swagger_api.add_namespace(api)
    swagger_api.add_namespace(auth_ns)
    swagger_api.add_namespace(billing_ns)
    swagger_api.add_namespace(webhook_ns)
    swagger_api.add_namespace(health_ns)
    
    # Регистрируем остальные blueprints
    app.register_blueprint(billing_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(auth_bp)

    # Инициализируем billing middleware
    billing_middleware = UsageMiddleware(app)
    
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
    
    # Root endpoint теперь обрабатывается Flask-RESTX
    # Удален во избежание конфликта с Flask-RESTX
    
    return app

async def initialize_orchestrator():
    """Инициализирует оркестратор и регистрирует агентов"""
    try:
        logger.info("Инициализация базы данных...")
        
        # Инициализируем базу данных
        init_database()
        logger.info("База данных инициализирована")
        
        logger.info("Инициализация оркестратора...")
        
        # Создаем агентов
        chief_agent = ChiefContentAgent("chief_001")
        drafting_agent = DraftingAgent("drafting_001")
        publisher_agent = PublisherAgent("publisher_001")
        factcheck_agent = ResearchFactCheckAgent("research_factcheck_agent")
        trends_scout_agent = TrendsScoutAgent("trends_scout_001")
        multimedia_agent = MultimediaProducerAgent("multimedia_producer_001")
        legal_agent = LegalGuardAgent("legal_guard_001")
        repurpose_agent = RepurposeAgent("repurpose_001")
        community_agent = CommunityConciergeAgent("community_concierge_001")
        paid_creative_agent = PaidCreativeAgent("paid_creative_001")
        
        # Регистрируем агентов
        orchestrator.register_agent(chief_agent)
        orchestrator.register_agent(drafting_agent)
        orchestrator.register_agent(publisher_agent)
        orchestrator.register_agent(factcheck_agent)
        orchestrator.register_agent(trends_scout_agent)
        orchestrator.register_agent(multimedia_agent)
        orchestrator.register_agent(legal_agent)
        orchestrator.register_agent(repurpose_agent)
        orchestrator.register_agent(community_agent)
        orchestrator.register_agent(paid_creative_agent)
        
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
    port = int(os.environ.get('PORT', 8080))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    logger.info(f"Запуск Flask приложения на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # Для production (gunicorn)
    run_initialization()
