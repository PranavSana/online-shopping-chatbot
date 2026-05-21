"""
Shopsphere - Online Shopping Chatbot
A modern e-commerce platform with intelligent shopping assistant
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
from functools import wraps
import logging
import re
import os

# Import configuration and utilities
from config import Config, config
from database import get_db_connection, execute_query, execute_update
from models import User, Product, Order, Review, Wishlist
from utils import validate_username, validate_password, validate_email

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Context Processor ---
@app.context_processor
def inject_user_and_cart():
    """Make user and cart info available to all templates"""
    cart_items = session.get('cart', [])
    total_quantity = sum(item.get('quantity', 1) for item in cart_items)
    return dict(
        username=session.get('username'),
        user_id=session.get('user_id'),
        cart_count=total_quantity,
        app_name=Config.APP_NAME
    )

# --- Decorators ---
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_token = request.args.get('token') or request.form.get('admin_token')
        admin_password = request.args.get('password') or request.form.get('admin_password')
        
        if admin_password != Config.ADMIN_PASSWORD:
            return "Unauthorized", 401
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---

@app.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))
        
        user = User.verify_login(username, password)
        
        if user:
            session['username'] = user['username']
            session['user_id'] = user['id']
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=7)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not validate_username(username):
            flash('Username must be 3-20 characters (alphanumeric + underscore).', 'error')
            return redirect(url_for('register'))
        
        if not validate_password(password):
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))
        
        if email and not validate_email(email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('register'))
        
        if User.username_exists(username):
            flash('Username already exists. Try a different one.', 'error')
            return redirect(url_for('register'))
        
        # Create user
        try:
            User.create(username, password, email, phone)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    username = session.get('username')
    session.clear()
    if username:
        flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = User.get_by_id(session.get('user_id'))
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    
    return render_template('profile.html', user=user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    user_id = session.get('user_id')
    
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    zip_code = request.form.get('zip_code', '').strip()
    
    if email and not validate_email(email):
        flash('Invalid email format.', 'error')
        return redirect(url_for('profile'))
    
    try:
        User.update_profile(user_id, email=email, phone=phone, address=address, 
                           city=city, state=state, zip_code=zip_code)
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        flash('Error updating profile.', 'error')
    
    return redirect(url_for('profile'))

# --- Shopping Routes ---

@app.route('/home')
@login_required
def home():
    """Home page with products"""
    search_query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'newest')
    
    # Get products
    if search_query:
        products = Product.search(search_query)
    elif category:
        products = Product.get_by_category(category)
    else:
        products = Product.get_all()
    
    # Sort products
    if products:
        if sort == 'price_low':
            products = sorted(products, key=lambda x: x['price'])
        elif sort == 'price_high':
            products = sorted(products, key=lambda x: x['price'], reverse=True)
        elif sort == 'rating':
            products = sorted(products, key=lambda x: x.get('rating', 0), reverse=True)
    
    return render_template('home.html', products=products, search_query=search_query)

@app.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    """Product detail page"""
    product = Product.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('home'))
    
    user_id = session.get('user_id')
    reviews = Review.get_product_reviews(product_id)
    avg_rating = Review.get_average_rating(product_id)
    is_wishlisted = Wishlist.is_wishlisted(user_id, product_id) if user_id else False
    
    return render_template('product_detail.html', product=product, reviews=reviews, 
                         avg_rating=avg_rating, is_wishlisted=is_wishlisted)

@app.route('/cart')
@login_required
def view_cart():
    """View shopping cart"""
    cart_items_session = session.get('cart', [])
    detailed_cart_items = []
    total_amount = 0.0
    shipping = 120
    
    if cart_items_session:
        product_ids = [item['product_id'] for item in cart_items_session]
        if product_ids:
            placeholders = ', '.join(['%s'] * len(product_ids))
            query = f"SELECT * FROM products WHERE id IN ({placeholders})"
            products_from_db = execute_query(query, tuple(product_ids), fetch_all=True)
            products_dict = {p['id']: p for p in products_from_db}
            
            for item in cart_items_session:
                product = products_dict.get(item['product_id'])
                if product:
                    price = float(product['price'])
                    quantity = item.get('quantity', 1)
                    subtotal = price * quantity
                    total_amount += subtotal
                    detailed_cart_items.append({
                        'id': product['id'],
                        'name': product['name'],
                        'price': price,
                        'image_url': product['image_url'],
                        'size': item.get('size'),
                        'quantity': quantity
                    })
    
    return render_template('cart.html', cart_items=detailed_cart_items, 
                         subtotal=total_amount, shipping=shipping, total=total_amount + shipping)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart (AJAX)"""
    try:
        data = request.get_json()
        product_id = int(data.get('product_id'))
        size = data.get('size')
        quantity = int(data.get('quantity', 1))
        
        # Validate product exists
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Validate quantity
        if quantity < 1 or quantity > 10:
            quantity = 1
        
        # Add to cart
        cart = session.get('cart', [])
        found = False
        for item in cart:
            if item['product_id'] == product_id and item.get('size') == size:
                item['quantity'] = min(item['quantity'] + quantity, 10)
                found = True
                break
        
        if not found:
            cart.append({
                'product_id': product_id,
                'size': size,
                'quantity': quantity,
                'price': float(product['price'])
            })
        
        session['cart'] = cart
        session.modified = True
        
        total_quantity = sum(item.get('quantity', 1) for item in cart)
        return jsonify({
            "message": "Product added to cart!",
            "cart_count": total_quantity
        }), 200
    
    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    """Update item quantity in cart"""
    try:
        product_id = int(request.form.get('product_id'))
        size = request.form.get('size') or None
        quantity = int(request.form.get('quantity', 1))
        
        quantity = max(1, min(quantity, 10))
        
        cart = session.get('cart', [])
        for item in cart:
            if item['product_id'] == product_id and item.get('size') == size:
                item['quantity'] = quantity
                break
        
        session['cart'] = cart
        session.modified = True
        flash('Cart updated.', 'success')
    except Exception as e:
        logger.error(f"Update quantity error: {e}")
        flash('Error updating cart.', 'error')
    
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove item from cart"""
    try:
        product_id = int(request.form.get('product_id'))
        size = request.form.get('size') or None
        
        cart = session.get('cart', [])
        session['cart'] = [item for item in cart 
                          if not (item['product_id'] == product_id and item.get('size') == size)]
        session.modified = True
        flash('Item removed from cart.', 'success')
    except Exception as e:
        logger.error(f"Remove from cart error: {e}")
        flash('Error removing item.', 'error')
    
    return redirect(url_for('view_cart'))

# --- Wishlist Routes ---

@app.route('/wishlist')
@login_required
def view_wishlist():
    """View wishlist"""
    user_id = session.get('user_id')
    wishlist_items = Wishlist.get_user_wishlist(user_id)
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    try:
        user_id = session.get('user_id')
        if Wishlist.add(user_id, product_id):
            return jsonify({"message": "Added to wishlist!"}), 200
        return jsonify({"error": "Error adding to wishlist"}), 500
    except Exception as e:
        logger.error(f"Wishlist add error: {e}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Remove product from wishlist"""
    try:
        user_id = session.get('user_id')
        if Wishlist.remove(user_id, product_id):
            flash('Removed from wishlist.', 'success')
        return redirect(url_for('view_wishlist'))
    except Exception as e:
        logger.error(f"Wishlist remove error: {e}")
        flash('Error removing from wishlist.', 'error')
        return redirect(url_for('view_wishlist'))

