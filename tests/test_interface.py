"""Tests for game/interface.py: stats, limits and terminal scores."""
import time

import chess
import pytest

from game.interface import (MATE, STATS_KEYS, Limits, SearchTimeout, is_terminal,
                            new_stats, terminal_score)


def play(*sans):
    board = chess.Board()
    for san in sans:
        board.push_san(san)
    return board


def test_new_stats_has_all_keys_and_is_fresh():
    stats = new_stats()
    assert tuple(stats) == STATS_KEYS
    stats["nodes"] = 5
    assert new_stats()["nodes"] == 0


def test_no_limits_never_stop():
    limits, stats = Limits(), new_stats()
    stats["nodes"] = 10**6
    limits.check(stats)
    assert limits.deeper_ok(stats)


def test_node_limit_stops_the_search():
    limits, stats = Limits(node_limit=100), new_stats()
    stats["nodes"], stats["qnodes"] = 60, 39
    limits.check(stats)                              # 99 positions: still fine
    stats["qnodes"] = 40
    with pytest.raises(SearchTimeout):
        limits.check(stats)                          # 100 positions: stop


def test_time_limit_stops_the_search():
    limits = Limits(time_limit=0.01)
    time.sleep(0.02)
    with pytest.raises(SearchTimeout):
        limits.check(new_stats())


def test_deeper_ok_stops_after_half_the_budget():
    limits, stats = Limits(node_limit=1000), new_stats()
    stats["nodes"] = 400
    assert limits.deeper_ok(stats)
    stats["nodes"] = 600
    assert not limits.deeper_ok(stats)


def test_white_mated_scores_negative():
    board = play("f3", "e5", "g4", "Qh4#")
    assert is_terminal(board, 4)
    assert terminal_score(board, 4) == -(MATE - 4)


def test_black_mated_scores_positive_and_faster_mate_is_better():
    board = play("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#")
    assert terminal_score(board, 1) == MATE - 1
    assert terminal_score(board, 1) > terminal_score(board, 5)


def test_stalemate_scores_zero():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert is_terminal(board, 1)
    assert terminal_score(board, 1) == 0


def test_repetition_is_terminal_inside_the_search_only():
    board = play("Nf3", "Nf6", "Ng1", "Ng8")         # start position again
    assert not is_terminal(board, 0)                 # the root must still pick a move
    assert is_terminal(board, 1)
    assert terminal_score(board, 1) == 0
