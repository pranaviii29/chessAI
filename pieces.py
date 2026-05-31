from move import Move


class Piece:

    WHITE = 'W'
    BLACK = 'B'

    def __init__(self, x, y, color, piece_type, value):
        self.x          = x
        self.y          = y
        self.color      = color
        self.piece_type = piece_type
        self.value      = value

    # Returns a Move to (xto, yto) if it is valid, otherwise returns None.
    # A move is invalid if it is out of bounds or captures a friendly piece.
    def get_move(self, board, xto, yto):
        if not board.in_bounds(xto, yto):
            return None
        target = board.get_piece(xto, yto)
        if target != 0 and target.color == self.color:
            return None
        return Move(self.x, self.y, xto, yto)

    # Returns all diagonal moves. Used by Bishop and Queen.
    def get_diagonal_moves(self, board):
        moves = []
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            x, y = self.x + dx, self.y + dy
            while board.in_bounds(x, y):
                moves.append(Move(self.x, self.y, x, y))
                if board.get_piece(x, y) != 0:
                    break
                x += dx
                y += dy
        return self.filter_valid(moves, board)

    # Returns all straight moves (horizontal + vertical). Used by Rook and Queen.
    def get_straight_moves(self, board):
        moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            x, y = self.x + dx, self.y + dy
            while board.in_bounds(x, y):
                moves.append(Move(self.x, self.y, x, y))
                if board.get_piece(x, y) != 0:
                    break
                x += dx
                y += dy
        return self.filter_valid(moves, board)

    # Removes moves that land on a friendly piece.
    def filter_valid(self, moves, board):
        valid = []
        for move in moves:
            target = board.get_piece(move.xto, move.yto)
            if target == 0 or target.color != self.color:
                valid.append(move)
        return valid

    def to_string(self):
        return self.color + self.piece_type + ' '


#Individual piece classes

class Pawn(Piece):

    PIECE_TYPE = 'P'
    VALUE      = 100

    def __init__(self, x, y, color):
        super().__init__(x, y, color, Pawn.PIECE_TYPE, Pawn.VALUE)

    def is_starting_position(self):
        if self.color == Piece.BLACK:
            return self.y == 1
        else:
            return self.y == 6

    def get_possible_moves(self, board):
        moves     = []
        direction = 1 if self.color == Piece.BLACK else -1

        # One step forward (only if the square is empty).
        if board.get_piece(self.x, self.y + direction) == 0:
            moves.append(Move(self.x, self.y, self.x, self.y + direction))

            # Two steps forward from starting position.
            if self.is_starting_position() and board.get_piece(self.x, self.y + direction * 2) == 0:
                moves.append(Move(self.x, self.y, self.x, self.y + direction * 2))

        # Diagonal captures.
        for dx in [-1, 1]:
            target = board.get_piece(self.x + dx, self.y + direction)
            if target != 0 and target.color != self.color:
                moves.append(Move(self.x, self.y, self.x + dx, self.y + direction))

        return moves

    def clone(self):
        return Pawn(self.x, self.y, self.color)


class Knight(Piece):

    PIECE_TYPE = 'N'
    VALUE      = 320

    def __init__(self, x, y, color):
        super().__init__(x, y, color, Knight.PIECE_TYPE, Knight.VALUE)

    def get_possible_moves(self, board):
        moves = []
        for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            move = self.get_move(board, self.x + dx, self.y + dy)
            if move:
                moves.append(move)
        return moves

    def clone(self):
        return Knight(self.x, self.y, self.color)


class Bishop(Piece):

    PIECE_TYPE = 'B'
    VALUE      = 330

    def __init__(self, x, y, color):
        super().__init__(x, y, color, Bishop.PIECE_TYPE, Bishop.VALUE)

    def get_possible_moves(self, board):
        return self.get_diagonal_moves(board)

    def clone(self):
        return Bishop(self.x, self.y, self.color)


class Rook(Piece):

    PIECE_TYPE = 'R'
    VALUE      = 500

    def __init__(self, x, y, color):
        super().__init__(x, y, color, Rook.PIECE_TYPE, Rook.VALUE)

    def get_possible_moves(self, board):
        return self.get_straight_moves(board)

    def clone(self):
        return Rook(self.x, self.y, self.color)


class Queen(Piece):

    PIECE_TYPE = 'Q'
    VALUE      = 900

    def __init__(self, x, y, color):
        super().__init__(x, y, color, Queen.PIECE_TYPE, Queen.VALUE)

    def get_possible_moves(self, board):
        return self.get_diagonal_moves(board) + self.get_straight_moves(board)

    def clone(self):
        return Queen(self.x, self.y, self.color)


class King(Piece):

    PIECE_TYPE = 'K'
    VALUE      = 20000

    def __init__(self, x, y, color):
        super().__init__(x, y, color, King.PIECE_TYPE, King.VALUE)

    def get_possible_moves(self, board):
        moves = []
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            move = self.get_move(board, self.x + dx, self.y + dy)
            if move:
                moves.append(move)

        # Kingside castling.
        if not board.king_moved[self.color]:
            rook = board.get_piece(self.x + 3, self.y)
            if (rook != 0 and rook.piece_type == Rook.PIECE_TYPE and rook.color == self.color
                    and board.get_piece(self.x + 1, self.y) == 0
                    and board.get_piece(self.x + 2, self.y) == 0):
                moves.append(Move(self.x, self.y, self.x + 2, self.y))

        # Queenside castling.
        if not board.king_moved[self.color]:
            rook = board.get_piece(self.x - 4, self.y)
            if (rook != 0 and rook.piece_type == Rook.PIECE_TYPE and rook.color == self.color
                    and board.get_piece(self.x - 1, self.y) == 0
                    and board.get_piece(self.x - 2, self.y) == 0
                    and board.get_piece(self.x - 3, self.y) == 0):
                moves.append(Move(self.x, self.y, self.x - 2, self.y))

        return moves

    def clone(self):
        return King(self.x, self.y, self.color)
