from groq import Groq
import time

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


def _get_client() -> Groq | None:
	if not settings.groq_api_key:
		return None
	return Groq(api_key=settings.groq_api_key)


def _call_model(prompt: str, model: str) -> dict:
	"""
	Call Groq LLM with token usage and latency tracking (Area #7).
	
	Returns:
		dict with 'output', 'tokens_used', 'latency_ms', 'model', 'mock'
	"""
	client = _get_client()
	
	start_time = time.time()
	
	if client is None:
		logger.warning("Groq client not initialized (missing API key)")
		return {
			"model": model,
			"output": "mock response (missing GROQ_API_KEY)",
			"mock": True,
			"tokens_used": 0,
			"latency_ms": 0,
		}
	
	try:
		response = client.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
		)
		
		latency_ms = int((time.time() - start_time) * 1000)
		content = response.choices[0].message.content if response.choices else ""
		
		# DEFENSIVE: Extract token usage (Area #7 - latency/token logging)
		tokens_used = 0
		if hasattr(response, 'usage') and response.usage:
			try:
				# Total tokens: input + output
				tokens_used = response.usage.total_tokens
				logger.debug(f"LLM usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}, Total: {tokens_used}")
			except Exception as usage_exc:
				logger.warning(f"Failed to extract token count: {usage_exc}")
		
		logger.info(f"LLM call completed: {model} in {latency_ms}ms, {tokens_used} tokens")
		
		return {
			"model": model,
			"output": content,
			"mock": False,
			"tokens_used": tokens_used,
			"latency_ms": latency_ms,
		}
		
	except Exception as exc:
		latency_ms = int((time.time() - start_time) * 1000)
		logger.warning(f"Groq call failed after {latency_ms}ms: {exc}")
		
		# DEFENSIVE: Return meaningful fallback (Area #8 - graceful degradation)
		return {
			"model": model,
			"output": "mock response (Groq call failed)",
			"mock": True,
			"tokens_used": 0,
			"latency_ms": latency_ms,
		}


def quick_model_call(prompt: str) -> dict:
	"""Call quick model (llama-3.1-8b-instant) with usage tracking."""
	return _call_model(prompt, settings.groq_quick_model)


def deep_model_call(prompt: str) -> dict:
	"""Call deep model (llama-3.3-70b-versatile) with usage tracking."""
	return _call_model(prompt, settings.groq_deep_model)
