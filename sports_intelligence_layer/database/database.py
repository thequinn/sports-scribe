from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
import json

class QueryType(Enum):
    PLAYER_STATS = "player_stats"
    TEAM_STATS = "team_stats"
    HEAD_TO_HEAD = "head_to_head"
    HISTORICAL = "historical"
    COMPARISON = "comparison"

@dataclass
class QueryResult:
    query_type: QueryType
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    confidence: float

class SoccerDatabaseQueryBuilder:
    """
    Converts parsed soccer queries into optimized Supabase SQL queries.
    Assumes a soccer database with standard tables.
    """

    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table_mappings = {
            'players': 'players',
            'teams': 'teams',
            'matches': 'matches',
            'player_stats': 'player_match_stats',
            'team_stats': 'team_match_stats',
            'competitions': 'competitions',
            'seasons': 'seasons'
        }

    async def build_and_execute_query(self, parsed_query) -> QueryResult:
        """Main entry point for query building and execution."""

        if parsed_query.query_intent == "stat_lookup":
            if any(e.entity_type.value == "player" for e in parsed_query.entities):
                return await self._build_player_stats_query(parsed_query)
            elif any(e.entity_type.value == "team" for e in parsed_query.entities):
                return await self._build_team_stats_query(parsed_query)

        elif parsed_query.query_intent == "comparison":
            return await self._build_comparison_query(parsed_query)

        elif parsed_query.query_intent == "historical":
            return await self._build_historical_query(parsed_query)

        else:
            # Default fallback
            return await self._build_basic_query(parsed_query)

    async def _build_player_stats_query(self, parsed_query) -> QueryResult:
        """Build query for player statistics."""

        # Find player entity
        player_entity = next((e for e in parsed_query.entities
                            if e.entity_type.value == "player"), None)

        if not player_entity:
            raise ValueError("No player found in query")

        # Base query structure
        query_parts = {
            'select': self._get_player_select_fields(parsed_query.statistic_requested),
            'from': 'player_match_stats pms',
            'joins': [
                'JOIN players p ON pms.player_id = p.id',
                'JOIN matches m ON pms.match_id = m.id',
                'JOIN teams t ON m.home_team_id = t.id OR m.away_team_id = t.id'
            ],
            'where': [f"p.name ILIKE '%{player_entity.name}%'"],
            'group_by': [],
            'order_by': []
        }

        # Add time context filters
        self._add_time_filters(query_parts, parsed_query.time_context)

        # Add venue filters if specified
        if 'venue' in parsed_query.filters:
            venue_condition = self._get_venue_condition(parsed_query.filters['venue'])
            query_parts['where'].append(venue_condition)

        # Add opponent tier filters
        if 'opponent_tier' in parsed_query.filters:
            opponent_condition = self._get_opponent_tier_condition(parsed_query.filters['opponent_tier'])
            query_parts['where'].append(opponent_condition)

        # Build aggregation based on statistic
        if parsed_query.statistic_requested:
            aggregation = self._get_stat_aggregation(parsed_query.statistic_requested)
            query_parts['select'].append(aggregation)
            query_parts['group_by'] = ['p.id', 'p.name']

        # Execute query
        sql_query = self._build_sql_from_parts(query_parts)
        result = await self._execute_query(sql_query)

        return QueryResult(
            query_type=QueryType.PLAYER_STATS,
            data=result,
            metadata={
                'player': player_entity.name,
                'statistic': parsed_query.statistic_requested,
                'time_context': parsed_query.time_context.value,
                'filters': parsed_query.filters
            },
            confidence=parsed_query.confidence
        )

    async def _build_team_stats_query(self, parsed_query) -> QueryResult:
        """Build query for team statistics."""

        team_entity = next((e for e in parsed_query.entities
                           if e.entity_type.value == "team"), None)

        if not team_entity:
            raise ValueError("No team found in query")

        query_parts = {
            'select': ['t.name as team_name'],
            'from': 'matches m',
            'joins': [
                'JOIN teams t ON (m.home_team_id = t.id OR m.away_team_id = t.id)'
            ],
            'where': [f"t.name ILIKE '%{team_entity.name}%'"],
            'group_by': ['t.id', 't.name'],
            'order_by': []
        }

        # Add specific team stat aggregations
        if parsed_query.statistic_requested == 'clean_sheets':
            query_parts['select'].append("""
                SUM(CASE
                    WHEN (t.id = m.home_team_id AND m.away_goals = 0)
                         OR (t.id = m.away_team_id AND m.home_goals = 0)
                    THEN 1 ELSE 0
                END) as clean_sheets
            """)

        elif parsed_query.statistic_requested == 'goals':
            query_parts['select'].append("""
                SUM(CASE
                    WHEN t.id = m.home_team_id THEN m.home_goals
                    WHEN t.id = m.away_team_id THEN m.away_goals
                    ELSE 0
                END) as total_goals
            """)

        # Add time and venue filters
        self._add_time_filters(query_parts, parsed_query.time_context)

        if 'venue' in parsed_query.filters:
            if parsed_query.filters['venue'] == 'home':
                query_parts['where'].append('t.id = m.home_team_id')
            elif parsed_query.filters['venue'] == 'away':
                query_parts['where'].append('t.id = m.away_team_id')

        sql_query = self._build_sql_from_parts(query_parts)
        result = await self._execute_query(sql_query)

        return QueryResult(
            query_type=QueryType.TEAM_STATS,
            data=result,
            metadata={
                'team': team_entity.name,
                'statistic': parsed_query.statistic_requested,
                'time_context': parsed_query.time_context.value,
                'filters': parsed_query.filters
            },
            confidence=parsed_query.confidence
        )

    async def _build_comparison_query(self, parsed_query) -> QueryResult:
        """Build query for statistical comparisons."""

        # This is a complex query type - simplified example
        if parsed_query.comparison_type.value == "vs_average":
            return await self._build_vs_average_query(parsed_query)
        elif parsed_query.comparison_type.value == "head_to_head":
            return await self._build_head_to_head_query(parsed_query)

        # Default fallback
        return await self._build_basic_query(parsed_query)

    async def _build_head_to_head_query(self, parsed_query) -> QueryResult:
        """Build head-to-head comparison query."""

        team_entities = [e for e in parsed_query.entities
                        if e.entity_type.value == "team"]

        if len(team_entities) < 2:
            raise ValueError("Head-to-head queries require two teams")

        team1, team2 = team_entities[0], team_entities[1]

        query = f"""
        SELECT
            t1.name as team1_name,
            t2.name as team2_name,
            COUNT(*) as total_matches,
            SUM(CASE
                WHEN (m.home_team_id = t1.id AND m.home_goals > m.away_goals)
                     OR (m.away_team_id = t1.id AND m.away_goals > m.home_goals)
                THEN 1 ELSE 0
            END) as team1_wins,
            SUM(CASE
                WHEN m.home_goals = m.away_goals THEN 1 ELSE 0
            END) as draws,
            SUM(CASE
                WHEN (m.home_team_id = t2.id AND m.home_goals > m.away_goals)
                     OR (m.away_team_id = t2.id AND m.away_goals > m.home_goals)
                THEN 1 ELSE 0
            END) as team2_wins
        FROM matches m
        JOIN teams t1 ON t1.name ILIKE '%{team1.name}%'
        JOIN teams t2 ON t2.name ILIKE '%{team2.name}%'
        WHERE (
            (m.home_team_id = t1.id AND m.away_team_id = t2.id) OR
            (m.home_team_id = t2.id AND m.away_team_id = t1.id)
        )
        GROUP BY t1.id, t1.name, t2.id, t2.name
        """

        result = await self._execute_query(query)

        return QueryResult(
            query_type=QueryType.HEAD_TO_HEAD,
            data=result,
            metadata={
                'teams': [team1.name, team2.name],
                'comparison_type': 'head_to_head'
            },
            confidence=parsed_query.confidence
        )

    def _get_player_select_fields(self, statistic: Optional[str]) -> List[str]:
        """Get appropriate SELECT fields for player queries."""
        base_fields = ['p.id', 'p.name', 'p.position']

        if statistic == 'goals':
            base_fields.extend(['pms.goals', 'pms.assists'])
        elif statistic == 'assists':
            base_fields.extend(['pms.assists', 'pms.key_passes'])
        elif statistic == 'minutes':
            base_fields.append('pms.minutes_played')
        else:
            # Default to common stats
            base_fields.extend(['pms.goals', 'pms.assists', 'pms.minutes_played'])

        return base_fields

    def _add_time_filters(self, query_parts: Dict, time_context):
        """Add time-based WHERE clauses."""

        if time_context.value == "this_season":
            query_parts['where'].append("m.season = '2024-25'")
        elif time_context.value == "last_season":
            query_parts['where'].append("m.season = '2023-24'")
        elif time_context.value == "champions_league":
            query_parts['joins'].append("JOIN competitions c ON m.competition_id = c.id")
            query_parts['where'].append("c.name = 'Champions League'")
        elif time_context.value == "league_only":
            query_parts['joins'].append("JOIN competitions c ON m.competition_id = c.id")
            query_parts['where'].append("c.type = 'domestic_league'")

    def _get_venue_condition(self, venue: str) -> str:
        """Generate venue-specific WHERE conditions."""
        if venue == 'home':
            return "m.home_team_id = t.id"
        elif venue == 'away':
            return "m.away_team_id = t.id"
        return ""

    def _get_opponent_tier_condition(self, tier: str) -> str:
        """Generate opponent tier conditions (e.g., top 6 teams)."""
        if tier == 'top_6':
            top_6_teams = ['Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester United', 'Tottenham']
            team_list = "', '".join(top_6_teams)
            return f"EXISTS (SELECT 1 FROM teams opp WHERE (opp.id = m.home_team_id OR opp.id = m.away_team_id) AND opp.name IN ('{team_list}') AND opp.id != t.id)"
        return ""

    def _get_stat_aggregation(self, statistic: str) -> str:
        """Get appropriate aggregation for statistics."""
        aggregations = {
            'goals': 'SUM(pms.goals) as total_goals',
            'assists': 'SUM(pms.assists) as total_assists',
            'minutes': 'SUM(pms.minutes_played) as total_minutes',
            'pass_completion': 'AVG(pms.pass_completion_rate) as avg_pass_completion'
        }
        return aggregations.get(statistic, 'COUNT(*) as match_count')

    def _build_sql_from_parts(self, parts: Dict) -> str:
        """Assemble SQL query from parts dictionary."""
        query = f"SELECT {', '.join(parts['select'])}"
        query += f"\nFROM {parts['from']}"

        if parts['joins']:
            query += f"\n{' '.join(parts['joins'])}"

        if parts['where']:
            query += f"\nWHERE {' AND '.join(parts['where'])}"

        if parts['group_by']:
            query += f"\nGROUP BY {', '.join(parts['group_by'])}"

        if parts['order_by']:
            query += f"\nORDER BY {', '.join(parts['order_by'])}"

        return query

    async def _execute_query(self, sql_query: str) -> List[Dict]:
        """Execute the SQL query against Supabase."""
        try:
            # In a real implementation, you'd use Supabase client
            # This is a placeholder for the actual database call
            result = self.client.rpc('execute_custom_query', {'query': sql_query})
            return result.execute().data if result else []
        except Exception as e:
            print(f"Query execution error: {e}")
            return []

    async def _build_vs_average_query(self, parsed_query) -> QueryResult:
        """Build comparison vs average performance query."""
        # Implementation for vs average queries
        pass

    async def _build_historical_query(self, parsed_query) -> QueryResult:
        """Build historical context queries."""
        # Implementation for historical queries
        pass

    async def _build_basic_query(self, parsed_query) -> QueryResult:
        """Fallback basic query builder."""
        return QueryResult(
            query_type=QueryType.PLAYER_STATS,
            data=[],
            metadata={'error': 'Basic query fallback'},
            confidence=0.5
        )

