# 🛍️ Shopsphere - AI-Powered E-Commerce Platform

A modern, feature-rich e-commerce platform with intelligent shopping assistant, user profiles, wishlists, product reviews, and a comprehensive admin dashboard.

## ✨ Features

### 🎯 Core Features
- **User Authentication**: Secure registration and login with password hashing
- **Product Catalog**: Browse, search, and filter products by category and price
- **Shopping Cart**: Add/remove items, update quantities
- **Order Management**: Place orders, track status, cancel/return orders
- **User Profile**: Manage personal information and preferences
- **Wishlist**: Save favorite items for later
- **Product Reviews**: Rate and review products, view community reviews

### 🤖 Smart Shopping Assistant
- Natural language chatbot for product search
- Order status inquiries
- Shipping and return policy information
- Product recommendations and suggestions
- Real-time product filtering

### 👑 Admin Dashboard
- User management
- Order management and status updates
- Order analytics
- Secure admin authentication

### 🔐 Security Features
- Password hashing with Werkzeug
- Environment-based configuration
- SQL injection protection
- CSRF protection ready
- Session management

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip or conda

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/shopsphere.git
cd shopsphere
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
# Login to MySQL
mysql -u root -p

# Create database and tables
SOURCE schema_updated.sql;
```

5. **Configure environment**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## 📁 Project Structure

```
shopsphere/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── database.py           # Database connection and queries
├── models.py             # Data models (User, Product, Order, etc.)
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── schema_updated.sql    # Database schema
├── .env.example          # Environment variables template
├── static/
│   ├── css/
│   │   └── style.css     # Application styles
│   ├── js/
│   │   └── chatbot.js    # Chatbot functionality
│   └── images/           # Product images
├── templates/
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── home.html         # Product listing
│   ├── product_detail.html   # Product details & reviews
│   ├── profile.html      # User profile
│   ├── cart.html         # Shopping cart
│   ├── payment.html      # Payment page
│   ├── order_history.html    # Order history
│   ├── wishlist.html     # Wishlist
│   ├── 404.html          # Not found page
│   ├── 500.html          # Server error page
│   └── admin/            # Admin templates
│       ├── dashboard.html
│       └── orders.html
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=shopping_db

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Application
APP_NAME=Shopsphere
APP_URL=http://localhost:5000
```

## 📚 API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login user
- `GET /logout` - Logout user

### Products
- `GET /home` - List all products
- `GET /product/<id>` - Product details
- `POST /get_response` - Chatbot responses

### Shopping
- `POST /add_to_cart` - Add item to cart
- `GET /cart` - View cart
- `POST /update_quantity` - Update item quantity
- `POST /remove_from_cart` - Remove item

### Orders
- `POST /payment` - Create order
- `GET /order_history` - View orders
- `POST /cancel_order/<id>` - Cancel order

### Wishlist
- `GET /wishlist` - View wishlist
- `POST /wishlist/add/<id>` - Add to wishlist
- `POST /wishlist/remove/<id>` - Remove from wishlist

### Reviews
- `POST /review/add/<id>` - Add product review

### Admin
- `GET /admin` - Admin dashboard
- `GET /admin/orders` - View all orders
- `POST /admin/order/<id>/update_status` - Update order status

## 🛠️ Development

### Running with Debug Mode
```bash
FLASK_ENV=development FLASK_DEBUG=true python app.py
```

### Database Maintenance
```bash
# Backup database
mysqldump -u root -p shopping_db > backup.sql

# Restore database
mysql -u root -p shopping_db < backup.sql
```

## 🐳 Docker Setup

### Build and Run with Docker

```bash
# Build image
docker build -t shopsphere:latest .

# Run container
docker run -p 5000:5000 --env-file .env shopsphere:latest

# Run with Docker Compose
docker-compose up
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 📊 Database Schema

### Tables
- **users**: User accounts and profiles
- **products**: Product catalog
- **orders**: Customer orders
- **order_items**: Items in orders
- **reviews**: Product reviews and ratings
- **wishlist**: User wishlists

## 🔐 Security Notes

⚠️ **Important**: Before deploying to production:
1. Change all default passwords and secrets
2. Set `DEBUG=False` in production
3. Use strong `SECRET_KEY`
4. Configure HTTPS
5. Set up proper database backups
6. Implement rate limiting
7. Use environment variables for all sensitive data

## 🚀 Deployment

### Heroku Deployment
```bash
heroku create your-app-name
heroku addons:create cleardb:ignite
git push heroku main
```

### AWS Deployment
See `docs/deployment.md` for detailed AWS setup instructions.

## 📝 License

MIT License - see LICENSE file for details

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support, email support@shopsphere.com or open an issue on GitHub.

## 🎯 Roadmap

- [ ] Payment gateway integration (Stripe, Razorpay)
- [ ] Email notifications
- [ ] Advanced product filtering
- [ ] Recommendation engine
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Analytics dashboard
- [ ] Subscription products
- [ ] Inventory management system
- [ ] Third-party seller integration

## 🙏 Acknowledgments

- Flask documentation
- MySQL community
- Open-source contributors

---

**Made with ❤️ by Shopsphere Team**