import sys
import time
import copy
import math

from itertools import chain

class Square:
    x = -1
    y = -1

    def __init__(self, x, y):
        self.x, self.y = x, y

    #def __init__(self, algebraic):
    #    self.x, self.y = algebraic_to_square(algebraic[0], algebraic[1])

    def __str__(self):
        return square_to_algebraic(x, y)

    def __neg__(self):
        return Square(-self.x, -self.y)

    def __add__(self, other):
        return Square(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Square(self.x - other.x, self.y - other.y)

# more or less standard piece value heuristics
PIECE_VALUES = {
    ' ' : 0.0,
    'P' : 1.0,
    'N' : 3.0,
    'B' : 3.25,
    'R' : 5,
    'Q' : 9.5,
    'K' : 100
}

def piece_value(piece):
    return PIECE_VALUES[piece.upper()]

# what the game looks like at the moment
# no castling, no en passant
class Position:
    def reset(self):
        self.board = []
        self.color = ''
        self.last_move = None
        self.optimal_move = None
        self.score = None

    def __init__(self, other=None):
        if other is None:
            self.reset()
        else:
            self.board = copy.deepcopy(other.board)
            self.color = other.color
            self.last_move = other.last_move
            self.optimal_move = None
            self.score = None

    def __str__(self):
        rows = list(map(lambda x: ''.join(x), self.board))
        show_board = '\n'.join(rows)
        show_board = ''
        show_pos = show_board + "\nscore: %0.2f\noptimal_move: %s" % (self.score, move_to_algebraic(self.optimal_move))
        return show_pos

    def flip_color(self):
        if self.color == 'w':
            self.color = 'b'
        else:
            self.color = 'w'

    def whose_man(self, square):
        return whose_man(self.board[square.y][square.x], self.color)

    def make_move(self, move):
        # it is the caller's responsibility to provide a legal move!
        new_pos = Position(self)
        new_pos.last_move = move
        sq_from, sq_to = move
        # pawn promotion?
        if new_pos.board[sq_from.y][sq_from.x] == 'P' and sq_to.y == 0 or new_pos.board[sq_from.y][sq_from.x] == 'p' and sq_to.y == 7:
            new_pos.board[sq_to.y][sq_to.x] = 'Q' if sq_to.y == 0 else 'q'
            new_pos.board[sq_from.y][sq_from.x] = ' '
        else:
            new_pos.board[sq_to.y][sq_to.x] = new_pos.board[sq_from.y][sq_from.x]
            new_pos.board[sq_from.y][sq_from.x] = ' '
        new_pos.flip_color()
        return new_pos

#### #### #### #### ####

def whose_man(piece, color):
    if piece == ' ':
        return 0
    if piece.isupper():
        return 1
    else:
        return -1

def turn_to_move(piece, color):
    if piece == ' ':
        return False
    if piece.isupper() == (color == 'w'):
        return True
    else:
        return False

def square_available(square, color):
    x, y = square.x, square.y
    if x < 0 or x > 7 or y < 0 or y > 7:
        return False
    return not turn_to_move(pos.board[y][x], pos.color)

def square_available_for_take(square, color):
    x, y = square.x, square.y
    if x < 0 or x > 7 or y < 0 or y > 7:
        return False
    if pos.board[y][x] == ' ':
        return False
    return pos.board[y][x].islower() == (color == 'w')

def get_moves(pos, square):
    moves = []
    x, y = square.x, square.y
    if pos.board[y][x] == ' ':
        return []
    # pawns are funky, define movement explicitly
    if pos.board[y][x] == 'p':
        if pos.board[y+1][x] == ' ':
            # not blocked
            moves.append((square, Square(x, y+1)))
            if y == 1 and pos.board[y+2][x] == ' ':
                # two squares from initial position
                moves.append((square, Square(x, y+2)))
        if x < 7 and pos.board[y+1][x+1].isupper():
            # take to the left
            moves.append((square, Square(x+1, y+1)))
        if x > 0 and pos.board[y+1][x-1].isupper():
            # take to the right
            moves.append((square, Square(x-1, y+1)))
        return moves
    if pos.board[y][x] == 'P':
        if pos.board[y-1][x] == ' ':
            # not blocked
            moves.append((square, Square(x, y-1)))
            if y == 6 and pos.board[y-2][x] == ' ':
                # two squares from initial position
                moves.append((square, Square(x, y-2)))
        if x > 0 and pos.board[y-1][x-1].islower():
            # take to the left
            moves.append((square, Square(x-1, y-1)))
        if x < 7 and pos.board[y-1][x+1].islower():
            # take to the right
            moves.append((square, Square(x+1, y-1)))
        return moves
    # --- regular pieces ---
    if pos.board[y][x].upper() == 'N':
        for dx in [-1, 1]:
            for dy in [-2, 2]:
                candidate_square = Square(x+dx, y+dy)
                if square_available(candidate_square, pos.color):
                    moves.append((square, candidate_square))
        for dx in [-2, 2]:
            for dy in [-1, 1]:
                candidate_square = Square(x+dx, y+dy)
                if square_available(candidate_square, pos.color):
                    moves.append((square, candidate_square))
    if pos.board[y][x].upper() == 'B':
        for delta in [Square(-1, -1), Square(-1, 1), Square(1, -1), Square(1, 1)]:
            candidate_square = square + delta
            while square_available(candidate_square, pos.color):
                moves.append((square, candidate_square))
                if square_available_for_take(candidate_square, pos.color):
                    break
                candidate_square += delta
    if pos.board[y][x].upper() == 'R':
        for delta in [Square(0, -1), Square(-1, 0), Square(0, 1), Square(1, 0)]:
            candidate_square = square + delta
            while square_available(candidate_square, pos.color):
                moves.append((square, candidate_square))
                if square_available_for_take(candidate_square, pos.color):
                    break
                candidate_square += delta
    if pos.board[y][x].upper() == 'Q':
        # a combination of B + R
        orig_piece = pos.board[y][x]
        pos.board[y][x] = 'B' if pos.board[y][x].isupper() else 'b'
        moves = get_moves(pos, square)
        pos.board[y][x] = 'R' if pos.board[y][x].isupper() else 'r'
        moves += get_moves(pos, square)
        pos.board[y][x] = orig_piece
    if pos.board[y][x].upper() == 'K':
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                candidate_square = Square(x+dx, y+dy)
                if square_available(candidate_square, pos.color):
                    moves.append((square, candidate_square))
    return moves

#### #### #### #### ####
def gen_all_moves(pos):
    i = 0
    for y in range(8):
        for x in range(8):
            if turn_to_move(pos.board[y][x], pos.color):
                moves = get_moves(pos, Square(x, y))
                for m in moves:
                    yield m

def minimax(pos, alpha, beta, depth): # depth is in plies
    if depth < 1:
        # call heuristic evaluation
        pos.score = score(pos)
        return pos
    optimum = Position()
    optimum.score = alpha if pos.color == 'w' else beta
    opt = max if pos.color == 'w' else min
    for move in gen_all_moves(pos):
        new_pos = pos.make_move(move)
        optimum = opt(optimum, minimax(new_pos, alpha, beta, depth - 1), key=lambda pos: pos.score)
        if pos.color == 'w':
            alpha = max(alpha, optimum.score)
        else:
            beta = min(beta, optimum.score)
        if alpha >= beta:
            break
    pos.optimal_move = optimum.last_move
    pos.score = optimum.score
    return pos

def test_minimax():
    pass  # how do you create a mock for gen_all_moves? :S
#### #### #### #### ####

def algebraic_to_square(algebraic):
    file, rank = algebraic[0], algebraic[1]
    x = ord(file) - ord('a')
    y = ord('8') - ord(rank)
    return (x, y)

def square_to_algebraic(x, y):
    rank = chr(ord('8') - y)
    file = chr(ord('a') + x)
    return file + rank

def move_to_algebraic(move):
    if move is None:
        return None
    sq_from = square_to_algebraic(move[0].x, move[0].y)
    sq_to = square_to_algebraic(move[1].x, move[1].y)
    return sq_from + sq_to

def score_material(pos):
    sum = 0
    for rank in pos.board:
        for square in rank:
            sum += whose_man(square, pos.color) * piece_value(square)
    return sum

# optimization results will go here:
TUNED_WEIGHTS = {}

def score_threats(pos):
    return 0

def score_position(pos):
    return 0

def score(pos):
    return 1 * score_material(pos) + 1 * score_threats(pos) + 1 * score_position(pos)

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

constants_count = int(input())
for i in range(constants_count):
    name, value = input().split()
#    print("name=%s, value=%s" % (name, value), file=sys.stderr, flush=True)

print("fen")

# game loop
while True:
    pos = Position()

    inputs = input().split()
    start_time = time.time_ns()
    for rank in inputs[0].split('/'):
        pos.board.append([])
        for square in rank:
            if square.isdigit():
                for _ in range(int(square)):
                    pos.board[-1].append(' ')
            else:
                pos.board[-1].append(square)
    pos.color = inputs[1]

    # use 'moves' and 'lastmove' perhaps?

    # the following input fields are unimportant
    castling = inputs[2]
    en_passant = inputs[3]
    half_move_clock = int(inputs[4])
    full_move = int(inputs[5])

    all_moves = gen_all_moves(pos)
    print(list(map(move_to_algebraic, all_moves)), file=sys.stderr, flush=True)
    best = minimax(pos, -1000, 1000, 2)
    print(best, file=sys.stderr, flush=True)
    #print(tree, file=sys.stderr, flush=True)
    #print("score: %0.2f" % score_material(pos), file=sys.stderr, flush=True)

    print(move_to_algebraic(best.optimal_move))

    print("time used: %d microsecs" % ((time.time_ns() - start_time) / (10**3)), file=sys.stderr, flush=True)
