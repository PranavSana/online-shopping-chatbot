

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
import mysql.connector
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Database Connection ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="4544",  # IMPORTANT: Replace with your MySQL password
    database="shopping_db",
    auth_plugin='caching_sha2_password'
)

# --- Context Processor to make variables globally available to templates ---
@app.context_processor
def inject_user_and_cart():
    cart_items = session.get('cart', [])
    total_quantity = sum(item.get('quantity', 1) for item in cart_items)
    return dict(
        username=session.get('username'),
        cart_count=total_quantity
    )

# --- Main User Routes ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cursor = db.cursor(dictionary=True)
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        cursor = db.cursor()
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            return render_template('register.html', error="Username already exists.")
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        cursor.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Shopping and Page Routes ---

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    cursor = db.cursor(dictionary=True)
    query = request.args.get('q', '').strip().lower()
    
    sql_query = "SELECT * FROM products"
    params = ()
    if query:
        search_query = f"%{query}%"
        sql_query += " WHERE name LIKE %s OR description LIKE %s OR category LIKE %s"
        params = (search_query, search_query, search_query)
        
    cursor.execute(sql_query, params)
    products = cursor.fetchall()
    cursor.close()
    return render_template('home.html', products=products)

@app.route('/cart')
def view_cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    cart_items_session = session.get('cart', [])
    detailed_cart_items = []
    total_amount = 0.0
    if cart_items_session:
        cursor = db.cursor(dictionary=True)
        product_ids = [item['product_id'] for item in cart_items_session]
        if product_ids:
            placeholders = ', '.join(['%s'] * len(product_ids))
            query = f"SELECT * FROM products WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(product_ids))
            products_from_db = {p['id']: p for p in cursor.fetchall()}
            cursor.close()
            for item in cart_items_session:
                product = products_from_db.get(item['product_id'])
                if product:
                    price = float(product['price'])
                    quantity = item.get('quantity', 1)
                    subtotal = price * quantity
                    total_amount += subtotal
                    detailed_cart_items.append({
                        'id': product['id'], 'name': product['name'], 'price': price,
                        'image_url': product['image_url'], 'size': item.get('size'),
                        'quantity': quantity
                    })
    return render_template('cart.html', cart_items=detailed_cart_items, total_amount=total_amount)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401
    data = request.get_json()
    product_id = int(data.get('product_id'))
    size = data.get('size')
    quantity = int(data.get('quantity', 1))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    if not product:
        return jsonify({"error": "Product not found"}), 404
    cart = session.get('cart', [])
    found = False
    for item in cart:
        if item['product_id'] == product_id and item.get('size') == size:
            item['quantity'] += quantity
            found = True
            break
    if not found:
        cart.append({
            'product_id': product_id, 'size': size,
            'quantity': quantity, 'price': float(product['price'])
        })
    session['cart'] = cart
    session.modified = True
    total_quantity = sum(item.get('quantity', 1) for item in cart)
    return jsonify({"message": f"Product added to cart!", "cart_count": total_quantity})

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    product_id = int(request.form['product_id'])
    size = request.form.get('size') or None
    quantity = int(request.form['quantity'])
    if quantity < 1: quantity = 1
    elif quantity > 10: quantity = 10
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id and item.get('size') == size:
            item['quantity'] = quantity
            break
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    size = request.form.get('size') or None
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if not (item['product_id'] == product_id and item.get('size') == size)]
    session.modified = True
    return redirect(url_for('view_cart'))

# --- Order Processing & History Routes ---

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('payment.html')
    address = request.form.get('address')
    payment_method = request.form.get('payment_method')
    if not address or not payment_method:
        flash('Please enter all required payment details.', 'error')
        return redirect(url_for('payment'))
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('view_cart'))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
    user_id = cursor.fetchone()['id']
    total_amount = sum(item['quantity'] * item['price'] for item in cart) + 120
    cursor.execute("SELECT MAX(user_order_number) FROM orders WHERE user_id = %s", (user_id,))
    last_number = cursor.fetchone()['MAX(user_order_number)'] or 0
    new_user_order_number = last_number + 1
    cursor.execute(
        "INSERT INTO orders (user_id, total_amount, shipping_address, payment_method, status, user_order_number) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, total_amount, address, payment_method, 'Placed', new_user_order_number)
    )
    order_id = cursor.lastrowid
    for item in cart:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, size, quantity, price) VALUES (%s, %s, %s, %s, %s)",
            (order_id, item['product_id'], item['size'], item['quantity'], item['price'])
        )
    db.commit()
    cursor.close()
    session.pop('cart', None)
    session.modified = True
    return redirect(url_for('payment', success='1'))

