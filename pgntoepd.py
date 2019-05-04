# -*- coding: utf-8 -*-
"""
pgntoepd.py

"""

import PySimpleGUI as sg
import sys
import os
import threading
import queue
import chess
import chess.pgn
import logging


logging.basicConfig(filename='pecg.log', filemode='w', level=logging.DEBUG,
                    format='%(asctime)s :: %(levelname)s :: %(message)s')


APP_NAME = 'PGN to EPD'
APP_VERSION = 'v0.1.3'


def delete_file(fn):
    """ Delete fn file """
    if os.path.isfile(fn):
        os.remove(fn)


class pgn_to_epd(threading.Thread):
    def __init__(self, pgntoepd_queue, pgnfn, output_epdfn, append_move, append_id, remove_duplicate,
                 side_to_move, min_move_number, max_move_number):
        threading.Thread.__init__(self)
        self.pgntoepd_queue = pgntoepd_queue
        self.pgnfn = pgnfn
        self.append_move = append_move
        self.append_id = append_id
        self.remove_duplicate = remove_duplicate
        self.side_to_move = side_to_move
        self.min_move_number = min_move_number
        self.max_move_number = max_move_number
        self.output_epdfn = output_epdfn
        self.num_games = self.get_num_games()
        self.num_processed_games = 0

    def get_num_games(self):
        num_games = 0
        with open(self.pgnfn, 'r') as f:
            for lines in f:
                if '[Result ' in lines:
                    num_games += 1
                    
        return num_games
        
    def run(self):
        with open(self.pgnfn, mode = 'r', encoding = 'utf-8') as h:
            game = chess.pgn.read_game(h)
            self.num_processed_games = 0
    
            # Loop thru the games
            while game: 
                white_tag = game.headers['White']
                black_tag = game.headers['Black']
                event_tag = game.headers['Event']
                
                game_node = game
                self.num_processed_games += 1
                self.pgntoepd_queue.put('processing game {} of {} or ({:0.1f}%)'.format(self.num_processed_games, 
                    self.num_games, 100*self.num_processed_games/self.num_games))
        
                # Loop thru the moves
                while game_node.variations:
                    side = game_node.board().turn
                    epd = game_node.board().epd()
                    
                    fmvn = game_node.board().fullmove_number
                    next_node = game_node.variation(0)
                    san_move = next_node.san()
                    
                    # Move number filter
                    if fmvn > self.max_move_number:
                        logging.info('fmvn {} is more than max move number {}, break'.format(fmvn, self.max_move_number))
                        break
                    
                    if fmvn < self.min_move_number:
                        game_node = next_node
                        logging.info('fmvn {} is less than min move number {}, continue'.format(fmvn, self.min_move_number))
                        continue
                    
                    # Side to move filter
                    if self.side_to_move == 'w' and not side:
                        game_node = next_node                        
                        logging.info('side to save is white, but side to move is black, skip')
                        continue
                    elif self.side_to_move == 'b' and side:
                        game_node = next_node
                        logging.info('side to save is black, but side to move is white, skip')
                        continue 
                    
                    epd_id ='my_id'
                    if self.append_id == 'w':
                        epd_id = white_tag
                    elif self.append_id == 'b':
                        epd_id = black_tag
                    elif self.append_id == 'e':
                        epd_id = event_tag                        

                    with open(self.output_epdfn, mode = 'a+', encoding = 'utf-8') as f:
                        if self.append_id == 'never':
                            if self.append_move == 'never':
                                f.write('{}\n'.format(epd))
                            else:
                                f.write('{} {} {};\n'.format(epd, self.append_move, san_move))
                        else:
                            if self.append_move == 'never':
                                f.write('{} id \"{}\";\n'.format(epd, epd_id))
                            else:
                                f.write('{} {} {}; id \"{}\";\n'.format(epd, self.append_move, san_move, epd_id))                                

                    game_node = next_node
        
                game = chess.pgn.read_game(h)
                
        self.pgntoepd_queue.put('done')
        

