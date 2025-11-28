import argparse
import sys
from src.orchestrator.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="Kasparro Agentic FB Performance Analyst"
    )
    parser.add_argument(
        "query",
        type=str,
        help="Analysis query, e.g. 'Analyze ROAS drop last month'"
    )
    args = parser.parse_args()

    run_pipeline(user_query=args.query)

if __name__ == "__main__":
    sys.exit(main())