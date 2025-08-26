from typing import Any, Dict, List
from query_parser import SoccerQueryParser, ParsedSoccerQuery, SoccerEntity, EntityType

# Soccer-Specific Enhancements for Query Parser

SOCCER_ENTITIES = {
    "players": {
        # Premier League stars
        "erling haaland": ["haaland", "erling", "man city striker"],
        "mohamed salah": ["salah", "mo salah", "liverpool winger"],
        "harry kane": ["kane", "harry", "bayern striker"],
        "kevin de bruyne": ["kdb", "de bruyne", "man city midfielder"],
        "virgil van dijk": ["van dijk", "virgil", "liverpool defender"],
        # La Liga stars
        "lionel messi": ["messi", "leo", "inter miami"],
        "karim benzema": ["benzema", "real madrid striker"],
        "pedri": ["pedri gonzalez", "barcelona midfielder"],
        "vinicius junior": ["vinicius", "vini jr", "real madrid winger"],
        # Serie A & Others
        "kylian mbappe": ["mbappe", "psg striker", "real madrid"],
        "robert lewandowski": ["lewandowski", "lewa", "barcelona striker"],
    },
    "teams": {
        # Premier League
        "arsenal": ["gunners", "afc", "emirates"],
        "manchester city": ["man city", "city", "citizens", "mcfc"],
        "manchester united": ["man utd", "united", "red devils", "mufc"],
        "liverpool": ["reds", "lfc", "anfield"],
        "chelsea": ["blues", "cfc", "stamford bridge"],
        "tottenham hotspur": ["spurs", "tottenham", "thfc"],
        # La Liga
        "real madrid": ["madrid", "real", "los blancos", "rmcf"],
        "barcelona": ["barca", "fcb", "blaugrana", "camp nou"],
        "atletico madrid": ["atletico", "atleti", "rojiblancos"],
        # Other major clubs
        "bayern munich": ["bayern", "fcb munich", "bavarians"],
        "paris saint-germain": ["psg", "paris", "parisiens"],
    },
    "competitions": {
        "premier league": ["epl", "english premier league", "pl"],
        "champions league": ["ucl", "cl", "european cup"],
        "europa league": ["uel", "europa"],
        "la liga": ["spanish league", "primera division"],
        "serie a": ["italian league"],
        "bundesliga": ["german league"],
        "world cup": ["fifa world cup", "wc"],
        "euros": ["european championship", "euro 2024"],
    },
}

SOCCER_STATISTICS = {
    # Offensive stats
    "goals": ["goals scored", "scored", "goalscorer", "strikes", "finishes"],
    "assists": ["assisted", "set up", "created", "provided"],
    "shots": ["attempts", "efforts", "shots on target", "shot accuracy"],
    "expected_goals": ["xg", "expected goals", "xg per game"],
    "key_passes": ["key passes", "chances created", "through balls"],
    # Defensive stats
    "clean_sheets": ["shutouts", "clean sheet", "nil"],
    "tackles": ["tackles won", "defensive actions", "duels won"],
    "interceptions": ["intercepted", "read the game", "cut out"],
    "blocks": ["blocked shots", "blocked crosses", "defensive blocks"],
    # Possession stats
    "pass_completion": ["passing accuracy", "pass success", "completion rate"],
    "possession": ["ball possession", "time on ball", "dominated possession"],
    "dribbles": ["successful dribbles", "take-ons", "beat defender"],
    "crosses": ["crossing accuracy", "crosses completed", "deliveries"],
    # Goalkeeper stats
    "saves": ["stops", "kept out", "denied", "save percentage"],
    "distribution": ["passing accuracy", "long balls", "distribution"],
    # Team stats
    "win_rate": ["win percentage", "victory rate", "success rate"],
    "form": ["recent form", "last 5 games", "current run"],
    "home_record": ["home form", "at home", "home advantage"],
    "away_record": ["away form", "on the road", "traveling"],
}

