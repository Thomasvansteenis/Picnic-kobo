#!/bin/bash
set -e

echo "===================================="
echo "Picnic Shopping Cart Add-on v4.0.0"
echo "Full-Featured Webapp"
echo "===================================="

# Read configuration from Home Assistant
CONFIG_FILE="/data/options.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Reading configuration..."
    FLASK_SECRET_KEY=$(jq -r '.flask_secret_key // "change-this-to-a-random-secret-key-minimum-32-characters-long"' "$CONFIG_FILE")
    MCP_SERVER_URL=$(jq -r '.mcp_server_url // "http://localhost:3000"' "$CONFIG_FILE")

    # MariaDB configuration (Home Assistant MariaDB addon)
    DB_HOST=$(jq -r '.db_host // ""' "$CONFIG_FILE")
    DB_PORT=$(jq -r '.db_port // "3306"' "$CONFIG_FILE")
    DB_NAME=$(jq -r '.db_name // "picnic"' "$CONFIG_FILE")
    DB_USER=$(jq -r '.db_user // "picnic"' "$CONFIG_FILE")
    DB_PASSWORD=$(jq -r '.db_password // ""' "$CONFIG_FILE")

    # JWT configuration
    JWT_SECRET=$(jq -r '.jwt_secret // ""' "$CONFIG_FILE")
    JWT_EXPIRY_HOURS=$(jq -r '.jwt_expiry_hours // "24"' "$CONFIG_FILE")

    # UI mode
    DEFAULT_UI_MODE=$(jq -r '.default_ui_mode // "full"' "$CONFIG_FILE")
else
    echo "WARNING: Configuration file not found, using defaults"
    FLASK_SECRET_KEY="change-this-to-a-random-secret-key-minimum-32-characters-long"
    MCP_SERVER_URL="http://localhost:3000"
    DB_HOST=""
    DB_PORT="3306"
    DB_NAME="picnic"
    DB_USER="picnic"
    DB_PASSWORD=""
    JWT_SECRET=""
    JWT_EXPIRY_HOURS="24"
    DEFAULT_UI_MODE="full"
fi

# Validate secret key
if [ "$FLASK_SECRET_KEY" = "change-this-to-a-random-secret-key-minimum-32-characters-long" ]; then
    echo "WARNING: Using default Flask secret key!"
    echo "WARNING: Please change it in the add-on configuration for security."
fi

# Generate JWT secret if not provided
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "INFO: Generated random JWT secret for this session"
fi

# Check database configuration
if [ -z "$DB_HOST" ]; then
    echo "INFO: No database configured, running in memory-only mode"
    echo "INFO: Analytics and recurring lists will not persist"
    echo ""
    echo "TIP: To enable persistence, install the MariaDB addon and configure:"
    echo "     - db_host: core-mariadb"
    echo "     - db_name: picnic"
    echo "     - db_user: your_mariadb_user"
    echo "     - db_password: your_mariadb_password"
    DB_ENABLED="false"
else
    echo "INFO: MariaDB database configured at $DB_HOST:$DB_PORT/$DB_NAME"
    echo "INFO: Tables will be created automatically if they don't exist"
    DB_ENABLED="true"
fi

# Export environment variables
export FLASK_SECRET_KEY
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
export MCP_SERVER_URL
export DB_HOST
export DB_PORT
export DB_NAME
export DB_USER
export DB_PASSWORD
export DB_ENABLED
export JWT_SECRET
export JWT_EXPIRY_HOURS
export DEFAULT_UI_MODE

echo ""
echo "Configuration Summary:"
echo "  - MCP Server: $MCP_SERVER_URL"
echo "  - Database: $( [ "$DB_ENABLED" = "true" ] && echo "MariaDB ($DB_HOST:$DB_PORT)" || echo "Disabled (in-memory mode)" )"
echo "  - Default UI Mode: $DEFAULT_UI_MODE"
echo ""
echo "Starting Flask application on port 5000..."
echo "===================================="

# Start Flask app
cd /app
exec python3 app.py
