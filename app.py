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
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем наши модули
from app.orchestrator.main_orchestrator import orchestrator  # Singleton для старых эндпоинтов
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
from app.routes.telegram_channels import bp as telegram_channels_bp
from app.routes.instagram_accounts import bp as instagram_accounts_bp
from app.routes.twitter_accounts import bp as twitter_accounts_bp
from app.routes.social_media_accounts import bp as social_media_accounts_bp
# from app.auth.routes.auth import init_auth_routes, auth_bp  # Не используем Flask Blueprint
from app.auth.models.user import User, UserSession
from app.database.connection import init_database, get_db_session
from app.api.schemas import (
    ContentRequestSchema, 
    ContentResponseSchema,
    WorkflowStatusSchema,
    AgentStatusSchema,
    ErrorResponseSchema
)
from app.api.routes import api, auth_ns, billing_ns, webhook_ns, health_ns, ai_ns
from app.api.social_media_ns import social_media_ns
from app.api.telegram_ns import telegram_ns
from app.api.instagram_ns import instagram_ns
from app.api.twitter_ns import twitter_ns
from app.api.scheduled_posts_ns import scheduled_posts_ns
from app.api.auto_posting_ns import auto_posting_ns
from app.api.projects_ns import projects_ns
from app.api.routes import content_sources_ns
from app.api.swagger_config import create_swagger_api
from app.workers import ScheduledPostsWorker, AutoPostingWorker
from app.workers.web_crawler_worker import WebCrawlerWorker

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
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        # Flask-JWT-Extended конфигурация
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', os.getenv('APP_SECRET_KEY', 'dev-secret-key')),
        'JWT_TOKEN_LOCATION': ['headers'],
        'JWT_HEADER_NAME': 'Authorization',
        'JWT_HEADER_TYPE': 'Bearer',
        'JWT_ALGORITHM': 'HS256',
        'JWT_IDENTITY_CLAIM': 'user_id'
    })
    
    # Инициализируем JWT Manager
    jwt_manager = JWTManager(app)
    
    # Настраиваем identity loader для совместимости с нашей JWT системой
    @jwt_manager.user_identity_loader
    def user_identity_lookup(user):
        """Извлекаем identity из токена"""
        return user
    
    @jwt_manager.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Загружаем пользователя по данным из токена"""
        # Наша JWT система сохраняет user_id в payload
        return jwt_data.get('user_id')
    
    # Обработчики ошибок JWT
    @jwt_manager.unauthorized_loader
    def unauthorized_callback(error):
        """Обработчик отсутствия токена"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Требуется авторизация. Используйте кнопку Authorize в Swagger UI',
            'details': str(error)
        }), 401
    
    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        """Обработчик невалидного токена"""
        return jsonify({
            'error': 'Invalid token',
            'message': 'Недействительный токен авторизации',
            'details': str(error)
        }), 401
    
    @jwt_manager.expired_token_loader
    def expired_token_callback(_jwt_header, jwt_data):
        """Обработчик истекшего токена"""
        return jsonify({
            'error': 'Token expired',
            'message': 'Токен авторизации истек. Пожалуйста, войдите снова'
        }), 401
    
    # CORS для фронтенда
    # Swagger UI работает на том же домене (same-origin) и не требует CORS
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",  # для локальной разработки
                "https://content4u.ai",
                "https://www.content4u.ai",
                "https://goinvesting.ai",  # старый домен для совместимости
                "https://www.goinvesting.ai",
                "https://content-curator-frontend-dt3n7kzpwq-uc.a.run.app",
                "https://content-curator-frontend-1046574462613.us-central1.run.app",
                "https://content-curator-dt3n7kzpwq-uc.a.run.app",
                "https://content-curator-web-1046574462613.europe-west1.run.app"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Глобальный обработчик OPTIONS запросов для CORS preflight
    # Обрабатываем до того, как запрос попадет в Flask-RESTX или JWT middleware
    @app.before_request
    def handle_preflight():
        """Обработка CORS preflight (OPTIONS) запросов"""
        if request.method == "OPTIONS":
            # Получаем Origin из запроса
            origin = request.headers.get('Origin', '*')
            
            # Проверяем, разрешен ли этот origin
            allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "https://content4u.ai",
                "https://www.content4u.ai",
                "https://goinvesting.ai",
                "https://www.goinvesting.ai",
                "https://content-curator-frontend-dt3n7zpq-uc.a.run.app",
                "https://content-curator-frontend-1046574462613.us-central1.run.app",
                "https://content-curator-dt3n7zpq-uc.a.run.app",
                "https://content-curator-web-1046574462613.europe-west1.run.app"
            ]
            
            # Используем origin из запроса, если он разрешен, иначе используем первый разрешенный
            if origin in allowed_origins:
                response_origin = origin
            else:
                # Для локальной разработки разрешаем любой origin
                response_origin = origin if origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1') else allowed_origins[0]
            
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", response_origin)
            response.headers.add('Access-Control-Allow-Headers', request.headers.get('Access-Control-Request-Headers', 'Content-Type, Authorization'))
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '3600')
            return response
    
    # Инициализируем базу данных
    logger.info("Initializing database...")
    if not init_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    # Получаем сессию базы данных
    db_session = get_db_session()
    
    # Auth система инициализируется через Flask-RESTX endpoints

    # Создаем и регистрируем Flask-RESTX API с Swagger
    swagger_api = create_swagger_api(app)
    swagger_api.add_namespace(api)
    swagger_api.add_namespace(auth_ns)
    swagger_api.add_namespace(billing_ns)
    swagger_api.add_namespace(webhook_ns)
    swagger_api.add_namespace(health_ns)
    swagger_api.add_namespace(social_media_ns)
    swagger_api.add_namespace(telegram_ns)
    swagger_api.add_namespace(instagram_ns)
    swagger_api.add_namespace(twitter_ns)
    swagger_api.add_namespace(scheduled_posts_ns, path='/scheduled-posts')
    swagger_api.add_namespace(auto_posting_ns, path='/auto-posting')
    swagger_api.add_namespace(content_sources_ns, path='/content-sources')
    swagger_api.add_namespace(projects_ns, path='/projects')
    swagger_api.add_namespace(ai_ns, path='/ai')
    
    # Регистрируем swagger_api в Flask app
    # swagger_api уже зарегистрирован в Flask app через create_swagger_api(app)
    
    # Регистрируем остальные blueprints
    app.register_blueprint(billing_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(telegram_channels_bp)
    app.register_blueprint(instagram_accounts_bp)
    app.register_blueprint(twitter_accounts_bp)
    app.register_blueprint(social_media_accounts_bp)
    # auth_bp не регистрируем - используем Flask-RESTX endpoints

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
        
        # Запускаем фоновую задачу очистки неактивных оркестраторов
        from app.orchestrator.user_orchestrator_factory import orchestrator_cleanup_task
        logger.info("Запуск фоновой задачи очистки оркестраторов...")
        loop.create_task(orchestrator_cleanup_task())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске инициализации: {e}")

# Feature flag для отключения агентов в тестовом режиме
DISABLE_AGENTS = os.getenv('DISABLE_AGENTS', 'false').lower() == 'true'

# Feature flag для отключения workers в тестовом режиме
DISABLE_WORKERS = os.getenv('DISABLE_WORKERS', 'false').lower() == 'true'

# Глобальные workers
scheduled_posts_worker = None
auto_posting_worker = None
web_crawler_worker = None

def start_workers():
    """Запуск background workers"""
    global scheduled_posts_worker, auto_posting_worker, web_crawler_worker
    
    if DISABLE_WORKERS:
        logger.warning("⚠️ WORKERS DISABLED: Background workers отключены (DISABLE_WORKERS=true)")
        return
    
    try:
        logger.info("Запуск background workers...")
        
        # Scheduled Posts Worker - проверяет каждую минуту
        scheduled_posts_worker = ScheduledPostsWorker(check_interval=60)
        scheduled_posts_worker.start()
        logger.info("✅ ScheduledPostsWorker запущен (интервал: 60s)")
        
        # Auto Posting Worker - проверяет каждые 5 минут
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
        auto_posting_worker = AutoPostingWorker(check_interval=300, api_base_url=api_base_url)
        auto_posting_worker.start()
        logger.info("✅ AutoPostingWorker запущен (интервал: 300s)")
        
        # Web Crawler Worker - проверяет каждую минуту
        web_crawler_worker = WebCrawlerWorker(check_interval=60)
        web_crawler_worker.start()
        logger.info("✅ WebCrawlerWorker запущен (интервал: 60s)")
        
        logger.info("🚀 Все background workers успешно запущены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска workers: {e}", exc_info=True)

# Создаем приложение
app = create_app()

# Инициализируем оркестратор при запуске
if __name__ == '__main__':
    # Инициализируем базу данных
    logger.info("🔧 Initializing database...")
    from app.database.connection import init_database
    init_database()
    logger.info("✅ Database initialized")
    
    # Запускаем инициализацию агентов (если не отключено)
    if not DISABLE_AGENTS:
        logger.info("Инициализация агентов включена")
        run_initialization()
    else:
        logger.warning("⚠️ AGENTS DISABLED: Система работает БЕЗ агентов (DISABLE_AGENTS=true)")
    
    # Запускаем background workers
    start_workers()
    
    # Запускаем Flask приложение
    port = int(os.environ.get('PORT', 8080))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    logger.info(f"Запуск Flask приложения на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # Для production (gunicorn)
    logger.info("🔧 Initializing database (production mode)...")
    from app.database.connection import init_database
    init_database()
    logger.info("✅ Database initialized")
    
    if not DISABLE_AGENTS:
        logger.info("Инициализация агентов включена (production mode)")
        run_initialization()
    else:
        logger.warning("⚠️ AGENTS DISABLED: Система работает БЕЗ агентов (DISABLE_AGENTS=true)")
    
    # Запускаем background workers
    start_workers()
