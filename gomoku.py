
from calendar import c
import operator
import time
import pygame
from torch.serialization import get_default_load_endianness
from music import start_muziek_vertraagd
import testai
import ai
import random
import stats
import numpy as np
import filereader
from threading import Thread
from time import sleep
from detect_pieces import *
import os

window_name = "Gomoku"
victory_text = ""
mark_last_move_model = True
 
#instructie: druk op de linkermuisknop wanneer je een zet hebt gedaan op het fysiek bord.

class GomokuGame:
    def __init__(self, values):
        self.GRID_SIZE = values[1]
        self.WIDTH = self.HEIGHT = self.GRID_SIZE * values[0]
        self.CELL_SIZE = self.WIDTH // self.GRID_SIZE
        self.P1COL = values[2]
        self.P2COL = values[3]
        self.BOARD_COL = values[4]
        self.LINE_COL = values[5]
        self.SLEEP_BEFORE_END = values[6]
        self.board = [[0] * self.GRID_SIZE for _ in range(self.GRID_SIZE)] # 0 = empty, 1 = player 1, 2 = player 2. De waarden corresponderen aan de kleuren.
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.winning_cells = []
        self.current_game = 0
        self.last_round = False
        self.ai_delay = False
        self.use_recognition=False
        self.play_music = False
        
    def set_board(self, board):
        self.board = board


class Player:
    def __init__(self, player_type, player_id):    
        #Initialize a Player object with the given player type and ID.
        self.TYPE = str(player_type) #type can be human, testai or AI-Model
        self.id = int(player_id) #id can be 1 or 2
        self.moves = 0
        self.wins = 0
        self.losses = 0
        self.score = 0
        self.sum_score = 0
        self.avg_score = 0
        self.all_moves = []
        self.avg_moves = 0
        self.weighed_scores = []
        self.score_loss = []
        self.weighed_moves = []
        self.move_loss = []
        self.final_move_scores = []
        self.final_move_loss = []
        self.win_rate = 0
        self.ai = ai.GomokuAI()
        self.allow_overrule = True
        self.final_action = None
        self.model_name=None
        

    def __str__(self) -> str:
        return f"Player{self.id},(type={self.TYPE}, model={self.model_name})"

    def set_player_type(self, player_type):
        self.TYPE = str(player_type) #type can be human, AI-Model or Test Algorithm
        
    def get_player_type(self):
        return self.TYPE
        
    def set_player_id(self, player_id):
        self.id = int(player_id) #id can be 1 or 2 corresponding to human or AI
    
    def get_player_id(self):
        return self.id

    def calculate_score(self, max_score, is_winner, game_number):
        if max_score > 0:
            if is_winner:
                self.score = (max_score - self.moves) / max_score
            else:
                self.score = -((max_score - self.moves) / max_score)
            # weighed_score = self.score / max_score
            self.weighed_scores.append(self.score)
        else:
            self.score = 0
            self.weighed_scores.append(0)
        print(f"score: {self.score}")
        self.sum_score += self.score
        self.avg_score = self.sum_score / game_number
        self.all_moves.append(self.moves)
        self.avg_moves = sum(self.all_moves) / len(self.all_moves)

    def calculate_win_rate(self, rounds):
        self.win_rate = self.wins / rounds

    def reset_score(self):
        self.score = 0
        self.moves = 0
        self.weighed_moves = []
        self.move_loss = []

    def reset_all_stats(self): #purely for testing purposes
        self.moves = 0
        self.wins = 0
        self.losses = 0
        self.score = 0
        self.sum_score = 0
        self.avg_score = 0
        self.weighed_scores = []
        self.score_loss = []
        self.all_moves = []
        self.weighed_moves = []
        self.move_loss = []
        self.final_move_scores = []
        self.final_move_loss = []
        self.avg_moves = 0
        
    def load_model(self, model):
        self.model_name = model
        self.ai.model.load_model(model)
        
    def get_model_name(self):
        return self.model_name
        
    def set_allow_overrule(self, allow_overrule):
        self.allow_overrule = allow_overrule
        self.ai.set_allow_overrule(allow_overrule)#ai=GomokuAI
        return self.id

# Set default player types. Can be changed on runtime (buttons in GUI)
player1 = Player("Human", 1)
player2 = Player("Human", 2)
players = [player1, player2]
current_player = player1


