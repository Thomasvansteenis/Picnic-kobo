import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from python_picnic_api import PicnicAPI
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Store Picnic API instance in session context
def get_picnic_api():
    """Get or create Picnic API instance for current session"""
    if 'picnic_username' in session and 'picnic_password' in session:
        try:
            api = PicnicAPI(
                username=session['picnic_username'],
                password=session['picnic_password'],
                country_code=session.get('picnic_country', 'NL')
            )
            return api
        except Exception as e:
            print(f'Error connecting to Picnic API: {str(e)}')
            print(traceback.format_exc())
            flash(f'Picnic authentication error: {str(e)}', 'error')
            return None
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
            # Test connection
            print(f"Attempting login for user: {username} in country: {country}")
            api = PicnicAPI(username=username, password=password, country_code=country)

            # Test API by trying to get cart (validates authentication)
            try:
                api.get_cart()
                print("Login successful - cart retrieved")
            except Exception as cart_error:
                print(f"Cart retrieval test failed: {str(cart_error)}")
                raise Exception(f"Authentication test failed: {str(cart_error)}")

            # Store in session
            session['picnic_username'] = username
            session['picnic_password'] = password
            session['picnic_country'] = country
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

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=True)
