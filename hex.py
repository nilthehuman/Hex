import sys
import time
import copy
import math

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
    board = []
    color = ''

    def reset(self):
        self.board = []
        self.color = ''

    def __init__(self, other=None):
        if other is None:
            self.reset()
        else:
            self.board = copy.deepcopy(other.board)
            self.color = other.color

    def __str__(self):
        rows = list(map(lambda x: ''.join(x), self.board))
        return '\n'.join(rows)

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

def piece_moves(pos, square):
    moves = []
    x, y = square.x, square.y
    if pos.board[y][x] == ' ':
        return []
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
    if pos.board[y][x].upper() == 'N':
        return []
    # etc.
    return moves
    assert False

def all_moves(pos):
    moves = []
    for y in range(8):
        for x in range(8):
            if turn_to_move(pos.board[y][x], pos.color):
                moves = moves + piece_moves(pos, Square(x, y))
    return moves

class Tree:
    def __init__(self, pos, last_move):
        self.children = []
        self.pos = pos
        self.last_move = last_move
        self.optimal_move = None
        self.score = None
    
    def __str__(self):
        show_children = "[" + ','.join(map(str, self.children)) + "]"
        show = "[%0.2f %s] %s" % (self.score, move_to_algebraic(self.optimal_move), show_children)
        return show

def build_game_tree(root, depth): # depth is in plies
    if depth < 1:
        return
    for move in all_moves(root.pos):
        new_pos = root.pos.make_move(move)
        root.children.append(Tree(new_pos, move))
    if depth > 1:
        for child in root.children:
            build_game_tree(child, depth - 1)

def score_tree_bottom(tree):
    if not tree.children:
        tree.score = score(tree.pos)
    else:
        for child in tree.children:
            score_tree_bottom(child)

def minimax(tree):
    if not tree.children:
        return
    for child in tree.children:
        minimax(child)
    optimal = None
    if tree.pos.color == 'w':
        optimal = max(tree.children, key=lambda child: child.score)
    else:
        optimal = min(tree.children, key=lambda child: child.score)
    tree.optimal_move = optimal.last_move
    tree.score = optimal.score

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

def score_mate(pos):
    return 0

def score_material(pos):
    sum = 0
    for rank in pos.board:
        for square in rank:
            sum = sum + whose_man(square, pos.color) * piece_value(square)
    return sum

# optimization results will go here:
TUNED_WEIGHTS = {}

def score_position(pos):
    return 0

def score(pos):
    mate = score_mate(pos)
    if bool(mate):
        return mate
    return score_material(pos) + score_position(pos)

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

constants_count = int(input())
for i in range(constants_count):
    name, value = input().split()
#    print("name=%s, value=%s" % (name, value), file=sys.stderr, flush=True)

# Write an action using print
# To debug: print("Debug messages...", file=sys.stderr, flush=True)

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

    # the following input fields are unimportant
    castling = inputs[2]
    en_passant = inputs[3]
    half_move_clock = int(inputs[4])
    full_move = int(inputs[5])

    #print(list(map(move_to_algebraic, all_moves(pos))), file=sys.stderr, flush=True)
    tree = Tree(pos, None)
    build_game_tree(tree, 1)
    score_tree_bottom(tree)
    minimax(tree)
    print(tree, file=sys.stderr, flush=True)

    print("random")

    print("time used: %d microsecs" % ((time.time_ns() - start_time) / (10**3)), file=sys.stderr, flush=True)
