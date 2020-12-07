import chess, random, time, math, chess.pgn, chess.engine, datetime

firstmovesdict = {}

openingmoves = ["e4"]

# Settings
random_mag = 0
centerbonus = 0.25
centerattackbonus = 0.5
checkbonus = 0.5
endbonus = 15
castlebonus = 0.5
kingmobilitypenalty = 0.25
captureimportant = 1.25

earlycurve_base = 1.2
earlycurve_k = 0.3
earlycurve_o = 7

depth_penalty = 0.95

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
devbonus = {chess.PAWN: 0.75,
            chess.KNIGHT: 0.5,
            chess.BISHOP: 0.5,
            chess.ROOK: -0.5,
            chess.QUEEN: -2,
            chess.KING: -2
            }

commands = {"a": "Analyze", "p": "Play", "h": "Help", "q": "Quit"}

kingtable_endgame = [
  -10,  -0.5,  -0.25,  -0.25,  -0.25, -0.25,  -0.5,  -10,
 -0.5,  -0.25,  -0.25,  -0.25,  -0.25,  -0.25,  -0.25, -0.5,
 -0.25,  -0.25,  -0.1,  -0.1,  0.1,  -0.1,  -0.25, -0.25,
 -0.25,  -0.25,  -0.1,  0,  0,  -0.1,  -0.25, -0.25,
 -0.25,  -0.25,  -0.1,  0,  0,  -0.1,  -0.25, -0.25,
 -0.25,  -0.25,  -0.1,  -0.1,  -0.1,  -0.1,  -0.25, -0.25,
  -0.5,  -0.25,  -0.25,  -0.25,  -0.25,  -0.25,   -0.25,  -0.5,
  -10,  -0.5,  -0.25,  -0.25,  -0.25,  -0.25,  -0.5, -10]


#def log(string):
    #logfile.write(str(string) + "\n")


def presort(board, movelist):
    return sorted(movelist, key=lambda x: "x" in board.san(x), reverse=True)


# Evaluates current board material for both colors. Slow invocation.
def evaluatematerial(board):
    whitemat = (pointsdict[chess.PAWN] * len(board.pieces(chess.PAWN, True))) \
            + (pointsdict[chess.QUEEN] * len(board.pieces(chess.QUEEN, True))) \
            + (pointsdict[chess.KNIGHT] * len(board.pieces(chess.KNIGHT, True))) \
            + (pointsdict[chess.ROOK] * len(board.pieces(chess.ROOK, True))) \
            + (pointsdict[chess.BISHOP] * len(board.pieces(chess.BISHOP, False)))
    blackmat = (pointsdict[chess.PAWN] * len(board.pieces(chess.PAWN, False))) \
            + (pointsdict[chess.QUEEN] * len(board.pieces(chess.QUEEN, False))) \
            + (pointsdict[chess.KNIGHT] * len(board.pieces(chess.KNIGHT, False))) \
            + (pointsdict[chess.ROOK] * len(board.pieces(chess.ROOK, False))) \
            + (pointsdict[chess.BISHOP] * len(board.pieces(chess.BISHOP, False)))
    return whitemat, blackmat


def abmax(board, move, alpha, beta, maximize, depthleft, material):
    if material is None:
        material = evaluatematerial(board)

    # If on last depth return just the evaluation of the given move
    if depthleft == 0:
        score = evaluatemove(board, move, material)
        if maximize:
            score = -score
        return move, score

    pushed = False
    if move is not None:
        thismovescore = evaluatemove(board, move, material)
        board.push(move)
        pushed = True
    else:
        thismovescore = None

    if board.legal_moves.count() == 0:
        board.pop()
        if move is not None:
            if maximize:
                thismovescore = -thismovescore
            return move, thismovescore
        else:
            return ("", 0)

    if maximize:
        maxScore = -10000
        for move in presort(board, board.legal_moves):
            #print("\nNow analyzing next upper move ^" + str(move))
            #print("Starting AB: " + str(alpha) + " " + str(beta))
            score = depth_penalty * abmax(board, move, alpha, beta, False, depthleft - 1, material)[1]
            if (thismovescore is not None):
                score -= thismovescore
            if not pushed:
                print("Results of upper move ^" + str(move) + " are " + str(score))
            if score > maxScore:
                bestmove = move
            maxScore = max(score, maxScore)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        if pushed:
            board.pop()
        return (bestmove, maxScore)
    else:
        minScore = 10000
        for move in presort(board, board.legal_moves):
            score = depth_penalty * abmax(board, move, alpha, beta, True, depthleft - 1, material)[1]
            if (thismovescore is not None):
                score += thismovescore
            if score < minScore:
                worstMove = move
            minScore = min(score, minScore)
            beta = min(beta, score)
            if beta <= alpha:
                break
        if pushed:
            board.pop()
        return worstMove, minScore


