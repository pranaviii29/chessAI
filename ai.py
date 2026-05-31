import board
import pieces


class Heuristics:

    # Piece-square tables: bonus points for piece position on the board.
    # Indexed as [x][y] from White's perspective.

    PAWN_TABLE = [
        [ 0,  5,  5,  0,  5, 10, 50,  0],
        [ 0, 10, -5,  0,  5, 10, 50,  0],
        [ 0, 10,-10,  0, 10, 20, 50,  0],
        [ 0,-20,  0, 20, 25, 30, 50,  0],
        [ 0,-20,  0, 20, 25, 30, 50,  0],
        [ 0, 10,-10,  0, 10, 20, 50,  0],
        [ 0, 10, -5,  0,  5, 10, 50,  0],
        [ 0,  5,  5,  0,  5, 10, 50,  0],
    ]

    KNIGHT_TABLE = [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ]

    BISHOP_TABLE = [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ]

    ROOK_TABLE = [
        [ 0, -5, -5, -5, -5, -5,  5,  0],
        [ 0,  0,  0,  0,  0,  0, 10,  0],
        [ 0,  0,  0,  0,  0,  0, 10,  0],
        [ 5,  0,  0,  0,  0,  0, 10,  0],
        [ 5,  0,  0,  0,  0,  0, 10,  0],
        [ 0,  0,  0,  0,  0,  0, 10,  0],
        [ 0,  0,  0,  0,  0,  0, 10,  5],
        [ 0, -5, -5, -5, -5, -5,  5,  0],
    ]

    QUEEN_TABLE = [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ]

    # Returns a score for the board. Positive = White is better. Negative = Black is better.
    @staticmethod
    def evaluate(chessboard):
        score = 0
        score += Heuristics.get_material_score(chessboard)
        score += Heuristics.get_position_score(chessboard, pieces.Pawn.PIECE_TYPE,   Heuristics.PAWN_TABLE)
        score += Heuristics.get_position_score(chessboard, pieces.Knight.PIECE_TYPE, Heuristics.KNIGHT_TABLE)
        score += Heuristics.get_position_score(chessboard, pieces.Bishop.PIECE_TYPE, Heuristics.BISHOP_TABLE)
        score += Heuristics.get_position_score(chessboard, pieces.Rook.PIECE_TYPE,   Heuristics.ROOK_TABLE)
        score += Heuristics.get_position_score(chessboard, pieces.Queen.PIECE_TYPE,  Heuristics.QUEEN_TABLE)
        return score

    # Returns the total material score (White minus Black).
    @staticmethod
    def get_material_score(chessboard):
        white = 0
        black = 0
        for x in range(board.Board.WIDTH):
            for y in range(board.Board.HEIGHT):
                piece = chessboard.grid[x][y]
                if piece != 0:
                    if piece.color == pieces.Piece.WHITE:
                        white += piece.value
                    else:
                        black += piece.value
        return white - black

    # Returns the position score for one piece type using its table.
    @staticmethod
    def get_position_score(chessboard, piece_type, table):
        white = 0
        black = 0
        for x in range(board.Board.WIDTH):
            for y in range(board.Board.HEIGHT):
                piece = chessboard.grid[x][y]
                if piece != 0 and piece.piece_type == piece_type:
                    if piece.color == pieces.Piece.WHITE:
                        white += table[x][y]
                    else:
                        # Mirror the table vertically for Black.
                        black += table[x][7 - y]
        return white - black


class AI:

    INFINITE = 10_000_000

    # Returns the best move for Black using alpha-beta search.
    @staticmethod
    def get_best_move(chessboard, depth=3):
        best_move  = None
        best_score = AI.INFINITE

        for move in chessboard.get_possible_moves(pieces.Piece.BLACK):
            copy = board.Board.clone(chessboard)
            copy.perform_move(move)

            # Skip moves that leave own king in check.
            if copy.is_in_check(pieces.Piece.BLACK):
                continue

            score = AI.alphabeta(copy, depth - 1, -AI.INFINITE, AI.INFINITE, True)

            if score < best_score:
                best_score = score
                best_move  = move

        return best_move

    # Minimax algorithm with alpha-beta pruning.
    # maximizing=True means it is White's turn (White wants to maximise the score).
    @staticmethod
    def alphabeta(chessboard, depth, alpha, beta, maximizing):
        if depth == 0:
            return Heuristics.evaluate(chessboard)

        color = pieces.Piece.WHITE if maximizing else pieces.Piece.BLACK

        if maximizing:
            best = -AI.INFINITE
            for move in chessboard.get_possible_moves(color):
                copy = board.Board.clone(chessboard)
                copy.perform_move(move)
                if copy.is_in_check(color):
                    continue
                score = AI.alphabeta(copy, depth - 1, alpha, beta, False)
                best  = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break   # beta cutoff
            return best

        else:
            best = AI.INFINITE
            for move in chessboard.get_possible_moves(color):
                copy = board.Board.clone(chessboard)
                copy.perform_move(move)
                if copy.is_in_check(color):
                    continue
                score = AI.alphabeta(copy, depth - 1, alpha, beta, True)
                best  = min(best, score)
                beta  = min(beta, best)
                if beta <= alpha:
                    break   # alpha cutoff
            return best
