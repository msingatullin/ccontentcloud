"""
Middleware для аутентификации
"""

from .jwt import JWTMiddleware

__all__ = ['JWTMiddleware']
