#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -e

bashio::log.info "Starting Picnic Shopping Cart add-on..."

# Read configuration from add-on options
FLASK_SECRET_KEY=$(bashio::config 'flask_secret_key')

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

# Export environment variables
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY}"
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

# Start the Flask application
cd /app || exit 1
exec python3 app.py
