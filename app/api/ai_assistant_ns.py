"""
Flask-RESTX namespace: AI Assistant API
Помощь в заполнении опросника и настроек проекта через анализ ресурсов
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
import asyncio
from openai import AsyncOpenAI
import os

from app.api.routes import jwt_required
from app.services.ai_assistant_service import AIAssistantService

logger = logging.getLogger(__name__)

ai_assistant_ns = Namespace(
    'ai-assistant',
    description='AI помощник для заполнения опросника и настроек проекта',
    path='/ai-assistant'
)

# ===== Swagger models =====

analyze_resource_request = ai_assistant_ns.model('AnalyzeResourceRequest', {
    'url': fields.String(required=True, description='URL ресурса для анализа'),
    'type': fields.String(description='Тип ресурса: website, telegram, instagram (опционально, определяется автоматически)')
})

analyze_resource_response = ai_assistant_ns.model('AnalyzeResourceResponse', {
    'success': fields.Boolean(description='Успешность операции'),
    'suggestions': fields.Raw(description='Предложения для заполнения полей'),
    'error': fields.String(description='Ошибка (если есть)')
})

error_model = ai_assistant_ns.model('ErrorResponse', {
    'success': fields.Boolean,
    'error': fields.String
})


@ai_assistant_ns.route('/analyze-resource')
class AnalyzeResource(Resource):
    """Анализ ресурса для автозаполнения настроек проекта"""
    
    @jwt_required
    @ai_assistant_ns.doc('analyze_resource', security='BearerAuth')
    @ai_assistant_ns.expect(analyze_resource_request)
    @ai_assistant_ns.response(200, 'OK', analyze_resource_response)
    @ai_assistant_ns.response(400, 'Bad Request', error_model)
    @ai_assistant_ns.response(500, 'Internal Server Error', error_model)
    def post(self, current_user):
        """
        Анализирует ресурс (сайт/телеграм-канал) и извлекает информацию
        для автозаполнения настроек проекта или опросника
        """
        try:
            data = request.json or {}
            url = data.get('url', '').strip()
            
            if not url:
                return {
                    'success': False,
                    'error': 'URL обязателен'
                }, 400
            
            # Инициализируем сервис
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API ключ не настроен'
                }, 500
            
            openai_client = AsyncOpenAI(api_key=api_key)
            service = AIAssistantService(openai_client)
            
            # Определяем тип ресурса
            resource_type = data.get('type') or service.detect_resource_type(url)
            
            # Получаем контент ресурса
            resource_content = asyncio.run(service.fetch_resource_content(url, resource_type))
            
            if resource_content.get('error'):
                return {
                    'success': False,
                    'error': f"Не удалось получить контент: {resource_content.get('error')}"
                }, 400
            
            # Анализируем для настроек проекта
            analysis = asyncio.run(
                service.analyze_for_project_settings(resource_content, resource_type)
            )
            
            if not analysis:
                return {
                    'success': False,
                    'error': 'Не удалось проанализировать ресурс'
                }, 500
            
            # Формируем предложения
            suggestions = {
                'product_service': analysis.get('product_service', ''),
                'target_audience': analysis.get('target_audience', ''),
                'pain_points': analysis.get('pain_points', []),
                'tone': analysis.get('tone', 'professional'),
                'cta': analysis.get('cta', ''),
                'keywords': analysis.get('keywords', []),
                'hashtags': analysis.get('hashtags', []),
                'brand_name': analysis.get('brand_name', ''),
                'brand_description': analysis.get('brand_description', '')
            }
            
            return {
                'success': True,
                'suggestions': suggestions
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка анализа ресурса: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, 500


@ai_assistant_ns.route('/analyze-for-survey')
class AnalyzeForSurvey(Resource):
    """Анализ ресурса для помощи в конкретном вопросе опросника"""
    
    @jwt_required
    @ai_assistant_ns.doc('analyze_for_survey', security='BearerAuth')
    @ai_assistant_ns.expect(ai_assistant_ns.model('AnalyzeForSurveyRequest', {
        'url': fields.String(required=True),
        'question_type': fields.String(required=True, description='Тип вопроса: niche, audience, pain_points, tone, cta')
    }))
    @ai_assistant_ns.response(200, 'OK', analyze_resource_response)
    def post(self, current_user):
        """Анализирует ресурс для помощи в конкретном вопросе"""
        try:
            data = request.json or {}
            url = data.get('url', '').strip()
            question_type = data.get('question_type', '')
            
            if not url or not question_type:
                return {
                    'success': False,
                    'error': 'URL и question_type обязательны'
                }, 400
            
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API ключ не настроен'
                }, 500
            
            openai_client = AsyncOpenAI(api_key=api_key)
            service = AIAssistantService(openai_client)
            
            resource_type = service.detect_resource_type(url)
            resource_content = asyncio.run(service.fetch_resource_content(url, resource_type))
            
            if resource_content.get('error'):
                return {
                    'success': False,
                    'error': f"Не удалось получить контент: {resource_content.get('error')}"
                }, 400
            
            analysis = asyncio.run(
                service.analyze_for_survey(resource_content, resource_type, question_type)
            )
            
            return {
                'success': True,
                'suggestions': analysis
            }, 200
            
        except Exception as e:
            logger.error(f"Ошибка анализа для опросника: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, 500

