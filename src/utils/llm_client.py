import os
import yaml
import time
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
try:
    from groq import Groq
except Exception:
    Groq = None
from utils.logging_utils import log_event

_CFG_PATH = Path("config/config.yaml")
_cfg = {}
if _CFG_PATH.exists():
    with open(_CFG_PATH, "r", encoding="utf-8") as fh:
        import yaml
        _cfg = yaml.safe_load(fh) or {}
else:
    _cfg = {}

class LLMClient:
    def __init__(self):
        cfg = _cfg or {}
        llm_cfg = cfg.get("llm", {})
        self.model = llm_cfg.get("model", "gpt-4.1")
        self.temperature = llm_cfg.get("temperature", 0.0)
        self.max_tokens = llm_cfg.get("max_tokens", 1024)
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY".upper())
        if not self.api_key:
            raise RuntimeError("Missing GROQ_API_KEY environment variable.")
        if Groq is None:
            raise RuntimeError("groq library not available")
        self.client = Groq(api_key=self.api_key)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type(Exception))
    def chat(self, messages):
        try:
            resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=self.temperature, max_tokens=self.max_tokens)
            out = resp.choices[0].message.content
            log_event("llm.success", {"model": self.model}, agent="LLMClient")
            return out
        except Exception as e:
            log_event("llm.error", {"error": str(e)}, agent="LLMClient")
            raise
