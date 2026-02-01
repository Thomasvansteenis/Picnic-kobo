-- ============================================================================
-- PICNIC WEBAPP DATABASE SCHEMA
-- PostgreSQL with optional TimescaleDB extension
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: users (local app users, not Picnic accounts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    picnic_user_id VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    pin_hash VARCHAR(255),
    access_token VARCHAR(512),
    token_expires_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_token ON users(access_token) WHERE token_expires_at > NOW();
CREATE INDEX IF NOT EXISTS idx_users_picnic_id ON users(picnic_user_id);

-- ============================================================================
-- TABLE: failed_pin_attempts (rate limiting)
-- ============================================================================
CREATE TABLE IF NOT EXISTS failed_pin_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failed_attempts_user ON failed_pin_attempts(user_id, attempted_at);

-- ============================================================================
-- TABLE: order_cache (cached order history for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    picnic_order_id VARCHAR(255) NOT NULL,
    order_status VARCHAR(50),
    delivery_date TIMESTAMP WITH TIME ZONE,
    delivery_slot_start TIMESTAMP WITH TIME ZONE,
    delivery_slot_end TIMESTAMP WITH TIME ZONE,
    total_price INTEGER,
    total_items INTEGER,
    order_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, picnic_order_id)
);

CREATE INDEX IF NOT EXISTS idx_order_cache_user_date ON order_cache(user_id, delivery_date DESC);
CREATE INDEX IF NOT EXISTS idx_order_cache_status ON order_cache(order_status);

-- ============================================================================
-- TABLE: order_items (denormalized items for efficient searching)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES order_cache(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    product_name_search TSVECTOR,
    quantity INTEGER NOT NULL,
    unit_price INTEGER,
    total_price INTEGER,
    unit_quantity VARCHAR(100),
    image_url VARCHAR(500),
    category VARCHAR(255),
    delivery_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_items_user_product ON order_items(user_id, picnic_product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_user_date ON order_items(user_id, delivery_date DESC);
CREATE INDEX IF NOT EXISTS idx_order_items_search ON order_items USING GIN(product_name_search);

-- Trigger to auto-update search vector
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.product_name_search := to_tsvector('dutch', COALESCE(NEW.product_name, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_order_items_search ON order_items;
CREATE TRIGGER trg_order_items_search
    BEFORE INSERT OR UPDATE ON order_items
    FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();

-- ============================================================================
-- TABLE: recurring_lists
-- ============================================================================
CREATE TABLE IF NOT EXISTS recurring_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(50) DEFAULT 'weekly',
    custom_days INTEGER,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_added_to_cart TIMESTAMP WITH TIME ZONE,
    reminder_enabled BOOLEAN DEFAULT FALSE,
    reminder_days_before INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recurring_lists_user ON recurring_lists(user_id, is_active);

-- ============================================================================
-- TABLE: recurring_list_items
-- ============================================================================
CREATE TABLE IF NOT EXISTS recurring_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID REFERENCES recurring_lists(id) ON DELETE CASCADE,
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    default_quantity INTEGER DEFAULT 1,
    unit_quantity VARCHAR(100),
    last_price INTEGER,
    image_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(list_id, picnic_product_id)
);

CREATE INDEX IF NOT EXISTS idx_recurring_list_items_list ON recurring_list_items(list_id, sort_order);

-- ============================================================================
-- TABLE: purchase_frequency (materialized analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS purchase_frequency (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    picnic_product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    total_purchases INTEGER DEFAULT 0,
    total_quantity INTEGER DEFAULT 0,
    first_purchased TIMESTAMP WITH TIME ZONE,
    last_purchased TIMESTAMP WITH TIME ZONE,
    avg_days_between NUMERIC(10,2),
    confidence_score NUMERIC(5,4),
    suggested_frequency VARCHAR(50),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, picnic_product_id)
);

CREATE INDEX IF NOT EXISTS idx_purchase_frequency_user ON purchase_frequency(user_id, avg_days_between);

-- ============================================================================
-- TABLE: recipe_history
-- ============================================================================
CREATE TABLE IF NOT EXISTS recipe_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(1000),
    source_text TEXT,
    recipe_title VARCHAR(500),
    parsed_ingredients JSONB,
    matched_products JSONB,
    items_added_to_cart INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recipe_history_user ON recipe_history(user_id, created_at DESC);

-- ============================================================================
-- TABLE: app_settings
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    ui_mode VARCHAR(20) DEFAULT 'full',
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'nl',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    sound_enabled BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INTEGER DEFAULT 30,
    show_product_images BOOLEAN DEFAULT TRUE,
    compact_cart_view BOOLEAN DEFAULT FALSE,
    default_search_mode VARCHAR(20) DEFAULT 'products',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- VIEWS for analytics queries
-- ============================================================================

CREATE OR REPLACE VIEW monthly_spending AS
SELECT
    user_id,
    DATE_TRUNC('month', delivery_date) AS month,
    COUNT(*) AS order_count,
    SUM(total_price) AS total_spent,
    SUM(total_items) AS total_items
FROM order_cache
WHERE order_status = 'COMPLETED'
GROUP BY user_id, DATE_TRUNC('month', delivery_date)
ORDER BY month DESC;

CREATE OR REPLACE VIEW top_products AS
SELECT
    user_id,
    picnic_product_id,
    product_name,
    SUM(quantity) AS total_quantity,
    COUNT(*) AS order_count,
    MAX(delivery_date) AS last_ordered
FROM order_items
GROUP BY user_id, picnic_product_id, product_name
ORDER BY total_quantity DESC;