@app.route('/order_history')
def order_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
    user_id = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC", (user_id,))
    orders = cursor.fetchall()
    order_data = []
    for order in orders:
        now = datetime.now()
        order_date = order.get('order_date', now)
        can_cancel = (now < order_date + timedelta(days=2)) and order['status'] == 'Placed'
        is_delivered = order['status'] == 'Delivered'
        if not is_delivered and order['status'] == 'Shipped' and (now > order_date + timedelta(days=3)):
            is_delivered = True
        can_return = is_delivered and (now < order_date + timedelta(days=10))
        cursor.execute("SELECT oi.*, p.name, p.image_url FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s", (order['id'],))
        items = cursor.fetchall()
        order_data.append({'order': order, 'items': items, 'can_cancel': can_cancel, 'can_return': can_return})
    cursor.close()
    return render_template('order_history.html', order_data=order_data)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
    user_id = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
    order = cursor.fetchone()
    if order:
        now = datetime.now()
        order_date = order.get('order_date', now)
        if (now < order_date + timedelta(days=2)) and order['status'] == 'Placed':
            cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))
            db.commit()
            flash('Your order has been cancelled successfully.', 'success')
        else:
            flash('This order can no longer be cancelled.', 'error')
    else:
        flash('Order not found.', 'error')
    cursor.close()
    return redirect(url_for('order_history'))

@app.route('/return_order/<int:order_id>', methods=['GET', 'POST'])
def return_order(order_id):
    if 'username' not in session: return redirect(url_for('login'))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
    user_id = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
    order = cursor.fetchone()
    if not order:
        flash('Order not found.', 'error'); cursor.close(); return redirect(url_for('order_history'))
    if request.method == 'POST':
        cursor.execute("UPDATE orders SET status = 'Return Initiated' WHERE id = %s", (order_id,))
        db.commit(); flash('Your return request has been submitted.', 'success'); cursor.close(); return redirect(url_for('order_history'))
    now = datetime.now(); order_date = order.get('order_date', now)
    is_delivered = order['status'] == 'Delivered' or (order['status'] == 'Shipped' and now > order_date + timedelta(days=3))
    if not (is_delivered and (now < order_date + timedelta(days=10))):
        flash('This order is not eligible for return.', 'error'); cursor.close(); return redirect(url_for('order_history'))
    cursor.close()
    return render_template('return_form.html', order=order)

@app.route('/exchange_order/<int:order_id>', methods=['GET', 'POST'])
def exchange_order(order_id):
    if 'username' not in session: return redirect(url_for('login'))
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
    user_id = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
    order = cursor.fetchone()
    if not order:
        flash('Order not found.', 'error'); cursor.close(); return redirect(url_for('order_history'))
    if request.method == 'POST':
        cursor.execute("UPDATE orders SET status = 'Exchange Initiated' WHERE id = %s", (order_id,))
        db.commit(); flash('Your exchange request has been submitted.', 'success'); cursor.close(); return redirect(url_for('order_history'))
    now = datetime.now(); order_date = order.get('order_date', now)
    is_delivered = order['status'] == 'Delivered' or (order['status'] == 'Shipped' and now > order_date + timedelta(days=3))
    if not (is_delivered and (now < order_date + timedelta(days=10))):
        flash('This order is not eligible for exchange.', 'error'); cursor.close(); return redirect(url_for('order_history'))
    cursor.close()
    return render_template('exchange_form.html', order=order)

# --- Admin Routes ---

@app.route('/admin')
def admin_panel():
    if request.args.get('password') != 'secret': return "Unauthorized", 401
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username FROM users ORDER BY id")
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', users=users)

@app.route('/admin/user/<int:user_id>')
def admin_user_orders(user_id):
    if request.args.get('password') != 'secret': return "Unauthorized", 401
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user: cursor.close(); return "User not found", 404
    cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC", (user_id,))
    orders = cursor.fetchall()
    cursor.close()
    return render_template('admin_user_orders.html', orders=orders, user=user)

@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
def admin_update_status(order_id):
    if request.form.get('admin_password') != 'secret': return "Unauthorized", 401
    new_status = request.form.get('status')
    user_id = request.form.get('user_id')
    if new_status:
        cursor = db.cursor(); cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id)); db.commit(); cursor.close()
    return redirect(url_for('admin_user_orders', user_id=user_id, password='secret'))

@app.route('/admin/delete_order/<int:order_id>', methods=['POST'])
def admin_delete_order(order_id):
    if request.form.get('admin_password') != 'secret': return "Unauthorized", 401
    user_id = request.form.get('user_id')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if order:
        user_id_for_redirect = order['user_id']
        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        db.commit()
        flash(f"Order #{order_id} has been permanently deleted.", 'success')
        cursor.close()
        return redirect(url_for('admin_user_orders', user_id=user_id_for_redirect, password='secret'))
    flash('Order not found.', 'error')
    cursor.close()
    return redirect(url_for('admin_panel', password='secret'))