# Example database schema suggestions for Supabase
SOCCER_DATABASE_SCHEMA = """
-- Core Tables
CREATE TABLE competitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL, -- 'domestic_league', 'cup', 'international'
    country VARCHAR,
    season VARCHAR NOT NULL
);

CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    short_name VARCHAR,
    founded_year INTEGER,
    stadium VARCHAR,
    league_id UUID REFERENCES competitions(id)
);

CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    birth_date DATE,
    nationality VARCHAR,
    current_team_id UUID REFERENCES teams(id)
);

CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID REFERENCES competitions(id),
    season VARCHAR NOT NULL,
    match_date TIMESTAMP NOT NULL,
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    home_goals INTEGER NOT NULL DEFAULT 0,
    away_goals INTEGER NOT NULL DEFAULT 0,
    status VARCHAR DEFAULT 'completed'
);

CREATE TABLE player_match_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id),
    player_id UUID REFERENCES players(id),
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes_attempted INTEGER DEFAULT 0,
    passes_completed INTEGER DEFAULT 0,
    pass_completion_rate DECIMAL(5,2),
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_player_match_stats_player_date ON player_match_stats(player_id, match_id);
CREATE INDEX idx_matches_teams_date ON matches(home_team_id, away_team_id, match_date);
CREATE INDEX idx_matches_season ON matches(season, competition_id);
CREATE INDEX idx_players_name ON players USING gin(name gin_trgm_ops);
CREATE INDEX idx_teams_name ON teams USING gin(name gin_trgm_ops);

-- Views for common queries
CREATE VIEW player_season_stats AS
SELECT
    p.id as player_id,
    p.name as player_name,
    p.position,
    t.name as team_name,
    m.season,
    c.name as competition_name,
    COUNT(pms.match_id) as appearances,
    SUM(pms.minutes_played) as total_minutes,
    SUM(pms.goals) as total_goals,
    SUM(pms.assists) as total_assists,
    SUM(pms.shots) as total_shots,
    SUM(pms.shots_on_target) as total_shots_on_target,
    AVG(pms.pass_completion_rate) as avg_pass_completion,
    SUM(pms.tackles) as total_tackles,
    SUM(pms.yellow_cards) as total_yellow_cards,
    SUM(pms.red_cards) as total_red_cards
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.id
JOIN matches m ON pms.match_id = m.id
JOIN teams t ON p.current_team_id = t.id
JOIN competitions c ON m.competition_id = c.id
GROUP BY p.id, p.name, p.position, t.name, m.season, c.name;

CREATE VIEW team_season_stats AS
SELECT
    t.id as team_id,
    t.name as team_name,
    m.season,
    c.name as competition_name,
    COUNT(*) as matches_played,
    SUM(CASE WHEN (t.id = m.home_team_id AND m.home_goals > m.away_goals)
              OR (t.id = m.away_team_id AND m.away_goals > m.home_goals)
         THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN (t.id = m.home_team_id AND m.home_goals < m.away_goals)
              OR (t.id = m.away_team_id AND m.away_goals < m.home_goals)
         THEN 1 ELSE 0 END) as losses,
    SUM(CASE WHEN t.id = m.home_team_id THEN m.home_goals
             WHEN t.id = m.away_team_id THEN m.away_goals
             ELSE 0 END) as goals_for,
    SUM(CASE WHEN t.id = m.home_team_id THEN m.away_goals
             WHEN t.id = m.away_team_id THEN m.home_goals
             ELSE 0 END) as goals_against,
    SUM(CASE WHEN (t.id = m.home_team_id AND m.away_goals = 0)
              OR (t.id = m.away_team_id AND m.home_goals = 0)
         THEN 1 ELSE 0 END) as clean_sheets
FROM teams t
JOIN matches m ON (t.id = m.home_team_id OR t.id = m.away_team_id)
JOIN competitions c ON m.competition_id = c.id
GROUP BY t.id, t.name, m.season, c.name;

-- Materialized view for head-to-head records (refresh periodically)
CREATE MATERIALIZED VIEW head_to_head_records AS
SELECT
    LEAST(t1.id, t2.id) as team1_id,
    GREATEST(t1.id, t2.id) as team2_id,
    LEAST(t1.name, t2.name) as team1_name,
    GREATEST(t1.name, t2.name) as team2_name,
    COUNT(*) as total_matches,
    SUM(CASE
        WHEN (m.home_team_id = LEAST(t1.id, t2.id) AND m.home_goals > m.away_goals)
             OR (m.away_team_id = LEAST(t1.id, t2.id) AND m.away_goals > m.home_goals)
        THEN 1 ELSE 0
    END) as team1_wins,
    SUM(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) as draws,
    SUM(CASE
        WHEN (m.home_team_id = GREATEST(t1.id, t2.id) AND m.home_goals > m.away_goals)
             OR (m.away_team_id = GREATEST(t1.id, t2.id) AND m.away_goals > m.home_goals)
        THEN 1 ELSE 0
    END) as team2_wins,
    MAX(m.match_date) as last_meeting
FROM matches m
JOIN teams t1 ON (m.home_team_id = t1.id OR m.away_team_id = t1.id)
JOIN teams t2 ON (m.home_team_id = t2.id OR m.away_team_id = t2.id)
WHERE t1.id != t2.id
GROUP BY LEAST(t1.id, t2.id), GREATEST(t1.id, t2.id),
         LEAST(t1.name, t2.name), GREATEST(t1.name, t2.name);

-- Function for calculating form (last N matches)
CREATE OR REPLACE FUNCTION get_team_form(team_uuid UUID, num_matches INTEGER)
RETURNS TABLE(
    match_date TIMESTAMP,
    opponent VARCHAR,
    result CHAR(1), -- W, D, L
    goals_for INTEGER,
    goals_against INTEGER
) AS $
BEGIN
    RETURN QUERY
    SELECT
        m.match_date,
        CASE
            WHEN m.home_team_id = team_uuid THEN away_team.name
            ELSE home_team.name
        END as opponent,
        CASE
            WHEN (m.home_team_id = team_uuid AND m.home_goals > m.away_goals)
                 OR (m.away_team_id = team_uuid AND m.away_goals > m.home_goals) THEN 'W'
            WHEN m.home_goals = m.away_goals THEN 'D'
            ELSE 'L'
        END as result,
        CASE
            WHEN m.home_team_id = team_uuid THEN m.home_goals
            ELSE m.away_goals
        END as goals_for,
        CASE
            WHEN m.home_team_id = team_uuid THEN m.away_goals
            ELSE m.home_goals
        END as goals_against
    FROM matches m
    JOIN teams home_team ON m.home_team_id = home_team.id
    JOIN teams away_team ON m.away_team_id = away_team.id
    WHERE (m.home_team_id = team_uuid OR m.away_team_id = team_uuid)
        AND m.status = 'completed'
    ORDER BY m.match_date DESC
    LIMIT num_matches;
END;
$ LANGUAGE plpgsql;
"""
