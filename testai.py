import random
DEPTH = 5


def check_line(row, col, direction, board, ai_id):
    score_white = score_black = previous = 0
    multiplier = 1
    adjacency_loss = 1
    for i in range(DEPTH-1):
        try:
            board_score = board[row + (direction[0] * (i + 1))][col + (direction[1] * (i + 1))]
            if board_score != 0:
                if previous == board_score:
                    multiplier *= (1 + multiplier)
                else:
                    multiplier = 1
                    score_white = 0
                    score_black = 0
                if board_score == 1:    # black piece
                    if ai_id == 0:
                        score_white += 3.5 * multiplier - i
                    elif ai_id == 1:
                        score_black += 2 * multiplier**2 - i
                elif board_score == 2:  # white piece
                    if ai_id == 0:
                        score_black += 2 * multiplier**2 - i
                    elif ai_id == 1:
                        score_white += 3.5 * multiplier - i
                # if board[row + (direction[0] * (i+1))][col + (direction[1] * (i+1))] == 1:
                #     score_enemy += 2 * multiplier**2 - i
                # elif board[row + (direction[0] * (i+1))][col + (direction[1] * (i+1))] == 2:
                #     score_own += 3.5 * multiplier - i
                previous = board_score
            elif i == 0:
                adjacency_loss = 8
        except IndexError:
            break
        try:
            # Double the score if there is the same piece on the opposing direction
            if board[row + direction[0]][col + direction[1]] == board[row - direction[0]][col - direction[1]]:
                for i in range(DEPTH-1):
                    if board[row + (direction[0] * (i+1))][col + (direction[1] * (i+1))] == 1:
                        score_black += score_black
                    if board[row + (direction[0] * (i+1))][col + (direction[1] * (i+1))] == 2:
                        score_white += score_white
                    else:
                        break
        except IndexError:
            pass
    score_white = score_white / adjacency_loss
    score_black = score_black / adjacency_loss
    return int(score_white), int(score_black)


def evaluate_board(instance, ai_id):
    scores = {}
    board = instance.board
    grid_size = instance.GRID_SIZE
    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, 1), (-1, -1)]
    for row in range(grid_size):
        for col in range(grid_size):
            if board[row][col] != 0:
                pass
            else:
                score_own = score_enemy = 0
                try:
                    for i in range(len(directions)):
                        score_own_, score_enemy_ = check_line(row, col, directions[i], board, ai_id)
                        score_own += score_own_
                        score_enemy += score_enemy_
                except IndexError:
                    pass
                if score_own > score_enemy:
                    score = score_own
                else:
                    score = score_enemy
                if score < 0:
                    score = 0
                scores[(row, col)] = score
    return scores


def make_move(move, player, instance):
    row, col = move
    instance.board[row][col] = player


def get_available_moves(instance):
    moves = []
    for row in range(instance.GRID_SIZE):
        for col in range(instance.GRID_SIZE):
             if instance.board[row][col] == 0:
                 moves.append((row, col))
    return moves


def check_game_over(instance):
    for row in range(instance.GRID_SIZE):
        for col in range(instance.GRID_SIZE):
            if instance.board[row][col] == 0:
                return False
    return True


def ai_move(instance, ai_id):
    moves = get_available_moves(instance)
    scores = evaluate_board(instance, ai_id)
    max_score = max(scores.values())
    try:
        best_move = random.choice([k for k,v in scores.items() if v == max_score])
    except IndexError:
        best_move = random.choice(moves)
    # print(f"AI {ai_id}: Max score: {max_score}, best move:", best_move)
    return best_move
