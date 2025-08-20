from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import re
import os
import sys
from datetime import datetime, timedelta

# project_root = os.path.join("../..", os.path.dirname(__file__))
current_dir = os.path.dirname(__file__)
print("current_dir:", current_dir)

# Add the project root to Python path
root_path = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, root_path)


from sports_intelligence_layer.config.soccer_entities import (
    PRIORITY_PLAYERS,
    PRIORITY_TEAMS,
    STATISTICS_KEYWORDS,
)


class EntityType(Enum):
    PLAYER = "player"
    TEAM = "team"
    COMPETITION = "competition"
    STATISTIC = "statistic"
    TIME_PERIOD = "time_period"
    OPPONENT = "opponent"
    VENUE = "venue"


class ComparisonType(Enum):
    VS_AVERAGE = "vs_average"
    VS_CAREER = "vs_career"
    VS_OPPONENT = "vs_opponent"
    VS_SEASON = "vs_season"
    HEAD_TO_HEAD = "head_to_head"
    LEAGUE_RANKING = "league_ranking"


class TimeContext(Enum):
    THIS_SEASON = "this_season"
    LAST_SEASON = "last_season"
    CAREER = "career"
    LAST_N_GAMES = "last_n_games"
    CURRENT_MONTH = "current_month"
    CHAMPIONS_LEAGUE = "champions_league"
    LEAGUE_ONLY = "league_only"


@dataclass
class SoccerEntity:
    name: str
    entity_type: EntityType
    aliases: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class ParsedSoccerQuery:
    original_query: str
    entities: List[SoccerEntity]
    time_context: TimeContext
    comparison_type: Optional[ComparisonType] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    statistic_requested: Optional[str] = None
    confidence: float = 1.0
    query_intent: str = "stat_lookup"  # stat_lookup, comparison, historical, context