def logging_players():
    print("Logging players")
    print("Player 1 : " + str(player1.get_player_id()))
    print("Player 1 : " + str(player1.TYPE))   
    print("Player 2 : " + str(player2.get_player_id()))
    print("Player 2 : " + str(player2.TYPE))
    print("Current player : " + str(current_player.get_player_id()))

def reset_player_stats():
    for i in range(len(players)):
        players[i].reset_score()

# Update win / loss stats of players: -1 = tie; 1 = player 1 won; 2 = player 2 won
def update_player_stats(instance, winning_player): 
    global players
    if winning_player > -1: # run if game was not a tie
        for i in range(len(players)):
            if i == winning_player-1:
                players[i].wins += 1
                is_winner = True
            else:
                players[i].losses += 1
                is_winner = False
            players[i].calculate_score(instance.GRID_SIZE ** 2, is_winner, instance.current_game)
            if instance.last_round:
                players[i].calculate_win_rate(instance.current_game)
    else:
        for i in range(len(players)):
            players[i].calculate_score(0, False, instance.current_game)
    stats.log_win(players)
    if instance.last_round:
        stats.log_message(f"\nStatistics:\n{players[0].TYPE} {players[0].id}:\nwins: {players[0].wins} - win rate: {players[0].win_rate} - average score: {players[0].avg_score} - weighed score: {sum(players[0].weighed_scores)/len(players[0].weighed_scores)} - average moves: {players[0].avg_moves}.\n"
                          f"{players[1].TYPE} {players[1].id}:\nwins: {players[1].wins} - win rate: {players[1].win_rate} - average score: {players[1].avg_score} - weighed score: {sum(players[1].weighed_scores)/len(players[1].weighed_scores)} - average moves: {players[1].avg_moves}.")



def is_move_model(row,col,last_move_model) -> bool:
    if (row,col)==last_move_model:
        return True
    else:
        return False

