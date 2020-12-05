import chess, random, time, math, chess.pgn, chess.engine, datetime

firstmovesdict = {}

# Settings
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
            chess.QUEEN: -1,
            chess.KING: -2
            }

commands = {"a": "Analyze", "p": "Play", "h": "Help", "q": "Quit"}


def log(string):
    logfile.write(str(string) + "\n")


def presort(board, movelist):
    return sorted(movelist, key=lambda x: "x" in board.san(x), reverse=True)


def analyzemove(board, move, alpha, beta, maximize, depthleft):
    # If on last depth return just the evaluation of the given move
    if depthleft == 0:
        score = evaluatemove(board, move)
        if maximize:
            score = -score
        return (move, score)

    pushed = False
    if move is not None:
        thismovescore = evaluatemove(board, move)
        board.push(move)
        pushed = True
    else:
        thismovescore = None

    if board.legal_moves.count() == 0:
        board.pop()
        return (move, -1000)

    if maximize:
        maxScore = -10000
        for move in presort(board, board.legal_moves):
            score = analyzemove(board, move, alpha, beta, False, depthleft-1)[1]
            if (thismovescore is not None):
                score -= thismovescore
            if score > maxScore:
                bestmove = move
            maxScore = max(score, maxScore)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        if pushed:
            board.pop()
        return (bestmove, maxScore)
    else:
        minScore = 10000
        for move in presort(board, board.legal_moves):
            score = analyzemove(board, move, alpha, beta, True, depthleft-1)[1]
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
        return (worstMove, minScore)



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
        finalvalue += pointsdict[piece]

    earlygain = (earlycurve_k * math.pow(earlycurve_base, -movenum + earlycurve_o))

    # Development
    if color == chess.WHITE:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_2))) or (move.from_square in chess.SquareSet(chess.BB_RANK_1)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            finalvalue += devbonusi
    if color == chess.BLACK:
        if (movepiece.piece_type == chess.PAWN and (move.from_square in chess.SquareSet(chess.BB_RANK_7))) or (
                move.from_square in chess.SquareSet(chess.BB_RANK_8)):
            devbonusi = earlygain * devbonus[movepiece.piece_type]
            finalvalue += devbonusi

    # Center position
    if move.to_square in chess.SquareSet(chess.BB_CENTER):
        finalvalue += earlygain * centerbonus

    # Check
    if board.gives_check(move):
        finalvalue += checkbonus

    if board.is_castling(move):
        finalvalue += castlebonus

    # Push move for the following points
    board.push(move)

    # Center attack
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
            finalvalue += 8
        if color == chess.BLACK and move.to_square in chess.SquareSet(chess.BB_RANK_1):
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


def LukasEngine(board, depth):
    global moves_checked
    starttime = time.time()
    move = analyzemove(board, None, -10, 10, True, int(depth))[0]
    # log()(f'{moves_checked:,}' + " possible moves analysed!")
    # log()(f'{moves_checked / (time.time() - starttime):,}' " moves/second")
    moves_checked = 0
    return move


def PlayGame(player1, p1name, p1depth, player2, p2name, p2depth):
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
    results = analyzemove(board, None, -10000, 10000, True, int(depth))
    print("\n\n")
    print(results)
    verbose = False


def StockFish(board, depth):
    move = engine.play(board, chess.engine.Limit(time=0.01))
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
            depth1 = 0
            depth2 = 0
            p1 = input("White player (h, l or s): ")
            if (p1 == "l"):
                depth1 = input("Enter Depth for p1: ")
            p2 = input("Black player (h, l or s): ")
            if (p2 == "l"):
                depth2 = input("Enter Depth for p2: ")

            print("Starting game!")
            PlayGame(ParsePlayer(p1)[0], ParsePlayer(p1)[1], depth1, ParsePlayer(p2)[0], ParsePlayer(p2)[1], depth2)

        elif cmd == "h":
            for item in commands:
                print(item + ": " + commands[item])
        elif cmd == "q":
            break

    print("Quitting")
    engine.quit()
    logfile.close()
