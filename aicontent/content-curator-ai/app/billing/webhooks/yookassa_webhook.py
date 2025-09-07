"""
Webhook обработчик для ЮКассы
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify, current_app

from app.billing.services.yookassa_service import YooKassaService
from app.billing.services.subscription_service import SubscriptionService
from app.billing.models.subscription import PaymentStatus, SubscriptionStatus

logger = logging.getLogger(__name__)

# Создаем Blueprint для webhooks
webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')


@webhook_bp.route('/yookassa', methods=['POST'])
def yookassa_webhook():
    """Обработчик webhook от ЮКассы"""
    try:
        # Получаем данные запроса
        request_body = request.get_data(as_text=True)
        signature = request.headers.get('X-YooMoney-Signature', '')
        
        logger.info(f"Получен webhook от ЮКассы: {request_body[:200]}...")
        
        # Инициализируем сервисы
        yookassa_service = YooKassaService()
        
        # Проверяем подпись
        if not yookassa_service.verify_webhook(request_body, signature):
            logger.warning("Неверная подпись webhook от ЮКассы")
            return jsonify({"error": "Invalid signature"}), 400
        
        # Парсим webhook
        webhook_data = yookassa_service.parse_webhook(request_body)
        if not webhook_data:
            logger.warning("Не удалось распарсить webhook от ЮКассы")
            return jsonify({"error": "Invalid webhook data"}), 400
        
        # Обрабатываем событие
        success = _process_webhook_event(webhook_data)
        
        if success:
            logger.info(f"Webhook успешно обработан: {webhook_data['event_type']}")
            return jsonify({"status": "ok"}), 200
        else:
            logger.error(f"Ошибка обработки webhook: {webhook_data['event_type']}")
            return jsonify({"error": "Processing failed"}), 500
            
    except Exception as e:
        logger.error(f"Ошибка обработки webhook от ЮКассы: {e}")
        return jsonify({"error": "Internal server error"}), 500


def _process_webhook_event(webhook_data: Dict[str, Any]) -> bool:
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


def _handle_payment_succeeded(webhook_data: Dict[str, Any]) -> bool:
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


def _handle_payment_canceled(webhook_data: Dict[str, Any]) -> bool:
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


def _handle_refund_succeeded(webhook_data: Dict[str, Any]) -> bool:
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


def _send_payment_notification(user_id: str, payment_id: str, status: str):
    """Отправить уведомление пользователю о статусе платежа"""
    try:
        # TODO: Интегрировать с системой уведомлений
        # notification_service = NotificationService()
        # 
        # if status == 'success':
        #     message = f"Платеж {payment_id} успешно обработан"
        # elif status == 'canceled':
        #     message = f"Платеж {payment_id} был отменен"
        # elif status == 'refunded':
        #     message = f"По платежу {payment_id} выполнен возврат"
        # else:
        #     message = f"Обновление статуса платежа {payment_id}"
        # 
        # notification_service.send_notification(
        #     user_id=user_id,
        #     type='payment_status',
        #     title='Статус платежа',
        #     message=message,
        #     data={'payment_id': payment_id, 'status': status}
        # )
        
        logger.info(f"Уведомление о платеже {payment_id} отправлено пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о платеже: {e}")


@webhook_bp.route('/yookassa/test', methods=['POST'])
def yookassa_test_webhook():
    """Тестовый webhook для отладки"""
    try:
        request_body = request.get_data(as_text=True)
        headers = dict(request.headers)
        
        logger.info("Получен тестовый webhook от ЮКассы:")
        logger.info(f"Headers: {headers}")
        logger.info(f"Body: {request_body}")
        
        return jsonify({
            "status": "ok",
            "message": "Test webhook received",
            "headers": headers,
            "body_length": len(request_body)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка обработки тестового webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500
