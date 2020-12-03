import chess, random, time, math, chess.pgn, multiprocessing

firstmovesdict = {}


# Settings
maxdepth = 3
random_mag = 0.25
centerbonus = 0.5
centerattackbonus = 0.5
checkbonus = 0.5
endbonus = 15

# Number of cores to utilize
usecores = 2

earlycurve_base = 1.2
earlycurve_k = 0.3
earlycurve_o = 7


global moves_checked

verbose = False

# Points for each piece
pointsdict = {chess.PAWN: 1,
              chess.KNIGHT: 3,
              chess.BISHOP: 3,
              chess.ROOK: 5,
              chess.QUEEN: 8,
              chess.KING: 20
              }

# Development bonus
devbonus = {chess.PAWN: 0.5,
            chess.KNIGHT: 0.25,
            chess.BISHOP: 0.25,
            chess.ROOK: -0.25,
            chess.QUEEN: 0,
            chess.KING: -1
            }


def analyzemove(movenum, firstcolor, color, aboard, depth):
    global moves_checked
    if (verbose):
        print("\n\nAnalyzing " + str(color) + " at Depth: " + str(depth))
        print(aboard)
    all_moves = {}
    # Change the sign of points addition depending on if we are analyzing our vs opponent move
    for move in aboard.legal_moves:
        moves_checked += 1
        if (verbose):
            if depth == 0:
                print("Analyzing upper move: ^" + str(move))
            else:
                print("Analyzing move: " + str(move))

        finalvalue = 0
        movepiece = aboard.piece_at(move.from_square)

        # Points distribution
        # Capture
        if aboard.is_capture(move):

            if aboard.is_en_passant(move):
                piece = chess.PAWN
            else:
                piece = aboard.piece_at(move.to_square).piece_type
            if verbose:
                print("Capture of value: " + str(pointsdict[piece]))
            finalvalue += pointsdict[piece]

        earlygain = (earlycurve_k * math.pow(earlycurve_base, -movenum + earlycurve_o))

        # Development
        if color == chess.WHITE:
            if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_2))) or (move.from_square in chess.SquareSet(chess.BB_RANK_1)):
                devbonusi = earlygain * devbonus[movepiece.piece_type]
                if verbose:
                    print("Applying development bonus of " + str(devbonusi))
                finalvalue += devbonusi
        if color == chess.BLACK:
            if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_7))) or (move.from_square in chess.SquareSet(chess.BB_RANK_8)):
                devbonusi = earlygain * devbonus[movepiece.piece_type]
                if verbose:
                    print("Applying development bonus of " + str(devbonusi))
                finalvalue += devbonusi

        # Center position
        if move.to_square in chess.SquareSet(chess.BB_CENTER):
            if verbose:
                print("Applying center position bonus")
            finalvalue += earlygain * centerbonus

        # Check
        if aboard.gives_check(move):
            finalvalue += checkbonus

        # Push move for the following points
        aboard.push(move)

        # Center attack
        if verbose & (len(chess.SquareSet(chess.BB_CENTER) & aboard.attacks(move.to_square)) > 0):
            print("Applying center attack bonus of: " + str(earlygain * centerattackbonus * len(chess.SquareSet(chess.BB_CENTER) & aboard.attacks(move.to_square))))
        finalvalue += earlygain * centerattackbonus * len(chess.SquareSet(chess.BB_CENTER) & aboard.attacks(move.to_square))

        # Mates
        if aboard.is_checkmate():
            finalvalue += endbonus
        if aboard.is_stalemate():
            finalvalue -= endbonus
        if aboard.is_repetition():
            finalvalue -= 100

        # Pop back move after analysing
        aboard.pop()

        # Random variance
        finalvalue += (random.random() * random_mag) - (random_mag / 2)

        # Promotion
        if movepiece.piece_type == chess.PAWN:
            currank = chess.square_rank(move.from_square)
            if color == chess.WHITE and move.to_square in chess.SquareSet(chess.BB_RANK_8):
                if (verbose):
                    print("Applying promotion bonus")
                finalvalue += 8
            if color == chess.BLACK and move.to_square in chess.SquareSet(chess.BB_RANK_1):
                if (verbose):
                    print("Applying promotion bonus")
                finalvalue += 8

        # Runs next depth
        if depth < maxdepth:
            if color == chess.WHITE:
                nextcolor = chess.BLACK
            else:
                nextcolor = chess.WHITE

            aboard.push(move)
            finalvalue += analyzemove(movenum + 1, firstcolor, nextcolor, aboard, depth + 1)[1]
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
        if (verbose):
            print(sortedMoves)
    else:
        sign = -1
    return (bestMove[0], sign * bestMove[1])


board = chess.Board()
print(board)
i = 0
moves_checked = 0

game = chess.pgn.Game()
game.headers["White"] = "LukasEngine"
game.headers["Black"] = "LukasEngine"
game.setup(board)
node = game

while not board.is_game_over(claim_draw=True):
    # Loops until legal move is entered]
    if False:
        while True:
            move = input("Move: ")
            try:
                board.parse_san(move)
                break
            except:
                print("Invalid or illegal move")

        board.push_san(move)
        print(board)
    else:
        starttime = time.time()
        # Analyze moves here
        mymove = analyzemove(i, chess.WHITE, chess.WHITE, board, 0)[0]
        node = node.add_variation(mymove)
        mymove = board.san(mymove)
        board.push_san(mymove)
        print(f'{moves_checked:,}' + " possible moves analysed!")
        print(f'{moves_checked / (time.time() - starttime):,}' " moves/second")
        moves_checked = 0
        print("\n\nMOVE: " + mymove)
        print(board)

    starttime = time.time()
    # Analyze moves here
    mymove = analyzemove(i, chess.BLACK, chess.BLACK, board, 0)[0]
    node = node.add_variation(mymove)
    mymove = board.san(mymove)
    board.push_san(mymove)
    print(f'{moves_checked:,}' + " possible moves analysed!")
    print(f'{moves_checked/(time.time() - starttime):,}' " moves/second")
    moves_checked = 0
    print("\n\nMOVE: " + mymove)
    print(board)

game.headers["Result"] = board.result()
print("Game Over!")
print("PGN:\n")
print(game)