#!/usr/bin/env python

#####################################################
# A very simple whiteboard based on python-tkinter
#
# Copyright (C) 2013-2022 Lars Schneidenbach
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#####################################################
# README:
#
# All it provides is:
# * a canvas area for drawings.
# * 4 pre-defined colors (black, red, blue, green)
# * an erase mode
# * adjustable size of the pen
# * a box mode to quickly draw frames (or erase areas)
# * clear/new
# * some undo
#
# Everything is controlled by keyboard
# <+/->  changes the size of the pen
# <b>    toggles box-drawing mode
# <c>    picks the next color
# <1-4>  select a color directly
# <e>    toggles erase mode and painting mode
# <N>    clears the board
# <Q>|<alt+f4> to exit
#
# Paint with mouse while holding button1
# Erase with mouse while holding button3 (or toggle erase mode)
#
# The status bar shows the key bindings. In the bottom right you'll
# find the current operation mode, the color, and the size of the pen.
#
# There are no facilities to save the content. If you need to take a
# picture, use screen capture facilities of your OS
#
# Jun'21: There's now limited number (100) of undo steps - which is
#         substantially more than on a real whiteboard ;-)
#
# Feb'22: Added a rudimentary way to continue drawing from a screenshot
#         place the image (or a softlink) named 'background.png' in CWD
#         it will load that image at startup
#         (note: clear board will delete image)
#
# feature requests, suggestions, improvements and help with coding are
# welcome
#
#
# TODOs/nice to have features:
# - [med] variable size of the board (maybe first step could be to
#   use command line parameters)
# - [low] implement a way to export/save the content into a bitmap file
# - [low] provide a way to type text (has to include the font size too)
# - [med] proper implementation (currently tons of ugly global vars)
#
# contributors
# - Lars Schneidenbach (implementation)
# - Marcel Schaal (testing, box-mode suggestion)
# - Michael Kaufmann (testing)
# - Joachim Fenkes (testing, autoincreased erase pen suggestion)
#

import time
import os

from Tkinter import *

# major global variables
xsize=2200
ysize=1600

brushsize = 1
paint_mode = 1
stored_paint_mode = paint_mode;
color = 1

box_mode = 0

last = [ 0, 0 ]
start_box = [ 0, 0 ]
undo = []
undostack = []

# color definitions and output strings
MAX_COLOR = 4
MAX_UNDO = 100
color_map=[]
color_map.append("white")
color_map.append("black")
color_map.append("red")
color_map.append("blue")
color_map.append("green")

paint_mode_str=[]
paint_mode_str.append("ERASE PEN")
paint_mode_str.append("PAINT PEN")
paint_mode_str.append("ERASE BOX")
paint_mode_str.append("PAINT BOX")


cursor_list=["dot","pencil","tcross","cross"]

# the window elements:
master = Tk()

board = Canvas( master,
                width=xsize, height=ysize,
                bg="white",
                relief=SUNKEN,
                cursor=cursor_list[paint_mode+box_mode*2])
temp_box = board.create_rectangle(0,0,0,0)

statuslineframe = Frame(master=master)

statusbar=Label(master=statuslineframe,
                text="(l-mouse)pen; (r-mouse)erase pen; (b)toggle box-mode; (+/-)brushsize; (e)toggle erase; (c)change color; (1-4)select color; (u)undo (N)clear; (Q)quit")

colorbar=Label(master=statuslineframe,
               padx=10,
               text=paint_mode_str[ paint_mode + 2*box_mode ]+"("+str(brushsize)+")",
               fg=color_map[ 1 - paint_mode ],
               bg=color_map[ paint_mode * color ] )


def toggle_erase():
    global paint_mode
    global brushsize
    paint_mode = (paint_mode + 1) % 2
    brushsize = brushsize + ( 1 - paint_mode*2 )*2
    board.config(cursor=cursor_list[paint_mode+box_mode*2])

def toggle_boxmode():
    global box_mode
    box_mode = (box_mode + 1) % 2
    board.config(cursor=cursor_list[paint_mode+box_mode*2])

def add_undo(undo):
    global undostack
    if len(undostack)>=MAX_UNDO:
        del undostack[0]
    undostack.append(undo)
#    print(len(undostack))

# initial mouse click callback
def callback_click(event):
    global last
    global undo
    global start_box
    last = [ event.x, event.y ]
    start_box = [ event.x, event.y ]
    undo = []

