"""Visual effects: move animation, capture particles, confetti (owner: Joseph).

Plan, Section 10.1. Every effect is time-based (not frame-based), so it looks the same
at any frame rate. Each one takes an optional `clock` so the tests can control time.
"""
from __future__ import annotations

import math
import random
import time

import pygame

ANIM_TIME = 0.15            # seconds for a piece to slide
BURST_TIME = 0.4            # seconds for capture particles to fade
CONFETTI_COLOURS = [(239, 71, 111), (255, 209, 102), (6, 214, 160),
                    (17, 138, 178), (227, 154, 69), (255, 255, 255)]


class Slide:
    """A piece sliding from one point to another, with ease-out (fast start, soft stop)."""

    def __init__(self, image, start, end, square, duration=ANIM_TIME, clock=time.perf_counter):
        self.image = image
        self.start, self.end = start, end        # top-left corners, in pixels
        self.square = square                     # destination square (hidden while sliding)
        self.duration = duration
        self.clock = clock
        self.t0 = clock()

    def progress(self) -> float:
        k = min((self.clock() - self.t0) / self.duration, 1.0)
        return 1 - (1 - k) ** 3

    @property
    def done(self) -> bool:
        return self.clock() - self.t0 >= self.duration

    def position(self):
        k = self.progress()
        return (self.start[0] + (self.end[0] - self.start[0]) * k,
                self.start[1] + (self.end[1] - self.start[1]) * k)

    def draw(self, screen):
        screen.blit(self.image, self.position())


class Burst:
    """A small burst of particles where a piece was taken."""

    def __init__(self, center, colour, count=18, life=BURST_TIME, rng=random,
                 clock=time.perf_counter):
        self.center, self.colour, self.life = center, colour, life
        self.clock = clock
        self.t0 = clock()
        self.particles = []
        for _ in range(count):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(60, 180)          # pixels per second
            self.particles.append((math.cos(angle) * speed, math.sin(angle) * speed,
                                   rng.uniform(3, 6)))

    @property
    def done(self) -> bool:
        return self.clock() - self.t0 >= self.life

    def draw(self, screen):
        t = self.clock() - self.t0
        if t >= self.life:
            return
        alpha = int(255 * (1 - t / self.life))
        for vx, vy, radius in self.particles:
            x = self.center[0] + vx * t
            y = self.center[1] + vy * t + 120 * t * t       # a little gravity
            r = max(1, int(radius * (1 - 0.5 * t / self.life)))
            dot = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*self.colour, alpha), (r, r), r)
            screen.blit(dot, (x - r, y - r))


class Confetti:
    """Confetti falling over an area (the board) after a checkmate."""

    def __init__(self, area: pygame.Rect, count=140, rng=random, clock=time.perf_counter):
        self.area = area
        self.clock = clock
        self.t0 = clock()
        self.pieces = []
        for _ in range(count):
            self.pieces.append({
                "x": rng.uniform(area.left, area.right),
                "y": rng.uniform(area.top - area.height, area.top),   # start above the area
                "vy": rng.uniform(90, 220),
                "sway": rng.uniform(10, 30),
                "phase": rng.uniform(0, 2 * math.pi),
                "spin": rng.uniform(-6, 6),
                "size": rng.uniform(5, 10),
                "colour": rng.choice(CONFETTI_COLOURS),
            })

    @property
    def done(self) -> bool:
        t = self.clock() - self.t0
        return all(p["y"] + p["vy"] * t > self.area.bottom for p in self.pieces)

    def draw(self, screen):
        t = self.clock() - self.t0
        for p in self.pieces:
            y = p["y"] + p["vy"] * t
            if not (self.area.top <= y <= self.area.bottom):
                continue
            x = p["x"] + p["sway"] * math.sin(p["phase"] + 3 * t)
            angle = p["spin"] * t
            w, h = p["size"], p["size"] * 0.45
            corners = []
            for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h)):
                corners.append((x + (dx * math.cos(angle) - dy * math.sin(angle)) / 2,
                                y + (dx * math.sin(angle) + dy * math.cos(angle)) / 2))
            pygame.draw.polygon(screen, p["colour"], corners)