# --- Chatbot and Static Info Page Routes ---

@app.route('/get_response', methods=['POST'])
def chatbot():
    cursor = db.cursor(dictionary=True) 
    data = request.get_json()
    message = data.get('message', '').lower()
    reply = ""
    products_to_show = []

    if message in ['help', 'what can you do?']:
        reply = "I can help you with: <br>- Order status<br>- Return & shipping policies<br>- Suggest products (e.g., 'suggest shirts')<br>- Search for items (e.g., 'search for blue jeans')<br>- Filter by price (e.g., 'show me shoes under 3000')"
        return jsonify({"response": reply})

    search_match = re.search(r'search for\s(.+)', message)
    if search_match:
        search_term = search_match.group(1)
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{search_term}%",))
        products_to_show = cursor.fetchall()
        reply = f"Here is what I found for '{search_term}':" if products_to_show else f"Sorry, I couldn't find anything matching '{search_term}'."
        return jsonify({"response": reply, "products": products_to_show})

    price_match = re.search(r'(?:show|find|suggest)\s(?:me\s)?(\w+)\s(under|over|above|below)\s(\d+)', message)
    if price_match:
        category, comparison, price = price_match.groups()
        operator = '<' if comparison in ['under', 'below'] else '>'
        sql_query = f"SELECT * FROM products WHERE category = %s AND price {operator} %s"
        cursor.execute(sql_query, (category, price))
        products_to_show = cursor.fetchall()
        reply = f"Here are some {category} {comparison} ₹{price}:" if products_to_show else f"Sorry, no {category} found in that price range."
        return jsonify({"response": reply, "products": products_to_show})

    if message in ['hello', 'hi', 'hey']: reply = "Hello there! How can I help you today?"
    elif message in ['thanks', 'thank you']: reply = "You're welcome! Is there anything else I can help with?"
    elif message in ['bye', 'goodbye']: reply = "Goodbye! Have a great day."
    elif 'order status' in message or 'where is my order' in message:
        if 'username' in session:
            cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],)); user = cursor.fetchone()
            if user:
                cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC LIMIT 1", (user['id'],)); last_order = cursor.fetchone()
                reply = f"Your most recent order (# {last_order['user_order_number']}) has a status of: {last_order['status']}." if last_order else "It looks like you don't have any past orders."
            else: reply = "Sorry, I couldn't find your user details."
        else: reply = "You need to be logged in to check your order status."
    elif 'return policy' in message or 'how to return' in message:
        reply = "You can return most items within 30 days of delivery. For more details, please check our full Return Policy page from the footer."
    elif 'shipping' in message:
        reply = "We offer standard shipping (5-7 business days). Costs are calculated at checkout. For more details, see our Shipping Policy page."
    elif 'payment method' in message:
        reply = "We accept credit cards, debit cards, UPI, and cash on delivery."
    elif 'what\'s in my cart' in message or 'my cart' in message:
        cart = session.get('cart', []); reply = "Your cart is empty."
        if cart:
            items_desc = []; product_ids = [c['product_id'] for c in cart]; placeholders = ','.join(['%s']*len(product_ids))
            cursor.execute(f"SELECT id, name FROM products WHERE id IN ({placeholders})", tuple(product_ids)); products = {p['id']: p['name'] for p in cursor.fetchall()}
            for item in cart: items_desc.append(f"{item['quantity']} x {products.get(item['product_id'], 'Unknown Item')}")
            reply = "In your cart: " + ", ".join(items_desc)
    elif 'suggest' in message:
        category_match = re.search(r'suggest\s+(\w+)', message)
        if category_match:
            category = category_match.group(1); cursor.execute("SELECT * FROM products WHERE category=%s ORDER BY RAND() LIMIT 2", (category,)); products_to_show = cursor.fetchall()
            reply = f"Here are some {category} you might like:" if products_to_show else f"Sorry, I couldn't find any products in the '{category}' category."
        else: reply = "What category would you like suggestions for? (e.g., 'suggest shirts')"
    else:
        reply = "Sorry, I didn't understand that. You can ask 'help' to see what I can do."
    
    cursor.close()
    return jsonify({"response": reply, "products": products_to_show})