# Function to draw the game board
def draw_board(instance,last_move_model=None):
    global mark_last_move_model
    instance.screen.fill(instance.BOARD_COL)#background color
    cell_size = instance.CELL_SIZE#cell_size=30
    radius_big_circle=cell_size//2 - 5#radius_big_circle=15
    radius_small_circle=cell_size//3 - 5#radius_small_circle=10
    red=(255,0,0) #R=255, G=0, B=0
    for row in range(instance.GRID_SIZE):#grid_size=15
        for col in range(instance.GRID_SIZE):
            pygame.draw.rect(instance.screen, instance.LINE_COL, (col * cell_size, row * cell_size, cell_size, cell_size), 1)

            if instance.board[row][col] == 1:
                if is_move_model(row,col,last_move_model) and mark_last_move_model:
                    #red (R,G,B)
                    pygame.draw.circle(instance.screen, instance.P1COL, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_big_circle)
                    pygame.draw.circle(instance.screen, red, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_small_circle)
                else:
                    pygame.draw.circle(instance.screen, instance.P1COL, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_big_circle)

            elif instance.board[row][col] == 2:
                if is_move_model(row,col,last_move_model) and mark_last_move_model:
                    #red (R,G,B)
                    pygame.draw.circle(instance.screen, instance.P2COL, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_big_circle)
                    pygame.draw.circle(instance.screen, red, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_small_circle)
                else:
                    pygame.draw.circle(instance.screen, instance.P2COL, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), radius_big_circle)

    # Draw the winning line
    if instance.winning_cells:
        start_row, start_col = instance.winning_cells[0]#start_cell=(0,0)
        end_row, end_col = instance.winning_cells[-1]#end_cell=(15,15)
        pygame.draw.line(instance.screen, (0, 255, 0),
                         (start_col * cell_size + cell_size // 2, start_row * cell_size + cell_size // 2),
                         (end_col * cell_size + cell_size // 2, end_row * cell_size + cell_size // 2), 5)

def reset_game(instance):
    global current_player
    instance.board = [[0] * instance.GRID_SIZE for _ in range(instance.GRID_SIZE)]
    current_player = player1

def calculate_score(board: tuple, board_size=15):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]#richtingen om te controleren of er 5 stukkenp een rij zijn.
    score_board = filereader.load_scores("consts.json")
    scored_board = np.zeros((board_size, board_size))
    for row in range(len(board[0])):
        for col in range(len(board[1])):
            adjacent_tiles = {}
            tiles = {}
            if board[row][col] == 0:
                for i in range(len(directions)):
                    forward = []
                    for j in range(5):
                        try:
                            forward.append(board[row + ((j + 1) * directions[i][0])][col + ((j + 1) * directions[i][1])])
                        except IndexError:
                            break
                    tiles[directions[i]] = forward
                adjacent_tiles[(row, col)] = tiles
            else:
                adjacent_tiles[(row, col)] = -1
            total_score = 0
            try:
                for id, values in adjacent_tiles.items():
                    directions = list(values.keys())
                    for i in range(0, len(directions), 2):  # Iterate in pairs (opposing directions)
                        dir1, dir2 = directions[i], directions[i + 1]
                        line1, line2 = values[dir1], values[dir2]
                        score1 = 0
                        score2 = 0
                        first = 0
                        # Convert line so that the first non-zero cell is 1 and any opposing non-zero number is 2
                        for j in range(len(line1)):
                            try:
                                if first == 0 and line1[j] > 0:
                                    first = line1[j]
                                if line1[j] > 0:
                                    if line1[j] == first:
                                        line1[j] = 1
                                    else:
                                        line1[j] = 2
                            except IndexError:
                                break
                        first = 0
                        for k in range(len(line2)):
                            try:
                                if first == 0 and line2[k] > 0:
                                    first = line2[k]
                                if line2[k] > 0:
                                    if line2[k] == first:
                                        line2[k] = 1
                                    else:
                                        line2[k] = 2
                            except IndexError:
                                break
                        lines = [str(line1), str(line2)]
                        for category in score_board:
                            for key in category.keys():
                                for item in category[key]:
                                    for l in range(len(lines)):
                                        if lines[l] in item:
                                            if l == 0:
                                                score1 += item[lines[l]]
                                            else:
                                                score2 += item[lines[l]]
                        if score1 > 0 and score2 > 0:
                            total_score += (score1 + score2)
                        else:
                            total_score += (score1 + score2)
            except AttributeError:
                total_score = -1
            scored_board[row][col] = total_score
    scores_normalized = []
    max_score = int(np.amax(scored_board))
    scored_board_flat = scored_board.flatten()
    # normalize the score for ai training purposes
    for i in range(len(scored_board_flat)):
        new_normalized_score = 0
        if max_score > 0:
            new_normalized_score = (scored_board_flat[i] / (max_score / 2) - 1)
        if new_normalized_score < 0:
            new_normalized_score = 0
        scores_normalized.append(new_normalized_score)
    return max_score, scored_board, scores_normalized#return de hoogste score, het board met scores, de scores genormaliseerd

def check_win(row, col, playerID, instance):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for drow, dcol in directions:
        winning_cells = [(row, col)]
        winning_direction = ()
        count = 1
        # positive direction
        for i in range(1, 5):
            row_, col_ = row + i * drow, col + i * dcol
            if 0 <= row_ < instance.GRID_SIZE and 0 <= col_ < instance.GRID_SIZE and instance.board[row_][col_] == playerID:
                count += 1
                winning_cells.append((row_, col_))
                winning_direction = [(drow, dcol)]
            else:
                break
        # negative direction
        for i in range(1, 5):
            row_, col_ = row - i * drow, col - i * dcol
            if 0 <= row_ < instance.GRID_SIZE and 0 <= col_ < instance.GRID_SIZE and instance.board[row_][col_] == playerID:
                count += 1
                winning_cells.append((row_, col_))
                winning_direction = (drow, dcol)
            else:
                break
        if count >= 5:  # Victory condition 
            match winning_direction:    # sort the array so that a strike can be drawn correctly
                case (1, 0): #if winning_direction==(1,0):
                    winning_cells.sort()
                case(0, 1):#if winning_direction==(0,1):
                    winning_cells.sort(key=lambda i: i[1])
                case(1, 1):#if winning_direction==(1,1):
                    winning_cells.sort(key=operator.itemgetter(0, 1))
                case(1, -1):#if winning_direction==(1,-1):
                    winning_cells.sort(key=operator.itemgetter(0, 1), reverse=True)
            instance.winning_cells = winning_cells
            return True
    return False

def check_board_full(instance):# checkt of het bord vol is
    board = instance.board
    grid_size = instance.GRID_SIZE
    for row in range(grid_size):
        for col in range(grid_size):
            if board[row][col] == 0:
                return False
    return True

def convert_to_one_hot(board, player_id):#vermijd dat ai denkt dat de getallen iets betekenen.
    board = np.array(board)
    height, width = board.shape
    one_hot_board = np.zeros((3, height, width), dtype=np.float32)
    one_hot_board[0] = (board == 0).astype(np.float32)
    if player_id == 1:
        one_hot_board[1] = (board == 1).astype(np.float32)  # AI's pieces as Player 1
        one_hot_board[2] = (board == 2).astype(np.float32)  # Enemy's pieces as Player 2
    else:
        one_hot_board[1] = (board == 2).astype(np.float32)  # AI's pieces as Player 2
        one_hot_board[2] = (board == 1).astype(np.float32)
    return one_hot_board

def refresh_screen(game_number, current_player):
    pygame.display.flip()#refresh
    window_name = "Game: " + str(game_number) + " - " + str(current_player) #beurt start
    pygame.display.set_caption(window_name)

def handle_human_move(instance, x, y, record_replay, players,p1_moves=None, p2_moves=None):
    global victory_text, winning_player, running,current_player
    col = x // instance.CELL_SIZE 
    row = y // instance.CELL_SIZE
    if instance.GRID_SIZE > row >= 0 == instance.board[row][col] and 0 <= col < instance.GRID_SIZE:
        instance.board[row][col] = current_player.get_player_id()
        if current_player.get_player_id() == 1 and record_replay:
            p1_moves.append((row, col))
        elif record_replay:
            p2_moves.append((row, col))
        players[current_player.get_player_id() - 1].moves += 1
        if check_win(row, col, current_player.get_player_id(), instance):
            victory_text = f"Player {current_player.get_player_id()} wins!"
            winning_player = current_player.get_player_id()
            running = False
        else:
            logging_players()
            if instance.play_music:
                Thread(target=start_muziek_vertraagd).start()

            # Switch player if neither player have won
            current_player = players[2 - current_player.get_player_id()]  #current_player kan 2 zijn of 1, maar in beide gevallen zal er van speler gewisseld worden.
            logging_players()    

def add_hover_effect(instance):
    ## adds hover effects to cells when mouse hovers over them##
    mouse_pos = pygame.mouse.get_pos()
    x,y = mouse_pos
    col = x // instance.CELL_SIZE
    row = y // instance.CELL_SIZE
    HOVER_COLOR = (211, 211, 211)
    if instance.GRID_SIZE > row >= 0 == instance.board[row][col] and 0 <= col < instance.GRID_SIZE:
        if instance.board[row][col] == 0:#cell is empty
            cell_size = instance.CELL_SIZE
            pygame.draw.circle(instance.screen, HOVER_COLOR, (col * cell_size + cell_size // 2, row * cell_size + cell_size // 2), cell_size // 2 - 5)
            pygame.display.flip()
            sleep(0.1)#otherwise it will be flashing uncontrollably

def runGame(instance, game_number, record_replay):#main function
    # Main game loop
    global window_name, victory_text, current_player, player1, player2, running,current_player,p1_moves, p2_moves
    if instance.use_recognition:
        print("using recognition")
    else:
        print("not using recognition")
    if player1.TYPE=="AI-Model":
        if player1.allow_overrule:
            print("Overruling is allowed for player 1")
        else:
            print("Overruling is not allowed for player 1")
    if player2.TYPE=="AI-Model":
        if player2.allow_overrule:
            print("Overruling is allowed for player 2")
        else:
            print("Overruling is not allowed for player 2")

    pygame.display.set_icon(pygame.image.load('res/ico.png'))
    pygame.init()
    pygame.display.set_caption(window_name)
    mark_last_move_model=True
    instance.winning_cells = []
    running = True
    winning_player = 0

    if record_replay:
        p1_moves = []
        p2_moves = []

    while running:
        if not check_board_full(instance):
            # Human move
            if current_player.TYPE == "Human":
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False 
                        #druk op linkermuisknop om te zetten
                    elif (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.K_UP or event.type == pygame.K_RIGHT) and event.button == 1: #kan zo gelaten worden. Wanneer op de muis wordt gedrukt,wordt de zet gelezen van het bestand
                        if instance.play_music:
                            Thread(target=lambda:pygame.mixer.music.fadeout(1000)).start()#don't block the main thread

                        if instance.use_recognition:
                            schrijf_relevante_stukken_na_zet_weg()
                            (x,y)=recognize_move()
                            schrijf_relevante_stukken_voor_zet_weg()
                            if (x,y) is None:
                                continue #don't do anything
                        else:
                            x,y=event.pos
                        try:
                            handle_human_move(instance, x, y, record_replay, players, p1_moves, p2_moves) 
                        except Exception as e:
                            handle_human_move(instance, x, y, record_replay, players)
                            
                add_hover_effect(instance)

            # test algorithm move
            elif current_player.TYPE == "Test Algorithm" and not testai.check_game_over(instance):
                if instance.ai_delay:
                    time.sleep(random.uniform(0.25, 1.0))   # randomize ai "thinking" time
                ai_row, ai_col = testai.ai_move(instance, players[current_player.get_player_id()-1].id)
                testai.make_move((ai_row, ai_col), current_player.get_player_id(), instance)
                players[current_player.get_player_id()-1].moves += 1
                if current_player.get_player_id() == 1 and record_replay:
                    p1_moves.append((ai_row, ai_col))
                elif record_replay:
                    p2_moves.append((ai_row, ai_col))

                if check_win(ai_row, ai_col, current_player.get_player_id(), instance):
                    victory_text = f"AI-Model {players[current_player.get_player_id()-1].id} wins!"
                    winning_player = current_player.get_player_id()
                    running = False
                else:
                    current_player = players[2 - current_player.get_player_id()]
                    logging_players()   
            
            # AI model
            elif current_player.TYPE == "AI-Model":
                if instance.ai_delay:
                    time.sleep(random.uniform(0.25, 1.0))   # randomize AI "thinking" time
                one_hot_board = convert_to_one_hot(instance.board, players[current_player.get_player_id()-1].id)
                mm_ai = players[current_player.get_player_id()-1].ai#player1.ai or player2.ai #always an instance of GomokuAI
                mm_ai.set_game(one_hot_board)
                max_score, scores, scores_normalized = calculate_score(instance.board)
                mm_ai.current_player_id=current_player.get_player_id()
                action = mm_ai.get_action(instance.board, one_hot_board, scores_normalized)
               
                np_scores = np.array(scores).reshape(15, 15)
                short_score = np_scores[action[0]][action[1]]
                if mark_last_move_model:
                    last_move_model=action #=last move for example :(3,6)
                else:
                    last_move_model=None
                if max_score <= 0:
                    # prevent division with negative values or zero
                    score = 0
                else:
                    score = short_score / max_score
                if current_player.get_player_id() == 1 and record_replay:
                    p1_moves.append(action)
                elif record_replay:
                    p2_moves.append(action)
                players[current_player.get_player_id() - 1].weighed_moves.append(score)
                instance.board[action[0]][action[1]] = current_player.get_player_id()
                game_over = check_win(action[0], action[1], current_player.get_player_id(), instance)
                players[current_player.get_player_id()-1].final_action = action
                players[current_player.get_player_id() - 1].moves += 1
                if game_over:
                    victory_text = f"AI-Model {players[current_player.get_player_id() - 1].id} wins!"
                    winning_player = current_player.get_player_id()
                    running = False
                else:
                    current_player = players[2 - current_player.get_player_id()]
                    print("Na switch player AI!!!!!!!!!!!")
                    logging_players()    
            try:
                draw_board(instance,last_move_model)
            except :
                draw_board(instance)

            refresh_screen(game_number, current_player)
                
        else:
            victory_text = "TIE"
            winning_player = -1
            running = False

    # End game
    stats.log_message(victory_text)
    pygame.display.set_caption("Gomoku - Game: " + str(game_number) + " - " + victory_text)
    update_player_stats(instance, winning_player)
    if record_replay:
        filereader.save_replay(p1_moves, p2_moves)
    
    time.sleep(instance.SLEEP_BEFORE_END)#sleep before closing for SLEEP_BEFORE_END seconds
    reset_game(instance)



def handle_events():
    if not player1.TYPE == "Human" and  not player2.TYPE == "Human":
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
def runTraining(instance, game_number, record_replay):#main function
    # Main game loop
    global window_name, victory_text, current_player,player1,player2,running
    mark_last_move_model=False 
    for p in players: #players=[Human, AI]
        if p.TYPE == "AI-Model":
            if p==player1:
                p.ai.model.load_model(player1.model_name)
            else:
                p.ai.model.load_model(player2.model_name)
            p.ai.train = True
        if p.TYPE == "Human":
            p.ai.train = False
            mark_last_move_model=True


    instance.play_music=False
    pygame.display.set_icon(pygame.image.load('res/ico.png'))
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (300,200)

    pygame.init()
    pygame.display.set_caption(window_name)
    instance.winning_cells = []
    running = True
    winning_player = 0

    if record_replay:
        p1_moves = []
        p2_moves = []

    while running:
        
        handle_events()
        # Check if board is full    
        if not check_board_full(instance):
            # Human move
            if current_player.TYPE == "Human":
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False 
                        #druk op linkermuisknop om te zetten
                    elif (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.K_UP or event.type == pygame.K_RIGHT) and event.button == 1: #kan zo gelaten worden. Wanneer op de muis wordt gedrukt,wordt de zet gelezen van het bestand
                        Thread(target=lambda:pygame.mixer.music.fadeout(1000)).start()#don't block the main thread
                        x,y=event.pos
                        try:
                            handle_human_move(instance, x, y, record_replay, players, p1_moves, p2_moves) 
                        except:
                            handle_human_move(instance, x, y, record_replay, players)
            # test algorithm
            elif current_player.TYPE == "Test Algorithm" and not testai.check_game_over(instance):
                if instance.ai_delay:
                    time.sleep(random.uniform(0.25, 1.0))   # randomize ai "thinking" time
                ai_row, ai_col = testai.ai_move(instance, players[current_player.get_player_id()-1].id)
                testai.make_move((ai_row, ai_col), current_player.get_player_id(), instance)
                players[current_player.get_player_id()-1].moves += 1
                if current_player.get_player_id() == 1 and record_replay:
                    p1_moves.append((ai_row, ai_col))
                elif record_replay:
                    p2_moves.append((ai_row, ai_col))
                if check_win(ai_row, ai_col, current_player.get_player_id(), instance):
                    victory_text = f"AI-Model {players[current_player.get_player_id()-1].id} wins!"
                    winning_player = current_player.get_player_id()
                    running = False
                else:
                    current_player = players[2 - current_player.get_player_id()]
                    logging_players()   
            
            # AI-Model
            elif current_player.TYPE == "AI-Model":
                if instance.ai_delay:
                    time.sleep(random.uniform(0.25, 1.0))   # randomize AI "thinking" time
                one_hot_board = convert_to_one_hot(instance.board, players[current_player.get_player_id()-1].id)
                handle_events()
                mm_ai = players[current_player.get_player_id()-1].ai
                mm_ai.set_game(one_hot_board)
                old_state = instance.board
                handle_events()
                max_score, scores, scores_normalized = calculate_score(instance.board)
                mm_ai.current_player_id=current_player.get_player_id()
                pygame.event.get()
                action = mm_ai.get_action(instance.board, one_hot_board, scores_normalized)
                if mark_last_move_model:
                    last_move=action #=last move for example :(3,6)
                else:
                    last_move=None
                np_scores = np.array(scores).reshape(15, 15)
                short_score = np_scores[action[0]][action[1]]
                if max_score <= 0:
                    # prevent division with negative values or zero
                    score = 0
                else:
                    score = short_score / max_score
                if current_player.get_player_id() == 1 and record_replay:
                    p1_moves.append(action)
                elif record_replay:
                    p2_moves.append(action)
                players[current_player.get_player_id() - 1].weighed_moves.append(score)
                handle_events()
                instance.board[action[0]][action[1]] = current_player.get_player_id()
                game_over = check_win(action[0], action[1], current_player.get_player_id(), instance)
                next_max_score, next_scores, next_scores_normalized = calculate_score(instance.board)
                
                handle_events()

                mm_ai.remember(old_state, action, score, instance.board, game_over)
                mm_ai.train_short_memory(one_hot_board, action, short_score, scores, convert_to_one_hot(instance.board, current_player), next_scores, game_over)
                current_player.move_loss.append(mm_ai.loss)
                
                current_player.final_action = action
                current_player.moves += 1
                if game_over:
                    victory_text = f"AI-Model {players[current_player.get_player_id() - 1].id} wins!"
                    winning_player = current_player.get_player_id()
                    running = False
                else:
                    current_player = players[2 - current_player.get_player_id()]
                    logging_players()    
            try:
                draw_board(instance,last_move)
            except:
                draw_board(instance)
            handle_events()
            refresh_screen(game_number, current_player)
                
        else:
            victory_text = "TIE"
            winning_player = -1
            running = False

    # End game
    stats.log_message(victory_text)
    pygame.display.set_caption("Gomoku - Game: " + str(game_number) + " - " + victory_text)
    update_player_stats(instance, winning_player)
    if record_replay:
        filereader.save_replay(p1_moves, p2_moves)
    # For any AI-Model, train for long memory and save model
    data = {}
    loss_data = {}
    move_loss_data = {}
    for p in players:
        if p.TYPE == "AI-Model":
            p.ai.remember(instance.board, p.final_action, p.score, instance.board, True)
            p.ai.train_long_memory()
            p.score_loss.append(p.ai.loss)
            move_loss = [float(val) for val in p.move_loss]
            p.final_move_loss.append(sum(move_loss)/len(move_loss))
            print("model saving")
            handle_events()
            p.ai.model.save_model(p.model_name) #only saves after each round
            p.final_move_scores.append(sum(p.weighed_moves)/len(p.weighed_moves))
            stats.log_message(f"{p.TYPE} {p.id}: score loss: {float(p.ai.loss)}")
            stats.log_message(f"{p.TYPE} {p.id}: move loss: {sum(p.move_loss)/len(p.move_loss)}")
        p.reset_score()
        if instance.last_round:
            if p.TYPE == "AI-Model":
                data[f"{p.TYPE} {p.id}: game accuracy"] = p.weighed_scores
                data[f"{p.TYPE} {p.id}: move accuracy"] = p.final_move_scores
                loss_data[f"{p.TYPE} {p.id}: score loss"] = [float(val) for val in p.score_loss]
                move_loss_data[f"{p.TYPE} {p.id}: move loss"] = p.final_move_loss
                stats.log_message(f"{p.TYPE} {p.id}: average score loss: {sum([float(val) for val in p.score_loss]) / len([float(val) for val in p.score_loss])}")
                stats.log_message(f"{p.TYPE} {p.id}: average move loss: {sum(p.final_move_loss) / len(p.final_move_loss)}")
            p.reset_all_stats()#purely for testing purposes
    if len(data) > 0:
        stats.plot_graph(data, 'accuracy')
    if len(loss_data) > 0:
        stats.plot_graph(loss_data, 'loss data')
    if len(move_loss_data) > 0:
        stats.plot_graph(move_loss_data, 'loss data')
    time.sleep(instance.SLEEP_BEFORE_END)#sleep before closing for SLEEP_BEFORE_END seconds
    reset_game(instance)
    


def runReplay(instance, moves:dict=None):#main function
    # Main game loop
    global window_name, victory_text, current_player, running
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (300,200)
    pygame.display.set_icon(pygame.image.load('res/ico.png'))
    pygame.init()
    pygame.display.set_caption(window_name)

    instance.winning_cells = []
    running = True

    if moves is not None:#always true for now
        move_id = 0
        position = list(moves.keys())
    else:
        pass
        
    while running:
        handle_events()

        if not check_board_full(instance):
            #Replay
            if players[current_player.get_player_id() - 1].TYPE == "Replay":
                if instance.ai_delay:
                    time.sleep(random.uniform(0.25, 1.0))   # randomize ai "thinking" time
                print(instance.board)
                instance.board[position[move_id][0]][position[move_id][1]] = current_player.get_player_id()
                last_move = position[move_id]
                if check_win(position[move_id][0], position[move_id][1], current_player.get_player_id(), instance):
                    victory_text = f"AI model {players[current_player.get_player_id()-1].id} wins!"
                    running = False
                else:
                    current_player = players[2 - current_player.get_player_id()]
                    move_id += 1
            try:
                draw_board(instance,last_move)
            except:
                draw_board(instance)
            refresh_screen(0, current_player)
                
        else:
            victory_text = "TIE"
            running = False

    # End game
    stats.log_message(victory_text)
    pygame.display.set_caption("Gomoku - Game: " + victory_text)
    time.sleep(instance.SLEEP_BEFORE_END)#sleep before closing for SLEEP_BEFORE_END seconds
    reset_game(instance)


pygame.quit()