"""Recurring Lists API endpoints."""

from flask import Blueprint, request, jsonify

from services.auth import require_auth, get_current_user
from services.db import get_db
from services.mcp_client import get_mcp_client

lists_bp = Blueprint('lists', __name__, url_prefix='/lists')


@lists_bp.route('/recurring', methods=['GET'])
@require_auth
def get_recurring_lists():
    """Get all recurring lists for the user."""
    user = get_current_user()

    try:
        db = get_db()
        lists = db.get_recurring_lists(user['id'])
        return jsonify({'lists': lists})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lists_bp.route('/recurring', methods=['POST'])
@require_auth
def create_recurring_list():
    """Create a new recurring list."""
    user = get_current_user()
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400

    try:
        db = get_db()
        new_list = db.create_recurring_list(user['id'], data)
        return jsonify(new_list), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lists_bp.route('/recurring/<list_id>', methods=['GET'])
@require_auth
def get_recurring_list(list_id):
    """Get a specific recurring list."""
    user = get_current_user()

    try:
        db = get_db()
        lists = db.get_recurring_lists(user['id'])
        for lst in lists:
            if str(lst['id']) == list_id:
                return jsonify(lst)
        return jsonify({'error': 'List not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lists_bp.route('/recurring/<list_id>', methods=['PUT'])
@require_auth
def update_recurring_list(list_id):
    """Update a recurring list."""
    data = request.get_json()
    # TODO: Implement update
    return jsonify({'error': 'Not implemented'}), 501


@lists_bp.route('/recurring/<list_id>', methods=['DELETE'])
@require_auth
def delete_recurring_list(list_id):
    """Delete a recurring list."""
    # TODO: Implement delete
    return jsonify({'success': True})


@lists_bp.route('/recurring/<list_id>/add-to-cart', methods=['POST'])
@require_auth
def add_list_to_cart(list_id):
    """Add all items from a list to cart."""
    user = get_current_user()

    try:
        db = get_db()
        lists = db.get_recurring_lists(user['id'])

        target_list = None
        for lst in lists:
            if str(lst['id']) == list_id:
                target_list = lst
                break

        if not target_list:
            return jsonify({'error': 'List not found'}), 404

        items = target_list.get('items', [])
        if not items:
            return jsonify({'added': 0, 'failed': 0, 'cart': {}})

        mcp = get_mcp_client()
        added = 0
        failed = 0

        for item in items:
            try:
                mcp.add_to_cart(
                    item['picnic_product_id'],
                    item.get('default_quantity', 1)
                )
                added += 1
            except:
                failed += 1

        cart = mcp.get_cart()
        return jsonify({
            'added': added,
            'failed': failed,
            'cart': cart
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lists_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions():
    """Get AI-suggested recurring lists based on purchase patterns."""
    user = get_current_user()

    try:
        db = get_db()
        frequency = db.get_purchase_frequency(user['id'], min_purchases=5)

        # Group products by suggested frequency
        weekly_items = []
        biweekly_items = []
        monthly_items = []

        for product in frequency:
            days = product.get('avg_days_between', 30)
            item = {
                'product_id': product['picnic_product_id'],
                'product_name': product['product_name'],
                'default_quantity': 1
            }

            if days <= 7:
                weekly_items.append(item)
            elif days <= 14:
                biweekly_items.append(item)
            else:
                monthly_items.append(item)

        suggestions = []

        if weekly_items:
            suggestions.append({
                'id': 'suggested-weekly',
                'name': 'Wekelijkse boodschappen',
                'frequency': 'weekly',
                'is_auto_generated': True,
                'items': weekly_items[:10]
            })

        if biweekly_items:
            suggestions.append({
                'id': 'suggested-biweekly',
                'name': 'Tweewekelijkse boodschappen',
                'frequency': 'biweekly',
                'is_auto_generated': True,
                'items': biweekly_items[:10]
            })

        return jsonify({'suggestions': suggestions})

    except Exception as e:
        return jsonify({'suggestions': []})
