-- Shopsphere Database Schema
-- Enhanced version with reviews, wishlist, and additional features

-- Users Table
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username)
);

-- Products Table
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(255),
    stock_quantity INT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_name (name),
    FULLTEXT INDEX ft_search (name, description)
);

-- Orders Table
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Placed',
    user_order_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Order Items Table
DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    size VARCHAR(20),
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    INDEX idx_order_id (order_id)
);

-- Reviews Table (NEW)
DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating),
    UNIQUE KEY unique_review (product_id, user_id)
);

-- Wishlist Table (NEW)
DROP TABLE IF EXISTS wishlist;
CREATE TABLE wishlist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    UNIQUE KEY unique_wishlist (user_id, product_id)
);

-- Sample Products Data
INSERT INTO products (name, description, category, price, image_url, stock_quantity, is_featured, rating) VALUES
('Classic Blue Jeans', 'Comfortable and stylish blue jeans perfect for everyday wear', 'Jeans', 2499, '/static/images/blue-jeans.jpg', 50, 1, 4.5),
('White T-Shirt', 'Pure cotton white t-shirt, perfect for casual styling', 'T-Shirts', 799, '/static/images/white-tshirt.jpg', 100, 1, 4.3),
('Black Formal Shirt', 'Professional black formal shirt for business occasions', 'Shirts', 1899, '/static/images/formal-shirt.jpg', 45, 1, 4.6),
('Navy Hoodie', 'Cozy navy hoodie for cold weather', 'Hoodies', 2299, '/static/images/navy-hoodie.jpg', 60, 1, 4.4),
('Gray Sweater', 'Soft gray sweater for layering', 'Sweaters', 1799, '/static/images/gray-sweater.jpg', 40, 0, 4.2),
('Khaki Shorts', 'Comfortable khaki shorts for summer', 'Shorts', 999, '/static/images/khaki-shorts.jpg', 75, 0, 4.1),
('Running Shoes', 'Professional running shoes with good grip', 'Shoes', 4999, '/static/images/running-shoes.jpg', 30, 1, 4.7),
('Casual Sneakers', 'Stylish casual sneakers for everyday use', 'Shoes', 3499, '/static/images/sneakers.jpg', 50, 0, 4.5),
('Leather Jacket', 'Premium leather jacket for a sophisticated look', 'Jackets', 7999, '/static/images/leather-jacket.jpg', 20, 1, 4.8),
('Denim Jacket', 'Classic denim jacket, timeless style', 'Jackets', 2999, '/static/images/denim-jacket.jpg', 35, 0, 4.3);
