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
            # Try both COMPLETED and ALL filters as API might not filter properly
            result = self.mcp_client.get_order_history(filter='ALL', limit=100)

            logger.info(f"Order history response: total={result.get('total', 'N/A')}, returned={result.get('returned', 'N/A')}")

            if not result or 'orders' not in result:
                # Check if orders are returned at top level (different API response format)
                if isinstance(result, list):
                    orders = result
                else:
                    return {'synced': 0, 'error': 'No orders returned from API'}
            else:
                orders = result.get('orders', [])

            synced = 0
            items_synced = 0

            for order in orders:
                order_id = order.get('id') or order.get('delivery_id')
                if not order_id:
                    logger.warning(f"Order without ID: {order.keys() if isinstance(order, dict) else type(order)}")
                    continue

                # Cache the order
                self.db.cache_order(user_id, order)
                synced += 1

                # Extract delivery time from multiple possible fields
                delivery_time = (
                    order.get('delivery_time') or
                    order.get('slot', {}).get('window_start') or
                    order.get('window_start') or
                    order.get('eta', {}).get('start') or
                    order.get('delivery_date')
                )

                # Extract and cache items
                items = self._extract_order_items(order)
                for item in items:
                    self._cache_order_item(user_id, order_id, item, delivery_time)
                    items_synced += 1

            logger.info(f"Synced {synced} orders with {items_synced} items")
            return {
                'synced': synced,
                'items_synced': items_synced,
                'total_available': result.get('total', synced) if isinstance(result, dict) else len(orders)
            }

        except Exception as e:
            logger.error(f"Failed to sync orders: {e}", exc_info=True)
            return {'synced': 0, 'error': str(e)}

    def _extract_order_items(self, order: Dict) -> List[Dict]:
        """Extract items from order data."""
        items = []

        # Handle different order structures from Picnic API
        order_items = order.get('items', [])

        # Some orders have nested structure under 'orders' key
        if not order_items and 'orders' in order:
            for sub_order in order.get('orders', []):
                order_items.extend(sub_order.get('items', []))

        # Try 'products' key as alternative
        if not order_items:
            order_items = order.get('products', [])

        # Try 'articles' key as alternative
        if not order_items:
            order_items = order.get('articles', [])

        for item in order_items:
            if not isinstance(item, dict):
                continue

            # Handle nested ORDER_LINE/ORDER_ARTICLE structure
            article = item
            item_type = item.get('type', '')
            if isinstance(item_type, str) and 'ORDER_LINE' in item_type:
                nested_items = item.get('items', [])
                if nested_items and isinstance(nested_items, list) and len(nested_items) > 0:
                    article = nested_items[0]

            # Extract product info with fallbacks for different API response formats
            product_id = (
                article.get('id') or
                article.get('product_id') or
                article.get('article_id')
            )
            product_name = (
                article.get('name') or
                article.get('product_name') or
                article.get('article_name', '')
            )
            quantity = (
                article.get('quantity') or
                article.get('count') or
                article.get('amount', 1)
            )

            if product_id or product_name:  # Only add if we have at least some info
                items.append({
                    'id': product_id,
                    'name': product_name,
                    'quantity': quantity,
                    'price': article.get('price') or article.get('unit_price'),
                    'unit_quantity': article.get('unit_quantity'),
                    'image_url': article.get('image_url') or article.get('image')
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
                    """INSERT IGNORE INTO order_items
                       (order_id, user_id, picnic_product_id, product_name,
                        quantity, unit_price, total_price, unit_quantity,
                        image_url, delivery_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                # Use GROUP_CONCAT for MariaDB (instead of PostgreSQL's ARRAY_AGG)
                cursor.execute(
                    """SELECT
                           picnic_product_id,
                           product_name,
                           COUNT(*) as purchase_count,
                           SUM(quantity) as total_quantity,
                           MIN(delivery_date) as first_purchased,
                           MAX(delivery_date) as last_purchased,
                           GROUP_CONCAT(delivery_date ORDER BY delivery_date SEPARATOR ',') as purchase_dates_str
                       FROM order_items
                       WHERE user_id = %s AND delivery_date IS NOT NULL
                       GROUP BY picnic_product_id, product_name
                       HAVING COUNT(*) >= 2""",
                    (user_id,)
                )
                products = cursor.fetchall()

                calculated = 0
                for product in products:
                    # Parse GROUP_CONCAT result (comma-separated dates string)
                    dates_str = product.get('purchase_dates_str', '')
                    dates = []
                    if dates_str:
                        for date_part in dates_str.split(','):
                            date_part = date_part.strip()
                            if date_part:
                                try:
                                    # Try to parse as date string or datetime
                                    if isinstance(date_part, str):
                                        dates.append(datetime.fromisoformat(date_part.replace(' ', 'T').split('.')[0]))
                                    else:
                                        dates.append(date_part)
                                except (ValueError, TypeError):
                                    continue

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

                            # Update purchase_frequency table (MariaDB syntax)
                            cursor.execute(
                                """INSERT INTO purchase_frequency
                                   (user_id, picnic_product_id, product_name,
                                    total_purchases, total_quantity, first_purchased,
                                    last_purchased, avg_days_between, confidence_score,
                                    suggested_frequency, calculated_at)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                   ON DUPLICATE KEY UPDATE
                                       product_name = VALUES(product_name),
                                       total_purchases = VALUES(total_purchases),
                                       total_quantity = VALUES(total_quantity),
                                       last_purchased = VALUES(last_purchased),
                                       avg_days_between = VALUES(avg_days_between),
                                       confidence_score = VALUES(confidence_score),
                                       suggested_frequency = VALUES(suggested_frequency),
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
                     AND delivery_date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
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
