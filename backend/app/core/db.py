import psycopg2
from psycopg2.extensions import connection

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def get_db_connection() -> connection:
	if not settings.database_url:
		raise ValueError("DATABASE_URL is not set")
	return psycopg2.connect(settings.database_url)


def test_db_connection() -> bool:
	try:
		with get_db_connection() as conn:
			with conn.cursor() as cur:
				cur.execute("SELECT 1;")
				cur.fetchone()
		return True
	except Exception as exc:
		logger.warning("Database connection failed: %s", exc)
		return False
