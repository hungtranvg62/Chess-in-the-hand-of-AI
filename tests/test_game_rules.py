"""Chess rules from python-chess: checks our setup before any engine exists.

When game/game.py is written, add tests for its game loop here.
"""
import chess
import pytest

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def perft(board, depth):
    """Count all positions reachable in `depth` half-moves."""
    if depth == 0:
        return 1
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += perft(board, depth - 1)
        board.pop()
    return total


def play(*sans):
    board = chess.Board()
    for san in sans:
        board.push_san(san)
    return board


# Published perft numbers (Chess Programming Wiki, "Perft Results").
@pytest.mark.parametrize("depth, expected", [(1, 20), (2, 400), (3, 8902)])
def test_perft_start_position(depth, expected):
    assert perft(chess.Board(), depth) == expected


@pytest.mark.parametrize("depth, expected", [(1, 48), (2, 2039)])
def test_perft_kiwipete(depth, expected):
    assert perft(chess.Board(KIWIPETE), depth) == expected


def test_checkmate_ends_the_game():
    board = play("f3", "e5", "g4", "Qh4#")
    assert board.is_checkmate()
    assert board.result() == "0-1"


def test_stalemate_is_a_draw():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()
    assert board.result() == "1/2-1/2"


def test_threefold_repetition_is_a_draw_only_when_claimed():
    board = play("Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8")
    assert not board.is_game_over()                  # fivefold only, by default
    assert board.is_game_over(claim_draw=True)       # what the game loop must use
    assert board.result(claim_draw=True) == "1/2-1/2"


def test_insufficient_material_is_a_draw():
    board = chess.Board("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
    assert board.is_insufficient_material()
    assert board.is_game_over()


def test_illegal_move_is_rejected():
    with pytest.raises(ValueError):
        chess.Board().push_san("e5")                 # a white pawn cannot jump 3 squares
