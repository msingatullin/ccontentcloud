"""
Database connection and initialization
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Global variables
engine = None
SessionLocal = None

def get_database_url():
    """Get database URL from environment variables"""
    # Check for explicit DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # For production, use Cloud SQL or external database
    if os.getenv('ENVIRONMENT') == 'production':
        db_name = os.getenv('DB_NAME', 'content_curator')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_host = os.getenv('DB_HOST', 'localhost')
        
        # Cloud SQL Unix socket connection (for Cloud Run)
        # DB_HOST может содержать путь к сокету: /cloudsql/INSTANCE_CONNECTION_NAME
        if db_host.startswith('/cloudsql/'):
            # Unix socket format for Cloud SQL
            return f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
        
        # Fallback to TCP connection
        db_port = os.getenv('DB_PORT', '5432')
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # For development, use SQLite
    return 'sqlite:///./content_curator.db'

def get_db_connection():
    """Get database connection"""
    global engine, SessionLocal
    
    if engine is None:
        database_url = get_database_url()
        
        # Configure engine based on database type
        if database_url.startswith('sqlite'):
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
            )
        else:
            engine = create_engine(
                database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                pool_pre_ping=True,
                pool_recycle=300
            )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info(f"Database connection established: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    return engine, SessionLocal

def get_db_session():
    """Get database session"""
    _, SessionLocal = get_db_connection()
    return SessionLocal()

def init_database():
    """Initialize database and create tables"""
    try:
        engine, _ = get_db_connection()
        
        # Import all models to ensure they are registered
        from app.auth.models.user import User, UserSession
        from app.billing.models.subscription import Subscription, Payment, UsageRecord
        from app.billing.models.agent_subscription import AgentSubscription
        from app.models.project import Project
        from app.models.telegram_channels import TelegramChannel
        from app.models.instagram_accounts import InstagramAccount
        from app.models.twitter_accounts import TwitterAccount
        from app.models.scheduled_posts import ScheduledPostDB
        from app.models.auto_posting_rules import AutoPostingRuleDB
        from app.models.content_sources import ContentSource, MonitoredItem
        from app.models.content import ContentPieceDB, TokenUsageDB
        from app.models.uploads import FileUploadDB
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
        # Initialize default data
        init_default_data()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def init_default_data():
    """Initialize default data (tariff plans, etc.)"""
    try:
        from app.billing.services.subscription_service import SubscriptionService
        from app.database.connection import get_db_session
        
        db = get_db_session()
        subscription_service = SubscriptionService(db)
        
        # Create default tariff plans if they don't exist
        subscription_service.create_default_tariff_plans()
        
        db.close()
        logger.info("Default data initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")

def test_connection():
    """Test database connection"""
    try:
        engine, _ = get_db_connection()
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def close_connection():
    """Close database connection"""
    global engine, SessionLocal
    
    if engine:
        engine.dispose()
        engine = None
        SessionLocal = None
        logger.info("Database connection closed")
