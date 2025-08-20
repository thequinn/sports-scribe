#!/usr/bin/env python3
"""
Test script to run query_parser.py with proper Python path setup.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import and run the query parser
from sports_intelligence_layer.src.query_parser import SoccerQueryParser

def main():
    parser = SoccerQueryParser()

    # Test queries
    test_queries = [
        "How many goals did Haaland score this season?",
        "Arsenal vs Manchester City head to head record",
        "Messi career goals"
    ]

    print("Testing Soccer Query Parser...")
    print("=" * 50)

    for query in test_queries:
        print(f"\nQuery: {query}")
        parsed = parser.parse_query(query)
        print(f"Entities: {[e.name for e in parsed.entities]}")
        print(f"Time Context: {parsed.time_context}")
        print(f"Statistic: {parsed.statistic_requested}")
        print(f"Intent: {parsed.query_intent}")
        print(f"Confidence: {parsed.confidence}")

if __name__ == "__main__":
    main()
