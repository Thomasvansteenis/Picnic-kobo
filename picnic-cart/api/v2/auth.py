"""Authentication API endpoints."""

from flask import Blueprint, request, jsonify, g

from services.auth import get_auth_service, require_auth, get_current_user
from services.mcp_client import get_mcp_client

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/status', methods=['GET'])
def get_status():
    """Check authentication status."""
    token = None

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]

    if not token:
        token = request.cookies.get('session_token')

    auth_service = get_auth_service()
    status = auth_service.get_auth_status(token)

    return jsonify(status)


@auth_bp.route('/setup-pin', methods=['POST'])
def setup_pin():
    """Set up PIN for first-time users."""
    data = request.get_json()
    pin = data.get('pin')

    if not pin:
        return jsonify({'error': 'PIN is required'}), 400

    # Get Picnic user ID from MCP server
    try:
        mcp = get_mcp_client()
        user_data = mcp.get_user()
        picnic_user_id = user_data.get('user_id') or user_data.get('id') or 'default'
    except Exception as e:
        # If MCP is not available, use a default ID
        picnic_user_id = 'default-user'

    try:
        auth_service = get_auth_service()
        result = auth_service.setup_pin(picnic_user_id, pin)

        response = jsonify(result)
        response.set_cookie(
            'session_token',
            result['token'],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            max_age=3600  # 1 hour
        )
        return response

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to set up PIN'}), 500


@auth_bp.route('/verify-pin', methods=['POST'])
def verify_pin():
    """Verify PIN and get session token."""
    data = request.get_json()
    pin = data.get('pin')

    if not pin:
        return jsonify({'error': 'PIN is required'}), 400

    # Get Picnic user ID from MCP server
    try:
        mcp = get_mcp_client()
        user_data = mcp.get_user()
        picnic_user_id = user_data.get('user_id') or user_data.get('id') or 'default'
    except Exception:
        picnic_user_id = 'default-user'

    try:
        auth_service = get_auth_service()
        result = auth_service.verify_pin(picnic_user_id, pin)

        response = jsonify(result)
        response.set_cookie(
            'session_token',
            result['token'],
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )
        return response

    except ValueError as e:
        return jsonify({'error': str(e), 'valid': False}), 401
    except Exception as e:
        return jsonify({'error': 'Failed to verify PIN', 'valid': False}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Log out and invalidate session."""
    user = get_current_user()

    if user:
        auth_service = get_auth_service()
        auth_service.logout(user['id'])

    response = jsonify({'success': True})
    response.delete_cookie('session_token')
    return response


@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """Refresh session token."""
    token = g.get('token')

    if not token:
        return jsonify({'error': 'No token to refresh'}), 400

    auth_service = get_auth_service()
    new_token = auth_service.refresh_token_if_active(token)

    if new_token and new_token != token:
        response = jsonify({'success': True, 'token': new_token})
        response.set_cookie(
            'session_token',
            new_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )
        return response

    return jsonify({'success': True, 'token': token})
