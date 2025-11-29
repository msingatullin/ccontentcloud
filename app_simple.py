#!/usr/bin/env python3
"""
AI Content Orchestrator - Упрощенная версия для быстрого запуска
Flask приложение с отложенной инициализацией агентов
"""

import os
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для состояния
orchestrator_initialized = False
initialization_error = None
agents_count = 0

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
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://localhost:5173',  # для локальной разработки
                'https://content4u.ai',
                'https://www.content4u.ai',
                'https://goinvesting.ai',  # старый домен для совместимости
                'https://content-curator-frontend-dt3n7kzpwq-uc.a.run.app',
                'https://content-curator-web-1046574462613.europe-west1.run.app'  # новый production frontend
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Health check endpoint - отвечает сразу
    @app.route('/health')
    def health_check():
        """Проверка состояния приложения"""
        global orchestrator_initialized, initialization_error, agents_count
        
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'service': 'AI Content Orchestrator',
            'orchestrator_initialized': orchestrator_initialized,
            'agents_count': agents_count
        }
        
        if initialization_error:
            status['initialization_error'] = str(initialization_error)
            status['status'] = 'degraded'
        
        return jsonify(status)
    
    # Root endpoint
    @app.route('/')
    def root():
        """Корневой endpoint с информацией о API"""
        return jsonify({
            'service': 'AI Content Orchestrator',
            'version': '1.0.0',
            'description': 'API для управления AI агентами создания контента',
            'status': 'running',
            'orchestrator_initialized': orchestrator_initialized,
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
    
    # Простой API endpoint для агентов
    @app.route('/api/v1/agents/status')
    def agents_status():
        """Статус агентов"""
        global orchestrator_initialized, agents_count
        
        if not orchestrator_initialized:
            return jsonify({
                'status': 'initializing',
                'message': 'Оркестратор инициализируется в фоновом режиме',
                'agents_count': 0,
                'timestamp': datetime.now().isoformat()
            }), 202
        
        return jsonify({
            'status': 'ready',
            'agents_count': agents_count,
            'agents': [
                {'id': 'chief_001', 'name': 'Chief Content Agent', 'status': 'ready'},
                {'id': 'drafting_001', 'name': 'Drafting Agent', 'status': 'ready'},
                {'id': 'publisher_001', 'name': 'Publisher Agent', 'status': 'ready'},
                {'id': 'research_factcheck_agent', 'name': 'Research FactCheck Agent', 'status': 'ready'},
                {'id': 'trends_scout_001', 'name': 'Trends Scout Agent', 'status': 'ready'},
                {'id': 'multimedia_producer_001', 'name': 'Multimedia Producer Agent', 'status': 'ready'},
                {'id': 'legal_guard_001', 'name': 'Legal Guard Agent', 'status': 'ready'},
                {'id': 'repurpose_001', 'name': 'Repurpose Agent', 'status': 'ready'},
                {'id': 'community_concierge_001', 'name': 'Community Concierge Agent', 'status': 'ready'},
                {'id': 'paid_creative_001', 'name': 'Paid Creative Agent', 'status': 'ready'}
            ],
            'timestamp': datetime.now().isoformat()
        })
    
    # Простой endpoint для создания контента
    @app.route('/api/v1/content/create', methods=['POST'])
    def create_content():
        """Создание контента"""
        global orchestrator_initialized
        
        if not orchestrator_initialized:
            return jsonify({
                'error': 'Service not ready',
                'message': 'Оркестратор еще инициализируется. Попробуйте через несколько секунд.',
                'status': 'initializing'
            }), 503
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Требуется JSON данные'
                }), 400
            
            # Простая обработка запроса
            content_type = data.get('content_type', 'post')
            topic = data.get('topic', 'Общая тема')
            
            return jsonify({
                'status': 'success',
                'message': f'Контент типа "{content_type}" по теме "{topic}" будет создан',
                'workflow_id': f'workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Ошибка создания контента: {e}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'Ошибка при создании контента'
            }), 500
    
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
    
    return app

def background_initialization():
    """Фоновая инициализация оркестратора"""
    global orchestrator_initialized, initialization_error, agents_count
    
    try:
        logger.info("Начинаем фоновую инициализацию оркестратора...")
        
        # Импортируем модули только когда нужно
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
        from app.database.connection import init_database
        import asyncio
        
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        init_database()
        logger.info("База данных инициализирована")
        
        # Создаем агентов
        logger.info("Создание агентов...")
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
        
        agents_count = 10
        
        # Запускаем оркестратор
        logger.info("Запуск оркестратора...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(orchestrator.start())
        
        orchestrator_initialized = True
        logger.info("Оркестратор успешно инициализирован в фоновом режиме")
        logger.info(f"Зарегистрировано агентов: {agents_count}")
        
    except Exception as e:
        logger.error(f"Ошибка фоновой инициализации оркестратора: {e}")
        initialization_error = e
        orchestrator_initialized = False

# Создаем приложение
app = create_app()

# Запускаем фоновую инициализацию
if __name__ == '__main__':
    # Запускаем инициализацию в отдельном потоке
    init_thread = threading.Thread(target=background_initialization, daemon=True)
    init_thread.start()
    
    # Запускаем Flask приложение
    port = int(os.environ.get('PORT', 8080))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    logger.info(f"Запуск Flask приложения на порту {port}")
    logger.info("Оркестратор инициализируется в фоновом режиме...")
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # Для production (gunicorn)
    init_thread = threading.Thread(target=background_initialization, daemon=True)
    init_thread.start()
