import os
import traceback
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, make_response
from dotenv import load_dotenv
from functools import wraps

# Import auth service for PIN-based authentication
try:
    from services.auth import get_auth_service
    HAS_AUTH_SERVICE = True
except ImportError:
    HAS_AUTH_SERVICE = False

load_dotenv()

__version__ = "4.0.0"

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# MCP Server configuration
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:3000')

# Static files directory for React frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

# ============================================================================
# Register API v2 Blueprint
# ============================================================================
try:
    from api.v2 import api_v2
    app.register_blueprint(api_v2)
    print(f"API v2 blueprint registered")
except ImportError as e:
    print(f"Warning: Could not load API v2 blueprint: {e}")

# ============================================================================
# Initialize Database (if available)
# ============================================================================
try:
    from services.db import get_db
    db = get_db()
    db.init_db()
    print("Database initialized")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")

# ============================================================================
# Helper Functions (for legacy e-reader routes)
# ============================================================================

def call_mcp_tool(tool_name, arguments=None):
    """Call an MCP server tool via HTTP"""
    if arguments is None:
        arguments = {}

    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/call-tool",
            json={"name": tool_name, "arguments": arguments},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        # Extract text content from MCP response
        if 'content' in result and len(result['content']) > 0:
            content_text = result['content'][0].get('text', '')
            try:
                return json.loads(content_text) if content_text else {}
            except:
                return content_text
        return result
    except requests.RequestException as e:
        print(f'Error calling MCP tool {tool_name}: {str(e)}')
        raise Exception(f'MCP server error: {str(e)}')

def login_required(f):
    """Decorator to require login for legacy routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('pin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# React SPA Routes (Full Version)
# ============================================================================

@app.route('/')
def index():
    """Serve React app or redirect to legacy"""
    # Check for UI mode preference
    ui_mode = request.cookies.get('ui_mode', 'full')

    if ui_mode == 'ereader':
        # Redirect to legacy e-reader interface
        if session.get('logged_in'):
            return redirect(url_for('legacy_cart'))
        return redirect(url_for('pin_login'))

    # Serve React app
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_from_directory(STATIC_DIR, 'index.html')

    # Fallback to legacy if React not built
    if session.get('logged_in'):
        return redirect(url_for('legacy_cart'))
    return redirect(url_for('pin_login'))


@app.route('/app')
@app.route('/app/<path:path>')
def serve_spa(path=''):
    """Serve React SPA for all app routes"""
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_from_directory(STATIC_DIR, 'index.html')
    return redirect(url_for('index'))


@app.route('/assets/<path:path>')
def serve_assets(path):
    """Serve static assets from React build"""
    return send_from_directory(os.path.join(STATIC_DIR, 'assets'), path)


# ============================================================================
# Legacy E-Reader Routes (Simplified Interface)
# ============================================================================

@app.route('/legacy')
def legacy_index():
    """Legacy home page"""
    if session.get('logged_in'):
        return redirect(url_for('legacy_cart'))
    return redirect(url_for('pin_login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - redirects to PIN login for ereader mode"""
    # Redirect to PIN login (the new standard for ereader mode)
    return redirect(url_for('pin_login'))


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'success')
    # Check which mode to return to
    ui_mode = request.cookies.get('ui_mode', 'full')
    if ui_mode == 'ereader':
        return redirect(url_for('pin_login'))
    return redirect(url_for('index'))


@app.route('/switch-to-full', methods=['GET', 'POST'])
def switch_to_full_mode():
    """Switch from ereader mode to full mode"""
    response = make_response(redirect(url_for('index')))
    response.set_cookie('ui_mode', 'full', max_age=31536000)  # 1 year
    session.clear()  # Clear ereader session to require fresh login
    return response


@app.route('/pin-login', methods=['GET', 'POST'])
def pin_login():
    """PIN-based login for e-reader mode (uses same PIN as full mode)"""
    if request.method == 'POST':
        pin = request.form.get('pin', '')

        if not pin or not pin.isdigit() or len(pin) != 4:
            flash('Please enter a valid 4-digit PIN', 'error')
            return render_template('pin_login.html')

        if not HAS_AUTH_SERVICE:
            flash('Authentication service not available', 'error')
            return render_template('pin_login.html')

        try:
            # Get Picnic user ID from MCP server (same as full mode)
            try:
                from services.mcp_client import get_mcp_client
                mcp = get_mcp_client()
                user_data = mcp.get_user()
                picnic_user_id = user_data.get('user_id') or user_data.get('id') or 'default'
            except Exception:
                picnic_user_id = 'default-user'

            # Verify PIN using the same auth service as full mode
            auth_service = get_auth_service()
            result = auth_service.verify_pin(picnic_user_id, pin)

            if result.get('valid'):
                # Set session for ereader mode
                session['logged_in'] = True
                session['picnic_username'] = result['user'].get('display_name') or picnic_user_id
                session['picnic_user_id'] = picnic_user_id

                flash('Login successful!', 'success')
                return redirect(url_for('legacy_cart'))
            else:
                flash('Invalid PIN', 'error')

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            print(f'PIN login failed: {str(e)}')
            print(traceback.format_exc())
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('pin_login.html')


