#!/bin/bash
set -e

echo "===================================="
echo "Picnic Shopping Cart Add-on"
echo "===================================="

# Read configuration from Home Assistant
CONFIG_FILE="/data/options.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Reading configuration..."
    FLASK_SECRET_KEY=$(jq -r '.flask_secret_key // "change-this-to-a-random-secret-key-minimum-32-characters-long"' "$CONFIG_FILE")
    MCP_SERVER_URL=$(jq -r '.mcp_server_url // "http://localhost:3000"' "$CONFIG_FILE")
else
    echo "WARNING: Configuration file not found, using defaults"
    FLASK_SECRET_KEY="change-this-to-a-random-secret-key-minimum-32-characters-long"
    MCP_SERVER_URL="http://localhost:3000"
fi

# Validate secret key
if [ "$FLASK_SECRET_KEY" = "change-this-to-a-random-secret-key-minimum-32-characters-long" ]; then
    echo "WARNING: Using default secret key!"
    echo "WARNING: Please change it in the add-on configuration for security."
fi

# Export environment variables
export FLASK_SECRET_KEY
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
export MCP_SERVER_URL

echo "Configuration loaded"
echo "Starting Flask application on port 5000..."
echo "===================================="

# Start Flask app
cd /app
exec python3 app.py
