import chess, random, time

firstmovesdict = {}


# Settings
maxdepth = 3
random_mag = 0.25
centerbonus = 0.25
centerattackbonus = 0.25
checkbonus = 0.5
endbonus = 15



global moves_checked

verbose = False

pointsdict = {chess.PAWN: 1,
              chess.KNIGHT: 3,
              chess.BISHOP: 3,
              chess.ROOK: 5,
              chess.QUEEN: 8,
              chess.KING: 20
              }

devbonus = {chess.PAWN: 0.25,
            chess.KNIGHT: 0.25,
            chess.BISHOP: 0.25,
            chess.ROOK: -0.25,
            chess.QUEEN: 0,
            chess.KING: -1
            }


def analyzemove(firstcolor, color, aboard, depth):
    global moves_checked
    if (verbose):
        print("\n\nAnalyzing " + str(color) + " at Depth: " + str(depth))
        print(aboard)
    all_moves = {}
    # Change the sign of points addition depending on if we are analyzing our vs opponent move
    for move in board.legal_moves:
        moves_checked += 1
        if (depth == 0):
            if (verbose):
                print("Analyzing upper move: ^" + str(move))
        finalvalue = 0
        movepiece = board.piece_at(move.from_square)

        # Points distribution
        # Capture
        if aboard.is_capture(move):
            if aboard.is_en_passant(move):
                piece = chess.PAWN
            else:
                piece = aboard.piece_at(move.to_square).piece_type
            finalvalue += pointsdict[piece]

        # Development
        if color == chess.WHITE:
            if (movepiece.symbol == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_2))) or (move.from_square in chess.SquareSet(chess.BB_RANK_1)):
                finalvalue += devbonus[movepiece.piece_type]
        if color == chess.BLACK:
            if (movepiece.symbol == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_7))) or (move.from_square in chess.SquareSet(chess.BB_RANK_8)):
                finalvalue += devbonus[movepiece.piece_type]

        # Center position
        if move.to_square in chess.SquareSet(chess.BB_CENTER):
            finalvalue += centerbonus

        # Check
        if aboard.gives_check(move):
            finalvalue += checkbonus

        # Push move for the following points
        aboard.push(move)

        # Center control
        finalvalue += centerattackbonus * len(chess.SquareSet(chess.BB_CENTER & move.from_square))

        # Mates
        if aboard.is_checkmate():
            finalvalue += endbonus
        if aboard.is_stalemate():
            finalvalue -= endbonus
        if aboard.is_repetition():
            finalvalue -= endbonus


        # Pop back move after analysing
        aboard.pop()

        # Random variance
        finalvalue += (random.random() * random_mag) - (random_mag / 2)

        # Promotion
        if movepiece.piece_type == chess.PAWN:
            currank = chess.square_rank(move.from_square)
            if color == chess.WHITE:
                squaresleft = 8 - currank
            if color == chess.BLACK:
                squaresleft = currank - 1
            if squaresleft > 0:
                finalvalue += 8 / (squaresleft * squaresleft * squaresleft)

        # Runs next depth
        if depth < maxdepth:
            if color == chess.WHITE:
                nextcolor = chess.BLACK
            else:
                nextcolor = chess.WHITE

            aboard.push(move)
            finalvalue += analyzemove(firstcolor, nextcolor, aboard, depth + 1)[1]
            aboard.pop()

        all_moves[move] = finalvalue
    if depth < maxdepth:
        if (verbose):
            print("\n\n\n##################################")
            print("SUMMARY OF DEPTH " + str(depth))
    if len(all_moves) == 0:
        bestMove = ("", 10)
    else:
        sortedMoves = sorted(all_moves.items(), key=lambda x: x[1], reverse=True)
        bestMove = sortedMoves[0]

        if (verbose):
            print("Best move " + str(bestMove[0]) + " had value of " + str(bestMove[1]))

    # When passing the best move's value upwards we need to sign it to benefit the above depth
    if (depth == 0):
        sign = 1
        print(sortedMoves)
    else:
        sign = -1
    return (bestMove[0], sign * bestMove[1])


board = chess.Board()
print(board)
i = 0
moves_checked = 0
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

    starttime = time.time()

    # Analyze moves here
    #Check if move in first moves dict
    if i == 0 and move in firstmovesdict:
        mymove = firstmovesdict[move]
    else:
        mymove = analyzemove(chess.BLACK, chess.BLACK, board, 0)[0]
        mymove = board.san(mymove)

    board.push_san(mymove)
    print(f'{moves_checked:,}' + " possible moves analysed!")
    print(f'{moves_checked/(time.time() - starttime):,}' " moves/second")
    moves_checked = 0
    print("\n\nMOVE: " + mymove)
    print(board)

print("Game Over!")