@app.route('/legacy/cart')
@login_required
def legacy_cart():
    """View shopping cart (legacy e-reader interface)"""
    try:
        print(f"Fetching cart for user: {session.get('picnic_username')}")
        cart_data = call_mcp_tool('get_cart')
        print(f"Cart data retrieved successfully")
        return render_template('cart.html', cart=cart_data)
    except Exception as e:
        print(f'Error loading cart: {str(e)}')
        print(traceback.format_exc())
        flash(f'Error loading cart: {str(e)}', 'error')
        return render_template('cart.html', cart=None)


# Keep /cart for backwards compatibility
@app.route('/cart')
@login_required
def cart():
    """Redirect to legacy cart or React app"""
    ui_mode = request.cookies.get('ui_mode', 'full')
    if ui_mode == 'ereader':
        return redirect(url_for('legacy_cart'))
    # For full mode, React handles /cart route
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_from_directory(STATIC_DIR, 'index.html')
    return redirect(url_for('legacy_cart'))


@app.route('/legacy/search')
@login_required
def legacy_search():
    """Search for products (legacy e-reader interface)"""
    query = request.args.get('q', '')
    results = []

    if query:
        try:
            print(f"Searching for: {query}")
            results = call_mcp_tool('search_products', {'query': query})
            print(f"Found {len(results) if results else 0} results")
        except Exception as e:
            print(f'Search error: {str(e)}')
            print(traceback.format_exc())
            flash(f'Search error: {str(e)}', 'error')

    return render_template('search.html', query=query, results=results)


# Keep /search for backwards compatibility
@app.route('/search')
@login_required
def search():
    """Redirect to legacy search or React app"""
    ui_mode = request.cookies.get('ui_mode', 'full')
    if ui_mode == 'ereader':
        return redirect(url_for('legacy_search', **request.args))
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_from_directory(STATIC_DIR, 'index.html')
    return redirect(url_for('legacy_search', **request.args))


@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart (legacy form submission)"""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    try:
        print(f"Adding product {product_id} (qty: {quantity}) to cart")
        call_mcp_tool('add_to_cart', {'productId': product_id, 'count': quantity})
        flash('Product added to cart!', 'success')
    except Exception as e:
        print(f'Error adding product: {str(e)}')
        print(traceback.format_exc())
        flash(f'Error adding product: {str(e)}', 'error')

    # Redirect back to search or cart
    if request.form.get('return_to') == 'search':
        return redirect(url_for('legacy_search', q=request.form.get('search_query', '')))
    return redirect(url_for('legacy_cart'))


@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove product from cart (legacy form submission)"""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    try:
        print(f"Removing product {product_id} (qty: {quantity}) from cart")
        call_mcp_tool('remove_from_cart', {'productId': product_id, 'count': quantity})
        flash('Product removed from cart', 'success')
    except Exception as e:
        print(f'Error removing product: {str(e)}')
        print(traceback.format_exc())
        flash(f'Error removing product: {str(e)}', 'error')

    return redirect(url_for('legacy_cart'))


@app.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart (legacy form submission)"""
    try:
        print("Clearing cart")
        call_mcp_tool('clear_cart')
        flash('Cart cleared', 'success')
    except Exception as e:
        print(f'Error clearing cart: {str(e)}')
        print(traceback.format_exc())
        flash(f'Error clearing cart: {str(e)}', 'error')

    return redirect(url_for('legacy_cart'))


# ============================================================================
# Utility Routes
# ============================================================================

@app.route('/version')
def version():
    """Return application version"""
    return jsonify({'version': __version__})


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'version': __version__})


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 - serve React app for client-side routing"""
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({'error': 'Not found'}), 404


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"Starting Picnic Cart App v{__version__} on {host}:{port}")
    print(f"MCP Server URL: {MCP_SERVER_URL}")
    print(f"Static files: {STATIC_DIR}")
    app.run(host=host, port=port, debug=True)
