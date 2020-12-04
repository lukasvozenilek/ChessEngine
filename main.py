import chess, random, time, math, chess.pgn, chess.engine, datetime

firstmovesdict = {}

# Settings
maxdepth = 1
random_mag = 0
centerbonus = 0.25
centerattackbonus = 0.25
checkbonus = 0.5
endbonus = 15
castlebonus = 0.5

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
              chess.KING: 0
              }

# Development bonus
devbonus = {chess.PAWN: 0.5,
            chess.KNIGHT: 0.25,
            chess.BISHOP: 0.25,
            chess.ROOK: -0.25,
            chess.QUEEN: -0.25,
            chess.KING: -1
            }

commands = {"a": "Analyze", "p": "Play", "h": "Help", "q": "Quit"}


def log(string):
    logfile.write(str(string) + "\n")


def analyzemove(aboard, alpha, beta, max, depth):
    global moves_checked
    global verbose
    color = aboard.turn
    if verbose:
        log("\n\nAnalyzing " + str(color) + " at Depth: " + str(depth))
        log(aboard)
    all_moves = {}
    for move in aboard.legal_moves:
        # moves_checked += 1
        if (verbose):
            if depth == 0:
                log("Analyzing upper move: ^" + str(move))

        finalvalue = evaluatemove(aboard, move)

        # Runs next depth
        if depth < maxdepth:
            aboard.push(move)
            finalvalue += analyzemove(aboard, alpha, beta, max, depth + 1)[1]
            aboard.pop()

        all_moves[move] = finalvalue
    if depth < maxdepth:
        if verbose:
            log("\n\n\n##################################")
            log("SUMMARY OF DEPTH " + str(depth))
    if len(all_moves) == 0:
        bestMove = ("", 10)
    else:
        sortedMoves = sorted(all_moves.items(), key=lambda x: x[1], reverse=True)
        bestMove = sortedMoves[0]
        if verbose:
            log(sortedMoves)
            log("\n\nBest move " + str(bestMove[0]) + " had value of " + str(bestMove[1]))

    # When passing the best move's value upwards we need to sign it to benefit the above depth
    if (depth == 0):
        sign = 1
    else:
        sign = -1
    return (bestMove[0], sign * bestMove[1])



'''
def alphaBetaMax(alpha, beta, depthleft):
    if (depthleft == 0): return evaluate()
    for (all moves):
        score = alphaBetaMin(alpha, beta, depthleft - 1)
        if (score >= beta):
            return beta  # fail hard beta-cutoff
        if (score > alpha):
            alpha = score  # alpha acts like max in MiniMax
    return alpha


def alphaBetaMin(alpha, beta, depthleft)
    if (depthleft == 0): return -evaluate()
    for (all moves):
        score = alphaBetaMax(alpha, beta, depthleft - 1)
        if (score <= alpha):
            return alpha  # fail hard alpha-cutoff
        if (score < beta):
            beta = score  # beta acts like min in MiniMax
    return beta

'''


