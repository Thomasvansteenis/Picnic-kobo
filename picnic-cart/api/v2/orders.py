"""Orders API endpoints."""

from flask import Blueprint, request, jsonify

from services.auth import require_auth, get_current_user
from services.mcp_client import get_mcp_client
from services.db import get_db

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


def transform_order(raw_order):
    """Transform raw order/delivery data to frontend format."""
    # Handle different date field names
    delivery_date = (
        raw_order.get('delivery_date') or
        raw_order.get('slot', {}).get('window_start') or
        raw_order.get('delivery_time', {}).get('start')
    )

    slot_start = (
        raw_order.get('delivery_slot_start') or
        raw_order.get('slot', {}).get('window_start') or
        raw_order.get('delivery_time', {}).get('start')
    )

    slot_end = (
        raw_order.get('delivery_slot_end') or
        raw_order.get('slot', {}).get('window_end') or
        raw_order.get('delivery_time', {}).get('end')
    )

    # Extract items
    items = []
    raw_items = raw_order.get('orders', [{}])[0].get('items', []) if raw_order.get('orders') else raw_order.get('items', [])

    for item in raw_items:
        actual_items = item.get('items', [item])
        for actual in actual_items:
            quantity = 1
            for dec in actual.get('decorators', []):
                if dec.get('type') == 'QUANTITY':
                    quantity = dec.get('quantity', 1)
                    break

            items.append({
                'id': actual.get('id'),
                'product_id': actual.get('id'),
                'product_name': actual.get('name'),
                'quantity': quantity,
                'price': actual.get('price', 0),
                'image_url': actual.get('image_url'),
            })

    return {
        'id': raw_order.get('id'),
        'status': raw_order.get('status', 'CURRENT'),
        'delivery_date': delivery_date,
        'delivery_slot_start': slot_start,
        'delivery_slot_end': slot_end,
        'total_price': raw_order.get('total_price', 0),
        'total_items': len(items),
        'items': items,
    }


@orders_bp.route('/upcoming', methods=['GET'])
@require_auth
def get_upcoming():
    """Get upcoming/scheduled orders."""
    try:
        mcp = get_mcp_client()
        result = mcp.call_tool('get_order_history', {
            'filter': 'CURRENT',
            'limit': 10
        })

        deliveries = result.get('deliveries', []) if isinstance(result, dict) else result
        if not isinstance(deliveries, list):
            deliveries = []

        orders = [transform_order(d) for d in deliveries]

        return jsonify({
            'orders': orders,
            'next_delivery': orders[0] if orders else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """Get order history."""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    try:
        mcp = get_mcp_client()
        result = mcp.call_tool('get_order_history', {
            'filter': 'COMPLETED',
            'limit': limit + offset
        })

        deliveries = result.get('deliveries', []) if isinstance(result, dict) else result
        if not isinstance(deliveries, list):
            deliveries = []

        # Apply offset
        deliveries = deliveries[offset:offset + limit]
        orders = [transform_order(d) for d in deliveries]

        return jsonify({
            'orders': orders,
            'total': len(orders),
            'has_more': len(orders) == limit
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/<order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    """Get specific order details."""
    try:
        mcp = get_mcp_client()
        result = mcp.call_tool('get_delivery_details', {
            'deliveryId': order_id
        })

        if not result:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify(transform_order(result))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/search', methods=['GET'])
@require_auth
def search_orders():
    """Search within orders."""
    query = request.args.get('q', '')
    scope = request.args.get('scope', 'all')

    if not query:
        return jsonify({
            'query': '',
            'scope': scope,
            'matches': []
        })

    try:
        mcp = get_mcp_client()
        result = mcp.call_tool('search_orders', {
            'query': query,
            'scope': scope
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/sync', methods=['POST'])
@require_auth
def sync_orders():
    """Sync order history to local database for analytics."""
    user = get_current_user()

    try:
        mcp = get_mcp_client()
        db = get_db()

        # Get all completed orders
        result = mcp.call_tool('get_order_history', {
            'filter': 'COMPLETED',
            'limit': 100
        })

        deliveries = result.get('deliveries', []) if isinstance(result, dict) else result
        if not isinstance(deliveries, list):
            deliveries = []

        synced = 0
        for delivery in deliveries:
            try:
                order = transform_order(delivery)
                db.cache_order(user['id'], order)
                synced += 1
            except Exception as e:
                pass

        return jsonify({
            'synced': synced,
            'new_orders': synced  # Simplified
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
