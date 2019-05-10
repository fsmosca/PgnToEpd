# -*- coding: utf-8 -*-
"""
pgntoepd.py

"""

import PySimpleGUI as sg
import sys
import os
import threading
import time
import queue
import chess
import chess.pgn
import logging


logging.basicConfig(filename='pecg.log', filemode='w', level=logging.DEBUG,
                    format='%(asctime)s :: %(levelname)s :: %(message)s')


APP_NAME = 'PGN to EPD'
APP_VERSION = 'v0.1.14.beta'
BOX_TITLE = APP_NAME + ' ' + APP_VERSION


def delete_file(fn):
    """ Delete fn file """
    if os.path.isfile(fn):
        os.remove(fn)


class pgn_to_epd(threading.Thread):
    def __init__(self, pgntoepd_queue, pgnfn, output_epdfn, append_move,
                 append_id, remove_duplicate, side_to_move, min_move_number,
                 max_move_number, write_append, is_first_move, is_bad_move_am,
                 is_good_move_bm):
        threading.Thread.__init__(self)
        self.pgntoepd_queue = pgntoepd_queue
        self.pgnfn = pgnfn
        self.append_move = append_move
        self.is_bad_move_am = is_bad_move_am
        self.is_good_move_bm = is_good_move_bm
        self.append_id = append_id
        self.remove_duplicate = remove_duplicate
        self.side_to_move = side_to_move
        self.min_move_number = min_move_number
        self.max_move_number = max_move_number
        self.output_epdfn = output_epdfn
        self.write_append = write_append
        self.is_first_move = is_first_move
        self.move_sequence = 0
        self.num_processed_games = 0
        self.tmp_save = []
        self.file_encoding = None
        self.num_games = self.get_num_games()

    def get_num_games(self):
        """
        This method is called the moment class pgn_to_epd is used.
        This method also changes the encoding from None to utf-8, if None
        will not work. If utf-8 also will not work, we will quit the program
        and log some warning messages.
        """
        num_games = 0
        
        try:
            with open(self.pgnfn, mode = 'r', encoding = self.file_encoding) as f:
                for lines in f:
                    if '[Result ' in lines:
                        num_games += 1
        except Exception as ex:
            template = 'An exception of type {0} occurred. Arguments:\n{1!r}'
            message = template.format(type(ex).__name__, ex.args)
            logging.warning(message)
            
            # Change encoding and try again
            if self.file_encoding is None:
                self.file_encoding = 'utf-8'
            else:
                self.file_encoding = None
                
            logging.info('Try using encoding: {}'.format(self.file_encoding))
            
            try:
                with open(self.pgnfn, mode = 'r', encoding = self.file_encoding) as f:
                    for lines in f:
                        if '[Result ' in lines:
                            num_games += 1
            except Exception as ex:
                template = 'An exception of type {0} occurred. Arguments:\n{1!r}'
                message = template.format(type(ex).__name__, ex.args)
                logging.warning(message)
                sys.exit(1)
                    
        return num_games
    
    def get_existing_epd(self):
        if os.path.isfile(self.output_epdfn):
            with open(self.output_epdfn, mode = 'r', encoding = self.file_encoding) as f:
                for lines in f:
                    line = lines.strip()
                    self.tmp_save.append(line)
        
    def run(self):            
        # If epd writing is overwrite mode
        if not self.write_append:
            logging.info('overwrite mode, delete file {}'.format(self.output_epdfn))
            delete_file(self.output_epdfn)
        else:
            logging.info('append mode, save existing epd lines')
            self.get_existing_epd()
            
        # Process PGN file
        with open(self.pgnfn, mode = 'r', encoding = self.file_encoding) as h:
            game = chess.pgn.read_game(h)
            self.num_processed_games = 0
    
            # Loop thru the games
            while game: 
                self.move_sequence = 0
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
                    hmvc = game_node.board().halfmove_clock
                    
                    next_node = game_node.variation(0)
                    san_move = next_node.san()
                    nags = next_node.nags
                    
                    # Count of read moves for every game. This is useful for
                    # "First move only" option
                    self.move_sequence += 1
                    
                    # If first move option is true and this is the second move,
                    # we skip the rest of the moves and read the next game instead.
                    if self.move_sequence > 1 and self.is_first_move:
                        break
                    
                    # If move is bad and "append am if move is bad" is true
                    if self.is_bad_move_am and (chess.pgn.NAG_MISTAKE in nags or \
                                        chess.pgn.NAG_BLUNDER in nags):
                        move_append = 'am'
                    # Else if move is good and "append bm if move is good" is true
                    elif self.is_good_move_bm and (chess.pgn.NAG_GOOD_MOVE in nags or \
                                        chess.pgn.NAG_BRILLIANT_MOVE in nags):
                        move_append = 'bm'
                    else:
                        move_append = self.append_move

                    # Only enable min and max move no. options if "First move only" is false
                    if not self.is_first_move:
                        # Move number filter
                        if fmvn > self.max_move_number:
                            logging.info('fmvn {} is more than max move number {}, break'.format(fmvn,
                                         self.max_move_number))
                            break
                        
                        if fmvn < self.min_move_number:
                            game_node = next_node
                            logging.info('fmvn {} is less than min move number {}, continue'.format(fmvn,
                                         self.min_move_number))
                            continue
                        
                    # Only enable side to move option if "First move only" is false
                    if not self.is_first_move:                    
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

                    with open(self.output_epdfn, mode = 'a+', encoding = self.file_encoding) as f:
                        # Writing hmvc or fifty-move number is not part of the options.
                        # But with high hmvc we record this number as it may affect
                        # the evaluation of the position.
                        if hmvc >= 80:
                            if self.append_id == 'never':
                                if move_append == 'never':
                                    unique_epd = epd
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} hmvc {};\n'.format(epd, hmvc))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} hmvc {};\n'.format(epd, hmvc))
                                else:
                                    unique_epd = '{} {} {};'.format(epd, move_append, san_move)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} {} {}; hmvc {};\n'.format(epd,
                                                    move_append, san_move, hmvc))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} {} {}; hmvc {};\n'.format(epd,
                                                move_append, san_move, hmvc))
                            else:
                                if move_append == 'never':
                                    unique_epd = '{}'.format(epd)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} hmvc {}; id \"{}\";\n'.format(epd, hmvc, epd_id))
                                            self.tmp_save.append(unique_epd)
                                        else:
                                            f.write('{} hmvc {}; id \"{}\";\n'.format(epd, hmvc, epd_id))
                                else:
                                    unique_epd = '{} {} {};'.format(epd, move_append, san_move)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} {} {}; hmvc {}; id \"{}\";\n'.format(epd, 
                                                    move_append, san_move, hmvc, epd_id))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} {} {}; hmvc {}; id \"{}\";\n'.format(epd,
                                                move_append, san_move, hmvc, epd_id))
                        # Else if hmvc is below 80
                        else:
                            if self.append_id == 'never':
                                if move_append == 'never':
                                    unique_epd = '{}'.format(epd)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{}\n'.format(epd))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{}\n'.format(epd))
                                else:
                                    unique_epd = '{} {} {};'.format(epd, move_append, san_move)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} {} {};\n'.format(epd, move_append, san_move))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} {} {};\n'.format(epd, move_append, san_move))
                            else:
                                if move_append == 'never':
                                    unique_epd = '{}'.format(epd)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} id \"{}\";\n'.format(epd, epd_id))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} id \"{}\";\n'.format(epd, epd_id))
                                else:
                                    unique_epd = '{} {} {};'.format(epd, move_append, san_move)
                                    if self.remove_duplicate:
                                        if not unique_epd in self.tmp_save:
                                            f.write('{} {} {}; id \"{}\";\n'.format(epd,
                                                    move_append, san_move, epd_id))
                                            self.tmp_save.append(unique_epd)
                                    else:
                                        f.write('{} {} {}; id \"{}\";\n'.format(epd,
                                                move_append, san_move, epd_id))

                    game_node = next_node
        
                game = chess.pgn.read_game(h)
                
        self.pgntoepd_queue.put('done')
        

