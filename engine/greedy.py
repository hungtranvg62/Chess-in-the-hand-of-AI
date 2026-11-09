# Owner: PLICHON Jacques (Level 1 - Easy)
import random
import time

import chess

from engine.evaluation.material import evaluate

INF = 10**9
MATE = 100_000


def search(board, time_limit=None, depth=None, node_limit=None, rng=None):
    start = time.perf_counter()
    rng = rng or random
    board = board.copy()
    sign = 1 if board.turn == chess.WHITE else -1
    best_score, best_moves, nodes = -INF, [], 0

    for move in list(board.legal_moves):
        board.push(move)
        nodes += 1
        if board.is_checkmate():
            score = MATE
        else:
            score = sign * evaluate(board)
        board.pop()

        if score > best_score:
            best_score, best_moves = score, [move]
        elif score == best_score:
            best_moves.append(move)

    if not best_moves:
        # Partie déjà terminée : aucun coup possible
        move, final_score = None, 0
    else:
        move, final_score = rng.choice(best_moves), sign * best_score

    stats = {
        "nodes": nodes, "depth": 1,
        "time": time.perf_counter() - start,
        "score": final_score,
        "tt_hits": 0, "qnodes": 0,
    }
    return move, stats