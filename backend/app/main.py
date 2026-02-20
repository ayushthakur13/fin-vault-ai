from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.utils.helpers import setup_logging, get_logger
from app.core.schema import init_schema
from app.agents.graph import build_graph

logger = get_logger(__name__)
app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    setup_logging(settings.log_level)
    logger.info(f"Starting {settings.app_name} in {settings.env} mode")
    
    # Initialize database schema
    try:
        if init_schema():
            logger.info("Database schema verified")
        else:
            logger.warning("Failed to initialize database schema (continuing anyway)")
    except Exception as exc:
        logger.warning(f"Database initialization issue: {exc} (continuing anyway)")
    
    # Build agent graph
    try:
        build_graph()
        logger.info("Agent graph built successfully")
    except Exception as exc:
        logger.error(f"Failed to build agent graph: {exc}")


@app.on_event("shutdown")
def on_shutdown() -> None:
    logger.info(f"Shutting down {settings.app_name}")
