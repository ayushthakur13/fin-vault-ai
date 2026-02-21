"""
Database schema initialization for FinVault AI
Handles user accounts and query history
"""

from app.core.db import get_db_connection
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def init_auth_schema() -> bool:
    """Initialize users and query_history tables"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create query_history table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    query TEXT NOT NULL,
                    mode VARCHAR(20) DEFAULT 'quick',
                    retrieval_mode VARCHAR(20) DEFAULT 'hybrid',
                    analysis TEXT,
                    model_used VARCHAR(50),
                    latency_ms INTEGER,
                    contradictions_detected VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Add missing columns safely (won't fail if they already exist)
            try:
                cur.execute("ALTER TABLE query_history ADD COLUMN retrieval_mode VARCHAR(20) DEFAULT 'hybrid';")
            except:
                pass  # Column already exists
            
            try:
                cur.execute("ALTER TABLE query_history ADD COLUMN analysis TEXT;")
            except:
                pass  # Column already exists
            
            try:
                cur.execute("ALTER TABLE query_history ADD COLUMN model_used VARCHAR(50);")
            except:
                pass  # Column already exists
            
            try:
                cur.execute("ALTER TABLE query_history ADD COLUMN latency_ms INTEGER;")
            except:
                pass  # Column already exists
            
            # Create index if it doesn't exist
            try:
                cur.execute("""
                    CREATE INDEX idx_query_history_user_id 
                    ON query_history(user_id);
                """)
            except:
                pass  # Index already exists
            
            conn.commit()
            logger.info("Auth schema initialized successfully")
            return True
    except Exception as exc:
        logger.warning(f"Auth schema initialization issue: {exc}")
        return False
    finally:
        if conn:
            conn.close()