def main():
    gui_que = queue.Queue()
    sg.ChangeLookAndFeel('Reddit')
    layout = [
            [sg.Text('Input PGN', size = (10, 1)), 
               sg.InputText('', size = (61, 1), key = '_txt_pgn_'),
               sg.FileBrowse('Get PGN', key = '_get_pgn_', file_types=(("PGN Files", "*.pgn"), ("All Files", "*.*"),))],
    
            [sg.Text('Output EPD', size = (10, 1)), 
               sg.InputText('', size = (61, 1), key = '_epd_file_'),
               sg.Button('Save EPD', key = '_save_epd_')],
              
            [sg.Frame(layout=[                 
                [sg.Text('Append move as', size = (12, 1)),
                 sg.Radio('bm', 'first_color', size=(8, 1), key = '_bm_',), 
                 sg.Radio('sm', 'first_color', size=(8, 1), key = '_sm_'),
                 sg.Radio('pm', 'first_color', size=(8, 1), key = '_pm_'),
                 sg.Radio('am', 'first_color', size=(8, 1), key = '_am_'),
                 sg.Radio('Never', 'first_color', size=(8, 1), key = '_never_move_', default=True)],
                 
                [sg.Text('Append id from', size = (12, 1), tooltip='Append id from Game header tags.'),
                 sg.Radio('White', 'epd_id', size=(8, 1), key = '_white_id_',), 
                 sg.Radio('Black', 'epd_id', size=(8, 1), key = '_black_id_'),
                 sg.Radio('Event', 'epd_id', size=(8, 1), key = '_event_id_'),
                 sg.Radio('Never', 'epd_id', size=(8, 1), key = '_never_id_', default=True)],
                 
                [sg.Text('EPD duplicates', size = (12, 1)),
                 sg.Radio('Remove', 'duplicate', size=(8, 1), key = '_remove_duplicate_', default=True), 
                 sg.Radio('Never', 'duplicate', size=(24, 1), key = '_never_remove_duplicate_')],
                
                [sg.Text('Side to move', size = (12, 1)),
                 sg.CBox('White', key = '_white_side_to_move_', default=True), 
                 sg.CBox('Black', key = '_black_side_to_move_', default=True)],
                 
                [sg.Text('Move no.', size = (12, 1)),
                 sg.Text('Minimum', size = (8, 1)),
                 sg.InputText('1', size = (6, 1), key = '_min_move_number_'), 
                 sg.Text('Maximum', size = (8, 1)),
                 sg.InputText('40', size = (6, 1), key = '_max_move_number_')],
                ], title='Options', title_color='red')
            ],
            
            [sg.Frame(layout=[
                [sg.Text('Engine', size = (12, 1)), 
                 sg.InputText('', size = (49, 1), key = '_txt_engine_'),
                 sg.Button('Get Engine', key='_get_engine_')],
                 
                [sg.Text('Window CP1', size = (12, 1)),
                 sg.Text('Minimum', size = (8, 1)),
                 sg.InputText('-50', size = (6, 1), key = '_cp_min_'), 
                 sg.Text('Maximum', size = (8, 1)),
                 sg.InputText('-25', size = (6, 1), key = '_cp_max_')],
                 
                [sg.Text('Window CP2', size = (12, 1)),
                 sg.Text('Minimum', size = (8, 1)),
                 sg.InputText('25', size = (6, 1), key = '_cp_min_'), 
                 sg.Text('Maximum', size = (8, 1)),
                 sg.InputText('50', size = (6, 1), key = '_cp_max_')],
                ], title='Analysis', title_color='blue', visible=False)
            ],
            
            [sg.OK(key = '_pgn_to_epd_'), sg.Text('Status: waiting', size = (44, 1), key = '_status_')]
    ]
    
    window = sg.Window('{} {}'.format(APP_NAME, APP_VERSION), layout,
                       default_button_element_size=(12, 1),
                       auto_size_buttons=False,
                       icon='')

    while True:
        button, value = window.Read(timeout=10)
        
        if button is None or button == 'Exit':
            logging.info('x is pressed')
            break
        
        if button == '_pgn_to_epd_':
            save_epdfn = value['_epd_file_']
            pgnfn = value['_txt_pgn_']
            
            # Radio
            is_bm_append_move = value['_bm_']
            is_sm_append_move = value['_sm_']
            is_pm_append_move = value['_pm_']
            is_am_append_move = value['_am_']
            
            if is_bm_append_move:
                append_move_type = 'bm'
            elif is_sm_append_move:
                append_move_type = 'sm'
            elif is_pm_append_move:
                append_move_type = 'pm'
            elif is_am_append_move:
                append_move_type = 'am'
            else:
                append_move_type = 'never'
            
            # Radio
            is_white_append_id = value['_white_id_']
            is_black_append_id = value['_black_id_']
            is_event_append_id = value['_event_id_']
            
            if is_white_append_id:
                append_tag = 'w'
            elif is_black_append_id:
                append_tag = 'b'
            elif is_event_append_id:
                append_tag = 'e'
            else:
                append_tag = 'never'
            
            # Radio
            is_remove_duplicate = value['_remove_duplicate_']
            
            # Checkbox
            is_white_to_move = value['_white_side_to_move_']
            is_black_to_move = value['_black_side_to_move_']
            
            if is_white_to_move and is_black_to_move:
                color_to_move = 'wb'
            elif is_white_to_move:
                color_to_move = 'w'
            elif is_black_to_move:
                color_to_move = 'b'
            else:
                color_to_move = None                
            
            # Move number filter
            min_move_number = int(value['_min_move_number_'])
            max_move_number = int(value['_max_move_number_']) 

            min_move_number = int(value['_min_move_number_'])
            max_move_number = int(value['_max_move_number_'])
            
            window.FindElement('_status_').Update('Status: processing ...')            
            pgntoepd = pgn_to_epd(gui_que, pgnfn, save_epdfn, append_move_type, append_tag, is_remove_duplicate,
                                  color_to_move, min_move_number, max_move_number)
            pgntoepd.setDaemon(True)
            pgntoepd.start()
            while True:
                button, value = window.Read(timeout=1000)
                
                if button is None:
                    logging.info('x is pressed')
                    sys.exit()
                    
                msg = gui_que.get()
                window.FindElement('_status_').Update('Status: {}'.format(msg))
                if 'done' in msg:
                    break
            pgntoepd.join()
            window.FindElement('_status_').Update('Status: waiting')
        
        if button == '_save_epd_':
            epd_path = sg.PopupGetFile('Input epd file or click save as to locate the file', 
                    file_types=(("EPD Files", "*.epd"), ("All Files", "*.*"),), title='PGN to EPD', save_as=False)
            try:
                while True:
                    button, value = window.Read(timeout=0)
                    window.FindElement('_epd_file_').Update(epd_path)
                    print(epd_path)
                    break
            except:
                continue            
        
    window.Close()


if __name__ == "__main__":
    main()
