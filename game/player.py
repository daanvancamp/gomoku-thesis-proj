class Player:
    def __init__(self, player_id):    
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
        self.allow_overrule = True
        self.final_action = None

class AI_Player(Player):
    def __init__(self, player_id):    
        super().__init__(player_id)  # Call the constructor of the base class
        self.AI_model=None
    
class Human_Player(Player):
    def __init__(self, player_id):    
        super().__init__(player_id)  # Call the constructor of the base class

class Test_Player(Player):
    def __init__(self, player_id):    
        super().__init__(player_id)  # Call the constructor of the base class