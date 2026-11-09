import random
import chess

from engine.greedy import search
from engine.evaluation.material import evaluate


def test_returns_legal_move():
    board = chess.Board()
    move, stats = search(board)
    assert move in board.legal_moves


def test_board_is_not_changed():
    board = chess.Board()
    fen_before = board.fen()
    search(board)
    assert board.fen() == fen_before
    assert len(board.move_stack) == 0


def test_takes_free_queen():
    board = chess.Board("4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1")
    move, stats = search(board)
    assert move == chess.Move.from_uci("e4d5")


def test_plays_mate_in_one():
    board = chess.Board("6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
    move, stats = search(board)
    assert move == chess.Move.from_uci("a1a8")


def test_same_seed_same_move():
    board = chess.Board()
    m1, _ = search(board, rng=random.Random(42))
    m2, _ = search(board, rng=random.Random(42))
    assert m1 == m2


def test_stats_keys():
    _, stats = search(chess.Board())
    for key in ("nodes", "depth", "time", "score", "tt_hits", "qnodes"):
        assert key in stats


def test_material_start_position_is_zero():
    assert evaluate(chess.Board()) == 0