# Chess in the Hand of AI

**Course:** IT3160E – Introduction to Artificial Intelligence (HUST)
**Type:** Group project (5 members, 4 weeks)
**Topic area:** Adversarial search (Chapter 4 – Search II)

---

## Table of contents

1. [Project summary](#1-project-summary)
2. [Problem statement](#2-problem-statement)
3. [Link to the course material](#3-link-to-the-course-material)
4. [Scope: what is in and what is out](#4-scope-what-is-in-and-what-is-out)
5. [Input and output data](#5-input-and-output-data)
6. [System architecture](#6-system-architecture)
7. [The four AI levels](#7-the-four-ai-levels)
8. [Algorithms in detail](#8-algorithms-in-detail)
9. [The heuristic evaluation function](#9-the-heuristic-evaluation-function)
10. [User interface](#10-user-interface)
11. [Benchmark module](#11-benchmark-module)
12. [Experiments](#12-experiments)
13. [Data and external resources](#13-data-and-external-resources)
14. [Project structure (code)](#14-project-structure-code)
15. [Team roles](#15-team-roles)
16. [Timeline](#16-timeline)
17. [Testing and debugging](#17-testing-and-debugging)
18. [Risks and how to handle them](#18-risks-and-how-to-handle-them)
19. [Expected results](#19-expected-results)
20. [Related work](#20-related-work)
21. [Future work](#21-future-work)
22. [Report outline](#22-report-outline)
23. [Glossary](#23-glossary)
24. [References](#24-references)

---

## 1. Project summary

We build a **chess app** where a person can play against an AI at **four levels**: Easy, Medium, Hard and Master. Each level adds **new search techniques** on top of the level before it (Levels 3 and 4 each add a small group; Experiment 6 tests each technique on its own):

| Level | Technique added |
|---|---|
| 1 – Easy | Greedy search (look 1 move ahead, random tie-break) |
| 2 – Medium | Minimax search |
| 3 – Hard | Alpha-beta pruning + move ordering + iterative deepening |
| 4 – Master | Transposition table + quiescence search + better evaluation (PeSTO) |

After building the levels, we run **controlled experiments** to measure how much each technique helps: how many positions it checks, how deep it searches, how many puzzles it solves, and how often it wins. A pilot test of the Section 8 pseudocode (Section 7.1) already shows four clearly different levels.

**This is a classical (search-based) AI project.** It does **not** use machine learning or deep learning. Nothing is trained. The "intelligence" comes from:
- **search** – exploring possible future moves, and
- **a heuristic evaluation function** – a hand-written formula that guesses how good a position is.

---

## 2. Problem statement

Chess is a **two-player, zero-sum game with perfect information**:
- two players (White = MAX, Black = MIN),
- one player's win is the other player's loss,
- both players see the whole board.

The problem is that the game tree is huge:
- **Branching factor b ≈ 35**: in a normal position there are about 35 legal moves.
- **Depth m ≈ 100 half-moves**: a typical game lasts about 50 moves per side.
- Full minimax costs **O(bᵐ)** ≈ 35¹⁰⁰ positions. That is impossible.
- Even looking only **6 half-moves** ahead means 35⁶ ≈ **1.8 billion** positions.

So a chess AI cannot check everything. It must:
1. **choose which moves are worth checking** (pruning, move ordering),
2. **guess how good a position is** without playing to the end (heuristic evaluation),
3. **expect the opponent to play their best move** (minimax).

**Goal:** build four AI levels, each adding new search techniques, and measure how much each technique improves search efficiency and playing strength.

**Research questions:**
1. How many positions does alpha-beta save compared with minimax at the same depth? How much does move ordering add?
2. With a fixed time per move (e.g. 2 seconds), how much deeper can each version search?
3. How much playing strength comes from better **search**, and how much from a better **evaluation**?

---

## 3. Link to the course material

All main algorithms come from **Chapter 4 – Search II** (`Chapter4__SearchII_ver2.pdf`) and the Vietnamese **Lecture Notes** (sections 3.6.2–3.6.3).

| Slides | Topic | Used in project |
|---|---|---|
| 8 | Informed search uses extra knowledge; lists MiniMax and Alpha-beta | General idea |
| 9–10 | Best-first search, greedy best-first, evaluation function | Level 1 idea (greedy choice by an evaluation function, see note) |
| 17, 25–36 | A*, heuristic h(n), admissible and consistent heuristics, dominance, effective branching factor | Heuristic idea, b* metric |
| 63–64 | Adversarial search, problems of searching in games | Problem statement |
| 65–66 | Tic-tac-toe, representing a game (initial state, successor function, terminal test, utility) | Game formulation |
| 69–71 | MINIMAX value, algorithm, properties (b ≈ 35, m ≈ 100 for chess) | Level 2 |
| 72 | Prune and search: the idea of α-β | Level 3 |
| 77–80 | α-β example, why it is called α-β, algorithm | Level 3 |
| 81 | α-β is still not enough for big games → need a heuristic like h(n) in A* | Evaluation function |

**Note:** Level 1 only looks one move ahead and plays the best-scoring move. It is not full greedy best-first search, which keeps a frontier (priority queue) of nodes to expand.

**Lecture Notes extra point:** with perfect move ordering, alpha-beta goes from **O(bᵐ)** to **O(b^(m/2))**; in chess the effective branching drops from 35 to about 6. With random ordering it is about **O(b^(3m/4))**, around 14. This is why we add **move ordering**.

### Game formulation (as in slide 66)

| Element | In our chess project |
|---|---|
| Initial state | Standard starting position, White to move |
| Players | MAX = White, MIN = Black |
| Successor function | `board.legal_moves` from python-chess |
| Terminal test | `board.is_game_over()` (checkmate, stalemate, draw rules); inside the search also `board.is_repetition(2)` (Section 8.8) |
| Utility function | Win = +∞ (large number), loss = −∞, draw = 0 |
| Heuristic (at cut-off depth) | Evaluation function (Section 9) |

---

## 4. Scope: what is in and what is out

**In scope**
- Playable app (human vs AI, AI vs AI)
- Four AI levels with one shared interface
- Hand-written evaluation (Simplified Evaluation and PeSTO)
- Benchmark scripts and six experiments
- Report and presentation

**Out of scope**
- Machine learning / neural networks: nothing is trained or learned, not even in future work (PeSTO's numbers were tuned by their author; we only copy them, see 9.4)
- Opening books and endgame tablebases (they would hide the effect of search)
- Writing our own move generator (python-chess does this)
- Online multiplayer

---

## 5. Input and output data

### Input

| Input | Description | Example |
|---|---|---|
| Board position | Current state, stored as FEN text | `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1` |
| Legal moves | Generated by python-chess | `[e7e5, c7c5, g8f6, ...]` |
| Settings | AI level, plus time per move (UI), node budget (experiments) or fixed depth | `level=3, time_limit=2.0` or `level=3, node_limit=26000` |
| Test puzzles | 50 tactical puzzles: WAC.001–WAC.050, the first 50, no hand-picking (Win At Chess, EPD format) | `... bm Qg6; id "WAC.001";` |
| Opening positions | 20–25 start positions for AI vs AI games | list of FEN strings |

### Output

| Output | Description | Example |
|---|---|---|
| Best move | The move the AI plays (UCI format) | `e2e4` |
| Search statistics | Nodes searched, depth reached, time, score | `{nodes: 48213, depth: 4, time: 1.98, score: +35}` |
| Game records | All test games saved as PGN files | `games/level3_vs_level2.pgn` |
| Experiment results | Tables and charts for the report | `results/exp2_nodes.csv`, `charts/nodes_vs_depth.png` |

**Note:** the data is used **only for testing**, not for training.

---

## 6. System architecture

```
          ┌───────────────────────┐
          │        PLAYER         │
          └──────────┬────────────┘
                     │ moves, level
                     ▼
┌──────────────────────────────────────────────┐
│ 1. INTERFACE (Pygame / web)                  │
│    Board on screen · Level selector · History│
└──────────────────────┬───────────────────────┘
                       │ board + time limit
                       ▼
┌──────────────────────────────────────────────┐
│ 2. GAME ENGINE (python-chess)                │
│    Legal moves · FEN · Checkmate/draw rules  │
└──────────────────────┬───────────────────────┘
                       │ position to search
                       ▼
┌──────────────────────────────────────────────┐
│ 3. SEARCH ENGINE                             │
│    search(board, limit) → (move, stats)      │
│    L1 Greedy                                 │
│    L2 Minimax                                │
│    L3 Alpha-beta + ordering + deepening      │
│    L4 + Transposition table + Quiescence     │
└──────────────────────┬───────────────────────┘
                       │ leaf positions ▲ scores
                       ▼                │
┌──────────────────────────────────────────────┐
│ 4. EVALUATION FUNCTION (heuristic)           │
│    Material · Piece-square tables ·          │
│    Game phase (tapered)                      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 5. BENCHMARK (no screen)                     │
│    Tournaments · Puzzles · Logs → charts     │
└──────────────────────────────────────────────┘
```

### The shared interface (very important)

Every level uses the **same function signature**:

```python
def search(board: chess.Board, time_limit: float | None = None,
           depth: int | None = None,
           node_limit: int | None = None) -> tuple[chess.Move, dict]:
    """Return the best move and a stats dictionary.

    Works on board.copy(), so the caller's board is never changed (Section 8.5).
    time_limit is for the UI; node_limit is for experiments (Section 12).
    """
```

The stats dictionary always has the same keys:

```python
stats = {
    "nodes": 0,        # positions visited
    "depth": 0,        # deepest full search completed
    "time": 0.0,       # seconds used
    "score": 0,        # evaluation of the chosen move (centipawns)
    "tt_hits": 0,      # Level 4 only
    "qnodes": 0,       # Level 4 only (quiescence nodes)
}
```

Because of this, the interface and the benchmark can use **any level in the same way**, and each member can work separately.

---

## 7. The four AI levels

| | Level 1 – Easy | Level 2 – Medium | Level 3 – Hard | Level 4 – Master |
|---|---|---|---|---|
| Search | Greedy (random tie-break) | Minimax | Alpha-beta | Alpha-beta |
| Depth | 1 half-move | 3 half-moves (fixed) | As deep as the limit allows | As deep as the limit allows |
| Move ordering | – | – | ✓ (MVV-LVA) | ✓ (+ TT move first) |
| Iterative deepening | – | – | ✓ | ✓ |
| Transposition table | – | – | – | ✓ |
| Quiescence search | – | – | – | ✓ |
| Repetition = draw | – | ✓ | ✓ | ✓ |
| Evaluation | Material only (+ mate in 1) | Simplified (material + PST) | Simplified | PeSTO (tapered) |
| Stop rule | Instant | Fixed depth (1–4 s in Python) | 2 s per move (UI) / node budget (experiments) | 2 s per move (UI) / node budget (experiments) |
| Playing style | Grabs pieces, falls into simple traps | Avoids 1-move blunders | Sees 4 half-moves, but misjudges captures at the horizon | Sound captures (quiescence), better endgames |

**Design rule:** each level adds **a small group of ideas** on top of the level before (one idea for Levels 1–2, three each for Levels 3 and 4). For the report experiments, we also test each idea **separately** (Experiments 2, 3 and 6 in Section 12), so we know exactly what caused each improvement.

### 7.1 Pilot test of the four levels

A pilot prototype of the Section 8 pseudocode **as first written** (before the fixes in 8.1 and 8.4–8.8) was run with python-chess 1.11.2 on an Intel i5-11400H laptop in October 2026. Level 4 used the hand-made tapered evaluation (9.4) instead of the PeSTO numbers. It measured 10 test positions, then played 40 games between neighbouring levels: 8 fixed openings × 2 colours (4 openings for Levels 1–2), node budgets equal to about 2 s of search, and the adjudication rule of Section 12.

| Level | Depth reached (middlegame / endgame) | Time per move | Result vs the level below |
|---|---|---|---|
| 1 – Easy | 1 | instant | – |
| 2 – Medium | 3 / 3 | 1–4 s | +7 =1 −0 (94%) |
| 3 – Hard | 4 / 5 | ≤ 2 s | +11 =5 −0 (84%) |
| 4 – Master | 3–4 / 5–7 | ≤ 2 s | +13 =3 −0 (91%) |

What the pilot showed:
- The four levels are clearly different in strength. With only 8–16 games per pair, the exact Elo gaps are still unknown.
- Level 4 did **not** search deeper than Level 3 (average depth in the games: 4.39 vs 4.42), because quiescence uses about half its time. Its advantage comes from quiescence, the transposition table and the tapered evaluation together; Experiment 6 separates them.
- Without a random tie-break, Level 1 always opens 1.Nh3 from the starting position and then shuffles its rooks (fixed in 8.1).
- All 9 draws were threefold repetitions, because the search could not see repetition (fixed in 8.8).
- "Medium" (fixed depth 3) sometimes thinks longer than "Hard" (2 s). The UI should show a "thinking…" message.

---

## 8. Algorithms in detail

Scores are in **centipawns** (1 pawn = 100). Positive = good for White, negative = good for Black.

### 8.1 Level 1 – Greedy search

Try every legal move, score the new position, pick the best. If several moves are equally good, pick one of them at random.

```python
import random

def greedy(board, rng=random):
    sign = 1 if board.turn == chess.WHITE else -1   # score from the mover's view
    best_score, best_moves = -INF, []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            score = MATE                            # always play mate in 1
        else:
            score = sign * evaluate_material(board)
        board.pop()
        if score > best_score:
            best_score, best_moves = score, [move]
        elif score == best_score:
            best_moves.append(move)                 # keep all equally good moves
    return rng.choice(best_moves)                   # random tie-break
```

- **Strength:** very fast.
- **Weakness:** cannot see the opponent's reply, so it takes a pawn even if it loses its queen next move.
- **Why the random tie-break:** with a material-only evaluation, every quiet move gets the same score. Without the random choice, Level 1 always plays the first move python-chess generates: from the starting position it always opens 1.Nh3 and then shuffles its rooks (pilot, Level 1 vs Level 1). For experiments, pass `random.Random(seed)` so games can be replayed.

### 8.2 Level 2 – Minimax (slides 69–71)

MAX (White) picks the highest value; MIN (Black) picks the lowest. Both assume the other plays perfectly.

```python
def minimax(board, depth, maximizing, ply=0):
    stats["nodes"] += 1
    if board.is_game_over() or (ply > 0 and board.is_repetition(2)):
        return terminal_score(board, ply)     # mate or draw, see 8.8
    if depth == 0:
        return evaluate(board)

    if maximizing:
        value = -INF
        for move in board.legal_moves:
            board.push(move)
            value = max(value, minimax(board, depth - 1, False, ply + 1))
            board.pop()
        return value
    else:
        value = INF
        for move in board.legal_moves:
            board.push(move)
            value = min(value, minimax(board, depth - 1, True, ply + 1))
            board.pop()
        return value
```

**Properties (slide 71):**
- Complete: yes (finite tree)
- Optimal: yes, against an optimal opponent (within the searched depth)
- Time: O(bᵐ)
- Space: O(bm) (depth-first)

### 8.3 Level 3 – Alpha-beta pruning (slides 72, 77–80)

- **α** = best value MAX is already sure of (lower bound)
- **β** = best value MIN is already sure of (upper bound)
- If **α ≥ β**, stop searching this branch. It cannot change the result.

```python
def alphabeta(board, depth, alpha, beta, maximizing, ply=0):
    stats["nodes"] += 1
    if board.is_game_over() or (ply > 0 and board.is_repetition(2)):
        return terminal_score(board, ply)     # mate or draw, see 8.8
    if depth == 0:
        return evaluate(board)

    if maximizing:
        value = -INF
        for move in order_moves(board):
            board.push(move)
            value = max(value, alphabeta(board, depth - 1, alpha, beta, False, ply + 1))
            board.pop()
            alpha = max(alpha, value)
            if alpha >= beta:
                break          # β cut-off
        return value
    else:
        value = INF
        for move in order_moves(board):
            board.push(move)
            value = min(value, alphabeta(board, depth - 1, alpha, beta, True, ply + 1))
            board.pop()
            beta = min(beta, value)
            if alpha >= beta:
                break          # α cut-off
        return value
```

**Key fact:** alpha-beta returns **exactly the same value** as minimax at the same depth. It only skips useless work. We use this as a correctness test (Experiment 1). The chosen move can still differ when two moves have the same value, because the moves are tried in a different order.

**Implementation tip:** many engines write this in **negamax** form (one function instead of two, using `score = -search(..., -beta, -alpha)`). It is shorter and makes quiescence and the transposition table easier. Both forms give the same result.

### 8.4 Move ordering

Alpha-beta prunes more when **good moves are searched first**.

Order used:
1. **TT move** (Level 4): the best move from the transposition table
2. **Captures**, sorted by **MVV-LVA** (Most Valuable Victim – Least Valuable Attacker): e.g. pawn takes queen first, queen takes pawn last
3. **Promotions**
4. Other (quiet) moves

**Checks are not tried first.** `board.gives_check()` costs about 4 µs per move, so in the pilot, sorting with it cost 260–300 µs per node, 7–8× the cost of generating the moves. Without it, ordering costs about 57 µs and Level 3 searches 2.3× more nodes per second. The search still finds checks; they are just not tried first.

```python
PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

def move_score(board, move, tt_move=None):
    if move == tt_move:
        return 100000
    score = 0
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        victim_value = PIECE_VALUE[victim.piece_type] if victim else 1  # en passant
        attacker_value = PIECE_VALUE[board.piece_at(move.from_square).piece_type]
        score += 10000 + 10 * victim_value - attacker_value
    if move.promotion:
        score += 9000
    return score

def order_moves(board, tt_move=None):
    return sorted(board.legal_moves,
                  key=lambda m: move_score(board, m, tt_move), reverse=True)
```

### 8.5 Iterative deepening

Search depth 1, then 2, then 3, ... until the limit is reached. Keep the best move from the **last completed** depth. The limit is a time (for the UI) or a node budget (for experiments, see Section 12).

```python
class SearchTimeout(Exception):
    pass

def iterative_deepening(board, time_limit=None, node_limit=None):
    board = board.copy()              # never search on the game board (see below)
    start = time.perf_counter()
    best_move = None
    depth = 1
    while True:
        try:
            move, score = search_root(board, depth, start, time_limit, node_limit,
                                      first_move=best_move)
            best_move = move
            stats["depth"] = depth
        except SearchTimeout:
            break                     # depth not finished → ignore it
        if time_limit and time.perf_counter() - start > time_limit * 0.5:
            break                     # next depth would likely not finish
        if node_limit and stats["nodes"] + stats["qnodes"] > node_limit * 0.5:
            break
        depth += 1
    return best_move
```

Why it helps:
- **Time control:** always has a move ready when time is up.
- **Better ordering:** the best move from depth d is searched first at depth d+1, so pruning works better.
- **Low extra cost:** most of the work is in the last depth, so repeating smaller depths costs little.

Inside the search, count every node and check the clock every ~1,000 nodes; raise `SearchTimeout` when a limit is reached.

**Why `board.copy()`:** the exception jumps out of the recursion, so all the `board.pop()` calls on the way up are skipped. In the pilot, an aborted search left 5 search moves on the game board, and `board.push()` does not check legality, so the game silently continued from a wrong position. A copy costs about 30 µs per search, and the UI thread needs one anyway (Section 10).

### 8.6 Level 4 – Transposition table (TT)

The same position can be reached by different move orders (e.g. `1.e4 e5 2.Nf3` and `1.Nf3 e5 2.e4`). The TT is a **dictionary** that remembers positions already searched.

- **Key:** Zobrist hash of the position: `chess.polyglot.zobrist_hash(board)` (python-chess provides it). It is computed from scratch each time, about 14 µs per call. `board._transposition_key()` (about 0.2 µs) also works as a dictionary key, but it is a private python-chess method; explain Zobrist hashing in the report either way.
- **Value:** depth searched, score, flag, best move.

Because of pruning, a stored score is not always exact. We save a **flag**:

| Flag | Meaning |
|---|---|
| `EXACT` | The score is the true value |
| `LOWER` | The real score is **at least** this (a β cut-off happened) |
| `UPPER` | The real score is **at most** this (no move beat α) |

```python
# at the start of a node (negamax form)
original_alpha = alpha                 # remember it before the TT changes alpha
entry = tt.get(key)
if entry and entry.depth >= depth:
    score = score_from_tt(entry.score, ply)
    if entry.flag == EXACT:
        return score
    if entry.flag == LOWER:
        alpha = max(alpha, score)
    elif entry.flag == UPPER:
        beta = min(beta, score)
    if alpha >= beta:
        return score

# ... search the moves (TT move first) ...

# at the end of a node
if best_score <= original_alpha:
    flag = UPPER
elif best_score >= beta:
    flag = LOWER
else:
    flag = EXACT
tt[key] = Entry(depth, score_to_tt(best_score, ply), flag, best_move)
```

**Mate scores:** a mate score counts plies from the root (8.8), but the same position can be reached at a different ply. Store mate scores relative to the node, and convert them back when reading:

```python
MATE_BOUND = MATE - 1000              # scores beyond this are mate scores

def score_to_tt(score, ply):
    if score > MATE_BOUND:
        return score + ply
    if score < -MATE_BOUND:
        return score - ply
    return score

def score_from_tt(score, ply):
    if score > MATE_BOUND:
        return score - ply
    if score < -MATE_BOUND:
        return score + ply
    return score
```

**Size:** a Python dictionary grows with every node searched. Clear the table at the start of each move (simplest), or cap its size.

**Warning:** this is the part with the most bugs. Test it carefully (Section 17). If it does not work by the end of week 3, skip it. Levels 1–3 plus quiescence is still a full project.

### 8.7 Level 4 – Quiescence search

**Horizon effect:** if the search stops in the middle of a capture exchange, the score is wrong. Example: at the last depth the AI takes a knight with its queen and thinks it is +3, but the next move (not searched) is a pawn taking the queen.

**Fix:** at depth 0, do not evaluate right away. Keep searching **captures only** (all escapes when in check) until the position is "quiet".

```python
MAX_PLY = 64

def quiescence(board, alpha, beta, ply):     # negamax form
    stats["qnodes"] += 1
    if ply >= MAX_PLY:
        return evaluate_side_to_move(board)   # safety stop
    if board.is_check():
        moves = order_moves(board)            # in check: try every escape, no stand pat
        if not moves:
            return -(MATE - ply)              # checkmated
    else:
        stand_pat = evaluate_side_to_move(board)  # score if we stop here
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        moves = order_captures(board)         # captures only, MVV-LVA

    for move in moves:
        board.push(move)
        score = -quiescence(board, -beta, -alpha, ply + 1)
        board.pop()
        if score >= beta:
            return beta
        alpha = max(alpha, score)
    return alpha
```

- **Stand pat:** the side to move can usually "do nothing" instead of capturing, so the current score is a lower bound. This is **not allowed in check**: the side to move must escape, so all escapes are searched.
- Quiescence **reduces** the horizon effect for captures. It does **not** remove it completely (quiet threats can still be missed).
- **Cost:** in the pilot, quiescence nodes were 1.5–6× the normal nodes in middlegames, so Level 4 searched no deeper than Level 3 (it still won clearly). If it is too slow, skip captures that cannot raise alpha even if they win the piece (**delta pruning**).

### 8.8 Special cases to handle

- **Checkmate:** the side to move gets `-(MATE - ply)` (prefer faster mates, delay being mated).
- **Stalemate / draw rules:** return 0.
- **Repetition:** inside the search, treat a position that already appeared as a draw (`board.is_repetition(2)`, about 1 µs). `board.is_game_over()` only sees fivefold repetition. In the pilot, all 9 drawn games were threefold repetitions because the search could not see repetition.
- **Do not call `board.can_claim_draw()` inside the search:** it costs about 280 µs per call (45× `board.is_game_over()`). Use `board.is_game_over(claim_draw=True)` only in the game loop (UI and tournaments), so games end at threefold repetition and the 50-move rule.
- **No legal moves at root:** game is over; return `None`.

```python
MATE = 100000

def terminal_score(board, ply):
    """Score of a finished or repeated position, from White's point of view."""
    if board.is_checkmate():
        return -(MATE - ply) if board.turn == chess.WHITE else MATE - ply
    return 0          # stalemate, insufficient material, 75-move rule, repetition
```

In negamax form (Level 4), scores are from the side to move's view: `-(MATE - ply)` if checkmated, otherwise 0.

### 8.9 Speed notes for Python (measured in the pilot)

Cost of one call with python-chess 1.11.2 on an i5-11400H laptop, in a middlegame position:

| Call | Cost | Rule |
|---|---|---|
| `board.push(move)` + `board.pop()` | 3 µs | – |
| `list(board.legal_moves)` | 35 µs | – |
| `board.is_game_over()` | 6 µs | Fine inside the search |
| `board.can_claim_draw()` | 282 µs | Never inside the search (8.8) |
| `board.is_repetition(2)` | 0.8 µs | Use for repetition inside the search (8.8) |
| `board.gives_check(move)` | 4 µs per move | Not in move ordering (8.4) |
| `chess.polyglot.zobrist_hash(board)` | 14 µs | Or `board._transposition_key()`, 0.2 µs (8.6) |
| Evaluation (material / Simplified / tapered) | 19–24 µs | – |
| `board.copy()` | 29 µs | Once per search (8.5) |

Search speed in the pilot: minimax about 25,000 nodes/s; alpha-beta with the original ordering 12,000–14,000 nodes/s in most positions (2.3× faster without `gives_check`); Level 4 15,000–31,000 nodes/s, counting quiescence nodes.

---

## 9. The heuristic evaluation function

### 9.1 What it is

The search cannot reach the end of the game, so it stops at a certain depth. At that point, the **evaluation function** gives a **single number** that estimates who is winning.

- `+300` → White is about 3 pawns better
- `0` → about equal
- `-150` → Black is about 1.5 pawns better

Slide 81 says: for big games, α-β is still not enough, so we need **"knowledge to enable evaluation of each state"**. This heuristic **plays a similar role to h(n) in A\***.

**Difference from A\*:** in A*, h(n) estimates **cost to the goal**, and if it is **admissible** (never overestimates) A* is optimal. In chess, the heuristic estimates **who is winning**. Admissibility does not apply, and there is no optimality guarantee. That is why **searching deeper** matters so much.

### 9.2 Evaluation 1 – Material only (Level 1)

| Piece | Value |
|---|---|
| Pawn | 100 |
| Knight | 320 |
| Bishop | 330 |
| Rook | 500 |
| Queen | 900 |
| King | not counted (cannot be captured) |

`score = sum(White pieces) − sum(Black pieces)`

### 9.3 Evaluation 2 – Simplified Evaluation Function (Levels 2–3)

**Source:** Tomasz Michniewski, "Simplified Evaluation Function", Chess Programming Wiki.

- The same material values as above.
- Plus a **piece-square table (PST)** for each piece: 64 numbers, one bonus or penalty per square.

Example – knight table (from White's side; top row = rank 8):

```
-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,  0,  0,  0,  0,-20,-40,
-30,  0, 10, 15, 15, 10,  0,-30,
-30,  5, 15, 20, 20, 15,  5,-30,
-30,  0, 15, 20, 20, 15,  0,-30,
-30,  5, 10, 15, 15, 10,  5,-30,
-40,-20,  0,  5,  5,  0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50
```

Meaning: "a knight in the centre is good, a knight on the edge is bad."

### 9.4 Evaluation 3 – PeSTO (Level 4)

**PeSTO = "Piece-Square Tables Only"**, by Ronald Friederich (engine RofChade). Source: Chess Programming Wiki, "PeSTO's Evaluation Function".

- **Two sets of tables** for each piece: **middlegame (mg)** and **endgame (eg)**.
- The numbers were **tuned automatically** by their author with Texel's tuning method (a logistic-regression fit to the results of many real games), so they are better than hand-picked values. We only copy the finished numbers; we do not train anything. Say this clearly in the report.

PeSTO material values:

| Piece | Middlegame | Endgame |
|---|---|---|
| Pawn | 82 | 94 |
| Knight | 337 | 281 |
| Bishop | 365 | 297 |
| Rook | 477 | 512 |
| Queen | 1025 | 936 |

**Tapered evaluation:** blend the two scores by **game phase**.

```
phase weights: knight = 1, bishop = 1, rook = 2, queen = 4   (max total = 24)
phase = sum of weights of pieces on the board   (24 = full board, 0 = only pawns/kings)

score = (mg_score * phase + eg_score * (24 - phase)) / 24
```

Why it matters: the king should **hide** in the middlegame but **walk to the centre** in the endgame. One fixed table cannot do both.

**Strict no-ML option (hand-made tapered evaluation):** if the lecturer counts tuned numbers as machine learning, build the tapered evaluation from hand-written tables only. Use the Simplified tables (9.3) for the middlegame, and the same tables with Michniewski's king **endgame** table for the endgame, with the same phase formula. The pilot's Level 4 used exactly this and still beat Level 3 (+13 =3 −0). King endgame table (from White's side; top row = rank 8):

```
-50,-40,-30,-20,-20,-30,-40,-50,
-30,-20,-10,  0,  0,-10,-20,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-30,  0,  0,  0,  0,-30,-30,
-50,-30,-30,-30,-30,-30,-30,-50
```

### 9.5 Code sketch

```python
def evaluate(board):
    # MG_PST / EG_PST use python-chess order: a1 = index 0. Tables copied from the
    # Chess Programming Wiki start at a8; convert each one once:
    #     table = [cpw_table[sq ^ 56] for sq in range(64)]
    mg = [0, 0]; eg = [0, 0]; phase = 0
    for square, piece in board.piece_map().items():
        p = piece.piece_type
        c = 0 if piece.color == chess.WHITE else 1
        sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
        mg[c] += MG_VALUE[p] + MG_PST[p][sq]
        eg[c] += EG_VALUE[p] + EG_PST[p][sq]
        phase += PHASE_INC[p]
    phase = min(phase, 24)
    mg_score = mg[0] - mg[1]
    eg_score = eg[0] - eg[1]
    return (mg_score * phase + eg_score * (24 - phase)) // 24
```

**Careful:** many published tables are written with rank 8 at the top (a8 = index 0), while python-chess numbers squares from a1 = 0 to h8 = 63. Convert the tables once, as in the comment above. Test the orientation with a **pawn or king**, not a knight: a white pawn on e7 must score more than on e2, and a white king on g1 more than on g8 in the middlegame. The knight table looks almost the same upside down, and the symmetry test (Section 17) flips both colours the same way, so neither catches this bug. In the pilot, tables pasted upside down passed both.

### 9.6 Possible extra terms (only if time allows)

| Term | Idea | Example value |
|---|---|---|
| Doubled pawns | Two pawns on the same file are weak | −15 each |
| Isolated pawn | No friendly pawn on neighbour files | −15 |
| Passed pawn | No enemy pawn can stop it | +20 to +100 by rank |
| Mobility | More legal moves = more activity | +2 to +5 per move |
| Bishop pair | Two bishops work well together | +30 |

Keep these as optional. Each extra term makes evaluation slower, which means less depth in Python.

---

## 10. User interface

### Option A – Pygame (recommended, simple)
- Draw 64 squares with your own colours.
- Load your own piece images (PNG). They can be designed in Figma for a custom look.
- Click a piece, then click a target square. Check legality with python-chess.
- Show: level selector, move history (SAN), AI thinking info (depth, nodes, score), new game / undo buttons.
- Run the AI in a **separate thread**, so the window does not freeze while it thinks. Give the thread `board.copy()`, never the board the UI is drawing (Section 8.5).

### Option B – Web (more modern look)
- Front end: **chessboard.js** or **chessground** (the Lichess board) with custom CSS themes and piece images.
- Back end: **Flask** or **FastAPI** with one endpoint, e.g. `POST /move {fen, level} → {move, stats}`.

### Nice extras
- Highlight the last move and legal target squares.
- Show an "evaluation bar" from the AI's score.
- Show the AI's "best line" (principal variation).
- Promotion dialog (choose queen, rook, bishop or knight).

### 10.1 Bonus: vivid UI

These are not needed for the AI part, but they make the demo much more fun to watch.

| Feature | How it looks | How to do it (Pygame) |
|---|---|---|
| **Board themes** | 3–4 colour themes (e.g. "Forest", "Ocean", "Wood", "Neon") the player can switch | Store each theme as `(light, dark, highlight)` colours; redraw with the chosen theme |
| **Custom pieces** | Your own piece set, designed in Figma, exported as PNG with transparent background | `pygame.image.load(...).convert_alpha()`, scale to square size once at start |
| **Drag and drop** | Pick up a piece with the mouse and drop it | On `MOUSEBUTTONDOWN` remember the piece; draw it at the mouse position; on `MOUSEBUTTONUP` try the move |
| **Legal-move hints** | Small dots on empty target squares, rings on capture squares | `[m for m in board.legal_moves if m.from_square == selected]` |
| **Last-move highlight** | The from- and to-squares glow softly | Draw a semi-transparent rectangle (`pygame.Surface` with alpha) |
| **Check glow** | Red radial glow under the king in check | If `board.is_check()`, draw a red circle with alpha on `board.king(board.turn)` |
| **Move animation** | Pieces slide smoothly (~150 ms) instead of jumping | Interpolate position between start and end square over several frames |
| **Capture effect** | Small burst of particles where a piece is taken | Spawn 15–20 small circles with random speed; fade them out over 0.4 s |
| **Checkmate screen** | Board dims, big "Checkmate! White wins" banner, confetti | Overlay a dark transparent surface, draw text, animate confetti particles |
| **Evaluation bar** | Vertical bar beside the board, white/black share shows who is winning | Map score with `0.5 + 0.5 * tanh(score / 400)` to the bar height |
| **Captured pieces** | Small icons of taken pieces, plus material difference ("+3") | Compare piece counts with the starting set |
| **AI thinking panel** | "Thinking… depth 4, 52,310 positions, score +0.4" | Read the `stats` dict from `search()`; update while the AI thread runs |
| **Move list** | Scrollable list in chess notation (1. e4 e5 2. Nf3 …) | `board.san(move)` before pushing the move |
| **Flip board** | Play as Black with Black at the bottom | Draw square `sq` at `chess.square_mirror(sq)` when flipped |

**Animation example:**

```python
ANIM_TIME = 0.15  # seconds

def animate_move(screen, piece_img, start_xy, end_xy, draw_board):
    clock = pygame.time.Clock()
    t = 0.0
    while t < ANIM_TIME:
        t += clock.tick(60) / 1000
        k = min(t / ANIM_TIME, 1.0)
        k = 1 - (1 - k) ** 3                      # ease-out: fast start, soft stop
        x = start_xy[0] + (end_xy[0] - start_xy[0]) * k
        y = start_xy[1] + (end_xy[1] - start_xy[1]) * k
        draw_board()                               # board without the moving piece
        screen.blit(piece_img, (x, y))
        pygame.display.flip()
```

### 10.2 Bonus: sound effects

Play a different sound for each kind of move.

| Event | Sound idea | How to detect it (python-chess) |
|---|---|---|
| Normal move | Soft wooden "tok" | Default case |
| Capture | Sharper "clack" | `board.is_capture(move)` **before** pushing |
| Castling | Double "tok-tok" | `board.is_castling(move)` before pushing |
| Promotion | Short rising "ding" | `move.promotion is not None` |
| Check | Alert "ping" | `board.is_check()` **after** pushing |
| Checkmate | Gong / victory fanfare | `board.is_checkmate()` after pushing |
| Draw / stalemate | Calm low tone | `board.is_game_over()` and not checkmate |
| Illegal move | Quiet "bonk" | Move not in `board.legal_moves` |
| Game start | Short jingle | When a new game begins |

**Priority rule:** only play **one** sound per move, the most important one:
checkmate > check > promotion > capture > castling > normal move.

```python
import pygame
import chess

pygame.mixer.init()
SOUNDS = {name: pygame.mixer.Sound(f"ui/assets/sounds/{name}.wav")
          for name in ["move", "capture", "castle", "promote",
                       "check", "checkmate", "draw", "illegal", "start"]}

def play_move(board: chess.Board, move: chess.Move) -> None:
    """Push the move and play the right sound."""
    is_capture = board.is_capture(move)      # must check BEFORE push
    is_castle = board.is_castling(move)
    is_promo = move.promotion is not None

    board.push(move)

    if board.is_checkmate():
        sound = "checkmate"
    elif board.is_game_over():
        sound = "draw"
    elif board.is_check():
        sound = "check"
    elif is_promo:
        sound = "promote"
    elif is_capture:
        sound = "capture"
    elif is_castle:
        sound = "castle"
    else:
        sound = "move"
    SOUNDS[sound].play()
```

Use the same `play_move()` for the player's moves **and** the AI's moves, so both make sounds.

**Where to get sounds (free and legal):**
- **Kenney.nl** – "Interface Sounds", "Impact Sounds" packs, licence **CC0** (free for any use, no credit needed).
- **Freesound.org** – many wood/click/gong sounds; check each file's licence (CC0 or CC-BY with credit).
- **Make your own** – record tapping a real chess piece on a table with your phone, then cut it in Audacity.
- **Generate with code** – simple tones with numpy, no files needed:

```python
import numpy as np, pygame

def make_tone(freq=880, ms=120, volume=0.4, sr=44100):
    t = np.linspace(0, ms / 1000, int(sr * ms / 1000), False)
    wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 25)   # fast fade-out
    audio = (wave * volume * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([audio, audio]))

check_sound = make_tone(1200, 150)
```

(Call `pygame.mixer.init(44100, -16, 2)` first so the format matches.)

**Tips:**
- Use short `.wav` or `.ogg` files (under 0.5 s), so sounds do not overlap.
- Add a **mute button** and a volume slider.
- Turn sounds **off in the benchmark scripts** – thousands of games with sound would be noisy and slow.
- Credit any CC-BY sounds in the report's appendix.

---

## 11. Benchmark module

Scripts that run **without the screen** and save results to CSV/PGN.

| Script | What it does |
|---|---|
| `run_nodes.py` | For each test position and each algorithm, search at depth 1–4 and log nodes and time |
| `run_tournament.py` | Play games between two engines from a list of openings, both colours, with a node budget per move and adjudication (Section 12); end games with `board.is_game_over(claim_draw=True)`; save PGN + results |
| `run_puzzles.py` | Give each level the WAC puzzles and check if it finds the best move |
| `analyze.py` | Read the CSV files and make tables and charts (matplotlib) |

**Elo difference** from a match score `s` (wins + 0.5 × draws, divided by games):

```
Elo difference = −400 × log10(1/s − 1)
```

Report a **95% confidence interval** too (e.g. with a simple bootstrap or the standard error of the score). With few games, the error range is large.

The formula fails when `s` is 0 or 1 (for example, Level 4 will probably score 100% against Level 1). Use it only for neighbouring levels, or rate the whole round-robin at once with **Ordo** or **BayesElo**, which handle this.

**Reading WAC puzzles with python-chess:**

```python
board = chess.Board()
ops = board.set_epd(line)        # returns {"bm": [Move...], "id": "WAC.001"}
best_moves = ops["bm"]
move, _ = engine.search(board, node_limit=BUDGET)   # or time_limit=2.0 on one machine
solved = move in best_moves
```

**Stockfish as a reference (optional):**

```python
import chess.engine
sf = chess.engine.SimpleEngine.popen_uci("stockfish")
sf.configure({"Skill Level": 0})            # or UCI_LimitStrength + UCI_Elo
result = sf.play(board, chess.engine.Limit(time=0.1))
```

Stockfish's lowest `UCI_Elo` is 1320 (Skill Level 0 is its weakest setting), so even weakened it is only a useful reference for Levels 3–4.

---

## 12. Experiments

| # | Experiment | Setup | Metrics | Purpose |
|---|---|---|---|---|
| 1 | **Correctness** | Minimax vs alpha-beta on 50 positions, same depth (1–4), same evaluation | Same score? (must be 100%; the move may differ when moves tie) | Prove alpha-beta is correct |
| 2 | **Search efficiency** | Same evaluation, depth 1–4: minimax / alpha-beta (no ordering) / + ordering / + TT | Nodes, time, effective branching factor b* | Show how much each technique saves |
| 3 | **Evaluation ablation** | Same search (Level 3, same node budget): material vs Simplified vs hand-made tapered vs PeSTO | Wins / draws / losses | Separate the effect of evaluation from search |
| 4 | **Playing strength** | Round-robin between levels, 20–25 openings × 2 colours, node budget per move; optional vs weak Stockfish (Levels 3–4 only) | W/D/L, Elo difference ± 95% CI for neighbouring levels, Ordo/BayesElo ratings, average depth | Overall ranking |
| 5 | **Tactics** | WAC.001–050, node budget equal to about 2 s (more if too hard) | % solved | Show tactical improvement per level |
| 6 | **Level 4 ablation** | Level 3 → + quiescence → + TT → + PeSTO (= Level 4); each version plays Level 3 (openings × 2 colours) and solves the WAC puzzles | Score vs Level 3, % solved, average depth | Find which Level 4 technique causes the jump |

### Why different openings?

Our engines are **deterministic**: the same position always gives the same move (Level 1 too, when its random tie-break uses a fixed seed). If Level 2 plays Level 3 from the start position 25 times, we get **the same game 25 times**. Starting from different openings (and swapping colours) gives real, different games.

### Node budgets instead of seconds

For experiments, limit each move by a **node budget** (number of positions searched), not by seconds. Choose it once so each level searches about 2 s on one reference laptop (pilot: 26,000 nodes for Level 3 and 40,000 for Level 4, counting quiescence nodes). Then:
- results are the same on all five laptops,
- games can run in parallel without changing the results,
- every game can be replayed exactly (the pilot replayed all 9 drawn games with identical results).

Time-based depth is noisy: in the pilot, the same code on the same laptop reached depth 3 instead of 4 in 3 of 10 positions after the laptop had been busy. Keep seconds for the UI.

### Adjudication and running time

To save time, end a test game early when the result is clear. A side that is at least 6 pawns (600 centipawns of material) ahead for 6 half-moves in a row wins. At 160 half-moves, the side at least 3 pawns ahead wins; otherwise it is a draw. With this rule, the pilot's 40 games took 11 minutes on 8 parallel processes. By the same estimate, Experiment 4 (about 300 games) needs roughly 10 hours on one core, so run games in parallel.

### Effective branching factor (slide 31)

```
N + 1 = 1 + b* + (b*)² + ... + (b*)^d
```

Here N is the number of nodes searched and d the depth. Solve for b* numerically. A smaller b* means a more efficient search. Plot b* for minimax, alpha-beta and alpha-beta + ordering.

### Expected charts

1. **Nodes vs depth** (log scale): minimax / alpha-beta / + ordering / + TT
2. **Depth reached in 2 s** for each level
3. **Puzzle solve rate** per level (bar chart)
4. **Elo ranking** with error bars
5. **Level 4 ablation**: score vs Level 3 and % solved for each added technique

---

## 13. Data and external resources

**No training data is needed.** Nothing is trained. All resources are small and free:

| Resource | Use | Where |
|---|---|---|
| python-chess | Rules, move generation, FEN, PGN, EPD, Zobrist hash | `pip install chess` |
| Simplified Evaluation tables | Levels 2–3 evaluation | Chess Programming Wiki |
| PeSTO tables | Level 4 evaluation | Chess Programming Wiki |
| WAC (Win At Chess) | 300 tactical puzzles; we use 50 | Single EPD text file, widely available |
| Opening positions | Start positions for AI-vs-AI games | Write by hand or take from an opening list |
| Stockfish (optional) | External reference opponent for Levels 3–4 (lowest `UCI_Elo` is 1320) | stockfishchess.org |
| Ordo or BayesElo (optional) | Elo ratings from a whole round-robin | github.com/michiguel/Ordo, remi-coulom.fr/Bayesian-Elo |
| Pygame / Flask | Interface | `pip install pygame` / `pip install flask` |
| matplotlib, pandas | Charts and tables | `pip install matplotlib pandas` |

---

## 14. Project structure (code)

```
chess-ai/
├── README.md
├── requirements.txt
├── engine/
│   ├── __init__.py
│   ├── interface.py        # search() signature, stats dict, timer
│   ├── greedy.py           # Level 1
│   ├── minimax.py          # Level 2
│   ├── alphabeta.py        # Level 3 (ordering + iterative deepening)
│   ├── master.py           # Level 4 (TT + quiescence)
│   ├── ordering.py         # MVV-LVA, move scoring
│   ├── tt.py               # transposition table
│   └── evaluation/
│       ├── material.py
│       ├── simplified.py   # Simplified Evaluation Function
│       ├── tapered.py      # hand-made tapered eval (strict no-ML option)
│       └── pesto.py        # PeSTO tables + tapered eval
├── ui/
│   ├── app.py              # Pygame (or web) app
│   ├── sounds.py           # play_move() + sound loading
│   ├── effects.py          # animation, particles, confetti
│   └── assets/
│       ├── pieces/         # custom piece images (PNG)
│       └── sounds/         # move, capture, check, checkmate ... (.wav/.ogg)
├── benchmark/
│   ├── run_nodes.py
│   ├── run_tournament.py
│   ├── run_puzzles.py
│   └── analyze.py
├── data/
│   ├── wac.epd
│   └── openings.txt
├── results/                # CSV, PGN
├── charts/                 # PNG charts
└── tests/
    ├── test_perft.py
    ├── test_minimax_vs_alphabeta.py
    ├── test_evaluation.py
    ├── test_search_board.py  # board unchanged after search, repetition = draw
    └── test_tt.py
```

---

## 15. Team roles

| Member | Role | Main tasks |
|---|---|---|
| 1 | Game engine & infrastructure | python-chess integration, shared `search()` interface, iterative deepening, time and node limits, opening set, unit tests |
| 2 | Search lead | Greedy, minimax, alpha-beta, move ordering |
| 3 | Search optimization | Zobrist hashing (via python-chess), transposition table, quiescence search |
| 4 | Evaluation | Material, Simplified Evaluation, PeSTO tables, tapered eval (hand-made and PeSTO), orientation tests, optional extra terms |
| 5 | Interface & benchmarks | Pygame/web UI, benchmark scripts (node budgets, adjudication, parallel games), logging, charts; bonus: themes, animations, sound effects |

**Everyone:** writes their part of the report and checks one other member's code.

**Rule:** log node counts and time **from day one**. Adding logging later is painful.

---

## 16. Timeline

| Week | Goals | Done when |
|---|---|---|
| **1** | Set up repo, python-chess, shared interface, basic UI, Level 1, material eval, benchmark skeleton | You can play against Level 1 on screen |
| **2** | Minimax, alpha-beta, move ordering, iterative deepening, Simplified eval. **Run Experiment 1** | Alpha-beta = minimax on all test positions |
| **3** | Transposition table, quiescence, PeSTO. **Run Experiments 2–3** | Level 4 works and beats Level 3 in quick tests |
| **3 (bonus)** | Member 5 adds themes, move animation, sounds while others finish Level 4 | Every move type plays its own sound |
| **4** | **Code freeze mid-week.** Run Experiments 4–6 (they take hours in Python; run games in parallel). Charts, report, slides | Report and presentation ready |

---

## 17. Testing and debugging

Search bugs do not crash the program. The AI just plays a bit worse, so you must test on purpose.

| Test | How | What it catches |
|---|---|---|
| **Perft** | Count all positions at depth 1–4 from known positions and compare with published numbers (start position: 20, 400, 8902, 197281) | Move generation errors (python-chess should pass; this checks your setup) |
| **Minimax = alpha-beta** | Same depth, same eval, many positions → scores must be equal | Pruning bugs |
| **Symmetry** | Evaluate a position and its colour-flipped mirror → scores must be opposite | Colour-handling bugs (but not tables that are upside down for both colours) |
| **Orientation** | White pawn on e7 must score more than on e2; white king on g1 more than on g8 (middlegame) | Upside-down PST tables (the knight and symmetry tests miss this) |
| **Mate-in-1 / mate-in-2** | Simple positions with a known mate | Mate scoring bugs |
| **Free piece** | Position where a queen can be taken for free → AI must take it | Evaluation sign errors |
| **TT on vs off** | Same depth with and without TT → same best move (in most positions) and fewer nodes; a mate in 2 must still be reported as mate in 2 | TT flag and mate-score bugs |
| **Hanging piece after capture** | Position where a capture loses the piece back → Level 4 should avoid it | Quiescence bugs |
| **Board unchanged** | Compare `board.fen()` and `len(board.move_stack)` before and after `search()`, also with a tiny time limit | Search moves left on the game board after a timeout |
| **Repetition** | Position where the side that is ahead could repeat moves → the search must score the repeat as 0 and play on | Missing repetition check |

**Debugging order:** build one technique at a time, test it, then add the next. Never add the TT before alpha-beta is verified.

---

## 18. Risks and how to handle them

| Risk | Effect | What to do |
|---|---|---|
| Python is slow | Low depth (pilot: 4 half-moves in middlegames in 2 s) | Avoid the slow calls in 8.9; use time or node limits, not promised depths; accept it as a limitation |
| TT bugs | Wrong moves, hard to find | Test TT on vs off; drop TT if not working by end of week 3 |
| Tournaments take too long | No time for report | Node budgets + parallel games + adjudication (pilot: 40 games in 11 min on 8 processes); start Experiment 4 early in week 4 |
| Identical games | Meaningless statistics | Different openings + colour swap |
| Levels too close to separate | Unclear ranking | Pilot: each level beat the one below (84–94%); re-check after changes; more games, or bigger budgets |
| Puzzles too hard | Very low solve rates | More time per puzzle, or use an easier subset |
| Team members blocked by each other | Delays | Shared interface from week 1; each part testable alone |
| Results differ between laptops | Experiments not comparable | Node budgets instead of seconds (Section 12) |
| Search changes the game board | Corrupted games after a timeout | Search on `board.copy()` (8.5); "board unchanged" test (Section 17) |

---

## 19. Expected results

1. **A working chess app** with four levels that are clearly different in strength.
2. **Alpha-beta returns the same score as minimax but checks far fewer positions** (the chosen move can differ when moves tie). The saving grows with depth; move ordering and the TT reduce it further.
3. **Deeper search in the same time:** with 2 s per move, Level 3 searches deeper than Level 2's fixed 3 half-moves (pilot: 4 in middlegames, 5 in endgames). Level 4 does not have to search deeper than Level 3 (quiescence uses about half its time; in the pilot their depths were equal), but its search is more accurate.
4. **Clear ranking:** Level 4 > Level 3 > Level 2 > Level 1 in games, reported with Elo and error ranges.
5. **Better tactics:** WAC solve rate goes up with each level; the biggest jump is expected when quiescence search is added (Experiment 6 checks this).
6. **Evaluation matters:** the tapered evaluations (hand-made and PeSTO) should beat the Simplified evaluation with the same search, but probably by less than the gain from deeper search.
7. **Honest limitations:**
   - Python is much slower than C++ engines, so depth is limited.
   - The horizon effect remains for quiet (non-capture) threats.
   - The evaluation does not understand long-term plans.

---

## 20. Related work

| Work | What it is | Link to our project |
|---|---|---|
| Shannon (1950), *Programming a Computer for Playing Chess* | First paper on chess programs: minimax + evaluation function | Same basic idea |
| Schaeffer (1989), *The History Heuristic and Alpha-Beta Search Enhancements in Practice* | Measured alpha-beta enhancements (e.g. transposition table, killer and history heuristics) alone and combined | Model for our Experiments 2 and 6 |
| **Deep Blue** (IBM, 1997) | Beat world champion Kasparov with alpha-beta search and a hand-written evaluation on special hardware | Same family of methods |
| **Stockfish** | Strongest open-source engine; still uses alpha-beta, iterative deepening, TT, quiescence. Evaluation is now a small neural network (NNUE) | Our Levels 3–4 are a small version of its search |
| **Sunfish** | Very small Python engine with alpha-beta-style search and PSTs | Close to our Levels 3–4; good to read |
| **AlphaZero / Leela Chess Zero** | Neural network + Monte Carlo Tree Search (MCTS), learned by self-play | A different approach (learning), not used here |
| **Monte Carlo Tree Search (pure)** | Search with random playouts, no learning; very strong in Go | Weak in chess because of shallow traps (Ramanujan et al., 2010), one reason we use alpha-beta |
| Russell & Norvig, *AIMA*, adversarial search chapter | Textbook source for minimax, α-β, cut-off, evaluation functions | Theory basis, same as course slides |

**What our project adds:** a step-by-step, controlled comparison showing **how much each classical technique helps**, with fair tests (different openings, both colours, node budgets, confidence intervals).

---

## 21. Future work

- **MCTS player:** compare pure Monte Carlo Tree Search (random playouts, no learning) with alpha-beta.
- **More search techniques:** killer moves, history heuristic, delta pruning in quiescence, null-move pruning, aspiration windows.
- **Finer difficulty levels for people:** copy Stockfish's handicap: stop at depth 1 + level and pick among the 4 best moves with a random term that grows at lower levels (pure search, no learning).
- **Opening book and endgame tablebases.**
- **Faster language:** rewrite the search core in C++ or Rust, or use PyPy.

---

## 22. Report outline

1. **Introduction** – chess as an AI problem, goals, research questions
2. **Background** – game formulation, minimax, α-β (cite course slides 63–81), heuristic evaluation (link to h(n) in A*)
3. **Related work** – Shannon, Schaeffer, Deep Blue, Stockfish, Sunfish; why not MCTS
4. **System design** – architecture diagram, shared interface, four levels
5. **Methods** – each algorithm with pseudocode; evaluation functions (Simplified, PeSTO, tapered)
6. **Experimental setup** – positions, openings, time limits, hardware, number of games
7. **Results** – Experiments 1–6 with tables and charts
8. **Discussion** – what helped most, why (e.g. quiescence and tactics), limitations
9. **Conclusion and future work**
10. **References**
11. **Appendix** – team roles and contributions, how to run the code

---

## 23. Glossary

| Term | Meaning |
|---|---|
| **Half-move (ply)** | One move by one player. A full "move" = White's move + Black's move = 2 half-moves |
| **Branching factor (b)** | Number of possible moves at each step (≈ 35 in chess) |
| **Depth (m or d)** | How many half-moves ahead the search looks |
| **Game tree** | Tree of all possible positions: root = current position, branches = moves |
| **Node** | One position in the game tree |
| **Leaf** | A node where the search stops and the evaluation is used |
| **MAX / MIN** | The player who wants a high score (White) / low score (Black) |
| **Utility function** | The true value of a finished game (win / loss / draw) |
| **Heuristic evaluation** | A quick estimate of how good a non-finished position is |
| **Centipawn** | 1/100 of a pawn; the unit of the evaluation score |
| **α (alpha)** | Best score MAX is already sure of |
| **β (beta)** | Best score MIN is already sure of |
| **Pruning / cut-off** | Skipping a branch that cannot change the result |
| **Move ordering** | Searching likely-good moves first so pruning works better |
| **MVV-LVA** | Most Valuable Victim – Least Valuable Attacker; a rule to order captures |
| **Iterative deepening** | Search depth 1, 2, 3, ... until time runs out |
| **Transposition** | The same position reached by a different move order |
| **Transposition table (TT)** | A dictionary that stores results for positions already searched |
| **Zobrist hashing** | A fast way to turn a position into a number (the TT key) |
| **Horizon effect** | Bad decisions because something important happens just after the search depth |
| **Quiescence search** | Extra search of captures at the leaves until the position is quiet |
| **Stand pat** | In quiescence: the score if the side to move makes no capture |
| **PST (piece-square table)** | 64 numbers per piece type: bonus or penalty for each square |
| **PeSTO** | "Piece-Square Tables Only": tuned middlegame + endgame tables |
| **Tapered evaluation** | Blending middlegame and endgame scores by game phase |
| **FEN** | Text format for one chess position |
| **PGN** | Text format for a full chess game |
| **EPD** | Text format for test positions with extra info (e.g. best move) |
| **UCI** | Move format like `e2e4`; also the protocol engines like Stockfish use |
| **Perft** | Counting all positions to a depth, to test move generation |
| **Elo** | Rating system; the difference shows expected score between two players |
| **Effective branching factor (b\*)** | The branching factor a uniform tree would need to have the same number of nodes; lower = more efficient |
| **Threefold repetition** | The same position three times → draw (can be claimed); inside the search, one repeat is already scored as a draw |
| **Node budget** | A fixed number of positions the search may visit per move, used instead of a time limit in experiments |
| **Adjudication** | Ending a test game early when the result is already clear |
| **Ablation** | Adding or removing one technique at a time to measure its effect |
| **Delta pruning** | In quiescence, skipping captures that cannot raise alpha even if they win the piece |

---

## 24. References

**Course and textbook**

1. Course slides: *Chapter 4 – Search II*, IT3160E Introduction to AI, HUST (slides 8–36, 63–81).
2. Course Lecture Notes (Vietnamese), sections 3.4 (A*, heuristics) and 3.6 (Minimax, α-β pruning).
3. S. Russell and P. Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed., Pearson, 2020, Chapter 5 "Adversarial Search and Games" (5.2 minimax and α-β; 5.3 evaluation, cut-off, quiescence, horizon effect).

**Search techniques (one paper per technique)**

4. C. E. Shannon, "Programming a Computer for Playing Chess," *Philosophical Magazine*, 41(314), 1950. Minimax + evaluation function (Level 2).
5. D. E. Knuth and R. W. Moore, "An Analysis of Alpha-Beta Pruning," *Artificial Intelligence*, 6(4):293–326, 1975. Best case O(b^(m/2)) (Level 3).
6. D. Slate and L. Atkin, "CHESS 4.5 – The Northwestern University Chess Program," in P. W. Frey (ed.), *Chess Skill in Man and Machine*, Springer, 1977. First documented iterative deepening (Level 3).
7. J. Schaeffer, "The History Heuristic and Alpha-Beta Search Enhancements in Practice," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 11(11):1203–1212, 1989. Model for Experiments 2 and 6.
8. S. Akl and M. Newborn, "The Principal Continuation and the Killer Heuristic," *Proc. ACM Annual Conference*, pp. 466–473, 1977. Killer moves (future work).
9. A. L. Zobrist, "A New Hashing Method with Application for Game Playing," Technical Report 88, University of Wisconsin, 1970 (reprinted in *ICCA Journal*, 13(2), 1990). TT keys (Level 4).
10. D. F. Beal, "A Generalized Quiescence Search Algorithm," *Artificial Intelligence*, 43(1):85–98, 1990. Quiescence search (Level 4).
11. M. Campbell, A. J. Hoane Jr., F. Hsu, "Deep Blue," *Artificial Intelligence*, 134(1–2):57–83, 2002.
12. R. Ramanujan, A. Sabharwal, B. Selman, "On Adversarial Search Spaces and Sampling-Based Planning," *Proc. ICAPS*, pp. 242–245, 2010. Why MCTS struggles in chess. https://ojs.aaai.org/index.php/ICAPS/article/view/13437

**Evaluation**

13. Chess Programming Wiki – Alpha-Beta, Move Ordering, MVV-LVA, Iterative Deepening, Transposition Table, Zobrist Hashing, Quiescence Search, Simplified Evaluation Function, PeSTO's Evaluation Function, Texel's Tuning Method, Perft Results. https://www.chessprogramming.org

**Difficulty levels, testing and ratings**

14. Stockfish source code, `src/search.h` and `src/search.cpp` (`Skill`: strength handicap; `UCI_Elo` range 1320–3190). https://github.com/official-stockfish/Stockfish
15. A. E. Elo, *The Rating of Chessplayers, Past and Present*, Arco, 1978.
16. Ordo (M. A. Ballicora), rating tool for engine tournaments. https://github.com/michiguel/Ordo
17. BayesElo (R. Coulom), Bayesian Elo rating tool. https://www.remi-coulom.fr/Bayesian-Elo/
18. Win At Chess (WAC) test suite (F. Reinfeld, *Win at Chess*, 1958; EPD version widely used for engine testing).

**Tools and assets**

19. python-chess documentation. https://python-chess.readthedocs.io
20. Stockfish. https://stockfishchess.org
21. Sunfish (Thomas Ahle). https://github.com/thomasahle/sunfish
22. Pygame documentation (graphics and `pygame.mixer` sound). https://www.pygame.org/docs
23. Kenney game assets (CC0 sounds). https://kenney.nl/assets
