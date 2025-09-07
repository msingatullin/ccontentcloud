"""
Database migrations
"""

import logging
from datetime import datetime
from sqlalchemy import text
from .connection import get_db_connection, Base

logger = logging.getLogger(__name__)

def run_migrations():
    """Run all database migrations"""
    try:
        engine, _ = get_db_connection()
        
        # Create migrations table if it doesn't exist
        create_migrations_table(engine)
        
        # Get list of applied migrations
        applied_migrations = get_applied_migrations(engine)
        
        # Define all migrations
        migrations = [
            ('001_create_users_table', create_users_table),
            ('002_create_user_sessions_table', create_user_sessions_table),
            ('003_create_subscriptions_table', create_subscriptions_table),
            ('004_create_payments_table', create_payments_table),
            ('005_create_usage_records_table', create_usage_records_table),
            ('006_create_indexes', create_indexes),
            ('007_insert_default_tariff_plans', insert_default_tariff_plans)
        ]
        
        # Run pending migrations
        for migration_id, migration_func in migrations:
            if migration_id not in applied_migrations:
                logger.info(f"Running migration: {migration_id}")
                migration_func(engine)
                mark_migration_applied(engine, migration_id)
                logger.info(f"Migration {migration_id} completed successfully")
        
        logger.info("All migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def create_migrations_table(engine):
    """Create migrations tracking table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS migrations (
                id VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

def get_applied_migrations(engine):
    """Get list of applied migrations"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM migrations"))
        return [row[0] for row in result.fetchall()]

def mark_migration_applied(engine, migration_id):
    """Mark migration as applied"""
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO migrations (id, applied_at) 
            VALUES (:migration_id, :applied_at)
        """), {
            'migration_id': migration_id,
            'applied_at': datetime.utcnow()
        })
        conn.commit()

def create_users_table(engine):
    """Create users table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                company VARCHAR(255),
                position VARCHAR(100),
                timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
                language VARCHAR(10) DEFAULT 'ru',
                role VARCHAR(20) DEFAULT 'user',
                is_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                notifications_enabled BOOLEAN DEFAULT TRUE,
                marketing_emails BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                email_verification_token VARCHAR(255),
                email_verification_expires_at TIMESTAMP,
                password_reset_token VARCHAR(255),
                password_reset_expires_at TIMESTAMP
            )
        """))
        conn.commit()

def create_user_sessions_table(engine):
    """Create user_sessions table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                refresh_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.commit()

def create_subscriptions_table(engine):
    """Create subscriptions table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                plan_name VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew BOOLEAN DEFAULT TRUE,
                trial_end_date TIMESTAMP,
                meta_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.commit()

def create_payments_table(engine):
    """Create payments table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                yookassa_payment_id VARCHAR(255) UNIQUE,
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'RUB',
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                payment_method VARCHAR(50),
                description TEXT,
                meta_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
            )
        """))
        conn.commit()

def create_usage_records_table(engine):
    """Create usage_records table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                resource_type VARCHAR(50) NOT NULL,
                resource_id VARCHAR(255),
                usage_count INTEGER DEFAULT 1,
                usage_date DATE DEFAULT CURRENT_DATE,
                meta_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
            )
        """))
        conn.commit()

def create_indexes(engine):
    """Create database indexes for performance"""
    with engine.connect() as conn:
        # Users table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(email_verification_token)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(password_reset_token)"))
        
        # User sessions table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at)"))
        
        # Subscriptions table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_name ON subscriptions(plan_name)"))
        
        # Payments table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id ON payments(yookassa_payment_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"))
        
        # Usage records table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_records_subscription_id ON usage_records(subscription_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_records_resource_type ON usage_records(resource_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_records_usage_date ON usage_records(usage_date)"))
        
        conn.commit()

def insert_default_tariff_plans(engine):
    """Insert default tariff plans"""
    with engine.connect() as conn:
        # Create tariff_plans table first
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tariff_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                price_monthly DECIMAL(10,2) NOT NULL,
                price_yearly DECIMAL(10,2),
                currency VARCHAR(3) DEFAULT 'RUB',
                features TEXT NOT NULL,
                limits TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        
        # Check if tariff plans already exist
        result = conn.execute(text("SELECT COUNT(*) FROM tariff_plans"))
        count = result.fetchone()[0]
        
        if count == 0:
            # Insert default plans
            default_plans = [
                {
                    'name': 'free',
                    'display_name': 'Free',
                    'description': 'Базовый план для начала работы',
                    'price_monthly': 0.00,
                    'price_yearly': 0.00,
                    'features': {
                        'posts_per_month': 50,
                        'agents': ['ChiefContentAgent', 'DraftingAgent', 'PublisherAgent'],
                        'platforms': ['telegram', 'vk'],
                        'support': 'community'
                    },
                    'limits': {
                        'max_posts_per_month': 50,
                        'max_agents': 3,
                        'max_platforms': 2
                    }
                },
                {
                    'name': 'pro',
                    'display_name': 'Pro',
                    'description': 'Профессиональный план для бизнеса',
                    'price_monthly': 2990.00,
                    'price_yearly': 29900.00,
                    'features': {
                        'posts_per_month': -1,  # unlimited
                        'agents': 'all',
                        'platforms': 'all',
                        'support': 'priority',
                        'analytics': True,
                        'api_access': True
                    },
                    'limits': {
                        'max_posts_per_month': -1,
                        'max_agents': -1,
                        'max_platforms': -1
                    }
                },
                {
                    'name': 'enterprise',
                    'display_name': 'Enterprise',
                    'description': 'Корпоративный план с полным функционалом',
                    'price_monthly': 0.00,  # Custom pricing
                    'price_yearly': 0.00,
                    'features': {
                        'posts_per_month': -1,
                        'agents': 'all',
                        'platforms': 'all',
                        'support': 'dedicated',
                        'analytics': True,
                        'api_access': True,
                        'white_label': True,
                        'team_management': True,
                        'custom_integrations': True
                    },
                    'limits': {
                        'max_posts_per_month': -1,
                        'max_agents': -1,
                        'max_platforms': -1,
                        'max_team_members': -1
                    }
                }
            ]
            
            import json
            
            for plan in default_plans:
                # Convert dict to JSON string for SQLite
                plan_data = {
                    'name': plan['name'],
                    'display_name': plan['display_name'],
                    'description': plan['description'],
                    'price_monthly': plan['price_monthly'],
                    'price_yearly': plan['price_yearly'],
                    'features': json.dumps(plan['features']),
                    'limits': json.dumps(plan['limits'])
                }
                
                conn.execute(text("""
                    INSERT INTO tariff_plans (name, display_name, description, price_monthly, price_yearly, features, limits)
                    VALUES (:name, :display_name, :description, :price_monthly, :price_yearly, :features, :limits)
                """), plan_data)
            
            conn.commit()
            logger.info("Default tariff plans inserted successfully")

def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        from .connection import init_database
        return init_database()
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False
