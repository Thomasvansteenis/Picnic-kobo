import os
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
            flash(f'Error connecting to Picnic: {str(e)}', 'error')
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
            api = PicnicAPI(username=username, password=password, country_code=country)
            # Store in session
            session['picnic_username'] = username
            session['picnic_password'] = password
            session['picnic_country'] = country
            flash('Login successful!', 'success')
            return redirect(url_for('cart'))
        except Exception as e:
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
        return redirect(url_for('login'))

    try:
        cart_data = api.get_cart()
        return render_template('cart.html', cart=cart_data)
    except Exception as e:
        flash(f'Error loading cart: {str(e)}', 'error')
        return render_template('cart.html', cart=None)

@app.route('/search')
@login_required
def search():
    """Search for products"""
    query = request.args.get('q', '')
    api = get_picnic_api()

    if not api:
        return redirect(url_for('login'))

    results = []
    if query:
        try:
            results = api.search(query)
        except Exception as e:
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
        return redirect(url_for('login'))

    try:
        api.add_product(product_id, quantity)
        flash('Product added to cart!', 'success')
    except Exception as e:
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
        return redirect(url_for('login'))

    try:
        api.remove_product(product_id, quantity)
        flash('Product removed from cart', 'success')
    except Exception as e:
        flash(f'Error removing product: {str(e)}', 'error')

    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart"""
    api = get_picnic_api()
    if not api:
        return redirect(url_for('login'))

    try:
        api.clear_cart()
        flash('Cart cleared', 'success')
    except Exception as e:
        flash(f'Error clearing cart: {str(e)}', 'error')

    return redirect(url_for('cart'))

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=True)
