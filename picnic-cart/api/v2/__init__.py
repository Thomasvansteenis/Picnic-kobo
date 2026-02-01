"""API v2 Blueprint for the full-featured webapp."""

from flask import Blueprint

from .auth import auth_bp
from .cart import cart_bp
from .products import products_bp
from .orders import orders_bp
from .lists import lists_bp
from .recipes import recipes_bp
from .analytics import analytics_bp
from .settings import settings_bp

# Create main v2 blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# Register sub-blueprints
api_v2.register_blueprint(auth_bp)
api_v2.register_blueprint(cart_bp)
api_v2.register_blueprint(products_bp)
api_v2.register_blueprint(orders_bp)
api_v2.register_blueprint(lists_bp)
api_v2.register_blueprint(recipes_bp)
api_v2.register_blueprint(analytics_bp)
api_v2.register_blueprint(settings_bp)
