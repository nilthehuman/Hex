import sys
import time
import copy
import math

from itertools import chain

COPY_COUNTER = 0

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
        self.last_taken = None
        self.optimal_move = None
        self.score = None

    def __init__(self, other=None):
        if other is None:
            self.reset()
        else:
            global COPY_COUNTER
            COPY_COUNTER += 1
            self.board = copy.deepcopy(other.board)
            self.color = other.color
            self.last_move = other.last_move
            self.last_taken = other.last_taken
            self.optimal_move = None
            self.score = None

    @classmethod
    def from_fen(cls, fen, color):
        pos = Position()
        pos.color = color
        for rank in fen.split('/'):
            pos.board.append([])
            for square in rank:
                if square.isdigit():
                    for _ in range(int(square)):
                        pos.board[-1].append(' ')
                else:
                    pos.board[-1].append(square)
        return pos

    def __str__(self):
        rows = list(map(lambda x: ''.join(x), self.board))
        show_board = '\n'.join(rows)
        show_pos = show_board #+ "\nscore: %0.2f\noptimal_move: %s" % (self.score, move_to_algebraic(self.optimal_move))
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
        sq_from, sq_to = move
        self.last_move = move
        self.last_taken = self.board[sq_to.y][sq_to.x]
        # pawn promotion?
        if self.board[sq_from.y][sq_from.x] == 'P' and sq_to.y == 0 or self.board[sq_from.y][sq_from.x] == 'p' and sq_to.y == 7:
            self.board[sq_to.y][sq_to.x] = 'Q' if sq_to.y == 0 else 'q'
            self.board[sq_from.y][sq_from.x] = ' '
        else:
            self.board[sq_to.y][sq_to.x] = self.board[sq_from.y][sq_from.x]
            self.board[sq_from.y][sq_from.x] = ' '
        self.flip_color()

    def unmake_last_move(self):
        sq_from, sq_to = self.last_move
        if False:
            # pawn unpromotion???
            assert False
        else:
            self.board[sq_from.y][sq_from.x] = self.board[sq_to.y][sq_to.x]
            self.board[sq_to.y][sq_to.x] = self.last_taken
        self.last_move = None
        self.last_taken = None
        self.flip_color()

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

def square_available_for_take(square, color):
    x, y = square.x, square.y
    if x < 0 or x > 7 or y < 0 or y > 7:
        return False
    if pos.board[y][x] == ' ':
        return False
    return pos.board[y][x].islower() == (color == 'w')

def square_available_for_quiet_move(square, color):
    x, y = square.x, square.y
    if x < 0 or x > 7 or y < 0 or y > 7:
        return False
    return pos.board[y][x] == ' '

def get_takes(pos, square):
    return get_moves(pos, square, square_available_for_take, take=True)

def get_quiet_moves(pos, square):
    return get_moves(pos, square, square_available_for_quiet_move, take=False)

def get_moves(pos, square, square_available, take):
    moves = []
    x, y = square.x, square.y
    if pos.board[y][x] == ' ':
        return []
    # pawns are funky, define movement explicitly
    elif pos.board[y][x] == 'p':
        if take:
            if x < 7 and pos.board[y+1][x+1].isupper():
                # take to the left
                moves.append((square, Square(x+1, y+1)))
            if x > 0 and pos.board[y+1][x-1].isupper():
                # take to the right
                moves.append((square, Square(x-1, y+1)))
        else:
            if pos.board[y+1][x] == ' ':
                # not blocked
                moves.append((square, Square(x, y+1)))
                if y == 1 and pos.board[y+2][x] == ' ':
                    # two squares from initial position
                    moves.append((square, Square(x, y+2)))
    elif pos.board[y][x] == 'P':
        if take:
            if x > 0 and pos.board[y-1][x-1].islower():
                # take to the left
                moves.append((square, Square(x-1, y-1)))
            if x < 7 and pos.board[y-1][x+1].islower():
                # take to the right
                moves.append((square, Square(x+1, y-1)))
        else:
            if pos.board[y-1][x] == ' ':
                # not blocked
                moves.append((square, Square(x, y-1)))
                if y == 6 and pos.board[y-2][x] == ' ':
                    # two squares from initial position
                    moves.append((square, Square(x, y-2)))
    # --- regular pieces ---
    elif pos.board[y][x].upper() == 'N':
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
    elif pos.board[y][x].upper() == 'B':
        for delta in [Square(-1, -1), Square(-1, 1), Square(1, -1), Square(1, 1)]:
            candidate_square = square + delta
            while square_available_for_quiet_move(candidate_square, pos.color):
                if not take:
                    moves.append((square, candidate_square))
                candidate_square += delta
            if square_available(candidate_square, pos.color):
                moves.append((square, candidate_square))
    elif pos.board[y][x].upper() == 'R':
        for delta in [Square(0, -1), Square(-1, 0), Square(0, 1), Square(1, 0)]:
            candidate_square = square + delta
            while square_available_for_quiet_move(candidate_square, pos.color):
                if not take:
                    moves.append((square, candidate_square))
                candidate_square += delta
            if square_available(candidate_square, pos.color):
                moves.append((square, candidate_square))
    elif pos.board[y][x].upper() == 'Q':
        # a combination of B + R
        orig_piece = pos.board[y][x]
        pos.board[y][x] = 'B' if orig_piece.isupper() else 'b'
        moves = get_moves(pos, square, square_available, take)
        pos.board[y][x] = 'R' if orig_piece.isupper() else 'r'
        moves += get_moves(pos, square, square_available, take)
        pos.board[y][x] = orig_piece
    elif pos.board[y][x].upper() == 'K':
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                candidate_square = Square(x+dx, y+dy)
                if square_available(candidate_square, pos.color):
                    moves.append((square, candidate_square))
    else:
        assert False
    return moves

