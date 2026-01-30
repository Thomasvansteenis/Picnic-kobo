#!/usr/bin/with-contenv bashio

# ==============================================================================
# Home Assistant Add-on: Picnic Shopping Cart
# Runs the Picnic cart Flask application
# ==============================================================================

bashio::log.info "Starting Picnic Shopping Cart add-on..."

# Read configuration from add-on options
export FLASK_SECRET_KEY=$(bashio::config 'flask_secret_key')
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

# Validate secret key
if [ "$FLASK_SECRET_KEY" = "change-this-to-a-random-secret-key-minimum-32-characters-long" ]; then
    bashio::log.warning "================================================"
    bashio::log.warning "You are using the default secret key!"
    bashio::log.warning "Please change it in the add-on configuration"
    bashio::log.warning "for better security."
    bashio::log.warning "================================================"
fi

bashio::log.info "Secret key configured"
bashio::log.info "Starting Flask application on port 5000..."

# Start the Flask application
exec python3 /app/app.py
