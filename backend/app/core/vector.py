from qdrant_client import QdrantClient

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def get_qdrant_client() -> QdrantClient:
	if not settings.qdrant_url:
		raise ValueError("QDRANT_URL is not set")
	return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


def test_qdrant_connection() -> bool:
	try:
		client = get_qdrant_client()
		client.get_collections()
		return True
	except Exception as exc:
		logger.warning("Qdrant connection failed: %s", exc)
		return False