def main():
    gui_queue = queue.Queue()
    sg.ChangeLookAndFeel('Reddit')
    
    menu_def = [
            ['File', ['Exit']],            
            ['Tools', ['Clean PGN']],
            ['&Help', ['PGN', 'EPD', 'OPTIONS']],
    ]
    
    layout = [
            [sg.Menu(menu_def, tearoff=False)],
            
            [sg.Text('Input PGN', size = (10, 1)), 
               sg.InputText('', size = (57, 1), key = '_txt_pgn_'),
               sg.FileBrowse('Get PGN', key = '_get_pgn_',
                  file_types=(("PGN Files", "*.pgn"), ("All Files", "*.*"),))],
    
            [sg.Text('Output EPD', size = (10, 1)), 
               sg.InputText('', size = (57, 1), key = '_epd_file_'),
               sg.Button('Save EPD', key = '_save_epd_')],
             
            # Options
            [sg.Frame(layout=[ 
                [sg.Text('EPD write mode', size = (12, 1)),
                 sg.Radio('append', 'write_mode', size=(6, 1),
                        key = '_write_append_', default=True), 
                 sg.Radio('overwrite', 'write_mode', size=(6, 1),
                        key = '_write_overwrite_')],
                        
                [sg.Text('Append move as', size = (12, 1)),
                 sg.Radio('bm', 'first_color', size=(6, 1), key = '_bm_',), 
                 sg.Radio('sm', 'first_color', size=(6, 1), key = '_sm_'),
                 sg.Radio('pm', 'first_color', size=(6, 1), key = '_pm_'),
                 sg.Radio('am', 'first_color', size=(6, 1), key = '_am_'),
                 sg.Radio('Never', 'first_color', size=(6, 1), 
                          key = '_never_move_', default=True)],
                          
                [sg.Text("NAG's", size = (12, 1), 
                    tooltip = 'NAG (Numeric Annotation Glyphs)\n1. Append am if move has ? or ??.\n2. Append bm if move has ! or !!.'),
                 sg.CBox('am ?, ??', key = '_am_bad_move_', size = (6, 1), default=False), 
                 sg.CBox('bm !, !!', key = '_bm_good_move_', default=False)],
                 
                [sg.Text('Append id from', size = (12, 1),
                         tooltip='Append id from Game header tags.'),
                 sg.Radio('White', 'epd_id', size=(6, 1), key = '_white_id_',), 
                 sg.Radio('Black', 'epd_id', size=(6, 1), key = '_black_id_'),
                 sg.Radio('Event', 'epd_id', size=(6, 1), key = '_event_id_'),
                 sg.Radio('Never', 'epd_id', size=(6, 1), key = '_never_id_', default=True)],
                 
                [sg.Text('EPD duplicates', size = (12, 1)),
                 sg.Radio('Remove', 'duplicate', size=(6, 1),
                          key = '_remove_duplicate_', default=True), 
                 sg.Radio('Never', 'duplicate', size=(24, 1),
                          key = '_never_remove_duplicate_')],
                
                [sg.Text('Side to move', size = (12, 1)),
                 sg.CBox('White', key = '_white_side_to_move_', size = (6, 1), default=True), 
                 sg.CBox('Black', key = '_black_side_to_move_', default=True)],
                 
                [sg.Text('Move no.', size = (12, 1)),
                 sg.Text('Minimum', size = (10, 1)),
                 sg.InputText('1', size = (8, 1), key = '_min_move_number_'), 
                 sg.Text('Maximum', size = (8, 1)),
                 sg.InputText('40', size = (8, 1), key = '_max_move_number_'),
                 sg.CBox('First move only', key = '_first_move_', size = (16, 1),
                         tooltip = 'If set to true, min and max move no. are ignored', default=False)],
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
            
            [sg.OK(key = '_pgn_to_epd_'), sg.Text('Status: waiting',
                 size = (64, 1), key = '_status_')]
    ]
    
    window = sg.Window('{} {}'.format(APP_NAME, APP_VERSION), layout,
                       default_button_element_size=(12, 1),
                       auto_size_buttons=False,
                       icon='')

    while True:
        button, value = window.Read(timeout=10)
        
        if button is None or button == 'Exit':
            logging.info('Exit app')
            break
        
        if button == 'PGN':
            sg.PopupOK('For update', title = BOX_TITLE, keep_on_top = True)
            
        if button == 'EPD':
            sg.PopupOK('For update', title = BOX_TITLE, keep_on_top = True)
            
        if button == 'Clean PGN':
            sg.PopupOK('For update', title = BOX_TITLE, keep_on_top = True)
            
        if button == 'OPTIONS':
            sg.PopupOK('For update', title = BOX_TITLE, keep_on_top = True)
        
        if button == '_pgn_to_epd_':
            save_epdfn = value['_epd_file_']
            pgnfn = value['_txt_pgn_']
            
            # Radio, write mode
            is_write_append = value['_write_append_']
            
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
                
            # Option reated to NAGS that is, !, !!, ? and ??
            # Element type: check box
            is_bad_move_am = value['_am_bad_move_']
            is_good_move_bm = value['_bm_good_move_']
            
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
            
            is_first_move = True if value['_first_move_'] else False
            
            t1 = time.time()
            
            # Make sure that pgn input box is not empty
            if pgnfn == '':
                logging.warning('Input pgn file is missing.')
                sg.PopupOK('Input PGN file is missing! Please press the Get PGN button.', title = BOX_TITLE)
                continue
            
            # Make sure that epd output box is not empty
            if save_epdfn == '':
                logging.warning('Output epd file is missing.')
                sg.PopupOK('Output EPD file is missing! Please press the Save EPD button.', title = BOX_TITLE)
                continue
            
            window.FindElement('_status_').Update('Status: processing ...')            
            pgntoepd = pgn_to_epd(gui_queue, pgnfn, save_epdfn, append_move_type,
                    append_tag, is_remove_duplicate, color_to_move, min_move_number, 
                    max_move_number, is_write_append, is_first_move, is_bad_move_am,
                    is_good_move_bm)
            pgntoepd.setDaemon(True)
            pgntoepd.start()
            while True:
                button, value = window.Read(timeout=1000)
                
                if button is None or button == 'Exit':
                    logging.info('Exit app')
                    sys.exit()
                    
                msg = gui_queue.get()
                window.FindElement('_status_').Update('Status: {}'.format(msg))
                if 'done' in msg:
                    break
            pgntoepd.join()
            elapsed = time.time() - t1
            window.FindElement('_status_').Update('Current Status: waiting, ' + 
                'Previous Status: Done!!, elapsed: {:0.2f}s'.format(elapsed))
        
        if button == '_save_epd_':
            epd_path = sg.PopupGetFile('Input epd file or click save as to locate the file', 
                    file_types=(("EPD Files", "*.epd"), ("All Files", "*.*"),), 
                        title='PGN to EPD', save_as=True)
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
