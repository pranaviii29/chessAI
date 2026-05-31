# ♟ Chess AI

A terminal Chess AI written in pure Python 3. Human plays as White and the AI plays as Black.

The AI uses **Minimax** with **Alpha-Beta Pruning** to search for the best move, and evaluates positions using **material scores** and **piece-square tables**.

> No external libraries required. Just Python 3 and a terminal.

---

## Preview-What the board looks like

```
   A  B  C  D  E  F  G  H
  ------------------------
8 | BR BN BB BQ BK BB BN BR
7 | BP BP BP BP BP BP BP BP
6 | .. .. .. .. .. .. .. ..
5 | .. .. .. .. .. .. .. ..
4 | .. .. .. .. .. .. .. ..
3 | .. .. .. .. .. .. .. ..
2 | WP WP WP WP WP WP WP WP
1 | WR WN WB WQ WK WB WN WR

```

---

## Project Structure

```
ChessAI/
│
├── move.py      →  Move class (from square, to square, equality check)
├── pieces.py    →  Piece classes:Pawn, Knight, Bishop, Rook, Queen, King
│                   Each piece has its own get_possible_moves() method
├── board.py     →  Board class:the 8x8 grid, perform_move(), is_in_check()
├── ai.py        →  Heuristics (board scoring) + AI (alpha-beta search)
├── main.py      →  Game loop:human input, AI response, board display
│
└── README.md
```

| File | Classes | What it does |
|------|---------|--------------|
| `move.py` | `Move` | Stores `xfrom, yfrom, xto, yto`. Has `equals()` and `to_string()` |
| `pieces.py` | `Piece`, `Pawn`, `Knight`, `Bishop`, `Rook`, `Queen`, `King` | Each piece knows its own movement rules |
| `board.py` | `Board` | Holds the grid. Handles `perform_move()`, `clone()`, `is_in_check()` |
| `ai.py` | `Heuristics`, `AI` | Scores the board and runs alpha-beta search |
| `main.py` | — | Game loop, input parsing, board printing |

---

## Requirements

- Python 3.7 or higher
- No pip installs — pure standard Python

---

## How to Run

**Step 1:Clone teh repo**

```bash
git clone https://github.com/pranaviii29/ChessAI.git
cd ChessAI
```

**Step 2:Start the game**
```bash
python main.py
```

On Linux / Mac you may need:
```bash
python3 main.py
```

The game starts right away. No configuration needed.

---

## How to Play

You are **White** (bottom of the board). The AI is **Black** (top of the board).

### Enter moves like this

Type the square you are moving **from**, a space, then the square you are moving **to**:

```
Example move: E2 E4
```

This moves the piece on **E2** to **E4**.

### Reading the board

```
   A  B  C  D  E  F  G  H
  ------------------------
8 | BR BN BB BQ BK BB BN BR    ← Black's back rank (AI)
7 | BP BP BP BP BP BP BP BP
6 | .. .. .. .. .. .. .. ..
5 | .. .. .. .. .. .. .. ..
4 | .. .. .. .. .. .. .. ..
3 | .. .. .. .. .. .. .. ..
2 | WP WP WP WP WP WP WP WP
1 | WR WN WB WQ WK WB WN WR    ← White's back rank (You)
    ↑                   ↑
   A-file             H-file
```

**Piece codes:**

| Code | Piece |
|------|-------|
| `WP` / `BP` | White / Black **Pawn** |
| `WN` / `BN` | White / Black **Knight** |
| `WB` / `BB` | White / Black **Bishop** |
| `WR` / `BR` | White / Black **Rook** |
| `WQ` / `BQ` | White / Black **Queen** |
| `WK` / `BK` | White / Black **King** |
| `..` | Empty square |

### Move examples

| You type | What it does |
|----------|--------------|
| `E2 E4` | Push pawn forward two squares |
| `G1 F3` | Develop right knight |
| `F1 C4` | Develop bishop to C4 |
| `D1 H5` | Move queen to H5 |
| `E1 G1` | Castle **kingside** (king slides 2 squares right) |
| `E1 C1` | Castle **queenside** (king slides 2 squares left) |
| `quit`  | Exit the game |

---

## How the AI Works

### Minimax
The AI builds a tree of all possible moves several turns ahead. It assumes the human will always play his/her best move, and it plays its best counter. It picks whichever move leads to the best outcome against perfect play.

### Alpha-Beta Pruning
An optimisation that makes Minimax much faster. It keeps track of:
- `alpha` — the best score White can already guarantee
- `beta` — the best score Black can already guarantee

Any branch where the outcome is already worse than what is guaranteed is **skipped entirely**. This allows the AI to search deeper without checking every single branch.

### Board Evaluation
At the bottom of the search tree, every position is scored:

**Material** — piece values added up for both sides:

| Piece | Value |
|-------|-------|
| Pawn | 100 |
| Knight | 320 |
| Bishop | 330 |
| Rook | 500 |
| Queen | 900 |

**Piece-square tables** — each piece type has an 8×8 bonus table. A knight in the centre of the board scores more than a knight stuck in a corner. A pawn closer to promotion scores more than one sitting on the start rank.

Final score = `White total − Black total`. Positive = White is better. Negative = Black is better.

---

## Adjust AI Strength

Open `main.py` and change the `depth` number:

```python
ai_move = AI.get_best_move(chessboard, depth=3)

---


## Supported Rules

| Rule | Status |
|------|--------|
| All standard piece moves |
| Castling — kingside and queenside |
| Pawn promotion — auto promotes to Queen |
| Check detection |
| Checkmate detection | 
| Stalemate detection |

Note: En passant is not implemented 

---

