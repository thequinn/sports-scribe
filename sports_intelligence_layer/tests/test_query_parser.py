import unittest
from dataclasses import asdict
from sports_intelligence_layer.src.query_parser import (
    SoccerQueryParser,
    EntityType,
    TimeContext,
    ComparisonType,
)


class TestSoccerQueryParser(unittest.TestCase):
    def setUp(self):
        self.parser = SoccerQueryParser()

    # PASSED
    def test_basic_player_goal_query(self):
        """Test: How many goals has Haaland scored this season?"""
        query = "How many goals has Haaland scored this season?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.query_intent, "stat_lookup")
        self.assertEqual(parsed.statistic_requested, "goals")
        self.assertEqual(parsed.time_context, TimeContext.THIS_SEASON)

        player_entities = [
            e for e in parsed.entities if e.entity_type == EntityType.PLAYER
        ]
        self.assertEqual(len(player_entities), 1)
        self.assertIn("Haaland", player_entities[0].name)
        self.assertGreater(parsed.confidence, 0.8)

    # PASSED
    def test_team_home_record_query(self):
        """Test: What's Arsenal's home record this season?"""
        query = "What's Arsenal's home record this season?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.query_intent, "stat_lookup")
        self.assertEqual(parsed.time_context, TimeContext.THIS_SEASON)
        self.assertEqual(parsed.filters.get("venue"), "home")

        team_entities = [e for e in parsed.entities if e.entity_type == EntityType.TEAM]
        self.assertEqual(len(team_entities), 1)
        self.assertEqual(team_entities[0].name, "Arsenal")

    # PASSED
    def test_player_comparison_query(self):
        """Test: How does Messi's past completion compare to his career average?"""
        query = "How does Messi's past completion compare to his career average?"
        parsed = self.parser.parse_query(query)
        self.assertEqual(parsed.query_intent, "comparison")
        self.assertEqual(parsed.comparison_type, ComparisonType.VS_CAREER)
        self.assertEqual(parsed.statistic_requested, "pass_completion")

        player_entities = [
            e for e in parsed.entities if e.entity_type == EntityType.PLAYER
        ]
        self.assertGreater(len(player_entities), 0)
        self.assertIn("Messi", player_entities[0].name)

    # PASSED
    def test_head_to_head_query(self):
        """Test: When did Barcelona last beat Real Madrid?"""
        query = "When did Barcelona last beat Real Madrid?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.query_intent, "historical")

        team_entities = [e for e in parsed.entities if e.entity_type == EntityType.TEAM]
        team_names = [e.name for e in team_entities]
        self.assertIn("Barcelona", team_names)
        self.assertIn("Real Madrid", team_names)

    # PASSED
    def test_clean_sheets_vs_big_six(self):
        """Test: What's Liverpool's clean sheet record against the big six?"""
        query = "What's Liverpool's clean sheet record against the big six?"
        parsed = self.parser.parse_query(query)
        self.assertEqual(parsed.statistic_requested, "clean_sheets")
        self.assertEqual(parsed.filters.get("opponent_tier"), "top_6")

        team_entities = [e for e in parsed.entities if e.entity_type == EntityType.TEAM]
        self.assertEqual(len(team_entities), 1)
        self.assertEqual(team_entities[0].name, "Liverpool")

    # PASSED
    def test_champions_league_context(self):
        """Test: How many goals has Mbappe scored in the Champions League?"""
        query = "How many goals has Mbappe scored in the Champions League?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.statistic_requested, "goals")
        self.assertEqual(parsed.time_context, TimeContext.CHAMPIONS_LEAGUE)

        player_entities = [
            e for e in parsed.entities if e.entity_type == EntityType.PLAYER
        ]
        self.assertGreater(len(player_entities), 0)

    # PASSED
    def test_significance_context_query(self):
        """Test: How significant is Salah's performance against City?"""
        query = "How significant is Salah's performance against City?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.query_intent, "context")

        entities = parsed.entities
        player_entities = [e for e in entities if e.entity_type == EntityType.PLAYER]
        team_entities = [e for e in entities if e.entity_type == EntityType.TEAM]

        self.assertGreater(len(player_entities), 0)
        self.assertGreater(len(team_entities), 0)

    # PASSED
    def test_multiple_stats_query(self):
        """Test: What are Benzema's goals and assists this season?"""
        query = "What are Benzema's goals and assists this season?"
        parsed = self.parser.parse_query(query)

        # Should pick up "goals" as primary statistic
        # (assists would be secondary - handled in response generation)
        self.assertIn(parsed.statistic_requested, ["goals", "assists"])
        self.assertEqual(parsed.time_context, TimeContext.THIS_SEASON)

    # PASSED
    def test_away_performance_query(self):
        """Test: How has Chelsea performed away from home this season?"""
        query = "How has Chelsea performed away from home this season?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.filters.get("venue"), "away")
        self.assertEqual(parsed.time_context, TimeContext.THIS_SEASON)

        team_entities = [e for e in parsed.entities if e.entity_type == EntityType.TEAM]
        self.assertEqual(len(team_entities), 1)
        self.assertEqual(team_entities[0].name, "Chelsea")

    # PASSED
    def test_derby_match_query(self):
        """Test: What's the history of Manchester derbies?"""
        query = "What's the history of Manchester derbies?"
        parsed = self.parser.parse_query(query)

        self.assertEqual(parsed.query_intent, "historical")
        self.assertEqual(parsed.filters.get("match_type"), "derby")


