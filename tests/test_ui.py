"""Tests for the UI helpers (owner: Joseph). No window and no sound is opened here."""
import random

import chess
import pygame
import pytest

from game.interface import MATE
from ui.app import (THEMES, captured_pieces, end_text, eval_fraction, find_engines,
                    material_balance, score_text)
from ui.effects import Burst, Confetti, Slide
from ui.sounds import SOUND_NAMES, TONES, make_tone, sound_for
from game.game import Game


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


# --- sounds: one sound per move, the most important one ---

def _sound(fen_or_moves, move):
    board = Game(fen_or_moves).board
    return sound_for(board, board.parse_san(move))


def test_normal_move_sound():
    assert _sound(None, "e4") == "move"


def test_capture_sound():
    assert _sound("e4 d5", "exd5") == "capture"


def test_castle_sound():
    assert _sound("e4 e5 Nf3 Nc6 Bc4 Bc5", "O-O") == "castle"


def test_promotion_sound():
    # Black keeps a pawn: king + knight vs bare king would be a draw (insufficient material).
    assert _sound("8/P7/8/7p/4k3/8/8/7K w - - 0 1", "a8=N") == "promote"


def test_check_beats_capture():
    assert _sound("e4 f5 exf5 g6", "fxg6") == "capture"          # not a check
    assert _sound("e4 f5 Qh5+ g6", "Qxg6+") == "check"           # capture that gives check


def test_checkmate_sound():
    assert _sound("f3 e5 g4", "Qh4#") == "checkmate"


def test_stalemate_plays_the_draw_sound():
    assert _sound("7k/8/6Q1/8/8/8/8/K7 w - - 0 1", "Qf7") == "draw"


def test_sound_for_does_not_change_the_board():
    board = chess.Board()
    sound_for(board, chess.Move.from_uci("e2e4"))
    assert board.fen() == chess.STARTING_FEN and not board.move_stack


def test_every_sound_has_a_tone_and_the_right_length():
    assert set(SOUND_NAMES) == {"move", "capture", "castle", "promote", "check",
                                "checkmate", "draw", "illegal", "start"}
    data = make_tone([(440, 100)], rate=8000, channels=2)
    assert len(data) == 800 * 2 * 2                               # samples x channels x 2 bytes
    assert all(TONES[name] for name in SOUND_NAMES)


# --- evaluation bar and score text ---

def test_eval_fraction():
    assert eval_fraction(None) == 0.5
    assert eval_fraction(0) == 0.5
    assert 0.5 < eval_fraction(100) < eval_fraction(500) < 1
    assert eval_fraction(-300) == pytest.approx(1 - eval_fraction(300))
    assert eval_fraction(MATE - 5) == 1.0
    assert eval_fraction(-(MATE - 5)) == 0.0


def test_score_text():
    assert score_text(None) == "–"
    assert score_text(150) == "+1.5"
    assert score_text(-200) == "-2.0"
    assert score_text(MATE - 3) == "+M2"                          # mate in 3 plies = 2 moves
    assert score_text(-(MATE - 2)) == "-M1"


# --- captured pieces and material ---

def test_captured_pieces_after_a_pawn_trade():
    board = Game("e4 d5 exd5").board
    assert captured_pieces(board) == {chess.WHITE: [chess.PAWN], chess.BLACK: []}
    assert material_balance(board) == 1


def test_promotion_is_not_counted_as_a_captured_pawn():
    # White has 7 pawns and 2 queens (one pawn promoted), and has lost a rook.
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/1PPPPPPP/RNBQKBNQ w - - 0 1")
    assert captured_pieces(board)[chess.BLACK] == [chess.ROOK]
    assert captured_pieces(board)[chess.WHITE] == []


def test_end_text():
    assert end_text(Game("f3 e5 g4 Qh4")) == ("Checkmate!", "Black wins")
    stalemate = Game("7k/5Q2/8/8/8/8/8/K7 b - - 0 1")
    assert end_text(stalemate) == ("Draw", "Stalemate")


# --- effects (fake clock, no window) ---

def test_slide_reaches_the_end():
    clock = FakeClock()
    slide = Slide(None, (0, 0), (80, 160), chess.E4, duration=0.15, clock=clock)
    assert slide.position() == (0, 0) and not slide.done
    clock.now = 0.075
    x, y = slide.position()
    assert 40 < x < 80 and 80 < y < 160                           # ease-out: past half-way
    clock.now = 0.2
    assert slide.position() == (80, 160) and slide.done


def test_burst_and_confetti_finish():
    clock = FakeClock()
    burst = Burst((100, 100), (255, 0, 0), rng=random.Random(1), clock=clock)
    confetti = Confetti(pygame.Rect(0, 0, 640, 640), rng=random.Random(1), clock=clock)
    assert not burst.done and not confetti.done
    clock.now = 20.0
    assert burst.done and confetti.done


def test_effects_draw_on_a_surface():
    clock = FakeClock()
    screen = pygame.Surface((200, 200))
    Burst((100, 100), (255, 0, 0), rng=random.Random(1), clock=clock).draw(screen)
    confetti = Confetti(pygame.Rect(0, 0, 200, 200), rng=random.Random(1), clock=clock)
    clock.now = 1.0
    confetti.draw(screen)                                         # must not raise


# --- app wiring ---

def test_themes_have_all_colours():
    assert len(THEMES) >= 3
    for theme in THEMES:
        assert all(len(c) == 3 for c in (theme.light, theme.dark, theme.highlight, theme.hint))


def test_engine_menu_lists_every_level_with_search():
    engines = find_engines()
    assert "random_player" in engines and "alphabeta" in engines
    assert all(callable(search) for search in engines.values())