# Contains all evaluation logic for a given move on a board
def evaluatemove(board, move):
    color = board.turn
    movenum = board.fullmove_number
    finalvalue = 0
    movepiece = board.piece_at(move.from_square)

    # Points distribution
    # Capture
    if board.is_capture(move):

        if board.is_en_passant(move):
            piece = chess.PAWN
        else:
            piece = board.piece_at(move.to_square).piece_type
        if verbose:
            pass
            # log("Capture of value: " + str(pointsdict[piece]))
        finalvalue += pointsdict[piece]

    earlygain = (earlycurve_k * math.pow(earlycurve_base, -movenum + earlycurve_o))

    # Development
    if board == chess.WHITE:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_2))) or (
                move.from_square in chess.SquareSet(chess.BB_RANK_1)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            if verbose:
                # log("Applying development bonus of " + str(devbonusi))
                pass
            finalvalue += devbonusi
    if board == chess.BLACK:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_7))) or (
                move.from_square in chess.SquareSet(chess.BB_RANK_8)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            if verbose:
                pass
                # log("Applying development bonus of " + str(devbonusi))
            finalvalue += devbonusi

    # Center position
    if move.to_square in chess.SquareSet(chess.BB_CENTER):
        if verbose:
            pass
            # log("Applying center position bonus")
        finalvalue += earlygain * centerbonus

    # Check
    if board.gives_check(move):
        finalvalue += checkbonus

    if board.is_castling(move):
        finalvalue += castlebonus

    # Push move for the following points
    board.push(move)

    # Center attack
    if verbose & (len(chess.SquareSet(chess.BB_CENTER) & board.attacks(move.to_square)) > 0):
        pass
        # log("Applying center attack bonus of: " + str(earlygain * centerattackbonus * len(chess.SquareSet(chess.BB_CENTER) & aboard.attacks(move.to_square))))
    finalvalue += earlygain * centerattackbonus * len(
        chess.SquareSet(chess.BB_CENTER) & board.attacks(move.to_square))

    # Mates
    if board.is_checkmate():
        finalvalue += endbonus
    if board.is_stalemate():
        finalvalue -= endbonus
    if board.is_repetition():
        finalvalue -= 100

    # Pop back move after analysing
    board.pop()

    # Random variance
    finalvalue += (random.random() * random_mag) - (random_mag / 2)

    # Promotion
    if movepiece.piece_type == chess.PAWN:
        currank = chess.square_rank(move.from_square)
        if color == chess.WHITE and move.to_square in chess.SquareSet(chess.BB_RANK_8):
            if (verbose):
                pass
                # log("Applying promotion bonus")
            finalvalue += 8
        if color == chess.BLACK and move.to_square in chess.SquareSet(chess.BB_RANK_1):
            if (verbose):
                pass
                # log("Applying promotion bonus")
            finalvalue += 8

    return finalvalue



def Human(board):
    while True:
        move = input("Your turn to move: ")
        try:
            if move == "/e":
                return move
            move = board.parse_san(move)
            break
        except:
            print("Invalid or illegal move")
    return move


def LukasEngine(board):
    global moves_checked
    starttime = time.time()
    move = analyzemove(board, -10, 10, True, 0)[0]
    # log()(f'{moves_checked:,}' + " possible moves analysed!")
    # log()(f'{moves_checked / (time.time() - starttime):,}' " moves/second")
    moves_checked = 0
    return move


def PlayGame(player1, p1name, player2, p2name):
    pgnfile = open("lastgame.pgn", "w")
    board = chess.Board()
    starttime = time.time()
    print(board)
    game = chess.pgn.Game()
    game.headers["White"] = p1name
    game.headers["Black"] = p2name
    game.setup(board)
    node = game

    while not board.is_game_over(claim_draw=True):
        move = player1(board)
        if move == "/e":
            break
        node = node.add_variation(move)
        print("\n\nPlayer 1's Move: " + str(board.san(move)))
        board.push(move)
        print(board)

        move = player2(board)
        if move == "/e":
            break
        node = node.add_variation(move)
        print("\n\nPlayer 2's Move: " + str(board.san(move)))
        board.push(move)
        print(board)

    game.headers["Result"] = board.result()
    game.headers["Date"] = datetime.datetime.today().strftime('%Y-%m-%d')
    print("Game over! Result: " + board.result())
    print("Total time: " + str(time.time() - starttime) + " seconds")
    pgnfile.write(str(game))
    pgnfile.close()



def AnalyzeFen(fen):
    global verbose
    verbose = True
    board = chess.Board(fen)
    move = analyzemove(board, -10, 10, True, 0)[0]
    verbose = False



def StockFish(board):
    move = engine.play(board, chess.engine.Limit(time=0.05))
    return move.move


def ParsePlayer(string):
    if string == "h":
        return (Human, "Human")
    if string == "s":
        return (StockFish, "StockFish")
    if string == "l":
        return (LukasEngine, "LukasEngine")




if __name__ == "__main__":
    # Open engine and files
    engine = chess.engine.SimpleEngine.popen_uci("C:/Users/lvoze/stockfish_12_win_x64/stockfish_20090216_x64.exe")
    logfile = open("log.txt", "w")


    print("Welcome to Lukas's Chess Engine!")
    for item in commands:
        print(item + ": " + commands[item])
    # Main program loop
    while True:
        # Input loops
        while True:
            cmd = input(">")
            if cmd in commands:
                break
            else:
                print("Command not found")

        if cmd == "a":
            FEN = input("Enter FEN: ")
            depth = input("Enter Depth: ")
            print("Analyzing...")
            AnalyzeFen(FEN)
            print("Analysis complete.")

        elif cmd == "p":
            p1 = input("White player (h, l or s): ")
            p2 = input("Black player (h, l or s): ")
            if (p1 == "l") or (p2 == "l"):
                depth = input("Enter Depth: ")

            print("Starting game!")
            PlayGame(ParsePlayer(p1)[0], ParsePlayer(p1)[1], ParsePlayer(p2)[0], ParsePlayer(p2)[1])

        elif cmd == "h":
            for item in commands:
                print(item + ": " + commands[item])
        elif cmd == "q":
            break

    print("Quitting")
    logfile.close()
