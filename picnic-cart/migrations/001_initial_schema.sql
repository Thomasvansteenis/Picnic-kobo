-- ============================================================================
-- PICNIC WEBAPP DATABASE SCHEMA
-- MariaDB compatible schema for Home Assistant MariaDB addon
-- ============================================================================

-- ============================================================================
-- TABLE: users (local app users, not Picnic accounts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY,
    picnic_user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    pin_hash VARCHAR(255),
    access_token VARCHAR(512),
    token_expires_at DATETIME,
    preferences JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_users_picnic_id (picnic_user_id),
    INDEX idx_users_token (access_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: failed_pin_attempts (rate limiting)
-- ============================================================================
CREATE TABLE IF NOT EXISTS failed_pin_attempts (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_failed_attempts_user (user_id, attempted_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: order_cache (cached order history for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_cache (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    picnic_order_id VARCHAR(255) NOT NULL,
    order_status VARCHAR(50),
    delivery_date DATETIME,
    delivery_slot_start DATETIME,
    delivery_slot_end DATETIME,
    total_price INT,
    total_items INT,
    order_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_order_cache_unique (user_id, picnic_order_id),
    INDEX idx_order_cache_user_date (user_id, delivery_date),
    INDEX idx_order_cache_status (order_status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: order_items (denormalized items for efficient searching)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id CHAR(36) PRIMARY KEY,
    order_id CHAR(36),
    user_id CHAR(36),
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    quantity INT NOT NULL,
    unit_price INT,
    total_price INT,
    unit_quantity VARCHAR(100),
    image_url VARCHAR(500),
    category VARCHAR(255),
    delivery_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_items_user_product (user_id, picnic_product_id),
    INDEX idx_order_items_user_date (user_id, delivery_date),
    FULLTEXT INDEX idx_order_items_search (product_name),
    FOREIGN KEY (order_id) REFERENCES order_cache(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: recurring_lists
-- ============================================================================
CREATE TABLE IF NOT EXISTS recurring_lists (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(50) DEFAULT 'weekly',
    custom_days INT,
    is_auto_generated TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    last_added_to_cart DATETIME,
    reminder_enabled TINYINT(1) DEFAULT 0,
    reminder_days_before INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_recurring_lists_user (user_id, is_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: recurring_list_items
-- ============================================================================
CREATE TABLE IF NOT EXISTS recurring_list_items (
    id CHAR(36) PRIMARY KEY,
    list_id CHAR(36),
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    default_quantity INT DEFAULT 1,
    unit_quantity VARCHAR(100),
    last_price INT,
    image_url VARCHAR(500),
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_list_product_unique (list_id, picnic_product_id),
    INDEX idx_recurring_list_items_list (list_id, sort_order),
    FOREIGN KEY (list_id) REFERENCES recurring_lists(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: purchase_frequency (materialized analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS purchase_frequency (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    total_purchases INT DEFAULT 0,
    total_quantity INT DEFAULT 0,
    first_purchased DATETIME,
    last_purchased DATETIME,
    avg_days_between DECIMAL(10,2),
    confidence_score DECIMAL(5,4),
    suggested_frequency VARCHAR(50),
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_user_product_unique (user_id, picnic_product_id),
    INDEX idx_purchase_frequency_user (user_id, avg_days_between),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: recipe_history
-- ============================================================================
CREATE TABLE IF NOT EXISTS recipe_history (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    source_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(1000),
    source_text TEXT,
    recipe_title VARCHAR(500),
    parsed_ingredients JSON,
    matched_products JSON,
    items_added_to_cart INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_recipe_history_user (user_id, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLE: app_settings
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36),
    ui_mode VARCHAR(20) DEFAULT 'full',
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'nl',
    notifications_enabled TINYINT(1) DEFAULT 1,
    sound_enabled TINYINT(1) DEFAULT 0,
    session_timeout_minutes INT DEFAULT 30,
    show_product_images TINYINT(1) DEFAULT 1,
    compact_cart_view TINYINT(1) DEFAULT 0,
    default_search_mode VARCHAR(20) DEFAULT 'products',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_app_settings_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
