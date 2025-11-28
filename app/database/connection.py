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
    # For production, use Cloud SQL or external database
    if os.getenv('ENVIRONMENT') == 'production':
        # Cloud SQL connection
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'content_curator')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Check if using Cloud SQL Unix Socket
        if db_host.startswith('/cloudsql/'):
            # Cloud SQL Unix Socket format
            # postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance
            return f"postgresql://{db_user}:{db_password}@/{db_name}?host={db_host}"
        else:
            # Standard TCP connection
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # For development, use SQLite
    db_path = os.getenv('DATABASE_URL', 'sqlite:///./content_curator.db')
    return db_path

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
            # Увеличиваем размер пула соединений для PostgreSQL
            # pool_size - количество постоянных соединений
            # max_overflow - максимальное количество дополнительных соединений
            # pool_timeout - время ожидания свободного соединения
            engine = create_engine(
                database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=20,  # Увеличено с 5 до 20
                max_overflow=30,  # Увеличено с 10 до 30
                pool_timeout=60  # Увеличено время ожидания до 60 секунд
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
        from app.billing.models.agent_subscription import AgentSubscription  # Новая модель
        from app.models.content import ContentPieceDB, TokenUsageDB, ContentHistoryDB
        from app.models.uploads import FileUploadDB
        from app.models.scheduled_posts import ScheduledPostDB
        from app.models.auto_posting_rules import AutoPostingRuleDB
        from app.models.content_sources import ContentSource, MonitoredItem, SourceCheckHistory
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
        # Initialize default data
        init_default_data()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def run_migrations():
    """Run database migrations for missing columns"""
    try:
        engine, _ = get_db_connection()
        
        with engine.connect() as conn:
            # Check and add project_id to instagram_accounts if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'instagram_accounts' AND column_name = 'project_id'
            """))
            if not result.fetchone():
                logger.info("Adding project_id column to instagram_accounts...")
                conn.execute(text("""
                    ALTER TABLE instagram_accounts 
                    ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_instagram_accounts_project_id 
                    ON instagram_accounts(project_id)
                """))
                conn.commit()
                logger.info("Migration completed: project_id added to instagram_accounts")
            
    except Exception as e:
        logger.warning(f"Migration check failed (may be expected on first run): {e}")


def init_default_data():
    """Initialize default data (tariff plans, etc.)"""
    try:
        # Run migrations first
        run_migrations()
        
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
