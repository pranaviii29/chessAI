"""
gui.py  —  Pygame GUI for Chess AI
-------------------------------------
Run with:   python gui.py

Controls:
  • Click a piece       to select it
  • Click a green dot   to move there
  • Click elsewhere     to deselect
  • U                   undo last move + AI reply
  • R                   restart
  • Q / close window    quit

New in this version:
  • En passant is fully supported
  • Promotion popup — choose Queen, Rook, Bishop, or Knight
"""

import sys
import threading
import pygame

import board as chess_board
import pieces
from ai   import AI
from move import Move

BOARD_PX   = 640          # board area (square)
SQUARE     = BOARD_PX // 8
STATUS_H   = 44
WIN_W      = BOARD_PX
WIN_H      = BOARD_PX + STATUS_H

LIGHT         = (240, 217, 181)
DARK          = (181, 136,  99)
SEL_COLOR     = ( 20, 200,  80, 160)
DOT_COLOR     = (100, 200, 100)
CAPTURE_COLOR = (220,  60,  60)
CHECK_COLOR   = (230,  30,  30, 180)
LAST_COLOR    = (205, 210,  80, 120)
BAR_BG        = ( 40,  40,  40)
WHITE_TEXT    = (255, 255, 255)
GREY_TEXT     = (160, 160, 160)
GREEN_TEXT    = ( 50, 200,  80)
YELLOW_TEXT   = (255, 200,   0)

# Promotion popup
POPUP_BG      = ( 30,  30,  30)
POPUP_BORDER  = (200, 200, 200)
POPUP_HOVER   = ( 70,  70,  70)

UNICODE = {
    (pieces.Piece.WHITE, pieces.King.PIECE_TYPE):   '♔',
    (pieces.Piece.WHITE, pieces.Queen.PIECE_TYPE):  '♕',
    (pieces.Piece.WHITE, pieces.Rook.PIECE_TYPE):   '♖',
    (pieces.Piece.WHITE, pieces.Bishop.PIECE_TYPE): '♗',
    (pieces.Piece.WHITE, pieces.Knight.PIECE_TYPE): '♘',
    (pieces.Piece.WHITE, pieces.Pawn.PIECE_TYPE):   '♙',
    (pieces.Piece.BLACK, pieces.King.PIECE_TYPE):   '♚',
    (pieces.Piece.BLACK, pieces.Queen.PIECE_TYPE):  '♛',
    (pieces.Piece.BLACK, pieces.Rook.PIECE_TYPE):   '♜',
    (pieces.Piece.BLACK, pieces.Bishop.PIECE_TYPE): '♝',
    (pieces.Piece.BLACK, pieces.Knight.PIECE_TYPE): '♞',
    (pieces.Piece.BLACK, pieces.Pawn.PIECE_TYPE):   '♟',
}

# Promotion options shown in the popup (in order)
PROMO_OPTIONS = [pieces.Queen, pieces.Rook, pieces.Bishop, pieces.Knight]
PROMO_SYMBOLS = {
    pieces.Piece.WHITE: ['♕', '♖', '♗', '♘'],
    pieces.Piece.BLACK: ['♛', '♜', '♝', '♞'],
}

def to_pixel(x, y):
    return x * SQUARE, (7 - y) * SQUARE

def to_board(px, py):
    return px // SQUARE, 7 - py // SQUARE

