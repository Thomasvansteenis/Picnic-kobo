#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: Picnic Shopping Cart
# ==============================================================================

# Read configuration
FLASK_SECRET_KEY=$(bashio::config 'flask_secret_key')

# Log startup
echo "[INFO] Starting Picnic Shopping Cart add-on..."

# Validate secret key
if [ "$FLASK_SECRET_KEY" = "change-this-to-a-random-secret-key-minimum-32-characters-long" ]; then
    echo "[WARNING] You are using the default secret key!"
    echo "[WARNING] Please change it in the add-on configuration for better security."
fi

# Export environment variables
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY}"
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

# Log ready state
echo "[INFO] Starting Flask application on port 5000..."

# Start the Flask application
cd /app || exit 1
exec python3 app.py
