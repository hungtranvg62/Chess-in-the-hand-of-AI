"""Rules every engine must follow (plan, Section 6: the shared search() interface).

Any module in engine/ that defines search() is found and tested automatically,
so these tests start running as soon as the first engine exists.
"""
import importlib
import pkgutil

import chess
import pytest

import engine

STATS_KEYS = {"nodes", "depth", "time", "score", "tt_hits", "qnodes"}
LIMITS = {"time_limit": 1.0, "depth": 2}

POSITIONS = {
    "start": chess.STARTING_FEN,
    "black to move": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "middlegame": "r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6",
    "only one legal move": "k7/8/8/8/8/8/1q6/K7 w - - 0 1",
    "endgame": "8/5pk1/4p1p1/3pP3/1b1P1P2/4BK2/6PP/8 w - - 0 40",
}


def find_engines():
    engines = []
    for info in pkgutil.iter_modules(engine.__path__):
        if info.ispkg:
            continue
        module = importlib.import_module(f"engine.{info.name}")
        if callable(getattr(module, "search", None)):
            engines.append(pytest.param(module.search, id=info.name))
    return engines


ENGINES = find_engines()   # empty list -> pytest skips these tests


def played_board():
    """A middlegame position with a real move stack (needed for repetition checks)."""
    board = chess.Board()
    for san in "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7".split():
        board.push_san(san)
    return board


@pytest.mark.parametrize("search", ENGINES)
@pytest.mark.parametrize("fen", POSITIONS.values(), ids=list(POSITIONS))
def test_returns_a_legal_move(search, fen):
    board = chess.Board(fen)
    move, _ = search(board, **LIMITS)
    assert move in board.legal_moves


@pytest.mark.parametrize("search", ENGINES)
def test_stats_have_all_keys(search):
    _, stats = search(chess.Board(), **LIMITS)
    assert STATS_KEYS <= stats.keys()
    assert all(isinstance(stats[key], (int, float)) for key in STATS_KEYS)


@pytest.mark.parametrize("search", ENGINES)
@pytest.mark.parametrize("time_limit", [1.0, 0.01], ids=["normal", "tiny time limit"])
def test_board_is_unchanged(search, time_limit):
    board = played_board()
    before = (board.fen(), list(board.move_stack))
    search(board, time_limit=time_limit, depth=3)
    assert (board.fen(), list(board.move_stack)) == before


@pytest.mark.parametrize("search", ENGINES)
def test_returns_none_when_the_game_is_over(search):
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert board.is_checkmate()
    move, _ = search(board, **LIMITS)
    assert move is None
