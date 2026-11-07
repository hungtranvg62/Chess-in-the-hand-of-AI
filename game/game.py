"""Game loop: players, legal moves, checkmate and draws (owner: Hưng).

The chess rules themselves come from python-chess. This module runs a game correctly
on top of them: it refuses illegal moves, ends the game at the right time (threefold
repetition and the 50-move rule included), supports undo, and records moves and stats.
The UI and the test runner (benchmark/) both use it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import chess
import chess.pgn

from game.interface import SearchFunction


class IllegalMoveError(ValueError):
    """Raised when a move is not legal in the current position."""


def make_board(start=None) -> chess.Board:
    """Build a starting board.

    start can be None (normal start), a FEN string, a string or list of SAN moves
    played from the normal start (an opening line), or a Board (copied).
    """
    if start is None:
        return chess.Board()
    if isinstance(start, chess.Board):
        return start.copy()
    if isinstance(start, str) and "/" in start:
        return chess.Board(start)
    board = chess.Board()
    for san in (start.split() if isinstance(start, str) else start):
        board.push_san(san)
    return board


class Game:
    """One game of chess. Use play() for moves, never board.push() directly."""

    def __init__(self, start=None):
        self.board = make_board(start)
        self._start_ply = len(self.board.move_stack)   # undo never goes before this

    def legal_moves(self, from_square: int | None = None) -> list[chess.Move]:
        """All legal moves, or only those of the piece on from_square (for UI hints)."""
        moves = self.board.legal_moves
        if from_square is None:
            return list(moves)
        return [m for m in moves if m.from_square == from_square]

    def play(self, move: chess.Move | str) -> chess.Move:
        """Play a legal move (a Move, UCI like 'e2e4', or SAN like 'Nf3')."""
        if self.is_over():
            raise IllegalMoveError("the game is over")
        if isinstance(move, str):
            move = self._parse(move)
        if move not in self.board.legal_moves:      # board.push() alone does not check
            raise IllegalMoveError(f"illegal move: {move}")
        self.board.push(move)
        return move

    def _parse(self, text: str) -> chess.Move:
        try:
            move = chess.Move.from_uci(text)
            if move in self.board.legal_moves:
                return move
        except ValueError:
            pass
        try:
            return self.board.parse_san(text)
        except ValueError as error:
            raise IllegalMoveError(f"illegal move: {text}") from error

    def undo(self, count: int = 1) -> int:
        """Take back up to `count` moves; returns how many were taken back."""
        undone = 0
        while undone < count and len(self.board.move_stack) > self._start_ply:
            self.board.pop()
            undone += 1
        return undone

    def plies(self) -> int:
        """Moves played since the game started (an opening line does not count)."""
        return len(self.board.move_stack) - self._start_ply

    # Threefold repetition and the 50-move rule end the game once they have really
    # happened. (board.is_game_over(claim_draw=True) is True one move earlier: as soon
    # as a player *could* claim the draw with their next move.)
    def _draw_rule(self) -> str | None:
        if self.board.is_repetition(3):
            return "threefold_repetition"
        if self.board.halfmove_clock >= 100:
            return "fifty_moves"
        return None

    def is_over(self) -> bool:
        return self.board.is_game_over() or self._draw_rule() is not None

    def result(self) -> str:
        """'1-0', '0-1', '1/2-1/2', or '*' while the game is still going."""
        if self.board.is_game_over():
            return self.board.result()
        return "1/2-1/2" if self._draw_rule() else "*"

    def reason(self) -> str | None:
        """Why the game ended, e.g. 'checkmate' or 'threefold_repetition'; None if not over."""
        outcome = self.board.outcome()
        return outcome.termination.name.lower() if outcome else self._draw_rule()

    def move_list(self) -> list[str]:
        """All moves in normal chess notation (SAN), from the first position."""
        board = self.board.root()
        sans = []
        for move in self.board.move_stack:
            sans.append(board.san(move))
            board.push(move)
        return sans

    def to_pgn(self, white: str = "?", black: str = "?", event: str = "?") -> str:
        pgn = chess.pgn.Game.from_board(self.board)
        pgn.headers["Event"] = event
        pgn.headers["White"] = white
        pgn.headers["Black"] = black
        pgn.headers["Result"] = self.result()
        return str(pgn)


class EnginePlayer:
    """Wraps any engine's search() so the UI and the test runner can use it."""

    def __init__(self, search: SearchFunction, name: str | None = None, **limits):
        self.search = search
        self.name = name or getattr(search, "__module__", "engine")
        self.limits = limits                  # time_limit, depth, node_limit
        self.last_stats: dict | None = None

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        move, stats = self.search(board.copy(), **self.limits)   # the engine never sees the real board
        self.last_stats = stats
        return move


@dataclass
class GameRecord:
    result: str                               # '1-0', '0-1' or '1/2-1/2'
    reason: str                               # 'checkmate', 'max_plies', 'adjudicated', ...
    moves: list[str]                          # SAN, from the first position
    stats: list[dict] = field(default_factory=list)   # one per move, in order
    pgn: str = ""


def play_game(white: EnginePlayer, black: EnginePlayer, start=None, max_plies: int = 300,
              adjudicate: Callable[[chess.Board], str | None] | None = None) -> GameRecord:
    """Play one full game without a screen.

    adjudicate(board) may return a result ('1-0', '0-1', '1/2-1/2') to stop the game
    early when it is clearly decided; the test runner uses this to save time.
    At max_plies the game is a draw.
    """
    game = Game(start)
    stats = []
    result = reason = None
    while not game.is_over():
        if game.plies() >= max_plies:
            result, reason = "1/2-1/2", "max_plies"
            break
        player = white if game.board.turn == chess.WHITE else black
        game.play(player.choose_move(game.board))   # an illegal engine move raises here
        stats.append(player.last_stats)
        if adjudicate and (decided := adjudicate(game.board)):
            result, reason = decided, "adjudicated"
            break
    if result is None:
        result, reason = game.result(), game.reason()
    record = GameRecord(result, reason, game.move_list(), stats)
    record.pgn = game.to_pgn(white.name, black.name)
    record.pgn = record.pgn.replace(f'[Result "{game.result()}"]', f'[Result "{result}"]', 1)
    return record
