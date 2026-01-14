class InvalidGameError(ValueError):
    """
    Exception raised when the provided bowling game data violates the rules.

    This custom exception allows consumers to distinguish between
    validation errors (business logic) and generic value errors.
    """
    pass

# Type definition for a single Frame (List of rolls as strings)
# Utilizes Python 3.12+ type alias syntax for clarity.
type Frame = list[str]

class BowlingGame:
    """
    A scoring engine for 10-pin bowling.
    Supports partially complete games by returning None for future frames.
    """

    def score_game(self, frames: list[Frame]) -> list[int | None]:
        """
        Calculates the cumulative score for a bowling game.

        This is the main entry point for the library. It orchestrates the
        validation, parsing, and scoring pipeline.

        Args:
            frames: A list of frames, where each frame is a list of string rolls.
                    Example: [['8', '/'], ['X'], ...]

        Returns:
            A list of exactly 10 items (integers or None). Each item represents
            the cumulative score at the end of that frame. Future frames in
            partial games are represented as None.
        """
        self._validate_structure(frames)
        rolls = self._parse_frames_to_rolls(frames)
        return self._calculate_cumulative_scores(rolls)

    def _validate_structure(self, frames: list[Frame]) -> None:
        """
        Validates the high-level structural integrity of the game input.

        Checks that the game does not exceed the maximum allowed length of
        10 frames. Detailed frame-level validation occurs during parsing.

        Args:
            frames: The input list of frames to check.

        Raises:
            InvalidGameError: If the input contains more than 10 frames.
        """
        # Allow partial games (<= 10 frames)
        if len(frames) > 10:
            raise InvalidGameError(f"Game cannot have more than 10 frames, got {len(frames)}")

    def _parse_frames_to_rolls(self, frames: list[Frame]) -> list[int]:
        """
        Converts string frames into integers.
        """
        """
        Converts the list of string frames into a flat list of integer pinfalls.

        This method also performs strict validation on a frame-by-frame basis,
        ensuring compliance with bowling rules (e.g., max 10 pins per frame,
        correct roll counts). Valid inputs: '0'-'9', 'X', 'x', '/'.

        Args:
            frames: The raw string input frames.

        Returns:
            A flat list of integers representing the number of pins knocked down
            per ball. Spares are converted to their numeric remainder.

        Raises:
            InvalidGameError: If any frame violates bowling physics or structure.
        """
        rolls: list[int] = []

        for index, frame in enumerate(frames):
            # --- VALIDATION BLOCK ---

            # Rule 1: Frames 1-9 can have at most 2 rolls
            if index < 9 and len(frame) > 2:
                 raise InvalidGameError(f"Frame {index+1} has too many rolls ({len(frame)}). Max is 2.")

            # Rule 2: Frames 1-9, if Strike, must be the ONLY roll
            if index < 9 and any(r.upper() == 'X' for r in frame):
                # Check position first, THEN check length.
                # This ensures ["0", "X"] fails with "Must be first roll"
                if frame[0].upper() != 'X':
                    raise InvalidGameError(f"Frame {index+1}: Strike must be the first roll.")
                if len(frame) != 1:
                    raise InvalidGameError(f"Frame {index+1} is a Strike but has extra rolls.")

            # Rule 3: 10th Frame Logic
            if index == 9:
                if len(frame) > 3:
                    raise InvalidGameError(f"Frame 10 has too many rolls ({len(frame)}). Max is 3.")
                # Check for "Unearned Bonus": If 3 rolls, you must have struck or spared.
                if len(frame) == 3:
                    # It's earned if 1st is X OR 2nd is /
                    if frame[0].upper() != 'X' and (len(frame) > 1 and frame[1] != '/'):
                        raise InvalidGameError("Frame 10: Extra roll only allowed for Strike or Spare.")

            # --- PARSING BLOCK ---

            # We track the sum of pins purely for the "Law of Physics" check (Sum <= 10)
            frame_pin_sum = 0

            for i, roll_str in enumerate(frame):
                roll_str = roll_str.strip()
                upper_str = roll_str.upper()

                if upper_str == 'X':
                    rolls.append(10)
                    frame_pin_sum += 10 # Reset/Logic handled by complexity of 10th frame usually

                elif roll_str == '/':
                    if i == 0:
                         raise InvalidGameError(f"Frame {index+1}: Spare cannot be the first roll.")

                    # You cannot Spare if the previous roll was X or /
                    prev_symbol = frame[i-1].strip().upper()
                    if prev_symbol == 'X' or prev_symbol == '/':
                        raise InvalidGameError(f"Frame {index+1}: Spare cannot follow '{prev_symbol}'.")

                    previous_roll = rolls[-1]
                    rolls.append(10 - previous_roll)
                    frame_pin_sum = 10 # A spare completes the 10 count
                else:
                    try:
                        val = int(roll_str)
                    except ValueError:
                        raise InvalidGameError(
                            f"Invalid symbol found: '{roll_str}'. Valid inputs are '0'-'9', 'X', 'x', and '/'."
                        )

                    if val < 0 or val > 9:
                        raise InvalidGameError(f"Invalid pin count: {val}")

                    # Rule 4: 10th Frame Logic for consecutive open pins
                    # (e.g., checks against 'X, 5, 6' or '5, 5' without slash)
                    if index == 9 and i > 0:
                         prev_roll = frame[i-1]
                         # If previous roll was also a number (not a mark), check their sum
                         if prev_roll.isdigit():
                             prev_val = int(prev_roll)
                             if prev_val + val > 10:
                                 raise InvalidGameError(f"Frame 10: Bonus rolls '{prev_roll}, {roll_str}' exceed 10 pins.")
                             if prev_val + val == 10:
                                 raise InvalidGameError(f"Frame 10: Spare '{prev_roll}, {roll_str}' must use '/'.")

                    rolls.append(val)
                    frame_pin_sum += val

                    # Rule 5: "Law of Physics" - Open Frames cannot exceed 9.
                    # If they equal 10, they should be '/', if > 10, it's impossible.
                    # We only check this if NOT a strike (which resets logic) and NOT a spare (which fixes sum to 10)
                    if index < 9 and i == 1 and 'X' not in [r.upper() for r in frame] and '/' not in frame:
                        if frame_pin_sum == 10:
                            raise InvalidGameError(f"Frame {index+1}: Sum is 10. You must use '/' for spares.")
                        elif frame_pin_sum > 10:
                            raise InvalidGameError(f"Frame {index+1}: Sum of pins {frame_pin_sum} is invalid.")

        return rolls

    def _calculate_cumulative_scores(self, rolls: list[int]) -> list[int | None]:
        """
        Calculates the running total score for each frame.

        Iterates through 10 frames, applying standard bowling logic:
        - Open Frame: Sum of 2 rolls.
        - Spare: 10 + next 1 roll.
        - Strike: 10 + next 2 rolls.

        Args:
            rolls: A flat list of integer pinfalls.

        Returns:
            A list of 10 cumulative scores. If a frame cannot be calculated
            due to insufficient data (partial game), its score is None.
        """
        # Initialize results with None
        cumulative_scores: list[int | None] = [None] * 10
        running_total = 0
        roll_index = 0

        for frame in range(10):
            # If we don't even have a roll for this frame start, we are done
            if roll_index >= len(rolls):
                break

            current_roll = rolls[roll_index]
            frame_score = 0

            # Logic: Check if we have enough data to score this frame.
            # If not, we break (leaving this and future frames as None).

            if current_roll == 10: # Strike
                # We need the strike (1) + 2 bonus rolls
                if roll_index + 2 >= len(rolls):
                    break # Not enough data yet

                frame_score = 10 + rolls[roll_index + 1] + rolls[roll_index + 2]
                roll_index += 1 # Advance 1 position

            else: # Open or Spare
                # We need at least 2 rolls for the frame itself
                if roll_index + 1 >= len(rolls):
                    break # waiting for second roll of frame

                second_roll = rolls[roll_index + 1]

                if current_roll + second_roll == 10: # Spare
                    # We need the 2 frame rolls + 1 bonus roll
                    if roll_index + 2 >= len(rolls):
                        break # waiting for bonus roll

                    frame_score = 10 + rolls[roll_index + 2]
                    roll_index += 2
                else: # Open Frame
                    frame_score = current_roll + second_roll
                    roll_index += 2

            running_total += frame_score
            cumulative_scores[frame] = running_total

        return cumulative_scores