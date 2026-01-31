#!/bin/bash
set -e

echo "===================================="
echo "Picnic MCP Server Add-on"
echo "===================================="

# Read configuration from Home Assistant
CONFIG_FILE="/data/options.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Reading configuration..."
    PICNIC_USERNAME=$(jq -r '.picnic_username // ""' "$CONFIG_FILE")
    PICNIC_PASSWORD=$(jq -r '.picnic_password // ""' "$CONFIG_FILE")
    PICNIC_COUNTRY_CODE=$(jq -r '.picnic_country // "NL"' "$CONFIG_FILE")
    HTTP_PORT=$(jq -r '.http_port // 3000' "$CONFIG_FILE")
    HTTP_HOST=$(jq -r '.http_host // "0.0.0.0"' "$CONFIG_FILE")
else
    echo "WARNING: Configuration file not found"
    exit 1
fi

# Validate required configuration
if [ -z "$PICNIC_USERNAME" ] || [ -z "$PICNIC_PASSWORD" ]; then
    echo "ERROR: Picnic username and password are required!"
    echo "Please configure them in the add-on settings."
    echo "DEBUG: PICNIC_USERNAME='$PICNIC_USERNAME'"
    echo "DEBUG: PICNIC_PASSWORD length: ${#PICNIC_PASSWORD}"
    exit 1
fi

# Export environment variables
export PICNIC_USERNAME
export PICNIC_PASSWORD
export PICNIC_COUNTRY_CODE
export HTTP_PORT
export HTTP_HOST
export ENABLE_HTTP_SERVER="true"

echo "Configuration loaded successfully"
echo "Username: $PICNIC_USERNAME"
echo "Password length: ${#PICNIC_PASSWORD} characters"
echo "Country: $PICNIC_COUNTRY_CODE"
echo "HTTP Server: http://$HTTP_HOST:$HTTP_PORT"
echo "===================================="
echo "Starting MCP Server..."
echo "DEBUG: Environment check before starting Node:"
echo "  PICNIC_USERNAME is set: $([ -n "$PICNIC_USERNAME" ] && echo 'yes' || echo 'no')"
echo "  PICNIC_PASSWORD is set: $([ -n "$PICNIC_PASSWORD" ] && echo 'yes' || echo 'no')"

# Start the MCP server
cd /app
exec node dist/index.js
