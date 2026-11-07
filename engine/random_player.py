"""Placeholder engine: random legal moves, for testing the UI (owner: Hưng).

It follows the shared search() rules (game/interface.py), so the UI, the test
runner and tests/test_engine_contract.py can use it before any real level exists.
"""
import random
import time

from game.interface import new_stats


def search(board, time_limit=None, depth=None, node_limit=None):
    """Pick a random legal move. The limits are ignored: it never needs time."""
    start = time.perf_counter()
    stats = new_stats()
    moves = list(board.legal_moves)        # reading the board only: it stays unchanged
    stats["nodes"] = len(moves)
    stats["depth"] = 1 if moves else 0
    stats["time"] = time.perf_counter() - start
    return (random.choice(moves) if moves else None), stats
