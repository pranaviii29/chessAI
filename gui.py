"""
Controls:
  • Click a piece to select it  (green highlight)
  • Click a highlighted square  to move there  (yellow dots)
  • Click anywhere else         to deselect
  • Press U                     to undo your last move + AI reply
  • Press R                     to restart the game
  • Press Q / close window      to quit
"""

import sys
import threading
import pygame
import board as chessboard_module
import pieces as pieces_module
from ai   import AI
from move import Move

WINDOW_WIDTH  = 720
WINDOW_HEIGHT = 720
BOARD_SIZE    = 8
SQUARE_SIZE   = WINDOW_WIDTH // BOARD_SIZE   # 90 px

# Colors
COLOR_LIGHT      = (240, 217, 181)   # light square
COLOR_DARK       = (181, 136,  99)   # dark square
COLOR_SELECTED   = ( 20, 200,  80)   # selected piece square
COLOR_MOVE_DOT   = (100, 200, 100)   # legal move dot
COLOR_CAPTURE    = (220,  60,  60)   # capture highlight
COLOR_CHECK      = (230,  30,  30)   # king in check
COLOR_LAST_FROM  = (205, 210,  80)   # last move from-square tint
COLOR_LAST_TO    = (205, 210,  80)   # last move to-square tint
COLOR_TEXT_BG    = ( 40,  40,  40)
COLOR_TEXT       = (255, 255, 255)
COLOR_STATUS_WIN = ( 50, 200,  80)
COLOR_STATUS_AI  = (255, 200,   0)

# Unicode chess pieces  {(color, kind): unicode}
UNICODE = {
    (pieces_module.Piece.WHITE, pieces_module.King.PIECE_TYPE):   '♔',
    (pieces_module.Piece.WHITE, pieces_module.Queen.PIECE_TYPE):  '♕',
    (pieces_module.Piece.WHITE, pieces_module.Rook.PIECE_TYPE):   '♖',
    (pieces_module.Piece.WHITE, pieces_module.Bishop.PIECE_TYPE): '♗',
    (pieces_module.Piece.WHITE, pieces_module.Knight.PIECE_TYPE): '♘',
    (pieces_module.Piece.WHITE, pieces_module.Pawn.PIECE_TYPE):   '♙',
    (pieces_module.Piece.BLACK, pieces_module.King.PIECE_TYPE):   '♚',
    (pieces_module.Piece.BLACK, pieces_module.Queen.PIECE_TYPE):  '♛',
    (pieces_module.Piece.BLACK, pieces_module.Rook.PIECE_TYPE):   '♜',
    (pieces_module.Piece.BLACK, pieces_module.Bishop.PIECE_TYPE): '♝',
    (pieces_module.Piece.BLACK, pieces_module.Knight.PIECE_TYPE): '♞',
    (pieces_module.Piece.BLACK, pieces_module.Pawn.PIECE_TYPE):   '♟',
}


#Coordinate helpers

def board_to_pixel(x, y):
    """Board (x, y) → top-left pixel of that square."""
    px = x * SQUARE_SIZE
    py = (7 - y) * SQUARE_SIZE      # y=0 is rank 1 (bottom of screen)
    return px, py

