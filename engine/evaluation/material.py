"""Material count (owner: Matthias)."""
import chess

VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0,
}

def evaluate(board: chess.Board) -> int:
    """Matériel seulement. Positif = bon pour les Blancs."""
    score = 0
    for piece in board.piece_map().values():
        value = VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value
    return score