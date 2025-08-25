# The "Brain" - Our Entity Database
# This is the central place for soccer knowledge for the parser.

# Priority entities help with disambiguation and focus.
PRIORITY_TEAMS = {
    "manchester city": {"aliases": ["man city", "city"]},
    "arsenal": {"aliases": ["gunners"]},
    "liverpool": {"aliases": ["reds", "lfc"]},
    "real madrid": {"aliases": ["real"]},
    "barcelona": {"aliases": ["barca"]},
    "bayern munich": {"aliases": ["bayern"]},
    "manchester united": {"aliases": ["man utd", "united"]},
}

PRIORITY_PLAYERS = {
    "erling haaland": {"aliases": ["haaland"]},
    "mohamed salah": {"aliases": ["salah", "mo salah"]},
    "harry kane": {"aliases": ["kane"]},
    "kevin de bruyne": {"aliases": ["de bruyne", "kdb"]},
    "lionel messi": {"aliases": ["messi"]},
    "kylian mbappe": {"aliases": ["mbappe"]},
}


STATISTICS_KEYWORDS = {
    "goals": ["goals", "scored", "goal"],
    "assists": ["assists", "assisted"],
    "clean sheets": ["clean sheets", "shutouts"],
    "hat-tricks": ["hat-tricks", "hat trick"],
}
