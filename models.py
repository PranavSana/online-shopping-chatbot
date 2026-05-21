"""
Data Models
"""
from database import execute_query, execute_update
from utils import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)

class User:
    """User Model"""
    
    @staticmethod
    def create(username, password, email=None, phone=None):
        """Create a new user"""
        password_hash = hash_password(password)
        query = """
            INSERT INTO users (username, password, email, phone, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        result = execute_update(query, (username, password_hash, email, phone))
        return result

    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = %s"
        return execute_query(query, (username,), fetch_one=True)

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        return execute_query(query, (user_id,), fetch_one=True)

    @staticmethod
    def verify_login(username, password):
        """Verify user credentials"""
        user = User.get_by_username(username)
        if user and verify_password(user['password'], password):
            return user
        return None

    @staticmethod
    def username_exists(username):
        """Check if username already exists"""
        user = User.get_by_username(username)
        return user is not None

    @staticmethod
    def update_profile(user_id, **kwargs):
        """Update user profile"""
        allowed_fields = ['email', 'phone', 'address', 'city', 'state', 'zip_code']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s"
        return execute_update(query, tuple(values)) is not None

class Product:
    """Product Model"""
    
    @staticmethod
    def get_all(limit=None):
        """Get all products"""
        query = "SELECT * FROM products"
        if limit:
            query += f" LIMIT {limit}"
        return execute_query(query, fetch_all=True)

    @staticmethod
    def get_by_id(product_id):
        """Get product by ID"""
        query = "SELECT * FROM products WHERE id = %s"
        return execute_query(query, (product_id,), fetch_one=True)

    @staticmethod
    def search(search_term):
        """Search products by name, description, or category"""
        search_term = f"%{search_term}%"
        query = """
            SELECT * FROM products 
            WHERE name LIKE %s OR description LIKE %s OR category LIKE %s
        """
        return execute_query(query, (search_term, search_term, search_term), fetch_all=True)

    @staticmethod
    def get_by_category(category):
        """Get products by category"""
        query = "SELECT * FROM products WHERE category = %s"
        return execute_query(query, (category,), fetch_all=True)

    @staticmethod
    def get_by_price_range(min_price, max_price):
        """Get products within price range"""
        query = "SELECT * FROM products WHERE price BETWEEN %s AND %s"
        return execute_query(query, (min_price, max_price), fetch_all=True)

    @staticmethod
    def get_featured(limit=6):
        """Get featured products"""
        query = "SELECT * FROM products WHERE is_featured = 1 LIMIT %s"
        return execute_query(query, (limit,), fetch_all=True)

class Order:
    """Order Model"""
    
    @staticmethod
    def create(user_id, total_amount, shipping_address, payment_method):
        """Create a new order"""
        query = """
            INSERT INTO orders (user_id, total_amount, shipping_address, payment_method, status, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        return execute_update(query, (user_id, total_amount, shipping_address, payment_method, 'Placed'))

    @staticmethod
    def get_user_orders(user_id):
        """Get all orders for a user"""
        query = "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC"
        return execute_query(query, (user_id,), fetch_all=True)

    @staticmethod
    def get_by_id(order_id):
        """Get order by ID"""
        query = "SELECT * FROM orders WHERE id = %s"
        return execute_query(query, (order_id,), fetch_one=True)

    @staticmethod
    def update_status(order_id, status):
        """Update order status"""
        query = "UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s"
        return execute_update(query, (status, order_id)) is not None

    @staticmethod
    def cancel(order_id):
        """Cancel an order"""
        return Order.update_status(order_id, 'Cancelled')

class Review:
    """Product Review Model"""
    
    @staticmethod
    def create(product_id, user_id, rating, comment):
        """Create a new review"""
        query = """
            INSERT INTO reviews (product_id, user_id, rating, comment, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        return execute_update(query, (product_id, user_id, rating, comment)) is not None

    @staticmethod
    def get_product_reviews(product_id):
        """Get all reviews for a product"""
        query = """
            SELECT r.*, u.username FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.created_at DESC
        """
        return execute_query(query, (product_id,), fetch_all=True)

    @staticmethod
    def get_average_rating(product_id):
        """Get average rating for a product"""
        query = "SELECT AVG(rating) as avg_rating FROM reviews WHERE product_id = %s"
        result = execute_query(query, (product_id,), fetch_one=True)
        return result['avg_rating'] if result and result['avg_rating'] else 0

class Wishlist:
    """Wishlist Model"""
    
    @staticmethod
    def add(user_id, product_id):
        """Add product to wishlist"""
        query = """
            INSERT INTO wishlist (user_id, product_id, created_at)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE created_at = NOW()
        """
        return execute_update(query, (user_id, product_id)) is not None

    @staticmethod
    def remove(user_id, product_id):
        """Remove product from wishlist"""
        query = "DELETE FROM wishlist WHERE user_id = %s AND product_id = %s"
        return execute_update(query, (user_id, product_id)) is not None

    @staticmethod
    def get_user_wishlist(user_id):
        """Get all wishlist items for a user"""
        query = """
            SELECT p.* FROM products p
            JOIN wishlist w ON p.id = w.product_id
            WHERE w.user_id = %s
            ORDER BY w.created_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True)

    @staticmethod
    def is_wishlisted(user_id, product_id):
        """Check if product is in user's wishlist"""
        query = "SELECT 1 FROM wishlist WHERE user_id = %s AND product_id = %s LIMIT 1"
        return execute_query(query, (user_id, product_id), fetch_one=True) is not None
