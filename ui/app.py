"""App entry point: board, level menu, move list (owner: Joseph; first prototype: Hưng).

A Pygame window to play against any engine, or to watch two engines play.
Run it from the repo root:  python -m ui.app

- Click a piece, then click a dot; or drag the piece. A pawn that reaches the last
  rank opens a small menu: queen, rook, bishop or knight.
- Each side can be "Human" or any engine in engine/ that has a search() function;
  new levels appear in the menu by themselves.
- Engines think in a background thread on a copy of the board, so the window never freezes.
- Extras from the plan (Section 10.1-10.2): sounds (ui/sounds.py), move animation,
  capture particles and checkmate confetti (ui/effects.py), evaluation bar, captured
  pieces, board themes, end-of-game screen.
- Own piece images: put 12 PNG files in ui/assets/pieces/ named wK, wQ, wR, wB, wN, wP,
  bK, ... (e.g. wK.png). If any is missing, Unicode chess symbols are drawn instead.
"""
from __future__ import annotations

import importlib
import math
import pkgutil
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):                      # allow "python ui/app.py" as well
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chess
import pygame

import engine
from game.game import EnginePlayer, Game, IllegalMoveError
from game.interface import MATE
from ui.effects import Burst, Confetti, Slide
from ui.sounds import SoundPlayer, sound_for

# --- layout ---
SQ = 80                                            # one square, in pixels
EVAL_X, EVAL_W = 16, 18                            # evaluation bar, left of the board
BOARD_X, BOARD_Y = 56, 40
PANEL_X = BOARD_X + 8 * SQ + 36
WIDTH, HEIGHT = PANEL_X + 340, BOARD_Y * 2 + 8 * SQ
MINI = 26                                          # captured-piece icons

# --- colours ---
BACKGROUND, INK, MUTED = (246, 243, 236), (27, 34, 48), (95, 102, 114)
ERROR = (180, 40, 40)
WHITE_PIECE = (251, 251, 248)


@dataclass(frozen=True)
class Theme:
    name: str
    light: tuple
    dark: tuple
    highlight: tuple                               # last move, selected square, particles
    hint: tuple                                    # legal-move dots and rings


THEMES = [
    Theme("Wood", (239, 231, 215), (176, 122, 62), (227, 154, 69), INK),
    Theme("Forest", (235, 236, 208), (119, 149, 86), (246, 246, 105), INK),
    Theme("Ocean", (222, 234, 242), (90, 132, 170), (120, 200, 235), INK),
    Theme("Neon", (72, 76, 110), (40, 42, 64), (255, 0, 170), (0, 255, 200)),
]

GLYPHS = {chess.KING: "♚", chess.QUEEN: "♛", chess.ROOK: "♜",
          chess.BISHOP: "♝", chess.KNIGHT: "♞", chess.PAWN: "♟"}
PIECE_DIR = Path(__file__).resolve().parent / "assets" / "pieces"
PROMOTION_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
TIME_CHOICES = [1.0, 2.0, 5.0]
HUMAN = "Human"

# --- small helpers (no window needed, tested in tests/test_ui.py) ---

MATE_BOUND = MATE - 1000                           # scores beyond this are mate scores
VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
START_COUNT = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}


def eval_fraction(score: int | None) -> float:
    """Share of the evaluation bar that is White's (0 to 1). Plan: 0.5 + 0.5 * tanh(score / 400)."""
    if score is None:
        return 0.5
    if abs(score) >= MATE_BOUND:
        return 1.0 if score > 0 else 0.0
    return 0.5 + 0.5 * math.tanh(score / 400)


def score_text(score: int | None) -> str:
    """'+0.4' in pawns, or '+M3' for White mates in 3 / '-M2' for Black mates in 2."""
    if score is None:
        return "–"
    if abs(score) >= MATE_BOUND:
        moves = (MATE - abs(score) + 1) // 2
        return f"{'+' if score > 0 else '-'}M{moves}"
    return f"{score / 100:+.1f}"


