"""Settings API endpoints."""

from flask import Blueprint, request, jsonify

from services.auth import require_auth, get_current_user

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# Default settings
DEFAULT_SETTINGS = {
    'ui_mode': 'full',
    'theme': 'light',
    'language': 'nl',
    'session_timeout_minutes': 30,
    'show_product_images': True,
    'sound_enabled': False,
}


@settings_bp.route('', methods=['GET'])
@require_auth
def get_settings():
    """Get user settings."""
    # TODO: Load from database
    return jsonify(DEFAULT_SETTINGS)


@settings_bp.route('', methods=['PUT'])
@require_auth
def update_settings():
    """Update user settings."""
    data = request.get_json()

    # Validate and merge with defaults
    settings = {**DEFAULT_SETTINGS}

    if 'ui_mode' in data and data['ui_mode'] in ['full', 'ereader']:
        settings['ui_mode'] = data['ui_mode']

    if 'theme' in data and data['theme'] in ['light', 'dark', 'auto']:
        settings['theme'] = data['theme']

    if 'language' in data and data['language'] in ['nl', 'en', 'de']:
        settings['language'] = data['language']

    if 'session_timeout_minutes' in data:
        settings['session_timeout_minutes'] = int(data['session_timeout_minutes'])

    if 'show_product_images' in data:
        settings['show_product_images'] = bool(data['show_product_images'])

    if 'sound_enabled' in data:
        settings['sound_enabled'] = bool(data['sound_enabled'])

    # TODO: Save to database

    return jsonify({
        'success': True,
        'settings': settings
    })


@settings_bp.route('/mode', methods=['GET'])
@require_auth
def get_mode():
    """Get current UI mode."""
    # TODO: Load from database
    return jsonify({'mode': 'full'})


@settings_bp.route('/mode', methods=['PUT'])
@require_auth
def set_mode():
    """Set UI mode."""
    data = request.get_json()
    mode = data.get('mode')

    if mode not in ['full', 'ereader']:
        return jsonify({'error': 'Invalid mode'}), 400

    # TODO: Save to database

    return jsonify({
        'success': True,
        'mode': mode
    })