def pixel_to_board(px, py):
    """Mouse pixel → board (x, y)."""
    x = px // SQUARE_SIZE
    y = 7 - (py // SQUARE_SIZE)
    return x, y

class ChessGUI:

    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Chess AI')

        # Load fonts:try a system font that has chess glyphs
        self.piece_font  = self._load_piece_font(int(SQUARE_SIZE * 0.78))
        self.label_font  = pygame.font.SysFont('consolas', 16)
        self.status_font = pygame.font.SysFont('consolas', 22, bold=True)

        self.reset()

    def reset(self):
        self.chess_board  = chessboard_module.Board.new()
        self.selected_sq  = None          # (x, y) of selected piece
        self.legal_moves  = []            # legal moves for selected piece
        self.last_move    = None          # (xfrom,yfrom,xto,yto) for highlighting
        self.move_history = []            # for undo
        self.status       = 'Your turn'   # status bar text
        self.status_color = COLOR_TEXT
        self.game_over    = False
        self.ai_thinking  = False

    def _load_piece_font(self, size):
        # Try fonts that render Unicode chess symbols well
        for name in ['segoeuisymbol', 'dejavusans', 'symbola', 'freesans', 'arial']:
            try:
                font = pygame.font.SysFont(name, size)
                if font:
                    return font
            except Exception:
                pass
        return pygame.font.SysFont(None, size)

    def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.ai_thinking:
                    mx, my = pygame.mouse.get_pos()
                    self.handle_click(pixel_to_board(mx, my))

            self.draw()
            clock.tick(60)

    def handle_key(self, key):
        if key == pygame.K_q:
            pygame.quit(); sys.exit()
        if key == pygame.K_r:
            self.reset()
        if key == pygame.K_u and not self.ai_thinking:
            self.undo()

    def handle_click(self, sq):
        x, y = sq
        if not self.chess_board.in_bounds(x, y):
            return

        piece = self.chess_board.get_piece(x, y)

        # If a piece is already selected, try to move it
        if self.selected_sq:
            moved = self.try_move(self.selected_sq, (x, y))
            if moved:
                self.selected_sq = None
                self.legal_moves = []
                return

        # Select a white piece
        if piece != 0 and piece.color == pieces_module.Piece.WHITE:
            self.selected_sq = (x, y)
            all_moves        = self.chess_board.get_possible_moves(pieces_module.Piece.WHITE)
            self.legal_moves = [
                m for m in all_moves
                if m.xfrom == x and m.yfrom == y
                and self._is_legal(m, pieces_module.Piece.WHITE)
            ]
        else:
            self.selected_sq = None
            self.legal_moves = []

    def try_move(self, from_sq, to_sq):
        """Try to move from from_sq to to_sq. Returns True if successful."""
        fx, fy = from_sq
        tx, ty = to_sq

        for move in self.legal_moves:
            if move.xto == tx and move.yto == ty:
                self.chess_board.perform_move(move)
                self.move_history.append(move)
                self.last_move = (fx, fy, tx, ty)

                # Check game over after human move
                if self.check_game_over(pieces_module.Piece.BLACK):
                    return True

                # Let AI respond in a background thread so UI stays responsive
                self.status       = 'AI is thinking...'
                self.status_color = COLOR_STATUS_AI
                self.ai_thinking  = True
                threading.Thread(target=self.ai_move, daemon=True).start()
                return True

        return False

    def ai_move(self):
        """Called in a background thread."""
        move = AI.get_best_move(self.chess_board, depth=3)

        if move is None:
            self.game_over    = True
            self.status       = 'AI has no moves — You win!'
            self.status_color = COLOR_STATUS_WIN
        else:
            self.last_move = (move.xfrom, move.yfrom, move.xto, move.yto)
            self.chess_board.perform_move(move)
            self.move_history.append(move)
            self.check_game_over(pieces_module.Piece.WHITE)

        self.ai_thinking = False

    def undo(self):
        """Undo AI move + human move."""
        steps = min(2, len(self.move_history))
        if steps == 0:
            return
        for _ in range(steps):
            move = self.move_history.pop()
            # Reverse the move manually by re-cloning from scratch
            # Simple approach: replay all remaining history on a fresh board
        # Rebuild board from history
        self.chess_board = chessboard_module.Board.new()
        history_copy     = self.move_history[:]
        self.move_history = []
        for m in history_copy:
            self.chess_board.perform_move(m)
            self.move_history.append(m)

        self.last_move    = None
        self.selected_sq  = None
        self.legal_moves  = []
        self.game_over    = False
        self.status       = 'Your turn'
        self.status_color = COLOR_TEXT

    def check_game_over(self, color_to_check):
        has_moves = any(
            True for m in self.chess_board.get_possible_moves(color_to_check)
            if self._is_legal(m, color_to_check)
        )
        if not has_moves:
            if self.chess_board.is_in_check(color_to_check):
                winner = 'You win! ♔' if color_to_check == pieces_module.Piece.BLACK else 'AI wins! ♚'
                self.status       = f'Checkmate — {winner}'
                self.status_color = COLOR_STATUS_WIN
            else:
                self.status       = 'Stalemate — Draw!'
                self.status_color = COLOR_STATUS_AI
            self.game_over = True
            return True

        if self.chess_board.is_in_check(color_to_check):
            who = 'You are' if color_to_check == pieces_module.Piece.WHITE else 'AI is'
            self.status       = f'{who} in check!'
            self.status_color = COLOR_CAPTURE
        else:
            self.status       = 'Your turn'
            self.status_color = COLOR_TEXT

        return False

    def _is_legal(self, move, color):
        copy = chessboard_module.Board.clone(self.chess_board)
        copy.perform_move(move)
        return not copy.is_in_check(color)

    def draw(self):
        self.draw_squares()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_status_bar()
        self.draw_coordinates()
        pygame.display.flip()

    def draw_squares(self):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                color = COLOR_LIGHT if (x + y) % 2 == 0 else COLOR_DARK
                px, py = board_to_pixel(x, y)
                pygame.draw.rect(self.screen, color, (px, py, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        # Last move highlight
        if self.last_move:
            fx, fy, tx, ty = self.last_move
            for (hx, hy) in [(fx, fy), (tx, ty)]:
                px, py = board_to_pixel(hx, hy)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((205, 210, 80, 120))
                self.screen.blit(s, (px, py))

        # Selected square
        if self.selected_sq:
            px, py = board_to_pixel(*self.selected_sq)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((20, 200, 80, 160))
            self.screen.blit(s, (px, py))

        # King in check
        for color in [pieces_module.Piece.WHITE, pieces_module.Piece.BLACK]:
            if self.chess_board.is_in_check(color):
                for x in range(BOARD_SIZE):
                    for y in range(BOARD_SIZE):
                        p = self.chess_board.get_piece(x, y)
                        if p != 0 and p.color == color and p.piece_type == pieces_module.King.PIECE_TYPE:
                            px, py = board_to_pixel(x, y)
                            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                            s.fill((230, 30, 30, 180))
                            self.screen.blit(s, (px, py))

        # Legal move dots
        for move in self.legal_moves:
            px, py = board_to_pixel(move.xto, move.yto)
            cx = px + SQUARE_SIZE // 2
            cy = py + SQUARE_SIZE // 2
            target = self.chess_board.get_piece(move.xto, move.yto)
            if target != 0:
                # Capture: draw a ring
                pygame.draw.circle(self.screen, COLOR_CAPTURE, (cx, cy), SQUARE_SIZE // 2 - 4, 5)
            else:
                # Quiet move: draw a small dot
                pygame.draw.circle(self.screen, COLOR_MOVE_DOT, (cx, cy), SQUARE_SIZE // 8)

    def draw_pieces(self):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                piece = self.chess_board.get_piece(x, y)
                if piece == 0:
                    continue
                symbol = UNICODE.get((piece.color, piece.piece_type), '?')
                px, py = board_to_pixel(x, y)

                # Shadow
                shadow = self.piece_font.render(symbol, True, (0, 0, 0))
                self.screen.blit(shadow, (px + 5 + 2, py + 4 + 2))

                # Piece
                color  = (255, 255, 255) if piece.color == pieces_module.Piece.WHITE else (30, 30, 30)
                text   = self.piece_font.render(symbol, True, color)
                self.screen.blit(text, (px + 5, py + 4))

    def draw_status_bar(self):
        # Dark bar at the bottom — drawn over the last rank row
        bar_h = 36
        bar_y = WINDOW_HEIGHT - bar_h
        pygame.draw.rect(self.screen, COLOR_TEXT_BG, (0, bar_y, WINDOW_WIDTH, bar_h))
        text = self.status_font.render(self.status, True, self.status_color)
        self.screen.blit(text, (12, bar_y + 7))

        # Hints on the right
        hint = self.label_font.render('U=undo  R=restart  Q=quit', True, (160, 160, 160))
        self.screen.blit(hint, (WINDOW_WIDTH - hint.get_width() - 10, bar_y + 10))

    def draw_coordinates(self):
        cols  = 'ABCDEFGH'
        pad   = 4
        for i in range(BOARD_SIZE):
            # Column letters (A–H) along the bottom edge
            col_label = self.label_font.render(cols[i], True, (80, 80, 80))
            px        = i * SQUARE_SIZE + SQUARE_SIZE // 2 - col_label.get_width() // 2
            self.screen.blit(col_label, (px, WINDOW_HEIGHT - 36 - col_label.get_height() - pad))

            # Row numbers (1–8) along the left edge
            row_label = self.label_font.render(str(i + 1), True, (80, 80, 80))
            py        = (7 - i) * SQUARE_SIZE + SQUARE_SIZE // 2 - row_label.get_height() // 2
            self.screen.blit(row_label, (pad, py))

if __name__ == '__main__':
    ChessGUI().run()
