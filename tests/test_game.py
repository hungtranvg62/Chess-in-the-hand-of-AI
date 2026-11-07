"""Tests for game/game.py: legal moves only, game over, undo, records."""
import random

import chess
import pytest

from game.game import EnginePlayer, Game, IllegalMoveError, make_board, play_game
from game.interface import new_stats

FOOLS_MATE = ["f3", "e5", "g4", "Qh4#"]
REPEAT = ["Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8"]


# --- fake engines (real ones are tested in test_engine_contract.py) ---

def random_search(board, time_limit=None, depth=None, node_limit=None, rng=random.Random(1)):
    moves = list(board.legal_moves)
    return (rng.choice(moves) if moves else None), new_stats()


def scripted(sans):
    """An engine that plays a fixed list of moves (SAN), for exact games."""
    moves = iter(sans)

    def search(board, time_limit=None, depth=None, node_limit=None):
        return board.parse_san(next(moves)), new_stats()
    return search


# --- starting positions ---

def test_start_from_opening_line_fen_or_board():
    assert make_board("e4 e5").fen() == make_board(["e4", "e5"]).fen()
    fen = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
    assert make_board(fen).fen() == fen
    original = chess.Board()
    copy = make_board(original)
    copy.push_san("e4")
    assert original.fen() == chess.STARTING_FEN       # the caller's board is copied


# --- moves ---

def test_play_accepts_move_uci_and_san():
    game = Game()
    game.play(chess.Move.from_uci("e2e4"))
    game.play("e7e5")
    game.play("Nf3")
    assert game.move_list() == ["e4", "e5", "Nf3"]


@pytest.mark.parametrize("bad", ["e2e5", "Ke2", "xyz", chess.Move.from_uci("e1e2")])
def test_illegal_move_is_refused_and_board_unchanged(bad):
    game = Game()
    with pytest.raises(IllegalMoveError):
        game.play(bad)
    assert game.board.fen() == chess.STARTING_FEN


def test_legal_moves_of_one_piece_for_ui_hints():
    moves = Game().legal_moves(chess.G1)
    assert sorted(m.uci() for m in moves) == ["g1f3", "g1h3"]


def test_no_moves_after_the_game_is_over():
    game = Game(FOOLS_MATE)
    with pytest.raises(IllegalMoveError):
        game.play("a3")


# --- undo ---

def test_undo_takes_back_moves_but_not_the_opening_line():
    game = Game("e4 e5")
    game.play("Nf3")
    game.play("Nc6")
    assert game.undo(2) == 2
    assert game.undo() == 0                           # cannot undo the opening line
    assert game.move_list() == ["e4", "e5"]


# --- game over ---

def test_checkmate():
    game = Game()
    for san in FOOLS_MATE:
        game.play(san)
    assert game.is_over()
    assert (game.result(), game.reason()) == ("0-1", "checkmate")


def test_threefold_repetition_ends_the_game():
    game = Game()
    for san in REPEAT:
        game.play(san)
    assert game.is_over()
    assert (game.result(), game.reason()) == ("1/2-1/2", "threefold_repetition")


def test_possible_repetition_does_not_end_the_game_early():
    game = Game()
    for san in REPEAT[:-1]:                           # Black *could* repeat with Ng8...
        game.play(san)
    assert not game.is_over()                         # ...but has not done it yet


def test_fifty_move_rule_ends_the_game():
    game = Game("8/8/4k3/8/8/4K3/8/R7 w - - 99 80")
    game.play("Ra2")
    assert (game.result(), game.reason()) == ("1/2-1/2", "fifty_moves")


def test_game_in_progress():
    game = Game("e4")
    assert not game.is_over()
    assert (game.result(), game.reason()) == ("*", None)


def test_pgn_has_players_moves_and_result():
    game = Game()
    for san in FOOLS_MATE:
        game.play(san)
    pgn = game.to_pgn(white="Easy", black="Master")
    assert '[White "Easy"]' in pgn and '[Result "0-1"]' in pgn
    assert "1. f3 e5 2. g4 Qh4#" in pgn


# --- players and full games ---

def test_engine_player_gets_a_copy_and_keeps_stats():
    def careless_search(board, **limits):
        board.push(next(iter(board.legal_moves)))     # changes its board...
        stats = new_stats()
        stats["nodes"] = 7
        return board.pop(), stats

    player = EnginePlayer(careless_search, name="careless", depth=1)
    board = chess.Board()
    player.choose_move(board)
    assert board.fen() == chess.STARTING_FEN          # ...but not the real one
    assert player.last_stats["nodes"] == 7


def test_play_game_scripted_checkmate():
    white = EnginePlayer(scripted(["f3", "g4"]), name="white")
    black = EnginePlayer(scripted(["e5", "Qh4#"]), name="black")
    record = play_game(white, black)
    assert (record.result, record.reason) == ("0-1", "checkmate")
    assert record.moves == FOOLS_MATE
    assert len(record.stats) == 4
    assert '[Result "0-1"]' in record.pgn


def test_play_game_random_engines_finish():
    white = EnginePlayer(random_search, name="random")
    black = EnginePlayer(random_search, name="random")
    record = play_game(white, black, start="e4 e5", max_plies=60)
    assert record.result in {"1-0", "0-1", "1/2-1/2"}
    assert len(record.stats) <= 60
    assert record.moves[:2] == ["e4", "e5"]


def test_play_game_stops_at_max_plies_as_a_draw():
    white = EnginePlayer(scripted(REPEAT[0::2]), name="w")
    black = EnginePlayer(scripted(REPEAT[1::2]), name="b")
    record = play_game(white, black, max_plies=3)
    assert (record.result, record.reason) == ("1/2-1/2", "max_plies")
    assert len(record.moves) == 3


def test_adjudication_stops_the_game():
    white = EnginePlayer(random_search, name="w")
    black = EnginePlayer(random_search, name="b")
    record = play_game(white, black, adjudicate=lambda board: "1-0" if board.ply() >= 2 else None)
    assert (record.result, record.reason) == ("1-0", "adjudicated")
    assert '[Result "1-0"]' in record.pgn


def test_illegal_engine_move_is_caught():
    def cheating_search(board, **limits):
        return chess.Move.from_uci("e2e5"), new_stats()

    with pytest.raises(IllegalMoveError):
        play_game(EnginePlayer(cheating_search), EnginePlayer(random_search))
