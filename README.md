# Kingpin: Bowling Scoring Engine

A Python library for scoring 10-pin bowling games. This engine handles standard scoring rules, look-ahead logic for strikes/spares, and supports partially complete games via state-machine logic.

## 📦 Installation

This project requires **Python 3.12+**.

1. Clone the repository:

   ```bash
   git clone [https://github.com/thewoogier/kingpin.git](https://github.com/thewoogier/kingpin.git)
   cd kingpin
   ```

2. Install the package and development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## 🧪 Running Tests

The project uses `pytest` for its test suite and achieves **100% Code Coverage**.

### Run Standard Tests

```bash
pytest
```

### Run with Coverage Report

To verify the 100% coverage metric and view the line-by-line analysis:

1. Generate the report:

   ```bash
   pytest --cov=src --cov-report html
   ```

2. Open the report `htmlcov/index.html` in your browser. Platform-specific commands:

   **macOS:**

   ```bash
   open htmlcov/index.html
   ```

   **Windows (PowerShell/CMD):**

   ```bash
   start htmlcov/index.html
   ```

   **Linux:**

   ```bash
   xdg-open htmlcov/index.html
   ```

## 📐 Design Decisions

### 1. Python 3.12 & Modern Typing

I chose **Python 3.12** to leverage **PEP 695 (Type Parameter Syntax)**.

- **Decision:** Utilizing `type Frame = list[str]` provides semantic clarity over generic `List` types.
- **Impact:** Reduces boilerplate and makes the data structures self-documenting for other developers.

### 2. Project Structure (`src` Layout)

I utilized the **Src Layout** (`src/kingpin/`) rather than placing the package in the root.

- **Reasoning:** This forces tests to run against the _installed_ version of the package, simulating how a real user would import the library. It prevents "it works on my machine" bugs caused by accidental local file imports.

### 3. Input Strategy: "Option A" (Frames)

The engine accepts **Nested Lists of Strings** (e.g., `[['X'], ['7', '/']]`) rather than a flat list of rolls.

- **Trade-off:** I prioritized readability over raw algorithmic simplicity. While a flat list (Option B) is easier to process mathematically, grouping rolls into frames mirrors how humans actually visualize a bowling score sheet, making the data much more intuitive to debug.
- **Implementation:** To handle the scoring math efficiently while respecting the input format, the engine creates a Pipeline:
  1.  **Validate:** Ensure structural integrity (10 frames max).
  2.  **Parse:** Flatten the frames into a raw integer stream (`/` becomes the calculated remainder).
  3.  **Score:** Apply the strike/spare look-ahead logic on the flat stream.

### 4. Robust Validation ("Fail Fast")

The engine implements strict validation logic that raises `InvalidGameError` (a custom `ValueError` subclass) the moment an invalid state is detected.

- **Scope:** We validate "Laws of Physics" (e.g., pins > 10), Structural Rules (e.g., Strike must be the first roll), and Notation Rules (e.g., Spares cannot start a frame).
- **Benefit:** This prevents "Garbage In, Garbage Out" scenarios where an invalid game might produce a nonsensical score silently.

### 5. Handling Partial Games (State Machine)

The engine is designed to handle the reality that not all games get finished. Whether a player walks away early or you just want to check the score mid-game, the logic acts as a **State Machine**.

- **Approach:** Instead of crashing because a game isn't "done," the engine calculates the score for the frames it has and returns `None` for the rest.
- **Logic:** If a Strike is thrown in Frame 9, but the bonus rolls haven't happened yet, the engine recognizes the state is "Indeterminate" and waits for more data rather than guessing.

### 6. Hybrid Testing Strategy

The test suite (`tests/test_game.py`) utilizes a hybrid approach to maximize confidence and maintainability:

- **Contract Tests:** A standalone test (`test_document_example_game`) strictly validates the specific example provided in the requirements document, acting as the Source of Truth.
- **Parameterized Tests:** We use `pytest.mark.parametrize` to cover the edge cases (Scoring Scenarios and Validation Errors) without code duplication.
- **Shared Verification:** A helper function `_verify_score` ensures that both the Contract Test and the Parameterized Suite use the exact same assertion logic.
