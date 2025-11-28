import json
from src.utils.llm_client import LLMClient
from src.utils.logging_utils import log_event

class PlannerAgent:
    """
    Planner Agent:
    - Breaks high-level user query into structured analysis steps.
    - Summary is truncated to avoid hitting Groq token limits.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def plan(self, user_query: str, data_summary):
        # Load system prompt
        with open("prompts/planner_prompt.md", "r", encoding="utf-8") as f:
            prompt = f.read()

        # Safe, token-limited data summary
        summary_snippet = json.dumps(data_summary, indent=2)[:3000]

        system_msg = {
            "role": "system",
            "content": prompt
        }

        user_msg = {
            "role": "user",
            "content": (
                f"User Query:\n{user_query}\n\n"
                f"High-Level Data Summary (truncated to 3000 chars):\n{summary_snippet}"
            )
        }

        # Call LLM
        response = self.llm.chat([system_msg, user_msg])

        # Log raw result
        log_event("planner_output_raw", {"response": response})

        # Return plan as plain text; JSON parsing will happen later in pipeline
        return {"plan": response}
