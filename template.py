import os

# Folders to create
folders = [
    "config",
    "prompts",
    "src",
    "src/agents",
    "src/utils",
    "src/orchestrator",
    "tests",
    "logs",
    "reports",
    "data"
]

# Files to create
files = {
    "README.md": "",
    "requirements.txt": "",
    "run.py": "",
    "agent_graph.md": "",

    "config/config.yaml": "",

    "prompts/planner_prompt.md": "",
    "prompts/insight_prompt.md": "",
    "prompts/creative_prompt.md": "",
    "prompts/data_summary_prompt.md": "",

    "src/__init__.py": "",
    "src/agents/__init__.py": "",
    "src/utils/__init__.py": "",
    "src/orchestrator/__init__.py": "",

    "src/orchestrator/pipeline.py": "",
    "src/agents/planner.py": "",
    "src/agents/data_agent.py": "",
    "src/agents/insight_agent.py": "",
    "src/agents/evaluator_agent.py": "",
    "src/agents/creative_agent.py": "",
    "src/utils/llm_client.py": "",
    "src/utils/logging_utils.py": "",
    "src/utils/data_utils.py": "",

    "tests/test_evaluator.py": "",

    "logs/.gitkeep": "",
    "reports/.gitkeep": "",
    "data/README.md": "Place dataset here."
}

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create files
for filepath, content in files.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Project structure created successfully!")
