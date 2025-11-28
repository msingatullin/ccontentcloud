"""
Flask-RESTX namespace: Instagram API (Swagger exposure for existing Blueprint routes)
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging

from app.database.connection import get_db_session
from app.services.instagram_account_service import InstagramAccountService
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

instagram_ns = Namespace(
    'instagram',
    description='Управление Instagram аккаунтами пользователя',
    path='/instagram'
)

account_model = instagram_ns.model('InstagramAccount', {
    'id': fields.Integer,
    'instagram_username': fields.String,
    'account_name': fields.String,
    'is_default': fields.Boolean,
    'is_active': fields.Boolean,
    'is_verified': fields.Boolean,
})

add_account_request = instagram_ns.model('AddInstagramAccountRequest', {
    'username': fields.String(required=True),
    'password': fields.String(required=True),
    'account_name': fields.String(required=True)
})


@instagram_ns.route('/accounts')
class InstagramAccounts(Resource):
    @jwt_required
    @instagram_ns.doc('list_instagram_accounts', security='BearerAuth', params={'active_only': 'true/false'})
    def get(self, current_user):
        try:
            user_id = current_user.get('user_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            db = get_db_session()
            service = InstagramAccountService(db)
            accounts = service.get_user_accounts(user_id, active_only=active_only)
            return {
                'success': True,
                'accounts': [acc.to_dict() for acc in accounts],
                'count': len(accounts)
            }, 200
        except Exception as e:
            logger.error(f"Ошибка получения Instagram аккаунтов: {e}")
            return {'success': False, 'error': 'Ошибка получения списка аккаунтов'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @instagram_ns.doc('add_instagram_account', security='BearerAuth')
    @instagram_ns.expect(add_account_request, validate=True)
    def post(self, current_user):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            account_name = data.get('account_name', '').strip()

            if not username:
                return {'success': False, 'error': 'Укажите Instagram username'}, 400
            if not password:
                return {'success': False, 'error': 'Укажите пароль от Instagram'}, 400
            if not account_name or len(account_name) < 3:
                return {'success': False, 'error': 'Название должно быть не короче 3 символов'}, 400

            db = get_db_session()
            service = InstagramAccountService(db)
            import asyncio
            success, message, account = asyncio.run(
                service.add_account(user_id, username, password, account_name)
            )
            if success:
                return {'success': True, 'message': message, 'account': account.to_dict()}, 201
            return {'success': False, 'error': message}, 400
        except Exception as e:
            logger.error(f"Критическая ошибка добавления Instagram: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@instagram_ns.route('/accounts/<int:account_id>')
class InstagramAccountItem(Resource):
    @jwt_required
    @instagram_ns.doc('get_instagram_account', security='BearerAuth')
    def get(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = InstagramAccountService(db)
            account = service.get_account_by_id(user_id, account_id)
            if not account:
                return {'success': False, 'error': 'Аккаунт не найден'}, 404
            return {'success': True, 'account': account.to_dict()}, 200
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта Instagram: {e}")
            return {'success': False, 'error': 'Ошибка получения информации'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @instagram_ns.doc('update_instagram_account', security='BearerAuth')
    def put(self, current_user, account_id: int):
        """Обновить аккаунт Instagram (включая привязку к проекту)"""
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            
            project_id = data.get('project_id')
            has_project_id = 'project_id' in data
            
            if not has_project_id:
                return {'success': False, 'error': 'Укажите project_id для обновления'}, 400
            
            db = get_db_session()
            from app.models.instagram_accounts import InstagramAccount
            
            account = db.query(InstagramAccount).filter(
                InstagramAccount.id == account_id,
                InstagramAccount.user_id == user_id
            ).first()
            
            if not account:
                return {'success': False, 'error': 'Аккаунт не найден'}, 404
            
            # Проверяем что project принадлежит пользователю (если не null)
            if project_id is not None:
                from app.models.project import Project
                project = db.query(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id
                ).first()
                if not project:
                    return {'success': False, 'error': 'Проект не найден'}, 404
            
            account.project_id = project_id
            db.commit()
            db.refresh(account)
            
            action = 'привязан к проекту' if project_id else 'отвязан от проекта'
            return {
                'success': True,
                'message': f'Аккаунт успешно {action}',
                'account': account.to_dict()
            }, 200
        except Exception as e:
            logger.error(f"Ошибка обновления Instagram аккаунта: {e}")
            return {'success': False, 'error': 'Ошибка обновления'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @instagram_ns.doc('delete_instagram_account', security='BearerAuth')
    def delete(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = InstagramAccountService(db)
            success = service.deactivate_account(user_id, account_id)
            if success:
                return {'success': True, 'message': 'Аккаунт успешно удален'}, 200
            return {'success': False, 'error': 'Аккаунт не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка удаления Instagram аккаунта: {e}")
            return {'success': False, 'error': 'Ошибка удаления'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@instagram_ns.route('/accounts/<int:account_id>/default')
class InstagramAccountDefault(Resource):
    @jwt_required
    @instagram_ns.doc('set_default_instagram', security='BearerAuth')
    def put(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = InstagramAccountService(db)
            success = service.set_default_account(user_id, account_id)
            if success:
                return {'success': True, 'message': 'Аккаунт установлен по умолчанию'}, 200
            return {'success': False, 'error': 'Аккаунт не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка установки дефолтного Instagram: {e}")
            return {'success': False, 'error': 'Ошибка установки'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


activate_request = instagram_ns.model('ActivateInstagramRequest', {
    'is_active': fields.Boolean(required=True, description='Статус активации (true/false)')
})


@instagram_ns.route('/accounts/<int:account_id>/activate')
class InstagramAccountActivate(Resource):
    @jwt_required
    @instagram_ns.doc('toggle_instagram_activation', security='BearerAuth')
    @instagram_ns.expect(activate_request, validate=True)
    def put(self, current_user, account_id: int):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            is_active = data.get('is_active')
            if is_active is None:
                return {'success': False, 'error': 'Укажите is_active (true/false)'}, 400
            
            db = get_db_session()
            service = InstagramAccountService(db)
            success = service.toggle_activation(user_id, account_id, bool(is_active))
            if success:
                status_text = "активирован" if is_active else "деактивирован"
                return {
                    'success': True,
                    'message': f'Аккаунт успешно {status_text}',
                    'is_active': is_active
                }, 200
            return {'success': False, 'error': 'Аккаунт не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка переключения активации Instagram: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()




