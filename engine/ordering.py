"""Move ordering: MVV-LVA (owner: Dominique).

Alpha-beta prunes more when good moves are searched first (plan, Section 8.4).
Order: TT / previous best move, then captures (MVV-LVA), then promotions, then quiet moves.
Checks are not tried first: board.gives_check() is too slow in Python.
"""
import chess

PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

FIRST_MOVE_BONUS = 100_000
CAPTURE_BONUS = 10_000
PROMOTION_BONUS = 9_000


def move_score(board, move, first_move=None):
    """Higher score = search this move earlier."""
    if move == first_move:
        return FIRST_MOVE_BONUS
    score = 0
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        victim_value = PIECE_VALUE[victim.piece_type] if victim else 1   # en passant
        attacker_value = PIECE_VALUE[board.piece_at(move.from_square).piece_type]
        score += CAPTURE_BONUS + 10 * victim_value - attacker_value
    if move.promotion:
        score += PROMOTION_BONUS + PIECE_VALUE[move.promotion]
    return score


def order_moves(board, first_move=None):
    """All legal moves, best candidates first. first_move is the TT or previous best move."""
    return sorted(board.legal_moves,
                  key=lambda m: move_score(board, m, first_move), reverse=True)