SOCCER_CONTEXTS = {
    # Match contexts
    "derby": ["local derby", "city derby", "rivalry", "local rivals"],
    "title_race": ["title implications", "championship race", "league title"],
    "relegation": ["relegation battle", "staying up", "drop zone"],
    "european_qualification": [
        "top 4",
        "european spots",
        "champions league qualification",
    ],
    # Situational contexts
    "comeback": ["fightback", "turnaround", "recovered from behind"],
    "upset": ["giant killing", "shock result", "underdog victory"],
    "milestone": ["landmark", "achievement", "record", "first time"],
    "injury_return": ["comeback from injury", "returning from", "back from layoff"],
    # Tactical contexts
    "high_scoring": ["goal fest", "thriller", "entertaining", "end-to-end"],
    "defensive": ["cagey affair", "tight game", "low scoring", "tactical battle"],
    "counter_attack": ["on the break", "transition", "quick attack"],
    "set_piece": ["from corners", "free kick", "penalty", "dead ball"],
}

OPPONENT_CATEGORIES = {
    "premier_league_big_six": [
        "arsenal",
        "chelsea",
        "liverpool",
        "manchester city",
        "manchester united",
        "tottenham",
    ],
    "la_liga_big_three": ["real madrid", "barcelona", "atletico madrid"],
    "serie_a_big_four": ["juventus", "ac milan", "inter milan", "napoli"],
    "bundesliga_top_four": [
        "bayern munich",
        "borussia dortmund",
        "rb leipzig",
        "bayer leverkusen",
    ],
    "champions_league_regulars": [
        "real madrid",
        "barcelona",
        "bayern munich",
        "manchester city",
        "liverpool",
        "psg",
    ],
}


class EnhancedSoccerQueryParser(SoccerQueryParser):
    def __init__(self):
        super().__init__()
        self.soccer_entities = SOCCER_ENTITIES
        self.soccer_stats = SOCCER_STATISTICS
        self.soccer_contexts = SOCCER_CONTEXTS
        self.opponent_categories = OPPONENT_CATEGORIES

    def _extract_entities_enhanced(self, query: str) -> List[SoccerEntity]:
        """Enhanced entity extraction with soccer-specific knowledge"""
        entities = []
        query_lower = query.lower()

        # Enhanced player recognition
        for player_name, aliases in self.soccer_entities["players"].items():
            if any(
                alias.lower() in query_lower for alias in [player_name] + aliases
            ):
                print(f"Player name: {player_name}, alias: {aliases}")
                entities.append(
                    SoccerEntity(
                        name=player_name.title(),
                        entity_type=EntityType.PLAYER,
                        aliases=aliases,
                        confidence=0.95,
                    )
                )

        # Enhanced team recognition
        for team_name, aliases in self.soccer_entities["teams"].items():
            if any(alias.lower() in query_lower for alias in [team_name] + aliases):
                entities.append(
                    SoccerEntity(
                        name=team_name.title(),
                        entity_type=EntityType.TEAM,
                        aliases=aliases,
                        confidence=0.95,
                    )
                )
        for comp_name, aliases in self.soccer_entities["competitions"].items():
            if any(alias.lower() in query_lower for alias in [comp_name] + aliases):
                entities.append(
                    SoccerEntity(
                        name=comp_name.title(),
                        entity_type=EntityType.COMPETITION,
                        aliases=aliases,
                        confidence=0.9,
                    )
                )

        return entities

    def _extract_soccer_context(self, query: str) -> Dict[str, Any]:
        """Extract soccer-specific contextual information"""
        context = {}
        query_lower = query.lower()

        # Match context
        for context_type, keywords in self.soccer_contexts.items():
            if any(keyword in query_lower for keyword in keywords):
                context["match_context"] = context_type
                break

        # Opponent category
        for category, teams in self.opponent_categories.items():
            if any(team.lower() in query_lower for team in teams):
                context["opponent_category"] = category
                break

        # Tactical context
        tactical_keywords = {
            "attacking": ["attacking", "offensive", "going forward", "in attack"],
            "defensive": ["defending", "defensive", "at the back", "defensively"],
            "midfield": ["midfield", "middle of the park", "center", "playmaking"],
            "set_pieces": [
                "corner",
                "free kick",
                "penalty",
                "set piece",
                "dead ball",
            ],
        }

        for tactical_type, keywords in tactical_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                context["tactical_focus"] = tactical_type
                break

        return context

    def parse_query_enhanced(self, query: str) -> ParsedSoccerQuery:
        """Enhanced parsing with soccer-specific improvements"""
        # Use enhanced entity extraction
        entities = self._extract_entities_enhanced(query)

        # Get standard parsing results
        base_parsed = self.parse_query(query)

        # Add enhanced soccer context
        soccer_context = self._extract_soccer_context(query)
        enhanced_filters = {**base_parsed.filters, **soccer_context}

        # Create enhanced parsed query
        return ParsedSoccerQuery(
            original_query=query,
            entities=entities if entities else base_parsed.entities,
            time_context=base_parsed.time_context,
            comparison_type=base_parsed.comparison_type,
            filters=enhanced_filters,
            statistic_requested=base_parsed.statistic_requested,
            confidence=min(
                base_parsed.confidence + 0.1, 1.0
            ),  # Boost confidence slightly
            query_intent=base_parsed.query_intent,
        )


