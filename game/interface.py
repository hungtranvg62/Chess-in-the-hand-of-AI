"""Shared search() interface, stats and time/node limits (owner: Hưng).

Every engine in engine/ provides one function with this shape (see SearchFunction):

    def search(board, time_limit=None, depth=None, node_limit=None):
        ...
        return move, stats

Rules for every engine (checked by tests/test_engine_contract.py):
- work on board.copy(): never change the caller's board;
- return (None, stats) when the game is over;
- start the stats from new_stats(), so all engines report the same keys.

Scores are in centipawns (1 pawn = 100).
"""
from __future__ import annotations

import time
from typing import Protocol

import chess

INF = 10**9
MATE = 100_000        # a mate found at ply p scores MATE - p, so faster mates score higher

STATS_KEYS = ("nodes", "depth", "time", "score", "tt_hits", "qnodes")


class SearchFunction(Protocol):
    """The shape of every engine's search() function."""

    def __call__(self, board: chess.Board, time_limit: float | None = None,
                 depth: int | None = None,
                 node_limit: int | None = None) -> tuple[chess.Move | None, dict]: ...


def new_stats() -> dict:
    """A fresh stats dictionary with the keys every engine must report."""
    return {"nodes": 0, "depth": 0, "time": 0.0, "score": 0, "tt_hits": 0, "qnodes": 0}


class SearchTimeout(Exception):
    """Raised inside a search when the time or node limit is reached."""


class Limits:
    """Time and node limits for one search.

    Call check(stats) at every node: it raises SearchTimeout when a limit is reached.
    After each finished depth, call deeper_ok(stats): False means the next depth would
    probably not finish, so stop and keep the result of the last completed depth.
    """

    CLOCK_EVERY = 1024    # reading the clock is slow in Python, so only every N nodes

    def __init__(self, time_limit: float | None = None, node_limit: int | None = None):
        self.time_limit = time_limit
        self.node_limit = node_limit
        self.start = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self.start

    def check(self, stats: dict) -> None:
        searched = stats["nodes"] + stats["qnodes"]
        if self.node_limit is not None and searched >= self.node_limit:
            raise SearchTimeout
        if (self.time_limit is not None and searched % self.CLOCK_EVERY == 0
                and self.elapsed() >= self.time_limit):
            raise SearchTimeout

    def deeper_ok(self, stats: dict) -> bool:
        if self.time_limit is not None and self.elapsed() > self.time_limit * 0.5:
            return False
        if self.node_limit is not None and stats["nodes"] + stats["qnodes"] > self.node_limit * 0.5:
            return False
        return True


def is_terminal(board: chess.Board, ply: int) -> bool:
    """True if the search must stop here: game over, or a repeated position.

    A position that already appeared counts as a draw inside the search (ply > 0 only:
    the root must still return a move). board.is_game_over() alone only sees fivefold
    repetition, and board.can_claim_draw() is far too slow to call at every node.
    """
    return board.is_game_over() or (ply > 0 and board.is_repetition(2))


def terminal_score(board: chess.Board, ply: int) -> int:
    """Score of a position where is_terminal() is True, from White's point of view.

    For negamax (score from the side to move), use: -(MATE - ply) if mated, else 0.
    """
    if board.is_checkmate():
        return -(MATE - ply) if board.turn == chess.WHITE else MATE - ply
    return 0              # stalemate, insufficient material, 75-move rule, repetition
