from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
	query: str
	mode: str | None = None


@router.get("/health")
def health_check() -> dict:
	return {"status": "ok"}


@router.get("/")
def root() -> dict:
	return {"service": "FinVault AI", "status": "ok"}


@router.post("/query")
def query_placeholder(payload: QueryRequest) -> dict:
	return {
		"status": "placeholder",
		"query": payload.query,
		"mode": payload.mode,
	}