class SoccerQueryParserIntegrationTest(unittest.TestCase):
    """Integration tests that simulate real agent workflows"""

    def setUp(self):
        self.parser = SoccerQueryParser()

    def test_research_agent_workflow(self):
        """Simulate Research Agent discovering storylines for a match"""
        queries = [
            "What storylines should fans know about tonight's Arsenal vs Tottenham game?",
            "How significant is Kane's return to North London?",
            "What's the head-to-head record in recent North London derbies?",
        ]

        for query in queries:
            parsed = self.parser.parse_query(query)
            # Each query should be parsed successfully with reasonable confidence
            self.assertGreater(parsed.confidence, 0.5)
            self.assertIn(parsed.query_intent, ["context", "historical", "stat_lookup"])

    def test_writing_agent_workflow(self):
        """Simulate Writing Agent verifying and enhancing content"""
        queries = [
            "Is this Haaland's best month of the season?",
            "What additional context makes this performance meaningful?",
            "How does this compare to similar performances this season?",
        ]

        for query in queries:
            parsed = self.parser.parse_query(query)
            # Should handle comparison and context queries
            self.assertIn(parsed.query_intent, ["comparison", "context", "stat_lookup"])

    def test_editor_agent_workflow(self):
        """Simulate Editor Agent fact-checking claims"""
        queries = [
            "Is Messi the first player since Ronaldinho to achieve this feat?",
            "What important context is missing from this Benzema analysis?",
            "Verify: Liverpool has the best defensive record in Europe this season",
        ]

        for query in queries:
            parsed = self.parser.parse_query(query)
            # Editor queries often involve verification and context
            self.assertIn(parsed.query_intent, ["historical", "context", "comparison"])


def run_comprehensive_test_suite():
    """Run all tests and provide detailed results"""

    print("🧪 Running Soccer Query Parser Test Suite\n")

    # Test categories
    test_categories = [
        ("Basic Queries", TestSoccerQueryParser),
        ("Integration Workflows", SoccerQueryParserIntegrationTest),
    ]

    all_results = []

    for category_name, test_class in test_categories:
        print(f"📂 {category_name}")
        print("-" * 50)

        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        all_results.append((category_name, result))
        print("\n")

    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    total_tests = sum(r.testsRun for _, r in all_results)
    total_failures = sum(len(r.failures) for _, r in all_results)
    total_errors = sum(len(r.errors) for _, r in all_results)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failed: {total_failures}")
    print(f"Errors: {total_errors}")

    if total_failures == 0 and total_errors == 0:
        print("✅ All tests passed! Parser is ready for Epic 1.")
    else:
        print("❌ Some tests failed. Review and fix before proceeding.")


# Sample query analysis for development
def analyze_sample_queries():
    """Analyze a variety of soccer queries to understand patterns"""

    parser = SoccerQueryParser()

    sample_queries = [
        # Player Performance
        "How many goals has Haaland scored this season?",
        "What's Messi's pass completion rate in El Clasicos?",
        "How many assists does De Bruyne have at home this season?",
        # Team Performance
        "What's Arsenal's away record in the Premier League?",
        "How many clean sheets has Liverpool kept this season?",
        "What's Barcelona's win rate against Real Madrid?",
        # Comparisons
        "How does Salah's scoring compare to last season?",
        "Is this Benzema's best Champions League campaign?",
        "How does City's possession compare to league average?",
        # Historical Context
        "When did these teams last meet in a title decider?",
        "What's the significance of this Liverpool performance?",
        "How rare is a hat-trick in El Clasico?",
        # Complex Queries
        "What storylines emerge from Mbappe's performance against his former club?",
        "How significant is this comeback for Arsenal's title hopes?",
        "What context makes this derby result historically important?",
    ]

    print("🔍 Query Analysis Report\n")

    for i, query in enumerate(sample_queries, 1):
        print(f"{i:2d}. {query}")
        parsed = parser.parse_query(query)

        print(f"    Intent: {parsed.query_intent}")
        print(
            f"    Entities: {[(e.name, e.entity_type.value) for e in parsed.entities]}"
        )
        print(f"    Statistic: {parsed.statistic_requested}")
        print(f"    Time: {parsed.time_context.value}")
        print(
            f"    Comparison: {parsed.comparison_type.value if parsed.comparison_type else None}"
        )
        print(f"    Filters: {parsed.filters}")
        print(f"    Confidence: {parsed.confidence:.2f}")
        print()


if __name__ == "__main__":
    # Run comprehensive test suite
    run_comprehensive_test_suite()

    print("\n" + "=" * 60 + "\n")

    # Analyze sample queries
    analyze_sample_queries()