# Real-world query examples for testing
REAL_WORLD_SOCCER_QUERIES = [
    # Player performance queries
    "How many goals has Haaland scored in Manchester derbies?",
    "What's Salah's conversion rate against the big six this season?",
    "How does Messi's El Clasico record compare to Ronaldo's?",
    "Is this Mbappe's best Champions League campaign?",
    # Team analysis queries
    "What's Arsenal's home record against top 6 teams?",
    "How many clean sheets has City kept in away games?",
    "What's Barcelona's possession average in La Liga this season?",
    "How does Liverpool's pressing compare to last season?",
    # Tactical and contextual queries
    "How significant is this comeback for Arsenal's title hopes?",
    "What's the historical significance of this North London Derby result?",
    "How rare is a hat-trick in El Clasico?",
    "What storylines emerge from Kane's return to Tottenham?",
    # Comparative analysis
    "Who has better Champions League knockout stats: Benzema or Lewandowski?",
    "How does City's away form compare to their home dominance?",
    "What's more impressive: Haaland's goal rate or Messi's assist rate?",
    # Historical context
    "When did Liverpool last win at Old Trafford?",
    "What's the longest goal drought in Messi's Clasico history?",
    "How does this Barcelona comeback rank historically?",
    # Complex multi-entity queries
    "What factors contributed to Real Madrid's Champions League success against PSG?",
    "How has Guardiola's tactical evolution affected City's European performances?",
    "What makes this Liverpool vs City title race historically significant?",
]


def test_enhanced_parser():
    """Test the enhanced parser with real-world queries"""
    parser = EnhancedSoccerQueryParser()

    print("🚀 Testing Enhanced Soccer Query Parser\n")
    print("=" * 70)

    success_count = 0
    total_queries = len(REAL_WORLD_SOCCER_QUERIES)

    for i, query in enumerate(REAL_WORLD_SOCCER_QUERIES, 1):
        print(f"\n{i:2d}. Query: {query}")
        print("-" * 50)

        try:
            parsed = parser.parse_query_enhanced(query)

            # Display results
            print(f"Intent: {parsed.query_intent}")
            print(
                f"Entities: {[(e.name, e.entity_type.value) for e in parsed.entities]}"
            )
            print(f"Statistic: {parsed.statistic_requested or 'None'}")
            print(f"Time Context: {parsed.time_context.value}")
            print(
                f"Comparison: {parsed.comparison_type.value if parsed.comparison_type else 'None'}"
            )
            print(f"Filters: {parsed.filters}")
            print(f"Confidence: {parsed.confidence:.2f}")

            # Success criteria
            has_entities = len(parsed.entities) > 0
            has_reasonable_confidence = parsed.confidence > 0.6
            has_valid_intent = parsed.query_intent in [
                "stat_lookup",
                "comparison",
                "historical",
                "context",
            ]

            if has_entities and has_reasonable_confidence and has_valid_intent:
                success_count += 1
                print("✅ PASSED")
            else:
                print("❌ NEEDS IMPROVEMENT")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'='*70}")
    print(f"📊 RESULTS: {success_count}/{total_queries} queries parsed successfully")
    print(f"Success Rate: {(success_count/total_queries)*100:.1f}%")

    if success_count >= total_queries * 0.8:  # 80% success threshold
        print("🎉 Parser ready for Epic 1 implementation!")
    else:
        print("⚠️  Parser needs refinement before proceeding to Epic 2")


