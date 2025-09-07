#!/usr/bin/env python3
"""
Database initialization script
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import init_database, test_connection, get_db_session
from app.database.migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Test connection first
    if not test_connection():
        logger.error("Database connection test failed")
        return False
    
    # Run migrations
    if not run_migrations():
        logger.error("Database migrations failed")
        return False
    
    # Initialize database with SQLAlchemy
    if not init_database():
        logger.error("Database initialization failed")
        return False
    
    # Create default data
    try:
        create_default_data()
    except Exception as e:
        logger.error(f"Failed to create default data: {e}")
        return False
    
    logger.info("Database initialization completed successfully!")
    return True

def create_default_data():
    """Create default data (tariff plans, etc.)"""
    logger.info("Creating default data...")
    
    try:
        from app.billing.services.subscription_service import SubscriptionService
        
        db = get_db_session()
        subscription_service = SubscriptionService(db)
        
        # Create default tariff plans if they don't exist
        subscription_service.create_default_tariff_plans()
        
        db.close()
        logger.info("Default data created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create default data: {e}")
        raise

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
