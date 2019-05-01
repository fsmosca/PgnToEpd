# -*- coding: utf-8 -*-
"""
pgntoepd.py

"""

import PySimpleGUI as sg


APP_NAME = 'PGN to EPD'
APP_VERSION = 'v0.1.1'


def main():
    layout = [
            [sg.Text('Input PGN', size = (10, 1)), 
               sg.InputText('', size = (61, 1), key = '_txt_pgn_'),
               sg.FileBrowse('Get PGN', key = '_get_pgn_')],
    
            [sg.Text('Output EPD', size = (10, 1)), 
               sg.InputText('', size = (61, 1), key = '_epd_file_'),
               sg.Button('Save EPD', key = '_save_epd_')],
              
            [sg.Frame(layout=[
                [sg.Text('Append move as', size = (12, 1)),
                 sg.Radio('bm', 'first_color', size=(8, 1), key = '_bm_',), 
                 sg.Radio('sm', 'first_color', size=(8, 1), key = '_sm_'),
                 sg.Radio('pm', 'first_color', size=(8, 1), key = '_pm_'),
                 sg.Radio('am', 'first_color', size=(8, 1), key = '_am_'),
                 sg.Radio('Never', 'first_color', size=(8, 1), key = '_nomove_', default=True)],
                 
                [sg.Text('Append id from', size = (12, 1), tooltip='Append id from Game header tags'),
                 sg.Radio('White', 'epd_id', size=(8, 1), key = '_wepdid_',), 
                 sg.Radio('Black', 'epd_id', size=(8, 1), key = '_bepdid_'),
                 sg.Radio('Event', 'epd_id', size=(8, 1), key = '_eventepdid_'),
                 sg.Radio('Never', 'epd_id', size=(8, 1), key = '_neverid_', default=True)],
                 
                [sg.Text('EPD duplicates', size = (12, 1)),
                 sg.Radio('Remove', 'duplicates', size=(8, 1), key = '_removedupes_', default=True), 
                 sg.Radio('Never', 'duplicates', size=(24, 1), key = '_donotremovedupes_')],
                
                [sg.Text('Side to move', size = (12, 1)),
                 sg.CBox('White', key = '_cb_white_', default=True), 
                 sg.CBox('Black', key = '_cb_black_', default=True)],
                 
                [sg.Text('Move no.', size = (12, 1)),
                 sg.Text('Minimum', size = (8, 1)),
                 sg.InputText('1', size = (6, 1), key = '_itxt_min_'), 
                 sg.Text('Maximum', size = (8, 1)),
                 sg.InputText('40', size = (6, 1), key = '_itxt_max_')],
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
            
            [sg.OK(key = '_process_pgn_'), sg.Cancel(key = '_cancel_')]
    ]
    
    window = sg.Window('{} {}'.format(APP_NAME, APP_VERSION), layout,
                       default_button_element_size=(12, 1),
                       auto_size_buttons=False,
                       icon='')

    while True:
        button, value = window.Read(timeout=10)
        
        if button is None or button == 'Exit':
            break
        
        if button == '_cancel_':
            break
        
        if button == '_save_epd_':
            epd_path = sg.PopupGetFile('Input epd file or click save as to locate the file', title='PGN to EPD', save_as=True)
            if epd_path is None:
                continue
            while True:
                button, value = window.Read(timeout=0)
                window.FindElement('_epd_file_').Update(epd_path)
                break
#            with open(epd_path, mode= 'a+', encoding='utf-8') as f:
#                f.write('my epd\n')
        
        if button == '_get_pgn_':
            layout1 = [
                    [sg.Text('PGN1', size = (6, 1)), 
                     sg.InputText('', size = (16, 1), key = '_pgn1_'),
                     sg.Button('Get PGN1', key='_get_pgn1_')],
                     
                    [sg.Text('PGN2', size = (6, 1)), 
                     sg.InputText('', size = (16, 1), key = '_pgn2_'),
                     sg.Button('Get PGN2', key='_get_pgn2_')],
                     
                    [sg.Text('PGN3', size = (6, 1)), 
                     sg.InputText('', size = (16, 1), key = '_pgn3_'),
                     sg.Button('Get PGN3', key='_get_pgn3_')],
                     
                    [sg.Text('PGN4', size = (6, 1)), 
                     sg.InputText('', size = (16, 1), key = '_pgn4_'),
                     sg.Button('Get PGN4', key='_get_pgn4_')],
                     
                    [sg.B('OK', key=('_OK_PGN'))],
                    ]
                     
            window1 = sg.Window('Get PGN', layout1,
                       default_button_element_size=(12, 1),
                       auto_size_buttons=False,
                       icon='')
            
            while True:
                button, value = window1.Read(timeout=10)
                
                if button is None or button == 'Exit':
                    break
                
            window1.Close()
        
    window.Close()


if __name__ == "__main__":
    main()
    
