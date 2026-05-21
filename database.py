"""
Database Connection and Helper Functions
"""
import mysql.connector
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            auth_plugin='caching_sha2_password',
            autocommit=False
        )
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """
    Execute a SELECT query and return results
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
        fetch_one: If True, return only first result
        fetch_all: If True, return all results
    
    Returns:
        Query result(s) or None
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        
        return result
    except mysql.connector.Error as err:
        logger.error(f"Query execution error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def execute_update(query, params=None):
    """
    Execute an INSERT, UPDATE, or DELETE query
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
    
    Returns:
        lastrowid for INSERT, or affected rows count
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Update execution error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
