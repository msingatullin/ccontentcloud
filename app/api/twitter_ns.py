"""
Flask-RESTX namespace: Twitter API (Swagger exposure for existing Blueprint routes)
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging

from app.database.connection import get_db_session
from app.services.twitter_account_service import TwitterAccountService
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

twitter_ns = Namespace(
    'twitter',
    description='Управление Twitter аккаунтами пользователя',
    path='/twitter'
)

account_model = twitter_ns.model('TwitterAccount', {
    'id': fields.Integer,
    'twitter_username': fields.String,
    'account_name': fields.String,
    'is_default': fields.Boolean,
    'is_active': fields.Boolean,
    'is_verified': fields.Boolean,
})

oauth_url_response = twitter_ns.model('TwitterOAuthUrl', {
    'success': fields.Boolean,
    'auth_url': fields.String,
    'oauth_token': fields.String,
    'oauth_token_secret': fields.String,
    'message': fields.String
})

oauth_complete_request = twitter_ns.model('TwitterOAuthCompleteRequest', {
    'oauth_token_secret': fields.String(required=True),
    'account_name': fields.String(description='Название аккаунта в UI')
})


@twitter_ns.route('/oauth/url')
class TwitterOAuthUrl(Resource):
    @jwt_required
    @twitter_ns.doc('get_twitter_oauth_url', security='BearerAuth', params={'callback_url': 'URL для возврата'})
    @twitter_ns.response(200, 'OK', oauth_url_response)
    def get(self, current_user):
        try:
            user_id = current_user.get('user_id')
            callback_url = request.args.get('callback_url')
            if not callback_url:
                import os
                base_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
                callback_url = f"{base_url}/api/twitter/oauth/callback"
            db = get_db_session()
            service = TwitterAccountService(db)
            auth_url, oauth_token, oauth_token_secret = service.get_oauth_url(callback_url)
            return {
                'success': True,
                'auth_url': auth_url,
                'oauth_token': oauth_token,
                'oauth_token_secret': oauth_token_secret,
                'message': 'Сохраните oauth_token_secret и передайте в callback'
            }, 200
        except Exception as e:
            logger.error(f"Ошибка генерации OAuth URL: {e}")
            return {'success': False, 'error': f'Ошибка OAuth: {str(e)}'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@twitter_ns.route('/oauth/callback')
class TwitterOAuthCallback(Resource):
    @jwt_required
    @twitter_ns.doc('twitter_oauth_callback', security='BearerAuth', params={'oauth_token': 'token', 'oauth_verifier': 'verifier'})
    @twitter_ns.expect(oauth_complete_request)
    def post(self, current_user):
        try:
            user_id = current_user.get('user_id')
            oauth_token = request.args.get('oauth_token')
            oauth_verifier = request.args.get('oauth_verifier')
            if not oauth_token or not oauth_verifier:
                return {'success': False, 'error': 'Отсутствуют параметры OAuth от Twitter'}, 400
            data = request.get_json() or {}
            oauth_token_secret = data.get('oauth_token_secret')
            account_name = data.get('account_name', 'Мой Twitter аккаунт')
            if not oauth_token_secret:
                return {'success': False, 'error': 'oauth_token_secret обязателен'}, 400
            db = get_db_session()
            service = TwitterAccountService(db)
            import asyncio
            success, message, account = asyncio.run(
                service.complete_oauth(
                    user_id=user_id,
                    oauth_token=oauth_token,
                    oauth_verifier=oauth_verifier,
                    oauth_token_secret=oauth_token_secret,
                    account_name=account_name
                )
            )
            if success:
                return {'success': True, 'message': message, 'account': account.to_dict()}, 201
            return {'success': False, 'error': message}, 400
        except Exception as e:
            logger.error(f"Критическая ошибка OAuth callback: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@twitter_ns.route('/accounts')
class TwitterAccounts(Resource):
    @jwt_required
    @twitter_ns.doc('list_twitter_accounts', security='BearerAuth', params={'active_only': 'true/false'})
    def get(self, current_user):
        try:
            user_id = current_user.get('user_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            db = get_db_session()
            service = TwitterAccountService(db)
            accounts = service.get_user_accounts(user_id, active_only=active_only)
            return {
                'success': True,
                'accounts': [acc.to_dict() for acc in accounts],
                'count': len(accounts)
            }, 200
        except Exception as e:
            logger.error(f"Ошибка получения Twitter аккаунтов: {e}")
            return {'success': False, 'error': 'Ошибка получения списка аккаунтов'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@twitter_ns.route('/accounts/<int:account_id>')
class TwitterAccountItem(Resource):
    @jwt_required
    @twitter_ns.doc('get_twitter_account', security='BearerAuth')
    def get(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TwitterAccountService(db)
            account = service.get_account_by_id(user_id, account_id)
            if not account:
                return {'success': False, 'error': 'Аккаунт не найден'}, 404
            return {'success': True, 'account': account.to_dict()}, 200
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта Twitter: {e}")
            return {'success': False, 'error': 'Ошибка получения информации'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @twitter_ns.doc('delete_twitter_account', security='BearerAuth')
    def delete(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TwitterAccountService(db)
            success = service.deactivate_account(user_id, account_id)
            if success:
                return {'success': True, 'message': 'Аккаунт успешно удален'}, 200
            return {'success': False, 'error': 'Аккаунт не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка удаления Twitter аккаунта: {e}")
            return {'success': False, 'error': 'Ошибка удаления'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@twitter_ns.route('/accounts/<int:account_id>/default')
class TwitterAccountDefault(Resource):
    @jwt_required
    @twitter_ns.doc('set_default_twitter', security='BearerAuth')
    def put(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TwitterAccountService(db)
            success = service.set_default_account(user_id, account_id)
            if success:
                return {'success': True, 'message': 'Аккаунт установлен по умолчанию'}, 200
            return {'success': False, 'error': 'Аккаунт не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка установки дефолтного Twitter: {e}")
            return {'success': False, 'error': 'Ошибка установки'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


