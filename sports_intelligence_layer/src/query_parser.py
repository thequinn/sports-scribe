from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import re
from datetime import datetime, timedelta


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
        self.player_patterns = [
            # Matches position keywords followed by a name, ex."striker Haaland" → captures "Haaland"
            r"\b(?:player|striker|midfielder|defender|goalkeeper)\s+(\w+(?:\s+\w+)?)",
            # Matches capitalized names followed by action verbs, ex. "Salah scored" → captures "Salah"
            # "?:" non-capturing group. Groups for logic (like alternation or quantifiers) but doesn't save the match.
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:scored|assisted|played)",
            # Matches question patterns with stats, ex. "How many goals has Messi scored?" → captures "Messi"
            r"(?:How many|What\'s)\s+.*?\b(?:has|have)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:scored|goals|assists|minutes)",
        ]

        self.team_patterns = [
            # Uses word boundaries (\b) to match exact team names, ex.Arsenal scored 3 goals" → captures "Arsenal"
            r"\b(Arsenal|Barcelona|Real Madrid|Manchester United|Liverpool|Chelsea|Bayern Munich|PSG|Inter Milan|AC Milan|Juventus|Manchester City|Tottenham|Atletico Madrid|Borussia Dortmund)\b",
            # Matches capitalized names followed by match context keywords, ex. "Liverpool vs Arsenal" → captures "Liverpool"
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:vs|against|home|away)",
            # Matches question patterns with team names, ex. "What's Arsenal's home record?" → captures "Arsenal"
            r"(?:What\'s|How\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:record|performance)",
        ]

        self.stat_patterns = {
            "goals": r"\b(?:goals?|scored|scoring|goalscorer)\b",
            "assists": r"\b(?:assists?|assisted|assisting)\b",
            "clean_sheets": r"\b(?:clean sheets?|shutouts?)\b",
            "pass_completion": r"\b(?:pass completion|passing accuracy|pass rate)\b",
            "possession": r"\b(?:possession|ball possession)\b",
            "shots": r"\b(?:shots?|shooting)\b",
            "tackles": r"\b(?:tackles?|tackling)\b",
            "saves": r"\b(?:saves?|saving)\b",
            "minutes": r"\b(?:minutes?|mins?|playing time)\b",
        }

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
        """Extract player, team, and other entities from the query."""
        entities = []

        # Extract players
        for pattern in self.player_patterns:
            """
            re.finditer():
            - finding all non-overlapping matches of a regex pattern.
            - Unlike re.findall(), which returns a list of strings, re.finditer() returns an iterator yielding Match objects.
            - A march object provides methods to access details about the match.
            """
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                print(f"query_parser.py::_extract_entities, match: {match.group()}")
                # match.group(0): Return the entire match string
                # match.group(1): Return the 1st string of the match
                player_name = match.group(1)
                print(f"query_parser.py::_extract_entities, player_name: {player_name}")
                if self._is_likely_player(player_name):
                    entities.append(
                        SoccerEntity(
                            name=player_name,
                            entity_type=EntityType.PLAYER,
                            confidence=0.85,
                        )
                    )

        # Extract teams
        for pattern in self.team_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                print(f"query_parser.py::_extract_entities, match: {match.group()}")
                team_name = match.group(1) if match.groups() else match.group(0)
                print(f"query_parser.py::_extract_entities, team_name: {team_name}")
                entities.append(
                    SoccerEntity(
                        name=team_name, entity_type=EntityType.TEAM, confidence=0.9
                    )
                )

        return entities

    def _extract_time_context(self, query: str) -> TimeContext:
        """Determine the time context of the query."""
        for time_context, pattern in self.time_patterns.items():
            print(f"""time_context: {time_context}, pattern: {pattern}""")
            if re.search(pattern, query, re.IGNORECASE):
                print(f"""time_context found: {time_context}""")
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
        for stat_name, pattern in self.stat_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
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

    test_queries = [
        "How many goals has Haaland scored this season?",
        # "What's Arsenal's home record in the Premier League?",
        # "How does Messi's pass completion compare to his career average?",
        # "When did Barcelona last beat Real Madrid in El Clasico?",
        # "What's Liverpool's clean sheet record against the big six?",
        # "How significant is Salah's performance against City?"
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