# --- Payment & Orders ---

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    """Payment page"""
    if request.method == 'GET':
        return render_template('payment.html')
    
    try:
        user_id = session.get('user_id')
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        
        if not address or not payment_method:
            flash('Please enter all required payment details.', 'error')
            return redirect(url_for('payment'))
        
        cart = session.get('cart', [])
        if not cart:
            flash('Your cart is empty.', 'error')
            return redirect(url_for('view_cart'))
        
        # Calculate total
        shipping = 120
        subtotal = sum(item['quantity'] * item['price'] for item in cart)
        total_amount = subtotal + shipping
        
        # Create order
        order_id = Order.create(user_id, total_amount, address, payment_method)
        
        if order_id:
            # Add order items
            conn = get_db_connection()
            cursor = conn.cursor()
            for item in cart:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, size, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, item['product_id'], item['size'], item['quantity'], item['price'])
                )
            conn.commit()
            cursor.close()
            conn.close()
            
            # Clear cart
            session.pop('cart', None)
            session.modified = True
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
        else:
            flash('Error creating order.', 'error')
            return redirect(url_for('payment'))
    
    except Exception as e:
        logger.error(f"Payment error: {e}")
        flash('An error occurred during payment.', 'error')
        return redirect(url_for('payment'))

@app.route('/order_history')
@login_required
def order_history():
    """View order history"""
    user_id = session.get('user_id')
    orders = Order.get_user_orders(user_id)
    
    order_data = []
    for order in orders:
        now = datetime.now()
        order_date = order.get('created_at', now)
        
        # Check eligibility for actions
        can_cancel = (now < order_date + timedelta(days=2)) and order['status'] == 'Placed'
        is_delivered = order['status'] == 'Delivered'
        can_return = is_delivered and (now < order_date + timedelta(days=10))
        
        # Get order items
        query = """
            SELECT oi.*, p.name, p.image_url 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
        """
        items = execute_query(query, (order['id'],), fetch_all=True)
        
        order_data.append({
            'order': order,
            'items': items,
            'can_cancel': can_cancel,
            'can_return': can_return
        })
    
    return render_template('order_history.html', order_data=order_data)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """View order detail"""
    user_id = session.get('user_id')
    order = Order.get_by_id(order_id)
    
    if not order or order['user_id'] != user_id:
        flash('Order not found.', 'error')
        return redirect(url_for('order_history'))
    
    query = """
        SELECT oi.*, p.name, p.image_url 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        WHERE oi.order_id = %s
    """
    items = execute_query(query, (order_id,), fetch_all=True)
    
    return render_template('order_detail.html', order=order, items=items)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order"""
    try:
        user_id = session.get('user_id')
        order = Order.get_by_id(order_id)
        
        if not order or order['user_id'] != user_id:
            flash('Order not found.', 'error')
            return redirect(url_for('order_history'))
        
        now = datetime.now()
        order_date = order.get('created_at', now)
        
        if (now < order_date + timedelta(days=2)) and order['status'] == 'Placed':
            Order.cancel(order_id)
            flash('Order cancelled successfully.', 'success')
        else:
            flash('This order can no longer be cancelled.', 'error')
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        flash('Error cancelling order.', 'error')
    
    return redirect(url_for('order_history'))

# --- Reviews ---

@app.route('/review/add/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review"""
    try:
        user_id = session.get('user_id')
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            rating = 5
        
        if Review.create(product_id, user_id, rating, comment):
            flash('Review added successfully!', 'success')
        else:
            flash('Error adding review.', 'error')
    except Exception as e:
        logger.error(f"Add review error: {e}")
        flash('An error occurred.', 'error')
    
    return redirect(request.referrer or url_for('home'))

