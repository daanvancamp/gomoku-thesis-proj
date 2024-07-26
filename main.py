
from datetime import datetime
import os
from threading import Thread
from filereader import log_info_overruling
import mainmenu
from lezen_stukken_en_trivia import initialiseer_muziek
from mainmenu import load_board_from_file

def main():
    mainmenu.mainmenu_run()
def controleer_bestandspaden():
    #glob.glob searches file in directory
    pad_gedetecteerde_stukken=r'..\vijf_op_een_rij_beeldherkenning\detected_pieces.json'

    paden=[r".\bord_gomoku\bord_na_zet.json",r".\bord_gomoku\bord_voor_zet.json", pad_gedetecteerde_stukken,"bool_overrule.txt","consts.json","wachten_muziek.mp3","logging_overruling.txt"]
    for bestandspad in paden:
        if not os.path.exists(bestandspad):
            if bestandspad==pad_gedetecteerde_stukken:
                print("The file doesn't exist")
                raise Exception("Are you sure that you have cloned the other repository:https://github.com/daanvancamp/vijf_op_een_rij_beeldherkenning"," That repository has to be located in the same main map")
            raise Exception("The file doesn't exist",bestandspad)
def log_new_run():
    log_info_overruling("\n\n\n\n\n\ndate and time: "+datetime.now().isoformat())
    log_info_overruling("\nnew run of the code begins:")

if __name__ == '__main__':
    load_board_from_file()
    log_new_run()
    controleer_bestandspaden()
    initialiseer_muziek()
    main()
