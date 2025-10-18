#!/usr/bin/env python3
"""
AI Content Orchestrator - Simplified Fixed Application
Упрощенная версия приложения для исправления проблем с запуском
"""

import os
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
    
    # CORS для фронтенда - разрешаем все необходимые домены
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://localhost:5173',  # для локальной разработки
                'https://content4u.ai',
                'https://www.content4u.ai',
                'https://goinvesting.ai',  # старый домен для совместимости
                'https://www.goinvesting.ai',
                'https://content-curator-frontend-dt3n7kzpwq-uc.a.run.app',
                'https://content-curator-frontend-1046574462613.us-central1.run.app',
                'https://content-curator-dt3n7kzpwq-uc.a.run.app',
                'https://content-curator-web-1046574462613.europe-west1.run.app'  # новый production frontend
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Базовые endpoints
    @app.route('/')
    def home():
        return jsonify({
            'message': 'AI Content Orchestrator API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'port': os.environ.get('PORT', '8080')
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    # API endpoints
    @app.route('/api/v1/agents/status', methods=['GET'])
    def agents_status():
        """Статус AI агентов"""
        try:
            # Имитируем статус агентов
            agents = {
                "chief_001": "Chief Content Agent - idle",
                "community_concierge_001": "Community Concierge Agent - idle",
                "drafting_001": "Drafting Agent - idle",
                "legal_guard_001": "Legal Guard Agent - idle",
                "multimedia_producer_001": "Multimedia Producer Agent - idle",
                "paid_creative_001": "Paid Creative Agent - idle",
                "publisher_001": "Publisher Agent - idle",
                "repurpose_001": "Repurpose Agent - idle",
                "research_factcheck_agent": "Research & FactCheck Agent - idle",
                "trends_scout_001": "Trends Scout Agent - idle"
            }
            
            return jsonify({
                'status': 'success',
                'agents': agents,
                'total_agents': len(agents),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting agents status: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/v1/billing/plans', methods=['GET'])
    def billing_plans():
        """Тарифные планы"""
        try:
            plans = [
                {
                    "id": "free",
                    "name": "Free",
                    "description": "Базовый план для начала работы",
                    "price_monthly": 0,
                    "price_yearly": 0,
                    "limits": {
                        "posts_per_month": 50,
                        "max_agents": 3,
                        "platforms": ["telegram"],
                        "api_calls_per_day": 100,
                        "storage_gb": 1,
                        "support_level": "community"
                    },
                    "features": ["Базовые AI агенты", "Telegram публикация", "Сообщество поддержка"],
                    "is_popular": False,
                    "trial_days": 7
                },
                {
                    "id": "pro",
                    "name": "Pro",
                    "description": "Профессиональный план для бизнеса",
                    "price_monthly": 2990,
                    "price_yearly": 29900,
                    "limits": {
                        "posts_per_month": 500,
                        "max_agents": 10,
                        "platforms": ["telegram", "vk", "youtube"],
                        "api_calls_per_day": 1000,
                        "storage_gb": 10,
                        "support_level": "priority"
                    },
                    "features": ["Все AI агенты", "Мультиплатформенная публикация", "Приоритетная поддержка", "API доступ"],
                    "is_popular": True,
                    "trial_days": 7
                },
                {
                    "id": "enterprise",
                    "name": "Enterprise",
                    "description": "Корпоративный план без ограничений",
                    "price_monthly": 9990,
                    "price_yearly": 99900,
                    "limits": {
                        "posts_per_month": -1,
                        "max_agents": -1,
                        "platforms": ["telegram", "vk", "youtube", "instagram", "facebook"],
                        "api_calls_per_day": -1,
                        "storage_gb": 100,
                        "support_level": "dedicated"
                    },
                    "features": ["Безлимитные возможности", "Все платформы", "Выделенная поддержка", "Кастомные интеграции"],
                    "is_popular": False,
                    "trial_days": 14
                }
            ]
            
            return jsonify({
                'status': 'success',
                'plans': plans,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting billing plans: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/v1/auth/register', methods=['POST'])
    def auth_register():
        """Регистрация пользователя"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            # Простая валидация
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({
                    'status': 'error',
                    'message': 'Email and password are required',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            # Имитируем успешную регистрацию
            return jsonify({
                'status': 'success',
                'message': 'User registered successfully',
                'user': {
                    'id': 'user_123',
                    'email': email,
                    'created_at': datetime.now().isoformat()
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in registration: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Endpoint not found',
            'status_code': 404,
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal error occurred',
            'status_code': 500,
            'timestamp': datetime.now().isoformat()
        }), 500
    
    logger.info("AI Content Orchestrator application created successfully")
    return app

# Создаем приложение
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('API_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting AI Content Orchestrator on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
