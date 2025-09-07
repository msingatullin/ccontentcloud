"""
Middleware для проверки лимитов использования
"""

import logging
from functools import wraps
from typing import Callable, Optional, Dict, Any

from flask import request, jsonify, g

from app.billing.services.subscription_service import SubscriptionService
from app.billing.models.subscription import get_plan_by_id

logger = logging.getLogger(__name__)


def check_usage_limit(
    resource_type: str,
    quantity: int = 1,
    required_plan: Optional[str] = None
):
    """
    Декоратор для проверки лимитов использования
    
    Args:
        resource_type: Тип ресурса (posts, api_calls, agents, storage)
        quantity: Количество ресурса
        required_plan: Требуемый план (если None, проверяется текущий план)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Получаем ID пользователя из заголовков
                user_id = request.headers.get('X-User-ID')
                if not user_id:
                    return jsonify({
                        "success": False,
                        "error": "Не указан ID пользователя"
                    }), 401
                
                # TODO: Получить сессию БД из контекста приложения
                # db_session = g.db_session
                # subscription_service = SubscriptionService(db_session)
                
                # Получаем подписку пользователя
                # subscription = subscription_service.get_user_subscription(user_id)
                # if not subscription:
                #     return jsonify({
                #         "success": False,
                #         "error": "У пользователя нет активной подписки"
                #     }), 403
                
                # Получаем план
                # plan = get_plan_by_id(subscription.plan_id)
                # if not plan:
                #     return jsonify({
                #         "success": False,
                #         "error": "План подписки не найден"
                #     }), 500
                
                # Проверяем требуемый план
                # if required_plan and subscription.plan_id != required_plan:
                #     return jsonify({
                #         "success": False,
                #         "error": f"Требуется план {required_plan}",
                #         "current_plan": subscription.plan_id,
                #         "upgrade_required": True
                #     }), 403
                
                # Проверяем лимиты использования
                # if not subscription_service.check_usage_limit(user_id, resource_type, quantity):
                #     usage_stats = subscription_service.get_usage_stats(user_id)
                #     if usage_stats:
                #         return jsonify({
                #             "success": False,
                #             "error": f"Превышен лимит использования {resource_type}",
                #             "usage": {
                #                 "used": getattr(usage_stats, f"{resource_type}_used", 0),
                #                 "limit": getattr(usage_stats, f"{resource_type}_limit", 0)
                #             },
                #             "upgrade_required": True
                #         }), 429
                
                # Временная заглушка - всегда разрешаем
                logger.info(f"Проверка лимита {resource_type} для пользователя {user_id}: разрешено")
                
                # Выполняем оригинальную функцию
                result = func(*args, **kwargs)
                
                # Записываем использование ресурса
                # subscription_service.record_usage(
                #     user_id=user_id,
                #     resource_type=resource_type,
                #     quantity=quantity,
                #     resource_id=request.endpoint,
                #     metadata={
                #         "endpoint": request.endpoint,
                #         "method": request.method,
                #         "user_agent": request.headers.get('User-Agent', ''),
                #         "ip": request.remote_addr
                #     }
                # )
                
                return result
                
            except Exception as e:
                logger.error(f"Ошибка проверки лимита использования: {e}")
                return jsonify({
                    "success": False,
                    "error": "Ошибка проверки лимитов"
                }), 500
        
        return wrapper
    return decorator


def require_plan(plan_id: str):
    """
    Декоратор для требования определенного плана
    
    Args:
        plan_id: ID требуемого плана
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user_id = request.headers.get('X-User-ID')
                if not user_id:
                    return jsonify({
                        "success": False,
                        "error": "Не указан ID пользователя"
                    }), 401
                
                # TODO: Проверить план пользователя
                # subscription = subscription_service.get_user_subscription(user_id)
                # if not subscription or subscription.plan_id != plan_id:
                #     return jsonify({
                #         "success": False,
                #         "error": f"Требуется план {plan_id}",
                #         "current_plan": subscription.plan_id if subscription else None,
                #         "upgrade_required": True
                #     }), 403
                
                logger.info(f"Проверка плана {plan_id} для пользователя {user_id}: разрешено")
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Ошибка проверки плана: {e}")
                return jsonify({
                    "success": False,
                    "error": "Ошибка проверки плана"
                }), 500
        
        return wrapper
    return decorator