# --- Chatbot Route ---

@app.route('/get_response', methods=['POST'])
def chatbot():
    """Chatbot response handler"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower().strip()
        reply = ""
        products_to_show = []
        
        # Help command
        if message in ['help', 'what can you do?', '?']:
            reply = """I can help you with:
            <br>• Search for products (e.g., 'search for blue jeans')
            <br>• Filter by price (e.g., 'show me shirts under 3000')
            <br>• Suggest products (e.g., 'suggest shirts')
            <br>• Order status
            <br>• Shipping & return policies"""
            return jsonify({"response": reply})
        
        # Search functionality
        search_match = re.search(r'search (?:for\s)?(.+)', message)
        if search_match:
            search_term = search_match.group(1).strip()
            products_to_show = Product.search(search_term)
            reply = f"Found {len(products_to_show)} items for '{search_term}':" if products_to_show else f"Sorry, no items found for '{search_term}'."
            return jsonify({"response": reply, "products": [dict(p) for p in products_to_show]})
        
        # Price filter
        price_match = re.search(r'(?:show|find|suggest)\s(?:me\s)?(\w+)\s(?:under|over|below|above)\s([\d]+)', message)
        if price_match:
            category, price = price_match.groups()
            products_to_show = Product.get_by_price_range(0, int(price))
            reply = f"Here are items under ₹{price}:"
            return jsonify({"response": reply, "products": [dict(p) for p in products_to_show]})
        
        # Greeting
        if message in ['hello', 'hi', 'hey', 'hiya']:
            reply = "Hello! 👋 Welcome to Shopsphere. How can I help you find the perfect item today?"
        elif message in ['thanks', 'thank you']:
            reply = "You're welcome! Is there anything else I can help with?"
        elif message in ['bye', 'goodbye']:
            reply = "Goodbye! Happy shopping! 🛍️"
        elif 'order status' in message or 'where is my order' in message:
            if 'username' in session:
                user = User.get_by_id(session.get('user_id'))
                orders = Order.get_user_orders(user['id'])
                if orders:
                    last_order = orders[0]
                    reply = f"Your most recent order status: <strong>{last_order['status']}</strong>"
                else:
                    reply = "You don't have any orders yet."
            else:
                reply = "Please log in to check your order status."
        elif 'return policy' in message:
            reply = "Items can be returned within 10 days of delivery. They must be in original condition with tags attached."
        elif 'shipping' in message:
            reply = "Standard shipping is ₹120 and takes 5-7 business days. Express shipping available at checkout."
        elif 'payment' in message:
            reply = "We accept Credit/Debit Cards, UPI, NetBanking, and Cash on Delivery."
        elif 'suggest' in message:
            category_match = re.search(r'suggest\s+(\w+)', message)
            if category_match:
                category = category_match.group(1)
                query = f"SELECT * FROM products WHERE category = %s ORDER BY RAND() LIMIT 3"
                products_to_show = execute_query(query, (category,), fetch_all=True)
                reply = f"Here are some {category} you might like:" if products_to_show else f"Sorry, no {category} available."
                return jsonify({"response": reply, "products": [dict(p) for p in products_to_show]})
            else:
                reply = "What category are you interested in? (e.g., 'suggest shirts')"
        else:
            reply = "I didn't quite catch that. Try 'help' for available commands."
        
        return jsonify({"response": reply, "products": products_to_show})
    
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return jsonify({"response": "Sorry, I encountered an error. Please try again."}), 500

# --- Admin Routes ---

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin dashboard"""
    try:
        query = "SELECT id, username, email, created_at FROM users ORDER BY id DESC"
        users = execute_query(query, fetch_all=True)
        
        stats_query = "SELECT COUNT(*) as total FROM orders"
        stats = execute_query(stats_query, fetch_one=True)
        
        return render_template('admin/dashboard.html', users=users, stats=stats)
    except Exception as e:
        logger.error(f"Admin panel error: {e}")
        return "Error loading admin panel", 500

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """View all orders"""
    try:
        query = """
            SELECT o.*, u.username FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """
        orders = execute_query(query, fetch_all=True)
        return render_template('admin/orders.html', orders=orders)
    except Exception as e:
        logger.error(f"Admin orders error: {e}")
        return "Error loading orders", 500

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@admin_required
def admin_update_status(order_id):
    """Update order status"""
    try:
        status = request.form.get('status', '').strip()
        if Order.update_status(order_id, status):
            flash(f'Order status updated to {status}', 'success')
        else:
            flash('Error updating order status', 'error')
    except Exception as e:
        logger.error(f"Update status error: {e}")
        flash('Error updating status', 'error')
    
    return redirect(request.referrer or url_for('admin_orders', password=request.args.get('password')))

