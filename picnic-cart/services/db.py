"""Database service for MariaDB connection and operations."""

import os
import logging
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

try:
    import pymysql
    from pymysql.cursors import DictCursor
    HAS_MARIADB = True
except ImportError:
    HAS_MARIADB = False

logger = logging.getLogger(__name__)


class DatabaseService:
    """MariaDB database service for Home Assistant MariaDB addon."""

    def __init__(self):
        self.enabled = os.getenv('DB_ENABLED', 'false').lower() == 'true'
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'core-mariadb'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_NAME', 'picnic'),
            'user': os.getenv('DB_USER', 'picnic'),
            'password': os.getenv('DB_PASSWORD', ''),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor if HAS_MARIADB else None,
        }
        self._connection = None

    @contextmanager
    def get_cursor(self):
        """Get a database cursor with automatic connection management."""
        if not HAS_MARIADB:
            logger.warning("PyMySQL not installed, database operations disabled")
            yield None
            return

        if not self.enabled:
            yield None
            return

        conn = None
        try:
            conn = pymysql.connect(**self.connection_params)
            cursor = conn.cursor()
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
        """Initialize database with schema - creates tables if they don't exist."""
        if not HAS_MARIADB:
            logger.warning("Database initialization skipped - PyMySQL not installed")
            return

        if not self.enabled:
            logger.info("Database disabled, skipping initialization")
            return

        logger.info("Checking and creating database tables if needed...")

        # Read and execute the schema file
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

        # Split by semicolon and execute each statement separately
        # (MariaDB doesn't support multiple statements in one execute by default)
        statements = [s.strip() for s in schema.split(';') if s.strip()]

        with self.get_cursor() as cursor:
            if cursor:
                for statement in statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                        except pymysql.err.OperationalError as e:
                            # Ignore "already exists" errors for CREATE TABLE IF NOT EXISTS
                            if e.args[0] not in (1050, 1061, 1062):  # Table/index already exists
                                logger.warning(f"SQL warning: {e}")
                        except Exception as e:
                            logger.warning(f"SQL statement warning: {e}")
                logger.info("Database schema initialized/verified")

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

            # Use INSERT ... ON DUPLICATE KEY UPDATE for MariaDB
            cursor.execute(
                """INSERT INTO users (id, picnic_user_id, pin_hash, display_name, email, created_at, updated_at)
                   VALUES (UUID(), %s, %s, %s, %s, NOW(), NOW())
                   ON DUPLICATE KEY UPDATE
                       pin_hash = COALESCE(VALUES(pin_hash), pin_hash),
                       display_name = COALESCE(VALUES(display_name), display_name),
                       email = COALESCE(VALUES(email), email),
                       updated_at = NOW()""",
                (picnic_user_id, pin_hash, display_name, email)
            )
            # Fetch the user after upsert
            cursor.execute(
                "SELECT * FROM users WHERE picnic_user_id = %s",
                (picnic_user_id,)
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
                    "INSERT INTO failed_pin_attempts (id, user_id, attempted_at) VALUES (UUID(), %s, NOW())",
                    (user_id,)
                )

    def get_recent_failed_attempts(self, user_id: str, minutes: int = 15) -> int:
        """Get count of failed attempts in the last N minutes."""
        with self.get_cursor() as cursor:
            if not cursor:
                return 0
            cursor.execute(
                """SELECT COUNT(*) as count FROM failed_pin_attempts
                   WHERE user_id = %s AND attempted_at > DATE_SUB(NOW(), INTERVAL %s MINUTE)""",
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
            # Get lists first
            cursor.execute(
                """SELECT * FROM recurring_lists
                   WHERE user_id = %s AND is_active = 1
                   ORDER BY created_at DESC""",
                (user_id,)
            )
            lists = cursor.fetchall()

            # Get items for each list
            for lst in lists:
                cursor.execute(
                    """SELECT * FROM recurring_list_items
                       WHERE list_id = %s
                       ORDER BY sort_order""",
                    (lst['id'],)
                )
                lst['items'] = cursor.fetchall()

            return lists

    def create_recurring_list(self, user_id: str, data: Dict) -> Dict:
        """Create a new recurring list."""
        with self.get_cursor() as cursor:
            if not cursor:
                return {}
            list_id = None
            cursor.execute("SELECT UUID() as new_id")
            list_id = cursor.fetchone()['new_id']

            cursor.execute(
                """INSERT INTO recurring_lists
                   (id, user_id, name, description, frequency, custom_days, is_auto_generated, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
                (
                    list_id,
                    user_id,
                    data['name'],
                    data.get('description'),
                    data.get('frequency', 'weekly'),
                    data.get('custom_days'),
                    1 if data.get('is_auto_generated', False) else 0
                )
            )
            cursor.execute("SELECT * FROM recurring_lists WHERE id = %s", (list_id,))
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
                   (id, user_id, picnic_order_id, order_status, delivery_date,
                    delivery_slot_start, delivery_slot_end, total_price,
                    total_items, order_data, created_at, synced_at)
                   VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                   ON DUPLICATE KEY UPDATE
                       order_status = VALUES(order_status),
                       order_data = VALUES(order_data),
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
                    json.dumps(order_data)
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
                   ORDER BY CASE WHEN avg_days_between IS NULL THEN 1 ELSE 0 END, avg_days_between ASC""",
                (user_id, min_purchases)
            )
            return cursor.fetchall()

    def get_monthly_spending(self, user_id: str, months: int = 6) -> List[Dict]:
        """Get monthly spending summary."""
        with self.get_cursor() as cursor:
            if not cursor:
                return []
            cursor.execute(
                """SELECT
                       user_id,
                       DATE_FORMAT(delivery_date, '%%Y-%%m-01') AS month,
                       COUNT(*) AS order_count,
                       SUM(total_price) AS total_spent,
                       SUM(total_items) AS total_items
                   FROM order_cache
                   WHERE user_id = %s AND order_status = 'COMPLETED'
                   GROUP BY user_id, DATE_FORMAT(delivery_date, '%%Y-%%m-01')
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
