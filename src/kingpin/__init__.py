"""
Kingpin: A production-grade bowling scoring engine.
Exposes the main entry points for the library.
"""

from .game import BowlingGame, InvalidGameError

__all__ = ["BowlingGame", "InvalidGameError"]
__version__ = "0.1.0"