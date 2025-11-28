import os
from typing import List, Dict, Any
from groq import Groq
import yaml

class LLMClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)

        self.model = cfg["llm"]["model"]
        self.temperature = cfg["llm"]["temperature"]
        self.max_tokens = cfg["llm"]["max_tokens"]

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")

        self.client = Groq(api_key=api_key)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Basic chat-completion wrapper returning assistant content as string.
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        # Groq uses OpenAI-style responses
        return completion.choices[0].message.content