@app.route('/page/<page_name>')
def show_page(page_name):
    # This dictionary now contains the full, detailed content for all pages
    pages_content = {
        'about': {
            'title': 'About Shopsphere',
            'content': """
                <h4>Welcome to Shopsphere!</h4>
                <p>Shopsphere was founded on a simple idea: that shopping online should be easy, modern, and fun. We grew tired of navigating complicated websites and wanted to create a streamlined experience that connects you with the styles you love, without the hassle.</p>
                <h4>Our Mission</h4>
                <p>Our mission is to bring you a curated collection of high-quality apparel and accessories that fit your lifestyle. We believe in great design, fair prices, and a customer-first approach. From the products we select to the technology we build, every decision is made with you in mind.</p>
                <h4>The Shopsphere Experience</h4>
                <p>We are more than just a marketplace; we are a platform built on innovation. Our friendly Shopping Assistant is always here to help you find the perfect item, check on your cart, or answer any questions you might have. We are constantly working to improve your experience and make Shopsphere your favorite place to shop.</p>
                <p>Thank you for joining us on this journey. We're so excited to have you as part of our community!</p>
            """
        },
        'careers': {
            'title': 'Careers at Shopsphere',
            'content': '<p>We are not currently hiring, but please check back later for opportunities to join our innovative and growing team.</p>'
        },
        'press': {
            'title': 'Press Releases',
            'content': '<p>There are no press releases at this time. For media inquiries, please contact us at media@shopsphere.com.</p>'
        },
        'returns': {
            'title': 'Returns Centre',
            'content': '<p>To return an item, please go to "Your Account" > "Order History" and select the item you wish to return. Our system will guide you through the process.</p>'
        },
        'protection': {
            'title': '100% Purchase Protection',
            'content': '<p>We provide 100% purchase protection for your shopping. All transactions are secured, and we guarantee the authenticity and quality of our products. Your security is our priority.</p>'
        },
        'help': {
            'title': 'Help & Customer Service',
            'content': '<p>For any help, please contact our customer service at support@shopsphere.com. We are available 24/7 to assist you with your queries.</p>'
        },
        'privacy': {
            'title': 'Privacy Policy',
            'content': """
                <h4>1. Information We Collect</h4>
                <p>We collect information you provide directly to us, such as when you create an account, place an order, or contact customer service. This includes your name, email address, shipping address, and payment information.</p>
                <h4>2. How We Use Your Information</h4>
                <p>We use the information we collect to process your orders, communicate with you, and personalize your shopping experience. We may also use your information for marketing purposes, from which you can opt-out at any time.</p>
                <h4>3. Data Protection</h4>
                <p>We implement a variety of security measures to maintain the safety of your personal information. Your personal information is contained behind secured networks and is only accessible by a limited number of persons who have special access rights to such systems.</p>
            """
        },
        'return_policy': {
            'title': 'Return Policy',
            'content': """
                <h4>1. Return Window</h4>
                <p>You may return most new, unopened items within 30 days of delivery for a full refund. We'll also pay the return shipping costs if the return is a result of our error (you received an incorrect or defective item, etc.).</p>
                <h4>2. Conditions for Return</h4>
                <p>Items must be returned in their original product packaging, unworn, unwashed, and with all tags attached. Items that do not meet these criteria will not be considered for return.</p>
                <h4>3. How to Initiate a Return</h4>
                <p>To initiate a return, please visit our Returns Centre or contact customer support with your order number.</p>
            """
        },
        'shipping': {
            'title': 'Shipping Policy',
            'content': """
                <h4>1. Order Processing</h4>
                <p>All orders are processed within 1-2 business days. Orders are not shipped or delivered on weekends or holidays.</p>
                <h4>2. Shipping Rates & Delivery Estimates</h4>
                <p>Shipping charges for your order will be calculated and displayed at checkout. Standard shipping typically takes 5-7 business days, while expedited shipping takes 2-3 business days.</p>
                <h4>3. Shipment Confirmation & Order Tracking</h4>
                <p>You will receive a Shipment Confirmation email once your order has shipped containing your tracking number(s).</p>
            """
        },
        'terms': {
            'title': 'Terms of Service',
            'content': """
                <h4>1. Agreement to Terms</h4>
                <p>By using our website and services, you agree to be bound by these Terms of Service. If you disagree with any part of the terms, then you may not access the service.</p>
                <h4>2. User Accounts</h4>
                <p>When you create an account with us, you must provide us with information that is accurate, complete, and current at all times. You are responsible for safeguarding the password that you use to access the service.</p>
                <h4>3. Intellectual Property</h4>
                <p>The Service and its original content, features, and functionality are and will remain the exclusive property of Shopsphere and its licensors. Our trademarks and trade dress may not be used in connection with any product or service without the prior written consent of Shopsphere.</p>
            """
        }
    }
    
    page = pages_content.get(page_name)
    
    if page:
        return render_template('page.html', title=page['title'], content=page['content'])
    else:
        return "Page not found", 404

if __name__ == '__main__':
    app.run(debug=True)