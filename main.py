"""
Chess AI  —  Human (White) vs AI (Black)
Move format:  A2 A4   (column letter + row number, space, destination)
Commands:     quit
"""

import board
import pieces
from ai   import AI
from move import Move

COLS = 'ABCDEFGH'


def parse_move(text, chessboard):
    # Expects format like "A2 A4"
    parts = text.strip().upper().split()
    if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2:
        return None

    try:
        xfrom = COLS.index(parts[0][0])
        yfrom = 8 - int(parts[0][1])
        xto   = COLS.index(parts[1][0])
        yto   = 8 - int(parts[1][1])
    except (ValueError, IndexError):
        return None

    return Move(xfrom, yfrom, xto, yto)


def is_legal_move(move, chessboard, color):
    legal = chessboard.get_possible_moves(color)
    for legal_move in legal:
        if legal_move.equals(move):
            copy = board.Board.clone(chessboard)
            copy.perform_move(legal_move)
            if not copy.is_in_check(color):
                return True
    return False


def has_any_legal_move(chessboard, color):
    for move in chessboard.get_possible_moves(color):
        copy = board.Board.clone(chessboard)
        copy.perform_move(move)
        if not copy.is_in_check(color):
            return True
    return False


def main():
    chessboard = board.Board.new()

    print('\n  Chess AI:Human plays White, AI plays Black')
    print('  Move format: A2 A4')
    print('  Type quit to exit\n')

    while True:
        print(chessboard.to_string())

        #White's turn (human) 
        if not has_any_legal_move(chessboard, pieces.Piece.WHITE):
            if chessboard.is_in_check(pieces.Piece.WHITE):
                print('  Checkmate! Black wins.')
            else:
                print('  Stalemate — draw.')
            break

        if chessboard.is_in_check(pieces.Piece.WHITE):
            print('  You are in check!')

        while True:
            raw = input('  Your move: ').strip()

            if raw.lower() == 'quit':
                print('  Goodbye!')
                return

            move = parse_move(raw, chessboard)

            if move and is_legal_move(move, chessboard, pieces.Piece.WHITE):
                chessboard.perform_move(move)
                break
            else:
                print('  Illegal move. Example: E2 E4')

        #Black's turn (AI)
        if not has_any_legal_move(chessboard, pieces.Piece.BLACK):
            if chessboard.is_in_check(pieces.Piece.BLACK):
                print('  Checkmate! White wins.')
            else:
                print('  Stalemate — draw.')
            break

        print('  AI is thinking...')
        ai_move = AI.get_best_move(chessboard, depth=3)

        if ai_move is None:
            print('  AI has no moves. You win!')
            break

        print(f'  AI move: {ai_move.to_string()}\n')
        chessboard.perform_move(ai_move)


if __name__ == '__main__':
    main()
