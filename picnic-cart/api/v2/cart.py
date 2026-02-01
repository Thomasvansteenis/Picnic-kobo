"""Cart API endpoints."""

from flask import Blueprint, request, jsonify

from services.auth import require_auth
from services.mcp_client import get_mcp_client

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def transform_cart(raw_cart):
    """Transform raw cart data to frontend format."""
    if not raw_cart:
        return {'items': [], 'total_price': 0, 'total_count': 0}

    items = []
    total_count = 0

    # Handle nested structure from Picnic API
    cart_items = raw_cart.get('items', [])
    for item in cart_items:
        # Handle ORDER_LINE/ORDER_ARTICLE structure
        actual_items = item.get('items', [item])
        for actual in actual_items:
            quantity = 1
            for dec in actual.get('decorators', []):
                if dec.get('type') == 'QUANTITY':
                    quantity = dec.get('quantity', 1)
                    break

            items.append({
                'id': actual.get('id'),
                'quantity': quantity,
                'total_price': actual.get('price', 0) * quantity,
                'product': {
                    'id': actual.get('id'),
                    'name': actual.get('name'),
                    'price': actual.get('price', 0),
                    'display_price': actual.get('display_price'),
                    'unit_quantity': actual.get('unit_quantity'),
                    'image_url': actual.get('image_url'),
                }
            })
            total_count += quantity

    return {
        'items': items,
        'total_price': raw_cart.get('total_price', 0),
        'total_count': total_count
    }


@cart_bp.route('', methods=['GET'])
@require_auth
def get_cart():
    """Get current shopping cart."""
    try:
        mcp = get_mcp_client()
        raw_cart = mcp.get_cart()
        cart = transform_cart(raw_cart)
        return jsonify(cart)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_bp.route('/items', methods=['POST'])
@require_auth
def add_item():
    """Add item to cart."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400

    try:
        mcp = get_mcp_client()
        result = mcp.add_to_cart(product_id, quantity)
        cart = transform_cart(mcp.get_cart())
        return jsonify({'success': True, 'cart': cart})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_bp.route('/items/<product_id>', methods=['PATCH'])
@require_auth
def update_item(product_id):
    """Update item quantity."""
    data = request.get_json()
    quantity = data.get('quantity')

    if quantity is None:
        return jsonify({'error': 'quantity is required'}), 400

    try:
        mcp = get_mcp_client()
        # Get current quantity first
        cart = mcp.get_cart()
        current_qty = 0
        for item in cart.get('items', []):
            for actual in item.get('items', [item]):
                if actual.get('id') == product_id:
                    for dec in actual.get('decorators', []):
                        if dec.get('type') == 'QUANTITY':
                            current_qty = dec.get('quantity', 1)
                            break

        diff = quantity - current_qty
        if diff > 0:
            mcp.add_to_cart(product_id, diff)
        elif diff < 0:
            mcp.remove_from_cart(product_id, abs(diff))

        cart = transform_cart(mcp.get_cart())
        return jsonify({'success': True, 'cart': cart})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_bp.route('/items/<product_id>', methods=['DELETE'])
@require_auth
def remove_item(product_id):
    """Remove item from cart."""
    quantity = request.args.get('quantity', type=int)

    try:
        mcp = get_mcp_client()
        if quantity:
            mcp.remove_from_cart(product_id, quantity)
        else:
            # Remove all
            mcp.remove_from_cart(product_id, 999)

        cart = transform_cart(mcp.get_cart())
        return jsonify({'success': True, 'cart': cart})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_bp.route('', methods=['DELETE'])
@require_auth
def clear_cart():
    """Clear entire cart."""
    try:
        mcp = get_mcp_client()
        mcp.clear_cart()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_bp.route('/bulk-add', methods=['POST'])
@require_auth
def bulk_add():
    """Add multiple items to cart."""
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'items array is required'}), 400

    try:
        mcp = get_mcp_client()
        results = []
        added = 0
        failed = 0

        for item in items:
            product_id = item.get('productId') or item.get('product_id')
            quantity = item.get('quantity', 1)

            try:
                mcp.add_to_cart(product_id, quantity)
                results.append({
                    'productId': product_id,
                    'success': True,
                    'quantity': quantity
                })
                added += 1
            except Exception as e:
                results.append({
                    'productId': product_id,
                    'success': False,
                    'error': str(e)
                })
                failed += 1

        cart = transform_cart(mcp.get_cart())
        return jsonify({
            'added': added,
            'failed': failed,
            'results': results,
            'cart': cart
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