# --- Static Pages ---

@app.route('/page/<page_name>')
def show_page(page_name):
    """Display static pages"""
    pages_content = {
        'about': {
            'title': 'About Shopsphere',
            'content': """
                <h4>Welcome to Shopsphere!</h4>
                <p>Shopsphere is a modern, AI-powered e-commerce platform dedicated to bringing you quality products with exceptional customer service.</p>
                <h4>Our Mission</h4>
                <p>To provide a seamless shopping experience with cutting-edge technology and customer-first approach.</p>
                <h4>Why Choose Us?</h4>
                <ul>
                    <li>🤖 Intelligent Shopping Assistant</li>
                    <li>📦 Fast & Reliable Shipping</li>
                    <li>🔒 100% Secure Transactions</li>
                    <li>💚 Customer-First Approach</li>
                </ul>
            """
        },
        'careers': {
            'title': 'Careers',
            'content': '<p>Join our innovative team! Send your resume to careers@shopsphere.com</p>'
        },
        'returns': {
            'title': 'Returns & Refunds',
            'content': '''
                <p>We offer hassle-free returns within 10 days of delivery.</p>
                <ol>
                    <li>Visit your order history</li>
                    <li>Select the item to return</li>
                    <li>Follow the return process</li>
                    <li>Receive refund within 5-7 days</li>
                </ol>
            '''
        },
        'help': {
            'title': 'Help & Support',
            'content': '<p>Contact us at support@shopsphere.com or use our chatbot for instant assistance.</p>'
        },
        'privacy': {
            'title': 'Privacy Policy',
            'content': '<p>Your privacy is important to us. We use industry-standard security to protect your data.</p>'
        },
        'terms': {
            'title': 'Terms of Service',
            'content': '<p>By using Shopsphere, you agree to our terms and conditions. Use for lawful purposes only.</p>'
        }
    }
    
    page = pages_content.get(page_name)
    return render_template('page.html', title=page['title'], content=page['content']) if page else ("Page not found", 404)

# --- Error Handlers ---

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return render_template('500.html'), 500

# --- Main ---

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
