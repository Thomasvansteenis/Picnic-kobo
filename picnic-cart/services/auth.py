"""Authentication service with PIN verification and JWT tokens."""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps

import bcrypt
import jwt
from flask import request, g, jsonify

from .db import get_db

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('FLASK_SECRET_KEY', 'change-me-in-production'))
TOKEN_EXPIRY_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
PIN_ATTEMPTS_LIMIT = 5
PIN_LOCKOUT_MINUTES = 15


class AuthService:
    """Authentication service for PIN-based auth."""

    def __init__(self):
        self.db = get_db()

    def setup_pin(self, picnic_user_id: str, pin: str) -> Dict:
        """Set up or update PIN for a user."""
        if not self._validate_pin_format(pin):
            raise ValueError("PIN must be 4-6 digits")

        pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()

        user = self.db.upsert_user(
            picnic_user_id=picnic_user_id,
            pin_hash=pin_hash
        )

        token = self._generate_token(str(user['id']))
        expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)

        self.db.update_user_token(str(user['id']), token, expires_at)

        return {
            'success': True,
            'token': token,
            'expires_at': expires_at.isoformat()
        }

    def verify_pin(self, picnic_user_id: str, pin: str) -> Dict:
        """Verify PIN and return session token."""
        user = self.db.get_user_by_picnic_id(picnic_user_id)

        if not user:
            raise ValueError("User not found. Please set up PIN first.")

        if not user.get('pin_hash'):
            raise ValueError("PIN not set up. Please set up PIN first.")

        # Check rate limiting
        if self._is_locked_out(str(user['id'])):
            raise ValueError(f"Too many attempts. Try again in {PIN_LOCKOUT_MINUTES} minutes.")

        if not bcrypt.checkpw(pin.encode(), user['pin_hash'].encode()):
            self.db.record_failed_attempt(str(user['id']))
            remaining = PIN_ATTEMPTS_LIMIT - self.db.get_recent_failed_attempts(str(user['id']), PIN_LOCKOUT_MINUTES)
            raise ValueError(f"Invalid PIN. {remaining} attempts remaining.")

        # Clear failed attempts on success
        self.db.clear_failed_attempts(str(user['id']))

        token = self._generate_token(str(user['id']))
        expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)

        self.db.update_user_token(str(user['id']), token, expires_at)

        return {
            'valid': True,
            'token': token,
            'expires_at': expires_at.isoformat(),
            'user': {
                'id': str(user['id']),
                'display_name': user.get('display_name'),
                'picnic_user_id': user['picnic_user_id']
            }
        }

    def validate_token(self, token: str) -> Dict:
        """Validate session token and return user info."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

            if not user_id:
                return {'valid': False, 'reason': 'invalid_payload'}

            user = self.db.get_user_by_id(user_id)
            if not user:
                return {'valid': False, 'reason': 'user_not_found'}

            if user.get('access_token') != token:
                return {'valid': False, 'reason': 'token_mismatch'}

            if user.get('token_expires_at') and user['token_expires_at'] < datetime.utcnow():
                return {'valid': False, 'reason': 'expired'}

            return {
                'valid': True,
                'user': {
                    'id': str(user['id']),
                    'display_name': user.get('display_name'),
                    'picnic_user_id': user['picnic_user_id']
                }
            }

        except jwt.ExpiredSignatureError:
            return {'valid': False, 'reason': 'expired'}
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return {'valid': False, 'reason': 'invalid'}

    def get_auth_status(self, token: Optional[str] = None) -> Dict:
        """Get current authentication status."""
        if not token:
            return {
                'authenticated': False,
                'needs_pin_setup': True
            }

        result = self.validate_token(token)

        if result['valid']:
            return {
                'authenticated': True,
                'user': result['user'],
                'needs_pin_setup': False
            }

        return {
            'authenticated': False,
            'needs_pin_setup': result.get('reason') == 'user_not_found'
        }

    def logout(self, user_id: str) -> None:
        """Invalidate user's session."""
        self.db.update_user_token(user_id, '', datetime.utcnow())

    def refresh_token_if_active(self, token: str) -> Optional[str]:
        """Extend token expiry if user is active."""
        result = self.validate_token(token)

        if not result['valid']:
            return None

        user = self.db.get_user_by_id(result['user']['id'])
        if not user:
            return None

        # Refresh if expiring in less than 5 minutes
        if user.get('token_expires_at'):
            remaining = user['token_expires_at'] - datetime.utcnow()
            if remaining < timedelta(minutes=5):
                new_token = self._generate_token(str(user['id']))
                new_expires = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
                self.db.update_user_token(str(user['id']), new_token, new_expires)
                return new_token

        return token

    def _generate_token(self, user_id: str) -> str:
        """Generate a JWT token."""
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
            'jti': secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    def _validate_pin_format(self, pin: str) -> bool:
        """Validate PIN format (4-6 digits)."""
        return pin.isdigit() and 4 <= len(pin) <= 6

    def _is_locked_out(self, user_id: str) -> bool:
        """Check if user is locked out due to failed attempts."""
        attempts = self.db.get_recent_failed_attempts(user_id, PIN_LOCKOUT_MINUTES)
        return attempts >= PIN_ATTEMPTS_LIMIT


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService()


def require_auth(f):
    """Decorator to require valid authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]

        # Check cookie
        if not token:
            token = request.cookies.get('session_token')

        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        auth_service = get_auth_service()
        result = auth_service.validate_token(token)

        if not result['valid']:
            return jsonify({
                'error': 'Invalid or expired token',
                'reason': result.get('reason')
            }), 401

        g.current_user = result['user']
        g.token = token

        return f(*args, **kwargs)

    return decorated


def get_current_user() -> Optional[Dict]:
    """Get the current authenticated user from context."""
    return getattr(g, 'current_user', None)
