"""App entry point: board, level menu, move list (owner: Joseph; first prototype: Hưng).

A simple Pygame window so every member can play against their own engine.
Run it from the repo root:  python -m ui.app

- Click a piece: dots show its legal squares. Click a dot to move (promotion = queen).
- Each side can be "Human" or any engine in engine/ that has a search() function;
  new levels appear in the menu by themselves.
- Engines think in a background thread on a copy of the board, so the window never freezes.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
import threading
from pathlib import Path

if __package__ in (None, ""):                      # allow "python ui/app.py" as well
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chess
import pygame

import engine
from game.game import EnginePlayer, Game, IllegalMoveError

# --- layout and colours ---
SQ = 80                                            # one square, in pixels
BOARD_X, BOARD_Y = 40, 40
PANEL_X = BOARD_X + 8 * SQ + 40
WIDTH, HEIGHT = PANEL_X + 340, BOARD_Y * 2 + 8 * SQ

LIGHT, DARK = (239, 231, 215), (176, 122, 62)
BACKGROUND, INK, MUTED = (246, 243, 236), (27, 34, 48), (95, 102, 114)
ACCENT, ERROR = (227, 154, 69), (180, 40, 40)
WHITE_PIECE = (251, 251, 248)

GLYPHS = {chess.KING: "♚", chess.QUEEN: "♛", chess.ROOK: "♜",
          chess.BISHOP: "♝", chess.KNIGHT: "♞", chess.PAWN: "♟"}
TIME_CHOICES = [1.0, 2.0, 5.0]
HUMAN = "Human"


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
        pygame.init()
        pygame.display.set_caption("Chess in the Hand of AI")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("segoeui,arial", 20)
        self.small = pygame.font.SysFont("segoeui,arial", 16)
        self.title = pygame.font.SysFont("segoeui,arial", 24, bold=True)
        self.pieces = self._piece_images()

        self.engines = find_engines()
        self.choices = [HUMAN] + sorted(self.engines)
        self.side = {chess.WHITE: HUMAN,
                     chess.BLACK: self.choices[1] if len(self.choices) > 1 else HUMAN}
        self.time_limit = TIME_CHOICES[0]
        self.flipped = False

        x = PANEL_X + 120
        self.buttons = [
            Button(x, 90, 190, 34, lambda: self._next_player(chess.WHITE)),
            Button(x, 132, 190, 34, lambda: self._next_player(chess.BLACK)),
            Button(x, 174, 190, 34, self._next_time),
            Button(PANEL_X, 226, 100, 36, self.new_game),
            Button(PANEL_X + 110, 226, 100, 36, self.undo),
            Button(PANEL_X + 220, 226, 90, 36, self.flip),
        ]
        self.new_game()

    # --- game control ---

    def new_game(self):
        self.game = Game()
        self._reset_turn()
        self.last_engine = None

    def _reset_turn(self):
        """Forget any engine that is still thinking (its answer will be ignored)."""
        self.token = getattr(self, "token", 0) + 1
        self.thinking = False
        self.result = None
        self.error = None
        self.selected = None

    def undo(self):
        humans = [c for c in (chess.WHITE, chess.BLACK) if self.side[c] == HUMAN]
        # Against an engine, take back the engine's reply too, so it is your turn again.
        steps = 2 if len(humans) == 1 and self.game.board.turn in humans else 1
        self.game.undo(steps)
        self._reset_turn()

    def flip(self):
        self.flipped = not self.flipped

    def _next_player(self, color):
        i = self.choices.index(self.side[color])
        self.side[color] = self.choices[(i + 1) % len(self.choices)]
        self._reset_turn()

    def _next_time(self):
        i = TIME_CHOICES.index(self.time_limit)
        self.time_limit = TIME_CHOICES[(i + 1) % len(TIME_CHOICES)]

    # --- input ---

    def handle_click(self, pos):
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                button.on_click()
                return
        square = self.square_at(pos)
        if square is None or self.game.is_over() or self.side[self.game.board.turn] != HUMAN:
            return
        piece = self.game.board.piece_at(square)
        if self.selected is not None:
            moves = [m for m in self.game.legal_moves(self.selected) if m.to_square == square]
            if moves:
                move = next((m for m in moves if m.promotion in (None, chess.QUEEN)), moves[0])
                self.game.play(move)
                self.selected = None
                return
        if piece and piece.color == self.game.board.turn and self.game.legal_moves(square):
            self.selected = square
        else:
            self.selected = None                   # an illegal click just deselects

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

    # --- engine turn (background thread) ---

    def update(self):
        if self.result is not None:
            token, move, stats, error = self.result
            self.result = None
            if token == self.token:
                self._apply_engine_move(move, stats, error)
        name = self.side[self.game.board.turn]
        if name != HUMAN and not self.thinking and not self.error and not self.game.is_over():
            self._start_engine(name)

    def _start_engine(self, name):
        player = EnginePlayer(self.engines[name], name=name, time_limit=self.time_limit)
        board, token = self.game.board.copy(), self.token
        self.thinking = True

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
            self.game.play(move)
        except IllegalMoveError as illegal:
            self.error = str(illegal)
            return
        self.last_engine = (name, san, stats or {})

    # --- drawing ---

    def _piece_images(self):
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
        self._draw_board()
        self._draw_panel()
        pygame.display.flip()

    def _overlay(self, square, color, alpha):
        layer = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        layer.fill((*color, alpha))
        self.screen.blit(layer, self.square_rect(square))

    def _draw_board(self):
        board = self.game.board
        for square in chess.SQUARES:
            light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
            pygame.draw.rect(self.screen, LIGHT if light else DARK, self.square_rect(square))
        if board.move_stack:
            last = board.move_stack[-1]
            for square in (last.from_square, last.to_square):
                self._overlay(square, ACCENT, 110)
        if self.selected is not None:
            self._overlay(self.selected, ACCENT, 170)
        if board.is_check():
            self._overlay(board.king(board.turn), ERROR, 120)
        for square, piece in board.piece_map().items():
            self.screen.blit(self.pieces[(piece.color, piece.piece_type)], self.square_rect(square))
        if self.selected is not None:
            for move in self.game.legal_moves(self.selected):
                center = self.square_rect(move.to_square).center
                if board.piece_at(move.to_square):
                    pygame.draw.circle(self.screen, INK, center, SQ // 2 - 4, 4)   # capture: ring
                else:
                    pygame.draw.circle(self.screen, INK, center, 10)                # move: dot
        for i in range(8):                                                          # a-h and 1-8
            file_label = "abcdefgh"[7 - i if self.flipped else i]
            rank_label = str(i + 1 if self.flipped else 8 - i)
            self._text(file_label, BOARD_X + i * SQ + SQ - 12, BOARD_Y + 8 * SQ + 4, self.small, MUTED)
            self._text(rank_label, BOARD_X - 16, BOARD_Y + i * SQ + 4, self.small, MUTED)

    def _text(self, text, x, y, font=None, color=INK):
        self.screen.blit((font or self.font).render(text, True, color), (x, y))

    def _draw_panel(self):
        self._text("Chess in the Hand of AI", PANEL_X, 40, self.title)
        labels = ["White", "Black", "AI time"]
        values = [self.side[chess.WHITE], self.side[chess.BLACK], f"{self.time_limit:g} s"]
        for button, label, value in zip(self.buttons[:3], labels, values):
            self._text(label, PANEL_X, button.rect.y + 6)
            self._button(button, value)
        for button, label in zip(self.buttons[3:], ["New game", "Undo", "Flip"]):
            self._button(button, label)

        status, color = self._status()
        self._text(status, PANEL_X, 284, self.font, color)

        y = 320
        if self.last_engine:
            name, san, stats = self.last_engine
            nodes = stats.get("nodes", 0) + stats.get("qnodes", 0)
            lines = [f"{name} played {san}",
                     f"depth {stats.get('depth', 0)} · {nodes:,} positions",
                     f"{stats.get('time', 0.0):.2f} s · score {stats.get('score', 0):+d}"]
            for line in lines:
                self._text(line, PANEL_X, y, self.small, MUTED)
                y += 22

        self._text("Moves", PANEL_X, 400, self.font)
        sans = self.game.move_list()
        rows = [f"{i // 2 + 1}. " + " ".join(sans[i:i + 2]) for i in range(0, len(sans), 2)]
        for i, row in enumerate(rows[-12:]):
            self._text(row, PANEL_X, 430 + i * 22, self.small)

    def _button(self, button, label):
        pygame.draw.rect(self.screen, (255, 253, 248), button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (226, 218, 203), button.rect, 1, border_radius=8)
        image = self.font.render(label, True, INK)
        self.screen.blit(image, image.get_rect(center=button.rect.center))

    def _status(self):
        if self.error:
            return self.error[:42], ERROR
        if self.game.is_over():
            result = {"1-0": "White wins", "0-1": "Black wins"}.get(self.game.result(), "Draw")
            return f"{result}: {self.game.reason().replace('_', ' ')}", INK
        if self.thinking:
            return f"{self.side[self.game.board.turn]} is thinking…", MUTED
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
            self.update()
            self.draw()
            clock.tick(30)


def main():
    App().run()


if __name__ == "__main__":
    main()