def track_usage(resource_type: str, quantity: int = 1):
    """
    Декоратор для отслеживания использования ресурса
    
    Args:
        resource_type: Тип ресурса
        quantity: Количество ресурса
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Записываем использование только при успешном выполнении
                if isinstance(result, tuple) and len(result) >= 2:
                    status_code = result[1]
                    if status_code < 400:  # Успешный ответ
                        user_id = request.headers.get('X-User-ID')
                        if user_id:
                            # TODO: Записать использование
                            # subscription_service.record_usage(
                            #     user_id=user_id,
                            #     resource_type=resource_type,
                            #     quantity=quantity,
                            #     resource_id=request.endpoint,
                            #     metadata={
                            #         "endpoint": request.endpoint,
                            #         "method": request.method,
                            #         "status_code": status_code
                            #     }
                            # )
                            logger.info(f"Записано использование {resource_type} для пользователя {user_id}")
                
                return result
                
            except Exception as e:
                logger.error(f"Ошибка отслеживания использования: {e}")
                return func(*args, **kwargs)  # Возвращаем результат без отслеживания
        
        return wrapper
    return decorator


class UsageMiddleware:
    """Middleware класс для проверки лимитов"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация middleware"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Выполняется перед каждым запросом"""
        # Добавляем информацию о пользователе в контекст
        user_id = request.headers.get('X-User-ID')
        if user_id:
            g.user_id = user_id
            
            # TODO: Получить информацию о подписке
            # subscription = subscription_service.get_user_subscription(user_id)
            # if subscription:
            #     g.subscription = subscription
            #     g.plan = get_plan_by_id(subscription.plan_id)
    
    def after_request(self, response):
        """Выполняется после каждого запроса"""
        # Логируем использование API
        if hasattr(g, 'user_id'):
            logger.info(f"API запрос от пользователя {g.user_id}: {request.method} {request.endpoint} - {response.status_code}")
        
        return response


def get_user_limits(user_id: str) -> Optional[Dict[str, Any]]:
    """Получить лимиты пользователя"""
    try:
        # TODO: Получить лимиты из подписки
        # subscription = subscription_service.get_user_subscription(user_id)
        # if not subscription:
        #     return None
        # 
        # plan = get_plan_by_id(subscription.plan_id)
        # if not plan:
        #     return None
        # 
        # usage_stats = subscription_service.get_usage_stats(user_id)
        # if not usage_stats:
        #     return None
        # 
        # return {
        #     "plan_id": subscription.plan_id,
        #     "plan_name": plan.name,
        #     "limits": {
        #         "posts_per_month": plan.limits.posts_per_month,
        #         "max_agents": plan.limits.max_agents,
        #         "api_calls_per_day": plan.limits.api_calls_per_day,
        #         "storage_gb": plan.limits.storage_gb
        #     },
        #     "usage": {
        #         "posts_used": usage_stats.posts_used,
        #         "agents_used": usage_stats.agents_used,
        #         "api_calls_used": usage_stats.api_calls_used,
        #         "storage_used_gb": usage_stats.storage_used_gb
        #     },
        #     "expires_at": subscription.expires_at.isoformat()
        # }
        
        # Временная заглушка
        return {
            "plan_id": "free",
            "plan_name": "Free",
            "limits": {
                "posts_per_month": 50,
                "max_agents": 3,
                "api_calls_per_day": 100,
                "storage_gb": 1
            },
            "usage": {
                "posts_used": 15,
                "agents_used": 2,
                "api_calls_used": 25,
                "storage_used_gb": 0.5
            },
            "expires_at": "2024-12-31T23:59:59Z"
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения лимитов пользователя: {e}")
        return None
