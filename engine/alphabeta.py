"""Level 3 (Hard): alpha-beta + iterative deepening (owner: Dominique).

Plan, Sections 8.3-8.5:
- alpha-beta pruning, written in negamax form (one function, score from the side to move);
- move ordering with MVV-LVA (engine/ordering.py);
- iterative deepening: depth 1, 2, 3, ... until the time or node limit; the best move
  of the last finished depth is searched first at the next depth.

Evaluation: Simplified (engine/evaluation/simplified.py). Until it exists, a material-only
fallback is used, so the engine already works and passes the tests.
"""
import time

import chess

from engine.ordering import order_moves
from game.interface import (INF, MATE, Limits, SearchTimeout, is_terminal,
                            new_stats)

try:
    from engine.evaluation.simplified import evaluate
except ImportError:                       # simplified.py not written yet
    _VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
               chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

    def evaluate(board):
        """Material only, centipawns from White's point of view (temporary)."""
        score = 0
        for piece in board.piece_map().values():
            value = _VALUES[piece.piece_type]
            score += value if piece.color == chess.WHITE else -value
        return score


def _negamax(board, depth, alpha, beta, ply, stats, limits, ordering=True):
    """Score of the position for the side to move."""
    stats["nodes"] += 1
    if limits is not None:
        limits.check(stats)               # raises SearchTimeout at the limit

    if is_terminal(board, ply):
        return -(MATE - ply) if board.is_checkmate() else 0
    if depth == 0:
        score = evaluate(board)
        return score if board.turn == chess.WHITE else -score

    moves = order_moves(board) if ordering else board.legal_moves
    best = -INF
    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, ply + 1, stats, limits, ordering)
        board.pop()
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break                         # cut-off: the opponent will avoid this line
    return best


def _search_root(board, depth, stats, limits, first_move=None, ordering=True):
    """Best move and its score (side to move) at a fixed depth."""
    stats["nodes"] += 1
    moves = order_moves(board, first_move) if ordering else list(board.legal_moves)
    best_move, best_score = moves[0], -INF
    alpha, beta = -INF, INF
    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, 1, stats, limits, ordering)
        board.pop()
        if score > best_score:
            best_move, best_score = move, score
        alpha = max(alpha, best_score)
    return best_move, best_score


def search_fixed_depth(board, depth, ordering=True):
    """One search at exactly this depth, no limits (for Experiments 1 and 2).

    Returns (move, score from White's point of view, stats).
    """
    start = time.perf_counter()
    stats = new_stats()
    board = board.copy()
    if board.is_game_over():
        return None, 0, stats
    move, score = _search_root(board, depth, stats, None, ordering=ordering)
    white_score = score if board.turn == chess.WHITE else -score
    stats.update(depth=depth, score=white_score, time=time.perf_counter() - start)
    return move, white_score, stats


def search(board, time_limit=None, depth=None, node_limit=None):
    """Shared engine interface (game/interface.py).

    time_limit: seconds per move (UI); node_limit: node budget (experiments);
    depth: maximum depth. With no limit at all, searches to depth 4.
    """
    start = time.perf_counter()
    stats = new_stats()
    board = board.copy()                  # an aborted search must not touch the game board
    if board.is_game_over():
        stats["time"] = time.perf_counter() - start
        return None, stats

    if time_limit is None and node_limit is None and depth is None:
        depth = 4
    white_to_move = board.turn == chess.WHITE   # read now: a timeout leaves moves pushed
    limits = Limits(time_limit, node_limit)
    best_move = order_moves(board)[0]     # always have a move, even if depth 1 is cut
    best_score = 0
    current = 1
    while depth is None or current <= depth:
        try:
            best_move, best_score = _search_root(board, current, stats, limits,
                                                 first_move=best_move)
            stats["depth"] = current
        except SearchTimeout:
            break                         # this depth did not finish: keep the last one
        if abs(best_score) >= MATE - 100:
            break                         # a forced mate was found: no need to go deeper
        if not limits.deeper_ok(stats):
            break
        current += 1

    stats["score"] = best_score if white_to_move else -best_score
    stats["time"] = time.perf_counter() - start
    return best_move, stats
