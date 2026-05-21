# Quick Start Guide

Get Shopsphere running in 5 minutes!

## Prerequisites
- Python 3.8+
- MySQL 8.0+
- Git

## Installation

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/shopsphere.git
cd shopsphere
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
mysql -u root -p < schema_updated.sql
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
nano .env
```

### 5. Run
```bash
python app.py
```

Visit http://localhost:5000

## Quick Test Accounts

### User Account
- **Username**: user
- **Password**: password123

### Admin Access
- **Password Parameter**: `?password=admin123`

## First Steps

1. **Register** a new account
2. **Browse** products on home page
3. **Add items** to cart
4. **Checkout** to place an order
5. **Check** order history
6. **Leave reviews** on products

## Docker Quick Start

```bash
docker-compose up
```

That's it! Everything is running.

## Troubleshooting

### Port Already in Use
```bash
python app.py --port 5001
```

### MySQL Connection Error
- Check .env DB_HOST, DB_USER, DB_PASSWORD
- Ensure MySQL service is running
- Verify database exists

### Template Not Found
- Ensure all files in `templates/` directory
- Restart Flask app

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [CHANGELOG.md](CHANGELOG.md) for latest updates
- Explore [API endpoints](README.md#-api-endpoints)
- Setup [Docker](README.md#-docker-setup)

## Need Help?

- Open an issue on GitHub
- Email: support@shopsphere.com
- Check existing issues for solutions
