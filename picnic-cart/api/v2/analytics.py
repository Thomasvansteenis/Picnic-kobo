"""Analytics API endpoints."""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

from services.auth import require_auth, get_current_user
from services.db import get_db
from services.analytics import get_analytics_service

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/frequency', methods=['GET'])
@require_auth
def get_frequency():
    """Get purchase frequency analysis."""
    user = get_current_user()
    min_purchases = request.args.get('min_purchases', 3, type=int)

    try:
        db = get_db()
        products = db.get_purchase_frequency(user['id'], min_purchases)

        # Convert to serializable format
        result = []
        for p in (products or []):
            result.append({
                'product_id': p.get('picnic_product_id'),
                'product_name': p.get('product_name'),
                'total_purchases': p.get('total_purchases'),
                'total_quantity': p.get('total_quantity'),
                'first_purchased': p.get('first_purchased').isoformat() if p.get('first_purchased') else None,
                'last_purchased': p.get('last_purchased').isoformat() if p.get('last_purchased') else None,
                'avg_days_between': float(p.get('avg_days_between', 0)),
                'confidence': float(p.get('confidence_score', 0)),
                'suggested_frequency': p.get('suggested_frequency')
            })

        return jsonify({
            'products': result,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting frequency: {e}")
        return jsonify({'products': [], 'error': str(e)})


@analytics_bp.route('/spending', methods=['GET'])
@require_auth
def get_spending():
    """Get spending analytics."""
    user = get_current_user()
    months = request.args.get('months', 6, type=int)

    try:
        db = get_db()
        monthly = db.get_monthly_spending(user['id'], months)

        # Calculate totals
        total = sum(m.get('total_spent', 0) or 0 for m in (monthly or []))

        # Get category breakdown
        analytics = get_analytics_service()
        categories = analytics.get_spending_by_category(user['id'], months)

        # Format monthly data
        monthly_data = []
        for m in (monthly or []):
            monthly_data.append({
                'month': m.get('month').isoformat() if m.get('month') else None,
                'order_count': m.get('order_count', 0),
                'total_spent': m.get('total_spent', 0),
                'total_items': m.get('total_items', 0)
            })

        # Format category data
        category_data = []
        for c in (categories or []):
            category_data.append({
                'category': c.get('category'),
                'total_spent': c.get('total_spent', 0),
                'item_count': c.get('item_count', 0)
            })

        return jsonify({
            'monthly': monthly_data,
            'categories': category_data,
            'total': total
        })
    except Exception as e:
        logger.error(f"Error getting spending: {e}")
        return jsonify({
            'monthly': [],
            'categories': [],
            'total': 0,
            'error': str(e)
        })


@analytics_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions():
    """Get smart product suggestions."""
    user = get_current_user()

    try:
        db = get_db()
        frequency = db.get_purchase_frequency(user['id'], min_purchases=3)

        due_for_reorder = []
        now = datetime.utcnow()

        for product in (frequency or []):
            if product.get('last_purchased') and product.get('avg_days_between'):
                last = product['last_purchased']
                if isinstance(last, str):
                    last = datetime.fromisoformat(last.replace('Z', '+00:00'))

                avg_days = float(product['avg_days_between'])
                expected_next = last + timedelta(days=avg_days)

                if expected_next < now:
                    days_overdue = (now - expected_next).days
                    due_for_reorder.append({
                        'product_id': product['picnic_product_id'],
                        'product_name': product['product_name'],
                        'days_overdue': days_overdue,
                        'avg_days_between': avg_days,
                        'confidence': float(product.get('confidence_score', 0))
                    })

        # Sort by most overdue first
        due_for_reorder.sort(key=lambda x: x['days_overdue'], reverse=True)

        # Get recurring list suggestions
        analytics = get_analytics_service()
        recurring = analytics.suggest_recurring_list(user['id'])

        return jsonify({
            'due_for_reorder': due_for_reorder[:10],
            'recurring_suggestions': recurring,
            'frequently_bought_together': []  # TODO: Implement association rules
        })

    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return jsonify({
            'due_for_reorder': [],
            'recurring_suggestions': {'weekly': [], 'biweekly': [], 'monthly': []},
            'frequently_bought_together': [],
            'error': str(e)
        })


@analytics_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_analytics():
    """Refresh analytics by syncing orders and recalculating frequencies."""
    user = get_current_user()

    try:
        analytics = get_analytics_service()

        # Sync orders from Picnic API
        sync_result = analytics.sync_orders(user['id'])

        # Recalculate purchase frequencies
        calc_result = analytics.calculate_purchase_frequency(user['id'])

        return jsonify({
            'success': True,
            'orders_synced': sync_result.get('synced', 0),
            'items_synced': sync_result.get('items_synced', 0),
            'frequencies_calculated': calc_result.get('calculated', 0),
            'sync_error': sync_result.get('error'),
            'calc_error': calc_result.get('error')
        })

    except Exception as e:
        logger.error(f"Error refreshing analytics: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/top-products', methods=['GET'])
@require_auth
def get_top_products():
    """Get top purchased products."""
    user = get_current_user()
    limit = request.args.get('limit', 20, type=int)

    try:
        analytics = get_analytics_service()
        products = analytics.get_top_products(user['id'], limit)

        result = []
        for p in (products or []):
            result.append({
                'product_id': p.get('picnic_product_id'),
                'product_name': p.get('product_name'),
                'total_quantity': p.get('total_quantity'),
                'order_count': p.get('order_count'),
                'last_ordered': p.get('last_ordered').isoformat() if p.get('last_ordered') else None
            })

        return jsonify({'products': result})

    except Exception as e:
        logger.error(f"Error getting top products: {e}")
        return jsonify({'products': [], 'error': str(e)})


@analytics_bp.route('/sync', methods=['POST'])
@require_auth
def sync_orders():
    """Sync order history from Picnic API."""
    user = get_current_user()

    try:
        analytics = get_analytics_service()
        result = analytics.sync_orders(user['id'])

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error syncing orders: {e}")
        return jsonify({'error': str(e)}), 500
