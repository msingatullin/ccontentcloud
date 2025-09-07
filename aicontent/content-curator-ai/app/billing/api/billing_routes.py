"""
API routes для billing системы
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin

from app.billing.services.yookassa_service import YooKassaService, PaymentRequest
from app.billing.services.subscription_service import SubscriptionService
from app.billing.models.subscription import get_all_plans, get_plan_by_id

logger = logging.getLogger(__name__)

# Создаем Blueprint для billing API
billing_bp = Blueprint('billing', __name__, url_prefix='/api/v1/billing')


@billing_bp.route('/plans', methods=['GET'])
@cross_origin()
def get_plans():
    """Получить все доступные тарифные планы"""
    try:
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
        
        return jsonify({
            "success": True,
            "plans": formatted_plans
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения планов: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения тарифных планов"
        }), 500


@billing_bp.route('/plans/<plan_id>', methods=['GET'])
@cross_origin()
def get_plan(plan_id: str):
    """Получить конкретный тарифный план"""
    try:
        plan = get_plan_by_id(plan_id)
        if not plan:
            return jsonify({
                "success": False,
                "error": "План не найден"
            }), 404
        
        return jsonify({
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
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения плана {plan_id}: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения тарифного плана"
        }), 500


@billing_bp.route('/subscription', methods=['GET'])
@cross_origin()
def get_subscription():
    """Получить подписку пользователя"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID пользователя"
            }), 400
        
        # TODO: Получить сессию БД из контекста приложения
        # subscription_service = SubscriptionService(db_session)
        # subscription = subscription_service.get_user_subscription(user_id)
        
        # Временная заглушка
        subscription = None
        
        if not subscription:
            return jsonify({
                "success": True,
                "subscription": None,
                "message": "У пользователя нет активной подписки"
            })
        
        return jsonify({
            "success": True,
            "subscription": {
                "id": subscription.id,
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "starts_at": subscription.starts_at.isoformat(),
                "expires_at": subscription.expires_at.isoformat(),
                "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                "auto_renew": subscription.auto_renew,
                "last_payment_at": subscription.last_payment_at.isoformat() if subscription.last_payment_at else None,
                "next_payment_at": subscription.next_payment_at.isoformat() if subscription.next_payment_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения подписки: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения подписки"
        }), 500


@billing_bp.route('/subscription', methods=['POST'])
@cross_origin()
def create_subscription():
    """Создать подписку"""
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID пользователя"
            }), 400
        
        plan_id = data.get('plan_id')
        if not plan_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID плана"
            }), 400
        
        plan = get_plan_by_id(plan_id)
        if not plan:
            return jsonify({
                "success": False,
                "error": "План не найден"
            }), 404
        
        # Если план бесплатный, создаем подписку сразу
        if plan.price_monthly == 0:
            # TODO: Создать бесплатную подписку
            return jsonify({
                "success": True,
                "subscription": {
                    "id": "temp_free_subscription",
                    "plan_id": plan_id,
                    "status": "active",
                    "message": "Бесплатная подписка активирована"
                }
            })
        
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
        
        return jsonify({
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
        })
        
    except Exception as e:
        logger.error(f"Ошибка создания подписки: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка создания подписки"
        }), 500


@billing_bp.route('/subscription/<int:subscription_id>/cancel', methods=['POST'])
@cross_origin()
def cancel_subscription(subscription_id: int):
    """Отменить подписку"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID пользователя"
            }), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'user_request')
        
        # TODO: Отменить подписку через SubscriptionService
        # subscription_service = SubscriptionService(db_session)
        # success = subscription_service.cancel_subscription(subscription_id, reason)
        
        # Временная заглушка
        success = True
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Ошибка отмены подписки"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Подписка успешно отменена"
        })
        
    except Exception as e:
        logger.error(f"Ошибка отмены подписки: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка отмены подписки"
        }), 500


@billing_bp.route('/usage', methods=['GET'])
@cross_origin()
def get_usage():
    """Получить статистику использования"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID пользователя"
            }), 400
        
        # TODO: Получить статистику через SubscriptionService
        # subscription_service = SubscriptionService(db_session)
        # usage_stats = subscription_service.get_usage_stats(user_id)
        
        # Временная заглушка
        usage_stats = {
            "posts_used": 15,
            "posts_limit": 50,
            "api_calls_used": 250,
            "api_calls_limit": 100,
            "storage_used_gb": 0.5,
            "storage_limit_gb": 1,
            "agents_used": 2,
            "agents_limit": 3,
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-31T23:59:59Z"
        }
        
        return jsonify({
            "success": True,
            "usage": usage_stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики использования: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения статистики использования"
        }), 500


@billing_bp.route('/payment-methods', methods=['GET'])
@cross_origin()
def get_payment_methods():
    """Получить доступные способы оплаты"""
    try:
        yookassa_service = YooKassaService()
        payment_methods = yookassa_service.get_payment_methods()
        
        return jsonify({
            "success": True,
            "payment_methods": payment_methods
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения способов оплаты: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения способов оплаты"
        }), 500


@billing_bp.route('/payment/<payment_id>', methods=['GET'])
@cross_origin()
def get_payment_status(payment_id: str):
    """Получить статус платежа"""
    try:
        yookassa_service = YooKassaService()
        payment_info = yookassa_service.get_payment(payment_id)
        
        if not payment_info:
            return jsonify({
                "success": False,
                "error": "Платеж не найден"
            }), 404
        
        return jsonify({
            "success": True,
            "payment": payment_info
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса платежа: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения статуса платежа"
        }), 500


@billing_bp.route('/events', methods=['GET'])
@cross_origin()
def get_billing_events():
    """Получить события billing системы"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Не указан ID пользователя"
            }), 400
        
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
        
        return jsonify({
            "success": True,
            "events": events
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения billing событий: {e}")
        return jsonify({
            "success": False,
            "error": "Ошибка получения billing событий"
        }), 500