def evaluatelegalkingmoves(board):
    return len(list(filter(lambda x: "K" in board.san(x), board.legal_moves)))

# Point distribution of a move on a given board
def evaluatemove(board, move, material):
    color = board.turn
    movenum = board.fullmove_number
    finalvalue = 0
    movepiece = board.piece_at(move.from_square)
    piecemap = board.piece_map()
    endgame = (len(piecemap) < 10) or math.fabs(material[0] - material[1]) > 8
    originalmat = material

    # Points distribution
    # End game bonuses
    if endgame:
        # Evaluates king mobility
        if len(board.move_stack) > 1:
            lastmove = board.peek()
            board.pop()
            legalkingmoves = evaluatelegalkingmoves(board)
            board.push(lastmove)
        else:
            legalkingmoves = None

        # End game pawn bonus
        if movepiece.piece_type == chess.PAWN:
            if color:
                distance = 8 - chess.square_rank(move.to_square)
            else:
                distance = chess.square_rank(move.to_square)
            finalvalue += 8 / ((distance * distance) + 1)

        # Incentivise moving king towards other pieces
        if movepiece.piece_type == chess.KING:
            xavg = 0
            yavg = 0
            i = 0
            for piece in piecemap:
                if piecemap[piece].color == board.turn:
                    xavg += chess.square_rank(piece)
                    yavg += chess.square_file(piece)
                    i += 1
            if i > 1:
                xavg = xavg / i
                yavg = yavg / i

                tocenterx = xavg - chess.square_rank(move.from_square)
                tocentery = yavg - chess.square_file(move.from_square)
                movedirectionx = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
                movedirectiony = chess.square_file(move.to_square) - chess.square_file(move.from_square)
                totalgain = (tocenterx * movedirectionx) + (tocentery * movedirectiony)
                totalgain *= 0.5
                #print("Total king close gain: " + str(totalgain))
                finalvalue += totalgain


    # Capture
    if board.is_capture(move):
        if board.is_en_passant(move):
            piece = chess.PAWN
        else:
            piece = board.piece_at(move.to_square).piece_type
        finalvalue += captureimportant * pointsdict[piece]

        # Pawns worth way more in endgame depending on closeness to end
        if piece == chess.PAWN and endgame:
            finalvalue += 8

        # If there was a capture, re-evaluate material
        material = evaluatematerial(board)

    if color:
        mymat = material[0]
        opmat = material[1]
    else:
        mymat = material[1]
        opmat = material[0]

    earlygain = (earlycurve_k * math.pow(earlycurve_base, -movenum + earlycurve_o))

    # Development
    if color == chess.WHITE:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_2))) or (move.from_square in chess.SquareSet(chess.BB_RANK_1)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            finalvalue += devbonusi
    if color == chess.BLACK:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_7))) or (move.from_square in chess.SquareSet(chess.BB_RANK_8)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            finalvalue += devbonusi

    # Center position
    if move.to_square in chess.SquareSet(chess.BB_CENTER):
        finalvalue += earlygain * centerbonus

    # Check
    givescheck = board.gives_check(move)
    if givescheck:
        finalvalue += checkbonus

    if board.is_castling(move):
        finalvalue += castlebonus

    if endgame:
        if board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
            if mymat > opmat:
                finalvalue -= 100
            else:
                finalvalue += 100


        # If I have less material, punish my kings movements based on the king mating table
        if mymat < opmat and movepiece == chess.KING:
            # Add king table value
            kingtablevalue = kingtable_endgame[move.to_square]
            finalvalue += kingtablevalue

    # Push move for the following points
    board.push(move)

    if endgame:
        if board.is_fivefold_repetition():
            if mymat > opmat:
                finalvalue -= 100
            else:
                finalvalue += 100

        if legalkingmoves is not None:
            currentlegalkingmoves = evaluatelegalkingmoves(board)
            mobilityless = kingmobilitypenalty * max(legalkingmoves - currentlegalkingmoves, 0)
            finalvalue -= mobilityless

    # Center attack
    finalvalue += earlygain * centerattackbonus * len(chess.SquareSet(chess.BB_CENTER) & board.attacks(move.to_square))

    # Checkmate
    if board.is_checkmate():
        if givescheck:
            finalvalue += 100
        else:
            finalvalue -= 100

    # Stalemate and draws. Value depends on who's winning
    if board.is_stalemate() or board.is_insufficient_material():
        if mymat > opmat:
            finalvalue -= 100
        else:
            finalvalue += 100

    if endgame:
        if board.is_repetition():
            if mymat > opmat:
                finalvalue -= 100
            else:
                finalvalue += 100

    # Pop back move after analysing
    board.pop()

    # Random variance
    finalvalue += (random.random() * random_mag) - (random_mag / 2)

    # Promotion
    if move.promotion is not None:
        finalvalue += pointsdict[move.promotion]

    material = originalmat
    #print("Analysis of move " + str(move) + " for " + str(color) + " has value " + str(finalvalue))
    return finalvalue


def Human(board, depth):
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


def LukasEngine(board, depth):
    global moves_checked
    starttime = time.time()
    # If white, pick a random first move from the list
    if board.fullmove_number == 1 and board.turn:
        move = board.parse_san(openingmoves[random.randrange(0, len(openingmoves), 1)])
    else:
        move = abmax(board, None, -10000, 10000, True, int(depth), None)[0]
    # log()(f'{moves_checked:,}' + " possible moves analysed!")
    # log()(f'{moves_checked / (time.time() - starttime):,}' " moves/second")
    moves_checked = 0
    return move


def PlayGame(player1, p1name, p1depth, player2, p2name, p2depth, startingpos):
    pgnfile = open("lastgame.pgn", "w")
    board = chess.Board(startingpos)
    starttime = time.time()
    print(board)
    game = chess.pgn.Game()
    game.headers["White"] = p1name
    game.headers["Black"] = p2name
    game.setup(board)
    node = game

    while not board.is_game_over(claim_draw=True):
        if board.is_game_over():
            break
        move = player1(board, p1depth)
        if move == "/e":
            break
        node = node.add_variation(move)
        print("\n\nPlayer 1's Move: " + str(board.san(move)))
        board.push(move)
        print(board)

        if board.is_game_over():
            break
        move = player2(board, p2depth)
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


def AnalyzeFen(fen, depth):
    global verbose
    verbose = True
    board = chess.Board(fen)
    print(board)
    results = abmax(board, None, -10000, 10000, True, int(depth), None)
    print("\n\n")
    print(results)
    verbose = False


def StockFish(board, depth):
    move = engine.play(board, chess.engine.Limit(depth=int(depth)))
    return move.move


def ParsePlayer(string, depth=None):
    if string == "h":
        return (Human, "Human")
    if string == "s":
        return (StockFish, "StockFish Depth " + str(depth))
    if string == "l":
        return (LukasEngine, "LukasEngine Depth " + str(depth))


if __name__ == "__main__":
    # Open stockfish and log file
    engine = chess.engine.SimpleEngine.popen_uci("C:/Users/lvoze/stockfish_12_win_x64/stockfish_20090216_x64.exe")
    #logfile = open("log.txt", "w")

    # Intro messages
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
            AnalyzeFen(FEN, depth)
            print("Analysis complete.")

        elif cmd == "p":
            depth1 = 0
            depth2 = 0
            print("Please enter player configuration. (h)uman, (l)ukasengine or (s)tockfish")

            p1 = input("White: ")
            if (p1 == "l" or p1 == "s"):
                depth1 = input("Enter Depth for p1: ")

            p2 = input("Black: ")
            if (p2 == "l" or p2 == "s"):
                depth2 = input("Enter Depth for p2: ")

            startingpos = input("Starting position (blank for default): ")
            if startingpos == "":
                startingpos = chess.STARTING_FEN

            PlayGame(ParsePlayer(p1, depth1)[0], ParsePlayer(p1, depth1)[1], depth1, ParsePlayer(p2, depth2)[0], ParsePlayer(p2, depth2)[1], depth2, startingpos)

        elif cmd == "h":
            for item in commands:
                print(item + ": " + commands[item])
        elif cmd == "q":
            break

    print("Quitting")
    engine.quit()
    #logfile.close()
