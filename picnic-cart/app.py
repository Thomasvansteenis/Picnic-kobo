import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from python_picnic_api import PicnicAPI
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

__version__ = "2.0.3"

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Cache for Picnic API instances to avoid re-authentication on every request
_api_cache = {}

# Store Picnic API instance in session context
def get_picnic_api():
    """Get or create Picnic API instance for current session"""
    if 'picnic_username' not in session or 'picnic_password' not in session:
        return None

    username = session['picnic_username']
    cache_key = f"{username}:{session.get('picnic_country', 'NL')}"

    # Return cached instance if available
    if cache_key in _api_cache:
        return _api_cache[cache_key]

    # Create new instance and cache it
    try:
        print(f"Creating new PicnicAPI instance for {username}")
        api = PicnicAPI(
            username=username,
            password=session['picnic_password'],
            country_code=session.get('picnic_country', 'NL')
        )
        _api_cache[cache_key] = api
        return api
    except Exception as e:
        print(f'Error connecting to Picnic API: {str(e)}')
        print(traceback.format_exc())
        flash(f'Picnic authentication error: {str(e)}', 'error')
        return None

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
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        country = request.form.get('country', 'NL')

        try:
            # Test connection - PicnicAPI constructor validates credentials
            print(f"Attempting login for user: {username} in country: {country}")
            api = PicnicAPI(username=username, password=password, country_code=country)
            print("Login successful - credentials validated")

            # Store in session
            session['picnic_username'] = username
            session['picnic_password'] = password
            session['picnic_country'] = country

            # Cache the API instance to avoid re-authentication on every request
            cache_key = f"{username}:{country}"
            _api_cache[cache_key] = api
            print(f"Cached API instance for {cache_key}")

            flash('Login successful!', 'success')
            return redirect(url_for('cart'))
        except Exception as e:
            print(f'Login failed: {str(e)}')
            print(traceback.format_exc())
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    # Clear cached API instance
    if 'picnic_username' in session:
        cache_key = f"{session['picnic_username']}:{session.get('picnic_country', 'NL')}"
        if cache_key in _api_cache:
            del _api_cache[cache_key]
            print(f"Cleared API cache for {cache_key}")

    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/cart')
@login_required
def cart():
    """View shopping cart"""
    api = get_picnic_api()
    if not api:
        session.clear()
        return redirect(url_for('login'))

    try:
        print(f"Fetching cart for user: {session.get('picnic_username')}")
        cart_data = api.get_cart()
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
    api = get_picnic_api()

    if not api:
        session.clear()
        return redirect(url_for('login'))

    results = []
    if query:
        try:
            print(f"Searching for: {query}")
            results = api.search(query)
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

    api = get_picnic_api()
    if not api:
        session.clear()
        return redirect(url_for('login'))

    try:
        print(f"Adding product {product_id} (qty: {quantity}) to cart")
        api.add_product(product_id, quantity)
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

    api = get_picnic_api()
    if not api:
        session.clear()
        return redirect(url_for('login'))

    try:
        print(f"Removing product {product_id} (qty: {quantity}) from cart")
        api.remove_product(product_id, quantity)
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
    api = get_picnic_api()
    if not api:
        session.clear()
        return redirect(url_for('login'))

    try:
        print("Clearing cart")
        api.clear_cart()
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