class ChessGUI:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption('Chess AI')

        self.piece_font  = self._load_font(int(SQUARE * 0.78))
        self.label_font  = pygame.font.SysFont('consolas', 15)
        self.status_font = pygame.font.SysFont('consolas', 21, bold=True)
        self.popup_font  = pygame.font.SysFont('consolas', 14)

        self.reset()

    def _load_font(self, size):
        for name in ['segoeuisymbol', 'dejavusans', 'symbola', 'freesans', 'arial']:
            try:
                f = pygame.font.SysFont(name, size)
                if f:
                    return f
            except Exception:
                pass
        return pygame.font.SysFont(None, size)

 
    def reset(self):
        self.chess_board   = chess_board.Board.new()
        self.selected      = None    # (x, y) of selected piece
        self.legal_moves   = []      # legal moves for selected piece
        self.last_move     = None    # (xfrom,yfrom,xto,yto) for highlight
        self.history       = []      # list of moves played (for undo)
        self.status        = 'Your turn'
        self.status_color  = WHITE_TEXT
        self.game_over     = False
        self.ai_thinking   = False

        # Promotion popup state
        self.promo_pending = None    # Move waiting for piece choice
        self.promo_rects   = []      # clickable rects in the popup
        self.promo_color   = None    # color of the promoting pawn

    def run(self):
        clock = pygame.time.Clock()
        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.promo_pending:
                        self.handle_promo_click(mx, my)
                    elif not self.game_over and not self.ai_thinking:
                        self.handle_click(to_board(mx, my))

            self.draw(mx, my)
            clock.tick(60)

    def handle_key(self, key):
        if key == pygame.K_q:
            pygame.quit(); sys.exit()
        if key == pygame.K_r:
            self.reset()
        if key == pygame.K_u and not self.ai_thinking and not self.promo_pending:
            self.undo()

    def handle_click(self, sq):
        x, y = sq
        if not self.chess_board.in_bounds(x, y):
            return

        # If a piece is already selected, try to move it
        if self.selected:
            if self.try_move(self.selected, (x, y)):
                self.selected    = None
                self.legal_moves = []
                return

        # Select a white piece
        piece = self.chess_board.get_piece(x, y)
        if piece != 0 and piece.color == pieces.Piece.WHITE:
            self.selected    = (x, y)
            all_moves        = self.chess_board.get_possible_moves(pieces.Piece.WHITE)
            self.legal_moves = [
                m for m in all_moves
                if m.xfrom == x and m.yfrom == y and self.is_legal(m, pieces.Piece.WHITE)
            ]
        else:
            self.selected    = None
            self.legal_moves = []

    def try_move(self, from_sq, to_sq):
        fx, fy = from_sq
        tx, ty = to_sq

        for move in self.legal_moves:
            if move.xto == tx and move.yto == ty:
                piece = self.chess_board.get_piece(fx, fy)

                # Check if this is a pawn promotion
                promo_rank = 0 if piece.color == pieces.Piece.WHITE else 7
                if piece.piece_type == pieces.Pawn.PIECE_TYPE and ty == promo_rank:
                    # Show promotion popup before completing the move
                    self.promo_pending = move
                    self.promo_color   = piece.color
                    return True

                # Normal move (or en passant)
                self.apply_move(move)
                return True

        return False

    def handle_promo_click(self, mx, my):
        for i, rect in enumerate(self.promo_rects):
            if rect.collidepoint(mx, my):
                # Player chose a piece — complete the move
                self.promo_pending.promotion_piece = PROMO_OPTIONS[i]
                self.apply_move(self.promo_pending)
                self.promo_pending = None
                self.promo_rects   = []
                self.promo_color   = None
                return

    def draw_promo_popup(self, mx, my):
        """Draw a centered popup letting the player pick a promotion piece."""
        option_size = 100
        padding     = 16
        total_w     = len(PROMO_OPTIONS) * option_size + padding * 2
        total_h     = option_size + padding * 2 + 30

        px = (WIN_W - total_w) // 2
        py = (BOARD_PX - total_h) // 2

        # Background
        popup_rect = pygame.Rect(px, py, total_w, total_h)
        pygame.draw.rect(self.screen, POPUP_BG, popup_rect, border_radius=10)
        pygame.draw.rect(self.screen, POPUP_BORDER, popup_rect, 2, border_radius=10)

        # Title
        title = self.popup_font.render('Choose promotion piece:', True, WHITE_TEXT)
        self.screen.blit(title, (px + padding, py + 8))

        # Piece options
        self.promo_rects = []
        symbols = PROMO_SYMBOLS[self.promo_color]

        for i, symbol in enumerate(symbols):
            rx = px + padding + i * option_size
            ry = py + 34
            rect = pygame.Rect(rx, ry, option_size - 6, option_size - 6)
            self.promo_rects.append(rect)

            # Hover highlight
            color = POPUP_HOVER if rect.collidepoint(mx, my) else (50, 50, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, POPUP_BORDER, rect, 1, border_radius=8)

            # Symbol
            text = self.piece_font.render(symbol, True, WHITE_TEXT)
            self.screen.blit(text, (rx + (option_size - 6 - text.get_width()) // 2,
                                    ry + (option_size - 6 - text.get_height()) // 2))

    # ── Apply move + trigger AI ───────────────────────────────────────────────

    def apply_move(self, move):
        self.last_move = (move.xfrom, move.yfrom, move.xto, move.yto)
        self.chess_board.perform_move(move)
        self.history.append(move)

        if self.check_game_over(pieces.Piece.BLACK):
            return

        self.status      = 'AI is thinking...'
        self.status_color = YELLOW_TEXT
        self.ai_thinking  = True
        threading.Thread(target=self.ai_turn, daemon=True).start()

    def ai_turn(self):
        move = AI.get_best_move(self.chess_board, depth=3)
        if move is None:
            self.game_over    = True
            self.status       = 'AI has no moves — You win!'
            self.status_color = GREEN_TEXT
        else:
            self.last_move = (move.xfrom, move.yfrom, move.xto, move.yto)
            self.chess_board.perform_move(move)
            self.history.append(move)
            self.check_game_over(pieces.Piece.WHITE)
        self.ai_thinking = False

    def undo(self):
        steps = min(2, len(self.history))
        if steps == 0:
            return
        # Rebuild board from scratch by replaying remaining history
        keep = self.history[:-steps]
        self.chess_board = chess_board.Board.new()
        self.history     = []
        for m in keep:
            self.chess_board.perform_move(m)
            self.history.append(m)

        self.last_move    = None
        self.selected     = None
        self.legal_moves  = []
        self.game_over    = False
        self.status       = 'Your turn'
        self.status_color = WHITE_TEXT

    # ── Game over check ───────────────────────────────────────────────────────

    def check_game_over(self, color):
        has_moves = any(
            True for m in self.chess_board.get_possible_moves(color)
            if self.is_legal(m, color)
        )
        if not has_moves:
            if self.chess_board.is_in_check(color):
                winner = 'You win! ♔' if color == pieces.Piece.BLACK else 'AI wins! ♚'
                self.status       = f'Checkmate — {winner}'
                self.status_color = GREEN_TEXT
            else:
                self.status       = 'Stalemate — Draw!'
                self.status_color = YELLOW_TEXT
            self.game_over = True
            return True

        if self.chess_board.is_in_check(color):
            who = 'You are' if color == pieces.Piece.WHITE else 'AI is'
            self.status       = f'{who} in check!'
            self.status_color = (255, 80, 80)
        else:
            self.status       = 'Your turn'
            self.status_color = WHITE_TEXT
        return False

    def is_legal(self, move, color):
        copy = chess_board.Board.clone(self.chess_board)
        copy.perform_move(move)
        return not copy.is_in_check(color)

    def draw(self, mx, my):
        self.draw_squares()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_status_bar()
        self.draw_coordinates()
        if self.promo_pending:
            self.draw_promo_popup(mx, my)
        pygame.display.flip()

    def draw_squares(self):
        for x in range(8):
            for y in range(8):
                color = LIGHT if (x + y) % 2 == 0 else DARK
                px, py = to_pixel(x, y)
                pygame.draw.rect(self.screen, color, (px, py, SQUARE, SQUARE))

    def draw_highlights(self):
        # Last move
        if self.last_move:
            for hx, hy in [(self.last_move[0], self.last_move[1]),
                           (self.last_move[2], self.last_move[3])]:
                s = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                s.fill(LAST_COLOR)
                self.screen.blit(s, to_pixel(hx, hy))

        # Selected square
        if self.selected:
            s = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
            s.fill(SEL_COLOR)
            self.screen.blit(s, to_pixel(*self.selected))

        # King in check
        for color in [pieces.Piece.WHITE, pieces.Piece.BLACK]:
            if self.chess_board.is_in_check(color):
                for x in range(8):
                    for y in range(8):
                        p = self.chess_board.get_piece(x, y)
                        if p != 0 and p.color == color and p.piece_type == pieces.King.PIECE_TYPE:
                            s = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                            s.fill(CHECK_COLOR)
                            self.screen.blit(s, to_pixel(x, y))

        # Legal move dots
        for move in self.legal_moves:
            px, py = to_pixel(move.xto, move.yto)
            cx, cy = px + SQUARE // 2, py + SQUARE // 2
            target = self.chess_board.get_piece(move.xto, move.yto)
            if target != 0 or move.is_en_passant:
                pygame.draw.circle(self.screen, CAPTURE_COLOR, (cx, cy), SQUARE // 2 - 4, 5)
            else:
                pygame.draw.circle(self.screen, DOT_COLOR, (cx, cy), SQUARE // 8)

    def draw_pieces(self):
        for x in range(8):
            for y in range(8):
                piece = self.chess_board.get_piece(x, y)
                if piece == 0:
                    continue
                symbol = UNICODE.get((piece.color, piece.piece_type), '?')
                px, py = to_pixel(x, y)

                shadow = self.piece_font.render(symbol, True, (0, 0, 0))
                self.screen.blit(shadow, (px + 5 + 2, py + 4 + 2))

                color = (255, 255, 255) if piece.color == pieces.Piece.WHITE else (30, 30, 30)
                text  = self.piece_font.render(symbol, True, color)
                self.screen.blit(text, (px + 5, py + 4))

    def draw_status_bar(self):
        pygame.draw.rect(self.screen, BAR_BG, (0, BOARD_PX, WIN_W, STATUS_H))
        text = self.status_font.render(self.status, True, self.status_color)
        self.screen.blit(text, (12, BOARD_PX + 11))
        hint = self.label_font.render('U=undo  R=restart  Q=quit', True, GREY_TEXT)
        self.screen.blit(hint, (WIN_W - hint.get_width() - 10, BOARD_PX + 14))

    def draw_coordinates(self):
        cols = 'ABCDEFGH'
        pad  = 4
        for i in range(8):
            col = self.label_font.render(cols[i], True, (100, 100, 100))
            px  = i * SQUARE + SQUARE // 2 - col.get_width() // 2
            self.screen.blit(col, (px, BOARD_PX - col.get_height() - pad))

            row = self.label_font.render(str(i + 1), True, (100, 100, 100))
            py  = (7 - i) * SQUARE + SQUARE // 2 - row.get_height() // 2
            self.screen.blit(row, (pad, py))

if __name__ == '__main__':
    ChessGUI().run()