#### #### #### #### ####
def gen_all_moves(pos, take=False):
    for y in range(8):
        for x in range(8):
            if turn_to_move(pos.board[y][x], pos.color):
                if take:
                    takes = get_takes(pos, Square(x, y))
                    for t in takes:
                        yield t
                else:
                    moves = get_quiet_moves(pos, Square(x, y))
                    for m in moves:
                        yield m

def minimax(pos, alpha, beta, depth): # depth is in plies
    if depth < 1:
        # call heuristic evaluation
        pos.score = score(pos)
        #print(pos, file=sys.stderr, flush=True)
        return pos
    # zugzwang does not exist, so a move can only improve the position
    optimal_move = None
    optimal_score = alpha if pos.color == 'w' else beta
    opt = max if pos.color == 'w' else min
    # avoid copying the entire board array every time
    new_pos = Position(pos)
    all_moves = chain(gen_all_moves(pos, take=True), gen_all_moves(pos, take=False))
    for move in all_moves:
        new_pos.make_move(move)
        new_score = opt(optimal_score, minimax(new_pos, alpha, beta, depth-1).score)
        # improvement?
        if pos.color == 'w' and optimal_score < new_score:
            optimal_move = move
            optimal_score = new_score
            alpha = max(alpha, new_score)
        elif pos.color == 'b' and optimal_score > new_score:
            optimal_move = move
            optimal_score = new_score
            beta = min(beta, new_score)
        if alpha > beta:
            break
        new_pos.unmake_last_move()
    pos.optimal_move = optimal_move
    pos.score = optimal_score
    return pos

def test_minimax():
    pos = Position()
    pos.board = [[' ', ' ']]
    pass
#### #### #### #### ####

def first_move(pos):
    bishops = []
    for y in range(8):
        for x in range(8):
            if (pos.board[y][x] == 'B' and pos.color == 'w' or
                pos.board[y][x] == 'b' and pos.color == 'b'):
                bishops.append(Square(x, y))
    candidates = []
    for b in bishops:
        dx = 1 if b.x < 4 else -1
        y = 6 if pos.color == 'w' else 1
        new_y = 5 if pos.color == 'w' else 2
        candidates.append((Square(b.x+dx, y), Square(b.x+dx, new_y)))
    if pos.color == 'w':
        return candidates[0]
    candidate_positions = []
    for c in candidates:
        pos.make_move(c)
        candidate_positions.append(Position(pos))
        pos.unmake_last_move()
    opt = max if pos.color == 'w' else min
    return opt(candidate_positions, key=lambda c: minimax(Position(), -1000, 1000, 1).score)

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
    COPY_COUNTER = 0

    inputs = input().split()
    start_time = time.time_ns()
    pos = Position.from_fen(inputs[0], inputs[1])

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
    #print("score: %0.2f" % score_material(pos), file=sys.stderr, flush=True)

    if full_move == 1:
        print(move_to_algebraic(first_move(pos)))
    elif best.optimal_move is None:
        print("random")
    else:
        print(move_to_algebraic(best.optimal_move))

    print("copies made: %d" % COPY_COUNTER, file=sys.stderr, flush=True)
    print("time used: %d microsecs" % ((time.time_ns() - start_time) / (10**3)), file=sys.stderr, flush=True)
