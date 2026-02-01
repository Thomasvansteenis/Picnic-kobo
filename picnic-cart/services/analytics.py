"""Analytics service for order syncing and purchase frequency calculation."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from .db import get_db
from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating purchase analytics."""

    def __init__(self):
        self.db = get_db()
        self.mcp_client = get_mcp_client()

    def sync_orders(self, user_id: str) -> Dict[str, Any]:
        """Sync order history from Picnic API to local cache."""
        try:
            # Get completed orders from Picnic
            result = self.mcp_client.get_order_history(filter='COMPLETED', limit=100)

            if not result or 'orders' not in result:
                return {'synced': 0, 'error': 'No orders returned from API'}

            orders = result.get('orders', [])
            synced = 0
            items_synced = 0

            for order in orders:
                order_id = order.get('id')
                if not order_id:
                    continue

                # Cache the order
                self.db.cache_order(user_id, order)
                synced += 1

                # Extract and cache items
                items = self._extract_order_items(order)
                for item in items:
                    self._cache_order_item(user_id, order_id, item, order.get('delivery_time'))
                    items_synced += 1

            return {
                'synced': synced,
                'items_synced': items_synced,
                'total_available': result.get('total', synced)
            }

        except Exception as e:
            logger.error(f"Failed to sync orders: {e}")
            return {'synced': 0, 'error': str(e)}

    def _extract_order_items(self, order: Dict) -> List[Dict]:
        """Extract items from order data."""
        items = []

        # Handle different order structures
        order_items = order.get('items', [])

        # Some orders have nested structure
        if not order_items and 'orders' in order:
            for sub_order in order['orders']:
                order_items.extend(sub_order.get('items', []))

        for item in order_items:
            # Handle nested ORDER_LINE/ORDER_ARTICLE structure
            article = item
            if 'ORDER_LINE' in item.get('type', ''):
                article = item.get('items', [{}])[0] if item.get('items') else item

            items.append({
                'id': article.get('id') or article.get('product_id'),
                'name': article.get('name') or article.get('product_name', ''),
                'quantity': article.get('quantity') or article.get('count', 1),
                'price': article.get('price'),
                'unit_quantity': article.get('unit_quantity'),
                'image_url': article.get('image_url')
            })

        return items

    def _cache_order_item(
        self,
        user_id: str,
        order_id: str,
        item: Dict,
        delivery_date: Optional[str]
    ) -> None:
        """Cache an order item for analytics."""
        with self.db.get_cursor() as cursor:
            if not cursor:
                return

            try:
                # First get the cached order UUID
                cursor.execute(
                    "SELECT id FROM order_cache WHERE user_id = %s AND picnic_order_id = %s",
                    (user_id, order_id)
                )
                order_row = cursor.fetchone()

                if not order_row:
                    return

                cursor.execute(
                    """INSERT INTO order_items
                       (order_id, user_id, picnic_product_id, product_name,
                        quantity, unit_price, total_price, unit_quantity,
                        image_url, delivery_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT DO NOTHING""",
                    (
                        order_row['id'],
                        user_id,
                        item.get('id'),
                        item.get('name'),
                        item.get('quantity', 1),
                        item.get('price'),
                        (item.get('price') or 0) * item.get('quantity', 1),
                        item.get('unit_quantity'),
                        item.get('image_url'),
                        delivery_date
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to cache order item: {e}")

    def calculate_purchase_frequency(self, user_id: str) -> Dict[str, Any]:
        """Calculate purchase frequency for all products."""
        with self.db.get_cursor() as cursor:
            if not cursor:
                return {'calculated': 0, 'error': 'Database not available'}

            try:
                # Get all order items grouped by product
                cursor.execute(
                    """SELECT
                           picnic_product_id,
                           product_name,
                           COUNT(*) as purchase_count,
                           SUM(quantity) as total_quantity,
                           MIN(delivery_date) as first_purchased,
                           MAX(delivery_date) as last_purchased,
                           ARRAY_AGG(delivery_date ORDER BY delivery_date) as purchase_dates
                       FROM order_items
                       WHERE user_id = %s AND delivery_date IS NOT NULL
                       GROUP BY picnic_product_id, product_name
                       HAVING COUNT(*) >= 2""",
                    (user_id,)
                )
                products = cursor.fetchall()

                calculated = 0
                for product in products:
                    dates = product.get('purchase_dates', [])

                    if len(dates) >= 2:
                        # Calculate average days between purchases
                        intervals = []
                        for i in range(1, len(dates)):
                            if dates[i] and dates[i-1]:
                                delta = dates[i] - dates[i-1]
                                intervals.append(delta.days)

                        if intervals:
                            avg_days = sum(intervals) / len(intervals)

                            # Calculate confidence based on consistency
                            if len(intervals) > 1:
                                variance = sum((x - avg_days) ** 2 for x in intervals) / len(intervals)
                                std_dev = variance ** 0.5
                                # Lower std_dev relative to avg_days = higher confidence
                                confidence = max(0, 1 - (std_dev / (avg_days + 1)))
                            else:
                                confidence = 0.5

                            # Determine suggested frequency
                            if avg_days <= 7:
                                suggested = 'weekly'
                            elif avg_days <= 14:
                                suggested = 'biweekly'
                            elif avg_days <= 30:
                                suggested = 'monthly'
                            else:
                                suggested = 'occasional'

                            # Update purchase_frequency table
                            cursor.execute(
                                """INSERT INTO purchase_frequency
                                   (user_id, picnic_product_id, product_name,
                                    total_purchases, total_quantity, first_purchased,
                                    last_purchased, avg_days_between, confidence_score,
                                    suggested_frequency, calculated_at)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                   ON CONFLICT (user_id, picnic_product_id)
                                   DO UPDATE SET
                                       product_name = EXCLUDED.product_name,
                                       total_purchases = EXCLUDED.total_purchases,
                                       total_quantity = EXCLUDED.total_quantity,
                                       last_purchased = EXCLUDED.last_purchased,
                                       avg_days_between = EXCLUDED.avg_days_between,
                                       confidence_score = EXCLUDED.confidence_score,
                                       suggested_frequency = EXCLUDED.suggested_frequency,
                                       calculated_at = NOW()""",
                                (
                                    user_id,
                                    product['picnic_product_id'],
                                    product['product_name'],
                                    product['purchase_count'],
                                    product['total_quantity'],
                                    product['first_purchased'],
                                    product['last_purchased'],
                                    avg_days,
                                    confidence,
                                    suggested
                                )
                            )
                            calculated += 1

                return {
                    'calculated': calculated,
                    'total_products': len(products)
                }

            except Exception as e:
                logger.error(f"Failed to calculate purchase frequency: {e}")
                return {'calculated': 0, 'error': str(e)}

    def get_top_products(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get top purchased products."""
        with self.db.get_cursor() as cursor:
            if not cursor:
                return []

            cursor.execute(
                """SELECT
                       picnic_product_id,
                       product_name,
                       SUM(quantity) as total_quantity,
                       COUNT(*) as order_count,
                       MAX(delivery_date) as last_ordered
                   FROM order_items
                   WHERE user_id = %s
                   GROUP BY picnic_product_id, product_name
                   ORDER BY total_quantity DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            return cursor.fetchall() or []

    def get_spending_by_category(self, user_id: str, months: int = 6) -> List[Dict]:
        """Get spending breakdown by category."""
        with self.db.get_cursor() as cursor:
            if not cursor:
                return []

            cursor.execute(
                """SELECT
                       COALESCE(category, 'Other') as category,
                       SUM(total_price) as total_spent,
                       COUNT(*) as item_count
                   FROM order_items
                   WHERE user_id = %s
                     AND delivery_date >= NOW() - INTERVAL '%s months'
                   GROUP BY category
                   ORDER BY total_spent DESC""",
                (user_id, months)
            )
            return cursor.fetchall() or []

    def suggest_recurring_list(self, user_id: str) -> Dict[str, Any]:
        """Suggest items for a recurring shopping list."""
        with self.db.get_cursor() as cursor:
            if not cursor:
                return {'items': []}

            # Get products with high purchase frequency and consistency
            cursor.execute(
                """SELECT
                       picnic_product_id,
                       product_name,
                       total_purchases,
                       avg_days_between,
                       confidence_score,
                       suggested_frequency
                   FROM purchase_frequency
                   WHERE user_id = %s
                     AND confidence_score >= 0.6
                     AND total_purchases >= 3
                   ORDER BY confidence_score DESC, total_purchases DESC
                   LIMIT 20""",
                (user_id,)
            )

            weekly = []
            biweekly = []
            monthly = []

            for row in cursor.fetchall() or []:
                item = {
                    'product_id': row['picnic_product_id'],
                    'product_name': row['product_name'],
                    'avg_days': float(row['avg_days_between']),
                    'confidence': float(row['confidence_score'])
                }

                if row['suggested_frequency'] == 'weekly':
                    weekly.append(item)
                elif row['suggested_frequency'] == 'biweekly':
                    biweekly.append(item)
                elif row['suggested_frequency'] == 'monthly':
                    monthly.append(item)

            return {
                'weekly': weekly,
                'biweekly': biweekly,
                'monthly': monthly
            }


# Global instance
_analytics_service = None


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