def _missing(board: chess.Board, color: chess.Color) -> list[int]:
    """Pieces of `color` no longer on the board, cheapest first (promotions handled)."""
    counts = {pt: len(board.pieces(pt, color)) for pt in START_COUNT}
    promoted = sum(max(0, counts[pt] - START_COUNT[pt]) for pt in START_COUNT if pt != chess.PAWN)
    missing = []
    for pt, start in START_COUNT.items():
        gone = start - counts[pt] - (promoted if pt == chess.PAWN else 0)
        missing += [pt] * max(0, gone)
    return missing


def captured_pieces(board: chess.Board) -> dict:
    """{WHITE: piece types White has taken, BLACK: piece types Black has taken}."""
    return {chess.WHITE: _missing(board, chess.BLACK), chess.BLACK: _missing(board, chess.WHITE)}


def material_balance(board: chess.Board) -> int:
    """White's material minus Black's, in pawns (1, 3, 3, 5, 9)."""
    return sum(value * (len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK)))
               for pt, value in VALUES.items())


def end_text(game: Game) -> tuple[str, str]:
    """Title and subtitle of the end-of-game screen."""
    result = game.result()
    if game.board.is_checkmate():
        return "Checkmate!", "White wins" if result == "1-0" else "Black wins"
    reason = (game.reason() or "draw").replace("_", " ")
    return "Draw", reason[0].upper() + reason[1:]


def find_engines() -> dict:
    """Every module in engine/ with a search() function, by name (same rule as the tests)."""
    engines = {}
    for info in pkgutil.iter_modules(engine.__path__):
        if info.ispkg:
            continue
        module = importlib.import_module(f"engine.{info.name}")
        if callable(getattr(module, "search", None)):
            engines[info.name] = module.search
    return engines


