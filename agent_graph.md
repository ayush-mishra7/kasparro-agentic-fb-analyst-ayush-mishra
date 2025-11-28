# Agent Graph — Kasparro Agentic Facebook Performance Analyst

## Nodes (Agents)

1. Planner Agent
   - Role: Decompose the user's natural language query into concrete analysis steps.
   - Input: user_query, high-level data summary.
   - Output: JSON plan describing ordered steps and expected outputs.

2. Data Agent
   - Role: Load and summarize the Facebook Ads dataset.
   - Input: config/data path.
   - Output: pandas DataFrame + basic aggregates (numeric summary, by_campaign, by_creative_type).

3. Insight Agent
   - Role: Transform numeric summaries into marketing hypotheses.
   - Input: user_query, data summary JSON.
   - Output: hypotheses JSON (id, title, summary, segment_filter, evidence).

4. Evaluator Agent
   - Role: Quantitatively validate hypotheses and assign confidence.
   - Input: raw hypotheses JSON, full DataFrame.
   - Output: evaluated hypotheses JSON with validation block (sample_size, mean_ctr, mean_roas, confidence, comment).

5. Creative Improvement Generator
   - Role: Generate new creative ideas for low-CTR segments.
   - Input: evaluated hypotheses JSON.
   - Output: creatives JSON with persona, angle, primary_text, headline, description, CTA.

## Edges (Data Flow)

User Query
  -> Planner Agent
      -> generates plan (logged for observability)

Data Agent
  -> loads dataset and computes aggregates
  -> provides `summary` to Planner and Insight Agent

Insight Agent
  -> reads user query + summary
  -> produces `hypotheses.json` (in memory)

Evaluator Agent
  -> reads full DataFrame + hypotheses
  -> produces validated hypotheses with confidence scores
  -> saved as `reports/insights.json`

Creative Improvement Generator
  -> reads evaluated hypotheses
  -> generates creatives
  -> saved as `reports/creatives.json`

Pipeline
  -> uses both insights + creatives to generate `reports/report.md`
  -> all major steps emit JSON logs to `logs/events.log.jsonl`.