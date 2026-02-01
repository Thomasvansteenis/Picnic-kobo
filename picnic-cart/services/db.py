"""Database service for PostgreSQL connection and operations."""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

logger = logging.getLogger(__name__)


class DatabaseService:
    """PostgreSQL database service."""

    def __init__(self):
        self.connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'picnic'),
            'user': os.getenv('POSTGRES_USER', 'picnic'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
        }
        self._connection = None

    @contextmanager
    def get_cursor(self):
        """Get a database cursor with automatic connection management."""
        if not HAS_POSTGRES:
            logger.warning("psycopg2 not installed, database operations disabled")
            yield None
            return

        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_db(self):
        """Initialize database with schema."""
        if not HAS_POSTGRES:
            logger.warning("Database initialization skipped - psycopg2 not installed")
            return

        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'migrations',
            '001_initial_schema.sql'
        )

        if not os.path.exists(schema_path):
            logger.warning(f"Schema file not found: {schema_path}")
            return

        with open(schema_path, 'r') as f:
            schema = f.read()

        with self.get_cursor() as cursor:
            if cursor:
                cursor.execute(schema)
                logger.info("Database schema initialized")

    # ========================================================================
    # User Operations
    # ========================================================================

    def get_user_by_picnic_id(self, picnic_user_id: str) -> Optional[Dict]:
        """Get user by Picnic user ID."""
        with self.get_cursor() as cursor:
            if not cursor:
                return None
            cursor.execute(
                "SELECT * FROM users WHERE picnic_user_id = %s",
                (picnic_user_id,)
            )
            return cursor.fetchone()

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by internal ID."""
        with self.get_cursor() as cursor:
            if not cursor:
                return None
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()

    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """Get user by access token."""
        with self.get_cursor() as cursor:
            if not cursor:
                return None
            cursor.execute(
                """SELECT * FROM users
                   WHERE access_token = %s AND token_expires_at > NOW()""",
                (token,)
            )
            return cursor.fetchone()

    def upsert_user(
        self,
        picnic_user_id: str,
        pin_hash: Optional[str] = None,
        display_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """Create or update user."""
        with self.get_cursor() as cursor:
            if not cursor:
                return {'id': 'mock-id', 'picnic_user_id': picnic_user_id}

            cursor.execute(
                """INSERT INTO users (picnic_user_id, pin_hash, display_name, email)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (picnic_user_id)
                   DO UPDATE SET
                       pin_hash = COALESCE(EXCLUDED.pin_hash, users.pin_hash),
                       display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                       email = COALESCE(EXCLUDED.email, users.email),
                       updated_at = NOW()
                   RETURNING *""",
                (picnic_user_id, pin_hash, display_name, email)
            )
            return cursor.fetchone()

    def update_user_token(
        self,
        user_id: str,
        token: str,
        expires_at: datetime
    ) -> None:
        """Update user's access token."""
        with self.get_cursor() as cursor:
            if cursor:
                cursor.execute(
                    """UPDATE users
                       SET access_token = %s, token_expires_at = %s, updated_at = NOW()
                       WHERE id = %s""",
                    (token, expires_at, user_id)
                )

    # ========================================================================
    # Failed PIN Attempts (Rate Limiting)
    # ========================================================================

    def record_failed_attempt(self, user_id: str) -> None:
        """Record a failed PIN attempt."""
        with self.get_cursor() as cursor:
            if cursor:
                cursor.execute(
                    "INSERT INTO failed_pin_attempts (user_id) VALUES (%s)",
                    (user_id,)
                )

    def get_recent_failed_attempts(self, user_id: str, minutes: int = 15) -> int:
        """Get count of failed attempts in the last N minutes."""
        with self.get_cursor() as cursor:
            if not cursor:
                return 0
            cursor.execute(
                """SELECT COUNT(*) as count FROM failed_pin_attempts
                   WHERE user_id = %s AND attempted_at > NOW() - INTERVAL '%s minutes'""",
                (user_id, minutes)
            )
            result = cursor.fetchone()
            return result['count'] if result else 0

    def clear_failed_attempts(self, user_id: str) -> None:
        """Clear failed attempts for a user."""
        with self.get_cursor() as cursor:
            if cursor:
                cursor.execute(
                    "DELETE FROM failed_pin_attempts WHERE user_id = %s",
                    (user_id,)
                )

    # ========================================================================
    # Recurring Lists
    # ========================================================================

    def get_recurring_lists(self, user_id: str) -> List[Dict]:
        """Get all recurring lists for a user."""
        with self.get_cursor() as cursor:
            if not cursor:
                return []
            cursor.execute(
                """SELECT rl.*,
                          COALESCE(json_agg(rli.*) FILTER (WHERE rli.id IS NOT NULL), '[]') as items
                   FROM recurring_lists rl
                   LEFT JOIN recurring_list_items rli ON rl.id = rli.list_id
                   WHERE rl.user_id = %s AND rl.is_active = true
                   GROUP BY rl.id
                   ORDER BY rl.created_at DESC""",
                (user_id,)
            )
            return cursor.fetchall()

    def create_recurring_list(self, user_id: str, data: Dict) -> Dict:
        """Create a new recurring list."""
        with self.get_cursor() as cursor:
            if not cursor:
                return {}
            cursor.execute(
                """INSERT INTO recurring_lists
                   (user_id, name, description, frequency, custom_days, is_auto_generated)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (
                    user_id,
                    data['name'],
                    data.get('description'),
                    data.get('frequency', 'weekly'),
                    data.get('custom_days'),
                    data.get('is_auto_generated', False)
                )
            )
            return cursor.fetchone()

    # ========================================================================
    # Order Cache & Analytics
    # ========================================================================

    def cache_order(self, user_id: str, order_data: Dict) -> None:
        """Cache an order for analytics."""
        with self.get_cursor() as cursor:
            if not cursor:
                return
            cursor.execute(
                """INSERT INTO order_cache
                   (user_id, picnic_order_id, order_status, delivery_date,
                    delivery_slot_start, delivery_slot_end, total_price,
                    total_items, order_data)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, picnic_order_id) DO UPDATE SET
                       order_status = EXCLUDED.order_status,
                       order_data = EXCLUDED.order_data,
                       synced_at = NOW()""",
                (
                    user_id,
                    order_data['id'],
                    order_data.get('status'),
                    order_data.get('delivery_date'),
                    order_data.get('delivery_slot_start'),
                    order_data.get('delivery_slot_end'),
                    order_data.get('total_price'),
                    order_data.get('total_items'),
                    psycopg2.extras.Json(order_data) if HAS_POSTGRES else str(order_data)
                )
            )

    def get_purchase_frequency(self, user_id: str, min_purchases: int = 3) -> List[Dict]:
        """Get purchase frequency data for a user."""
        with self.get_cursor() as cursor:
            if not cursor:
                return []
            cursor.execute(
                """SELECT * FROM purchase_frequency
                   WHERE user_id = %s AND total_purchases >= %s
                   ORDER BY avg_days_between ASC NULLS LAST""",
                (user_id, min_purchases)
            )
            return cursor.fetchall()

    def get_monthly_spending(self, user_id: str, months: int = 6) -> List[Dict]:
        """Get monthly spending summary."""
        with self.get_cursor() as cursor:
            if not cursor:
                return []
            cursor.execute(
                """SELECT * FROM monthly_spending
                   WHERE user_id = %s
                   ORDER BY month DESC
                   LIMIT %s""",
                (user_id, months)
            )
            return cursor.fetchall()


# Global instance
_db = None


def get_db() -> DatabaseService:
    """Get the database service singleton."""
    global _db
    if _db is None:
        _db = DatabaseService()
    return _db
