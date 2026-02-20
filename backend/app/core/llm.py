from groq import Groq

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def _get_client() -> Groq | None:
	if not settings.groq_api_key:
		return None
	return Groq(api_key=settings.groq_api_key)


def _call_model(prompt: str, model: str) -> dict:
	client = _get_client()
	if client is None:
		return {
			"model": model,
			"output": "mock response (missing GROQ_API_KEY)",
			"mock": True,
		}
	try:
		response = client.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
		)
		content = response.choices[0].message.content if response.choices else ""
		return {"model": model, "output": content, "mock": False}
	except Exception as exc:
		logger.warning("Groq call failed: %s", exc)
		return {
			"model": model,
			"output": "mock response (Groq call failed)",
			"mock": True,
		}


def quick_model_call(prompt: str) -> dict:
	return _call_model(prompt, settings.groq_quick_model)


def deep_model_call(prompt: str) -> dict:
	return _call_model(prompt, settings.groq_deep_model)
