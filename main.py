import chess

board = chess.Board()

print(board)

while (not board.is_checkmate()) and (not board.is_stalemate()) and (not board.is_insufficient_material()):
    # Loops until legal move is entered
    while True:
        move = input("Move: ")
        try:
            board.parse_san(move)
            break
        except:
            print("Invalid or illegal move")

    board.push_san(move)
    print(board)

    # Analyze moves here
    for move in board.legal_moves:
        print(board.san(move))


print("Game Over!")
