# PgnToEpd
A program written in python that converts positions in the games to EPD format. There are options which the user can set such as side to move, move numbers and others.

![](https://i.imgur.com/BDgRpMr.png)

### A. Requirements
#### 1. If you use the source pgntoepd.py
* Python 3<br>
`Download and install Python 3 from https://www.python.org/downloads/`
* PySimpleGUI<br>
`pip install pysimplegui`
* Python-Chess<br>
`pip install python-chess`

#### 2. If you use an exe file
* Just download the pgntoepd.exe file for windows at https://github.com/fsmosca/PgnToEpd/releases

### B. Options
#### 1. Append move as:
* bm  
`rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - bm d6;`
* sm  
`rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - sm d6;`
* pm  
`rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - pm d6;`
* am  
`rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - am d6;`
* never  
`rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -`

#### 2. NAG'S
* am  
Input game:  
```
[Event "?"]
[Site "?"]
[Date "?"]
[Round "?"]
[White "?"]
[Black "?"]
[Result "*"]

1.e4 f6? *
```
Output epd:  
`rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - am f6;`
* bm  
Input game:  
```
[Event "?"]
[Site "?"]
[Date "?"]
[Round "?"]
[White "?"]
[Black "?"]
[Result "*"]

1.e4 e5! *
```
Output epd:  
`rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - bm e5;`

### C. Credits
* PySimpleGUI<br>
https://github.com/PySimpleGUI/PySimpleGUI

* Python-Chess<br>
https://github.com/niklasf/python-chess
