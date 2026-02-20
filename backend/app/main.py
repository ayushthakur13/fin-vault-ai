from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.utils.helpers import setup_logging

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
	setup_logging(settings.log_level)
