import time
import chess

def testdepth(depth):
    if depth == 0:
        return 1
    nodes = 0
    for move in board.legal_moves:
        board.push(move)
        nodes = nodes + testdepth(depth -1)
        board.pop()

    return nodes

board = chess.Board()
startime = time.time()
pos = testdepth(4)
endtime = time.time()
print(pos)
print(pos /(endtime-startime))