# Integration helpers for your agent system
class SoccerIntelligenceInterface:
    """
    Interface class for your agents to interact with the Soccer Intelligence Layer
    This is what your Research, Writing, and Editor agents will use
    """

    def __init__(self, parser, query_builder, supabase_client):
        self.parser = parser
        self.query_builder = query_builder
        self.db = supabase_client
        self.session_memory = {}

    async def ask(
        self, question: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Main interface method for agents to ask soccer intelligence questions
        """
        try:
            # Parse the natural language question
            parsed_query = self.parser.parse_query_enhanced(question)

            # Execute database query
            result = await self.query_builder.build_and_execute_query(parsed_query)

            # Generate narrative response (this would connect to SIL-003)
            narrative_response = await self._generate_narrative_response(
                result, parsed_query, context
            )

            return {
                "question": question,
                "main_insight": narrative_response["main_insight"],
                "supporting_context": narrative_response["supporting_context"],
                "article_angles": narrative_response["article_angles"],
                "raw_data": result.data,
                "confidence_score": result.confidence,
                "suggested_follow_ups": self._suggest_follow_ups(parsed_query),
            }

        except Exception as e:
            return {
                "question": question,
                "error": str(e),
                "confidence_score": 0.0,
                "suggested_alternatives": self._suggest_alternative_queries(question),
            }

    async def _generate_narrative_response(self, result, parsed_query, context):
        """Generate narrative response from raw data (placeholder for SIL-003)"""
        # This is where you'll integrate with OpenAI/Claude for narrative generation
        return {
            "main_insight": f"Based on the data analysis for your query about {parsed_query.original_query}...",
            "supporting_context": ["Context point 1", "Context point 2"],
            "article_angles": ["Narrative angle 1", "Narrative angle 2"],
        }

    def _suggest_follow_ups(self, parsed_query):
        """Suggest related queries based on current query"""
        suggestions = []

        if parsed_query.query_intent == "stat_lookup":
            suggestions.extend(
                [
                    "How does this compare to league average?",
                    "What's the historical context of this performance?",
                    "How significant is this statistically?",
                ]
            )

        elif parsed_query.query_intent == "comparison":
            suggestions.extend(
                [
                    "What factors explain this difference?",
                    "How consistent is this pattern over time?",
                    "What other players/teams show similar patterns?",
                ]
            )

        return suggestions[:3]  # Return top 3 suggestions

    def _suggest_alternative_queries(self, failed_query):
        """Suggest alternative phrasings for failed queries"""
        return [
            "Try asking about specific statistics (goals, assists, clean sheets)",
            "Include time context (this season, career, last 5 games)",
            "Specify the competition (Premier League, Champions League)",
        ]


# Example usage for your agents
async def example_agent_integration():
    """
    Example of how your Research Agent would use the Soccer Intelligence Layer
    """

    # Initialize the soccer intelligence interface (pseudo-code)
    parser = EnhancedSoccerQueryParser()
    # query_builder = SoccerDatabaseQueryBuilder(supabase_client)
    # soccer_intel = SoccerIntelligenceInterface(parser, query_builder, supabase_client)

    # Example Research Agent workflow
    research_queries = [
        "What storylines should fans know about tonight's Arsenal vs Tottenham derby?",
        "How significant is Kane's goal scoring record at Emirates Stadium?",
        "What tactical battles might decide this North London Derby?",
    ]

    print("📋 Research Agent Workflow Example:")
    print("-" * 40)

    for query in research_queries:
        parsed = parser.parse_query_enhanced(query)
        print(f"Query: {query}")
        print(f"Intent: {parsed.query_intent} | Confidence: {parsed.confidence:.2f}")
        print(f"Entities: {[e.name for e in parsed.entities]}")
        print(f"Context: {parsed.filters}")
        print()

        # In real implementation:
        # response = await soccer_intel.ask(query, context={"match_id": "ARS_TOT_20240915"})
        # print(f"Insight: {response['main_insight']}")


if __name__ == "__main__":
    # Test the enhanced parser
    test_enhanced_parser()

    print(f"\n{'='*70}\n")

    # Show agent integration example
    import asyncio

    asyncio.run(example_agent_integration())
