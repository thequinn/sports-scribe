from ..src.query_parser import SoccerQueryParser

parser = SoccerQueryParser()
result = parser.parse_query("How many goals has Haaland scored this season?")

print(f"Entities: {[e.name for e in result.entities]}")
print(f"Statistic: {result.statistic_requested}")
print(f"Confidence: {result.confidence}")
