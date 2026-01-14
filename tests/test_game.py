import pytest
from kingpin.game import BowlingGame, InvalidGameError

@pytest.fixture
def game():
    """Fixture to provide a fresh game instance for each test."""
    return BowlingGame()

def _verify_score(game, frames, expected, scenario_name=None):
    """
    Helper function to centralize scoring assertions.
    Reduces redundancy by sharing logic between the Acceptance Test and Parameterized Suite.
    """
    error_msg = f"Failed Scenario: {scenario_name}" if scenario_name else "Failed Acceptance Test"
    assert game.score_game(frames) == expected, error_msg

# --- ACCEPTANCE TEST FROM CHALLENGE DOCUMENT ---

def test_document_example_game(game):
    """
    Verifies the specific example provided in the requirements document.
    Matches the product owner's exact output contract.
    """
    frames = [
        ["8", "/"], ["5", "4"], ["9", "0"], ["X"], ["X"],
        ["5", "/"], ["5", "3"], ["6", "3"], ["9", "/"], ["9", "/", "X"]
    ]
    expected = [15, 24, 33, 58, 78, 93, 101, 110, 129, 149]

    _verify_score(game, frames, expected)

# --- PARAMETERIZED SCORING SUITE ---

@pytest.mark.parametrize("name, frames, expected", [
    (
        "Gutter Game",
        [["0", "0"]] * 10,
        [0] * 10
    ),
    (
        "All Ones",
        [["1", "1"]] * 10,
        [i * 2 for i in range(1, 11)]
    ),
    (
        "Perfect Game (12 Strikes)",
        [["X"]] * 9 + [["X", "X", "X"]],
        [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
    ),
    (
        "All Spares (5/ + bonus 5)",
        [["5", "/"]] * 9 + [["5", "/", "5"]],
        [15, 30, 45, 60, 75, 90, 105, 120, 135, 150]
    ),
    (
        "Dutch 200 (Alternating Strikes/Spares)",
        # Pattern: Strike, Spare, Strike, Spare... ending with Spare + Strike bonus
        [["X"], ["5", "/"]] * 4 + [["X"], ["5", "/", "X"]],
        [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
    ),
    (
        "The Heartbreaker (299 Game)",
        [["X"]] * 9 + [["X", "X", "9"]], # 11 Strikes + 9
        [30, 60, 90, 120, 150, 180, 210, 240, 270, 299]
    ),
    (
        "Empty Game (New Game State)",
        [],
        [None] * 10
    ),
    (
        "Partial Game: Dangling 10th Frame",
        [["X"]] * 9 + [["X", "X"]], # Missing the final bonus roll
        [30, 60, 90, 120, 150, 180, 210, 240, 270, None]
    ),
    (
        "Partial Game: Strike -> Open -> Wait",
        [["X"], ["5", "4"], ["X"]],
        [19, 28] + [None] * 8
    ),
    (
        "Partial Game: Dangling Open (Wait for 2nd roll)",
        [["5"]],
        [None] * 10
    ),
    (
        "Partial Game: Dangling Spare (Wait for bonus)",
        [["5", "/"]],
        [None] * 10
    ),
    (
        "Partial Game: Clean Stop (Open Frame -> Stop)",
        [["5", "4"]],
        [9] + [None] * 9
    ),
    (
        "Gutter Spares (0, /)",
        [["0", "/"]] * 9 + [["0", "/", "X"]],
        [10, 20, 30, 40, 50, 60, 70, 80, 90, 110]
    ),
    (
        "Lowercase Inputs (Robustness)",
        # Partial game using lowercase 'x'
        [["x"], ["5", "/"], ["x"]],
        [20, 40] + [None] * 8
    ),
    (
        "Whitespace Resilience",
        [[" X "], [" 5", "4 "]] + [["0", "0"]] * 8, # Dirty inputs
        [19, 28] + [28] * 8
    ),
    (
        "Dirty Whitespace (Tabs/Newlines)",
        [["\tX\n"], [" 5", "4\t"]] + [["0", "0"]] * 8,
        [19, 28] + [28] * 8
    ),

])
def test_scoring_scenarios(game, name, frames, expected):
    """
    Covers Standard, Edge, and Partial scoring scenarios using the shared verification logic.
    """
    _verify_score(game, frames, expected, name)

# --- PARAMETERIZED VALIDATION SUITE ---

@pytest.mark.parametrize("name, frames, match_string", [
    ("Spare at start", [["/", "5"]], "Spare cannot be the first roll"),
    ("Invalid character", [["A", "0"]], "Invalid symbol"),
    ("Too many frames", [["0", "0"]] * 11, "more than 10 frames"),
    ("Frame sum > 10", [["5", "6"]], "Sum of pins"),
    ("Frame sum = 10 (no /)", [["5", "5"]], "must use '/'"),
    ("Strike with extra roll", [["X", "2"]], "Strike but has extra rolls"),
    ("Strike as 2nd roll", [["0", "X"]], "Strike must be the first roll"),
    ("Normal frame too many rolls", [["3", "3", "3"]], "too many rolls"),
    ("10th Frame unearned bonus", [["X"]] * 9 + [["5", "3", "1"]], "Extra roll only allowed"),
    ("10th Frame too many rolls", [["X"]] * 9 + [["X", "X", "X", "X"]], "Frame 10 has too many rolls"),
    ("10th Frame Impossible Bonus (5+6)", [["X"]] * 9 + [["X", "5", "6"]], "exceed 10 pins"),
    ("10th Frame Notation (5+5)", [["X"]] * 9 + [["X", "5", "5"]], "must use '/'"),
    ("10th Frame Spare after Strike", [["X"]] * 9 + [["X", "/", "X"]], "Spare cannot follow"),
    ("10th Frame Double Spare", [["X"]] * 9 + [["5", "/", "/"]], "Spare cannot follow"),
    ("10th Frame Spare after Two Strikes", [["X"]] * 9 + [["X", "X", "/"]], "Spare cannot follow"),
    ("Negative pins", [["-1", "0"]], "Invalid pin count"),
    ("Pin count > 9", [["12", "0"]], "Invalid pin count"),
])
def test_validation_logic(game, name, frames, match_string):
    """
    Verifies that invalid inputs raise InvalidGameError with helpful messages.
    """
    with pytest.raises(InvalidGameError) as excinfo:
        game.score_game(frames)
    assert match_string in str(excinfo.value), f"Failed Scenario: {name}"