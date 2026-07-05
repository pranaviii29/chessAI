import pieces
from move import Move


class Board:

    WIDTH  = 8
    HEIGHT = 8

    def __init__(self, grid, king_moved,ep_target=None):
        self.grid       = grid          # grid[x][y] = Piece or 0
        self.king_moved = king_moved    # {WHITE: bool, BLACK: bool}
        self.ep_target  = ep_target


    # Creates a deep copy of the given board.
    @classmethod
    def clone(cls, other):
        grid = [[0] * Board.HEIGHT for _ in range(Board.WIDTH)]
        for x in range(Board.WIDTH):
            for y in range(Board.HEIGHT):
                piece = other.grid[x][y]
                if piece != 0:
                    grid[x][y] = piece.clone()
        return cls(grid, dict(other.king_moved),other.ep_target)

    # Creates a new board with pieces in the starting position.
    @classmethod
    def new(cls):
        grid = [[0] * Board.HEIGHT for _ in range(Board.WIDTH)]

        # Pawns.
        for x in range(Board.WIDTH):
            grid[x][1] = pieces.Pawn(x, 1, pieces.Piece.BLACK)
            grid[x][6] = pieces.Pawn(x, 6, pieces.Piece.WHITE)

        # Rooks.
        grid[0][0] = pieces.Rook(0, 0, pieces.Piece.BLACK)
        grid[7][0] = pieces.Rook(7, 0, pieces.Piece.BLACK)
        grid[0][7] = pieces.Rook(0, 7, pieces.Piece.WHITE)
        grid[7][7] = pieces.Rook(7, 7, pieces.Piece.WHITE)

        # Knights.
        grid[1][0] = pieces.Knight(1, 0, pieces.Piece.BLACK)
        grid[6][0] = pieces.Knight(6, 0, pieces.Piece.BLACK)
        grid[1][7] = pieces.Knight(1, 7, pieces.Piece.WHITE)
        grid[6][7] = pieces.Knight(6, 7, pieces.Piece.WHITE)

        # Bishops.
        grid[2][0] = pieces.Bishop(2, 0, pieces.Piece.BLACK)
        grid[5][0] = pieces.Bishop(5, 0, pieces.Piece.BLACK)
        grid[2][7] = pieces.Bishop(2, 7, pieces.Piece.WHITE)
        grid[5][7] = pieces.Bishop(5, 7, pieces.Piece.WHITE)

        # Queens.
        grid[3][0] = pieces.Queen(3, 0, pieces.Piece.BLACK)
        grid[3][7] = pieces.Queen(3, 7, pieces.Piece.WHITE)

        # Kings.
        grid[4][0] = pieces.King(4, 0, pieces.Piece.BLACK)
        grid[4][7] = pieces.King(4, 7, pieces.Piece.WHITE)

        return cls(grid, {pieces.Piece.WHITE: False, pieces.Piece.BLACK: False})

    # Returns the piece at (x, y), or 0 if empty or out of bounds.
    def get_piece(self, x, y):
        if not self.in_bounds(x, y):
            return 0
        return self.grid[x][y]

    def in_bounds(self, x, y):
        return 0 <= x < Board.WIDTH and 0 <= y < Board.HEIGHT

    # Returns all possible moves for the given color.
    def get_possible_moves(self, color):
        moves = []
        for x in range(Board.WIDTH):
            for y in range(Board.HEIGHT):
                piece = self.grid[x][y]
                if piece != 0 and piece.color == color:
                    moves += piece.get_possible_moves(self)
        return moves

    # Applies the move to the board.
    def perform_move(self, move):
        piece = self.grid[move.xfrom][move.yfrom]
        # En passant: remove the captured pawn
        if move.is_en_passant and move.ep_capture_pos:
            cx, cy = move.ep_capture_pos
            self.grid[cx][cy] = 0
        self.move_piece(piece, move.xto, move.yto)

        # Update en passant target for next move
        if piece.piece_type == pieces.Pawn.PIECE_TYPE and abs(move.yto - move.yfrom) == 2:
            direction = 1 if piece.color == pieces.Piece.BLACK else -1
            self.ep_target = (piece.x, piece.y - direction)
        else:
            self.ep_target = None
        # Promote pawn — use player's chosen piece or default to Queen
        if piece.piece_type == pieces.Pawn.PIECE_TYPE:
            if piece.y == 0 or piece.y == Board.HEIGHT - 1:
                promo_class = move.promotion_piece if move.promotion_piece else pieces.Queen
                self.grid[piece.x][piece.y] = promo_class(piece.x, piece.y, piece.color)

        # Handle king moves and castling.
        if piece.piece_type == pieces.King.PIECE_TYPE:
            self.king_moved[piece.color] = True

            # Kingside castling: move the rook from x+1 to x-1 relative to king's new pos.
            if move.xto - move.xfrom == 2:
                rook = self.grid[piece.x + 1][piece.y]
                self.move_piece(rook, piece.x - 1, piece.y)

            # Queenside castling: move the rook from x-2 to x+1 relative to king's new pos.
            if move.xto - move.xfrom == -2:
                rook = self.grid[piece.x - 2][piece.y]
                self.move_piece(rook, piece.x + 1, piece.y)

    # Moves a piece to (xto, yto), updating the piece's internal coordinates.
    def move_piece(self, piece, xto, yto):
        self.grid[piece.x][piece.y] = 0
        piece.x = xto
        piece.y = yto
        self.grid[xto][yto] = piece

    # Returns True if the given color's king is in check.
    def is_in_check(self, color):
        opponent = pieces.Piece.BLACK if color == pieces.Piece.WHITE else pieces.Piece.WHITE
        for move in self.get_possible_moves(opponent):
            copy = Board.clone(self)
            copy.perform_move(move)
            # If the king is gone after the move, it was captured = check.
            king_found = any(
                copy.grid[x][y] != 0 and
                copy.grid[x][y].color == color and
                copy.grid[x][y].piece_type == pieces.King.PIECE_TYPE
                for x in range(Board.WIDTH)
                for y in range(Board.HEIGHT)
            )
            if not king_found:
                return True
        return False

    # Prints the board to the terminal.
    def to_string(self):
        output  = '   A  B  C  D  E  F  G  H\n'
        for y in range(Board.HEIGHT):
            output += str(8 - y) + ' | '
            for x in range(Board.WIDTH):
                piece = self.grid[x][y]
                output += piece.to_string() if piece != 0 else '.. '
            output += '\n'
        return output
