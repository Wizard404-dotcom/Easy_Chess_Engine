import asyncio
import platform
import pygame
import chess
from typing import Tuple, Optional

# Initialize pygame
pygame.init()

# Constants
BOARD_WIDTH, HEIGHT = 600, 600
SIDEBAR_WIDTH = 200
WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
BOARD_SIZE = 8
SQUARE_SIZE = BOARD_WIDTH // BOARD_SIZE
RED = (255, 100, 100)
PINK = (255, 200, 200)
HIGHLIGHT = (255, 255, 0, 100)
WHITE_TEXT = (255, 255, 255)
BLACK_TEXT = (0, 0, 0)
SIDEBAR_BG = (50, 50, 50)
FPS = 30

# Piece representations
PIECE_CHARS = {
    chess.PAWN: 'P', chess.KNIGHT: 'N', chess.BISHOP: 'B',
    chess.ROOK: 'R', chess.QUEEN: 'Q', chess.KING: 'K'
}

# Piece values for AI evaluation
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Font setup
FONT = pygame.font.SysFont('Arial', 40, bold=True)
SMALL_FONT = pygame.font.SysFont('Arial', 20, bold=True)

# Draw the board
def draw_board(screen: pygame.Surface, selected: Optional[Tuple[int, int]] = None, last_move: Optional[chess.Move] = None):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = PINK if (row + col) % 2 == 0 else RED
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    if selected:
        col, row = selected
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(HIGHLIGHT)
        screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    if last_move:
        from_col = chess.square_file(last_move.from_square)
        from_row = 7 - chess.square_rank(last_move.from_square)
        to_col = chess.square_file(last_move.to_square)
        to_row = 7 - chess.square_rank(last_move.to_square)
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill((0, 255, 0, 100))
        screen.blit(highlight_surface, (from_col * SQUARE_SIZE, from_row * SQUARE_SIZE))
        screen.blit(highlight_surface, (to_col * SQUARE_SIZE, to_row * SQUARE_SIZE))

# Draw pieces
def draw_pieces(screen: pygame.Surface, board: chess.Board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            char = PIECE_CHARS[piece.piece_type]
            color = WHITE_TEXT if piece.color == chess.WHITE else BLACK_TEXT
            if piece.color == chess.BLACK:
                char = char.lower()
            text = FONT.render(char, True, color)
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            text_rect = text.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                            row * SQUARE_SIZE + SQUARE_SIZE // 2))
            screen.blit(text, text_rect)

# Simple evaluation
def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -10000 if board.turn else 10000
    if board.is_stalemate():
        return 0
    
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = PIECE_VALUES[piece.piece_type]
            score += value if piece.color == chess.WHITE else -value
    return score

# Simple AI move selection with accuracy tracking
def get_ai_move(board: chess.Board) -> Tuple[chess.Move, float]:
    best_move = None
    best_score = float('inf')
    total_moves = 0
    good_moves = 0
    for move in board.legal_moves:
        total_moves += 1
        board.push(move)
        score = evaluate_board(board)
        board.pop()
        if score < best_score:
            best_score = score
            best_move = move
            good_moves = total_moves
    accuracy = (good_moves / total_moves) * 100 if total_moves > 0 else 100
    return best_move, accuracy

# Game class
class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.board = chess.Board()
        self.selected = None
        self.valid_moves = []
        self.running = True
        self.last_player_move = None
        self.last_ai_move = None
        self.player_accuracy = []
        self.ai_accuracy = []
        pygame.display.set_caption("Chess Game - Player vs AI")

    def calculate_move_accuracy(self, move: chess.Move) -> float:
        board_copy = self.board.copy()
        board_copy.push(move)
        best_score = evaluate_board(board_copy)
        total_moves = 0
        good_moves = 0
        for alt_move in self.board.legal_moves:
            total_moves += 1
            board_copy = self.board.copy()
            board_copy.push(alt_move)
            if evaluate_board(board_copy) >= best_score:
                good_moves += 1
        return (good_moves / total_moves) * 100 if total_moves > 0 else 100

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, SIDEBAR_BG, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))
        
        # Last moves
        if self.last_player_move:
            text = SMALL_FONT.render(f"Player: {self.last_player_move.uci()}", True, WHITE_TEXT)
            self.screen.blit(text, (BOARD_WIDTH + 10, 10))
        if self.last_ai_move:
            text = SMALL_FONT.render(f"AI: {self.last_ai_move.uci()}", True, BLACK_TEXT)
            self.screen.blit(text, (BOARD_WIDTH + 10, 40))
        
        # Game status
        status = "Playing"
        if self.board.is_check():
            status = "Check"
        if self.board.is_checkmate():
            status = "Checkmate"
        if self.board.is_stalemate():
            status = "Stalemate"
        text = SMALL_FONT.render(f"Status: {status}", True, WHITE_TEXT)
        self.screen.blit(text, (BOARD_WIDTH + 10, 70))
        
        # Accuracy
        player_acc = sum(self.player_accuracy) / len(self.player_accuracy) if self.player_accuracy else 100
        ai_acc = sum(self.ai_accuracy) / len(self.ai_accuracy) if self.ai_accuracy else 100
        text = SMALL_FONT.render(f"Player Acc: {player_acc:.1f}%", True, WHITE_TEXT)
        self.screen.blit(text, (BOARD_WIDTH + 10, 100))
        text = SMALL_FONT.render(f"AI Acc: {ai_acc:.1f}%", True, BLACK_TEXT)
        self.screen.blit(text, (BOARD_WIDTH + 10, 130))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if pos[0] >= BOARD_WIDTH:  # Ignore clicks on sidebar
                    return
                col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
                square = chess.square(col, 7 - row)
                
                if self.selected is None and self.board.turn == chess.WHITE:
                    piece = self.board.piece_at(square)
                    if piece and piece.color == chess.WHITE:
                        self.selected = (col, row)
                        self.valid_moves = [m for m in self.board.legal_moves if m.from_square == square]
                elif self.selected:
                    target_square = chess.square(col, 7 - row)
                    move = next((m for m in self.valid_moves if m.to_square == target_square), None)
                    if move:
                        accuracy = self.calculate_move_accuracy(move)
                        self.player_accuracy.append(accuracy)
                        self.board.push(move)
                        self.last_player_move = move
                        self.selected = None
                        self.valid_moves = []
                        if not self.board.is_game_over() and self.board.turn == chess.BLACK:
                            ai_move, ai_accuracy = get_ai_move(self.board)
                            self.board.push(ai_move)
                            self.last_ai_move = ai_move
                            self.ai_accuracy.append(ai_accuracy)
                    else:
                        self.selected = None
                        self.valid_moves = []

    def draw(self):
        self.screen.fill((0, 0, 0))
        draw_board(self.screen, self.selected, self.last_player_move if self.board.turn == chess.BLACK else self.last_ai_move)
        draw_pieces(self.screen, self.board)
        self.draw_sidebar()
        pygame.display.flip()

async def main():
    game = ChessGame()
    while game.running:
        game.handle_events()
        game.draw()
        await asyncio.sleep(1.0 / FPS)
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())