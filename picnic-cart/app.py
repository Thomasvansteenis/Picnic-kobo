import os
import traceback
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

__version__ = "3.0.0"

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# MCP Server configuration
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:3000')

# Helper function to call MCP server tools
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
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'picnic_username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page - redirect to login or cart"""
    if 'picnic_username' in session:
        return redirect(url_for('cart'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - Note: Authentication is handled by MCP server"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        country = request.form.get('country', 'NL')

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')

        try:
            # Check if MCP server is accessible
            print(f"Testing connection to MCP server at {MCP_SERVER_URL}")
            health_response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
            health_response.raise_for_status()
            print("MCP server is accessible")

            # Store in session (MCP server handles actual authentication)
            session['logged_in'] = True
            session['picnic_username'] = username
            session['picnic_country'] = country
            print(f"Session created for user: {username} in country: {country}")

            flash('Login successful!', 'success')
            return redirect(url_for('cart'))
        except requests.RequestException as e:
            print(f'MCP server connection failed: {str(e)}')
            print(traceback.format_exc())
            flash(f'Cannot connect to Picnic service. Please ensure the MCP server is running: {str(e)}', 'error')
        except Exception as e:
            print(f'Login failed: {str(e)}')
            print(traceback.format_exc())
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/cart')
@login_required
def cart():
    """View shopping cart"""
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

@app.route('/search')
@login_required
def search():
    """Search for products"""
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

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart"""
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
        return redirect(url_for('search', q=request.form.get('search_query', '')))
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove product from cart"""
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

    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart"""
    try:
        print("Clearing cart")
        call_mcp_tool('clear_cart')
        flash('Cart cleared', 'success')
    except Exception as e:
        print(f'Error clearing cart: {str(e)}')
        print(traceback.format_exc())
        flash(f'Error clearing cart: {str(e)}', 'error')

    return redirect(url_for('cart'))

@app.route('/version')
def version():
    """Return application version"""
    return jsonify({'version': __version__})

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"Starting Picnic Cart App v{__version__} on {host}:{port}")
    app.run(host=host, port=port, debug=True)
