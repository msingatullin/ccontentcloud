"""
Сервис для работы с ЮКассой
"""

import os
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import yookassa
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotification

from app.billing.models.subscription import PaymentStatus, SubscriptionStatus

logger = logging.getLogger(__name__)


@dataclass
class PaymentRequest:
    """Запрос на создание платежа"""
    amount: int  # в копейках
    currency: str = "RUB"
    description: str = ""
    return_url: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class PaymentResponse:
    """Ответ от ЮКассы"""
    payment_id: str
    payment_url: str
    status: str
    amount: int
    currency: str
    created_at: datetime
    expires_at: datetime


class YooKassaService:
    """Сервис для работы с ЮКассой"""
    
    def __init__(self):
        # Настройка ЮКассы
        self.shop_id = os.getenv('YOOKASSA_SHOP_ID')
        self.secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        self.webhook_secret = os.getenv('YOOKASSA_WEBHOOK_SECRET')
        
        if not self.shop_id or not self.secret_key:
            raise ValueError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY должны быть установлены")
        
        # Инициализация SDK
        Configuration.account_id = self.shop_id
        Configuration.secret_key = self.secret_key
        
        # URL для возврата
        self.return_url = os.getenv('YOOKASSA_RETURN_URL', 'https://content-curator-1046574462613.us-central1.run.app/billing/success')
        self.cancel_url = os.getenv('YOOKASSA_CANCEL_URL', 'https://content-curator-1046574462613.us-central1.run.app/billing/cancel')
        
        logger.info(f"YooKassaService инициализирован для shop_id: {self.shop_id}")
    
    def create_payment(
        self, 
        payment_request: PaymentRequest,
        user_id: str,
        subscription_id: Optional[int] = None
    ) -> PaymentResponse:
        """Создать платеж"""
        try:
            # Подготовка данных для платежа
            payment_data = {
                "amount": {
                    "value": f"{payment_request.amount / 100:.2f}",
                    "currency": payment_request.currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": payment_request.return_url or self.return_url
                },
                "description": payment_request.description,
                "metadata": {
                    "user_id": user_id,
                    "subscription_id": str(subscription_id) if subscription_id else None,
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            # Добавляем дополнительные метаданные
            if payment_request.metadata:
                payment_data["metadata"].update(payment_request.metadata)
            
            # Создание платежа
            payment = Payment.create(payment_data)
            
            logger.info(f"Создан платеж {payment.id} для пользователя {user_id}")
            
            return PaymentResponse(
                payment_id=payment.id,
                payment_url=payment.confirmation.confirmation_url,
                status=payment.status,
                amount=payment_request.amount,
                currency=payment_request.currency,
                created_at=datetime.fromisoformat(payment.created_at.replace('Z', '+00:00')),
                expires_at=datetime.fromisoformat(payment.expires_at.replace('Z', '+00:00'))
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            raise
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о платеже"""
        try:
            payment = Payment.find_one(payment_id)
            
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": int(float(payment.amount.value) * 100),
                "currency": payment.amount.currency,
                "description": payment.description,
                "metadata": payment.metadata,
                "created_at": datetime.fromisoformat(payment.created_at.replace('Z', '+00:00')),
                "paid": payment.paid,
                "refundable": payment.refundable,
                "test": payment.test
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения платежа {payment_id}: {e}")
            return None
    
    def cancel_payment(self, payment_id: str) -> bool:
        """Отменить платеж"""
        try:
            payment = Payment.cancel(payment_id)
            logger.info(f"Платеж {payment_id} отменен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отмены платежа {payment_id}: {e}")
            return False
    
    def create_refund(self, payment_id: str, amount: int, reason: str = "") -> Optional[str]:
        """Создать возврат"""
        try:
            from yookassa import Refund
            
            refund_data = {
                "amount": {
                    "value": f"{amount / 100:.2f}",
                    "currency": "RUB"
                },
                "payment_id": payment_id,
                "description": reason or "Возврат по запросу пользователя"
            }
            
            refund = Refund.create(refund_data)
            logger.info(f"Создан возврат {refund.id} для платежа {payment_id}")
            
            return refund.id
            
        except Exception as e:
            logger.error(f"Ошибка создания возврата для платежа {payment_id}: {e}")
            return None
    
    def verify_webhook(self, request_body: str, signature: str) -> bool:
        """Проверить подпись webhook"""
        if not self.webhook_secret:
            logger.warning("YOOKASSA_WEBHOOK_SECRET не установлен, пропускаем проверку подписи")
            return True
        
        try:
            # Создаем HMAC подпись
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                request_body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Сравниваем подписи
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Ошибка проверки подписи webhook: {e}")
            return False
    
    def parse_webhook(self, request_body: str) -> Optional[Dict[str, Any]]:
        """Парсить webhook от ЮКассы"""
        try:
            notification = WebhookNotification(request_body)
            
            if notification.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
                payment = notification.object
                
                return {
                    "event_type": "payment.succeeded",
                    "payment_id": payment.id,
                    "amount": int(float(payment.amount.value) * 100),
                    "currency": payment.amount.currency,
                    "metadata": payment.metadata,
                    "created_at": datetime.fromisoformat(payment.created_at.replace('Z', '+00:00')),
                    "paid_at": datetime.fromisoformat(payment.paid_at.replace('Z', '+00:00')) if payment.paid_at else None
                }
            
            elif notification.event == WebhookNotificationEventType.PAYMENT_CANCELED:
                payment = notification.object
                
                return {
                    "event_type": "payment.canceled",
                    "payment_id": payment.id,
                    "amount": int(float(payment.amount.value) * 100),
                    "currency": payment.amount.currency,
                    "metadata": payment.metadata,
                    "created_at": datetime.fromisoformat(payment.created_at.replace('Z', '+00:00'))
                }
            
            elif notification.event == WebhookNotificationEventType.REFUND_SUCCEEDED:
                refund = notification.object
                
                return {
                    "event_type": "refund.succeeded",
                    "refund_id": refund.id,
                    "payment_id": refund.payment_id,
                    "amount": int(float(refund.amount.value) * 100),
                    "currency": refund.amount.currency,
                    "created_at": datetime.fromisoformat(refund.created_at.replace('Z', '+00:00'))
                }
            
            else:
                logger.info(f"Получен неизвестный тип webhook: {notification.event}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка парсинга webhook: {e}")
            return None
    
    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """Получить доступные способы оплаты"""
        return [
            {
                "id": "bank_card",
                "name": "Банковская карта",
                "description": "Visa, MasterCard, МИР",
                "icon": "💳"
            },
            {
                "id": "yoo_money",
                "name": "ЮMoney",
                "description": "Кошелек ЮMoney",
                "icon": "💰"
            },
            {
                "id": "qiwi",
                "name": "QIWI",
                "description": "Кошелек QIWI",
                "icon": "🟣"
            },
            {
                "id": "webmoney",
                "name": "WebMoney",
                "description": "Кошелек WebMoney",
                "icon": "🟠"
            },
            {
                "id": "alfabank",
                "name": "Альфа-Клик",
                "description": "Интернет-банк Альфа-Банка",
                "icon": "🏦"
            },
            {
                "id": "sberbank",
                "name": "Сбербанк Онлайн",
                "description": "Интернет-банк Сбербанка",
                "icon": "🟢"
            }
        ]
    
    def format_amount(self, amount_kopecks: int) -> str:
        """Форматировать сумму для отображения"""
        rubles = amount_kopecks / 100
        return f"{rubles:,.2f} ₽".replace(',', ' ')
    
    def is_test_mode(self) -> bool:
        """Проверить, работает ли в тестовом режиме"""
        return os.getenv('YOOKASSA_TEST_MODE', 'false').lower() == 'true'