# right-button click start
def callback_click_erase(event):
    global last
    global start_box
    global paint_mode
    global stored_paint_mode
    global undo
    global temp_box
    global box_mode

    stored_paint_mode = paint_mode;
    if( stored_paint_mode != 0 ):
        toggle_erase()
    last = [ event.x, event.y ]
    start_box = [ event.x, event.y ]
    if( box_mode != 0):
        temp_box = board.create_rectangle(start_box[0], start_box[1],
                                          event.x, event.y,
                                          outline=color_map[ color ],
                                          width=1 )
    undo = []

# right-button release
def callback_click_erase_reset(event):
    global paint_mode
    global stored_paint_mode
    global box_mode
    global temp_box
    global undo
    if( box_mode != 0):
        board.delete( temp_box )
        undo.append( board.create_rectangle(start_box[0], start_box[1],
                                            event.x, event.y,
                                            width=0,
                                            fill=color_map[ paint_mode * color ]) )
    if( stored_paint_mode != 0 ):
        toggle_erase()
    add_undo(undo)

# mouse movement callback
def callback_move(event):
    global last
    global start_box
    global temp_box
    global box_mode
    global undo
    if( box_mode == 0):
        diffX = event.x-last[0]
        diffY = event.y-last[1]
        undo.append(board.create_oval(event.x-brushsize,
                                      event.y-brushsize,
                                      event.x+brushsize,
                                      event.y+brushsize,
                                      width=0,
                                      outline=color_map[ paint_mode * color ],
                                      fill=color_map[ paint_mode * color ]) )

        if( diffX*diffX + diffY*diffY > brushsize*brushsize ):
            undo.append(board.create_line(last[0], last[1],
                                          event.x, event.y,
                                          width=brushsize*2,
                                          # outline=color_map[ paint_mode * color ],
                                          fill=color_map[ paint_mode * color ]) )
            last = [ event.x, event.y ]
    else:
        board.delete( temp_box )
        temp_box = board.create_rectangle(start_box[0], start_box[1],
                                          event.x, event.y,
                                          outline=color_map[ color ],
                                          width=1 )

# left-click release
def callback_click_release( event ):
    global start_box
    global temp_box
    global undo
    if( box_mode == 1 ):
        board.delete( temp_box )
        if( paint_mode == 1 ):
            undo.append( board.create_rectangle(start_box[0], start_box[1],
                                                event.x, event.y,
                                                width=brushsize*2,
                                                outline=color_map[ paint_mode * color ]) )
        else:
            undo.append( board.create_rectangle(start_box[0], start_box[1],
                                                event.x, event.y,
                                                width=0,
                                                fill=color_map[ paint_mode * color ]) )
    add_undo(undo)


# key stroke callback handler
def key_handler(event):
    global brushsize
    global paint_mode
    global color
    global undo

    if( event.char == "+" ):
        brushsize = brushsize + 1
        if( brushsize > 15 ):
            brushsize = 15
    elif ( event.char == "-" ):
        brushsize = brushsize - 1
        if( brushsize < 1 ):
            brushsize = 1
    elif ( event.char == "e" ):
        toggle_erase()
    elif ( event.char == "c" ):
        color = ( color + 1 )
        if ( color > MAX_COLOR ):
            color = 1
    elif ( event.char == "1" ):
        paint_mode=1
        color = 1
    elif ( event.char == "2" ):
        paint_mode=1
        color = 2
    elif ( event.char == "3" ):
        paint_mode=1
        color = 3
    elif ( event.char == "4" ):
        paint_mode=1
        color = 4
    elif ( event.char == "N" ):
        board.delete(ALL)
    elif ( event.char == "b" ):
        toggle_boxmode()
    elif ( event.char == "u" ):
        lastundo=len(undostack)-1
        if lastundo>=0:
            undo = undostack.pop(lastundo)
            for x in undo:
                board.delete( x )
    elif( event.char == "Q" ):
        master.destroy()
        return
    else:
        char=event.char

    colorbar.config(
        text=paint_mode_str[ paint_mode + 2*box_mode ]+"("+str(brushsize)+")",
        fg=color_map[ 1-paint_mode ],
        bg=color_map[ paint_mode * color ] )


# placement of window elements and key bindings
master.title("Simple WhiteBoard")

board.bind("<B1-Motion>", callback_move)
board.bind("<Button-1>", callback_click)
board.bind("<ButtonRelease-1>", callback_click_release)

board.bind("<B3-Motion>", callback_move)
board.bind("<Button-3>", callback_click_erase)
board.bind("<ButtonRelease-3>", callback_click_erase_reset)
master.bind("<Key>", key_handler)

statusbar.pack(side=LEFT, expand=1, padx=30)
colorbar.pack(side=RIGHT)

statuslineframe.pack(side=TOP)
board.pack(side=BOTTOM)

img = PhotoImage(file='background.png')
board.create_image(10,10,anchor=NW,image=img) # add background image

master.mainloop()
