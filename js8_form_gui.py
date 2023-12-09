#!/usr/bin/env python
import sys
import constant as cn
import string
import struct

try:
  import PySimpleGUI as sg
except:
  import PySimpleGUI27 as sg

import json
import threading
import os
import platform
import calendar
import xmlrpc.client
import math
import debug as db

import hrrm
import js8_form_events
import js8_form_dictionary

from datetime import datetime, timedelta
from datetime import time

from uuid import uuid4

"""
MIT License

Copyright (c) 2022-2023 Lawrence Byng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def createTextElement(self, keyname, t1, text, width, height, pad, sub_layout):
  if(width>0):
    line =  [sg.Text(text, size=(width, height), font=("Courier New", 9), pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT)]
  else:  
    line =  [sg.Text(text, size=(width, height), font=("Helvetica", 9), expand_x=True, pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT )]
  return line

def createSimTextElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + '_' * (width - len(text))
  return line

def createPreviewTextElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + ':' + ' ' * (width - len(text))
  return line

def createInputElement(self, keyname, t1, text, width, height, pad, sub_layout):

  t1 = self.replaceFields(t1)

  disabled_field = self.render_disabled_controls

  if(height == 1):	  
    if(width>0):
      line = [sg.InputText(t1 , size=(width, height), font=("Courier New", 9), key=keyname, pad=(0,0), border_width=1, disabled=disabled_field, disabled_readonly_background_color='white' )]
    else:  
      line = [sg.InputText(t1 , size=(width, height), font=("Courier New", 9), key=keyname, pad=(0,0), border_width=1, expand_x=True, disabled=disabled_field, disabled_readonly_background_color='white' )]
  else:
    if(width>0):
      line = [sg.MLine(t1, size=(width, height), key=keyname, font=("Courier New", 9), autoscroll=True, pad=(0,0), border_width=1, disabled=disabled_field)]
    else:
      line = [sg.MLine(t1, size=(width, height), key=keyname, font=("Courier New", 9), autoscroll=True, pad=(0,0), border_width=1, expand_x=True, disabled=disabled_field)]

  return line

def createSimInputElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  '' 
  if(height == 1):	  
    line =  'I' * width
  else:
    line =  ('I' * width + '\n ') * height
  return line

def createPreviewInputElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  """
  line =  '' 
  if(height == 1):	  
    line =  'P' * width
  else:
    line =  ('P' * width + '\n ') * height
  """
  return line

def createCkboxElement(self, keyname, t1, text, width, height, pad, sub_layout):

  line = [sg.CBox(t1 , size=(width, height), font=("Courier New", 9), key=keyname, metadata='CB')] 
  return line

def createSimCkboxElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  '' 
  line =  'Ckbox' 
  return line

def createPreviewCkboxElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + ' ' * (width - len(text))
  return line


def createRadioElement(self, keyname, t1, text, width, height, pad, sub_layout):

  line = [sg.Radio(t1 , text, size=(width, height), font=("Courier New", 9), key=keyname)] 
  return line

def createSimRadioElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'Radio'
  return line

def createPreviewRadioElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  return line


def createComboElement(self, keyname, t1, text, width, height, pad, sub_layout):
  combo_list = 'Normal,High,Low'.split(',')
  line = [sg.Combo(combo_list, key=keyname)]
  return line

def createSimComboElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'Combo'
  return line

def createPreviewComboElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  return line

def createMainHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  [sg.Text(text, size=(width, height), font=("Courier New", 20), pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT, expand_x=True, justification ='center', background_color=self.main_heading_background_clr, text_color=self.main_heading_text_clr)]
  return line

def createSimMainHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + 'H' * (width - len(text))
  return line

def createPreviewMainHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + ' ' * (width - len(text))
  return line

def createSubHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  [sg.Text(text, size=(width, height), font=("Courier New", 14), pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT, expand_x=True, justification ='center', background_color=self.sub_heading_background_clr,text_color=self.sub_heading_text_clr)]
  return line

def createSimSubHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + 'H' * (width - len(text))
  return line

def createPreviewSubHeadingElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  return line


def createNumberedSectionElement(self, keyname, t1, text, width, height, pad, sub_layout):
  height = 1
  width = len(text)
  line =  [sg.Text(text, size=(width, height), font=("Courier New", 14), pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT, background_color=self.numbered_section_background_clr,text_color=self.numbered_section_text_clr)]
  return line

def createSimNumberedSectionElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + 'N' * (width - len(text))
  return line

def createPreviewNumberedSectionElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  return line


def createSeparatorElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  [sg.Text(' '*width, size=(width, height), font=("Courier New", 9), pad=(pad,0), border_width=0, relief = sg.RELIEF_FLAT, expand_x=True, justification ='center', text_color='blue')]
  return line

def createSimSeparatorElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + 'H' * (width - len(text))
  return line

def createPreviewSeparatorElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + ' ' * (width - len(text))
  return line


def createColumnElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  [sg.Col(sub_layout, background_color=sg.DEFAULT_BACKGROUND_COLOR, key=keyname, vertical_alignment = 'top')]
  return line

def createSimColumnElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + 'H' * (width - len(text))
  return line

def createPreviewColumnElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  text + ' ' * (width - len(text))
  return line


"""
USE METADATA metadata=<radiogroup>_<# in radio button group>
set the key of each radio button to this value
when readin, read each radio button until selected is found then skip the rest.
"""
def createRadioGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):

  button_list = text.split(',')

  widest = 0
  for x in range (len(button_list)):
    if(len(button_list[x])>widest):
      widest = len(button_list[x])

  width = widest

  line = []
  for x in range (len(button_list)):
    btn_keyname = keyname + '_' + str(x)
    meta_value = 'BG,' + str(len(button_list))
    if(str(x) == t1):
      checked = True
    else:
      checked = False

    if(x==0):
      line = line + [sg.Radio(button_list[x], keyname, size=(width, height), font=("Courier New", 9), key=keyname, metadata=meta_value, default=checked )] 
    else:
      line = line + [sg.Radio(button_list[x], keyname, size=(width, height), font=("Courier New", 9), key=btn_keyname, default=checked)] 
  return line

def createSimRadioGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'RadioGroup'
  return line

def createPreviewRadioGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line = ''

  strings = text.split(',')
  for x in range (len(strings)):
    if(t1 != '' and x == int(t1)):
      line = line + ' X '
    else:
      line = line + '   '
    line = line + strings[x] + ' '
  return line


def createOptionMenuElement(self, keyname, t1, text, width, height, pad, sub_layout):

  option_list = text.split(',')

  selected = t1

  meta_value = 'OM,' + str(len(option_list))

  line = [sg.OptionMenu(option_list, key=keyname, default_value = selected, metadata=meta_value)]

  return line

def createSimOptionMenuElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'OptionMenu'
  return line

def createPreviewOptionMenuElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  t1 + ' ' * (width - len(t1))
  return line


def createCheckBoxGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):
  button_list = text.split(',')

  widest = 0
  for x in range (len(button_list)):
    if(len(button_list[x])>widest):
      widest = len(button_list[x])

  width = widest

  line = []
  for x in range (len(button_list)):
    btn_keyname = keyname + '_' + str(x)
    meta_value = 'CG,' + str(len(button_list))
    if(len(t1) > x and t1[x] == 'X'):
      checked = True
    else:
      checked = False

    if(x==0):
      line = line + [sg.CBox(button_list[x] , size=(width, height), font=("Courier New", 9), key=keyname, metadata=meta_value, default=checked)] 
    else:
      line = line + [sg.CBox(button_list[x] , size=(width, height), font=("Courier New", 9), key=btn_keyname, default=checked)] 
  return line

def createSimCheckBoxGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'CkBoxGroup'
  return line

def createPreviewCheckBoxGroupElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'ckbox'+ t1 + ' ' + text + ' ' * (width - len(t1))
  return line



""" format of string: header1, header2, header3,header4:combo(a,b,c),header5 """
"""   'PE'    : 'Paramedics:Combo(Yes:No)',  """

def createEditableTableElement(self, keyname, t1, text, width, height, pad, sub_layout):

  self.debug.info_message('createEditableTableElement t1: ' + str(t1) )

  unprocessed_strings = text
  column_headings = ''
  column_types = ''

  col_widths=[]

  for x in range (len(unprocessed_strings)):
    heading = ''
    if( ':Combo(' in unprocessed_strings[x]):
      split_string = unprocessed_strings[x].split(':',1)
      heading = split_string[0]
      coltype = split_string[1]
    else:
      self.debug.info_message('createEditableTableElement LOC2' )
      heading = unprocessed_strings[x]
      coltype = 'Text'

    self.debug.info_message('createEditableTableElement LOC3' )

    split_item = heading.split('\n')
    max_width = len(split_item[0])
    for header_row_count in range(len(split_item)):
      max_width = max(max_width, len(split_item[header_row_count]))

    col_widths.append(max_width+2)

    if(column_headings == ''):
      column_headings = heading
    else:
      column_headings = column_headings + ',' + heading

    self.debug.info_message('createEditableTableElement LOC4' )

    if(column_types == ''):
      column_types = coltype
    else:
      column_types = column_types + ',' + coltype

  self.debug.info_message('createEditableTableElement LOC5' )

  self.debug.info_message('createEditableTableElement column_headings:' + column_headings)
  self.debug.info_message('createEditableTableElement column_types:' + column_types)

  rows= 1
  cols=len(unprocessed_strings)

  meta_value = 'ET,' + str(rows) + ',' + str(cols) + ',' + column_types

  data = 'abc,def'.split(',')

  data = t1

  headings = text

  self.debug.info_message('createEditableTableElement col widths: ' + str(col_widths) )

  #select_mode=TABLE_SELECT_MODE_NONE 
  #TABLE_SELECT_MODE_BROWSE
  #TABLE_SELECT_MODE_EXTENDED

  line = [sg.Table(values=data, headings=headings,
                        col_widths=col_widths,
                        auto_size_columns=False,
                        justification='right',
                        num_rows=height,
                        #FIXME USED FOR MULTI LINE ROWS IN TABLE
                        #row_height=60,
                        alternating_row_color='lightgray',
                        key=keyname,
                        expand_x=True,
                        header_text_color = self.table_header_text_clr,
                        header_background_color = self.table_header_background_clr,
                        text_color = 'black',
                        background_color = 'white',
                        metadata=meta_value,
                        #display_row_numbers = True,
                        enable_click_events=True,
                        font=("Courier New", 9),
                        )]

  self.debug.info_message('createEditableTableElement LOC6' )

  return line

def createSimEditableTableElement(self, keyname, t1, text, width, height, pad, sub_layout):
  line =  'EditTable'
  return line

def createPreviewEditableTableElement(self, keyname, t1, text, width, height, pad, sub_layout):

  try:
    line = ''
    max_header_rows = 1
    col_widths = []

    """ calculate the column widths"""
    for x in range (len(text)):
      heading = ''
      if( ':Combo(' in text[x]):
        split_string = text[x].split(':',1)
        heading = split_string[0]
      else:
        heading = text[x]

      split_item = heading.split('\n')
      max_width = len(split_item[0])
      max_header_rows = max( len(split_item), max_header_rows)
      for header_row_count in range(len(split_item)):
        max_width = max(max_width, len(split_item[header_row_count]))

      col_widths.append(max_width+2)

    """ line """
    for col_count in range (len(text)):
      line = line + '-'
      line = line + '-' * col_widths[col_count]
    line = line + '-\n'

    """ print out the headers """
    for row_count in range (max_header_rows):
      for col_count in range (len(text)):
        line = line + '| '
        heading = ''
        if( ':Combo(' in text[col_count]):
          split_string = text[col_count].split(':',1)
          heading = split_string[0]
        else:
          heading = text[col_count]

        split_item = heading.split('\n')
        if(len(split_item)-1 < row_count):
          line = line + ' ' * (col_widths[col_count]-1)
        else:
          line = line + split_item[row_count] + ' ' * (col_widths[col_count] - len(split_item[row_count])-1)

      line = line + '|\n'

    """ line """
    for col_count in range (len(text)):
      line = line + '|'
      line = line + '-' * col_widths[col_count]
    line = line + '|\n'

    """ print out the data for each column """
    for row_count in range (len(t1)):
      row_item = t1[row_count]
      for col_count in range (len(row_item)):
        line = line + '| '
        line = line + row_item[col_count] + ' ' * (col_widths[col_count] - len(row_item[col_count])-1)
      line = line + '|\n'

    """ line """
    for col_count in range (len(text)):
      line = line + '-'
      line = line + '-' * col_widths[col_count]
    line = line + '-\n'


  except:
    self.debug.error_message("Exception in createPreviewEditableTableElement: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

  return line



class FormGui(object):


  """
  debug level 0=off, 1=info, 2=warning, 3=error
  """
  def __init__(self, group_arq, debug):  

    self.form_events = None
    self.form_dictionary = None
    self.group_arq = group_arq
    self.layout_inbox = None
    self.layout_outbox = None
    self.layout_compose = None
    self.layout_template = None
    self.layout_myinfo = None
    self.layout_settings = None
    self.layout_relay = None
    self.debug = debug
    self.tabgrp = None
    self.window = None
    self.table_lookup = None
    self.special_chars = '0@'
    self.compose_popup_window = None
    self.render_disabled_controls = False

    self.main_heading_background_clr     = 'red'
    self.sub_heading_background_clr      = 'green1'
    self.numbered_section_background_clr = 'yellow'
    self.table_header_background_clr     = 'cyan'
    self.main_heading_text_clr           = 'white'
    self.sub_heading_text_clr            = 'black'
    self.numbered_section_text_clr       = 'black'
    self.table_header_text_clr           = 'black'

    """ form designed debug code is verbose see notch this back to ERROR level unless needed"""
    self.debugForms = db.Debug(cn.DEBUG_ERROR)

    self.customized_headers=[['content_0', 4, 3, 'my\nfirst\ncol', 'my\nsecond\ncol', 'my\nthird\ncol', 'my\nfourth\ncol']]


    return

  def setComposePopupWindow(self, window):
    self.compose_popup_window = window

  def getComposePopupWindow(self):
    return self.compose_popup_window

  def setFormEvents(self, form_events):
    self.form_events = form_events
    return

  def setFormDictionary(self, form_dictionary):
    self.form_dictionary = form_dictionary
    return

  def setGroupArq(self, group_arq):
    self.group_arq = group_arq
    return

  def isCommand(self, char):
    if(char in self.special_chars):
      return True
    else:
      return False	
      
      	
  """ This is the forward lookup """

  field_lookup = {}
  """
  field_lookup = {
    'T1'    : ['Title', 5, 1, createTextElement, createSimTextElement, False,createPreviewTextElement],
    'T2'    : ['To', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T3'    : ['From', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T4'    : ['Subj.', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T5'    : ['Date', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T6'    : ['Time', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T7'    : ['Message:', 19, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T8'    : ['Inc.:', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T9'    : ['Pos.', 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T10'   : ["App'd", 5, 1, createTextElement, createSimTextElement,False,createPreviewTextElement],
    'T11'   : ["", 1, 1, createTextElement, createSimTextElement,False,createPreviewInputElement],
    'I1'    : ['',47, 1, createInputElement, createSimInputElement,True,createPreviewInputElement],
    'I2'    : ['',30, 1, createInputElement, createSimInputElement,True,createPreviewInputElement],
    'I3'    : ['',10, 1, createInputElement, createSimInputElement,True,createPreviewInputElement],
    'I4'    : ['',53, 20, createInputElement, createSimInputElement,True,createPreviewInputElement],
    'I5'    : ['',20, 1, createInputElement, createSimInputElement,True,createPreviewInputElement],
    'I6'    : ['',0, 1, createInputElement, createSimInputElement,True,createPreviewInputElement],
  }
  """

  field_names = {

    #################################
    # sequence of '0' control codes #
    #################################

    #""" column control codes """
    '00'    : 'NewColumn',
    '01'    : 'EndColumn',
    '02'    : 'StartColumn',


    #""" separator control code """
    '03'    : '10xSeparator',
    '04'    : '15xSeparator',
    '05'    : '20xSeparator',
    '06'    : '30xSeparator',
    '07'    : '60xSeparator',
    '08'    : '80xSeparator',

    #""" sub heading control code """
    '09'    : 'SubHeading',

    #""" combo control code """
    '0A'    : 'Combo',

    #""" main heading control code """
    '0B'    : 'MainHeading',

    #""" numbered section text """
    '0C'    : 'NumberedSection',
    '0D'    : 'NumberedSection +1',
    '0E'    : 'NumberedSection -1',

    #""" number the column headings automatically """
    '0F'    : 'NumberedSecTable',

    #""" add a filler field that spans number of filelds on relative line index """
    '0G'    : 'FillerSpan 5,-1',
    '0H'    : 'FillerSpan 5,1',

    '0I'    : 'LineAlign 1,-2',
    '0J'    : 'LineAlign 1,-3',

    #""" add a filler field that spans number of filelds on relative line index """
    '0K'    : 'FillerSpan 1,-1',
    '0L'    : 'FillerSpan 2,-1',
    '0M'    : 'FillerSpan 3,-1',
    '0N'    : 'FillerSpan 4,-1',

    #""" add a filler field that spans number of filelds on relative line index """
    '0O'    : 'FillerSpan 1,1',
    '0P'    : 'FillerSpan 2,1',
    '0Q'    : 'FillerSpan 3,1',
    '0R'    : 'FillerSpan 4,1',


    #""" radio button control code """
    '0S'    : 'RadioButton',

    #""" checkbox control code """
    '0T'    : 'Checkbox',

    #""" align field with prev row field# 6 """
    '0U'    : 'FillerPad 1',
    '0V'    : 'FillerPad 2',
    '0W'    : 'FillerPad 3',
    '0X'    : 'FillerPad 4',
    '0Y'    : 'FillerPad 5',
    '0Z'    : 'FillerPad 6',

    #################################
    # sequence of '@' control codes #
    #################################
    '@1'    : 'Spacer 5',
    '@2'    : 'Spacer 10',
    '@3'    : 'Spacer 15',
    '@4'    : 'Spacer 20',
    '@5'    : 'Spacer 25',
    '@6'    : 'Spacer 30',
    '@7'    : 'Spacer 35',
    '@8'    : 'Spacer 40',
    '@9'    : 'Spacer 45',
    '@A'    : 'Spacer 50',
    '@B'    : 'Spacer 55',
    '@C'    : 'Spacer 60',
    '@D'    : 'Spacer 65',
    '@E'    : 'Spacer 70',
    '@F'    : 'Spacer 75',
    '@G'    : 'Spacer 80',

    '@H'    : '3xLineRepeat',
    '@I'    : '5xLineRepeat',
    '@J'    : '10xLineRepeat',  
    '@K'    : '15xLineRepeat',
    '@L'    : '20xLineRepeat',  
    '@M'    : '30xLineRepeat',
    '@N'    : '40xLineRepeat',
    '@O'    : '50xLineRepeat',


    #""" Radio button group """
    '@Q'    : 'RadioBtnGroup',
    #""" option menu """
    '@R'    : 'OptionMenu',
    #""" option menu """
    '@S'    : 'CkBoxGroup',


    #################################
    # sequence of '#' control codes #
    #################################

    #""" table rows ????"""
    '#1'    : 'EditTable 5',
    '#2'    : 'EditTable 10',
    '#3'    : 'EditTable 20',
    '#4'    : 'EditTable 40',


    #%CALLSIGN%
    '#5'    : 'Macro %CALLSIGN%',
    #%OPERATORNAME%
    '#6'    : 'Macro %OPERATORNAME%',
    #%OPERATORTITLE%
    '#7'    : 'Macro %OPERATORTITLE%',
    #%INCIDENTNAME%
    '#8'    : 'Macro %INCIDENTNAME%',
    #%DATE%
    '#9'    : 'Macro %DATE%',
    #%TIME%
    '#A'    : 'Macro %TIME%',
    #%DATETIME%
    '#B'    : 'Macro %DATETIME%',
    #%LOCALTIME%
    '#C'    : 'Macro %ZULUTIME%',
    #%ZULUTIME%
    '#D'    : 'Macro %ZULUDATETIME%',
    #%UTCTIME%
    '#E'    : 'Macro %UTCTIME%',
    #%UTCTIME%
    '#F'    : 'Macro %UTCDATETIME%',
    #%GROUPNAME%
    '#G'    : 'Macro %GROUPNAME%',
    #%GPSLAT%
    '#H'    : 'Macro %GPSLAT%',
    #%GPSLONG%
    '#I'    : 'Macro %GPSLONG%',
    #%GRIDSQUARE%
    '#J'    : 'Macro %GRIDSQUARE%',
    #%QTHLOCATION%
    '#K'    : 'Macro %QTHLOCATION%',



    #############################
    # sequence of numeric codes #
    #############################
    '1A'    : '13x1 %CALLSIGN%',
    '1B'    : '35x1 %OPERATORNAME%',
    '1C'    : '23x1 %DATETIME%',
    '1D'    : '10x1 %DATE%',
    '1E'    : '10x1 %TIME%',
    '1F'    : '30x1 %INCIDENTNAME%',
    '1G'    : '30x1 %OPERATORTITLE%',
    '1'     : '1x1',
    '2'     : '2x1',
    '3'     : '3x1',
    '4'     : '4x1',
    '5'     : '5x1',
    '6'     : '6x1',
    '7'     : '7x1',
    '8'     : '8x1',
    '9'     : '9x1',
    '10'    : '10x1',
    '11'    : '11x1',
    '12'    : '12x1',
    '13'    : '13x1',
    '14'    : '14x1',
    '15'    : '15x1',
    '16'    : '16x1',
    '17'    : '17x1',
    '18'    : '18x1',
    '19'    : '19x1',
    '20'    : '20x1',
    '21'    : '25x1',
    '22'    : '30x1',
    '23'    : '35x1',
    '24'    : '40x1',
    '25'    : '45x1',
    '26'    : '50x1',
    '27'    : '55x1',
    '28'    : '60x1',
    '29'    : '65x1',
    '30'    : '70x1',
    '31'    : '75x1',
    '32'    : '80x1',
    '33'    : '60x10',
    '34'    : '70x10',
    '35'    : '80x10',
    '36'    : '90x10',
    '37'    : '91x10',
    '38'    : '92x10',
    '39'    : '93x10',
    '40'    : '94x10',
    '41'    : '90x5',
    '42'    : '0x1',
    '43'    : '0x3',
    '44'    : '0x5',
    '45'    : '0x10',
    '46'    : '0x15',
    '47'    : '0x20',
  
    'A1'    : 'Approved by',
    'A2'    : 'Assignment',
    'A3'    : 'Approved by (CUL)',
    'A4'    : 'Assignment List (ICS 204)',
    'A5'    : 'Add',
    'A6'    : 'Approved by Incident Commander',
    'A7'    : 'Agency / Organization Representatives',
    'A8'    : 'Agency / Organization',
    'A9'    : 'Air Ops Branch Director',
    'AA'    : 'Ambulance Services',
    'AB'    : 'Address and Phone',
    'AC'    : 'ALS',
    'AD'    : 'Address\nLatitude and Longitude\nif Helipad',
    'AE'    : 'Air',
    'AF'    : 'Approved by (Safety Officer)',
    'AG'    : 'Assignment / Location',
    'AH'    : 'Activity Log',
    'AI'    : 'Activity Log (ICS 214)',
    'AJ'    : 'Attn',

    'B1'    : 'Basic Radio Channel Use',
    'B2'    : 'Branch',
    'B3'    : 'Branch Director',
    #""" spacer text field """
    'B4'    : '     ',
    #""" vertical separator text field """
    'B5'    : '|',
    'B6'    : 'BLS',
    'B7'    : 'Burn Center',
    'B8'    : 'Bulletin #',
    'B9'    : 'Bulletin',
    'BA'    : 'Burn Center:Combo(Yes:No)',

    'C1'    : 'Call Sign',
    'C2'    : 'Ch#',
    'C3'    : 'Channel Name',
    'C4'    : 'COMMUNICATIONS LOG (ICS 309)',
    'C5'    : 'Contact (e.g. \nPhone, Pager,\nradio frequency, etc)',
    'C6'    : 'Communications (radio and/or phone contact numbers needed for this assignment)',
    'C7'    : 'Chief',
    'C8'    : 'Communications Unit',
    'C9'    : 'Cost Unit',
    'CA'    : 'Comp / Claims Unit',
    'CB'    : 'Contact\nNumber(s) /\nFrequency',
    'CC'    : 'Cost',
    'CD'    : 'Communications Resource Availability Worksheet (ICS 217A)',
    'CE'    : 'Channel Configuration',
    'CF'    : 'Channel Name /\nTrunked Radio\nSystem Talkgroup',
    'CG'    : 'Comments',



    'D1'    : 'Date',
    'D2'    : 'Date / Time Prepared',
    'D3'    : 'Date / Time',
    'D4'    : 'Date From',
    'D5'    : 'Date To',
    'D6'    : 'Division',
    'D7'    : 'Division / Group Supervisor',
    'D8'    : 'Deputy',
    'D9'    : 'Division / Group',
    'DA'    : 'Documentation Unit',
    'DB'    : 'Demobilization Unit',
    'DC'    : 'Director',
    'DD'    : 'Detailed Item Description, Vital Characteristics, Brand, Specs, Experience, Size, etc.',
    'DE'    : 'Delivery / Reporting Location',
    'DF'    : 'Description',
    'DG'    : 'Date / Time (Optional)',
    'DH'    : '(Date / Time) From',
    

    'E1'    : 'Express Sender',
    'E2'    : 'Estimated',
    'E3'    : 'Eligible Users',
    'E4'    : 'Email',

    'F1'    : 'From',
    'F2'    : 'For Operational Period',
    'F3'    : 'Function',
    'F4'    : 'From (Name / Position)',
    'F5'    : 'Facilities Unit',
    'F6'    : 'Food Unit',
    'F7'    : 'Finance / Administration Section',
    'F8'    : 'Finance',
    'F9'    : 'Finance Section Chief Name',
    'FA'    : 'Frequency Band',
    'FB'    : 'From (Name/Group)',
    'FC'    : 'For (Name/Group)',

    'G1'    : 'Group',
    'G2'    : 'General Situational Awareness',
    'G3'    : 'Ground Support Unit',
    'G4'    : 'Ground',
    'G5'    : 'General Message (ICS 213)',

    'H1'    : 'Hospitals',
    'H2'    : 'Hospital Name',
    'H3'    : 'Helipad',
    'H4'    : 'Hazards / Risks',
    'H5'    : 'Home Agency and Unit',
    'H6'    : 'Helipad:Combo(Yes:No)',

    'I1'    : 'Incident Name',
    'I2'    : 'IAP Page',
    'I3'    : 'INCIDENT RADIO COMMUNICATIONS PLAN (ICS 205)',
    'I4'    : 'Information',
    'I5'    : 'Incident Objectives (ICS 202)',
    'I6'    : 'Incident Actiona Plan (the items checked below are included in this Incident Action Plan)',
    'I7'    : 'ICS 203',
    'I8'    : 'ICS 204',
    'I9'    : 'ICS 205',
    'IA'    : 'Indicate cell, pager, or radio (frequency/system/channel)',
    'IB'    : 'ICS 205A',
    'IC'    : 'ICS 206',
    'ID'    : 'ICS 207',
    'IE'    : 'ICS 208',
    'IF'    : 'ICS 202',
    'IG'    : 'Incident Commander(s) and Command Staff',
    'IH'    : 'IC / UCs',
    'II'    : 'Item Description',
    'IJ'    : 'Incident Action Safety Analysis (ICS 215A)',
    'IK'    : 'Incident Number',
    'IL'    : 'Incident Area',
    'IM'    : 'Individual Activity Log (ICS 214A)',
    'IN'    : 'ICS Section',
    'IO'    : 'ICS Position',
    'IP'    : 'Information,Read Soon,READ NOW',
    'IQ'    : 'Individual Name',

    'K1'    : 'Kind',

    'L1'    : 'Leader',
    'L2'    : 'Liason Officer',
    'L3'    : 'Location',
    'L4'    : 'Level of Service',
    'L5'    : 'Level',
    'L6'    : 'Low',
    'L7'    : 'Logistics',
    'L8'    : 'Logistics Order Number',
    'L9'    : 'Level of Service:Combo(ALS:BLS)',

    'M1'    : 'Message',
    'M2'    : 'Mode\n(A,D,M)',
    'M3'    : 'Map / Chart',
    'M4'    : 'Medical Unit',
    'M5'    : 'Medical Plan',
    'M6'    : 'Medical Aid Stations',
    'M7'    : 'Medical Emergency Procedures (Be Brief)',
    'M8'    : 'Medical Plan (ICS 206)',
    'M9'    : 'Mitigations',
    'MA'    : 'Major Events',
    'MB'    : 'Method(s) of contact\nradio frequency\nphone, cell#, etc',

    'N1'    : 'Name / Contact Number(s)',
    'N2'    : '# or\nPersons',
    'N3'    : 'Notes',
    'N4'    : 'Name / Function',
    'N5'    : 'Name',
    'N6'    : 'No',
    'N7'    : 'New Status:Combo(---:Available:Assigned:OUT OF SERVICE)',
    'N8'    : 'Needed Date / Time (local 24 hr)',
    'N9'    : 'Name of Supplier',
    'NA'    : 'Name of Auth Logistics Rep',
    'NB'    : 'Notable Activities',
    'NC'    : 'N or W',

    'O1'    : 'Operator Name',
    'O2'    : 'Operational Period',
    'O3'    : 'Operations Personnel',
    'O4'    : 'Operations Section Chief',
    'O5'    : 'Objectives',
    'O6'    : 'Operational Period Command Emphasis',
    'O7'    : 'Other Attachments',
    'O8'    : 'Organizational Assignment List (ICS 203)',
    'O9'    : 'Operations Section',
    'OA'    : 'Order',
    'OB'    : 'Order was Requested by',

    'P1'    : 'Position / Title',
    'P2'    : 'Page #',
    'P3'    : 'Primary Contact. Indicate\ncell, pager or radio\n(frequency/system/channel)',
    'P4'    : 'Prepared by',
    'P5'    : 'Planning Section',
    'P6'    : 'Public Info Officer',
    'P7'    : 'Procurement Unit',
    'P8'    : 'Paramedics',
    'P9'    : 'Prepared by (MUL)',
    'PA'    : 'Priority',
    'PB'    : 'Point of Contact',
    'PC'    : 'Prepared by (Safety Officer)',
    'PD'    : 'Prepared by (Operations Section Chief)',
    'PE'    : 'Paramedics:Combo(Yes:No)',
	
    'Q1'    : 'Qty',
    'Q2'    : 'Quick Message',
    'Q3'    : '---,Available,Assigned,OUT OF SERVICE',
    'Q4'    : '---,VHF LOW,VHF HIGH,UHF,700,800,HF,OTHER',

    'R1'    : 'RX Freq',
    'R2'    : 'RX Tone',
    'R3'    : 'Remarks',
    'R4'    : 'Resources Assigned\nResource Identifier',
    'R5'    : 'Reporting Location, Special\nEquipment and Supplies,\nRemarks, Notes, Information',
    'R6'    : 'Resource Unit',
    'R7'    : 'Resource Status Change (ICS 210)',
    'R8'    : 'Resource #',
    'R9'    : 'Resource Request Message (ICS 213 RR)',
    'RA'    : 'Resource Request Number',
    'RB'    : 'Requester',
    'RC'    : 'Requested',
    'RD'    : 'Requested by Name / Position',
    'RE'    : 'Routine',
    'RF'    : 'Reply / Comments from Finance',
    'RG'    : 'RX\nFreq',
    'RH'    : 'RX\nTone/NAC',
    'RI'    : 'RX\nN or W',

    'S1'    : 'Subject',
    'S2'    : 'Station ID',
    'S3'    : 'Special Instructions (Be Brief)',
    'S4'    : 'Staging Area',
    'S5'    : 'Special Equipment and Supplies',
    'S6'    : 'Special Instructions',
    'S7'    : 'Safety Plan Required',
    'S8'    : 'Safety Plan(s) Located at',
    'S9'    : 'Signature',
    'SA'    : 'Staging Area',
    'SB'    : 'Safety Officer',
    'SC'    : 'Situation Unit',
    'SD'    : 'Supply Unit',
    'SE'    : 'Safety Message / Plan (ICS 208)',
    'SF'    : 'Safety Message / Expanded Safety Message, Safety Plan, Site Safety Plan',
    'SG'    : 'Substitutes and / or Suggested Sources',
    'SH'    : 'Section Chief Name for Approval',
    'SI'    : 'Supplier Phone / Fax / Email',
    'SJ'    : 'Send to Address',
    'SK'    : 'Station ID\nFrom',
    'SL'    : 'Station ID\nTo',
    
    'T1'    : 'To (Name/Position)',
    'T2'    : 'Time',
    'T3'    : 'Task',
    'T4'    : 'Task Name',
    'T5'    : "Track and Increment your page #'s (Default is 1)",
    'T6'    : 'To',
    'T7'    : 'Time From',
    'T8'    : 'Time To',
    'T9'    : 'TX Freq',
    'TA'    : 'TX Tone',
    'TB'    : 'Task #',
    'TC'    : 'Technical Specialists',
    'TD'    : 'Time Unit',
    'TE'    : 'Transportation',
    'TF'    : 'Travel Time\nAir',
    'TG'    : 'Trauma\nCenter',
    'TH'    : 'Time and Date of Change',
    'TI'    : 'Type',
    'TJ'    : 'TX\nFreq',
    'TK'    : 'TX\nTone/NAC',
    'TL'    : 'Test1,Test2,Test3,test4',
    'TM'    : 'Trauma Center:Combo(No:Yes - Level I:Yes - Level I & II:Yes - Level III:Yes - Level IV)',
    'TN'    : 'Travel Time\nGround',
    'TO'    : 'TX\nN or W',

    'U1'    : 'Urgent',

    'W1'    : 'Work Assignments',
    'W2'    : 'Weather forecast / Tides / Currents',
    'W3'    : 'Worksheet Incident or Event Name',

    'Y1'    : 'Yes',
    'Y2'    : 'Yes,No',
    'Y3'    : 'Yes - Level',
    
    'Z1'    : 'Zone\nGrp',

  }

  reverse_field_names = {}
  

  def createFieldLookup(self):
    for key in self.field_names:
      if(key[0].isalpha()):
        value_string = self.field_names.get(key)
        string_len = len(value_string)
        self.debug.info_message("string length is: " + str(string_len) )
        new_len = (math.ceil((string_len / 5.0)))*5
        self.debug.info_message("new string length is: " + str(new_len) )
        data = [value_string, new_len, 1, createTextElement, createSimTextElement, False, createPreviewTextElement]
        self.field_lookup[key] = data
      elif(key[0].isdigit()):
        if(key[0] == '0'):
          self.debug.info_message("Handle zero codes\n")
          """ format:     '0F'    : 'LineAlign 1,-1',  these numbers are *relative* to the current line index"""
          if('LineAlign' in self.field_names.get(key)):
            split_string = self.field_names.get(key).split(' ',1)
            split_string2 = split_string[1].split(',',1)
            int_width  = int(split_string2[0])
            int_height = int(split_string2[1])
            control_type = split_string[0]
            data = [control_type, int_width, int_height, createInputElement, createSimInputElement, False, createPreviewInputElement]		
            self.field_lookup[key] = data
            """ format:    '0L'    : 'FillerSpan 2,-1',"""
          elif('FillerSpan' in self.field_names.get(key)):
            split_string = self.field_names.get(key).split(' ',1)
            split_string2 = split_string[1].split(',',1)
            int_width  = int(split_string2[0])
            int_height = int(split_string2[1])
            control_type = split_string[0]
            data = [control_type, int_width, int_height, createTextElement, createSimTextElement, False, createPreviewTextElement]		
            self.field_lookup[key] = data
          elif('FillerPad' in self.field_names.get(key)):
            split_string = self.field_names.get(key).split(' ',1)
            int_width  = int(split_string[1])
            int_height = 0
            control_type = split_string[0]
            data = [control_type, int_width, int_height, createTextElement, createSimTextElement, False, createPreviewTextElement]		
            self.field_lookup[key] = data
          elif('Checkbox' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createCkboxElement, createSimCkboxElement, True, createPreviewCkboxElement]		
            self.field_lookup[key] = data
          elif('RadioButton' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createRadioElement, createSimRadioElement, True, createPreviewRadioElement]		
            self.field_lookup[key] = data
          elif('Combo' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createComboElement, createSimComboElement, True, createPreviewComboElement]		
            self.field_lookup[key] = data
          elif('MainHeading' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createMainHeadingElement, createSimMainHeadingElement, False, createPreviewMainHeadingElement]		
            self.field_lookup[key] = data
          elif('SubHeading' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createSubHeadingElement, createSimSubHeadingElement, False, createPreviewSubHeadingElement]		
            self.field_lookup[key] = data

          elif('NumberedSection' in self.field_names.get(key)):
            int_width  = 0
            int_height = 0
            split_string = self.field_names.get(key).split(' ',1)
            control_type = split_string[0]

            if(len(split_string) == 2):
              int_width  = int(split_string[1])

            data = [control_type, int_width, int_height, createNumberedSectionElement, createSimNumberedSectionElement, False, createPreviewNumberedSectionElement]		
            self.field_lookup[key] = data

          elif('NumberedSecTable' in self.field_names.get(key)):
            int_width  = 0
            int_height = 0
            control_type = self.field_names.get(key)
            data = [control_type, int_width, int_height, createNumberedSectionElement, createSimNumberedSectionElement, False, createPreviewNumberedSectionElement]		
            self.field_lookup[key] = data

          elif('Separator' in self.field_names.get(key)):
            split_string = self.field_names.get(key).split('x',1)
            int_width    = int(split_string[0])
            control_type = split_string[1]
            int_height = 0
            data = [control_type, int_width, int_height, createSeparatorElement, createSimSeparatorElement, False, createPreviewSeparatorElement]		
            self.field_lookup[key] = data
          elif('StartColumn' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createColumnElement, createSimColumnElement, False, createPreviewColumnElement]		
            self.field_lookup[key] = data
          elif('EndColumn' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createColumnElement, createSimColumnElement, False, createPreviewColumnElement]		
            self.field_lookup[key] = data
          elif('NewColumn' in self.field_names.get(key)):
            control_type = self.field_names.get(key)
            int_width  = 0
            int_height = 0
            data = [control_type, int_width, int_height, createColumnElement, createSimColumnElement, False, createPreviewColumnElement]		
            self.field_lookup[key] = data
          else:
            split_string = self.field_names.get(key).split('x',1)
            int_width  = int(split_string[0])
            int_height = 0
            control_type = split_string[1].split(' ')[0]
            data = [control_type, int_width, int_height, createInputElement, createSimInputElement, True, createPreviewInputElement]		
            self.field_lookup[key] = data
        else:	
          #"""    '20'    : '20x1',               input field """
          split_string = self.field_names.get(key).split('x',1)
          int_width  = int(split_string[0])
          split_string2 = split_string[1].split(' ',1)
          if(len(split_string2) == 1):
            # this is input field 			  
            int_height = int(split_string2[0])
            data = ['', int_width, int_height, createInputElement, createSimInputElement, True, createPreviewInputElement]		
            self.field_lookup[key] = data
          else:  
            # this is line repeat code or dynamic content macro
            int_height = int(split_string2[0])
            data = [split_string2[1], int_width, int_height, createInputElement, createSimInputElement, True, createPreviewInputElement]		
            self.field_lookup[key] = data

      elif(key[0] == '@'):
        self.debug.info_message("@ control code\n")
        if('Spacer' in self.field_names.get(key)):
          split_string = self.field_names.get(key).split(' ',1)
          int_width  = int(split_string[1])
          int_height = 0
          control_type = split_string[0]
          data = [control_type, int_width, int_height, createTextElement, createSimTextElement, False, createPreviewTextElement]		
          self.field_lookup[key] = data
        elif('RadioBtnGroup' in self.field_names.get(key)):
          control_type = self.field_names.get(key)
          int_width  = 0
          int_height = 0
          data = [control_type, int_width, int_height, createRadioGroupElement, createSimRadioGroupElement, True, createPreviewRadioGroupElement]		
          self.field_lookup[key] = data
        elif('CkBoxGroup' in self.field_names.get(key)):
          control_type = self.field_names.get(key)
          int_width  = 0
          int_height = 0
          data = [control_type, int_width, int_height, createCheckBoxGroupElement, createSimCheckBoxGroupElement, True, createPreviewCheckBoxGroupElement]		
          self.field_lookup[key] = data
        elif('OptionMenu' in self.field_names.get(key)):
          control_type = self.field_names.get(key)
          int_width  = 0
          int_height = 0
          data = [control_type, int_width, int_height, createOptionMenuElement, createSimOptionMenuElement, True, createPreviewOptionMenuElement]		
          self.field_lookup[key] = data
        else:	
          #"""    '@J'    : '10xLine Repeat',     repeat line code"""
          split_string = self.field_names.get(key).split('x',1)
          int_width  = int(split_string[0])
          int_height = int(split_string[0])
          data = [split_string[1], int_width, int_height, createInputElement, createSimInputElement, True, createPreviewInputElement]		
          self.field_lookup[key] = data
      elif(key[0] == '#'):
        self.debug.info_message("# control code\n")
        if('EditTable' in self.field_names.get(key)):
          split_string = self.field_names.get(key).split(' ',1)
          int_width  = 0
          int_height = int(split_string[1])
          control_type = split_string[0]
          data = [control_type, int_width, int_height, createEditableTableElement, createSimEditableTableElement, True, createPreviewEditableTableElement]		
          self.field_lookup[key] = data
        elif('Macro' in self.field_names.get(key)):
          data = [self.field_names.get(key), 0, 0, createTextElement, createSimTextElement, False, createPreviewTextElement]		
          self.field_lookup[key] = data

    return

  def createTableFromNames(self):
    table_list = []	  
    for key, value in sorted(self.field_names.items()):    
      table_list.append(value)
    self.table_lookup = table_list  
    return table_list

  def createReverseLookup(self):
    for key in self.field_names:
      value = self.field_names.get(key)
      self.reverse_field_names[value]=key			   
    return self.reverse_field_names


  def createInboxViewReplyWindow(self, formname, form_content, category, msgto, filename, message_id, subject, use_dynamic_content_macro, show_headers, is_reply):
    self.debug.info_message("CREATE INBOX VIEW REPLY WINDOW\n")
  
    """ static fields at the top of the form """

    self.debug.info_message("formname is: " + formname )
    self.debug.info_message("category is: " + category )
    self.debug.info_message("filename is: " + filename )

    combo_list_priority = 'Normal,High,Low'.split(',')

    layout_header = [sg.Button('Close')]

    self.debugForms.info_message("createInboxViewReplyWindow LOC 1\n")

    if(show_headers):
      layout_header = [
          [sg.Button('Close'),
           sg.Text('Form: ', size=(5, 1) ), 
           sg.InputText(formname, size=(15, 1), key='preview_form_type', disabled=True ), 
           sg.Text('MSGID:', size=(6, 1) ), 
           sg.InputText(message_id, size=(21, 1), key='preview_message_id', disabled=True ), 
           sg.Text('Priority:', size=(6, 1) ), 
           sg.Combo(combo_list_priority, key='preview_message_priority', enable_events=True)],
          [sg.Text('To:', size=(7, 1) ), 
           sg.InputText(msgto, size=(66, 1), key='preview_message_msgto' )], 
          [sg.Text('Subject:', size=(7, 1) ), 
           sg.InputText(subject, size=(66, 1), key='preview_form_subject' )], 
          [
           sg.Text('Category: ', size=(8, 1), visible=False ), 
           sg.InputText(category, size=(14, 1), key='preview_form_category', disabled=True, visible=False )], 
          [sg.Text('Filename: ', size=(8, 1), visible=False ), 
           sg.InputText(filename, size=(14, 1), key='preview_form_filename', disabled=True, visible=False )], 
          [sg.Button('Post To Outbox', size=(15, 1), key='btn_prev_post_to_outbox')],
          [sg.Text('_'*80 )],

      ]

    self.debugForms.info_message("createInboxViewReplyWindow LOC 2\n")

    if(self.group_arq.saamfram.isReply(message_id)):
      self.debugForms.info_message("createInboxViewReplyWindow LOC 3\n")
      mainID = self.group_arq.getOriginalSenderID(message_id)
      replyID = self.group_arq.getReplyID(message_id)
    else:
      mainID = message_id
      self.debugForms.info_message("createInboxViewReplyWindow LOC 4\n")


    self.debug.info_message("message ID: " + mainID + " \n")

    layout = []
    tab_layout = []

    if(is_reply):   
      mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)
      text_render, table_render, actual_render = self.renderPage(mytemplate, use_dynamic_content_macro, form_content)
      layout = actual_render
      callsign = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(replyID)
      tab_line = sg.Tab('Reply:' + callsign, layout, title_color='Green', background_color='Blue')
      tab_layout = tab_layout + [tab_line]

    pages = self.form_dictionary.getPagesKeyvalFromInboxDictionary(mainID)
    if (pages != None and len(pages)>1):
      self.debug.info_message("REPLY MULTI PAGE \n")
      for page_num in reversed (range(len(pages))):
        page_dictionary = pages.get(str(page_num))
        retrieved_formname = page_dictionary.get('formname')
        content = page_dictionary.get('content')
        mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(retrieved_formname)
        text_render, table_render, actual_render = self.renderPage(mytemplate, use_dynamic_content_macro, content)
        if(page_num == 0):
          callsign = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(mainID)
          layout = [ [sg.MLine(text_render, size=(92, 30), key='ml_inbox_view_preview', font=("Courier New", 12), autoscroll=True)],]
          tab_line = sg.Tab('Page ' + str(page_num+1) +':' + callsign, layout, title_color='Green', background_color='Blue')
          tab_layout = tab_layout + [tab_line]
        else:
          replyID = page_dictionary.get('replyid')
          callsign = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(replyID)
          layout = [ [sg.MLine(text_render, size=(92, 30), key='ml_inbox_view_preview', font=("Courier New", 12), autoscroll=True)],]
          tab_line = sg.Tab('Page ' + str(page_num+1) +':' + callsign, layout, title_color='Green', background_color='Blue')
          tab_layout = tab_layout + [tab_line]
    else:
      self.debug.info_message("SINGLE PAGE\n")

      if(pages == None):
        page_dictionary = self.form_dictionary.getPagesKeyvalFromOutboxDictionary(mainID)
        self.debug.info_message("acquiring page+dictionary from outbox")
      else:
        page_dictionary = pages.get('0')
        self.debug.info_message("acquiring page+dictionary from inbox pages(0)")

      retrieved_formname = page_dictionary.get('formname')
      content = page_dictionary.get('content')
      mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(retrieved_formname)
      text_render, table_render, actual_render = self.renderPage(mytemplate, use_dynamic_content_macro, content)

      layout = actual_render

      callsign = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(mainID)
      #tab_line = sg.Tab('Page 1' +':' + callsign, layout, title_color='Green', background_color='Blue')
      tab_line = sg.Tab('Page 1' +':' + callsign, layout, title_color='Green', background_color='SlateGray')
      tab_layout = tab_layout + [tab_line]
  
    self.tabgrp = [layout_header, [sg.TabGroup([tab_layout], tab_location='centertop', title_color='Blue', tab_background_color='Dark Gray',
                                               background_color='Dark Gray', selected_title_color='Black', selected_background_color='White', expand_x=True, expand_y=True )]]  

    multi_page_window = sg.Window(formname, self.tabgrp, resizable=True, default_element_size=(40, 1), grab_anywhere=False, disable_close=True)                       

    return (multi_page_window)


  """
  create a preview window to display the actual form 
  This is the dynamic window used to compose a message
  """
  def createDynamicPopupWindow(self, formname, form_content, category, msgto, filename, message_id, subject, use_dynamic_content_macro):

    self.debug.info_message("CREATE DYNAMIC POPUP WINDOW\n")
  
    """ static fields at the top of the form """

    self.debug.info_message("formname is: " + formname )
    self.debug.info_message("category is: " + category )
    self.debug.info_message("filename is: " + filename )
  
    layout = []

    combo_list_priority = 'Normal,High,Low'.split(',')

    layout = [
          [sg.Text('Form: ', size=(5, 1) ), 
           sg.InputText(formname, size=(15, 1), key='preview_form_type', disabled=True ), 
           sg.Text('MSGID:', size=(6, 1) ), 
           sg.InputText(message_id, size=(21, 1), key='preview_message_id', disabled=True ), 
           sg.Text('Priority:', size=(6, 1) ), 
           sg.Combo(combo_list_priority, default_value=combo_list_priority[0], key='preview_message_priority', enable_events=True)],
          [sg.Text('To:', size=(7, 1) ), 
           sg.InputText(msgto, size=(100, 1), key='preview_message_msgto' )], 
          [sg.Text('Subject:', size=(7, 1) ), 
           sg.InputText(subject, size=(100, 1), key='preview_form_subject' )], 
          [
           sg.Text('Category: ', size=(8, 1), visible=False ), 
           sg.InputText(category, size=(14, 1), key='preview_form_category', disabled=True, visible=False )], 
          [sg.Text('Filename: ', size=(8, 1), visible=False ), 
           sg.InputText(filename, size=(14, 1), key='preview_form_filename', disabled=True, visible=False )], 
          [sg.Text('_'*80 )],

    ]
    
    mytemplate = self.form_dictionary.getTemplateFromTemplateDictionary(formname, category, filename)

    self.debug.info_message("retrieved template: " + str(mytemplate) )

    try:
      text_render, table_render, actual_render = self.renderPage(mytemplate, use_dynamic_content_macro, form_content)
    except:
      self.debug.error_message("Exception in createDynamicPopupWindow: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    layout = layout + actual_render

    layout2 = [ [sg.Button('Hello')],]
    layout3 = [ [sg.Button('More')],]

    """ multipage tab not yet implemented """
    """
    self.tabgrp = [[sg.TabGroup([[
                             sg.Tab('Page 1', layout, title_color='Green', background_color=sg.DEFAULT_BACKGROUND_COLOR),
                             sg.Tab('Page 2', layout2, title_color='Blue',border_width =10, background_color='Green1' ),
                             sg.Tab('Page 3', layout3, title_color='Blue', background_color='Magenta1')]],
                       tab_location='centertop',
                       title_color='Blue', tab_background_color='Dark Gray', background_color='Dark Gray', selected_title_color='Black', selected_background_color='White' )]]  
    """
    """ single page tab for now """

    self.tabgrp = [[sg.TabGroup([[
                             sg.Tab('Page 1', layout, title_color='Green', background_color=sg.DEFAULT_BACKGROUND_COLOR, key='popup_main_tab1')]],
                       tab_location='centertop',
                       title_color='Blue', tab_background_color='Dark Gray', background_color='Dark Gray', selected_title_color='Black', selected_background_color='White', size=(930,1000) )]]  
    
    scrollable_tabgrp = [[sg.Button('Cancel'), sg.Button('Post To Outbox', key='btn_prev_post_to_outbox')], [sg.Col(self.tabgrp, background_color=sg.DEFAULT_BACKGROUND_COLOR, vertical_alignment = 'top', scrollable=True, expand_x=True, expand_y=True, key='sgcol')] ]
    multi_page_window = sg.Window(formname, scrollable_tabgrp, resizable=True, size=(980,700), default_element_size=(40, 1), grab_anywhere=False, disable_close=True)                       

    self.setComposePopupWindow(multi_page_window)

    return (multi_page_window)


  def renderPage(self, mytemplate, use_dynamic_content_macro, form_content):
    self.debug.info_message("renderPage")
    self.debug.info_message("type is:" + str(self))

    layout = []

    text_equiv = ''

    repeat_field = 1
    repeat_lines = 1
    next_repeat_lines = 1

    num_input_fld_on_line = []

    columns_list = []
    field_width = 0
    columns_list_line = ''
    modified_line = False
    
    existing_line_filler = 0

    text_field_padding = 0

    align_widths_adjustment_line = -1
    align_widths_anchor_line = -1

    table_data = []
    
    render_text_only_text = ''
    
    intercept_next_field = False
    intercept_type = ''
    intercept_field = ''

    col_row_text = []
    col_row_count = 0
    column_count = 0
    previous_cols_total_max_width = 0

    column_intercept = False
    column_layout = []
    column_intercept_type = ''
    column_intercept_field = ''
    window_line_columns = []

    table_header_string = ''
    table_header_list = []

    self.customized_headers=[]

    self.number_section_table_header = False
    
    for read_ahead in range(2):
      field_count = 0
      content_field_count = 0
      content_count = 0
      line_content_count = 0
      row_num = 1
      table_data = []
      numbered_section_count = 1

      """ loop around all of the rows (x)"""
      for x in range (2, len(mytemplate)):
        existing_line_filler = 0
        text_field_padding = 0
        new_field_widths = ''
        line_content_count = 0
        columns_list_line = ''
        modified_line = False

        line = mytemplate[x]

        self.debugForms.info_message("processing line : " + str(line) )

        split_string = line.split(',')
        repeat_lines = next_repeat_lines
        for rl in range(repeat_lines):
          self.debugForms.info_message("RL LOC 1\n")

          window_line_text = ''
          window_line = []
          """ loop around all of the fields in the row (y) """
          for y in range (len(split_string)):

            if(y == (len(split_string)-1) ):
              last_field = True
            else:
              last_field = False

            field = split_string[y]
            mylist = self.field_lookup[field]

            self.debugForms.info_message("Y LOC 1\n")

            if(mylist[5] == True):
              line_content_count = line_content_count + 1

            self.debugForms.info_message("Y LOC 2\n")

            if(read_ahead == 1 and rl == 0):
              self.debugForms.info_message("readahead: 1, rl: 0\n")
              if(field[0] == '0' and mylist[0]=='FillerSpan'):
                self.debug.info_message("do nothing here\n")
              else:
                if(y==0):
                  """ if this is a zero code set width to zero"""
                  if(field[0] == '0' or field[0] == '@' or field[0] == '#'):
                    columns_list_line = '0'
                  else:
                    columns_list_line = str(mylist[1])
                else:
                  if(field[0] == '0' or field[0] == '@' or field[0] == '#'):
                    columns_list_line = columns_list_line + ',' + '0'
                  else:
                    columns_list_line = columns_list_line + ',' + str(mylist[1])
              if(modified_line == True):
                columns_list[x-2] = columns_list_line
                self.debug.info_message("updating modified line columns_list[x-2] = " + str(columns_list[x-2]) )


            if(read_ahead == 0):
              if(rl == 0):
                self.debugForms.info_message("readahead: 0, rl: 0\n")
                if(y==0):
                  """ if this is a zero code set width to zero"""
                  if(field[0] == '0' or field[0] == '@' or field[0] == '#'):
                    columns_list.append('0')
                    columns_list_line = '0'
                  else:
                    columns_list.append(str(mylist[1]))
                    columns_list_line = str(mylist[1])
                  num_input_fld_on_line.append(str(line_content_count))
                else:
                  if(field[0] == '0' or field[0] == '@' or field[0] == '#'):
                    previous_string = columns_list[x-2]
                    columns_list[x-2] = previous_string + ',' + '0'
                    columns_list_line = columns_list_line + ',' + '0'
                  else:
                    previous_string = columns_list[x-2]
                    columns_list[x-2] = previous_string + ',' + str(mylist[1])
                    columns_list_line = columns_list_line + ',' + str(mylist[1])
                  temp_value = num_input_fld_on_line[x-2]
                  num_input_fld_on_line[x-2] = temp_value + ',' + str(line_content_count)

            elif(read_ahead == 1 and mylist[0]!='FillerSpan' and mylist[0]!='FillerPad'):
              self.debugForms.info_message("readahead: 1 and not FillerSpan or FillerPad\n")
              if(new_field_widths == ''):
                new_field_widths = str(mylist[1])
              else:
                new_field_widths = new_field_widths + ',' + str(mylist[1])
                
            """ handle the zero control codes """
            if(intercept_next_field == True):

              keyname = 'field_' + str(field_count)
              field_count = field_count + 1

              if(intercept_type=='Checkbox' and read_ahead == 1):
                self.debugForms.info_message("Checkbox\n")
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, mylist[0], '', field_width, 1, 0, None))
              elif(intercept_type=='RadioButton' and read_ahead == 1):
                self.debugForms.info_message("Radio Button\n")
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, mylist[0], '', field_width, 1, 0, None))
              elif(intercept_type=='RadioBtnGroup' and read_ahead == 1):
                mylist_intercept = self.field_lookup[intercept_field]
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                self.debugForms.info_message("Radio Button Group\n")
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                self.debugForms.info_message("content count is:" + str(content_count) )
                display_content = ''
                if(content_count < len(form_content)):
                  display_content = form_content[content_count]
                window_line = window_line + (mylist_intercept[3](self, keyname, display_content, mylist[0], field_width, 1, 0, None))
                window_line_text = window_line_text + ' ' + (mylist_intercept[6](self, keyname, display_content, mylist[0], field_width, 1, 0, None))
                content_count = content_count + 1  
              elif(intercept_type=='CkBoxGroup' and read_ahead == 1):
                mylist_intercept = self.field_lookup[intercept_field]
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                self.debugForms.info_message("Check Box Group\n")
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                self.debugForms.info_message("content count is:" + str(content_count) )
                window_line = window_line + (mylist_intercept[3](self, keyname, form_content[content_count], mylist[0], field_width, 1, 0, None))
                content_count = content_count + 1  
              elif(intercept_type=='OptionMenu' and read_ahead == 1):
                self.debugForms.info_message("Option Menu\n")
                mylist_intercept = self.field_lookup[intercept_field]
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, form_content[content_count], mylist[0], field_width, 1, 0, None))
                window_line_text = window_line_text + ' ' + (mylist_intercept[6](self, keyname, form_content[content_count], mylist[0], field_width, 1, 0, None))
                content_count = content_count + 1  
              elif(intercept_type=='Combo' and read_ahead == 1):
                self.debugForms.info_message("Combo\n")
                if(mylist_intercept[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, mylist[0], '', field_width, 1, 0, None))

              elif(intercept_type=='Macro' and read_ahead == 1):
                self.debugForms.info_message("Macro")
                mylist_intercept = self.field_lookup[intercept_field]
                keyname = 'content_' + str(content_field_count)
                content_field_count = content_field_count + 1

                mylist_intercept = self.field_lookup[intercept_field]
                field_width = int(mylist[1])
                field_height= 1

                dynamic_content_macro = mylist_intercept[0].split(' ', 1)[1]

                if(content_count >= len(form_content) or form_content[content_count] == ''):
                  window_line = window_line + (mylist[3](self, keyname, dynamic_content_macro, mylist[0], field_width, field_height, 0, None))
                  window_line_text = window_line_text + (mylist[6](self, keyname, dynamic_content_macro, mylist[0], field_width, field_height, 0, None))
                else:
                  window_line = window_line + (mylist[3](self, keyname, form_content[content_count], mylist[0], field_width, field_height, 0, None))
                  window_line_text = window_line_text + (mylist[6](self, keyname, form_content[content_count], mylist[0], field_width, field_height, 0, None))
                content_count = content_count + 1  

              elif(intercept_type=='EditTable' and read_ahead == 1):
                self.debugForms.info_message("EditTable")

                if(table_header_string == ''):
                  table_header_string = mylist[0]
                  table_header_list.append(mylist[0])
                else:
                  table_header_string = table_header_string + ',' + mylist[0]
                  table_header_list.append(mylist[0])
                self.debugForms.info_message("table_header_string: " + table_header_string)

                if(last_field == True):
                  self.debugForms.info_message("EditTable LOC2")
                  mylist_intercept = self.field_lookup[intercept_field]
                  if(mylist_intercept[5] == True):
                    keyname = 'content_' + str(content_field_count)
                    content_field_count = content_field_count + 1
                  self.debugForms.info_message("EditTable LOC3")
                  field_width = len(mylist[0])
                  self.debugForms.info_message("EditTable LOC4")

                  new_content_table = []
                  header_row = []
                  numcols_from_header = len(table_header_list)
                  header_row.append(keyname)
                  header_row.append(numcols_from_header)
                  header_row.append(3)

                  if(content_count < len(form_content) and form_content[content_count] != ''):
                    content_value = form_content[content_count]
                    content_count = content_count + 1
                    self.debugForms.info_message("EditTable rows,cols: " + content_value)
                    split_content = content_value.split(',')
                    rows = int(split_content[0])
                    cols = int(split_content[1])
                    for row_count in range(rows):
                      new_content_row = []
                      for col_count in range(cols):
                        header_row.append(table_header_list[col_count].split(':')[0])
                        if(content_count < len(form_content)):
                          new_content_row.append(form_content[content_count])
                          content_count = content_count + 1
                      new_content_table.append(new_content_row)
                    self.debugForms.info_message("EditTable new content table: " + str(new_content_table))
                  else:
                    content_count = content_count + 1
                    new_content_row = []
                    for col_count in range(numcols_from_header):
                      new_content_row.append('')

                      if(self.number_section_table_header == True):
                        header_row.append(str(numbered_section_count) + '. ' + table_header_list[col_count].split(':')[0])
                        numbered_section_count = numbered_section_count + 1
                      else:
                        header_row.append(table_header_list[col_count].split(':')[0])
                    """ create 1 empty row"""
                    new_content_table.append(new_content_row)

                  self.customized_headers.append(header_row)
                  self.debugForms.info_message("EditTable LOC5b")
                  window_line = window_line + (mylist_intercept[3](self, keyname, new_content_table, table_header_list, field_width, int(mylist_intercept[2]), 0, None))
                  self.debugForms.info_message("EditTable LOC5c")
                  window_line_text = window_line_text + (mylist_intercept[6](self, keyname, new_content_table, table_header_list, field_width, int(mylist_intercept[2]), 0, None))
                  self.debugForms.info_message("EditTable LOC5d")

                  self.number_section_table_header = False


              elif(intercept_type=='MainHeading' and read_ahead == 1):
                self.debugForms.info_message("Main Heading\n")
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, mylist[0], mylist[0], field_width, 1, 0, None))
                window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, mylist[0], mylist[0], field_width, 1, 0, None))
              elif(intercept_type=='SubHeading' and read_ahead == 1):
                self.debugForms.info_message("SubHeading\n")
                mylist_intercept = self.field_lookup[intercept_field]
                field_width = len(mylist[0])
                window_line = window_line + (mylist_intercept[3](self, keyname, mylist[0], mylist[0], field_width, 1, 0, None))
                window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, mylist[0], mylist[0], field_width, 1, 0, None))

              if(intercept_type=='EditTable' and read_ahead == 1):
                if(last_field == True):
                  intercept_next_field = False
                  intercept_type = ''
                  intercept_field = ''
                else:
                  self.debugForms.info_message("do nothing")
              else:
                intercept_next_field = False
                intercept_type = ''
                intercept_field = ''

            elif(field[0] == '0' or field[0] == '@' or field[0] == '#'):

              keyname = 'field_' + str(field_count)
              field_count = field_count + 1

              self.debugForms.info_message("0 control codes\n")
              if(mylist[0]=='Field'):
                self.debugForms.info_message("repeat field. CONTROL CODE  0: " + str(mylist[1]) )
                repeat_field = mylist[1]
              elif(mylist[0]=='Spacer'):
                self.debugForms.info_message("spacer CONTROL CODE  0: " + str(mylist[1]) )
                field_width = int(mylist[1])
                window_line = window_line + (mylist[3](self, keyname, '', '', field_width, 1, text_field_padding, None))
              elif(mylist[0]=='LineRepeat'):
                self.debugForms.info_message("repeat lines. CONTROL CODE  0: " + str(mylist[1]) )
                next_repeat_lines = int(mylist[1])
                """ format:     '0F'    : 'LineAlign 1,-1',  these numbers are *relative* to the current line index"""
              elif(mylist[0]=='LineAlign'):
                self.debugForms.info_message("Align lines. CONTROL CODE  0: " + str(mylist[1]) )
                align_widths_anchor_line     = int(mylist[1]) + x - 2
                align_widths_adjustment_line = int(mylist[2]) + x - 2
                self.debugForms.info_message("adjusting line values anchor,adjustment: " + str(align_widths_anchor_line) + ',' + str(align_widths_adjustment_line) )
                """ format:    '0L'    : 'FillerSpan 2,-1',"""
              elif(mylist[0]=='FillerPad' and read_ahead == 1):
                self.debugForms.info_message("Filler Pad. CONTROL CODE  0: " + str(mylist[1]) )
                text_field_padding = int(mylist[1])

              elif(mylist[0]=='Checkbox' and read_ahead == 1):
                self.debugForms.info_message("Checkbox. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='RadioButton' and read_ahead == 1):
                self.debugForms.info_message("RadioButton. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='RadioBtnGroup' and read_ahead == 1):
                self.debugForms.info_message("RadioButtonGroup. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='CkBoxGroup' and read_ahead == 1):
                self.debugForms.info_message("Check Box Group. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='OptionMenu' and read_ahead == 1):
                self.debugForms.info_message("OptionMenu. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='Combo' and read_ahead == 1):
                self.debugForms.info_message("Combo. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif('Macro ' in mylist[0] and read_ahead == 1):
                self.debugForms.info_message("Macro. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = 'Macro'
                intercept_field = field

              elif(mylist[0]=='EditTable' and read_ahead == 1):
                self.debugForms.info_message("EditTable. CONTROL CODE  0: " + str(mylist[1]) )
                table_header_string = ''
                table_header_list = []
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='MainHeading' and read_ahead == 1):
                self.debugForms.info_message("Main Heading. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='SubHeading' and read_ahead == 1):
                self.debugForms.info_message("SubHeading. CONTROL CODE  0: " + str(mylist[1]) )
                intercept_next_field = True
                intercept_type = mylist[0]
                intercept_field = field

              elif(mylist[0]=='NumberedSection' and read_ahead == 1):
                self.debugForms.info_message("NumberedSection. CONTROL CODE  0: " + str(mylist[1]) )
                field_width = 0
                numbering_offset = int(mylist[1])
                window_line = window_line + (mylist[3](self, keyname, '', str(numbered_section_count + numbering_offset) + '.', field_width, 1, text_field_padding, None))
                numbered_section_count = numbered_section_count + 1

              elif(mylist[0]=='NumberedSecTable' and read_ahead == 1):
                self.debugForms.info_message("NumberedSecTable. CONTROL CODE  0: " + str(mylist[1]) )

                """ modifier for the next table """
                self.number_section_table_header = True

              elif(mylist[0]=='Separator' and read_ahead == 1):
                self.debugForms.info_message("Separator. CONTROL CODE  0: " + str(mylist[1]) )
                field_width = int(mylist[1])
                window_line = window_line + (mylist[3](self, keyname, '', '', field_width, 1, text_field_padding, None))

              elif(mylist[0]=='StartColumn' and read_ahead == 1):
                self.debugForms.info_message("Start Column. CONTROL CODE  0: " + str(mylist[1]) )
                column_intercept = True
                column_intercept_type = mylist[0]
                column_intercept_field = field
                column_layout = []
                window_line_columns = []
                col_row_count = 0
                column_count = 0

              elif(mylist[0]=='NewColumn' and read_ahead == 1):
                self.debugForms.info_message("NewColumn. CONTROL CODE  0: " + str(mylist[1]) )

                if(mylist[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1

                mylist_column = self.field_lookup[field]
                field_width = 10 
                self.debugForms.info_message("NewColumn. keyname is: " + str(keyname) )
                self.debugForms.info_message("NewColumn. column layout is: " + str(column_layout) )
                window_line_columns = window_line_columns + (mylist_column[3](self, keyname, mylist[0], '', field_width, 1, 0, column_layout))

                max_col_row_width = 0
                col_row_padding = ''
                for col_row in range (len(col_row_text)):
                  if(len(col_row_text[col_row]) > max_col_row_width):
                    max_col_row_width = len(col_row_text[col_row])
                    previous_cols_total_max_width = max_col_row_width

                for col_row in range (len(col_row_text)):
                  if(len(col_row_text[col_row]) < max_col_row_width):
                    self.debugForms.info_message("adding col row padding: " + str((max_col_row_width - len(col_row_text[col_row]))) )
                    col_row_padding = ' '* (max_col_row_width - len(col_row_text[col_row]))
                    previous_col_row_text = col_row_text[col_row]
                    col_row_text[col_row] = previous_col_row_text + col_row_padding

                column_layout = []
                column_intercept_type = mylist[0]
                col_row_count = 0
                column_count = column_count + 1

              elif(mylist[0]=='EndColumn' and read_ahead == 1):
                self.debugForms.info_message("EndColumn. CONTROL CODE  0: " + str(mylist[1]) )

                if(mylist[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1

                mylist_column = self.field_lookup[field]
                field_width = 10 
                self.debugForms.info_message("EndColumn. keyname is: " + str(keyname) )
                self.debugForms.info_message("EndColumn. column layout is: " + str(column_layout) )
                window_line_columns = window_line_columns + (mylist_column[3](self, keyname, mylist[0], '', field_width, 1, 0, column_layout))

                for col_row in range (len(col_row_text)):
                  window_line_text = window_line_text + col_row_text[col_row] + '\n'
                  self.debugForms.info_message("set colrow text to: " + col_row_text[col_row] )

                layout = layout + [window_line_columns]
                column_layout = []
                column_intercept_type = mylist[0]
                window_line = []
                col_row_count = 0
              
              elif(mylist[0]=='FillerSpan' and read_ahead == 1):
                modified_line = True
                self.debugForms.info_message("Filler Span. CONTROL CODE  0: " + str(mylist[1]) )
                filler_span_fields = int(mylist[1])
                filler_span_anchor_line = int(mylist[2]) + x - 2

                self.debug.info_message("columns_list_line: " + str(columns_list_line) )

                columns_list[x-2] = new_field_widths
                next_line_values = columns_list[filler_span_anchor_line]
                this_line_values = columns_list[x-2]
                self.debug.info_message("next_line_values: " + str(next_line_values) )
                field_width = 0
                for filler_count in range(filler_span_fields):
                  field_width = field_width + int(next_line_values.split(',')[filler_count])
                self.debug.info_message("new field width: " + str(field_width) )
                if(y > 0):
                  self.debug.info_message("y is : " + str(y) )
                  subtract_value = 0

                  self.debug.info_message("LOC 1\n")

                  if(this_line_values != ''):
                    for existing_fields in range(y):
                      self.debug.info_message("LOC 2\n")
                      subtract_value = subtract_value + int(this_line_values.split(',')[existing_fields])
                      self.debug.info_message("subtract value is: " + str(subtract_value) )
                    if(field_width > subtract_value):
                      self.debug.info_message("LOC 3\n")
                      field_width = field_width - subtract_value
                      self.debug.info_message("new field width: " + str(field_width) )

                self.debug.info_message("LOC 4\n")

                if(columns_list_line == ''):
                  columns_list_line = str(field_width)
                else:
                  columns_list_line = columns_list_line + ',' + str(field_width)
					
                self.debug.info_message("columns_list_line: " + str(columns_list_line) )

                if(new_field_widths != ''):
                  new_field_widths = new_field_widths + ',' + str(field_width)
                else:
                  new_field_widths = str(field_width)

                self.debug.info_message("new field widths: " + str(new_field_widths) )
                self.debug.info_message("num_input_fld_on_line: " + str(num_input_fld_on_line) )
                self.debug.info_message("LOC 5\n")
                self.debug.info_message("text_field_padding: " + str(text_field_padding) )
                self.debug.info_message("LOC 6\n")

                window_line = window_line + (mylist[3](self, keyname, '', '', field_width, 1, text_field_padding, None))
                self.debugForms.info_message("field_count +1.    LOC 10\n")
                existing_line_filler = existing_line_filler + text_field_padding
                text_field_padding = 0

                self.debug.info_message("LOC 7\n")

            else:
              self.debugForms.info_message("resetting repeat lines to 1\n")
              next_repeat_lines = 1
          
              for rf in range(repeat_field):

                keyname = 'field_' + str(field_count)
                field_count = field_count + 1
                if(mylist[5] == True):
                  keyname = 'content_' + str(content_field_count)
                  content_field_count = content_field_count + 1

                if(read_ahead == 1 and x==align_widths_adjustment_line+2):
                  text_field_padding = 1
                  next_line_values = columns_list[align_widths_anchor_line]
                  self.debug.info_message("next_line_values: " + str(next_line_values) )
                  field_width = int(next_line_values.split(',')[y])
                  self.debug.info_message("override field width: " + str(field_width) )
                else:
                  field_width = int(mylist[1])

                if(content_count < len(form_content)):
                  if(use_dynamic_content_macro == True):
                    window_line = window_line + (mylist[3](self, keyname, mylist[0], mylist[0], field_width, mylist[2], text_field_padding, None))
                    window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, form_content[content_count], mylist[0], field_width, mylist[2], text_field_padding, None))
                  else:
                    window_line = window_line + (mylist[3](self, keyname, form_content[content_count], mylist[0], field_width, mylist[2], text_field_padding, None))
                    window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, form_content[content_count], mylist[0], field_width, mylist[2], text_field_padding, None))
                else:
                  if(use_dynamic_content_macro == True):
                    window_line = window_line + (mylist[3](self, keyname, mylist[0], mylist[0], field_width, mylist[2], text_field_padding, None))
                    window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, '', mylist[0], field_width, mylist[2], text_field_padding, None))
                  else:
                    window_line = window_line + (mylist[3](self, keyname, '', mylist[0], field_width, mylist[2], text_field_padding, None))
                    window_line_text = window_line_text + ' ' + (mylist[6](self, keyname, '', mylist[0], field_width, mylist[2], text_field_padding, None))

                if(mylist[5] == True):
                  content_count = content_count + 1  

              
              repeat_field = 1
              text_field_padding = 0
        
          if(read_ahead ==1):
            if(column_intercept == True):
              self.debugForms.info_message("column_intercept == True. column_intercept_type: " + str(column_intercept_type) + " \n")
              if(column_intercept_type == 'StartColumn'):
                column_intercept_type = ''
              elif(column_intercept_type == 'NewColumn'):
                column_intercept_type = ''
              elif(column_intercept_type == 'EndColumn'):
                column_intercept_type = ''
                column_intercept = False
                col_row_text=[]
              else:
                column_layout = column_layout + [window_line]

                if(len(col_row_text) <= col_row_count):
                  if(column_count > 0):
                    max_col_row_width = 0
                    col_row_padding = ''
                    for col_row in range (len(col_row_text)):
                      if(len(col_row_text[col_row]) > max_col_row_width):
                        max_col_row_width = len(col_row_text[col_row])
                    col_row_text.append(previous_cols_total_max_width * ' ' + window_line_text)
                    col_row_count = col_row_count + 1 
                  else:
                    col_row_text.append(window_line_text)
                    col_row_count = col_row_count + 1 
                else:
                  previous_text = col_row_text[col_row_count]
                  col_row_text[col_row_count] = previous_text + window_line_text
                  col_row_count = col_row_count + 1 

            if(column_intercept == False):
            #else:
              layout = layout + [window_line]
              split_str = window_line_text.split('\n')
              for z in range(len(split_str)):
                table_data.append( [split_str[z]] )
                render_text_only_text = render_text_only_text + split_str[z] + '\n'
                row_num = row_num + 1


    self.debug.info_message("COLUMNS LIST IS: " + str(columns_list) + " \n")
    self.debugForms.info_message("CREATE DYNAMIC POPUP WINDOW LOC 5\n")
	  
    return render_text_only_text, table_data, layout


  """
outbox dictionary items formatted as...
[u'ICS-213', u'v1.0', u'750cc9d8_2fc1d3d0', u'High', u'WH6ABC,WH6DEF,WH6GHI', u'I AM THE SUBJECT', 'Test', 'Lawrence', 'something important', 'Peter', 'nobody', 'Hello from rainy hawaii', '', '', u'This is a short message to show how the formatting works', '', '']
<FORMNAME> <Version> <ID> <PRIORITY> <TO list> <Subject> <contents.....>

sent dictionary items formatted as...
[u'Yes', u'ICS-213', u'v1.0', u'750cc9d8_2fc1d3d0', u'High', u'WH6ABC,WH6DEF,WH6GHI', u'I AM THE SUBJECT', 'Test', 'Lawrence', 'something important', 'Peter', 'nobody', 'Hello from rainy hawaii', '', '', u'This is a short message to show how the formatting works', '', '']
<CONFIRMED RCVD BY ALL> <FORMNAME> <Version> <ID> <PRIORITY> <TO list> <Subject> <contents.....>

inbox dictionary items formatted as...
[u'Yes', u'ICS-213', u'v1.0', u'750cc9d8_2fc1d3d0', u'High', u'WH6ABC,WH6DEF,WH6GHI', u'I AM THE SUBJECT', 'Test', 'Lawrence', 'something important', 'Peter', 'nobody', 'Hello from rainy hawaii', '', '', u'This is a short message to show how the formatting works', '', '']
<ALL CRC CHECKS PASSED> <FORMNAME> <Version> <ID> <PRIORITY> <TO list> <Subject> <contents.....>

  """
  def extractContentFromForm(self, values):

    return_list = []
    field_count = 0

    self.debug.info_message("VALUE IS: " + str(values) )

    formname = values['preview_form_type']	  
    category = values['preview_form_category']	  
    filename = values['preview_form_filename']	  
    mytemplate = self.form_dictionary.getTemplateFromTemplateDictionary(formname, category, filename)
    if(mytemplate != None):
      self.debug.info_message("returned template is: " + str(mytemplate) )

    popup_window = self.getComposePopupWindow()

    self.debug.info_message("popup window: " + str(popup_window) )

    repeat_field = 1
    repeat_lines = 1
    next_repeat_lines = 1
    already_appended = False

    try:
      for x in range (2, len(mytemplate)):
        line = mytemplate[x]
        split_string = line.split(',')
        repeat_lines = next_repeat_lines

        for rl in range(repeat_lines):
          window_line = []

          for y in range (len(split_string)):
            field = split_string[y]
            self.debug.info_message("field is: " + str(field) )
            mylist = self.field_lookup[field]
            self.debug.info_message("LOC 5\n")

            already_appended = False

            control_field = False
            if(field[0] == '0' or field[0] == '@'):
              control_field = True
            if(control_field and mylist[0]=='LineRepeat'):
              self.debugForms.info_message("repeat lines. CONTROL CODE  0: " + str(mylist[1]) )
              next_repeat_lines = int(mylist[1])

            elif(mylist[5] == True):
              keyname = 'content_' + str(field_count)

              """ PROCESS THE METADATA IN HERE for BG (button group) """
              metadata = popup_window[keyname].metadata
              self.debugForms.info_message("metadata: " + str(metadata) )
              if(metadata != None and 'BG' in metadata):
                self.debug.info_message("processing Button Group: \n")
                split_metadata = metadata.split(',')
                num_buttons = int(split_metadata[1])
                if(values[keyname]==True):    
                  self.debug.info_message("item selected: " + str(0) )
                  data_item = '0'
                else:
                  for btn_count in range (1, num_buttons):
                    btn_keyname = keyname + '_' + str(btn_count)
                    if(values[btn_keyname]==True):    
                      self.debug.info_message("item selected: " + str(btn_count) )
                      data_item = str(btn_count)
              elif(metadata != None and 'CG' in metadata):
                split_metadata = metadata.split(',')
                num_buttons = int(split_metadata[1])
                if(values[keyname]==True):    
                  self.debug.info_message("item selected: " + str(0) )
                  data_item = 'X'
                else:
                  data_item = ' '
                for btn_count in range (1, num_buttons):
                  btn_keyname = keyname + '_' + str(btn_count)
                  if(values[btn_keyname]==True):    
                    data_item = data_item + 'X'
                  else:
                    data_item = data_item + ' '
              elif(metadata != None and 'ET,' in metadata):
                self.debug.info_message("extractContentFromForm. EditTable: " + str(metadata) )
                split_metadata = metadata.split(',')
                num_rows = int(split_metadata[1])
                num_cols = int(split_metadata[2])


                tkinter_table = popup_window[keyname].Widget
                tkinter_numrows = len(tkinter_table.get_children())
                self.debug.info_message("extractContentFromForm. tkinter numrows: " + str(len(tkinter_table.get_children())) )

                """ create a content item (hidden field) for rows and cols used for parsing"""
                return_list.append(str(tkinter_numrows) + ',' + str(num_cols) )

                table = popup_window[keyname].get()
                self.debug.info_message("extractContentFromForm. Table: " + str(table) )
                for row_count in range(tkinter_numrows):
                  data_row = table[row_count]
                  for col_count in range(num_cols):
                    data_item = tkinter_table.item(row_count+1, "values")[col_count]
                    self.debug.info_message("extractContentFromForm. Item: " + str(data_item) )
                    return_list.append(data_item)
                already_appended = True

            #elif(metadata != None and 'OM' in metadata):
            #  split_metadata = metadata.split(',')
            #  num_buttons = int(split_metadata[1])
            #  if(values[keyname]==True):    
            #    self.debug.info_message("item selected: " + str(0) )
            #    data_item = 'X'
            #  else:
            #    data_item = ' '
            #  for btn_count in range (1, num_buttons):
            #    btn_keyname = keyname + '_' + str(btn_count)
            #    if(values[btn_keyname]==True):    
            #      data_item = data_item + 'X'
            #    else:
            #      data_item = data_item + ' '
              else:
                data_item = values[keyname].strip()

              if(already_appended == False):
                return_list.append(data_item)

              field_count = field_count + 1

              if(rl == repeat_lines-1):
                next_repeat_lines = 1
                self.debugForms.info_message("resetting repeat lines\n")

    except:
      self.debug.error_message("Exception in extractContentFromForm: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("CONTENT STRING IS: " + str(return_list) )
      		
    return return_list

  def replaceFields(self, message):

    message = self.parseIt3(message, '%DATE%',     datetime.now().strftime('%Y/%m/%d') )
    message = self.parseIt3(message, '%TIME%',     datetime.now().strftime('%H:%M') )
    message = self.parseIt3(message, '%DATETIME%', datetime.now().strftime('%Y/%m/%d %H:%M') )
    message = self.parseIt3(message, '%ZULUTIME%',     datetime.utcnow().strftime('%H:%MZ') )
    message = self.parseIt3(message, '%ZULUDATETIME%', datetime.utcnow().strftime('%Y/%m/%d %H:%MZ') )
    message = self.parseIt3(message, '%UTCTIME%',      datetime.utcnow().strftime('%H:%M UTC') )
    message = self.parseIt3(message, '%UTCDATETIME%',  datetime.utcnow().strftime('%Y/%m/%d %H:%M UTC') )

    if(self.group_arq.formdesigner_mode == False):
      message = self.parseIt(message, '%CALLSIGN%', self.window['input_myinfo_callsign'].get().strip() )
      message = self.parseIt(message, '%OPERATORNAME%', self.window['input_myinfo_operator_name'].get().strip())
      message = self.parseIt(message, '%OPERATORTITLE%', self.window['input_myinfo_operator_title'].get().strip())
      message = self.parseIt(message, '%INCIDENTNAME%', self.window['input_myinfo_incident_name'].get().strip())

      message = self.parseIt(message, '%GROUPNAME%', self.window['input_myinfo_group_name'].get().strip())
      message = self.parseIt(message, '%GPSLAT%', self.window['input_myinfo_gpslat'].get().strip())
      message = self.parseIt(message, '%GPSLONG%', self.window['input_myinfo_gpslong'].get().strip())
      message = self.parseIt(message, '%GRIDSQUARE%', self.window['input_myinfo_gridsquare'].get().strip())
      message = self.parseIt(message, '%QTHLOCATION%', self.window['input_myinfo_location'].get().strip())

    return message

  """
  generic parse function. usage parseIt(message, '%FIELDNAME', self.window['input_fieldx'].get().strip() )
  """
  def parseIt(self, message, replacestring, value):
    if replacestring in message :
      message = message.replace(replacestring, value )
        
    return message

  """
  generic parse function. usage parseIt3(message, '%NETNAME', self.window['input_netname'].get().strip() )
  """
  def parseIt3(self, message, replacestring, value):
    if replacestring in message :
      message = message.replace(replacestring, value )
        
    return message

  """
  create the main GUI window
  """
  def createFormDesignerPage(self):
  
    template_lookup = {
      'General Message'    : ['T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
      'ICS-213'            : ['T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5'],
    }

    form_content = ['gfhjgfsfsdfhj', 'asdf', 'gfhj', 'ssdfdffadf']

    """ static fields at the top of the form """
    combo_list_2    = 'General Message,ICS-213'.split(',')
    combo_list_3    = '-,T1,T2,T3,T4,T5,T6,T7,T8,T9,I1,I2,I3,I4,I5,I6,I7,I8,I9'.split(',')

    templates = [['ICS 213', 'General Form', '1.0','def.tpl'],['ICS 456', 'my form', '2.0','def.tpl']]
    self.group_arq.setTemplates(templates)
    self.group_arq.addTemplate('ICS 789', 'custom form', '1.6', 'mynewfile.tpl')

    elements = [['1', 'T1,I1'],['2', 'T2,I2,T5,I3']]

    individ_elements = ['T2','I2','T5','I3']


    mytemplate = 'my template'
    field_count = 0
    content_count = 0
    layout = [

         [sg.Table(values=self.group_arq.getCategories(), headings=['Category'],
                            max_col_width=35,
                            col_widths=[14],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=6, key='tbl_tmplt_categories'),
          sg.Table(values=self.group_arq.getTemplates(), headings=['Template Name', 'Description', 'Ver', 'File'],
                            max_col_width=75,
                            col_widths=[14, 20, 5, 15],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=6, key='tbl_tmplt_templates')],

         [
          sg.Button('Copy To Clipboard',   key='btn_tmplt_copytoclip', size=(16, 1) ), 
          sg.CBox('From', key='cb_tmplt_clipcopyfrom'),
          sg.InputText('', key='in_tmpl_clipcopyfrom', size=(8, 1), enable_events=True),
          sg.CBox('To', key='cb_tmplt_clipcopyto'),
          sg.InputText('', key='in_tmpl_clipcopyto', size=(8, 1), enable_events=True),
          sg.Button('Paste From Clipboard',   key='btn_tmplt_pastefromclip', size=(16, 1) )], 


         [sg.InputText('', key='in_tmpl_category_name', size=(21, 1), enable_events=True),
          sg.InputText(mytemplate, key='in_tmpl_name', size=(20, 1), enable_events=True),
          sg.InputText('', key='in_tmpl_desc', size=(28, 1), enable_events=True),
          sg.InputText('', key='in_tmpl_ver', size=(8, 1), enable_events=True),
          sg.InputText('', key='in_tmpl_file', size=(22, 1), enable_events=True)],
          
         [
          sg.Button('New Category',   key='btn_tmplt_new_category', size=(12, 1) ), 
          sg.Button('Delete Category',   key='btn_tmplt_delete_template_category', size=(12, 1) ), 
          sg.Button('New Template',   key='btn_tmplt_new_template', size=(12, 1) ), 
          sg.Button('Delete Template',   key='btn_tmplt_delete_template', size=(12, 1) ), 
          sg.Button('Update Template',   key='btn_tmplt_update_template', size=(12, 1) ), 
          sg.Button('Save',   key='btn_tmplt_save_template', size=(12, 1) ), 
          sg.Button('**UPDATE**',   key='btn_tmplt_update', size=(12, 1) ), 
          sg.Button('Preview',   key='btn_tmplt_preview_form', size=(10, 1) )], 
          
         [
          sg.Button('Insert Row',   key='btn_tmplt_add_row', size=(10, 1) ), 
          sg.Button('Delete Row',   key='btn_tmplt_delete_row', size=(10, 1) ), 
          sg.Button('Duplicate Row',   key='btn_tmplt_duplicate_row', size=(10, 1) ), 
          sg.Combo(['At','Before','After','End'], default_value='After', key='combo_tmplt_insertwhere', enable_events=True, size=(10, 1) ),
          sg.InputText('', key='in_tmpl_line_number', size=(8, 1)),

          sg.Button('Insert Element',   key='btn_tmplt_insertelement', size=(10, 1) ), 
          sg.Button('Delete Element',   key='btn_tmplt_deleteelement', size=(10, 1) ), 
          sg.Combo(['At','Before','After'], default_value='At', key='combo_tmplt_insertelementwhere', enable_events=True, size=(10, 1) ),
          sg.InputText('', key='in_tmpl_insertelementnumber', size=(8, 1))],

         [
          sg.Text('Fields 1-6:', size=(10, 1) ),
          sg.Combo(self.table_lookup, key='combo_element1', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element2', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element3', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element4', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element5', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element6', enable_events=True, size=(18, 1))],
         [
          sg.Text('Fields 7-12:', size=(10, 1) ),
          sg.Combo(self.table_lookup, key='combo_element7', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element8', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element9', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element10', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element11', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element12', enable_events=True, size=(18, 1))],
         [
          sg.Text('Fields 13-18:', size=(10, 1) ),
          sg.Combo(self.table_lookup, key='combo_element13', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element14', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element15', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element16', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element17', enable_events=True, size=(18, 1)),
          sg.Combo(self.table_lookup, key='combo_element18', enable_events=True, size=(18, 1))],

    ]
    
    mytemplate = template_lookup[self.group_arq.selected_template]

    text_equiv = ''
    table_data = []

    mytemplate = template_lookup['ICS-213']
    mytemplate = template_lookup['General Message']
    
    table_data = self.createSyntheticView(mytemplate, form_content)


    layout = layout + [[sg.Table(values=table_data, headings=['Elements Page 1'],
                            max_col_width=140,
                            col_widths=[140],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=40, key='table_templates_preview', font=("Courier New", 9))] ]
    return (layout)

  def createSyntheticView(self, mytemplate, form_content):
    row_num = 1
    field_count = 0
    content_count = 0
    table_data = []
    
    for x in range (len(mytemplate)):
      line = mytemplate[x]

      window_line = ''
      split_string = line.split(',')
      for y in range (len(split_string)):
        field = split_string[y]
        mylist = self.field_lookup[field]
        keyname = 'field_' + str(field_count)
        if(content_count < len(form_content)):
          self.debug.info_message("keyname is: " + str(keyname) )
          self.debug.info_message("content count is: " + str(content_count) )
          self.debug.info_message("field data is: " + str(form_content[content_count]) )
          window_line = window_line + ' ' + (mylist[4](self, keyname, form_content[content_count], mylist[0], mylist[1], mylist[2], 0, None))
        else:
          window_line = window_line + ' ' + (mylist[4](self, keyname, '', mylist[0], mylist[1], mylist[2], 0, None))

        self.debug.info_message("mylist 5 is: " + str(mylist[5]) )

        if(mylist[5] == True):
          content_count = content_count + 1  
        field_count = field_count + 1
        self.debugForms.info_message("line : " + str(mylist) )

      split_string = window_line.split('\n')
      for z in range(len(split_string)):
        table_data.append( [str("{:02d}".format(row_num)) + ':    ' + split_string[z]] )
        row_num = row_num + 1
    return table_data


  """
  create the main GUI window
  This code is used to create the 'compose' tab
  """
  def createWindowComposeTab(self):

    combo_types         = 'General Message,Report,ICS-213'.split(',')
    combo_fragtypes     = '20,30,40,60,80,100,120,140,160'.split(',')


    template_lookup = {
      'General Message'    : ['T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
      'ICS-213'            : ['T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5'],
    }

    form_content = ['gfhjgfhj', 'asdf', 'gfhjgfhj', 'sadf']

    """ static fields at the top of the form """
    combo_list_2    = 'General Message,ICS-213'.split(',')
    combo_list_3    = '20 CHARS, 40 CHARS, 80 CHARS'.split(',')

    templates = [['ICS 213', 'General Form', '1.0','ghi.tpl'],['ICS 456', 'my form', '2.0','ghi.tpl']]
    self.group_arq.setTemplates(templates)
    self.group_arq.addTemplate('ICS 789', 'custom form', '1.6','myotherone.tpl')

    mytemplate = 'my template'
    field_count = 0
    content_count = 0
    layout = [

         [
         sg.Table(values=self.group_arq.getCategories(), headings=['Category'],
                            max_col_width=35,
                            col_widths=[20],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='tbl_compose_categories'),
         
         sg.Table(values=self.group_arq.getTemplates(), headings=['Form', 'Description', 'Ver.', 'File'],
                            max_col_width=35,
                            col_widths=[16, 24, 12, 27],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='tbl_compose_select_form')],

         [
          sg.Text('To: ', size=(5, 1)),
          sg.InputText('', key='in_compose_selected_callsigns', size=(70, 1)),

          sg.Button('Compose Message', size=(15, 1), key='btn_cmpse_compose', disabled = True)],

         [sg.Table(values=self.createSyntheticView(template_lookup['General Message'], form_content), headings=['Elements Page 1'],
                            max_col_width=116,
                            col_widths=[116],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_COMPOSE, key='table_compose_preview', font=("Courier New", 10))],

    ]
    
    return (layout)


  def refreshSelectedTables(self):

    self.debug.info_message("refreshSelectedTables"  )

    self.window['tbl_compose_selectedstations'].update(values=self.group_arq.getSelectedStations() )
    self.window['tbl_compose_selectedstations'].update(row_colors=self.group_arq.getSelectedStationsColors())
    self.window['tbl_compose_selectedrelaystations'].update(values=self.group_arq.getSelectedRelayStations() )
    self.window['tbl_compose_selectedrelaystations'].update(row_colors=self.group_arq.getSelectedRelayStationsColors())
    return

    
  """
  create the main GUI window
  """
  def createMainTabbedWindow(self, text, js):

    combo_list_2    = 'General Message,ICS-213'.split(',')
    combo_list_3    = '20 CHARS,40 CHARS,80 CHARS'.split(',')
    combo_sendto    = 'Rig 1 - JS8,Rig 1 - Fldigi,Rig 2 - JS8,Fig 2 - Fldigi'.split(',')
    combo_wide      = 'HF - 500,VHF/UHF - 1000,VHF/UHF - 2000,VHF/UHF - 3500'.split(',')
    combo_premsg    = 'Message IDs,Message Callsigns,Grid Square,GPS LATLONG,QTH'.split(',')
    combo_mode1     = 'SLOW,NORMAL,FAST,TURBO'.split(',')
    combo_mode2 = 'MODE 5 - QPSK500,MODE 8 - BPSK500,MODE 13 - 8PSK125,MODE 14 - 8PSK250F,MODE 15 - 8PSK250FL,MODE 16 - PSK500R,\
MODE 18 - QPSK250,MODE 19 - BPSK250,MODE 22 - 8PSK125FL,MODE 23 - 8PSK125F,MODE 24 - PSK250R,MODE 25 - PSK63RC4,MODE 26 - DOMX22,\
MODE 28 - DOMX16,MODE 29 - OFDM500F'.split(',')

    self.group_arq.saamfram.fldigiclient.setModeSelectionList(combo_mode2)

    mytemplate = 'my template'
    combo_fragtypes     = '10,20,30,40,50,60,80,100,120,140,160,180,200'.split(',')
    combo_direct_relay  = 'Peer Only,Peer + Relay'.split(',')
    combo_channels      = 'Channel 1 - 500Hz,Channel 2 - 625Hz,Channel 3 - 750Hz,Channel 4 - 875Hz,\
Channel 5 - 1000Hz,Channel 6 - 1125Hz,Channel 7 - 1250Hz,Channel 8 - 1375Hz,\
Channel 9 - 1500Hz,Channel 10 - 1625Hz,Channel 11 - 1750Hz,Channel 12 - 1875Hz,\
Channel 13 - 2000Hz,Channel 14 - 2125Hz,Channel 15 - 2250Hz,Channel 16 - 2375Hz'.split(',')
    option_colors   = 'red,tomato,DeepPink3,orange,yellow,green,green1,forest green,purple,purple3,blue,blue2,blue4,steel blue,LightSkyBlue4,SkyBlue4,indigo,violet,\
dark violet,gray,magenta2,slate gray,slategray4,grey30,grey60,dark gray,white,black,turquoise1,cyan,khaki,dark khaki,olive drab,ivory2,plum1,orchid1,OliveDrab1,thistle2'.split(',')
    combo_numtimes_frag  = 'f1x2,f1x3,f1+f2x2,f1+f2x3,f1+f2+f3x2,f1+f2+f3x3'.split(',')
    combo_numtimes_msg  = 'x1,x2,x3'.split(',')
    combo_showactive    = 'Minute,Hour,Day,Week,Month,Year,Unlimited'.split(',')
    combo_fldigi_modes  = 'DOMX88,DOMX44,DOMX22,Cont-4/1K,Cont-8/1K,\
Cont-4/500,Cont-16/1K,OLIVIA-4/1K'.split(',')
    combo_reply_tmplts  = 'ICS_305_REPLY, ICS_305_PG2, GENERIC_REPLY'.split(',')

    combo_send_to_calls  = 'WH6GGO, WH6FQI'.split(',')

    combo_verify_by      = 'Next Only,All,None'.split(',')

    combo_server_or_client = 'Server Listen,Client Connect'.split(',')


    about_text = '\n\
                                                Ham Radio Relay Messenger de WH6GGO v1.0.1 Beta \n\
\n\
Ham Radio Relay Messenger and SAAMFRAM Protocol Copyright (c) 2022-2023 Lawrence Byng. MIT License details included\n\
below for reference (scroll down). For latest information and updates re: Ham Radio Relay Messenger and SAAMFRAM Protocol, \n\
please refer to https://github.com/gh42lb/\n\
Contact Email: LarryByng@gmail.com\n\
\n\
Ham Radio Relay Messenger Main Features:\n\
- Dynamic Routing: Builds routing information from active relay stations. Relay messages directed to relay station with fewest hops.\n\
- Self Organizing Radio Mesh: HRRM allows active stations to form a Dynamic Self Organizing Radio Mesh for message transfer.\n\
- Critical Messages: Enables transfer of fully verified, error-corrected chats/emails/forms/files/messages to ham radio stations in real time.\n\
- File Transfer: Capable of sending files.\n\
- Winlink Messages: Capable of sending Winlink message files directly from winlink outbox of sending station to winlink inbox of receiving station.\n\
- Group Communication: Capable of real time Peer to Peer, Peer to Group, Group to Peer** and Group to Group** mode communications.\n\
- Resilience: Optimized data transfer protocol for increased performance and resilience to adverse band conditions.\n\
- Integration: Integrates with Fldigi, Winlink and Pat Winlink applications.\n\
- Cross-Platform: Runs on Windows, Linux and any other platform supporting python + related libraries.\n\
- Flexibility: Multiple message delivery techniques including push, pull, store and forward, relay, active session, passive mode.\n\
- Mesh Node: Ad-hoc mesh node functionality provided out-of-the-box, including: relay, hub, gateway, RX or TX end node, \n\
- Notifications: Stub messages provide notification to the group of any pending messages waiting to be sent.\n\
- Data Compression: Uses a variety of data compression techniques inluding dictionary compression and run length encoding.\n\
- Customized Interface: Email style interface with inbox, outbox, relay box and sent box, utilizing notebook style and customized GUI controls.\n\
- 31 Modulation Modes: Supports a wide variety of underlying modulations including OFDM, PSK, QPSK, BPSK, DominoEX, 8PSK and Olivia.\n\
- Extendable: Form designer built-in with many pre-built ICS form templates and standard templates included.\n\
\n\
** Please note:- Group to Peer and Group to Group is currently available only with JS8Call\n\
\n\
enjoy :)\n\
73s LB WH6GGO\n\
\n\
\n\
MIT License\n\
\n\
\n\
Permission is hereby granted, free of charge, to any person obtaining a copy\n\
of this software and associated documentation files (the "Software"), to deal\n\
in the Software without restriction, including without limitation the rights\n\
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n\
copies of the Software, and to permit persons to whom the Software is\n\
furnished to do so, subject to the following conditions:\n\
\n\
The above copyright notice and this permission notice shall be included in all\n\
copies or substantial portions of the Software.\n\
\n\
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n\
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n\
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n\
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n\
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n\
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n\
SOFTWARE.\n'

    self.layout_substation = [
                          [sg.Text('Station Name: ', size=(11, 1) ) ,
                           sg.InputText('Yaesu HF Fldigi', key='in_substation_name_1', size=(15, 1)),
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='in_substation_ipaddress_1', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='in_substation_port_1', size=(15, 1)),
                           sg.Combo(combo_server_or_client, default_value=combo_server_or_client[1], size=(11, 1), key='option_substation_svrcli_1', enable_events=True) ,
                           sg.Button('Connect', size=(11, 1), key='btn_substation_connect_1'),
                           sg.Button('Dis-Connect', size=(11, 1), key='btn_substation_disconnect_1', disabled = True)],


                          [sg.CBox('Accept All Incoming Connection Requests', key='cb_inbox_autoresendrequest')],

                          [sg.Text('='*130, size=(130, 1) ) ],

                          [sg.Text('Digital Ham Radio Net: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.CBox('Auto Accept Connection', key='cb_inbox_autoresendrequest')],

                          [sg.Text('='*130, size=(130, 1) ) ],

                          [sg.Text('Pat Winlink Client: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.Text('Pat Winlink VARA: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.CBox('Auto Accept Connection', key='cb_inbox_autoresendrequest')],

                        ] 


    self.layout_chat = [
                          [sg.MLine('', size=(64, 3), font=("Courier New", 9), key='ml_chat_sendtext', text_color='black', background_color='white', expand_x = True, expand_y=False, disabled = False)], 
                          [sg.Button('Send', size=(7, 1), key='btn_prev_chat_post_and_send' ) ,
                           sg.Text('To: ', size=(3, 1), background_color=js.get("params").get('ChatTabClr'), text_color='black' ) ,
                           sg.CBox('Use connect to', default = js.get("params").get('UseConnectTo'), key='cb_chat_useconnecto', background_color=js.get("params").get('ChatTabClr'), text_color='black'),
                           sg.InputText('', key='in_chat_msgto', size=(50, 1)),
                           sg.Button('Launch Net', size=(11, 1), disabled = True )] ,

                          [sg.Table(values=[], headings=['From', 'Message', 'MSGID'],
                            max_col_width=116,
                            col_widths=[10,91,15],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=24, key='table_chat_received_messages', font=("Courier New", 10))],

                        ] 


    self.layout_inbox = [
         [sg.Table(values=self.group_arq.getMessageInbox(), headings=['From', 'To', 'Subject', 'Rcvd Time', 'Important', 'Type', 'Completion', 'MSGID'],
                            max_col_width=65,
                            col_widths=[10, 20, 25, 15, 8, 7, 5, 15],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='table_inbox_messages')],

          [
           sg.Button('View', size=(10, 1), key='btn_inbox_viewmsg'),
           sg.Button('Copy', size=(10, 1), key='btn_inbox_copyclipboard'),
           sg.Button('Paste', size=(10, 1), key='btn_inbox_pasteclipboard', disabled = True),
           sg.Button('Delete', size=(10, 1), key='btn_inbox_deleteselected'),
           sg.Button('Delete All', size=(10, 1), key='btn_inbox_deleteall'),
           sg.Button('Query Msg', size=(10, 1), key='btn_inbox_querydoyouhaveacopy', visible=False),
           sg.Button('Request Msg', size=(10, 1), key='btn_inbox_sendreqm'),
           sg.Button('Request CRC', size=(10, 1), key='btn_inbox_requestchecksums', disabled = True),
           sg.Button('Export', size=(10, 1), key='btncli_clear', visible = False),
           sg.InputText('myfile.dat', key='sidebar_offset', size=(15, 1), visible=False),
           sg.Combo(combo_reply_tmplts, key='option_inbox_reply_template', enable_events=True, visible = False),
           sg.Button('Reply', size=(7, 1), key='btn_inbox_replytomsg', visible = False)],

          [sg.Text('Error Frames:', size=(12, 1), visible = False),
           sg.InputText('', key='in_inbox_errorframes', size=(15, 1), visible = False),
           sg.CBox('Auto resend req', key='cb_inbox_autoresendrequest', visible = False),
           sg.Button('Send Ack Nack', size=(15, 1), key='btn_inbox_sendacknack', visible = False)],

         [sg.Table(values=[], headings=['Preview'],
                            max_col_width=116,
                            col_widths=[116],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_INBOX, key='table_inbox_preview', font=("Courier New", 10))],
       
    ]

    self.layout_relay = [
         [sg.Table(values=self.group_arq.getMessageRelaybox(), headings=['From', 'To', 'Subject', 'Rcvd Time', 'Important', 'Type', 'MSGID', 'confirmed', 'fragsize', 'Verified'],
                            max_col_width=65,
                            col_widths=[10, 12, 15, 15, 8, 7, 13, 7, 7, 7],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='table_relay_messages')],

          [
           sg.Button('Copy', size=(11, 1), key='btn_relay_copytoclipboard'),
           sg.Button('Paste', size=(11, 1), key='btn_relay_pastefromclipboard', disabled = True),
           sg.Button('Delete', size=(11, 1), key='btn_relaybox_deleteselected'),
           sg.Button('Delete All', size=(11, 1), key='btn_relaybox_deleteall'),
           sg.Button('Add to Outbox', size=(11, 1), key='btn_relay_copytooutbox'),
           sg.Button('Query Msg', size=(11, 1), key='btn_relay_querymessageorfragments', visible=False),
           sg.Button('Request Msg', size=(11, 1), key='btn_relay_sendreqm'),
           sg.Button('Request CRC', size=(11, 1), key='btn_relay_requestchecksums', disabled = True)],

          [sg.Table(values=[], headings=['Preview'],
                            max_col_width=116,
                            col_widths=[116],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_RELAYBOX, key='table_relaybox_preview', font=("Courier New", 10))],

    ]

    self.layout_compose = self.createWindowComposeTab()

   
    self.layout_outbox = [
         [sg.Table(values=self.group_arq.getMessageOutbox(), headings=['From', 'To', 'Subject', 'Created Time', 'Priority', 'Form', 'MSGID'],
                            max_col_width=65,
                            col_widths=[10, 20, 25, 20, 8, 7, 15],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='table_outbox_messages')],

         [
          sg.Button('View',   key='btn_outbox_viewform', size=(11, 1) ), 
          sg.Button('Copy',   key='btn_outbox_copytoclipboard', size=(11, 1) ), 
          sg.Button('Edit',   key='btn_outbox_editform', size=(11, 1) ), 
          sg.Button('Delete',   key='btn_outbox_deletemsg', size=(11, 1) ), 
          sg.Button('Delete All',   key='btn_outbox_deleteallmsg', size=(11, 1) ), 
          sg.Button('Ready?', size=(9, 1), key='btn_compose_areyoureadytoreceive'),
          sg.Button('Send',   key='btn_outbox_sendselected', size=(11, 1) )], 

         [
          sg.CBox('Pre Message:',  key='cb_outbox_includepremsg' ), 
          sg.OptionMenu(combo_premsg, default_value=combo_premsg[0], key='option_outbox_premessage', visible=False),
          sg.CBox('Repeat Message',  key='cb_outbox_repeatmsg' ), 
          sg.Combo(combo_numtimes_msg, default_value=combo_numtimes_msg[0], key='option_repeatmessagetimes'),
          sg.CBox('Repeat Fragments',  key='cb_outbox_repeatfrag', visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_JS8CALL) else False ), 
          sg.OptionMenu(combo_numtimes_frag, default_value=combo_numtimes_frag[0], key='option_repeatfragtimes', visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_JS8CALL) else False),
          sg.CBox('Include Template', key='cb_outbox_includetmpl', visible=False),
          sg.Text('Fragment Size:' ), 
          sg.OptionMenu(combo_fragtypes, default_value=combo_fragtypes[2], key='option_framesize')],


          [
           sg.InputText('', key='in_outbox_resendframes', size=(30, 1), visible = False),
           sg.InputText('', key='in_outbox_confirmcallsign', size=(30, 1), visible = False)],
          [sg.Table(values=[], headings=[''],
                            max_col_width=136,
                            col_widths=[136],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            vertical_scroll_only=False,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_OUTBOX, key='table_outbox_preview', font=("Courier New", 10))],
       ] 

    self.layout_sent = [
         [sg.Table(values=self.group_arq.getMessageSentbox(), headings=['From', 'To', 'Subject', 'Sent Time', 'Priority', 'Form', 'MSGID', 'verified'],
                            max_col_width=65,
                            col_widths=[10, 17, 20, 20, 8, 7, 13, 7],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='table_sent_messages')],

         [sg.Button('Delete',   key='btn_sentbox_deletemsg', size=(11, 1) ), 
          sg.Button('Delete All',   key='btn_sentbox_deleteallmsg', size=(11, 1) )], 


         [sg.Table(values=[], headings=['Preview'],
                            max_col_width=116,
                            col_widths=[116],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_SENT, key='table_sent_preview', font=("Courier New", 10))],
       ] 

    self.layout_template = self.createFormDesignerPage()
    
    self.layout_settings = [
                        [sg.Text('Loaded Templates:', size=(17, 1) ), 
                         sg.Text('', size=(20, 1) ), 
                         sg.Text('All Available Templates:', size=(22, 1) )], 

                        [sg.Table(values=self.group_arq.getTemplateFiles(), headings=['File'],
                            max_col_width=65,
                            col_widths=[30],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=3, key='tbl_layout_all_files', font=("Courier New", 10)),

                        sg.Table(values=self.group_arq.getLoadedTemplateFiles(), headings=['File', 'Description', 'Ver'],
                            max_col_width=65,
                            col_widths=[25, 20, 6],
                            auto_size_columns=False,
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=3, key='tbl_tmplt_files', font=("Courier New", 10))],

                        [
                         sg.Text('Template Folder:', size=(15, 1) ),
                         sg.InputText('./' if (platform.system() == 'Linux') else '.\\', key='in_settings_templatefolder', size=(20, 1) )],

                        [
                         sg.Button('List',   key='btn_settings_list', size=(6, 1) ), 
                         sg.Button('Add',   key='btn_settings_add', size=(6, 1) ), 
                         sg.Button('Load Selected',   key='btn_tmplt_load_sel', size=(10, 1) ), 
                         sg.Button('Load All',   key='btn_tmplt_load_all', size=(10, 1) ), 
                         sg.Button('Remove',   key='btn_settings_tmplt_remove', size=(6, 1) )], 
                         
                        [ sg.CBox('Auto load', default = js.get("params").get('AutoLoadTemplate'), key='cb_settings_autoload', enable_events=True),
                          sg.CBox('Save Partial Messages', key='cb_settings_savepartialmsgs', enable_events=True, visible = False)],

                        [sg.CBox('Trust original sender only', key='cb_settings_trustorigsndronly', default = js.get("params").get('TrustOrigSenderOnly'), visible = False),
                         sg.Text('Trusted Relays:', size=(15, 1), visible = False),
                         sg.InputText(key='in_settings_trustedrelays', size=(20, 1), default_text = js.get("params").get('TrustedRelays'), visible = False)],

                        [sg.Text('Rig 1:', size=(10, 1), visible = False ), 
                         sg.CBox('VOX', default = js.get("params").get('Rig1Vox'), key='cb_settings_vox1', visible = False)],
                         
                        [sg.Text('JS8Call IP address: ', size=(15, 1), visible = False ), 
                         sg.InputText(key='input_settings_js8callip1', size=(10, 1), default_text = js.get("params").get('Rig1Js8callIp'), visible = False),
                         sg.Text('JS8Call port #: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_js8callport1', size=(10, 1), default_text = js.get("params").get('Rig1Js8callPort'), visible = False)],

                        [sg.Text('Fldigi IP address: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_fldigiip1', size=(10, 1), default_text = js.get("params").get('Rig1FldigiIp'), visible = False),
                         sg.Text('Fldigi port #: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_fldigiport1', size=(10, 1), default_text = js.get("params").get('Rig1FldigiPort'), visible = False),
                         sg.Button('Squelch',   key='btn_settings_squelchautoadjust', size=(6, 1) , visible = False)], 

                        [sg.Text('_'*100, visible = False )], 

                        [sg.Text('Rig 2:', size=(10, 1), visible = False ), 
                         sg.CBox('VOX', key='cb_settings_vox2', default = js.get("params").get('Rig2Vox'), visible = False)],
                         
                        [sg.Text('JS8Call IP address: ', size=(15, 1), visible = False ), 
                         sg.InputText(key='input_settings_js8callip2', size=(10, 1), default_text = js.get("params").get('Rig2Js8callIp'), visible = False),
                         sg.Text('JS8Call port #: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_js8callport2', size=(10, 1), default_text = js.get("params").get('Rig2Js8callPort'), visible = False)],

                        [sg.Text('Fldigi IP address: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_fldigiip2', size=(10, 1), default_text = js.get("params").get('Rig2FldigiIp'), visible = False),
                         sg.Text('Fldigi port #: ', size=(15, 1) , visible = False), 
                         sg.InputText(key='input_settings_fldigiport2', size=(10, 1), default_text = js.get("params").get('Rig2FldigiPort'), visible = False),
                         sg.Text('Fldigi mode: ', size=(15, 1) , visible = False), 
                         sg.Combo(combo_fldigi_modes, key='combo_settings_fldigimoode2', enable_events=True, visible = False)],
                         
                      ] 


    self.layout_myinfo = [
                        [sg.Text('Callsign', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('CallSign'), key='input_myinfo_callsign', size=(10, 1))],
                        [sg.Text('Group Name', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('GroupName'), key='input_myinfo_group_name', size=(10, 1))],
                        [sg.Text('Operator Name', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('OperatorName'), key='input_myinfo_operator_name', size=(10, 1))],
                        [sg.Text('Operator Title', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('OperatorTitle'), key='input_myinfo_operator_title', size=(10, 1))],
                        [sg.Text('Incident Name', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('IncidentName'), key='input_myinfo_incident_name', size=(10, 1))],
                        [sg.Text('First Name', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('FirstName'), key='input_myinfo_firstname', size=(10, 1)),
                         sg.Text('Last Name', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('LastName'), key='input_myinfo_lastname', size=(10, 1))],
                        [sg.Text('Title', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('Title'), key='input_myinfo_title', size=(10, 1))],
                        [sg.Text('GPS Lat', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('GPSLat'), key='input_myinfo_gpslat', size=(10, 1)),
                         sg.Text('GPS Long', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('GPSLong'), key='input_myinfo_gpslong', size=(10, 1))],
                        [sg.Text('Grid Square', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('GridSquare'), key='input_myinfo_gridsquare', size=(10, 1))],
                        [sg.Text('Location', size=(20, 1) ), 
                         sg.InputText(default_text=js.get("params").get('Location'), key='input_myinfo_location', size=(10, 1))],
                      ] 

    self.layout_colors = [
                        [sg.Text('TX Buttons', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_tx_btns', default_value=js.get("params").get('TxButtonClr')),
                         sg.Text('Message Management Buttons', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_msgmgmt_btns', default_value=js.get("params").get('MessagesBtnClr')),
                         sg.Text('Clipboard Buttons', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_clipboard_btns', default_value=js.get("params").get('ClipboardBtnClr'))],
                        [sg.Text('Compose Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_compose_tab', default_value=js.get("params").get('ComposeTabClr')),
                         sg.Text('In Box Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_inbox_tab', default_value=js.get("params").get('InboxTabClr')),
                         sg.Text('Out Box Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_outbox_tab', default_value=js.get("params").get('OutboxTabClr'))],
                        [sg.Text('Relay Box Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_relay_tab', default_value=js.get("params").get('RelayboxTabClr')),
                         sg.Text('Sent Box Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_sentbox_tab', default_value=js.get("params").get('SentboxTabClr')),
                         sg.Text('Info Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_info_tab', default_value=js.get("params").get('InfoTabClr'))],
                        [sg.Text('Colors Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_colors_tab', default_value=js.get("params").get('ColorsTabClr')),
                         sg.Text('Settings Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_settings_tab', default_value=js.get("params").get('SettingsTabClr')),
                         sg.Text('Chat Tab', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_colors_chat_tab', default_value=js.get("params").get('ChatTabClr'))],

                        [sg.Text('Main Heading Background', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_main_heading_background_clr', default_value=js.get("params").get('FormHeadingClr')),
                         sg.Text('Main Heading Text', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_main_heading_text_clr', default_value=js.get("params").get('FormHeadingTextClr'))],
                        [sg.Text('Sub Heading Background', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_sub_heading_background_clr', default_value=js.get("params").get('FormSubHeadingClr')),
                         sg.Text('Sub Heading Text', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_sub_heading_text_clr', default_value=js.get("params").get('FormSubHeadingTextClr'))],
                        [sg.Text('Numbered Section Background', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_numbered_section_background_clr', default_value=js.get("params").get('NumberedSectionClr')),
                         sg.Text('Numbered Section Text', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_numbered_section_text_clr', default_value=js.get("params").get('NumberedSectionTextClr'))],
                        [sg.Text('Table Header Background', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_table_header_background_clr', default_value=js.get("params").get('TableHeaderClr')),
                         sg.Text('Table Header Text', size=(20, 1) ), 
                         sg.OptionMenu(option_colors, key='option_table_header_text_clr', default_value=js.get("params").get('TableHeaderTextClr'))],


                        [sg.Button('Update',   key='btn_colors_update', size=(6, 1) )], 
                      ] 


    self.layout_about = [
                          [sg.Button('Repository', key='btn_mainarea_visitgithub')],
                          [sg.MLine(about_text, size=(64, 20), font=("Courier New", 9),expand_x = True, expand_y=True, disabled = True)], 
                        ] 

    self.layout_winlink = [
                           [
                            sg.Text('Winlink Inbox:', size=(15,1), justification='left'),
                            sg.InputText(js.get("params").get('WinlinkInboxFolder'), size=(44, 1), key='in_winlink_inboxfolder', expand_x=True )], 
                            [sg.Table(values=self.group_arq.getWinlinkInboxFiles(), headings=['Filename', 'From', 'To', 'Subject', 'Timestamp', 'form', 'ID'],
                            max_col_width=116,
                            col_widths=[17, 15, 15, 20, 17, 15, 15],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            expand_x = True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=4, key='winlink_inbox_table', font=("Courier New", 10))],

                            [sg.Text('Winlink Outbox:', size=(15,1), justification='left'),
                            sg.InputText(js.get("params").get('WinlinkOutboxFolder'), size=(44, 1), key='in_winlink_outboxfolder', expand_x=True )], 
                            [sg.Table(values=self.group_arq.getWinlinkOutboxFiles(), headings=['Filename', 'From', 'To', 'Subject', 'Timestamp', 'form', 'ID'],
                            max_col_width=116,
                            col_widths=[17, 15, 15, 20, 17, 15, 15],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            expand_x = True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=4, key='winlink_outbox_table', font=("Courier New", 10))],

                            [sg.CBox('ICS Form Messages Only', key='cb_winlink_icsonly', disabled=True),
                             sg.Button('Edit', size=(11, 1), key='btn_winlink_edit_selected', disabled = True),
                             sg.Button('Send', size=(11, 1), key='btn_winlink_send_selected', disabled = False),
                             sg.Button('List', size=(11, 1), key='btn_winlink_list_emails')],

                            [sg.Table(values=[], headings=['Preview'],
                            max_col_width=116,
                            col_widths=[116],
                            auto_size_columns=False,
                            text_color='black',
                            background_color='white',
                            justification='left',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=cn.PREVIEW_NUM_ROWS_INBOX, key='table_winlink_inbox_preview', font=("Courier New", 10))],
                          ] 

    if(self.group_arq.formdesigner_mode ==True):
      self.tabgrp = [[sg.TabGroup([[
                             sg.Tab('Form Designer', self.layout_template, title_color='Black', key='tab_templates', background_color='Purple'),
                             sg.Tab('Settings', self.layout_settings, title_color='Black', background_color='Orange')]],
                       tab_location='centertop',
                       title_color='Blue', tab_background_color='Dark Gray', background_color='Dark Gray', selected_title_color='Black', selected_background_color='White', key='tabgrp_main' )], [sg.Button('Exit')]]  
    else:
      self.tabgrp = [
                       [

                        sg.Button('CQ CQ', size=(5, 1), key='btn_mainpanel_cqcqcq'),
                        sg.Button('Copy', size=(5, 1), key='btn_mainpanel_copycopy'),
                        sg.Button('RR 73', size=(5, 1), key='btn_mainpanel_rr73'),
                        sg.Button('73', size=(5, 1), key='btn_mainpanel_73'),

                        sg.CBox('Auto', key='cb_mainpanel_ft8stylefullauto', enable_events=True),
                        sg.Button('Relay', size=(4, 1), key='btn_mainpanel_relay', visible = False),

                        sg.Button('Propagation', size=(8, 1), key='btn_mainpanel_testprop'),
                        sg.CBox('Auto', size=(4, 1), key='cb_mainpanel_autobeacon'),
                        sg.Button('Standing By', size=(8, 1), key='btn_compose_standby'),
                        sg.Button('QRT', size=(4, 1), key='btn_compose_qrt'),

                        sg.Text('    ', size=(5, 1), visible = True), 

                        sg.Button('Reset', size=(4, 1), key='btn_mainarea_reset'),
                        sg.Button('Abort', size=(4, 1), key='btn_compose_abortsend'),

                        sg.Button('Save & Exit', size=(9, 1), key='Exit')],
                       [
                        sg.Table(values=self.group_arq.getSelectedStations(), headings=['Peer Callsign', '#', 'Grid', 'Sel.', 'Rig', 'Mod', 'SNR'],
                            max_col_width=35,
                            col_widths=[13, 3, 9, 3, 10, 8, 4, 11],
                            auto_size_columns=False,
                            justification='left',
                            text_color='black',
                            background_color='ivory2',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='tbl_compose_selectedstations'),
                        sg.Table(values=self.group_arq.getSelectedRelayStations(), headings=['Callsign', '#', 'Grid', 'Relay Callsign', 'Sel.', 'hops'],
                            max_col_width=35,
                            col_widths=[13, 3, 9, 13, 3, 4, 11],
                            auto_size_columns=False,
                            justification='left',
                            text_color='black',
                            background_color='plum1',
                            enable_events=True,
                            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                            num_rows=5, key='tbl_compose_selectedrelaystations')],

                       [
                        sg.CBox('Active TX Channel: ', key='cb_mainwindow_acttxchan', visible = False),
                        sg.InputText('', size=(30, 1), key='in_mainwindow_activetxchannel', visible = False ), 

                        sg.Text('Mode:', size=(5, 1), visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_FLDIGI) else False ), 
                        sg.Combo(combo_mode2, default_value=combo_mode2[5], key='option_outbox_fldigimode', enable_events = True, visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_FLDIGI) else False),

                        sg.Text('Channel:', size=(7, 1) ), 
                        sg.Combo(combo_channels, key='combo_settings_channels', size=(18, 1), default_value=combo_channels[8], enable_events=True),

                        sg.Text('Send To:', size=(7, 1), visible = False ), 
                        sg.Combo(combo_sendto, default_value=combo_sendto[0], key='option_outbox_txrig', visible = False),
                        sg.Text('Span:', size=(5, 1) ), 
                        sg.Combo(combo_wide, default_value=combo_wide[0], key='combo_main_signalwidth', size=(13, 1), enable_events=True),
                        sg.Button('Beacon', size=(5, 1), key='btn_mainpanel_beacon', visible = False),

                        sg.Text('Timescale:', size=(10, 1), visible = True), 
                        sg.Combo(combo_showactive, default_value=combo_showactive[6], key='option_showactive'),
                        sg.Button('Update', size=(5, 1), key='btn_mainpanel_updaterecent'),
                        sg.Button('Clear', size=(5, 1), key='btn_mainpanel_clearstations')],
 
                       [
                        sg.CBox('Active RX Channel: ', key='cb_mainwindow_actrxchan', visible = False),
                        sg.InputText('', size=(30, 1), key='in_mainwindow_activerxchannel', visible = False ), 
                       
                        sg.Text('Peer / Relay:', visible = False  ), 
                        sg.Combo(combo_direct_relay, key='combo_settings_direct_relay', default_value=combo_direct_relay[1], enable_events=True, visible = False ),
                       
                        sg.Text('Connect To:', key='text_mainarea_connect_to'),
                        sg.InputText('', key='in_inbox_listentostation', size=(20, 1), disabled=False),
                        sg.CBox('Auto Receive', key='cb_mainwindow_autoacceptps', default = js.get("params").get('AutoReceive'), visible = False),
                        sg.Button('Clipboard Import',   key='btn_outbox_importfromclipboard', size=(12, 1), visible = False ), 
                        #sg.Button('Save As', size=(7, 1), key='btn_mainpanel_saveasfile', disabled=False),
                        sg.InputText('myfile', key='in_mainpanel_saveasfilename', size=(10, 1), disabled=True, enable_events=True),
                        sg.FileSaveAs(key='btn_mainpanel_saveasfile', initial_folder='/tmp', disabled=False),
                        sg.Button('Send File:', size=(7, 1), key='btn_mainpanel_sendgfile', disabled=False),
                        sg.InputText('', key='in_mainpanel_sendfilename', size=(20, 1), disabled=False),
                        sg.FileBrowse(),
                        sg.Text('--In Session--', size=(10, 1), key='text_mainarea_insession', font=("Helvetica", 20), expand_x=True, justification = 'right', text_color='gray' )], 

                       [ sg.Text('Fldigi mode: ', size=(15, 1) , visible = False      ), 
                         sg.Combo(combo_fldigi_modes, key='combo_settings_fldigimoode1', enable_events=True, visible = False),
                         sg.Text('JS8Call Mode:', size=(5, 1), visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_JS8CALL) else False ), 
                         sg.Combo(combo_mode1, default_value=combo_mode1[0], key='option_outbox_js8callmode', disabled = True, enable_events = True, visible = True if (self.group_arq.send_mode_rig1 == cn.SEND_JS8CALL) else False)],

                       [sg.MLine('', size=(64, 10), key='ml_mainwindow_textarea_1', background_color='Green1', font=("Courier New", 9), autoscroll=True, visible=False), 
                        sg.MLine('', size=(64, 10), key='ml_mainwindow_textarea_2', background_color='Green1', font=("Courier New", 9), autoscroll=True, visible=False)], 


                          [sg.TabGroup([[
                             sg.Tab('Chat', self.layout_chat, title_color='Blue',border_width =10, background_color=js.get("params").get('ChatTabClr'), key='tab_chat' ),
                             sg.Tab('In Box', self.layout_inbox, title_color='Blue',border_width =10, background_color=js.get("params").get('InboxTabClr'), key='tab_inbox' ),
                             sg.Tab('Out Box', self.layout_outbox, title_color='Blue', background_color=js.get("params").get('OutboxTabClr'), key='tab_outbox'),
                             sg.Tab('Sent Box', self.layout_sent, title_color='Blue', background_color=js.get("params").get('SentboxTabClr')),
                             sg.Tab('Relay Box', self.layout_relay, title_color='Blue', background_color=js.get("params").get('RelayboxTabClr'), key='tab_relaybox'),
                             sg.Tab('Compose Msg', self.layout_compose, title_color='Green', background_color=js.get("params").get('ComposeTabClr'), key='tab_compose'),
                             #sg.Tab('Sub-Station', self.layout_substation, title_color='Blue',border_width =10, background_color=js.get("params").get('ChatTabClr') ),
                             sg.Tab('Winlink', self.layout_winlink, title_color='Blue',border_width =10, background_color=js.get("params").get('InboxTabClr') ),
                             sg.Tab('My Info', self.layout_myinfo, title_color='Black', background_color=js.get("params").get('InfoTabClr')),
                             sg.Tab('Colors', self.layout_colors, title_color='Black', background_color=js.get("params").get('ColorsTabClr')),
                             sg.Tab('Settings', self.layout_settings, title_color='Black', background_color=js.get("params").get('SettingsTabClr')),
                             sg.Tab('About', self.layout_about, title_color='Black', background_color=js.get("params").get('SettingsTabClr')) ]],
                       tab_location='centertop',
                       title_color='Blue', tab_background_color='Dark Gray', background_color='Dark Gray', size=(940, 450), selected_title_color='Black', selected_background_color='White', key='tabgrp_main' )] ]  

    self.window = sg.Window("Ham Radio Relay Messenger de WH6GGO. v1.0.1 Beta", self.tabgrp, default_element_size=(40, 1), grab_anywhere=False)                       

    return (self.window)

  def runPopup(self, form, dispatcher, window, non_render_view_only, render_disabled_controls):

    initialized_headers = False
    self.form_events.editing_table = False
    self.render_disabled_controls = render_disabled_controls

    try:
      while True:
        event, values = window.read(timeout=100)

        if(initialized_headers == False):
          if(non_render_view_only == False):
            self.form_events.fixup_table_headers(window, 'content_0', values)
          initialized_headers = True

        try:
          self.form_events.dispatch[event](self.form_events, values)
        except:
          if(event == '__TIMEOUT__'):
            self.debug.info_message("Timeout in runPopup")
            if(self.form_events.hasWindowMovedDuringEdit(window) == True):
              self.form_events.cancelEdit()

          elif(event == 'Close' or event == 'Cancel'):
            self.debug.info_message("Close popup window in runPopup")
          #elif(event == 'in_mainpanel_saveasfilename'):
          #  self.debug.info_message("Save As in runPopup")
          else:

            if self.render_disabled_controls==False and isinstance(event, tuple):

              self.debug.info_message("Edit Cell event: " + str(event))
              self.debug.info_message("Edit Cell event[0]: " + str(event[0]))
              cell = row, col = event[2]
              self.debug.info_message("row: " + str(row))
              self.debug.info_message("col: " + str(col))
              if(row != None):
                self.form_events.editCell(window, event[0], row+1, col, values, False)

            self.debug.error_message("Exception in runPopup: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

        if event in ('Close', 'Cancel', 'btn_prev_post_to_outbox', None):
          break

      self.form_events.editing_table = False
      window.close()
    except:
      self.debug.error_message("Exception in runPopup: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.form_events.editing_table = False
      window.close()

  def runReceive(self, form, dispatcher):

    self.debug.info_message("in run receive. \n")

    try:
      while True:
        event, values = self.window.read(timeout=100)

        #self.debug.info_message("event: " + str(event) )
       
        try:
          self.form_events.dispatch[event](self.form_events, values)
        except:
          self.form_events.event_catchall(values)

        if event in ('Exit', None):
          break

      self.form_events.event_exit_receive(values)
      self.window.close()
    except:
      self.debug.error_message("Exception in runReceive: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.window.close()

  
    
