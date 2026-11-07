"""Tests for Level 3: move ordering and alpha-beta (owner: Dominique).

The key check (plan, Experiment 1): alpha-beta gives exactly the same score as plain
minimax at the same depth, while searching fewer positions.
"""
import chess
import pytest

from engine import alphabeta
from engine.ordering import order_moves
from game.interface import INF, MATE, is_terminal

POSITIONS = {
    "start": chess.STARTING_FEN,
    "middlegame": "r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6",
    "tactics": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/5pk1/4p1p1/3pP3/1b1P1P2/4BK2/6PP/8 w - - 0 40",
    "black to move": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
}


def plain_minimax(board, depth, ply=0):
    """Reference negamax without pruning, same evaluation as alpha-beta."""
    if is_terminal(board, ply):
        return -(MATE - ply) if board.is_checkmate() else 0
    if depth == 0:
        score = alphabeta.evaluate(board)
        return score if board.turn == chess.WHITE else -score
    best = -INF
    for move in board.legal_moves:
        board.push(move)
        best = max(best, -plain_minimax(board, depth - 1, ply + 1))
        board.pop()
    return best


# --- move ordering ---------------------------------------------------------------

def test_ordering_keeps_every_legal_move():
    board = chess.Board(POSITIONS["tactics"])
    assert sorted(order_moves(board), key=str) == sorted(board.legal_moves, key=str)


def test_pawn_takes_queen_comes_before_queen_takes_pawn():
    board = chess.Board("4k3/8/8/3q4/4P3/p7/8/Q3K3 w - - 0 1")
    moves = order_moves(board)
    pxq = chess.Move.from_uci("e4d5")
    qxp = chess.Move.from_uci("a1a3")
    assert moves[0] == pxq
    assert moves.index(pxq) < moves.index(qxp)


def test_first_move_is_searched_first():
    board = chess.Board()
    quiet = chess.Move.from_uci("a2a3")
    assert order_moves(board, first_move=quiet)[0] == quiet


# --- alpha-beta ------------------------------------------------------------------

@pytest.mark.parametrize("depth", [1, 2, 3])
@pytest.mark.parametrize("fen", POSITIONS.values(), ids=list(POSITIONS))
def test_alphabeta_score_equals_minimax(fen, depth):
    if depth == 3 and fen == POSITIONS["tactics"]:
        pytest.skip("too slow for plain minimax in CI")
    board = chess.Board(fen)
    _, score, _ = alphabeta.search_fixed_depth(board, depth)
    expected = plain_minimax(board.copy(), depth)
    white_expected = expected if board.turn == chess.WHITE else -expected
    assert score == white_expected


def test_ordering_searches_fewer_nodes_with_same_score():
    board = chess.Board(POSITIONS["middlegame"])
    _, score_ordered, ordered = alphabeta.search_fixed_depth(board, 3, ordering=True)
    _, score_plain, plain = alphabeta.search_fixed_depth(board, 3, ordering=False)
    assert score_ordered == score_plain
    assert ordered["nodes"] < plain["nodes"]


def test_finds_mate_in_one():
    board = chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")     # Ra8#
    move, stats = alphabeta.search(board, depth=3)
    assert move == chess.Move.from_uci("a1a8")
    assert stats["score"] >= MATE - 10


def test_node_limit_is_respected():
    board = chess.Board(POSITIONS["middlegame"])
    move, stats = alphabeta.search(board, node_limit=2000)
    assert move in board.legal_moves
    assert stats["nodes"] <= 2000
    assert stats["depth"] >= 1
