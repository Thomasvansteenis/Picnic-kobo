"""Products API endpoints."""

from flask import Blueprint, request, jsonify

from services.auth import require_auth
from services.mcp_client import get_mcp_client

products_bp = Blueprint('products', __name__, url_prefix='/products')


def transform_product(raw_product):
    """Transform raw product data to frontend format."""
    return {
        'id': raw_product.get('id'),
        'name': raw_product.get('name'),
        'price': raw_product.get('price', 0),
        'display_price': raw_product.get('display_price'),
        'unit_quantity': raw_product.get('unit_quantity'),
        'image_url': raw_product.get('image_url') or raw_product.get('image_id'),
        'category': raw_product.get('category'),
        'decorators': raw_product.get('decorators', []),
    }


@products_bp.route('/search', methods=['GET'])
@require_auth
def search_products():
    """Search for products."""
    query = request.args.get('q', '')
    category = request.args.get('category')

    if not query:
        return jsonify({
            'query': '',
            'results': [],
            'in_cart': {},
            'in_upcoming_order': {}
        })

    try:
        mcp = get_mcp_client()
        raw_results = mcp.search_products(query)

        # Handle different response formats
        if isinstance(raw_results, dict):
            products = raw_results.get('products', raw_results.get('items', []))
        elif isinstance(raw_results, list):
            products = raw_results
        else:
            products = []

        # Transform products
        results = [transform_product(p) for p in products]

        # Get current cart to show what's in cart
        in_cart = {}
        try:
            cart = mcp.get_cart()
            for item in cart.get('items', []):
                for actual in item.get('items', [item]):
                    quantity = 1
                    for dec in actual.get('decorators', []):
                        if dec.get('type') == 'QUANTITY':
                            quantity = dec.get('quantity', 1)
                            break
                    in_cart[actual.get('id')] = quantity
        except:
            pass

        # Get upcoming orders to show what's ordered
        in_upcoming_order = {}
        try:
            orders = mcp.call_tool('search_orders', {'query': query, 'scope': 'upcoming'})
            if orders and 'matches' in orders:
                for match in orders['matches']:
                    in_upcoming_order[match.get('productId')] = True
        except:
            pass

        return jsonify({
            'query': query,
            'results': results,
            'in_cart': in_cart,
            'in_upcoming_order': in_upcoming_order
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>', methods=['GET'])
@require_auth
def get_product(product_id):
    """Get single product details."""
    try:
        mcp = get_mcp_client()
        # Search for the specific product
        results = mcp.search_products(product_id)

        if isinstance(results, list) and len(results) > 0:
            for p in results:
                if p.get('id') == product_id:
                    return jsonify(transform_product(p))

        return jsonify({'error': 'Product not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories():
    """Get product categories."""
    try:
        mcp = get_mcp_client()
        categories = mcp.get_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
