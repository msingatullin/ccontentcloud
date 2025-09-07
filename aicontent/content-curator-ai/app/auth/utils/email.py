"""
Email сервис для отправки уведомлений
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime

from app.auth.models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    """Сервис для отправки email уведомлений"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@goinvesting.ai')
        self.from_name = os.getenv('FROM_NAME', 'AI Content Orchestrator')
        self.base_url = os.getenv('BASE_URL', 'https://goinvesting.ai')
        
        # Проверка конфигурации
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending will be disabled.")

    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """Отправить email"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning(f"Email not sent to {to_email}: SMTP not configured")
            return False
        
        try:
            # Создание сообщения
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Добавление текстового контента
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Добавление HTML контента
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Отправка email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, user: User) -> bool:
        """Отправить email для верификации"""
        verification_url = f"{self.base_url}/auth/verify-email?token={user.email_verification_token}"
        
        subject = "Подтвердите ваш email - AI Content Orchestrator"
        
        html_content = self._get_verification_email_html(user, verification_url)
        text_content = self._get_verification_email_text(user, verification_url)
        
        return self.send_email(user.email, subject, html_content, text_content)

    def send_password_reset_email(self, user: User) -> bool:
        """Отправить email для сброса пароля"""
        reset_url = f"{self.base_url}/auth/reset-password?token={user.password_reset_token}"
        
        subject = "Сброс пароля - AI Content Orchestrator"
        
        html_content = self._get_password_reset_email_html(user, reset_url)
        text_content = self._get_password_reset_email_text(user, reset_url)
        
        return self.send_email(user.email, subject, html_content, text_content)

    def send_welcome_email(self, user: User) -> bool:
        """Отправить приветственный email"""
        subject = "Добро пожаловать в AI Content Orchestrator!"
        
        html_content = self._get_welcome_email_html(user)
        text_content = self._get_welcome_email_text(user)
        
        return self.send_email(user.email, subject, html_content, text_content)

    def send_subscription_confirmation_email(self, user: User, subscription: Any) -> bool:
        """Отправить email подтверждения подписки"""
        subject = "Подписка активирована - AI Content Orchestrator"
        
        html_content = self._get_subscription_confirmation_html(user, subscription)
        text_content = self._get_subscription_confirmation_text(user, subscription)
        
        return self.send_email(user.email, subject, html_content, text_content)

    def send_payment_confirmation_email(self, user: User, payment: Any) -> bool:
        """Отправить email подтверждения платежа"""
        subject = "Платеж подтвержден - AI Content Orchestrator"
        
        html_content = self._get_payment_confirmation_html(user, payment)
        text_content = self._get_payment_confirmation_text(user, payment)
        
        return self.send_email(user.email, subject, html_content, text_content)

    def _get_verification_email_html(self, user: User, verification_url: str) -> str:
        """HTML контент для email верификации"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Подтверждение email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Content Orchestrator</h1>
                    <p>Подтвердите ваш email адрес</p>
                </div>
                <div class="content">
                    <h2>Привет, {user.get_display_name()}!</h2>
                    <p>Спасибо за регистрацию в AI Content Orchestrator. Для завершения регистрации подтвердите ваш email адрес.</p>
                    <p>Нажмите на кнопку ниже для подтверждения:</p>
                    <a href="{verification_url}" class="button">Подтвердить email</a>
                    <p>Если кнопка не работает, скопируйте и вставьте эту ссылку в браузер:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    <p><strong>Важно:</strong> Ссылка действительна в течение 24 часов.</p>
                </div>
                <div class="footer">
                    <p>Если вы не регистрировались в AI Content Orchestrator, просто проигнорируйте это письмо.</p>
                    <p>© 2024 AI Content Orchestrator. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_verification_email_text(self, user: User, verification_url: str) -> str:
        """Текстовый контент для email верификации"""
        return f"""
        AI Content Orchestrator - Подтверждение email
        
        Привет, {user.get_display_name()}!
        
        Спасибо за регистрацию в AI Content Orchestrator. Для завершения регистрации подтвердите ваш email адрес.
        
        Перейдите по ссылке для подтверждения:
        {verification_url}
        
        Важно: Ссылка действительна в течение 24 часов.
        
        Если вы не регистрировались в AI Content Orchestrator, просто проигнорируйте это письмо.
        
        © 2024 AI Content Orchestrator. Все права защищены.
        """

    def _get_password_reset_email_html(self, user: User, reset_url: str) -> str:
        """HTML контент для email сброса пароля"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Сброс пароля</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Content Orchestrator</h1>
                    <p>Сброс пароля</p>
                </div>
                <div class="content">
                    <h2>Привет, {user.get_display_name()}!</h2>
                    <p>Мы получили запрос на сброс пароля для вашего аккаунта.</p>
                    <p>Нажмите на кнопку ниже для создания нового пароля:</p>
                    <a href="{reset_url}" class="button">Сбросить пароль</a>
                    <p>Если кнопка не работает, скопируйте и вставьте эту ссылку в браузер:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    <div class="warning">
                        <strong>Важно:</strong> Ссылка действительна в течение 1 часа. Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
                    </div>
                </div>
                <div class="footer">
                    <p>© 2024 AI Content Orchestrator. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_password_reset_email_text(self, user: User, reset_url: str) -> str:
        """Текстовый контент для email сброса пароля"""
        return f"""
        AI Content Orchestrator - Сброс пароля
        
        Привет, {user.get_display_name()}!
        
        Мы получили запрос на сброс пароля для вашего аккаунта.
        
        Перейдите по ссылке для создания нового пароля:
        {reset_url}
        
        Важно: Ссылка действительна в течение 1 часа. Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
        
        © 2024 AI Content Orchestrator. Все права защищены.
        """

    def _get_welcome_email_html(self, user: User) -> str:
        """HTML контент для приветственного email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Добро пожаловать!</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .feature {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Content Orchestrator</h1>
                    <p>Добро пожаловать!</p>
                </div>
                <div class="content">
                    <h2>Привет, {user.get_display_name()}!</h2>
                    <p>Добро пожаловать в AI Content Orchestrator! Ваш email успешно подтвержден.</p>
                    
                    <h3>Что дальше?</h3>
                    <div class="feature">
                        <h4>🚀 Начните создавать контент</h4>
                        <p>Используйте наших AI-агентов для автоматического создания контента</p>
                    </div>
                    <div class="feature">
                        <h4>📊 Анализируйте результаты</h4>
                        <p>Отслеживайте эффективность вашего контента в реальном времени</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ Масштабируйте бизнес</h4>
                        <p>Создавайте больше контента с меньшими усилиями</p>
                    </div>
                    
                    <a href="{self.base_url}/dashboard" class="button">Перейти в панель управления</a>
                </div>
                <div class="footer">
                    <p>© 2024 AI Content Orchestrator. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_welcome_email_text(self, user: User) -> str:
        """Текстовый контент для приветственного email"""
        return f"""
        AI Content Orchestrator - Добро пожаловать!
        
        Привет, {user.get_display_name()}!
        
        Добро пожаловать в AI Content Orchestrator! Ваш email успешно подтвержден.
        
        Что дальше?
        
        🚀 Начните создавать контент
        Используйте наших AI-агентов для автоматического создания контента
        
        📊 Анализируйте результаты
        Отслеживайте эффективность вашего контента в реальном времени
        
        ⚡ Масштабируйте бизнес
        Создавайте больше контента с меньшими усилиями
        
        Перейти в панель управления: {self.base_url}/dashboard
        
        © 2024 AI Content Orchestrator. Все права защищены.
        """

    def _get_subscription_confirmation_html(self, user: User, subscription: Any) -> str:
        """HTML контент для подтверждения подписки"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Подписка активирована</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Content Orchestrator</h1>
                    <p>Подписка активирована</p>
                </div>
                <div class="content">
                    <h2>Поздравляем, {user.get_display_name()}!</h2>
                    <p>Ваша подписка успешно активирована. Теперь у вас есть доступ ко всем возможностям AI Content Orchestrator.</p>
                    
                    <a href="{self.base_url}/dashboard" class="button">Начать использовать</a>
                </div>
                <div class="footer">
                    <p>© 2024 AI Content Orchestrator. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_subscription_confirmation_text(self, user: User, subscription: Any) -> str:
        """Текстовый контент для подтверждения подписки"""
        return f"""
        AI Content Orchestrator - Подписка активирована
        
        Поздравляем, {user.get_display_name()}!
        
        Ваша подписка успешно активирована. Теперь у вас есть доступ ко всем возможностям AI Content Orchestrator.
        
        Начать использовать: {self.base_url}/dashboard
        
        © 2024 AI Content Orchestrator. Все права защищены.
        """

    def _get_payment_confirmation_html(self, user: User, payment: Any) -> str:
        """HTML контент для подтверждения платежа"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Платеж подтвержден</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #06b6d4, #10b981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Content Orchestrator</h1>
                    <p>Платеж подтвержден</p>
                </div>
                <div class="content">
                    <h2>Спасибо, {user.get_display_name()}!</h2>
                    <p>Ваш платеж успешно обработан. Спасибо за использование AI Content Orchestrator!</p>
                </div>
                <div class="footer">
                    <p>© 2024 AI Content Orchestrator. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_payment_confirmation_text(self, user: User, payment: Any) -> str:
        """Текстовый контент для подтверждения платежа"""
        return f"""
        AI Content Orchestrator - Платеж подтвержден
        
        Спасибо, {user.get_display_name()}!
        
        Ваш платеж успешно обработан. Спасибо за использование AI Content Orchestrator!
        
        © 2024 AI Content Orchestrator. Все права защищены.
        """
