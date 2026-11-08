"""Sound effects: one sound per move (owner: Joseph).

Plan, Section 10.2. Priority, only the most important sound plays:
checkmate > draw > check > promotion > capture > castling > normal move.

No sound files are needed: each sound is a short tone made in code. To use real
sounds instead, put move.wav (or .ogg), capture.wav, ... in ui/assets/sounds/;
a file with the right name always wins over the generated tone.

The UI never crashes because of sound: on a computer without audio, sounds are off.
"""
from __future__ import annotations

import math
from array import array
from pathlib import Path

import chess
import pygame

from game.game import Game

ASSETS = Path(__file__).resolve().parent / "assets" / "sounds"

# Each sound is a list of (frequency in Hz, length in ms); frequency 0 = silence.
TONES = {
    "move":      [(520, 60)],                                   # soft "tok"
    "capture":   [(800, 70)],                                   # sharper "clack"
    "castle":    [(520, 50), (0, 40), (520, 50)],               # "tok-tok"
    "promote":   [(660, 60), (880, 60), (1100, 90)],            # rising "ding"
    "check":     [(1200, 140)],                                 # alert "ping"
    "checkmate": [(523, 120), (659, 120), (784, 120), (1047, 320)],   # fanfare
    "draw":      [(330, 300)],                                  # calm low tone
    "illegal":   [(180, 90)],                                   # quiet "bonk"
    "start":     [(523, 80), (784, 120)],                       # short jingle
}
SOUND_NAMES = tuple(TONES)


def sound_for(board: chess.Board, move: chess.Move) -> str:
    """Name of the sound for `move`, played from `board` (the board is not changed).

    Uses the same game-over rules as the game itself (game/game.py), so threefold
    repetition and the 50-move rule play the draw sound too.
    """
    is_capture = board.is_capture(move)          # must be read BEFORE the move
    is_castle = board.is_castling(move)
    is_promo = move.promotion is not None
    game = Game(board)                           # Game copies the board
    game.play(move)
    after = game.board
    if after.is_checkmate():
        return "checkmate"
    if game.is_over():
        return "draw"
    if after.is_check():
        return "check"
    if is_promo:
        return "promote"
    if is_capture:
        return "capture"
    if is_castle:
        return "castle"
    return "move"


def make_tone(segments, rate: int = 44100, channels: int = 2, volume: float = 0.35) -> bytes:
    """Signed 16-bit PCM for a list of (frequency, ms) segments, with a fast fade-out."""
    samples = array("h")
    for freq, ms in segments:
        count = int(rate * ms / 1000)
        decay = 25 if ms < 150 else 8            # long notes fade more slowly
        for i in range(count):
            t = i / rate
            value = 0.0 if freq == 0 else math.sin(2 * math.pi * freq * t) * math.exp(-t * decay)
            sample = int(value * volume * 32767)
            for _ in range(channels):
                samples.append(sample)
    return samples.tobytes()


class SoundPlayer:
    """Loads every sound once. play(name) does nothing when muted or without audio."""

    def __init__(self, folder: Path = ASSETS):
        self.enabled = True
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            rate, size, channels = pygame.mixer.get_init()
        except pygame.error:                     # no audio device: stay silent
            return
        for name, segments in TONES.items():
            try:
                path = next((p for p in (folder / f"{name}.wav", folder / f"{name}.ogg")
                             if p.exists()), None)
                if path is not None:
                    self.sounds[name] = pygame.mixer.Sound(str(path))
                elif size == -16:
                    self.sounds[name] = pygame.mixer.Sound(
                        buffer=make_tone(segments, rate, channels))
            except pygame.error:
                continue                         # a broken file: skip only that sound

    @property
    def available(self) -> bool:
        return bool(self.sounds)

    def toggle(self) -> None:
        self.enabled = not self.enabled

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if self.enabled and sound is not None:
            sound.play()
