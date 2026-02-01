"""Analytics API endpoints."""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

from services.auth import require_auth, get_current_user
from services.db import get_db

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

        return jsonify({
            'products': products,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
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
        total = sum(m.get('total_spent', 0) for m in monthly)

        # TODO: Get category breakdown
        categories = []

        return jsonify({
            'monthly': monthly,
            'categories': categories,
            'total': total
        })
    except Exception as e:
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

        for product in frequency:
            if product.get('last_purchased') and product.get('avg_days_between'):
                last = product['last_purchased']
                if isinstance(last, str):
                    last = datetime.fromisoformat(last.replace('Z', '+00:00'))

                expected_next = last + timedelta(days=float(product['avg_days_between']))
                if expected_next < now:
                    days_overdue = (now - expected_next).days
                    due_for_reorder.append({
                        'product_id': product['picnic_product_id'],
                        'product_name': product['product_name'],
                        'days_overdue': days_overdue,
                        'avg_days_between': float(product['avg_days_between'])
                    })

        # Sort by most overdue first
        due_for_reorder.sort(key=lambda x: x['days_overdue'], reverse=True)

        return jsonify({
            'due_for_reorder': due_for_reorder[:10],
            'frequently_bought_together': []  # TODO: Implement
        })

    except Exception as e:
        return jsonify({
            'due_for_reorder': [],
            'frequently_bought_together': [],
            'error': str(e)
        })


@analytics_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_analytics():
    """Refresh analytics calculations."""
    user = get_current_user()

    try:
        # TODO: Recalculate purchase_frequency table
        # This would involve:
        # 1. Getting all order_items for user
        # 2. Calculating avg days between purchases per product
        # 3. Updating purchase_frequency table

        return jsonify({
            'success': True,
            'processed_orders': 0
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
