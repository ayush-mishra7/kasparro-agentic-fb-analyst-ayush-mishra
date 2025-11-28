# Kasparro Agentic FB Analyst (v1.0)

An end-to-end **agentic AI system** designed to analyze Facebook Ads performance, diagnose ROAS/CTR issues, and generate data-driven creative recommendations using LLM reasoning and modular pipelines.

---

## Overview

This project implements a production-grade, multi-agent architecture inspired by Kasparro’s Applied AI workflow.  
It autonomously performs:

1. **Insight generation** (LLM + fallback rules)  
2. **Hypothesis validation** using real campaign metrics  
3. **Creative generation** aligned to low-performing segments  
4. **Automated reporting** in JSON + Markdown  

Outputs:
- `insights.json` – validated hypotheses with CTR/ROAS stats  
- `creatives.json` – platform-ready creative ideas  
- `report.md` – polished performance analysis report  

---

## Architecture

### **Agentic Pipeline**
```
Planner → Insight Agent → Evaluator → Creative Generator → Report Builder
```

### **Agents**
- **PlannerAgent** – structures user queries into a reasoning plan  
- **InsightAgent** – generates hypotheses using LLM + deterministic fallback  
- **EvaluatorAgent** – validates hypotheses using CTR/ROAS calculations  
- **CreativeAgent** – generates ad creatives for weak-performing segments  

---

## Tech Stack

| Category | Tools |
|---------|--------|
| Language | Python |
| LLMs | Groq API (Llama 3.1 models) |
| Data | Pandas, CSV ingestion |
| Agents | Modular OOP design |
| Output | JSON, Markdown |
| Logging | event logs (`logs/events.log.jsonl`) |

---

## 📂 Folder Structure

```
src/
  agents/
    insight_agent.py
    planner.py
    evaluator_agent.py
    creative_agent.py
  orchestrator/
    pipeline.py
  utils/
    data_utils.py
    llm_client.py
    logging_utils.py
  prompts/
data/
logs/
reports/
run.py
requirements.txt
README.md
```

---

## ▶️ How to Run

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Add your Groq API key  
Create `.env`:
```
GROQ_API_KEY=your_key_here
```

### 3. Run the pipeline
```
python run.py "Analyze ROAS drop in the last 30 days"
```

### 4. View Results  
Check the `reports/` folder:
- `insights.json`
- `creatives.json`
- `report.md`

Logs are stored in:
```
logs/events.log.jsonl
```

---

## Example Outputs

### **Insights**
- Low CTR campaigns  
- Low ROAS campaigns  
- Underperforming creative types  
- Country-level drops in efficiency  

### **Creatives**
- Persona-based  
- Angle-driven  
- Multi-platform  
- Unique hooks + descriptions  

---

## Key Features

- **LLM-first reasoning** with fallback heuristics  
- **Fuzzy matching** to clean noisy campaign names  
- **Fully deterministic evaluation**  
- **Agentic modular design**  
- **Production-ready pipeline**  

---

## 🎯 Why This Project Matters

This system demonstrates strong capabilities in:

- Applied AI engineering  
- LLM orchestration  
- Agent workflow design  
- Real-world marketing analytics  
- Automated creative generation  
- Clean, modular, scalable code patterns  

Suitable for roles like:  
**Applied AI Engineer • LLM Engineer • AI Solutions Engineer • Growth AI Specialist**

---
## ✉️ Contact  
For questions or collaborations, connect on GitHub or LinkedIn.