class Button:
    def __init__(self, x, y, w, h, on_click):
        self.rect = pygame.Rect(x, y, w, h)
        self.on_click = on_click


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)  # small buffer: sounds play without delay
        pygame.init()
        pygame.display.set_caption("Chess in the Hand of AI")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("segoeui,arial", 20)
        self.small = pygame.font.SysFont("segoeui,arial", 16)
        self.title = pygame.font.SysFont("segoeui,arial", 24, bold=True)
        self.big = pygame.font.SysFont("segoeui,arial", 46, bold=True)
        self.pieces = self._piece_images()
        self.mini = {key: pygame.transform.smoothscale(image, (MINI, MINI))
                     for key, image in self.pieces.items()}
        self.sounds = SoundPlayer()

        self.engines = find_engines()
        self.choices = [HUMAN] + sorted(self.engines)
        self.side = {chess.WHITE: HUMAN,
                     chess.BLACK: self.choices[1] if len(self.choices) > 1 else HUMAN}
        self.time_limit = TIME_CHOICES[0]
        self.flipped = False
        self.theme_index = 0

        x = PANEL_X + 120
        self.buttons = [
            Button(x, 90, 190, 34, lambda: self._next_player(chess.WHITE)),
            Button(x, 132, 190, 34, lambda: self._next_player(chess.BLACK)),
            Button(x, 174, 190, 34, self._next_time),
            Button(PANEL_X, 222, 100, 36, self.new_game),
            Button(PANEL_X + 110, 222, 100, 36, self.undo),
            Button(PANEL_X + 220, 222, 90, 36, self.flip),
            Button(PANEL_X, 266, 150, 36, self._next_theme),
            Button(PANEL_X + 160, 266, 150, 36, self.sounds.toggle),
        ]
        self.new_game()

    @property
    def theme(self) -> Theme:
        return THEMES[self.theme_index]

    # --- game control ---

    def new_game(self):
        self.game = Game()
        self._reset_turn()
        self._clear_effects()
        self.last_engine = None
        self.eval_score = None
        self.eval_shown = 0.5
        self.sounds.play("start")

    def _reset_turn(self):
        """Forget any engine that is still thinking (its answer will be ignored)."""
        self.token = getattr(self, "token", 0) + 1
        self.thinking = False
        self.think_start = 0.0
        self.result = None
        self.error = None
        self.selected = None
        self.dragging = False
        self.drag_pos = (0, 0)
        self.promotion = None                      # {"moves": [...], "animate": bool}

    def _clear_effects(self):
        self.slide = None
        self.bursts = []
        self.confetti = None
        self.show_end = True

    def undo(self):
        humans = [c for c in (chess.WHITE, chess.BLACK) if self.side[c] == HUMAN]
        # Against an engine, take back the engine's reply too, so it is your turn again.
        steps = 2 if len(humans) == 1 and self.game.board.turn in humans else 1
        self.game.undo(steps)
        self._reset_turn()
        self._clear_effects()
        self.eval_score = None                     # the old score was for another position

    def flip(self):
        self.flipped = not self.flipped
        self.slide = None                          # its pixel positions are for the old side

    def _next_player(self, color):
        i = self.choices.index(self.side[color])
        self.side[color] = self.choices[(i + 1) % len(self.choices)]
        self._reset_turn()

    def _next_time(self):
        i = TIME_CHOICES.index(self.time_limit)
        self.time_limit = TIME_CHOICES[(i + 1) % len(TIME_CHOICES)]

    def _next_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)

    def _play(self, move: chess.Move, animate: bool = True):
        """Play a legal move with its sound and effects (human and engine moves alike)."""
        board = self.game.board
        sound = sound_for(board, move)
        piece = board.piece_at(move.from_square)
        taken_square = move.to_square
        if board.is_en_passant(move):
            taken_square = chess.square(chess.square_file(move.to_square),
                                        chess.square_rank(move.from_square))
        victim = board.piece_at(taken_square) if board.is_capture(move) else None

        self.game.play(move)                       # raises IllegalMoveError if illegal
        self.selected = None
        self.slide = None
        if animate:
            image = self.pieces[(piece.color, move.promotion or piece.piece_type)]
            self.slide = Slide(image, self.square_rect(move.from_square).topleft,
                               self.square_rect(move.to_square).topleft, move.to_square)
        if victim is not None:
            self.bursts.append(Burst(self.square_rect(taken_square).center, self.theme.highlight))
        if self.game.is_over():
            self.show_end = True
            if self.game.board.is_checkmate():
                self.confetti = Confetti(self.board_rect())
        self.sounds.play(sound)

    # --- input ---

    def handle_click(self, pos):
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                button.on_click()
                return
        if self._end_screen_visible():
            if self.board_rect().collidepoint(pos):
                self.show_end = False              # click to look at the final position
            return
        if self.promotion:
            self._choose_promotion(pos)
            return
        square = self.square_at(pos)
        if square is None or self.game.is_over() or self.side[self.game.board.turn] != HUMAN:
            return
        if self.selected is not None and square != self.selected and self._moves_to(square):
            self._human_move(square, animate=True)
            return
        piece = self.game.board.piece_at(square)
        if piece and piece.color == self.game.board.turn and self.game.legal_moves(square):
            self.selected = square                 # select it, and start a drag
            self.dragging = True
            self.drag_pos = pos
        else:
            if self.selected is not None:
                self.sounds.play("illegal")
            self.selected = None                   # an illegal click just deselects

    def handle_release(self, pos):
        if not self.dragging:
            return
        self.dragging = False
        square = self.square_at(pos)
        if square is None or square == self.selected:
            return                                 # dropped back: keep it selected
        if self._moves_to(square):
            self._human_move(square, animate=False)   # the piece is already there
        else:
            self.sounds.play("illegal")

    def _moves_to(self, square):
        return [m for m in self.game.legal_moves(self.selected) if m.to_square == square]

    def _human_move(self, square, animate):
        moves = self._moves_to(square)
        if len(moves) > 1:                         # a promotion: let the player choose
            moves.sort(key=lambda m: PROMOTION_ORDER.index(m.promotion))
            self.promotion = {"moves": moves, "animate": animate}
            return
        self._play(moves[0], animate)

    def _promotion_rects(self):
        moves = self.promotion["moves"]
        target = self.square_rect(moves[0].to_square)
        step = SQ if target.centery < BOARD_Y + 4 * SQ else -SQ    # grow towards the centre
        return [(move, target.move(0, i * step)) for i, move in enumerate(moves)]

    def _choose_promotion(self, pos):
        for move, rect in self._promotion_rects():
            if rect.collidepoint(pos):
                animate = self.promotion["animate"]
                self.promotion = None
                self._play(move, animate)
                return
        self.promotion = None                      # clicked elsewhere: cancel
        self.selected = None

    def square_at(self, pos):
        x, y = pos[0] - BOARD_X, pos[1] - BOARD_Y
        if not (0 <= x < 8 * SQ and 0 <= y < 8 * SQ):
            return None
        file, row = x // SQ, y // SQ
        return chess.square(7 - file, row) if self.flipped else chess.square(file, 7 - row)

    def square_rect(self, square):
        file, rank = chess.square_file(square), chess.square_rank(square)
        if self.flipped:
            file, rank = 7 - file, 7 - rank
        return pygame.Rect(BOARD_X + file * SQ, BOARD_Y + (7 - rank) * SQ, SQ, SQ)

    def board_rect(self):
        return pygame.Rect(BOARD_X, BOARD_Y, 8 * SQ, 8 * SQ)

    # --- engine turn (background thread) ---

    def update(self):
        if self.result is not None:
            token, move, stats, error = self.result
            self.result = None
            if token == self.token:
                self._apply_engine_move(move, stats, error)
        if self.slide and self.slide.done:
            self.slide = None
        self.bursts = [b for b in self.bursts if not b.done]
        if self.confetti and self.confetti.done:
            self.confetti = None
        target = eval_fraction(self.eval_score)
        self.eval_shown += (target - self.eval_shown) * 0.15     # the bar moves smoothly

        name = self.side[self.game.board.turn]
        if name != HUMAN and not self.thinking and not self.error and not self.game.is_over():
            self._start_engine(name)

    def _start_engine(self, name):
        player = EnginePlayer(self.engines[name], name=name, time_limit=self.time_limit)
        board, token = self.game.board.copy(), self.token
        self.thinking = True
        self.think_start = time.perf_counter()

        def work():
            try:
                move = player.choose_move(board)
                self.result = (token, move, player.last_stats, None)
            except Exception as error:                   # show engine bugs instead of crashing
                self.result = (token, None, None, f"{type(error).__name__}: {error}")

        threading.Thread(target=work, daemon=True).start()

    def _apply_engine_move(self, move, stats, error):
        self.thinking = False
        name = self.side[self.game.board.turn]
        if error:
            self.error = f"{name} crashed: {error}"
            return
        if move is None or move not in self.game.board.legal_moves:
            self.error = f"{name} returned an illegal move: {move}"
            return
        san = self.game.board.san(move)
        try:
            self._play(move, animate=True)
        except IllegalMoveError as illegal:
            self.error = str(illegal)
            return
        self.last_engine = (name, san, stats or {})
        if stats and "score" in stats:
            self.eval_score = stats["score"]       # centipawns, from White's point of view

    # --- drawing ---

    def _piece_images(self):
        files = {(color, kind): PIECE_DIR / f"{'w' if color else 'b'}{chess.piece_symbol(kind).upper()}.png"
                 for color in (chess.WHITE, chess.BLACK) for kind in GLYPHS}
        if all(path.exists() for path in files.values()):
            try:
                return {key: pygame.transform.smoothscale(pygame.image.load(str(path)).convert_alpha(),
                                                          (SQ, SQ))
                        for key, path in files.items()}
            except pygame.error:
                pass                               # a broken file: use the symbols
        path = pygame.font.match_font("segoeuisymbol,dejavusans,freeserif,notosanssymbols2")
        font = pygame.font.Font(path, 64) if path else None
        images = {}
        for color in (chess.WHITE, chess.BLACK):
            for kind, glyph in GLYPHS.items():
                text = glyph if font else chess.piece_symbol(kind).upper()
                use = font or pygame.font.SysFont("arial", 48, bold=True)
                fill, edge = (WHITE_PIECE, INK) if color == chess.WHITE else (INK, WHITE_PIECE)
                image = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                    outline = use.render(text, True, edge)
                    image.blit(outline, outline.get_rect(center=(SQ // 2 + dx, SQ // 2 + dy)))
                face = use.render(text, True, fill)
                image.blit(face, face.get_rect(center=(SQ // 2, SQ // 2)))
                images[(color, kind)] = image
        return images

    def draw(self):
        self.screen.fill(BACKGROUND)
        self._draw_eval_bar()
        self._draw_board()
        self._draw_panel()
        pygame.display.flip()

    def _overlay(self, rect, color, alpha):
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        layer.fill((*color, alpha))
        self.screen.blit(layer, rect)

    def _check_glow(self, square):
        """Red radial glow under the king in check."""
        glow = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        for r in range(SQ // 2, 0, -3):            # inner circles are drawn last, stronger
            alpha = int(30 + 170 * (1 - r / (SQ / 2)))
            pygame.draw.circle(glow, (*ERROR, alpha), (SQ // 2, SQ // 2), r)
        self.screen.blit(glow, self.square_rect(square))

    def _draw_board(self):
        board, theme = self.game.board, self.theme
        for square in chess.SQUARES:
            light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
            pygame.draw.rect(self.screen, theme.light if light else theme.dark,
                             self.square_rect(square))
        if board.move_stack:
            last = board.move_stack[-1]
            for square in (last.from_square, last.to_square):
                self._overlay(self.square_rect(square), theme.highlight, 110)
        if self.selected is not None:
            self._overlay(self.square_rect(self.selected), theme.highlight, 170)
        if board.is_check():
            self._check_glow(board.king(board.turn))

        hidden = {self.slide.square} if self.slide else set()
        if self.dragging and self.selected is not None:
            hidden.add(self.selected)              # drawn under the mouse instead
        for square, piece in board.piece_map().items():
            if square not in hidden:
                self.screen.blit(self.pieces[(piece.color, piece.piece_type)], self.square_rect(square))

        if self.selected is not None and not self.promotion:
            for move in self.game.legal_moves(self.selected):
                center = self.square_rect(move.to_square).center
                if board.piece_at(move.to_square) or board.is_en_passant(move):
                    pygame.draw.circle(self.screen, theme.hint, center, SQ // 2 - 4, 4)   # capture: ring
                else:
                    pygame.draw.circle(self.screen, theme.hint, center, 10)               # move: dot
        for i in range(8):                                                                # a-h and 1-8
            file_label = "abcdefgh"[7 - i if self.flipped else i]
            rank_label = str(i + 1 if self.flipped else 8 - i)
            self._text(file_label, BOARD_X + i * SQ + SQ - 12, BOARD_Y + 8 * SQ + 4, self.small, MUTED)
            self._text(rank_label, BOARD_X - 14, BOARD_Y + i * SQ + 4, self.small, MUTED)

        if self.slide:
            self.slide.draw(self.screen)
        for burst in self.bursts:
            burst.draw(self.screen)
        if self.dragging and self.selected is not None:
            piece = board.piece_at(self.selected)
            image = self.pieces[(piece.color, piece.piece_type)]
            self.screen.blit(image, image.get_rect(center=self.drag_pos))
        if self.promotion:
            self._draw_promotion()
        if self._end_screen_visible():
            self._draw_end_screen()
        if self.confetti:
            self.confetti.draw(self.screen)

    def _draw_promotion(self):
        self._overlay(self.board_rect(), INK, 90)
        color = self.game.board.turn
        for move, rect in self._promotion_rects():
            pygame.draw.rect(self.screen, (255, 253, 248), rect, border_radius=10)
            pygame.draw.rect(self.screen, self.theme.highlight, rect, 3, border_radius=10)
            self.screen.blit(self.pieces[(color, move.promotion)], rect)

    def _end_screen_visible(self):
        return self.game.is_over() and self.show_end and not self.slide

    def _draw_end_screen(self):
        board_rect = self.board_rect()
        self._overlay(board_rect, (0, 0, 0), 140)
        title, subtitle = end_text(self.game)
        box = pygame.Rect(0, 0, 420, 150)
        box.center = board_rect.center
        pygame.draw.rect(self.screen, (255, 253, 248), box, border_radius=16)
        pygame.draw.rect(self.screen, self.theme.highlight, box, 4, border_radius=16)
        for text, font, color, dy in ((title, self.big, INK, -32), (subtitle, self.font, INK, 18),
                                      ("click the board to see the position", self.small, MUTED, 48)):
            image = font.render(text, True, color)
            self.screen.blit(image, image.get_rect(center=(box.centerx, box.centery + dy)))

    def _draw_eval_bar(self):
        rect = pygame.Rect(EVAL_X, BOARD_Y, EVAL_W, 8 * SQ)
        pygame.draw.rect(self.screen, INK, rect)
        white = round(rect.height * self.eval_shown)
        part = (pygame.Rect(rect.x, rect.bottom - white, rect.width, white) if not self.flipped
                else pygame.Rect(rect.x, rect.y, rect.width, white))
        pygame.draw.rect(self.screen, WHITE_PIECE, part)
        pygame.draw.rect(self.screen, MUTED, rect, 1)
        label = self.small.render(score_text(self.eval_score), True, MUTED)
        self.screen.blit(label, label.get_rect(midtop=(rect.centerx + 4, rect.bottom + 4)))

    def _text(self, text, x, y, font=None, color=INK):
        self.screen.blit((font or self.font).render(text, True, color), (x, y))

    def _draw_panel(self):
        self._text("Chess in the Hand of AI", PANEL_X, 40, self.title)
        labels = ["White", "Black", "AI time"]
        values = [self.side[chess.WHITE], self.side[chess.BLACK], f"{self.time_limit:g} s"]
        for button, label, value in zip(self.buttons[:3], labels, values):
            self._text(label, PANEL_X, button.rect.y + 6)
            self._button(button, value)
        sound = ("Sound: on" if self.sounds.enabled else "Sound: off") if self.sounds.available \
            else "No audio"
        for button, label in zip(self.buttons[3:], ["New game", "Undo", "Flip",
                                                    f"Theme: {self.theme.name}", sound]):
            self._button(button, label)

        status, color = self._status()
        self._text(status, PANEL_X, 316, self.font, color)

        y = 348
        if self.last_engine:
            name, san, stats = self.last_engine
            nodes = stats.get("nodes", 0) + stats.get("qnodes", 0)
            lines = [f"{name} played {san}",
                     f"depth {stats.get('depth', 0)} · {nodes:,} positions",
                     f"{stats.get('time', 0.0):.2f} s · score {score_text(stats.get('score', 0))}"]
            for line in lines:
                self._text(line, PANEL_X, y, self.small, MUTED)
                y += 22

        self._draw_captured(424)

        self._text("Moves", PANEL_X, 500, self.font)
        sans = self.game.move_list()
        rows = [f"{i // 2 + 1}. " + " ".join(sans[i:i + 2]) for i in range(0, len(sans), 2)]
        for i, row in enumerate(rows[-7:]):
            self._text(row, PANEL_X, 530 + i * 22, self.small)

    def _draw_captured(self, y):
        """Pieces each side has taken, and who is ahead in material."""
        taken = captured_pieces(self.game.board)
        balance = material_balance(self.game.board)
        for color, row_y in ((chess.WHITE, y), (chess.BLACK, y + 34)):
            self._text("White" if color == chess.WHITE else "Black", PANEL_X, row_y + 4, self.small, MUTED)
            x = PANEL_X + 56
            for kind in taken[color]:
                self.screen.blit(self.mini[(not color, kind)], (x, row_y))
                x += 16
            lead = balance if color == chess.WHITE else -balance
            if lead > 0:
                self._text(f"+{lead}", x + 14, row_y + 4, self.small, INK)

    def _button(self, button, label):
        pygame.draw.rect(self.screen, (255, 253, 248), button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (226, 218, 203), button.rect, 1, border_radius=8)
        image = self.font.render(label, True, INK)
        self.screen.blit(image, image.get_rect(center=button.rect.center))

    def _status(self):
        if self.error:
            return self.error[:42], ERROR
        if self.game.is_over():
            title, subtitle = end_text(self.game)
            return (subtitle if title == "Checkmate!" else f"Draw: {subtitle.lower()}"), INK
        if self.thinking:
            elapsed = time.perf_counter() - self.think_start
            return f"{self.side[self.game.board.turn]} is thinking… {elapsed:.1f} s", MUTED
        if self.promotion:
            return "Choose a piece", INK
        return ("White" if self.game.board.turn == chess.WHITE else "Black") + " to move", INK

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_release(event.pos)
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    self.drag_pos = event.pos
            self.update()
            self.draw()
            clock.tick(60)


def main():
    App().run()


if __name__ == "__main__":
    main()