class SoccerQueryParser:
    def __init__(self):
        """
        Players, Teams, Stats (Nouns):
        - These are entities or domain knowledge. The list of these is long and will change often. Putting them in a config file (soccer_entities.py) is the perfect strategy. It's our "knowledge base."

        Time, Comparisons (Grammar/Structure):
        - These are more about the structure and grammar of a question. "This season," "last 5 games," "compared to" are linguistic patterns. Keeping them as regex inside the parser is perfectly acceptable because they define how a user asks a question, not what they are asking about. They are less likely to change frequently.

        Why we design this way:
        (a) External Config (soccer_entities.py):
            - Holds the "what" (the nouns of our domain).
        (b) Internal Parser Logic (query_parser.py):
            - Holds the "how" (the grammar for parsing questions).
        """

        self.player_patterns = [
            # r"\b(?:player|striker|midfielder|defender|goalkeeper)\s+(\w+(?:\s+\w+)?)",
            # r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:scored|assisted|played)",
            # r"(?:How many|What\'s)\s+.*?(\w+(?:\s+\w+)?)\s+(?:goals|assists|minutes)",
        ]
        print("in __init__(), self.player_patterns:", self.player_patterns)

        # self.team_patterns = [
        #     r"\b(Arsenal|Barcelona|Real Madrid|Manchester United|Liverpool|Chelsea|Bayern Munich|PSG|Inter Milan|AC Milan|Juventus|Manchester City|Tottenham|Atletico Madrid|Borussia Dortmund)\b",
        #     r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:vs|against|home|away)",
        #     r"(?:What\'s|How\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:record|performance)",
        # ]

        # self.stat_patterns = {
        #     "goals": r"\b(?:goals?|scored|scoring|goalscorer)\b",
        #     "assists": r"\b(?:assists?|assisted|assisting)\b",
        #     "clean_sheets": r"\b(?:clean sheets?|shutouts?)\b",
        #     "pass_completion": r"\b(?:pass completion|passing accuracy|pass rate)\b",
        #     "possession": r"\b(?:possession|ball possession)\b",
        #     "shots": r"\b(?:shots?|shooting)\b",
        #     "tackles": r"\b(?:tackles?|tackling)\b",
        #     "saves": r"\b(?:saves?|saving)\b",
        #     "minutes": r"\b(?:minutes?|mins?|playing time)\b",
        # }

        self.time_patterns = {
            TimeContext.THIS_SEASON: r"\b(?:this season|current season|2024-25|2024/25)\b",
            TimeContext.LAST_SEASON: r"\b(?:last season|previous season|2023-24|2023/24)\b",
            TimeContext.CAREER: r"\b(?:career|all time|total|overall)\b",
            TimeContext.LAST_N_GAMES: r"\b(?:last|past)\s+(\d+)\s+(?:games?|matches?)\b",
            TimeContext.CHAMPIONS_LEAGUE: r"\b(?:Champions League|UCL|CL)\b",
            TimeContext.LEAGUE_ONLY: r"\b(?:Premier League|La Liga|Serie A|Bundesliga|Ligue 1|league)\b",
        }

        self.comparison_patterns = {
            ComparisonType.VS_AVERAGE: r"\b(?:compared to|vs|versus|against)\s+(?:average|normal|typical)\b",
            ComparisonType.VS_CAREER: r"\b(?:compared to|vs|versus|against)\s+(?:career|overall)\b",
            ComparisonType.VS_OPPONENT: r"\b(?:against|vs|versus)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            ComparisonType.HEAD_TO_HEAD: r"\b(?:head to head|h2h|historical)\s+(?:record|against)\b",
        }

    def parse_query(self, query: str) -> ParsedSoccerQuery:
        """Parse a natural language soccer query into structured components."""
        print("in parse_query()")
        entities = self._extract_entities(query)
        time_context = self._extract_time_context(query)
        comparison_type = self._extract_comparison_type(query)
        statistic = self._extract_statistic(query)
        filters = self._extract_filters(query)
        intent = self._determine_intent(query, entities, comparison_type)

        confidence = self._calculate_confidence(entities, time_context, statistic)

        return ParsedSoccerQuery(
            original_query=query,
            entities=entities,
            time_context=time_context,
            comparison_type=comparison_type,
            filters=filters,
            statistic_requested=statistic,
            confidence=confidence,
            query_intent=intent,
        )

    def _extract_entities(self, query: str) -> List[SoccerEntity]:
        """Extract player and team entities using the knowledge base."""
        entities = []

        # Pad with spaces for whole word matching
        query_lower = f" {query.lower()} "

        # --- Team Recognition ---
        for official_name, data in PRIORITY_TEAMS.items():
            # Create a list of all possible names for the team
            names_to_check = [official_name] + data.get("aliases", [])
            print("official_name:", official_name)
            print("data:", data)
            print("names_to_check:", names_to_check)

            for name in names_to_check:
                if f" {name} " in query_lower:
                    # Avoid adding the same team twice from an alias
                    if not any(e.name == official_name for e in entities):
                        entities.append(
                            SoccerEntity(
                                name=official_name,
                                entity_type=EntityType.TEAM,
                                confidence=0.95,
                            )
                        )
                        break  # Move to the next team once found

        # --- Player Recognition ---
        for official_name, data in PRIORITY_PLAYERS.items():
            names_to_check = [official_name] + data.get("aliases", [])
            for name in names_to_check:
                if f" {name} " in query_lower:
                    if not any(e.name == official_name for e in entities):
                        entities.append(
                            SoccerEntity(
                                name=official_name,
                                entity_type=EntityType.PLAYER,
                                confidence=0.95,
                            )
                        )
                        break  # Move to next player

        return entities

    def _extract_time_context(self, query: str) -> TimeContext:
        """Determine the time context of the query."""
        for time_context, pattern in self.time_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return time_context

        # Default to current season if no time context found
        return TimeContext.THIS_SEASON

    def _extract_comparison_type(self, query: str) -> Optional[ComparisonType]:
        """Extract comparison type if present."""
        for comp_type, pattern in self.comparison_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return comp_type
        return None

    def _extract_statistic(self, query: str) -> Optional[str]:
        """Extract the main statistic being requested."""
        for stat_name, keywords in STATISTICS_KEYWORDS.items():
            for keyword in keywords:
                if re.search(rf"\b(?:{keyword})\b", query, re.IGNORECASE):
                    return stat_name
        return None

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract additional filters like home/away, competition type."""
        filters = {}

        if re.search(r"\b(?:home|at home)\b", query, re.IGNORECASE):
            filters["venue"] = "home"
        elif re.search(r"\b(?:away|on the road)\b", query, re.IGNORECASE):
            filters["venue"] = "away"

        if re.search(r"\b(?:big six|top 6|top six)\b", query, re.IGNORECASE):
            filters["opponent_tier"] = "top_6"

        if re.search(r"\b(?:derby|derbies)\b", query, re.IGNORECASE):
            filters["match_type"] = "derby"

        return filters

    def _determine_intent(
        self,
        query: str,
        entities: List[SoccerEntity],
        comparison_type: Optional[ComparisonType],
    ) -> str:
        """Determine the overall intent of the query."""
        if comparison_type:
            return "comparison"
        elif re.search(
            r"\b(?:when|history|last time|historical)\b", query, re.IGNORECASE
        ):
            return "historical"
        elif re.search(
            r"\b(?:context|significance|important|why)\b", query, re.IGNORECASE
        ):
            return "context"
        else:
            return "stat_lookup"

    def _is_likely_player(self, name: str) -> bool:
        """Simple heuristic to determine if a name is likely a player."""
        # This is a simplified check - in production you'd want a more sophisticated approach
        return len(name.split()) <= 3 and name[0].isupper()

    def _calculate_confidence(
        self,
        entities: List[SoccerEntity],
        time_context: TimeContext,
        statistic: Optional[str],
    ) -> float:
        """Calculate overall confidence in the query parsing."""
        base_confidence = 0.5

        if entities:
            base_confidence += 0.3
        if time_context != TimeContext.THIS_SEASON:  # Explicit time context found
            base_confidence += 0.1
        if statistic:
            base_confidence += 0.1

        return min(base_confidence, 1.0)


# Example usage and testing
if __name__ == "__main__":
    parser = SoccerQueryParser()
    print(f"parser: {parser}")
    test_queries = [
        "How many goals has Haaland scored this season?",
        "What's Arsenal's home record in the Premier League?",
        "How does Messi's pass completion compare to his career average?",
        "When did Barcelona last beat Real Madrid in El Clasico?",
        "What's Liverpool's clean sheet record against the big six?",
        "How significant is Salah's performance against City?",
    ]

    for query in test_queries:
        parsed = parser.parse_query(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {parsed.query_intent}")
        print(f"Entities: {[(e.name, e.entity_type.value) for e in parsed.entities]}")
        print(f"Statistic: {parsed.statistic_requested}")
        print(f"Time Context: {parsed.time_context.value}")
        print(
            f"Comparison: {parsed.comparison_type.value if parsed.comparison_type else None}"
        )
        print(f"Filters: {parsed.filters}")
        print(f"Confidence: {parsed.confidence:.2f}")
