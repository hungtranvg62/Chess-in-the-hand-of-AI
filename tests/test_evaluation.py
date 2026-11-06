"""Checks for every evaluation function (plan, Sections 9 and 17).

Any module in engine/evaluation/ that defines evaluate(board) is found and tested
automatically. Scores are in centipawns from White's point of view.
"""
import importlib
import pkgutil

import chess
import pytest

import engine.evaluation

POSITIONS = {
    "start": chess.STARTING_FEN,
    "middlegame": "r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6",
    "unbalanced": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/5pk1/4p1p1/3pP3/1b1P1P2/4BK2/6PP/8 w - - 0 40",
}


def find_evaluations():
    evaluations = []
    for info in pkgutil.iter_modules(engine.evaluation.__path__):
        module = importlib.import_module(f"engine.evaluation.{info.name}")
        if callable(getattr(module, "evaluate", None)):
            evaluations.append(pytest.param(module.evaluate, id=info.name))
    return evaluations


EVALUATIONS = find_evaluations()   # empty list -> pytest skips these tests


@pytest.mark.parametrize("evaluate", EVALUATIONS)
def test_start_position_is_equal(evaluate):
    assert evaluate(chess.Board()) == 0


@pytest.mark.parametrize("evaluate", EVALUATIONS)
@pytest.mark.parametrize("fen", POSITIONS.values(), ids=list(POSITIONS))
def test_colour_flipped_position_has_opposite_score(evaluate, fen):
    board = chess.Board(fen)
    assert evaluate(board) == -evaluate(board.mirror())


@pytest.mark.parametrize("evaluate", EVALUATIONS)
def test_extra_queen_is_good_for_white(evaluate):
    no_black_queen = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert evaluate(no_black_queen) > 0


@pytest.mark.parametrize("evaluate", EVALUATIONS)
def test_tables_are_not_upside_down(evaluate):
    # Tables copied rank-8-first and used without flipping would prefer e2 to e7.
    # The knight and symmetry tests cannot catch this (plan, Section 9.5).
    pawn_e7 = chess.Board("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
    pawn_e2 = chess.Board("k7/8/8/8/8/8/4P3/4K3 w - - 0 1")
    assert evaluate(pawn_e7) >= evaluate(pawn_e2)
