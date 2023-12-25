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
import glob
import webbrowser
import shutil

import base64
import bz2 as bz2

import hrrm
import js8_form_gui
import js8_form_dictionary
import winlink_import

from datetime import datetime, timedelta
from datetime import time

from PIL import Image

from uuid import uuid4

import clipboard as clip

from JSONPipe import JSONPipe


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


class ReceiveControlsProc(object):
  
  
  def __init__(self, group_arq, form_gui, form_dictionary, debug):  
    self.form_gui = form_gui
    self.form_dictionary = form_dictionary
    self.group_arq = group_arq
    self.current_edit_string = []
    self.current_edit_category = ''
    self.background_snr = ''
    self.saamfram = None
    self.debug = debug

    self.refresh_timer = 0

    self.countdown_timer = 0
    self.countdown_timer_delay = 5 
    self.tablerow_templaterow_xref = {}
    self.window_initialized = False

    self.winlink_import = winlink_import.WinlinkImport(debug)

    self.editing_table = False
    self.editing_scrolly_pos = 0
    self.editing_table_key = ''
    self.editing_table_entry = None
    self.editing_table_button = None
    self.editing_table_row = 0
    self.editing_table_col = 0

    #FIXME REMOVE
    self.substationClient1 = None

    self.flash_timer_group1 = 0
    self.flash_toggle_group1 = 0
    self.flash_buttons_group1 = {
                                  'btn_mainpanel_cqcqcq'     : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'black,green1'],
                                  'btn_mainpanel_copycopy'   : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_mainpanel_rr73'       : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_mainpanel_73'         : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_outbox_sendselected'  : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_relay_copytooutbox'   : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_relay_sendreqm'       : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_compose_areyoureadytoreceive'  : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_inbox_sendreqm'       : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'btn_inbox_viewmsg'        : ['False', 'black,green1', 'white,slate gray', cn.STYLE_BUTTON, 'white,slate gray'],
                                  'in_inbox_listentostation' : ['False', 'red,green1', 'green1,red', cn.STYLE_INPUT, 'white,gray'],
                                  'text_mainarea_insession'  : ['False', 'red,green1', 'green1,red', cn.STYLE_TEXT, 'gray,white'],

                                  'in_mainpanel_saveasfilename'       : ['False', 'red,green1', 'green1,red', cn.STYLE_TEXT, 'gray,white'],
                                  'in_mainpanel_saveasimagefilename'  : ['False', 'red,green1', 'green1,red', cn.STYLE_TEXT, 'gray,white'],



                                }
    



  def setSaamfram(self, saamfram):
    self.saamfram = saamfram

  def getSaamfram(self):
    return self.saamfram

  def setCountdownTimer(self, value):
    self.countdown_timer = value
    return

  def getCountdownTimer(self):
    return self.countdown_timer

  def getCountdownTimerDelay(self):
    return self.countdown_timer_delay	  

  def getCountdownTimerDelay(self, delay):
    self.countdown_timer_delay = delay
    return

  def setCommStatus(self, comm_status):
    self.comm_status = comm_status
    return

  def getCommStatus(self):
    return self.comm_status

  def getRetransmitCount(self):
    return self.retransmit_count

  def setRetransmitCount(self, retransmit_count):
    self.retransmit_count = retransmit_count
    return
    
  def getMaxRetransmit(self):
    return self.max_retransmit


    
  def setFormGui(self, form_gui):
    self.form_gui = form_gui
    return


  def setFormDictionary(self, form_dictionary):
    self.form_dictionary = form_dictionary
    return

  def setGroupArq(self, group_arq):
    self.group_arq = group_arq
    return

   
  def event_catchall(self, values):

    if(self.group_arq.formdesigner_mode == True):
      return

    if(self.window_initialized == False and self.form_gui.window != None):
      self.event_btnmainareareset(values)
      self.window_initialized = True		

      winlink_folder_in  = self.form_gui.window['in_winlink_inboxfolder'].get().strip()
      winlink_folder_out = self.form_gui.window['in_winlink_outboxfolder'].get().strip()
      winlink_folder_rms = self.form_gui.window['in_winlink_rmsmsgfolder'].get().strip()
      callsign = self.form_gui.window['input_myinfo_callsign'].get().strip()


      if (platform.system() == 'Windows'):
        username = os.getenv('USERNAME')
        if(winlink_folder_rms =='' and os.path.exists('C:\\RMS Express\\' + callsign + '\\Messages\\')):
          self.form_gui.window['in_winlink_rmsmsgfolder'].update('C:\\RMS Express\\' + callsign + '\\Messages\\')
        if(os.path.exists('C:\\Users\\' + os.getenv('USERNAME') + '\\AppData\\Local\\pat\\mailbox\\' + callsign )):
          if(winlink_folder_in ==''):
            self.form_gui.window['in_winlink_inboxfolder'].update('C:\\Users\\' + os.getenv('USERNAME') + '\\AppData\\Local\\pat\\mailbox\\' + callsign + '\\in\\')
          if(winlink_folder_out ==''):
            self.form_gui.window['in_winlink_outboxfolder'].update('C:\\Users\\' + os.getenv('USERNAME') + '\\AppData\\Local\\pat\\mailbox\\' + callsign + '\\out\\')
      else:
        username = 'pi'
        username = os.getenv('USER')
        if(winlink_folder_rms =='' and os.path.exists('/home/' + username + '/.wine/drive_c/RMS Express/' + callsign + '/Messages/')):
          self.form_gui.window['in_winlink_rmsmsgfolder'].update('/home/' + username + '/.wine/drive_c/RMS Express/' + callsign + '/Messages/')
        if(os.path.exists('/home/' + username + '/.wl2k/mailbox/' + callsign + '/')):
          if(winlink_folder_in ==''):
            self.form_gui.window['in_winlink_inboxfolder'].update('/home/' + username + '/.wl2k/mailbox/' + callsign + '/' + 'in/')
          if(winlink_folder_out ==''):
            self.form_gui.window['in_winlink_outboxfolder'].update('/home/' + username + '/.wl2k/mailbox/' + callsign + '/' + 'out/')


      if(self.group_arq.formdesigner_mode == False):

        """ set initial values only"""
        """ select the initial category and form on the compose tab"""
        self.form_gui.window['tbl_compose_categories'].update(select_rows=[0])

        """ update the colors in the inbox"""
        self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
        self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

        self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
        self.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

        if(self.getSaamfram().tx_mode == 'JS8CALL'):
          self.form_gui.window['option_outbox_txrig'].update(values=['Rig 1 - JS8'])
          self.form_gui.window['option_outbox_txrig'].update('Rig 1 - JS8')
        elif(self.getSaamfram().tx_mode == 'FLDIGI'):
          self.form_gui.window['option_outbox_txrig'].update(values=['Rig 1 - FLDIGI'])
          self.form_gui.window['option_outbox_txrig'].update('Rig 1 - FLDIGI')


    if(self.group_arq.formdesigner_mode == False and self.window_initialized == True):
      saam = self.getSaamfram()
      if(saam != None and saam.tx_mode == 'JS8CALL'):
        saam.processSendJS8()

        """ need to poll JS8Call to get the speed"""
        if(self.refresh_timer <30):
          self.refresh_timer = self.refresh_timer + 1
        elif(self.refresh_timer >=30):
          self.group_arq.getSpeed()
          self.refresh_timer = 0

    if(self.group_arq.formdesigner_mode == False):
      if(self.flash_timer_group1 <6):
        self.flash_timer_group1 = self.flash_timer_group1 + 1
      elif(self.flash_timer_group1 >=6):
        self.flash_timer_group1 = 0

        if(self.getSaamfram().inSession() == True):
          self.changeFlashButtonState('text_mainarea_insession', True)
        else:
          self.changeFlashButtonState('text_mainarea_insession', False)

        if(self.flash_toggle_group1 == 0):
          self.flash_toggle_group1 = 1
        else:
          self.flash_toggle_group1 = 0

        for key in self.flash_buttons_group1:
          button_colors = self.flash_buttons_group1.get(key)
          flash = button_colors[0]
          if(flash == 'True'):
            if(self.flash_toggle_group1 == 0):
              button_on = button_colors[1].split(',')
              button_clr1_on = button_on[0]
              button_clr2_on = button_on[1]

              if(button_colors[3] == cn.STYLE_BUTTON):
                self.form_gui.window[key].Update(button_color=(button_clr1_on, button_clr2_on))
              elif(button_colors[3] == cn.STYLE_INPUT):
                self.form_gui.window[key].Update(background_color=button_clr1_on)
              elif(button_colors[3] == cn.STYLE_TEXT):
                self.form_gui.window[key].Update(text_color=button_clr1_on)
            else:
              button_off = button_colors[2].split(',')
              button_clr1_off = button_off[0]
              button_clr2_off = button_off[1]
              if(button_colors[3] == cn.STYLE_BUTTON):
                self.form_gui.window[key].Update(button_color=(button_clr1_off, button_clr2_off))
              elif(button_colors[3] == cn.STYLE_INPUT):
                self.form_gui.window[key].Update(background_color=button_clr1_off)
              elif(button_colors[3] == cn.STYLE_TEXT):
                self.form_gui.window[key].Update(text_color=button_clr1_off)
	  
    return()

  def changeFlashButtonState(self, button_name, state):
    try:
      button_colors = self.flash_buttons_group1.get(button_name)
      old_state  = button_colors[0]
      button_on  = button_colors[1]
      button_off = button_colors[2]
      style      = button_colors[3]
      atrestclr  = button_colors[4]
      if(state == True and old_state == 'False'):
        self.flash_buttons_group1[button_name] = ['True', button_on, button_off, style, atrestclr]
      elif(state == False and old_state == 'True'):
        self.flash_buttons_group1[button_name] = ['False', button_on, button_off, style, atrestclr]
        atrestclr = button_colors[4].split(',')
        clr1 = atrestclr[0]
        clr2 = atrestclr[1]
        if(button_colors[3] == cn.STYLE_BUTTON):
          self.form_gui.window[button_name].Update(button_color=(clr1, clr2))
        elif(button_colors[3] == cn.STYLE_INPUT):
          self.form_gui.window[button_name].Update(background_color=clr1)
        elif(button_colors[3] == cn.STYLE_TEXT):
          self.form_gui.window[button_name].Update(text_color=clr1)

    except:
      self.debug.error_message("Exception in changeFlashButtonState: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))




  def updateSimulatedPreview(self, mytemplate):

    self.debug.info_message("update simulated preview\n")

    text_equiv = ''
    table_data = []
   
    form_content = ['gfhjgfhj', 'asdf', 'gfhjgfhj', 'sadf']
    content_count = 0
    field_count = 0
    
    row_num = 1
    
    for x in range (2, len(mytemplate)):
      line = mytemplate[x]

      self.debug.info_message("processing line: " + str(x) )

      self.debug.info_message("line is: " + str(line) )

      window_line = ''
      split_string = line.split(',')
      for y in range (len(split_string)):
        field = split_string[y]
        mylist = self.form_gui.field_lookup[field]

        self.debug.info_message("mylist is: " + str(mylist) )

        keyname = 'field_' + str(field_count)
        window_line = window_line + ' ' + (mylist[4](self, keyname, '', mylist[0], mylist[1], mylist[2], 0, None))

        self.debug.info_message("window line: " + str(window_line) )

        if(mylist[4] == True):
          content_count = content_count + 1  
        field_count = field_count + 1
        self.debug.info_message("line : " + str(mylist) )

      split_string = window_line.split('\n')
      for z in range(len(split_string)):
        self.tablerow_templaterow_xref[row_num] = x-1
        table_data.append( [str("{:02d}".format(row_num)) + ':    ' + split_string[z]] )
        row_num = row_num + 1

    self.debug.info_message("tablerow_templaterow_xref: " + str(self.tablerow_templaterow_xref) )
    self.debug.info_message("TABLE DATA IS: " + str(table_data) )

    return (table_data)


  def event_btntmpltpreviewform(self, values):
    self.debug.info_message("BTN NEW TEMPLATE\n")

    form_content = ['', '', '', '']

    #FIXME SHOULD NOT BE HARDCODED
    ID='123'
    msgto = 'WH6ABC;WH6DEF;WH6XYZ'

    category    = values['in_tmpl_category_name']
    formname    = values['in_tmpl_name']
    description = values['in_tmpl_desc']
    version     = values['in_tmpl_ver']
    filename    = values['in_tmpl_file']
    
    subject = ''

    self.form_gui.render_disabled_controls = False

    window = self.form_gui.createDynamicPopupWindow(formname, form_content, category, msgto, filename, ID, subject, True)
    dispatcher = PopupControlsProc(self, window)
    self.form_gui.runPopup(self, dispatcher, window, False, False)

    return()

  def event_tmplt_template(self, values):
    self.debug.info_message("EVENT TMPLT TEMPLATE\n")
    
    line_index = int(values['tbl_tmplt_templates'][0])
    field_1 = (self.group_arq.getTemplates()[line_index])[0]
    field_2 = (self.group_arq.getTemplates()[line_index])[1]
    field_3 = (self.group_arq.getTemplates()[line_index])[2]
    field_4 = (self.group_arq.getTemplates()[line_index])[3]

    self.form_gui.window['in_tmpl_name'].update(field_1)
    self.form_gui.window['in_tmpl_desc'].update(field_2)
    self.form_gui.window['in_tmpl_ver'].update(field_3)
    self.form_gui.window['in_tmpl_file'].update(field_4)

    edit_list = self.form_dictionary.getDataFromDictionary(field_1, field_2, field_3, field_4)

    self.debug.info_message("edit string: " + str(edit_list) )

    self.debug.info_message("UPDATEING SIMULATED PREVIEW WITH: " + str(edit_list) )
    table_data = self.updateSimulatedPreview(edit_list)

    self.debug.info_message("table data : " + str(table_data) )

    self.form_gui.window['table_templates_preview'].update(values=table_data)

    self.current_edit_string = edit_list

    self.debug.info_message("edit string: " + str(self.current_edit_string) )
    return()

  def event_tmplt_newtemplate(self, values):
    self.debug.info_message("EVENT TMPLT NEW TEMPLATE\n")

    category    = values['in_tmpl_category_name']
    formname    = values['in_tmpl_name']
    description = values['in_tmpl_desc']
    version     = values['in_tmpl_ver']
    filename    = values['in_tmpl_file']

    self.debug.info_message("EVENT TMPLT NEW TEMPLATE 2\n")

    self.group_arq.addTemplate(formname, description, version, filename)

    self.debug.info_message("EVENT TMPLT NEW TEMPLATE 3\n")

    data = [version,description,'T1,I1']

    self.debug.info_message("EVENT TMPLT NEW TEMPLATE 4\n")

    self.form_dictionary.createNewTemplateInDictionary(filename, category, formname, version, description, data)

    table_data = self.updateSimulatedPreview(data)
    self.debug.info_message("table data : " + str(table_data) )
    self.form_gui.window['table_templates_preview'].update(values=table_data)
    self.current_edit_string = data

    self.debug.info_message("EVENT TMPLT NEW TEMPLATE 5\n")

    self.form_gui.window['tbl_tmplt_templates'].update(self.group_arq.getTemplates())
    return

  def event_tmplt_updatetemplate(self, values):
    self.debug.info_message("EVENT TMPLT UPDATE TEMPLATE\n")

    line_index = int(values['tbl_tmplt_templates'][0])

    field_1 = values['in_tmpl_name']
    field_2 = values['in_tmpl_desc']
    field_3 = values['in_tmpl_ver']
    field_4 = values['in_tmpl_file']

    templates = self.group_arq.getTemplates()
    templates[line_index][0] = field_1
    templates[line_index][1] = field_2
    templates[line_index][2] = field_3
    templates[line_index][3] = field_4

    self.form_gui.window['tbl_tmplt_templates'].update(self.group_arq.getTemplates())

    return

  def event_tmplt_deletetemplate(self, values):
    self.debug.info_message("EVENT TMPLT DELETE TEMPLATE\n")

    line_index = int(values['tbl_tmplt_templates'][0])

    self.debug.info_message("line index = " + str(line_index) )
    
    templates = self.group_arq.getTemplates()
    filename = templates[line_index][3]
    formname = templates[line_index][0]
    category = values['in_tmpl_category_name']
    templates.remove(templates[line_index])
    
    self.debug.info_message("FILENAME:  " + str(filename) )
    self.debug.info_message("FORMNAME:  " + str(formname) )
    self.debug.info_message("CATEGORY:  " + str(category) )
    self.form_dictionary.removeTemplateFromTemplateDictionary(filename, category, formname)
   
    self.form_gui.window['tbl_tmplt_templates'].update(self.group_arq.getTemplates())
   
    return
    
  def event_tmplt_savetemplate(self, values):
    self.debug.info_message("EVENT TMPLT SAVE TEMPLATE\n")

    field_1 = values['in_tmpl_name']
    field_2 = values['in_tmpl_desc']
    field_3 = values['in_tmpl_ver']
    field_4 = values['in_tmpl_file']
    
    self.debug.info_message("WRITING FILE: "+ field_4 )
    
    self.form_dictionary.writeTemplateDictToFile(field_4)

    return

  def event_tmplt_loadsel(self, values):
    self.debug.info_message("EVENT TMPLT LOAD SELECTED FILE\n")

    line_index = int(values['tbl_layout_all_files'][0])
    templatefiles = self.group_arq.getTemplateFiles()
    filename = templatefiles[line_index][0]

    self.form_dictionary.readTemplateDictFromFile(filename)

    self.form_gui.window['tbl_tmplt_categories'].update(self.group_arq.getCategories())
    self.form_gui.window['tbl_tmplt_files'].update(self.group_arq.getLoadedTemplateFiles())

    if(self.group_arq.formdesigner_mode == False):
      self.form_gui.window['tbl_compose_categories'].update(self.group_arq.getCategories())

    return
    

  def event_settings_add(self, values):
    self.debug.info_message("EVENT TMPLT ADD FILE\n")

    line_index = int(values['tbl_layout_all_files'][0])

    templatefiles = self.group_arq.getTemplateFiles()
    filename = templatefiles[line_index][0]

    self.debug.info_message("filename to add is: " + str(filename) )

    self.form_dictionary.readTemplateDictFromFile(filename)
    self.form_gui.window['tbl_tmplt_categories'].update(self.group_arq.getCategories())
    self.form_gui.window['tbl_compose_categories'].update(self.group_arq.getCategories())

    description = self.form_dictionary.getFileDescriptionFromTemplateDictionary(filename)
    version     = self.form_dictionary.getFileVersionFromTemplateDictionary(filename)

    self.group_arq.addLoadedTemplateFile(filename, description, version)
    self.form_gui.window['tbl_tmplt_files'].update(self.group_arq.getLoadedTemplateFiles())
    return

  def event_settings_tmplt_remove(self, values):
    self.debug.info_message("EVENT TMPLT REMOVE SELECTED FILE\n")

    line_index = int(values['tbl_tmplt_files'][0])

    self.debug.info_message("line index = " + str(line_index) )
    
    templatefiles = self.group_arq.getLoadedTemplateFiles()
    filename = templatefiles[line_index][0]
    templatefiles.remove(templatefiles[line_index])

    self.debug.info_message("filename: " + str(filename) )
    self.form_dictionary.removeTemplatesFileFromTemplateDictionary(filename)
    
    self.form_gui.window['tbl_tmplt_files'].update(self.group_arq.getLoadedTemplateFiles())

    return


  def event_tmplt_categories(self, values):
    self.debug.info_message("event_tmplt_categories")
    line_index = int(values['tbl_tmplt_categories'][0])
    category = (self.group_arq.getCategories()[line_index])[0]

    self.debug.info_message("category: " + category )

    self.form_dictionary.getTemplatesFromCategory(category)

    if(self.group_arq.formdesigner_mode == False):
      self.form_gui.window['tbl_compose_select_form'].update(self.group_arq.getTemplates())

    self.current_edit_category = category

    self.form_gui.window['tbl_tmplt_templates'].update(self.group_arq.getTemplates())
    self.form_gui.window['in_tmpl_category_name'].update(category)
    
    return

  def event_tablepreview(self, values):
    self.debug.info_message("EVENT TABLE PREVIEW\n")

    line_index_form = int(values['table_templates_preview'][0])+1
    self.debug.info_message("line index form = " + str(line_index_form) )
    line_index = self.tablerow_templaterow_xref[line_index_form]-1
    self.debug.info_message("line index = " + str(line_index) )

    self.form_gui.window['in_tmpl_line_number'].update(str(line_index+1))

    edit_list = self.current_edit_string

    line_data = str(edit_list[2+line_index]) 		
    self.debug.info_message("data item:" + line_data )

    for x in range (18):
      field_name = 'combo_element' + str(x+1)
      self.form_gui.window[field_name].update('-')


    split_string = line_data.split(',')
    for x in range (len(split_string)):
      self.debug.info_message(" line item:" + split_string[x] )
      field_name = 'combo_element' + str(x+1)
      self.form_gui.window[field_name].update(self.form_gui.field_names[ split_string[x] ])

    clipboard_string = 'JSDIGI_FORMS_CLIPBOARD_DATA={'
    checked = values['cb_tmplt_clipcopyto']
    if(checked):
      self.form_gui.window['in_tmpl_clipcopyto'].update(str(line_index+1))
      self.form_gui.window['cb_tmplt_clipcopyto'].update(False)

      index_from = values['in_tmpl_clipcopyfrom']
      index_to = str(line_index+1)
      if(index_to != '' and index_from != ''):
        for line_index in range(int(index_from)-1, int(index_to)) :
          string_data = str(edit_list[2+line_index]) 		
          self.debug.info_message(" line to copy: " + string_data )
          if(line_index > int(index_from)-1):
            clipboard_string = clipboard_string + ',\'' + string_data + '\''
          else:
            clipboard_string = clipboard_string + '\'' + string_data + '\''

      clipboard_string = clipboard_string + '}'

      self.debug.info_message(" clipboard string: " + clipboard_string )
      clip.copy(clipboard_string)

    checked = values['cb_tmplt_clipcopyfrom']
    if(checked):
      self.form_gui.window['in_tmpl_clipcopyfrom'].update(str(line_index+1))
      self.form_gui.window['cb_tmplt_clipcopyfrom'].update(False)
      self.form_gui.window['cb_tmplt_clipcopyto'].update(True)

    return

  def event_tmpltupdate(self, values):
    self.debug.info_message("EVENT TABLE UPDATE\n")
    self.debug.info_message("line index: " + str(values['in_tmpl_line_number']) )

    line_index = int(values['in_tmpl_line_number'])-1

    self.debug.info_message("line index: " + str(line_index) )

    new_string = ''
    
    try:
      for x in range(18):
        field_name = 'combo_element' + str(x+1)
        if(values[field_name] != '-'):
          if(x > 0):		  
            new_string = new_string + ',' + self.form_gui.reverse_field_names[values[field_name] ]
          else:
            new_string = new_string + self.form_gui.reverse_field_names[values[field_name] ]
    except:
      self.debug.error_message("Exception in event_tmpltupdate: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("new string: " + new_string )
					  
    self.current_edit_string[2+line_index]=new_string

    formname = values['in_tmpl_name']
    filename = values['in_tmpl_file']
    category = self.current_edit_category
    self.debug.info_message("formname: " + formname )
    self.debug.info_message("filename: " + filename )
    self.debug.info_message("category: " + category )
    self.debug.info_message("edit string: " + str(self.current_edit_string) )
    js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
    self.debug.info_message("js: " + str(js) )
        
    table_data = self.updateSimulatedPreview(self.current_edit_string)
    self.form_gui.window['table_templates_preview'].update(values=table_data)

    return

  def event_tmplt_addrow(self, values):
    self.debug.info_message("EVENT TEMPLATE ADD ROW\n")

    insert_where = values['combo_tmplt_insertwhere']

    self.debug.info_message("combo value = " + str(insert_where) )

    if(insert_where == 'Before'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-1

        self.debug.info_message("line index is" + str(line_index) )
        new_string = 'T1'		
        self.current_edit_string.insert(line_index+2, new_string)
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)

        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index_form-1])

      self.debug.info_message("insert before\n")
    elif(insert_where == 'After'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-1

        self.debug.info_message("line index is" + str(line_index) )
        new_string = 'T1'		
        self.current_edit_string.insert(line_index+3, new_string)
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)
        self.form_gui.window['in_tmpl_line_number'].update(str(line_index+2))

        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index_form])

      self.debug.info_message("inser after\n")
    elif(insert_where == 'At'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-1

        self.debug.info_message("line index is" + str(line_index) )
        new_string = 'T1'		
        self.current_edit_string.insert(line_index+2, new_string)
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)
        self.form_gui.window['in_tmpl_line_number'].update(str(line_index+2))

        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index_form-1])

      self.debug.info_message("inser at\n")
    elif(insert_where == 'End'):
      self.debug.info_message("Insert at End\n")
      new_string = 'T1'		
      self.current_edit_string.append(new_string)
      self.debug.info_message("edit string: " + str(self.current_edit_string) )
      formname = values['in_tmpl_name']
      filename = values['in_tmpl_file']
      category = self.current_edit_category
      js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
      table_data = self.updateSimulatedPreview(self.current_edit_string)
      self.form_gui.window['table_templates_preview'].update(values=table_data)

    return

  def event_tmplt_typingsomething(self, values):
    self.debug.info_message("EVENT TYPING SOMETHING\n")

    categoryname = values['in_tmpl_category_name']
    templatename = values['in_tmpl_name']
    description  = values['in_tmpl_desc']
    version      = values['in_tmpl_ver']
    filename     = values['in_tmpl_file']
    return


  def event_composemsg(self, values):
    self.debug.info_message("BTN COMPOSE\n")

    line_index = int(values['tbl_compose_categories'][0])
    category = (self.group_arq.getCategories()[line_index])[0]
    line_index = int(values['tbl_compose_select_form'][0])
    formname = (self.group_arq.getTemplates()[line_index])[0]
    filename = (self.group_arq.getTemplates()[line_index])[3]
    form_content = ['', '', '', '']

    self.debug.info_message("SELECTED CATEGORY IS: "  + category )
    self.debug.info_message("SELECTED FORMNAME IS: "  + formname )

    selected_stations = self.group_arq.getSelectedStations()

    msgto = values['in_compose_selected_callsigns']
   
    callsign = self.saamfram.getMyCall()

    self.debug.info_message("saamfram: " + str(self.saamfram) +  "\n")

    ID = self.saamfram.getEncodeUniqueId(callsign)
   
    self.saamfram.getDecodeTimestampFromUniqueId(ID)

    self.debug.info_message("reverse encoded callsign is: " + self.group_arq.saamfram.getDecodeCallsignFromUniqueId(ID) )

    self.debug.info_message("UNIQUE ID USING UUID IS: " + str(ID) )
    subject = ''

    self.form_gui.render_disabled_controls = False

    window = self.form_gui.createDynamicPopupWindow(formname, form_content, category, msgto, filename, ID, subject, True)
    dispatcher = PopupControlsProc(self, window)
    self.form_gui.runPopup(self, dispatcher, window, False, False)

    return()

  def event_prevposttooutbox(self, values):
    self.debug.info_message("BTN POST TO OUTBOX\n")

    try:
      """ loop thru the dictionary to populate outbox display """
      fromform_ID = values['preview_message_id']	  
    
      self.debug.info_message("ID IS: " + str(fromform_ID) )

      ID = ''

      if(self.group_arq.saamfram.isReply(fromform_ID)):
        mainID = self.group_arq.getOriginalSenderID(fromform_ID)
        replyID = self.group_arq.getReplyID(fromform_ID)
        ID = replyID
      else:
        ID = fromform_ID

      timestamp = self.group_arq.saamfram.getDecodeTimestampFromUniqueId(ID)
      msgfrom   = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(ID)

      """ clean up the data pulled from the form. remove whitespace and uppercase it"""
      msgto = values['preview_message_msgto'].strip().upper()
      subject = values['preview_form_subject']
      priority = values['preview_message_priority']
      formname = values['preview_form_type']	  
      content = self.form_gui.extractContentFromForm(values)
 
      dictionary = self.form_dictionary.createOutboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content)
      message_dictionary = dictionary.get(ID)		  

      content   = message_dictionary.get('content')		  
      msgto     = message_dictionary.get('to')		  
      msgfrom   = message_dictionary.get('from')		  
      subject   = message_dictionary.get('subject')		  
      timestamp = message_dictionary.get('timestamp')		  
      priority  = message_dictionary.get('priority')		  
      msgtype   = message_dictionary.get('formname')		  
      self.group_arq.addMessageToOutbox(msgfrom, msgto, subject, timestamp, priority, msgtype, ID)
      self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )

      if(self.group_arq.saamfram.isReply(fromform_ID)):
        """ there is no need to refresh the inbox table as the item already exist this is just a sub page"""
        self.form_dictionary.addInboxDictionaryReply(mainID, replyID, msgto, msgfrom, subject, priority, timestamp, formname, content)

      self.form_dictionary.writeOutboxDictToFile('outbox.msg')
    except:
      self.debug.error_message("Exception in event_prevposttooutbox: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return()



  def event_prevchatpostandsend(self, values):
    self.debug.info_message("BTN CHAT POST AND SEND\n")

    try:

      selected_mode = values['option_chat_fldigimode'].split(' - ')[1]
      self.group_arq.fldigiclient.setMode(selected_mode)
      self.debug.info_message("selected chat mode is: " + selected_mode)

      """ loop thru the dictionary to populate outbox display """

      from_call = self.saamfram.getMyCall()
      ID = self.group_arq.saamfram.getEncodeUniqueId(from_call)

      timestamp = self.group_arq.saamfram.getDecodeTimestampFromUniqueId(ID)
      msgfrom   = self.group_arq.saamfram.getDecodeCallsignFromUniqueId(ID)

      """ clean up the data pulled from the form. remove whitespace and uppercase it"""

      msgto=''     
      checked = self.form_gui.window['cb_chat_useconnecto'].get()
      if(checked):
        msgto = values['in_inbox_listentostation'].strip().upper()
      else:
        msgto = values['in_chat_msgto'].strip().upper()

      subject = '' 
      """ priority None indicates the message is not to be saved anywhere """
      priority = 'None' 
      formname = 'QUICKMSG' 

      content = []
      content.append('')
      content.append('')
      content.append('')
      content.append('')
      content.append('')

      the_message = values['ml_chat_sendtext']	  
      content.append(the_message)

      dictionary = self.form_dictionary.createOutboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content)

      msgid = ID 
      tolist   = msgto 
      frag_size = 20
      
      sender_callsign = self.group_arq.saamfram.getMyCall()
      tagfile = 'ICS'
      version  = '1.3'
      complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

      self.form_dictionary.removeOutboxDictionaryItem(ID)
    
      sender_callsign = self.group_arq.saamfram.getMyCall()
      fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

      """ put the relay stations on the front end of the list. """
      revised_tolist = (self.group_arq.getRelayListFromSendList(tolist) + ';' + tolist).strip(';')

      self.debug.info_message("event_prevchatpostandsend. revised to list: " + revised_tolist)
  
      self.group_arq.sendFormRig1(fragtagmsg, revised_tolist.replace(';;',';'), msgid)

      self.group_arq.addChatData(sender_callsign, the_message, ID)
      self.form_gui.window['table_chat_received_messages'].update(values=self.group_arq.getChatData())

    except:
      self.debug.error_message("Exception in event_prevchatpostandsend: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return()


  def event_tableoutboxmessages(self, values):
    self.debug.info_message("TABLE OUTBOX MESSAGES\n")

    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]

    self.debug.info_message("MESSAGE ID = " + str(msgid) )

    form_content = self.form_dictionary.getContentFromOutboxDictionary(msgid)

    mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)
    use_dynamic_content_macro = False
    text_render, table_data, actual_render = self.form_gui.renderPage(mytemplate, use_dynamic_content_macro, form_content)

    self.form_gui.form_events.changeFlashButtonState('btn_outbox_sendselected', True)
    self.form_gui.form_events.changeFlashButtonState('btn_compose_areyoureadytoreceive', True)


    self.form_gui.window['table_outbox_preview'].update(values=table_data )
    return

  def event_tableinboxmessages(self, values):
    self.debug.info_message("TABLE INBOX MESSAGES\n")

    line_index = int(values['table_inbox_messages'][0])
    msgid = (self.group_arq.getMessageInbox()[line_index])[7]
    formname = self.form_dictionary.getFormnameFromInboxDictionary(msgid)

    self.debug.info_message("MESSAGE ID AND FORMNAME = " + str(msgid) + "," + formname)

    form_content = self.form_dictionary.getContentFromInboxDictionary(msgid)

    mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)
    use_dynamic_content_macro = False
    text_render, table_data, actual_render = self.form_gui.renderPage(mytemplate, use_dynamic_content_macro, form_content)
    
    self.form_gui.form_events.changeFlashButtonState('btn_inbox_sendreqm', True)
    self.form_gui.form_events.changeFlashButtonState('btn_inbox_viewmsg', True)


    self.form_gui.window['table_inbox_preview'].update(values=table_data )

    return

  def event_tablerelayboxmessages(self, values):
    self.debug.info_message("TABLE RELAYBOX MESSAGES\n")

    line_index = int(values['table_relay_messages'][0])
    msgid = (self.group_arq.getMessageRelaybox()[line_index])[6]
    formname = self.form_dictionary.getFormnameFromRelayboxDictionary(msgid)

    self.debug.info_message("MESSAGE ID AND FORMNAME = " + str(msgid) + "," + formname)

    form_content = self.form_dictionary.getContentFromRelayboxDictionary(msgid)

    mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)
    use_dynamic_content_macro = False
    text_render, table_data, actual_render = self.form_gui.renderPage(mytemplate, use_dynamic_content_macro, form_content)
    
    self.form_gui.form_events.changeFlashButtonState('btn_relay_copytooutbox', True)
    self.form_gui.form_events.changeFlashButtonState('btn_relay_sendreqm', True)


    self.form_gui.window['table_relaybox_preview'].update(values=table_data )

    return



  def event_outboxeditform(self, values):
    self.debug.info_message("OUTBOX EDIT FORM\n")

    line_index = int(values['table_outbox_messages'][0])
    ID        = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname  = (self.group_arq.getMessageOutbox()[line_index])[5]
    priority  = (self.group_arq.getMessageOutbox()[line_index])[4]
    timestamp = (self.group_arq.getMessageOutbox()[line_index])[3]
    subject   = (self.group_arq.getMessageOutbox()[line_index])[2]
    msgto     = (self.group_arq.getMessageOutbox()[line_index])[1]
    msgfrom   = (self.group_arq.getMessageOutbox()[line_index])[0]
    

    form_content = ['gfhjgfhj', 'asdf', 'gfhjgfhj', 'sadf']

    category, filename = self.form_dictionary.getCategoryAndFilenameFromFormname(formname)

    form_content = self.form_dictionary.getContentFromOutboxDictionary(ID)


    """ create a new ID as this message is being edited."""
    ID = self.saamfram.getEncodeUniqueId(self.saamfram.getMyCall())

    self.form_gui.render_disabled_controls = False
   
    window = self.form_gui.createDynamicPopupWindow(formname, form_content, category, msgto, filename, ID, subject, False)
    dispatcher = PopupControlsProc(self, window)
    self.form_gui.runPopup(self, dispatcher, window, False, False)
    return

  def event_settingslist(self, values):
    self.debug.info_message("SETTINGS LIST\n")

    try:
      self.debug.info_message("self.form_gui.window: " + str(self.form_gui) )
    except:  
      self.debug.error_message("Exception in event_settingslist: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    """ Code to locate all the template files """
    self.group_arq.clearTemplateFiles()
    folder = values['in_settings_templatefolder']
    dir_list = os.listdir(folder)
    for x in dir_list:
      if x.endswith(".tpl"):
        self.debug.info_message("template file located: " + str(x) )
        self.group_arq.addTemplateFile(str(x))
    self.form_gui.window['tbl_layout_all_files'].update(self.group_arq.getTemplateFiles())

    return


  def event_compose_categories(self, values):
    self.debug.info_message("EVENT TMPLT CATEGORIES\n")
    line_index = int(values['tbl_compose_categories'][0])
    category = (self.group_arq.getCategories()[line_index])[0]

    self.debug.info_message("category: " + category )

    self.form_dictionary.getTemplatesFromCategory(category)

    self.current_edit_category = category

    self.form_gui.window['tbl_compose_select_form'].update(self.group_arq.getTemplates())

    return


  def event_mainpanelsaveasfile(self, values):

    save_file_name = self.form_gui.window['in_mainpanel_saveasfilename'].get()

    shutil.copyfile('./sent_data.dat', save_file_name)

    self.debug.info_message("event_mainpanelsaveasfile\n")

    self.form_gui.form_events.changeFlashButtonState('in_mainpanel_saveasfilename', False)

  def event_mainpanelsaveasimagefile(self, values):

    save_file_name = self.form_gui.window['in_mainpanel_saveasimagefilename'].get()

    shutil.copyfile('./received_image.jpg', save_file_name)

    self.debug.info_message("event_mainpanelsaveasimagefile\n")

    self.form_gui.form_events.changeFlashButtonState('in_mainpanel_saveasimagefilename', False)


  def event_mainpanelsendimagefile(self, values):
    self.debug.info_message("event_mainpanelsendimagefile")

    selected_mode = values['option_filexfer_fldigimode'].split(' - ')[1]
    self.group_arq.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected file xfer mode is: " + selected_mode)


    sender_callsign = self.group_arq.saamfram.getMyCall()
    msgid = self.group_arq.saamfram.getEncodeUniqueId(sender_callsign)
    formname = ''
    priority = ''
    subject  = ''
    tolist   = self.form_gui.window['in_inbox_listentostation'].get()

    frag_size = 200
    tagfile = 'ICS'
    version  = '1.0'

    complete_send_string = ''

    filename =  'compressed.jpg' #self.form_gui.window['in_mainpanel_sendfilename'].get()

    self.debug.info_message("selected filename is : " + filename )

    content = self.saamfram.getBinaryFile(filename)
    
    self.debug.info_message("OK got the data: " + str(content) )

    complete_send_string = self.group_arq.saamfram.getImageFileSendString(msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("EVENT SEND FILE 3\n")
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("SEND STRING IS: " + fragtagmsg )
    self.debug.info_message("ACTUAL MSG SENT TO FLDIGI: " + str(fragtagmsg) )
    
    self.group_arq.sendFormRig1(fragtagmsg, tolist, msgid)

    return



  def event_mainpanelsendfile(self, values):
    self.debug.info_message("event_mainpanelsendfile\n")

    selected_mode = values['option_filexfer_fldigimode'].split(' - ')[1]
    self.group_arq.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected file xfer mode is: " + selected_mode)

    sender_callsign = self.group_arq.saamfram.getMyCall()
    msgid = self.group_arq.saamfram.getEncodeUniqueId(sender_callsign)
    formname = ''
    priority = ''
    subject  = ''
    tolist   = self.form_gui.window['in_inbox_listentostation'].get()

    frag_size = 200
    tagfile = 'ICS'
    version  = '1.0'

    complete_send_string = ''

    filename =  self.form_gui.window['in_mainpanel_sendfilename'].get()

    self.debug.info_message("selected filename is : " + filename )

    content = self.saamfram.getBinaryFile(filename)
    
    self.debug.info_message("OK got the data: " + str(content) )

    complete_send_string = self.group_arq.saamfram.getFileSendString(msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("EVENT SEND FILE 3\n")
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("SEND STRING IS: " + fragtagmsg )
    self.debug.info_message("ACTUAL MSG SENT TO FLDIGI: " + str(fragtagmsg) )
    
    self.group_arq.sendFormRig1(fragtagmsg, tolist, msgid)

    return

  def event_outboxsendselectedasfile(self, values):
    self.debug.info_message("event_outboxsendselectedasfile\n")
    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]
    priority = (self.group_arq.getMessageOutbox()[line_index])[4]
    subject  = (self.group_arq.getMessageOutbox()[line_index])[2]
    tolist   = (self.group_arq.getMessageOutbox()[line_index])[1]

    self.debug.info_message("event_outboxsendselectedasfile 2\n")
    
    frag_size = 50
    #frag_string = values['option_framesize'].strip()
    #if(frag_string != ''):
    #  frag_size = int(values['option_framesize'])
      
    include_template = values['cb_outbox_includetmpl']

    self.debug.info_message("event_outboxsendselectedasfile 2b\n")

    sender_callsign = self.group_arq.saamfram.getMyCall()
    tagfile = 'ICS'
    version  = '1.0'
    complete_send_string = ''

    complete_send_string = self.group_arq.saamfram.getHRRMSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("event_outboxsendselectedasfile 3\n")

    try:
      self.debug.info_message("event_outboxsendselectedasfile complete send string = " + complete_send_string)

      compressionlevel=9
      self.debug.info_message("event_outboxsendselectedasfile 4\n")
      encoded_send_string = base64.b64encode(bz2.compress(bytes(complete_send_string, 'utf-8'), compressionlevel))

      self.debug.info_message("event_outboxsendselectedasfile encoded send string = " + str(encoded_send_string))

      self.debug.info_message("event_outboxsendselectedasfile 5\n")
      complete_send_string = str(encoded_send_string.decode())

      self.debug.info_message("event_outboxsendselectedasfile decoded send string = " + complete_send_string)

      self.debug.info_message("event_outboxsendselectedasfile 6\n")


    except:
      self.debug.error_message("Exception in event_outboxsendselectedasfile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("event_outboxsendselectedasfile 7\n")


    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.group_arq.sendFormRig1(fragtagmsg, tolist, msgid)

    self.form_dictionary.transferOutboxMsgToSentbox(msgid)
    #self.form_dictionary.transferOutboxMsgToRelaybox(msgid)

    self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
    self.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )
    self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )

    return




  def event_outboxsendselected(self, values):
    self.debug.info_message("EVENT OUTBOX SEND SELECTED\n")

    selected_mode = values['option_outbox_fldigimode'].split(' - ')[1]
    self.group_arq.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected outbox mode is: " + selected_mode)

    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]
    priority = (self.group_arq.getMessageOutbox()[line_index])[4]
    subject  = (self.group_arq.getMessageOutbox()[line_index])[2]
    tolist   = (self.group_arq.getMessageOutbox()[line_index])[1]

    self.debug.info_message("EVENT OUTBOX SEND SELECTED 2\n")
    
    frag_size = 20
    frag_string = values['option_framesize'].strip()
    if(frag_string != ''):
      frag_size = int(values['option_framesize'])
      
    include_template = values['cb_outbox_includetmpl']

    self.debug.info_message("EVENT OUTBOX SEND SELECTED 2b\n")

    # this is for testing only!!!!!!
    #FIXME

    sender_callsign = self.group_arq.saamfram.getMyCall()
    tagfile = 'ICS'
    version  = '1.3'
    complete_send_string = ''
    if(include_template):
      self.debug.info_message("EVENT OUTBOX SEND SELECTED 2c\n")

      complete_send_string = self.group_arq.saamfram.getContentAndTemplateSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)
    else:  
      self.debug.info_message("EVENT OUTBOX SEND SELECTED 2d\n")

      complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("EVENT OUTBOX SEND SELECTED 3\n")
    self.form_dictionary.transferOutboxMsgToSentbox(msgid)

    self.form_dictionary.transferOutboxMsgToRelaybox(msgid)
    self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )

    self.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )
    self.debug.info_message("EVENT OUTBOX SEND SELECTED 4\n")

    
    self.debug.info_message("EVENT OUTBOX SEND SELECTED 5\n")
    
    sender_callsign = self.group_arq.saamfram.getMyCall()
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("SEND STRING IS: " + fragtagmsg )
    
    self.debug.info_message("ACTUAL MSG SENT TO FLDIGI: " + str(fragtagmsg) )
    
    self.group_arq.sendFormRig1(fragtagmsg, tolist, msgid)

    self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )

    return

  def event_outboxsendall(self, values):
    self.debug.info_message("EVENT OUTBOX SEND ALL\n")

    for line_index in reversed(range(len(self.group_arq.getMessageOutbox()))):
      msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
      formname = (self.group_arq.getMessageOutbox()[line_index])[5]
      priority = (self.group_arq.getMessageOutbox()[line_index])[4]
      subject  = (self.group_arq.getMessageOutbox()[line_index])[2]
      tolist   = (self.group_arq.getMessageOutbox()[line_index])[1]
 
      frag_size = int(values['option_framesize'])
      include_template = values['cb_outbox_includetmpl']


      complete_send_string = ''
      sender_callsign = self.saamfram.getMyCall()
      tagfile = 'ICS'
      version  = '1.3'
      if(include_template):
        complete_send_string = self.group_arq.saamfram.getContentAndTemplateSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)
      else:  
        complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

      self.form_dictionary.transferOutboxMsgToSentbox(msgid)

    self.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )

    return

  def event_outboxdeletemsg(self, values):
    self.debug.info_message("EVENT OUTBOX DELETE SELECTED\n")

    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]

    self.form_dictionary.outbox_file_dictionary_data.pop(msgid, None)
    self.group_arq.deleteMessageFromOutbox(msgid)
    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )
    return


  def event_outboxdeleteallmsg(self, values):
    self.debug.info_message("EVENT OUTBOX DELETE ALL\n")

    self.form_dictionary.outbox_file_dictionary_data = {}
    self.group_arq.clearOutbox()
    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )
    return


  def event_sentboxdeletemsg(self, values):
    self.debug.info_message("EVENT SENTBOX DELETE SELECTED\n")

    line_index = int(values['table_sent_messages'][0])
    msgid = (self.group_arq.getMessageSentbox()[line_index])[6]

    self.form_dictionary.sentbox_file_dictionary_data.pop(msgid, None)
    self.group_arq.deleteMessageFromSentbox(msgid)
    self.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
    return

  def event_sentboxdeleteallmsg(self, values):
    self.debug.info_message("EVENT SENTBOX DELETE ALL\n")

    self.form_dictionary.sentbox_file_dictionary_data = {}
    self.group_arq.clearSentbox()
    self.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
    return


  def event_inboxdeleteselected(self, values):
    self.debug.info_message("EVENT INBOX DELETE SELECTED\n")

    line_index = int(values['table_inbox_messages'][0])
    msgid = (self.group_arq.getMessageInbox()[line_index])[7]

    self.form_dictionary.inbox_file_dictionary_data.pop(msgid, None)
    self.group_arq.deleteMessageFromInbox(msgid)
    self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )

    return

  def event_inboxdeleteall(self, values):
    self.debug.info_message("EVENT INBOX DELETE ALL\n")

    for line_index in reversed(range(len(self.group_arq.getMessageInbox()))):
      msgid = (self.group_arq.getMessageInbox()[line_index])[7]
      self.group_arq.deleteMessageFromInbox(msgid)

    self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )

    self.form_dictionary.resetInboxDictionary()

    return


  def event_relayboxdeleteselected(self, values):
    self.debug.info_message("EVENT RELAYBOX DELETE SELECTED\n")

    line_index = int(values['table_relay_messages'][0])
    msgid = (self.group_arq.getMessageRelaybox()[line_index])[6]

    self.form_dictionary.relaybox_file_dictionary_data.pop(msgid, None)
    self.group_arq.deleteMessageFromRelaybox(msgid)
    self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )

    return

  def event_relayboxdeleteall(self, values):
    self.debug.info_message("EVENT RELAYBOX DELETE ALL\n")

    for line_index in reversed(range(len(self.group_arq.getMessageRelaybox()))):
      msgid = (self.group_arq.getMessageRelaybox()[line_index])[6]
      self.group_arq.deleteMessageFromRelaybox(msgid)

    self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )

    self.form_dictionary.resetRelayboxDictionary()

    return




  def event_tablesentmessages(self, values):
    self.debug.info_message("EVENT TABLE SENT MESSAGES\n")

    line_index = int(values['table_sent_messages'][0])
    msgid = (self.group_arq.getMessageSentbox()[line_index])[6]
    formname = self.form_dictionary.getFormnameFromSentboxDictionary(msgid)

    self.debug.info_message("MESSAGE ID AND FORMNAME = " + str(msgid) + "," + formname)

    form_content = self.form_dictionary.getContentFromSentboxDictionary(msgid)

    mytemplate = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)
    use_dynamic_content_macro = False
    text_render, table_data, actual_render = self.form_gui.renderPage(mytemplate, use_dynamic_content_macro, form_content)

    self.form_gui.window['table_sent_preview'].update(values=table_data )

    return


  def event_outboxreqconfirm(self, values):
    self.debug.info_message("EVENT RESEND FRAMES OUTBOX REQUEST CONFIRM\n")

    to_callsign = self.saamfram.getSenderCall()
    from_callsign = self.saamfram.getMyCall()
    resend_frames = values['in_outbox_resendframes']
    self.group_arq.resendFrames(resend_frames, from_callsign, to_callsign)

    return

  def event_inboxrcvstatus(self, values):
    self.debug.info_message("EVENT INBOX SEND RCV STATUS\n")

    frames_missing = self.group_arq.saamfram.getFramesMissingReceiver("ABC_FDE", 5)
    self.debug.info_message("FRAMES MISSING: " + frames_missing + " \n")
    
    #FIXME CALL SIGNS SHOULD NOT BE HARDCODED
    self.group_arq.sendFormRig1("WH6ABC 3495865_DFE567 " + frames_missing, '', None)

    return

  def event_templateseditline(self, values):
    self.form_gui.window['cb_templates_insertdeleteline'].update(False)
    self.form_gui.window['btn_tmplt_update'].update(disabled = False)
    self.form_gui.window['btn_tmplt_add_row'].update(disabled = True)
    self.form_gui.window['btn_delete_row'].update(disabled = True)
    self.form_gui.window['in_tmpl_line_number'].update(disabled = False)
    self.form_gui.window['in_tmpl_insert_linenumber'].update(disabled = True)
    self.form_gui.window['combo_tmplt_insertwhere'].update(disabled = True)
    
    
    return
    
  def event_templatesinsertdeleteline(self, values):
    self.form_gui.window['cb_templates_editline'].update(False)
    self.form_gui.window['btn_tmplt_update'].update(disabled = True)
    self.form_gui.window['btn_tmplt_add_row'].update(disabled = False)
    self.form_gui.window['btn_delete_row'].update(disabled = False)
    self.form_gui.window['in_tmpl_line_number'].update(disabled = True)
    self.form_gui.window['in_tmpl_insert_linenumber'].update(disabled = False)
    self.form_gui.window['combo_tmplt_insertwhere'].update(disabled = False)
    
    return

  def event_tmpltdeletetemplatecategory(self, values):

    self.debug.info_message("EVENT TMPLT DELETE TEMPLATE CATEGORY\n")
    
    filename = values['in_tmpl_file']
    category = values['in_tmpl_category_name']
    
    self.debug.info_message("FILENAME:  " + str(filename) )
    self.debug.info_message("CATEGORY:  " + str(category) )

    self.form_dictionary.removeCategoryFromTemplateDictionary(filename, category)
    self.group_arq.deleteCategory(category)
    self.form_gui.window['tbl_tmplt_categories'].update(self.group_arq.getCategories())
    self.form_gui.window['tbl_tmplt_templates'].update([])

    return

  def event_composeselectform(self, values):

    self.debug.info_message("EVENT COMPOSE SELECT FORM\n")
    
    self.debug.info_message("EVENT TMPLT TEMPLATE\n")
    
    line_index = int(values['tbl_compose_select_form'][0])
    field_1 = (self.group_arq.getTemplates()[line_index])[0]
    field_2 = (self.group_arq.getTemplates()[line_index])[1]
    field_3 = (self.group_arq.getTemplates()[line_index])[2]
    field_4 = (self.group_arq.getTemplates()[line_index])[3]

    """ enable the compose button on compose tab"""
    self.form_gui.window['btn_cmpse_compose'].update(disabled = False)


    edit_list = self.form_dictionary.getDataFromDictionary(field_1, field_2, field_3, field_4)

    self.debug.info_message("edit string: " + str(edit_list) )

    self.debug.info_message("UPDATEING SIMULATED PREVIEW WITH: " + str(edit_list) )
    table_data = self.updateSimulatedPreview(edit_list)

    self.debug.info_message("table data : " + str(table_data) )

    self.form_gui.window['table_compose_preview'].update(values=table_data)

    self.current_edit_string = edit_list

    self.debug.info_message("edit string: " + str(self.current_edit_string) )
    
    return

  def event_outboxfldigimode(self, values):

    self.debug.info_message("EVENT OUTBOX FLDIGI MODE\n")
   
    selected_string = values['option_outbox_fldigimode']
    split_string = selected_string.split(' - ')
    mode = split_string[1]

    self.group_arq.fldigiclient.setMode(mode)

    return

  def event_inboxsendacknack(self, values):

    self.debug.info_message("EVENT SEND ACK NACK\n")

    error_frames = values['in_inbox_errorframes'].strip()
    from_callsign = self.saamfram.getMyCall()
    to_callsign = self.saamfram.getSenderCall()
    if(error_frames == ''):
      self.group_arq.sendAck(from_callsign, to_callsign)
    else:  
      self.group_arq.sendNack(error_frames, from_callsign, to_callsign)

    return


  def event_outboxpleaseconfirm(self, values):

    self.debug.info_message("EVENT PLEASE COONFIRM\n")

    to_callsign = self.saamfram.getSenderCall()
    from_callsign = self.saamfram.getMyCall()
    self.group_arq.requestConfirm(from_callsign, to_callsign)

  def event_inboxcopyclipboard(self, values):

    self.debug.info_message("event_inboxcopyclipboard")
    text_table = self.form_gui.window['table_inbox_preview'].get()
    self.debug.info_message("preview text is: " + str(text_table) )

    self.debug.info_message("event_inboxcopyclipboard LOC1")

    text = ''
    for x in range(len(text_table)):
      text = text + text_table[x][0] + '\n'

    self.debug.info_message("preview text is: " + str(text) )


    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]
    priority = (self.group_arq.getMessageOutbox()[line_index])[4]
    subject  = (self.group_arq.getMessageOutbox()[line_index])[2]
    tolist   = (self.group_arq.getMessageOutbox()[line_index])[1]

    self.debug.info_message("event_inboxcopyclipboard LOC2")
   
    frag_size = 30
    frag_string = values['option_framesize'].strip()
    if(frag_string != ''):
      frag_size = int(values['option_framesize'])

    self.debug.info_message("event_inboxcopyclipboard LOC3")
      
    sender_callsign = self.group_arq.saamfram.getMyCall()
    tagfile = 'ICS'
    version  = '1.3'

    self.debug.info_message("event_inboxcopyclipboard LOC4")

    complete_send_string = ''
    include_template = values['cb_outbox_includetmpl']
    if(include_template):
      complete_send_string = self.group_arq.saamfram.getContentAndTemplateSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)
    else:  
      complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("event_inboxcopyclipboard LOC5")
    
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("event_inboxcopyclipboard LOC6")


    clip.copy(text + '\n\n\nSaam-Mail-Export=' + fragtagmsg)


  def event_outboxcopyclipboard(self, values):

    self.debug.info_message("event_outboxcopyclipboard")

    text_table = self.form_gui.window['table_outbox_preview'].get()

    text = ''
    for x in range(len(text_table)):
      text = text + text_table[x][0] + '\n'

    self.debug.info_message("preview text is: " + str(text) )

    line_index = int(values['table_outbox_messages'][0])
    msgid = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]
    priority = (self.group_arq.getMessageOutbox()[line_index])[4]
    subject  = (self.group_arq.getMessageOutbox()[line_index])[2]
    tolist   = (self.group_arq.getMessageOutbox()[line_index])[1]

    self.debug.info_message("event_inboxcopyclipboard LOC2")
   
    frag_size = 30
    frag_string = values['option_framesize'].strip()
    if(frag_string != ''):
      frag_size = int(values['option_framesize'])

    self.debug.info_message("event_inboxcopyclipboard LOC3")
      
    sender_callsign = self.group_arq.saamfram.getMyCall()
    tagfile = 'ICS'
    version  = '1.3'

    self.debug.info_message("event_inboxcopyclipboard LOC4")

    complete_send_string = ''
    include_template = values['cb_outbox_includetmpl']
    if(include_template):
      complete_send_string = self.group_arq.saamfram.getContentAndTemplateSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)
    else:  
      complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("event_inboxcopyclipboard LOC5")
    
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("event_inboxcopyclipboard LOC6")


    clip.copy(text + '\n\n\nSaam-Mail-Export=' + fragtagmsg)


  def event_outboximportfromclipboard(self, values):

    self.debug.info_message("event_outboximportfromclipboard")

    text_from_clipboard = clip.paste()
    self.debug.info_message(text_from_clipboard)

    split_string = text_from_clipboard.split('Saam-Mail-Export=')
    if(len(split_string)==1):
      split_string = text_from_clipboard.split('SAAM-MAIL-EXPORT=')
    if(len(split_string)==1):
      self.debug.info_message("event_outboximportfromclipboard LOC3")
      return
    else:
      self.debug.info_message("event_outboximportfromclipboard LOC4")
      self.debug.info_message("EXPORT STRING: " + split_string[1])
      self.saamfram.processIncomingMessage(split_string[1])



  def event_inboxreplytomsg(self, values):

    self.debug.info_message("EVENT REPLY TO INBOX MESSAGE\n")

    line_index = int(values['table_inbox_messages'][0])
    mainID = (self.group_arq.getMessageInbox()[line_index])[7]

    line_index = int(values['tbl_compose_categories'][0])
    category = (self.group_arq.getCategories()[line_index])[0]
    line_index = int(values['tbl_compose_select_form'][0])
    formname = (self.group_arq.getTemplates()[line_index])[0]
    filename = (self.group_arq.getTemplates()[line_index])[3]
   
    form_content = ['', '', '', '']

    self.debug.info_message("SELECTED CATEGORY IS: "  + category )
    self.debug.info_message("SELECTED FORMNAME IS: "  + formname )

    selected_stations = self.group_arq.getSelectedStations()
    msgto = ''
    for x in range(len(selected_stations)):
      if(x>0):		
        msgto = msgto + ';' + str(selected_stations[x])
      else:		
        msgto = msgto + str(selected_stations[x])
    
    callsign = self.saamfram.getMyCall()

    self.debug.info_message("mainID: "  + mainID )

    replyID = mainID + '-' + self.group_arq.saamfram.getEncodeUniqueId(callsign)

    self.debug.info_message("UNIQUE ID USING UUID IS: " + str(replyID) )
    
    subject = ''

    self.form_gui.render_disabled_controls = False

    window = self.form_gui.createInboxViewReplyWindow(formname, form_content, category, msgto, filename, replyID, subject, True, True, True)
    dispatcher = PopupControlsProc(self, window)
    self.form_gui.runPopup(self, dispatcher, window, False, False)


  def event_inboxviewmsg(self, values):

    self.debug.info_message("EVENT INBOX VIEW MSG\n")

    line_index = int(values['table_inbox_messages'][0])
    ID = (self.group_arq.getMessageInbox()[line_index])[7]
    formname = (self.group_arq.getMessageInbox()[line_index])[5]
    category, filename = self.form_dictionary.getCategoryAndFilenameFromFormname(formname)

    form_content = ['', '', '', '']

    self.debug.info_message("SELECTED CATEGORY IS: "  + category )
    self.debug.info_message("SELECTED FORMNAME IS: "  + formname )

    selected_stations = self.group_arq.getSelectedStations()
    msgto = ''
    for x in range(len(selected_stations)):
      if(x>0):		
        msgto = msgto + ';' + str(selected_stations[x])
      else:		
        msgto = msgto + str(selected_stations[x])
    
    self.group_arq.saamfram.getDecodeTimestampFromUniqueId(ID)

    self.debug.info_message("reverse encoded callsign is: " + self.group_arq.saamfram.getDecodeCallsignFromUniqueId(ID) )
    self.debug.info_message("UNIQUE ID USING UUID IS: " + str(ID) )

    subject = ''
    self.form_gui.render_disabled_controls = True

    window = self.form_gui.createInboxViewReplyWindow(formname, form_content, category, msgto, filename, ID, subject, False, False, False)
    dispatcher = PopupControlsProc(self, window)
    self.form_gui.runPopup(self, dispatcher, window, False, True)


  def event_fordesignerInsertElement(self, values):
    self.debug.info_message("INSERT ELEMENT\n")

    at_before_after = values['combo_tmplt_insertelementwhere'].strip()
    self.debug.info_message("at_before_after = " + str(at_before_after) + " \n")
    index = int(values['in_tmpl_insertelementnumber'])
    self.debug.info_message("index = " + str(index) + " \n")

    start_index = 0
    end_index = 18
    if(at_before_after == 'At' or at_before_after == 'Before'):
      start_index = index
    elif(at_before_after == 'After'):
      start_index = index +1

    self.debug.info_message("start index = " + str(start_index) + " \n")
    self.debug.info_message("end index = " + str(end_index) + " \n")

    for x in reversed (range (start_index, end_index)):
      field_name_from = 'combo_element' + str(x)
      field_name_to = 'combo_element' + str(x+1)
      contents = values[field_name_from]
      self.form_gui.window[field_name_to].update(contents)

    self.form_gui.window[field_name_from].update('-')

  def event_fordesignerDeleteElement(self, values):

    self.debug.info_message("DELETE ELEMENT\n")

    at_before_after = values['combo_tmplt_insertelementwhere'].strip()
    self.debug.info_message("at_before_after = " + str(at_before_after) + " \n")
    index = int(values['in_tmpl_insertelementnumber'])
    self.debug.info_message("index = " + str(index) + " \n")

    start_index = 0
    end_index = 18
    if(at_before_after == 'At' or at_before_after == 'Before'):
      start_index = index
    elif(at_before_after == 'After'):
      start_index = index +1

    self.debug.info_message("start index = " + str(start_index) + " \n")
    self.debug.info_message("end index = " + str(end_index) + " \n")

    for x in range (start_index, end_index):
      field_name_from = 'combo_element' + str(x+1)
      field_name_to = 'combo_element' + str(x)
      contents = values[field_name_from]
      self.form_gui.window[field_name_to].update(contents)

    self.form_gui.window[field_name_from].update('-')

  def event_tmpltnewcategory(self, values):
    self.debug.info_message("NEW CATEGORY\n")

    category    = values['in_tmpl_category_name']
    formname    = values['in_tmpl_name']
    description = values['in_tmpl_desc']
    version     = values['in_tmpl_ver']
    filename    = values['in_tmpl_file']

    data = [version,description,'T1,I1']
    self.form_dictionary.createNewTemplateInDictionary(filename, category, formname, version, description, data)
    self.group_arq.addCategory(category)
    self.group_arq.addTemplate(formname, description, version, filename)

    table_data = self.updateSimulatedPreview(data)
    self.debug.info_message("table data : " + str(table_data) )
    self.form_gui.window['table_templates_preview'].update(values=table_data)
    self.current_edit_string = data

    self.debug.info_message("EVENT TMPLT NEW TEMPLATE 5\n")

    self.form_gui.window['tbl_tmplt_categories'].update(self.group_arq.getCategories())
    self.form_gui.window['tbl_tmplt_templates'].update(self.group_arq.getTemplates())
    return

  def event_tmpltdeleterow(self, values):
    self.debug.info_message("TEMPLATE DELETE ROW\n")

    insert_where = values['combo_tmplt_insertwhere']

    self.debug.info_message("combo value = " + str(insert_where) )

    #FIXME NEEDS TO REMOVE THE DATA FROM THE DICTIONARY ITEM
    if(insert_where == 'At'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-1

        self.debug.info_message("line index is" + str(line_index) )

        del self.current_edit_string[line_index+2]
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)
        self.form_gui.window['in_tmpl_line_number'].update(str(line_index+2))

        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index_form-1])

      self.debug.info_message("inser after\n")
    elif(insert_where == 'Before'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-2

        self.debug.info_message("line index is" + str(line_index) )

        del self.current_edit_string[line_index+2]

        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)

        #FIXME NEED TO GO BACK THRU THE XREF TABLE THEN BACK AGAIN
        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index_form-2])

      self.debug.info_message("insert before\n")
    elif(insert_where == 'After'):
      linestr = values['table_templates_preview']
      self.debug.info_message("line str is: " + str(linestr) )
      if(linestr != '[]'):		
        line_index_form = int(values['table_templates_preview'][0])+1
        line_index = self.tablerow_templaterow_xref[line_index_form]-1

        self.debug.info_message("line index is" + str(line_index) )
        del self.current_edit_string[line_index+3]

        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)
        self.form_gui.window['in_tmpl_line_number'].update(str(line_index+2))

        self.form_gui.window['table_templates_preview'].update(select_rows=[line_index])

      self.debug.info_message("inser after\n")
    elif(insert_where == 'End'):
      self.debug.info_message("Insert at End\n")
      del self.current_edit_string[len(self.current_edit_string)-1]
      self.debug.info_message("edit string: " + str(self.current_edit_string) )
      formname = values['in_tmpl_name']
      filename = values['in_tmpl_file']
      category = self.current_edit_category
      js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
      table_data = self.updateSimulatedPreview(self.current_edit_string)
      self.form_gui.window['table_templates_preview'].update(values=table_data)

      self.form_gui.window['table_templates_preview'].update(select_rows=[len(self.current_edit_string)-2])

    return

  def event_tmpltduplicaterow(self, values):
    self.debug.info_message("TEMPLATE DUPLICATE ROW\n")

    line_index_form = int(values['in_tmpl_line_number'])-1

    self.debug.info_message("line index form: " + str(line_index_form) )
    line_index_form = int(values['table_templates_preview'][0])+1
    line_index = self.tablerow_templaterow_xref[line_index_form]-1
    self.debug.info_message("line index: " + str(line_index) )

    new_string = ''
    
    try:
      for x in range(18):
        field_name = 'combo_element' + str(x+1)
        if(values[field_name] != '-'):
          if(x > 0):		  
            new_string = new_string + ',' + self.form_gui.reverse_field_names[values[field_name] ]
          else:
            new_string = new_string + self.form_gui.reverse_field_names[values[field_name] ]
    except:
      self.debug.error_message("Exception in event_tmpltduplicaterow: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("new string: " + new_string )
					  
    formname = values['in_tmpl_name']
    filename = values['in_tmpl_file']
    self.current_edit_string.insert(line_index+2, new_string)
    category = self.current_edit_category
    js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
    self.debug.info_message("js: " + str(js) )
        
    table_data = self.updateSimulatedPreview(self.current_edit_string)
    self.form_gui.window['table_templates_preview'].update(values=table_data)

    self.form_gui.window['table_templates_preview'].update(select_rows=[line_index+1])

    return

  def event_outboxtxrig(self, values):
    self.debug.info_message("OUTBOX SELECT TXRIG\n")

    txrig = values['option_outbox_txrig']

    self.debug.info_message("TXRIG: " + str(txrig) )

    saam = self.getSaamfram()
    saam.setTxRig(txrig)

    return



  def event_compose_qrysaam(self, values):
    self.debug.info_message("COMPOSE QUERY SAAM\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendQuerySAAM(from_call, group_name)
    saam.send('SAAM?')

    return

  def event_compose_cqcqcq(self, values):
    self.debug.info_message("COMPOSE CQCQCQ\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendCQCQCQ(from_call, group_name)
    return

  def event_btnmainpaneltestprop(self, values):
    self.debug.info_message("COMPOSE TEST PROPAGATION\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendTestProp(from_call, group_name)
    return



  def event_compose_copycopy(self, values):
    self.debug.info_message("COMPOSE COPYCOPY\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendCopy(from_call, group_name)
    return

  def event_compose_rr73(self, values):
    self.debug.info_message("COMPOSE RR73\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendRR73(from_call, group_name)
    return

  def event_compose_73(self, values):
    self.debug.info_message("COMPOSE 73\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.send73(from_call, group_name)
    return

  def event_compose_checkin(self, values):
    self.debug.info_message("COMPOSE CKIN\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendCheckin(from_call, group_name)
    return

  def event_compose_standby(self, values):
    self.debug.info_message("COMPOSE STBY\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendStandby(from_call, group_name)
    return

  def event_compose_qrt(self, values):
    self.debug.info_message("COMPOSE QRT\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendQrt(from_call, group_name)
    return

  def event_compose_saam(self, values):
    self.debug.info_message("COMPOSE SAAM\n")

    saam = self.getSaamfram()
    from_call = self.saamfram.getMyCall()
    group_name = self.saamfram.getMyGroup()
    saam.sendSAAM(from_call, group_name)
    self.changeFlashButtonState('btn_mainpanel_cqcqcq', False)

    saam.send('SAAM?')

    return


  def event_btnmyinfosave(self, values):
    self.debug.info_message("event_btnmyinfosave\n")

    if(values != None):
      self.form_dictionary.writeMainDictionaryToFile("saamcom_save_data.txt", values)
    """ write the inbox dictionary to file """
    self.form_dictionary.writeInboxDictToFile('inbox.msg')
    self.form_dictionary.writeOutboxDictToFile('outbox.msg')
    self.form_dictionary.writeSentDictToFile('sentbox.msg')
    self.form_dictionary.writeRelayboxDictToFile('relaybox.msg')
    self.form_dictionary.writePeerstnDictToFile('peerstn.sav')
    self.form_dictionary.writeRelaystnDictToFile('relaystn.sav')


  def event_btnmainpanelclearstations(self, values):
    self.debug.info_message("event_btnmainpanelclearstations\n")
    self.group_arq.clearSelectedStations()
    self.group_arq.clearSelectedRelayStations()

    self.form_dictionary.peerstn_file_dictionary_data = {}
    self.form_dictionary.relaystn_file_dictionary_data = {}

    self.form_gui.refreshSelectedTables()


  def event_tmpltcopytoclip(self, values):
    self.debug.info_message("TEMPLATE COPY TO CLIPBOARD\n")
    return

  def event_tmpltpastefromclip(self, values):
    self.debug.info_message("TEMPLATE PASTE FROM CLIPBOARD\n")

    clipboard_string = clip.paste()
    
    clipboard_string = clipboard_string.replace('JSDIGI_FORMS_CLIPBOARD_DATA={\'', '')
    clipboard_string = clipboard_string.replace('\'}', '')

    self.debug.info_message(" clipboard string: " + clipboard_string )
    
    sublist = clipboard_string.split('\',\'')
    for sublist_items in range(len(sublist)):
      self.debug.info_message(" substring : " + str(sublist[sublist_items]) )

    insert_where = values['combo_tmplt_insertwhere']

    self.debug.info_message("combo value = " + str(insert_where) + "---\n")

    linestr = values['table_templates_preview']
    self.debug.info_message("line str is:---" + str(linestr) + "---\n")

    if(insert_where == 'Before' or insert_where == 'After'):
      self.debug.info_message("processing before and after\n")
      line_index_form = int(values['table_templates_preview'][0])+1
      line_index = self.tablerow_templaterow_xref[line_index_form]-1

      self.debug.info_message("line index is" + str(line_index) )

      if(insert_where == 'Before'):
        for sublist_items in reversed(range(len(sublist))):
          self.debug.info_message(" substring : " + str(sublist[sublist_items]) )
          new_string = str(sublist[sublist_items])
          self.current_edit_string.insert(line_index+2, new_string)
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)

        self.form_gui.window['table_templates_preview'].update(select_rows=[len(sublist) + line_index_form-1])

        self.debug.info_message("insert before\n")
      elif(insert_where == 'After'):
        for sublist_items in reversed(range(len(sublist))):
          self.debug.info_message(" substring : " + str(sublist[sublist_items]) )
          new_string = str(sublist[sublist_items])
          self.current_edit_string.insert(line_index+3, new_string)
        self.debug.info_message("edit string: " + str(self.current_edit_string) )
        formname = values['in_tmpl_name']
        filename = values['in_tmpl_file']
        category = self.current_edit_category
        js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
        table_data = self.updateSimulatedPreview(self.current_edit_string)
        self.form_gui.window['table_templates_preview'].update(values=table_data)
        self.form_gui.window['in_tmpl_line_number'].update(str(line_index+2))

        self.form_gui.window['table_templates_preview'].update(select_rows=[len(sublist) + line_index_form])

        self.debug.info_message("inser after\n")

    if(insert_where == 'End'):
      self.debug.info_message("Insert at End\n")
      for sublist_items in reversed(range(len(sublist))):
        self.debug.info_message(" substring : " + str(sublist[sublist_items]) )
        new_string = str(sublist[sublist_items])
        self.current_edit_string.append(new_string)
      self.debug.info_message("edit string: " + str(self.current_edit_string) )
      formname = values['in_tmpl_name']
      filename = values['in_tmpl_file']
      category = self.current_edit_category
      js = self.form_dictionary.setDataInDictionary(formname, category, filename, self.current_edit_string)
      table_data = self.updateSimulatedPreview(self.current_edit_string)
      self.form_gui.window['table_templates_preview'].update(values=table_data)

    return


  def event_colorsupdate(self, values):
    self.debug.info_message("COLORS UPDATE\n")
    txbtn_color        = values['option_colors_tx_btns']
    msgmgmt_color      = values['option_colors_msgmgmt_btns']
    clipboard_color    = values['option_colors_clipboard_btns']
    compose_tab_color  = values['option_colors_compose_tab']
    inbox_tab_color    = values['option_colors_inbox_tab']
    outbox_tab_color   = values['option_colors_outbox_tab']
    relaybox_tab_color = values['option_colors_relay_tab']
    sentbox_tab_color  = values['option_colors_sentbox_tab']
    info_tab_color     = values['option_colors_info_tab']
    colors_tab_color   = values['option_colors_colors_tab']
    settings_tab_color = values['option_colors_settings_tab']

    try:
      wording_color = 'black'
      self.form_gui.window['btn_mainpanel_cqcqcq'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_mainpanel_copycopy'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_mainpanel_rr73'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_mainpanel_73'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_inbox_replytomsg'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_inbox_sendacknack'].update(button_color=(wording_color, txbtn_color))
      self.form_gui.window['btn_outbox_sendselected'].update(button_color=(wording_color, txbtn_color))

      self.form_gui.main_heading_background_clr     = values['option_main_heading_background_clr']
      self.form_gui.sub_heading_background_clr      = values['option_sub_heading_background_clr']
      self.form_gui.numbered_section_background_clr = values['option_numbered_section_background_clr']
      self.form_gui.table_header_background_clr     = values['option_table_header_background_clr']

      self.form_gui.main_heading_text_clr     = values['option_main_heading_text_clr']
      self.form_gui.sub_heading_text_clr      = values['option_sub_heading_text_clr']
      self.form_gui.numbered_section_text_clr = values['option_numbered_section_text_clr']
      self.form_gui.table_header_text_clr     = values['option_table_header_text_clr']

      self.debug.info_message("DONE COLORS UPDATE\n")
    except:
      self.debug.error_message("Exception in event_colorsupdate: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


  def event_btncomposeabortsend(self, values):
    self.debug.info_message("ABORT BUTTON PRESSED\n")

    self.group_arq.saamfram.sendAbort('','')

    return

  def event_composeselectedstations(self, values):
    self.debug.info_message("SELECT CALLSIGN\n")

    line_index = int(values['tbl_compose_selectedstations'][0])
    selected_callsigns = self.group_arq.toggleSelectedStations(line_index)
    selected_callsigns = self.group_arq.getConnectToString()

    self.form_gui.window['in_compose_selected_callsigns'].update(selected_callsigns)
    self.form_gui.window['in_inbox_listentostation'].update(selected_callsigns)

    self.debug.info_message("selected callsigns: " + selected_callsigns )

    self.form_gui.refreshSelectedTables()

  def event_composeselectedrelaystations(self, values):
    self.debug.info_message("SELECT RELAY CALLSIGN\n")

    line_index = int(values['tbl_compose_selectedrelaystations'][0])
    selected_callsigns = self.group_arq.toggleSelectedRelayStations(line_index)
    self.debug.info_message("selected callsigns: " + selected_callsigns )

    selected_callsigns = self.group_arq.getConnectToString()
    self.form_gui.window['in_inbox_listentostation'].update(selected_callsigns)

    table = self.group_arq.getSelectedRelayStations()
    self.form_gui.window['tbl_compose_selectedrelaystations'].update(values=table )
    self.form_gui.window['tbl_compose_selectedrelaystations'].update(row_colors=self.group_arq.getSelectedRelayStationsColors())

  def event_composestationcapabilities(self, values):
    self.debug.info_message("event_composestationcapabilities\n")

    callsign, channel_name = self.group_arq.saamfram.updateChannelView(values)

    self.form_gui.window['in_inbox_listentostation'].update(callsign )

    if('TX_' in channel_name):
      txchannel = channel_name
      self.form_gui.window['in_mainwindow_activetxchannel'].update(txchannel )
    else:
      rxchannel = channel_name
      self.form_gui.window['in_mainwindow_activerxchannel'].update(rxchannel )


  def event_btnrelaysendreqm(self, values):
    self.debug.info_message("event_btnrelaysendreqm\n")

    line_index = int(values['table_relay_messages'][0])
    selected_msgid = (self.group_arq.getMessageRelaybox()[line_index])[6]

    self.debug.info_message("selected msgid: " + str(selected_msgid) )

    from_call = self.saamfram.getMyCall()
    sender_call = self.saamfram.getSenderCall()
    self.saamfram.sendREQM(from_call, sender_call, selected_msgid)

  def event_btninboxsendreqm(self, values):
    self.debug.info_message("event_btninboxsendreqm\n")

    line_index = int(values['table_inbox_messages'][0])
    selected_msgid = (self.group_arq.getMessageInbox()[line_index])[7]

    self.debug.info_message("selected msgid: " + str(selected_msgid) )

    from_call = self.saamfram.getMyCall()
    sender_call = self.saamfram.getSenderCall()
    self.saamfram.sendREQM(from_call, sender_call, selected_msgid)

  def event_btnmainpanelrelay(self, values):
    self.debug.info_message("event_btnmainpanelrelay\n")

    try:
      self.form_gui.window['tab_relaybox'].select()
    except:
      self.debug.info_message("method: event_btnmainpanelrelay exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

  def event_btnmainareareset(self, values):
    self.debug.info_message("event_btnmainareareset\n")

    self.changeFlashButtonState('btn_mainpanel_cqcqcq', True)
    self.changeFlashButtonState('btn_mainpanel_copycopy', True)
    self.changeFlashButtonState('btn_mainpanel_rr73', True)
    self.changeFlashButtonState('btn_mainpanel_73', True)

    self.changeFlashButtonState('btn_outbox_sendselected', True)
    self.changeFlashButtonState('btn_relay_copytooutbox', True)
    self.changeFlashButtonState('btn_relay_sendreqm', True)
    self.changeFlashButtonState('btn_compose_areyoureadytoreceive', True)

    self.form_gui.form_events.changeFlashButtonState('btn_inbox_sendreqm', True)
    self.form_gui.form_events.changeFlashButtonState('btn_inbox_viewmsg', True)


    self.changeFlashButtonState('btn_mainpanel_cqcqcq', False)
    self.changeFlashButtonState('btn_mainpanel_copycopy', False)
    self.changeFlashButtonState('btn_mainpanel_rr73', False)
    self.changeFlashButtonState('btn_mainpanel_73', False)

    self.changeFlashButtonState('btn_outbox_sendselected', False)
    self.changeFlashButtonState('btn_relay_copytooutbox', False)
    self.changeFlashButtonState('btn_relay_sendreqm', False)
    self.changeFlashButtonState('btn_compose_areyoureadytoreceive', False)

    self.form_gui.form_events.changeFlashButtonState('btn_inbox_sendreqm', False)
    self.form_gui.form_events.changeFlashButtonState('btn_inbox_viewmsg', False)

    self.form_gui.refreshSelectedTables()

  
    selected_string = values['option_outbox_fldigimode']
    split_string = selected_string.split(' - ')
    mode = split_string[1]
    self.group_arq.fldigiclient.setMode(mode)

    channel = values['combo_settings_channels'].split(' - ')[1]
    self.group_arq.fldigiclient.setChannel(channel.split('Hz')[0])

    selected_callsigns = self.group_arq.getConnectToString()
    self.form_gui.window['in_inbox_listentostation'].update(selected_callsigns)


  def event_btnmainpanelupdaterecent(self, values):
    self.debug.info_message("event_btnmainpanelupdaterecent\n")

    how_recent = 1000
    selected_timescale = values['option_showactive']

    self.debug.info_message("selected option is: " + selected_timescale)

    if(selected_timescale == 'Minute'):
      how_recent = 60
    elif(selected_timescale == 'Hour'):
      how_recent = 3600
    elif(selected_timescale == 'Day'):
      how_recent = 86400
    elif(selected_timescale == 'Week'):
      how_recent = 604800
    elif(selected_timescale == 'Month'):
      how_recent = 18144000
    elif(selected_timescale == 'Year'):
      how_recent = 217728000
    elif(selected_timescale == 'Unlimited'): #This is 1000 years!
      how_recent = 217728000000

    self.form_dictionary.selectRecentFromPeerstnDicttionaryItems(how_recent)
    self.form_dictionary.selectRecentFromRelaystnDicttionaryItems(how_recent)
    self.form_gui.refreshSelectedTables()

    return

  def event_btnrelaycopytooutbox(self, values):
    self.debug.info_message("event_btnrelaycopytooutbox\n")

    try:
      self.form_gui.window['tab_outbox'].select()
    except:
      self.debug.info_message("method: event_btnrelaycopytooutbox exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

    line_index = int(values['table_relay_messages'][0])
    ID = (self.group_arq.getMessageRelaybox()[line_index])[6]
    self.debug.info_message("selected msgid: " + str(ID) )
    self.form_dictionary.transferRelayboxMsgToOutbox(ID)

    self.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )
    self.form_gui.window['table_outbox_messages'].update(row_colors=self.group_arq.getMessageOutboxColors())

    self.form_gui.window['table_relaybox_messages'].update(values=self.group_arq.getMessageRelaybox() )
    self.form_gui.window['table_relaybox_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

    self.debug.info_message("event_btnrelaycopytooutbox COMPLETE\n")


  def event_btncomposegoingqrtsaam(self, values):
    self.debug.info_message("event_btncomposegoingqrtsaam\n")
    self.saamfram.sendSaamQrt()

  def event_btncomposeconfirmedhavecopy(self, values):
    self.debug.info_message("event_btncomposeconfirmedhavecopy\n")
    self.saamfram.sendConf()

  def event_btncomposeareyoureadytoreceive(self, values):
    self.debug.info_message("event_btncomposeareyoureadytoreceive\n")
    self.saamfram.sendQryReady()

  def event_btncomposereadytoreceive(self, values):
    self.debug.info_message("event_btncomposereadytoreceive\n")
    self.saamfram.sendReadyToReceive()

  def event_btncomposenotreadytoreceive(self, values):
    self.debug.info_message("event_btncomposenotreadytoreceive\n")
    self.saamfram.sendNotReady()

  def event_btncomposecancelalreadyhavecopy(self, values):
    self.debug.info_message("event_btncomposecancelalreadyhavecopy\n")
    self.saamfram.sendCancelHaveCopy()



  def event_combosettingschannels(self, values):
    self.debug.info_message("event_combosettingschannels\n")
    channel = values['combo_settings_channels'].split(' - ')[1]
    self.debug.info_message("selected channel : " + channel )
    self.debug.info_message("selected channel : " + channel.split('Hz')[0] )

    if(self.saamfram.tx_mode == 'JS8CALL'):
      dial = 7095000
      offset = int(channel.split('Hz')[0])
      self.group_arq.setDialAndOffset(dial, offset)
      self.group_arq.setSpeed(cn.JS8CALL_SPEED_NORMAL)

    else:
      self.group_arq.fldigiclient.setChannel(channel.split('Hz')[0])


  def event_btnmainpanelpreviewimagefile(self, values):
    self.debug.info_message("event_btnmainpanelpreviewimagefile")

    jpg_filename = values['in_mainpanel_sendimagefilename'].strip()

    try:

      if(jpg_filename != ''):
        grayscale = values['cb_filexfer_grayscale']

        im = Image.open(jpg_filename)

        original_size_x, original_size_y = im.size

        slider_size_factor = values['filexfer_slider_size']
        slider_quality_factor = values['filexfer_slider_quality']
        self.debug.info_message("size factor : " + str(slider_size_factor))
        self.debug.info_message("quality factor : " + str(slider_quality_factor))

        resized_im = im.resize((int(original_size_x*(slider_size_factor)), int(original_size_y*(slider_size_factor))), Image.ANTIALIAS)
        if(grayscale):
          grayscale_im = resized_im.convert('L')     
          grayscale_im.save('compressed.jpg', optimize = True, quality=int(slider_quality_factor))
        else:
          resized_im.save('compressed.jpg', optimize = True, quality=int(slider_quality_factor))

        compressed_size = os.path.getsize('compressed.jpg')
        self.debug.info_message("compressed size is: " + str(compressed_size))

        self.form_gui.window['text_image_size'].update(str(compressed_size)+ ' Bytes')
        if(compressed_size<=3000):
          self.form_gui.window['text_image_size'].update(text_color='green1')
        elif(compressed_size<=5000):
          self.form_gui.window['text_image_size'].update(text_color='yellow')
        elif(compressed_size<=10000):
          self.form_gui.window['text_image_size'].update(text_color='orange')
        else:
          self.form_gui.window['text_image_size'].update(text_color='red')

        im = Image.open('compressed.jpg')
        im.save('preview.png')

        filename =  'preview.png'
        self.form_gui.window['filexfer_image'].update(filename)

    except:
      self.debug.info_message("method: event_btnmainpanelpreviewimagefile exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )


    return


  def event_combomainsignalwidth(self, values):
    self.debug.info_message("event_combomainsignalwidth\n")

    selected_width = values['combo_main_signalwidth']

    new_selection_list = self.group_arq.fldigiclient.getSelectionList(selected_width).split(',')

    self.form_gui.window['option_chat_fldigimode'].update(values=new_selection_list )
    self.form_gui.window['option_chat_fldigimode'].update(new_selection_list[0] )

    self.form_gui.window['option_filexfer_fldigimode'].update(values=new_selection_list )
    self.form_gui.window['option_filexfer_fldigimode'].update(new_selection_list[0] )

    self.form_gui.window['option_outbox_fldigimode'].update(values=new_selection_list )
    self.form_gui.window['option_outbox_fldigimode'].update(new_selection_list[0] )

    self.form_gui.window['option_winlink_fldigimode'].update(values=new_selection_list )
    self.form_gui.window['option_winlink_fldigimode'].update(new_selection_list[0] )

    self.form_gui.window['option_main_fldigimode'].update(values=new_selection_list )
    self.form_gui.window['option_main_fldigimode'].update(new_selection_list[0] )

    first_mode = new_selection_list[0].split(' - ')[1]
    self.group_arq.saamfram.fldigiclient.setMode(first_mode)
    self.group_arq.saamfram.fldigiclient.setModeSelectionList(new_selection_list)


  def event_btnoutboxviewform(self, values):
    self.debug.info_message("event_btnoutboxviewform")

    line_index = int(values['table_outbox_messages'][0])
    ID = (self.group_arq.getMessageOutbox()[line_index])[6]
    formname = (self.group_arq.getMessageOutbox()[line_index])[5]
    category, filename = self.form_dictionary.getCategoryAndFilenameFromFormname(formname)

    form_content = ['', '', '', '']

    self.debug.info_message("SELECTED CATEGORY IS: "  + category )
    self.debug.info_message("SELECTED FORMNAME IS: "  + formname )
    
    msgto = ''
    self.group_arq.saamfram.getDecodeTimestampFromUniqueId(ID)

    self.debug.info_message("reverse encoded callsign is: " + self.group_arq.saamfram.getDecodeCallsignFromUniqueId(ID) )
    self.debug.info_message("UNIQUE ID USING UUID IS: " + str(ID) )

    subject = ''

    self.form_gui.render_disabled_controls = True

    window = self.form_gui.createInboxViewReplyWindow(formname, form_content, category, msgto, filename, ID, subject, False, False, False)
    dispatcher = PopupControlsProc(self, window)

    self.form_gui.runPopup(self, dispatcher, window, False, True)


  def event_optionoutboxjs8callmode(self, values):
    self.debug.info_message("event_optionoutboxjs8callmode\n")

    speed = values['option_outbox_js8callmode']
    self.debug.info_message("selected speed : " + speed )

    if(self.saamfram.tx_mode == 'JS8CALL'):
      if(speed == 'SLOW'):
        self.group_arq.setSpeed(cn.JS8CALL_SPEED_SLOW)
      if(speed == 'NORMAL'):
        self.group_arq.setSpeed(cn.JS8CALL_SPEED_NORMAL)
      if(speed == 'FAST'):
        self.group_arq.setSpeed(cn.JS8CALL_SPEED_FAST)
      if(speed == 'TURBO'):
        self.group_arq.setSpeed(cn.JS8CALL_SPEED_TURBO)


  def editCell(self, window, table_key, row, col, values, istab):

    self.debug.info_message("editCell key: " + str(table_key))
    self.debug.info_message("editCell row: " + str(row))
    self.debug.info_message("editCell col: " + str(col))

    #multi_line_row = True
    multi_line_row = False

    def callback2(event, row, col, text, key):
        widget = event.widget
        if key == 'Button-1':

            table = window[table_key].get()
            metadata = window[table_key].metadata

            split_metadata = metadata.split(',')
            max_num_rows = int(split_metadata[1])
            max_num_cols = int(split_metadata[2])
            new_row = []
            for col_count in range(max_num_cols):
              new_row.append('')
            self.debug.info_message("editCell metadata: " + str(metadata))
            table.append(new_row)
            window[table_key].update(values=table)
            print(table)

    def callback(event, row, col, text, key):
        widget = event.widget

        if key == 'Return':
            self.editing_table = False
            text = widget.get()

            print(text)
            metadata = window[table_key].metadata
            self.debug.info_message("editCell metadata: " + str(metadata))

            button_widget = button
            button_widget.destroy()
            button_widget.master.destroy()
        elif key == 'Leave':
            sys.stdout.write("Leave called")

            if(self.editing_table ==True):
              sys.stdout.write("EDIT TRUE")
              entry.destroy()
              entry.master.destroy()
              button_widget = button
              button_widget.destroy()
              button_widget.master.destroy()
              self.editing_table = False
            return
        elif key == 'FocusOut':
            self.editing_table = False
            if(multi_line_row == False):
              text = widget.get()
            else:
              text = widget.get("1.0",sg.tk.END)

            button_widget = button
            button_widget.destroy()
            button_widget.master.destroy()
            self.editing_table = False
        elif key == 'Tab':
            self.editing_table = False
            text = widget.get()

            new_table = window[table_key].get()
            metadata = window[table_key].metadata
            split_metadata = metadata.split(',')
            max_num_rows = int(split_metadata[1])
            max_num_cols = int(split_metadata[2])

            if(col <= max_num_cols-2):
              self.editCell(window, table_key, row, col+1, values, True)
            else:
              if(row <= max_num_rows-1):
                self.editCell(window, table_key, row+1, 0, values, True)
              else:
                new_row = []
                for col_count in range(max_num_cols):
                  new_row.append('')
                self.debug.info_message("editCell metadata: " + str(metadata))
                new_table.append(new_row)
                window[table_key].update(values=new_table)
                self.editCell(window, table_key, row+1, 0, values, True)

            print(text)

            button_widget = button
            button_widget.destroy()
            button_widget.master.destroy()
            self.editing_table = True

        widget.destroy()
        widget.master.destroy()

        list_values = list(table.item(row, 'values'))
        list_values[col] = text
        table.item(row, values=list_values)

        self.debug.info_message("editCell row is: " + str(row))
        self.debug.info_message("editCell col is: " + str(col))
        psgtable = window[table_key].get()
        psgtable_row = psgtable[row-1]
        psgtable_row[col] = text
        window[table_key].update(values=psgtable)
        
    self.debug.info_message("istab: " + str(istab))
    self.debug.info_message("editing: " + str(self.editing_table))
    self.debug.info_message("row: " + str(row))

    #FIXME
    if (row <= 0):
      if (istab == False):
        return

    if (self.editing_table == True):
      entry = self.editing_table_entry
      text = entry.get()
      button = self.editing_table_button
      entry.destroy()
      entry.master.destroy()
      button_widget = button
      button_widget.destroy()
      button_widget.master.destroy()
      self.editing_table = False


      table = window[self.editing_table_key].Widget
      #table = window[table_key].get()
      list_values = list(table.item(self.editing_table_row, 'values'))
      list_values[self.editing_table_col] = text
      table.item(self.editing_table_row, values=list_values)

      self.debug.info_message("editCell row is: " + str(self.editing_table_row))
      self.debug.info_message("editCell col is: " + str(self.editing_table_col))
      psgtable = window[self.editing_table_key].get()
      psgtable_row = psgtable[self.editing_table_row-1]
      psgtable_row[self.editing_table_col] = text
      window[self.editing_table_key].update(values=psgtable)

    #  if (istab == False):
    #    return


    self.editing_table = True
    self.editing_table_row = row   
    self.editing_table_col = col

    root = window.TKroot
    table = window[table_key].Widget

    table3 = window['sgcol'].Widget
    widget_x3, widget_y3 = table3.winfo_rootx(),table3.winfo_rooty()
    self.debug.info_message("editCell widget x3: " + str(widget_x3))
    self.debug.info_message("editCell widget y3: " + str(widget_y3))

    widget_x1, widget_y1 = table.winfo_rootx(),table.winfo_rooty()
    self.debug.info_message("editCell widget x1: " + str(widget_x1))
    self.debug.info_message("editCell widget y1: " + str(widget_y1))

    table2 = window['popup_main_tab1'].Widget  
    widget_x2, widget_y2 = table2.winfo_rootx(),table2.winfo_rooty()
    self.debug.info_message("editCell widget x2: " + str(widget_x2))
    self.debug.info_message("editCell widget y2: " + str(widget_y2))

    self.editing_scrolly_pos = widget_y2
    self.editing_table_key = table_key 

    self.debug.info_message("editCell widget y1-y2: " + str(widget_y1 - widget_y2))
    self.debug.info_message("editCell widget x1-x2: " + str(widget_x1 - widget_x2))
    offset_y = (widget_y2 - widget_y3) + (widget_y1 - widget_y2) + 4 + 35
    offset_x = (widget_x2 - widget_x3) + (widget_x1 - widget_x2) + 5

    text = table.item(row, "values")[col]
    x, y, width, height = table.bbox(row, col)

    self.debug.info_message("editCell x: " + str(x))
    self.debug.info_message("editCell y: " + str(y))
    self.debug.info_message("text is: " + str(text))

    frame = sg.tk.Frame(root)

    if(multi_line_row == False):
      frame.place(x=x+offset_x, y=y+offset_y, anchor="nw", width=width, height=height)
    else:
      frame.place(x=x+offset_x, y=y+offset_y, anchor="nw", width=width, height=height*3)

    textvariable = sg.tk.StringVar()
    textvariable.set(text)
    metadata = window[table_key].metadata
    self.debug.info_message("editCell metadata: " + str(metadata))
    column_types = metadata.split(',')
    this_column = column_types[col+3]
    self.debug.info_message("editCell this column type: " + str(this_column))

    if('Text' in this_column):
      if(multi_line_row == False):
        entry = sg.tk.Entry(frame, textvariable=textvariable, justify='left')
      else:
        entry = sg.tk.Text(frame, width=20, height=3)

      entry.pack()

      if(multi_line_row == False):
        entry.select_range(0, sg.tk.END)
        entry.icursor(sg.tk.END)
    elif('Combo(' in this_column):
      split_string = this_column.split('Combo(')
      split_string2 = split_string[1].split(')')
      list_values = split_string2[0].split(':')

      entry = sg.ttk.Combobox(frame, values=list_values)
      for item_count in range(len(list_values)):
        if(list_values[item_count] == text):
          entry.current(item_count)
      entry.pack()

    """
    #use this for checkbox?????????...
    entry = sg.tk.Checkbutton(frame)
    entry.pack()
    """

    frame2 = sg.tk.Frame(root)
    frame2.place(x=x+offset_x, y=y+offset_y-16, anchor="nw", width=width, height=height)
    button = sg.tk.Button(frame2, text='++ Add Rows ++')
    button.pack()
    button.bind("<Button-1>", lambda e, r=row, c=col, t=text, k='Button-1':callback2(e, r, c, t, k))

    entry.focus_force()
    entry.bind("<Return>", lambda e, r=row, c=col, t=text, k='Return':callback(e, r, c, t, k))
    entry.bind("<Escape>", lambda e, r=row, c=col, t=text, k='Escape':callback(e, r, c, t, k))
    entry.bind("<Tab>", lambda e, r=row, c=col, t=text, k='Tab':callback(e, r, c, t, k))

    """ experimental code
    entry.bind("<FocusOut>", lambda e, r=row, c=col, t=text, k='FocusOut':callback(e, r, c, t, k))
    entry.bind("<Leave>", lambda e, r=row, c=col, t=text, k='Leave':callback(e, r, c, t, k))
    frame.bind("<Leave>", lambda e, r=row, c=col, t=text, k='Leave':callback(e, r, c, t, k))
    window['sgcol'].Widget.bind("<Button-1>", lambda e, r=row, c=col, t=text, k='Leave':callback(e, r, c, t, k))
    """

    self.editing_table_entry = entry
    self.editing_table_button = button


  def cancelEdit(self):
    entry = self.editing_table_entry
    button = self.editing_table_button
    entry.destroy()
    entry.master.destroy()
    button_widget = button
    button_widget.destroy()
    button_widget.master.destroy()
    self.editing_table = False
    return

  def hasWindowMovedDuringEdit(self, window):
    #self.debug.info_message("hasWindowMovedDuringEdit")
    if(self.editing_table == True):
      table = window['popup_main_tab1'].Widget  
      widget_x1, widget_y1 = table.winfo_rootx(),table.winfo_rooty()
      self.debug.info_message("widget y1: " + str(widget_y1))

      if(self.editing_scrolly_pos != widget_y1):
        self.debug.info_message("Window has moved while editing")
        return True

    return False


  def fixup_table_headers(self, window, table_key, values):

    for table_count in range(len(self.form_gui.customized_headers)):
      header_string = self.form_gui.customized_headers[table_count]

      self.debug.info_message("fixup_table_headers. header_string: " + str(header_string))

      custom_headers = header_string
      table_key     = custom_headers[0]
      numheadercols = int(custom_headers[1])
      numheaderrows = int(custom_headers[2])
      table = window[table_key].Widget
      if(numheaderrows == 2):
        table.heading('#0', text='\n')
      elif(numheaderrows == 3):
        table.heading('#0', text='\n\n')
      elif(numheaderrows == 4):
        table.heading('#0', text='\n\n\n')
      for x in range(numheadercols):
        table.heading(x, text=custom_headers[x+3])

    """ this is the magic code that resizes the column heading"""
    style = sg.ttk.Style()
    style.configure('Treeview.Heading', foreground='black')

    return

  def processFileData(self, folder, filename):
    tabledata = []
    has_xml = False
    xml_data = []
    xml_string_data = ''
    message_id = ''
    date = ''
    msg_from = ''
    msg_to = ''
    subject = ''
    formname = ''
    with open(folder + filename) as f:
      data = f.read()
      string_data = str(data)
      self.debug.info_message("data: " + string_data)
      data = string_data.split('\n')
      for x in range(len(data)):
        data_item = [str(data[x])]
        tabledata.append(data_item)

        if('Mid: ' in data_item[0]):
          message_id = data_item[0].split('Mid: ')[1]
        elif('Date: ' in data_item[0]):
          date = data_item[0].split('Date: ')[1]
        elif('From: ' in data_item[0]):
          msg_from = data_item[0].split('From: ')[1]
        elif('Subject: ' in data_item[0]):
          subject = data_item[0].split('Subject: ')[1]
        elif('To: ' in data_item[0]):
          msg_to = data_item[0].split('To: ')[1]

        if(has_xml == False and '<?xml version=' in data_item[0]):
          has_xml = True
          xml_data.append('<?xml version=' + data_item[0].split('<?xml version=')[1])
          xml_string_data = xml_string_data + '<?xml version=' + data_item[0].split('<?xml version=')[1] + '\n'
        elif(has_xml == True):
          xml_data.append(data_item)
          xml_string_data = xml_string_data + data_item[0] + '\n'

      if(has_xml == True):
        formname, sender = self.winlink_import.parseBasicXmlInfo(xml_string_data)
        self.debug.info_message("event_winlinklist formname: " + formname )
        self.debug.info_message("event_winlinklist sender: " + sender )

      self.debug.info_message("event_winlinklist. message_id: " + message_id)
      self.debug.info_message("event_winlinklist. date: " + date)
      self.debug.info_message("event_winlinklist. msg_from: " + msg_from)
      self.debug.info_message("event_winlinklist. subject: " + subject)
      self.debug.info_message("event_winlinklist. msg_to: " + msg_to)

      return filename, msg_from, msg_to, subject, date, formname, message_id


  def event_winlinklist(self, values):
    self.debug.info_message("event_winlinklist")

    folder = values['in_winlink_inboxfolder']

    extension = "*.b2f"
    if (platform.system() == 'Windows'):
      extension = "*.mime"
      self.debug.info_message("Windows Platform")
    else:
      extension = "*.b2f"
      self.debug.info_message("Non-Windows Platform")

    """ Test code only
    extension = "*.mime"
    """

    if(folder != ''):
      extension = "*.b2f"
      self.group_arq.clearWinlinkInboxFiles()
      dir_list = glob.glob(folder + extension)
      dir_list.sort(key=os.path.getmtime)
      for full_filename in reversed(dir_list):
        filename = full_filename.split(folder)[1]
        self.debug.info_message("pat winlink email located: " + str(filename) )
        filename, msg_from, msg_to, subject, date, formname, message_id = self.processFileData(folder, filename)
        self.group_arq.addWinlinkInboxFile(filename, msg_from, msg_to, subject, date, formname, message_id)
      self.form_gui.window['winlink_inbox_table'].update(values=self.group_arq.getWinlinkInboxFiles())

    folder = values['in_winlink_outboxfolder']

    if(folder != ''):
      extension = "*.b2f"
      self.group_arq.clearWinlinkOutboxFiles()
      dir_list = glob.glob(folder + extension)
      dir_list.sort(key=os.path.getmtime)
      for full_filename in reversed(dir_list):
        filename = full_filename.split(folder)[1]
        self.debug.info_message("event_winlinklist. filename: " + filename )
        self.debug.info_message("pat winlink email located: " + str(filename) )
        filename, msg_from, msg_to, subject, date, formname, message_id = self.processFileData(folder, filename)
        self.group_arq.addWinlinkOutboxFile(filename, msg_from, msg_to, subject, date, formname, message_id)
      self.form_gui.window['winlink_outbox_table'].update(values=self.group_arq.getWinlinkOutboxFiles())

    folder = values['in_winlink_rmsmsgfolder']

    if(folder != ''):
      extension = "*.mime"
      self.group_arq.clearWinlinkRMSMsgFiles()
      dir_list = glob.glob(folder + extension)
      dir_list.sort(key=os.path.getmtime)
      for full_filename in reversed(dir_list):
        filename = full_filename.split(folder)[1]
        self.debug.info_message("event_winlinklist. filename: " + filename )
        self.debug.info_message("pat winlink email located: " + str(filename) )
        filename, msg_from, msg_to, subject, date, formname, message_id = self.processFileData(folder, filename)
        self.group_arq.addWinlinkRMSMsgFile(filename, msg_from, msg_to, subject, date, formname, message_id)
      self.form_gui.window['winlink_rmsmsg_table'].update(values=self.group_arq.getWinlinkRMSMsgFiles())

    return

  def event_winlinkinboxtable(self, values):
    self.debug.info_message("event_winlinkinboxtable")

    line_index = int(values['winlink_inbox_table'][0])
    filename = (self.group_arq.getWinlinkInboxFiles()[line_index])[0]

    formname = (self.group_arq.getWinlinkInboxFiles()[line_index])[5]
    if(formname == ""):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    elif(formname == 'ICS 213'):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    else:
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = True)


    folder = values['in_winlink_inboxfolder']

    self.debug.info_message("selected id: " + str(filename))

    tabledata = []

    body_length = 5000

    with open(folder+filename) as f:
      data = f.read()
      string_data = str(data)
      self.debug.info_message("data read in")
      data = string_data.split('\n')
      running_count = 0
      self.debug.info_message("event_winlinkinboxtable. datalen: " + str(len(data)))
      for x in range(len(data)):
        running_count = running_count + int(len(data[x]))
        if('Body: ' in data[x]):
          body_length = int(data[x].split('Body: ')[1])
          self.debug.info_message("body length: " + str(body_length))
          running_count = 0
        elif('X-Filepath: ' in data[x]):
          running_count = 0

        self.debug.info_message("event_winlinkinboxtable. running count: " + str(running_count))
        if(running_count <= body_length):
          tabledata.append([str(data[x])])
          self.debug.info_message("appending: " + str(data[x]))

    self.form_gui.window['table_winlink_inbox_preview'].update(values=tabledata)
    
    self.form_gui.window['winlink_outbox_table'].update(values=self.group_arq.getWinlinkOutboxFiles())
    self.form_gui.window['winlink_rmsmsg_table'].update(values=self.group_arq.getWinlinkRMSMsgFiles())

    return

  def event_winlinkoutboxtable(self, values):
    self.debug.info_message("event_winlinkoutboxtable")

    line_index = int(values['winlink_outbox_table'][0])
    filename = (self.group_arq.getWinlinkOutboxFiles()[line_index])[0]

    formname = (self.group_arq.getWinlinkOutboxFiles()[line_index])[5]
    if(formname == ""):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    elif(formname == 'ICS 213'):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    else:
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = True)

    folder = values['in_winlink_outboxfolder']

    tabledata = []

    body_length = 5000

    with open(folder+filename) as f:
      data = f.read()
      string_data = str(data)
      data = string_data.split('\n')
      running_count = 0
      for x in range(len(data)):
        running_count = running_count + int(len(data[x]))
        if('Body: ' in data[x]):
          body_length = int(data[x].split('Body: ')[1])
          self.debug.info_message("body length: " + str(body_length))
          running_count = 0
        elif('X-Filepath: ' in data[x]):
          running_count = 0
        elif('X-P2ponly: ' in data[x]):
          running_count = 0
        elif('Type: ' in data[x]):
          running_count = 0

        if(running_count <= body_length):
          data_item = [str(data[x])]
          tabledata.append(data_item)

    self.form_gui.window['table_winlink_inbox_preview'].update(values=tabledata)

    self.form_gui.window['winlink_inbox_table'].update(values=self.group_arq.getWinlinkInboxFiles())
    self.form_gui.window['winlink_rmsmsg_table'].update(values=self.group_arq.getWinlinkRMSMsgFiles())

    return



  def event_winlinkrmsmsgtable(self, values):
    self.debug.info_message("event_winlinkrmsmsgtable")

    line_index = int(values['winlink_rmsmsg_table'][0])
    filename = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[0]

    formname = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[5]
    if(formname == ""):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    elif(formname == 'ICS 213'):
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = False)
    else:
      self.form_gui.window['btn_winlink_edit_selected'].update(disabled = True)

    folder = values['in_winlink_rmsmsgfolder']

    tabledata = []

    body_length = 5000

    with open(folder+filename) as f:
      data = f.read()
      string_data = str(data)
      data = string_data.split('\n')
      running_count = 0
      for x in range(len(data)):
        running_count = running_count + int(len(data[x]))
        if('Body: ' in data[x]):
          body_length = int(data[x].split('Body: ')[1])
          self.debug.info_message("body length: " + str(body_length))
          running_count = 0
        elif('X-Filepath: ' in data[x]):
          running_count = 0
        elif('X-P2ponly: ' in data[x]):
          running_count = 0
        elif('Type: ' in data[x]):
          running_count = 0

        if(running_count <= body_length):
          data_item = [str(data[x])]
          tabledata.append(data_item)

    self.form_gui.window['table_winlink_inbox_preview'].update(values=tabledata)

    self.form_gui.window['winlink_inbox_table'].update(values=self.group_arq.getWinlinkInboxFiles())
    self.form_gui.window['winlink_outbox_table'].update(values=self.group_arq.getWinlinkOutboxFiles())

    return


  def event_btnwinlinksendselected(self, values):

    self.debug.info_message("event_btnwinlinksendselected")

    selected_mode = values['option_winlink_fldigimode'].split(' - ')[1]
    self.group_arq.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected file winlink mode is: " + selected_mode)

    if(values['winlink_outbox_table'] != []):
      line_index = int(values['winlink_outbox_table'][0])
      filename = (self.group_arq.getWinlinkOutboxFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkOutboxFiles()[line_index])[5]
      folder = values['in_winlink_outboxfolder']
    elif(values['winlink_inbox_table'] != []):
      line_index = int(values['winlink_inbox_table'][0])
      filename = (self.group_arq.getWinlinkInboxFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkInboxFiles()[line_index])[5]
      folder = values['in_winlink_inboxfolder']
    elif(values['winlink_rmsmsg_table'] != []):
      line_index = int(values['winlink_rmsmsg_table'][0])
      filename = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[5]
      folder = values['in_winlink_rmsmsgfolder']


    self.debug.info_message("selected id: " + str(filename))


    self.debug.info_message("full filename is: " + str(folder + filename))

    full_filename = str(folder + filename)

###################
    sender_callsign = self.group_arq.saamfram.getMyCall()
    msgid = self.group_arq.saamfram.getEncodeUniqueId(sender_callsign)
    formname = filename
    priority = ''
    subject  = ''
    tolist   = self.form_gui.window['in_inbox_listentostation'].get()

    frag_size = 200
    tagfile = 'ICS'
    version  = '1.0'

    complete_send_string = ''

    filename =  full_filename

    content = self.saamfram.getBinaryFile(filename)
    
    self.debug.info_message("OK got the data: " + str(content) )

    complete_send_string = self.group_arq.saamfram.getWL2KSendString(msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)

    self.debug.info_message("EVENT SEND FILE 3\n")
    fragtagmsg = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)

    self.debug.info_message("SEND STRING IS: " + fragtagmsg )
    self.debug.info_message("ACTUAL MSG SENT TO FLDIGI: " + str(fragtagmsg) )
    
    self.group_arq.sendFormRig1(fragtagmsg, tolist, msgid)


    return

  def event_btnwinlinkeditselected(self, values):

    self.debug.info_message("event_btnwinlinkeditselected")

    self.debug.info_message("event_btnwinlinkeditselected. line index: " + str(values['winlink_outbox_table']))

    if(values['winlink_outbox_table'] != []):
      line_index = int(values['winlink_outbox_table'][0])
      filename = (self.group_arq.getWinlinkOutboxFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkOutboxFiles()[line_index])[5]
      folder = values['in_winlink_outboxfolder']
    elif(values['winlink_inbox_table'] != []):
      line_index = int(values['winlink_inbox_table'][0])
      filename = (self.group_arq.getWinlinkInboxFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkInboxFiles()[line_index])[5]
      folder = values['in_winlink_inboxfolder']
    elif(values['winlink_rmsmsg_table'] != []):
      line_index = int(values['winlink_rmsmsg_table'][0])
      filename = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[0]
      formname = (self.group_arq.getWinlinkRMSMsgFiles()[line_index])[5]
      folder = values['in_winlink_rmsmsgfolder']


    self.debug.info_message("selected id: " + str(filename))

    tabledata = []

    has_xml = False
    xml_data = []
    xml_string_data = ''
    main_string_data = ''

    body_length = 5000

    with open(folder+filename) as f:
      data = f.read()
      string_data = str(data)
      self.debug.info_message("data read in")
      data = string_data.split('\n')
      running_count = 0
      for x in range(len(data)):
        running_count = running_count + int(len(data[x]))

        if('Body: ' in data[x]):
          body_length = int(data[x].split('Body: ')[1])
          self.debug.info_message("body length: " + str(body_length))
          running_count = 0
        elif('X-Filepath: ' in data[x]):
          running_count = 0
        elif('X-P2ponly: ' in data[x]):
          running_count = 0
        elif('Type: ' in data[x]):
          running_count = 0
        elif('Content-Transfer-Encoding: ' in data[x]):
          running_count = 0

        if(running_count <= body_length or formname != ''):
          data_item = [str(data[x])]
          tabledata.append(data_item)

        self.debug.info_message("DATA ITEM IS: " + str(data_item))
        if(has_xml == False and '<?xml version=' in data_item[0]):
          self.debug.info_message("HAS XML = TRUE")
          has_xml = True
          xml_data.append('<?xml version=' + data_item[0].split('<?xml version=')[1])
          xml_string_data = xml_string_data + '<?xml version=' + data_item[0].split('<?xml version=')[1] + '\n'
        elif(has_xml == True):
          self.debug.info_message("HAS XML = TRUE2")
          xml_data.append(data_item)
          xml_string_data = xml_string_data + data_item[0] + '\n'
        else:
          main_string_data = main_string_data + data_item[0] + '\n'

    self.form_gui.window['table_winlink_inbox_preview'].update(values=tabledata)

    self.debug.info_message("event_winlinkoutboxtable LOC3")
    self.debug.info_message("event_winlinkoutboxtable XML is: " + str(xml_data))

    if( has_xml == True):
      formname, form_content, msgto, subject = self.winlink_import.parseWinlinkXml(xml_string_data)
      category, filename = self.form_dictionary.getCategoryAndFilenameFromFormname(formname)

      """ create a new ID as this message is being edited."""
      ID = self.saamfram.getEncodeUniqueId(self.saamfram.getMyCall())

      self.form_gui.render_disabled_controls = False

      window = self.form_gui.createDynamicPopupWindow(formname, form_content, category, msgto, filename, ID, subject, False)
      dispatcher = PopupControlsProc(self, window)
      self.form_gui.runPopup(self, dispatcher, window, False, False)
    else:
      self.debug.info_message("event_winlinkoutboxtable. main data: " + main_string_data)

      if('X-Filepath: ' in main_string_data):
        message_content = main_string_data.split('X-Filepath: ')[1]
      elif('X-P2ponly: ' in main_string_data):
        message_content = main_string_data.split('X-P2ponly: ')[1]
      elif('Content-Transfer-Encoding: ' in main_string_data):
        message_content = main_string_data.split('Content-Transfer-Encoding: ')[1]

      message_content = message_content.split('\n', 1)[1]

      if('--boundary' in message_content):
        message_content = message_content.split('--boundary')[0]

      self.debug.info_message("event_winlinkoutboxtable. message content: " + message_content)

      form_content = [message_content]
      category, filename = self.form_dictionary.getCategoryAndFilenameFromFormname('EMAIL')
      ID = self.saamfram.getEncodeUniqueId(self.saamfram.getMyCall())
      msgto = ''
      subject = ''

      self.form_gui.render_disabled_controls = False

      window = self.form_gui.createDynamicPopupWindow('EMAIL', form_content, category, msgto, filename, ID, subject, False)
      dispatcher = PopupControlsProc(self, window)
      self.form_gui.runPopup(self, dispatcher, window, False, False)

    self.debug.info_message("event_winlinkoutboxtable LOC10")

    return


  def event_btnmainareavisitgithub(self, values):
    self.debug.info_message("event_btnmainareavisitgithub")

    url = "https://github.com/gh42lb"
    webbrowser.open(url)


  def event_btnsubstationconnect1(self, values):
    self.debug.info_message("event_btnsubstationconnect1")

    name        = values['in_substation_name_1'].strip()
    ip_address  = values['in_substation_ipaddress_1'].strip()
    port        = values['in_substation_port_1'].strip()

    self.debug.info_message("name = " + name + ", ip_address = " + ip_address + ", port = " + port)

    self.form_gui.window['btn_substation_connect_1'].update(disabled = True)
    self.form_gui.window['btn_substation_disconnect_1'].update(disabled = False)

    try:
      pipe = self.group_arq.pipes.createClientPipe(name, ip_address, port )
      self.group_arq.pipes.connectClient(pipe)

      speed = 50
      #client = self.group_arq.pipes.getClient()
      client = self.group_arq.pipes.getPipe(name, ip_address, port )
      client.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )

      self.debug.info_message("event_btnsubstationconnect1 LOC4")
      sys.stdout.write("sending message from HRRM Client to external module server\n")

    except:
      self.debug.info_message("Exception in event_btnsubstationconnect1: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))



  def event_btnsubstationdisconnect1(self, values):
    self.debug.info_message("event_btnsubstationdisconnect1")

    self.form_gui.window['btn_substation_connect_1'].update(disabled = False)
    self.form_gui.window['btn_substation_disconnect_1'].update(disabled = True)

    name        = values['in_substation_name_1'].strip()
    ip_address  = values['in_substation_ipaddress_1'].strip()
    port        = values['in_substation_port_1'].strip()

    client = self.group_arq.pipes.getPipe(name, ip_address, port )
    client.stopThreads()
    self.group_arq.pipes.removePipe(name, ip_address, port )


  def event_comboelement1(self, values):
    self.debug.info_message("COMBO ELEMENT 1\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('1')

  def event_comboelement2(self, values):
    self.debug.info_message("COMBO ELEMENT 2\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('2')
    
  def event_comboelement3(self, values):
    self.debug.info_message("COMBO ELEMENT 3\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('3')

  def event_comboelement4(self, values):
    self.debug.info_message("COMBO ELEMENT 4\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('4')

  def event_comboelement5(self, values):
    self.debug.info_message("COMBO ELEMENT 5\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('5')

  def event_comboelement6(self, values):
    self.debug.info_message("COMBO ELEMENT 6\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('6')

  def event_comboelement7(self, values):
    self.debug.info_message("COMBO ELEMENT 7\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('7')

  def event_comboelement8(self, values):
    self.debug.info_message("COMBO ELEMENT 8\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('8')

  def event_comboelement9(self, values):
    self.debug.info_message("COMBO ELEMENT 9\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('9')

  def event_comboelement10(self, values):
    self.debug.info_message("COMBO ELEMENT 10\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('10')

  def event_comboelement11(self, values):
    self.debug.info_message("COMBO ELEMENT 11\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('11')

  def event_comboelement12(self, values):
    self.debug.info_message("COMBO ELEMENT 12\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('12')

  def event_comboelement13(self, values):
    self.debug.info_message("COMBO ELEMENT 13\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('13')

  def event_comboelement14(self, values):
    self.debug.info_message("COMBO ELEMENT 14\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('14')

  def event_comboelement15(self, values):
    self.debug.info_message("COMBO ELEMENT 15\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('15')

  def event_comboelement16(self, values):
    self.debug.info_message("COMBO ELEMENT 16\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('16')

  def event_comboelement17(self, values):
    self.debug.info_message("COMBO ELEMENT 17\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('17')

  def event_comboelement18(self, values):
    self.debug.info_message("COMBO ELEMENT 18\n")
    self.form_gui.window['in_tmpl_insertelementnumber'].update('18')


  def event_exit_receive(self, values):

    try:
      self.debug.info_message("WRITING DICTIONARIES TO FILE\n")
      """ write the main dictionary of values to file """
      if(values != None):
        self.form_dictionary.writeMainDictionaryToFile("saamcom_save_data.txt", values)
      """ write the inbox dictionary to file """
      self.form_dictionary.writeInboxDictToFile('inbox.msg')

      self.form_dictionary.writeOutboxDictToFile('outbox.msg')
      self.form_dictionary.writeSentDictToFile('sentbox.msg')
      self.form_dictionary.writeRelayboxDictToFile('relaybox.msg')

      self.form_dictionary.writePeerstnDictToFile('peerstn.sav')
      self.form_dictionary.writeRelaystnDictToFile('relaystn.sav')
   
      self.debug.info_message("COMPLETED WRITING DICTIONARIES TO FILE\n")

      self.debug.info_message("waiting for threads to exit...")

      if(self.group_arq.js8client != None):
        self.group_arq.js8client.stopThreads()
      if(self.group_arq.fldigiclient != None):
        self.group_arq.pipes.appClose()
        self.group_arq.fldigiclient.stopThreads()



    except:
      self.debug.error_message("Exception in event_exit_receive: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      
    return()


  dispatch = {
      'btn_tmplt_preview_form'    : event_btntmpltpreviewform,
      'tbl_tmplt_templates'       : event_tmplt_template,
      'btn_tmplt_new_template'    : event_tmplt_newtemplate,
      'btn_tmplt_update_template' : event_tmplt_updatetemplate,
      'btn_tmplt_delete_template' : event_tmplt_deletetemplate,
      'btn_tmplt_save_template'   : event_tmplt_savetemplate,
      'btn_tmplt_load_sel'        : event_tmplt_loadsel,
      'btn_settings_add'          : event_settings_add,
      'btn_settings_tmplt_remove'          : event_settings_tmplt_remove,
      'tbl_tmplt_categories'      : event_tmplt_categories,
      'table_templates_preview'   : event_tablepreview,
      'btn_tmplt_update'          : event_tmpltupdate,
      'btn_tmplt_add_row'         : event_tmplt_addrow,
      'in_tmpl_category_name'     : event_tmplt_typingsomething,
      'in_tmpl_name'              : event_tmplt_typingsomething,
      'in_tmpl_desc'              : event_tmplt_typingsomething,
      'in_tmpl_ver'               : event_tmplt_typingsomething,
      'in_tmpl_file'              : event_tmplt_typingsomething,
      'btn_cmpse_compose'         : event_composemsg,
      'btn_prev_post_to_outbox'   : event_prevposttooutbox,
      'btn_prev_chat_post_and_send'  : event_prevchatpostandsend,
      'table_outbox_messages'     : event_tableoutboxmessages,
      'table_inbox_messages'      : event_tableinboxmessages,
      'table_relay_messages'   : event_tablerelayboxmessages,
      'btn_outbox_editform'       : event_outboxeditform,
      'btn_settings_list'         : event_settingslist,
      'tbl_compose_categories'    : event_compose_categories,
      'btn_outbox_sendselected'   : event_outboxsendselected,
      'btn_outbox_sendselectedasfile'   : event_outboxsendselectedasfile,
      'btn_outbox_deletemsg'      : event_outboxdeletemsg,
      'btn_outbox_deleteallmsg'   : event_outboxdeleteallmsg,
      'btn_sentbox_deletemsg'      : event_sentboxdeletemsg,
      'btn_sentbox_deleteallmsg'   : event_sentboxdeleteallmsg,
      'btn_outbox_sendall'        : event_outboxsendall,
      'btn_inbox_deleteselected'  : event_inboxdeleteselected,
      'btn_inbox_deleteall'       : event_inboxdeleteall,
      'btn_relaybox_deleteselected'  : event_relayboxdeleteselected,
      'btn_relaybox_deleteall'       : event_relayboxdeleteall,
      'table_sent_messages'       : event_tablesentmessages,
      'btn_outbox_reqconfirm'     : event_outboxreqconfirm,
      'btn_inbox_rcvstatus'       : event_inboxrcvstatus,
      'cb_templates_editline'         : event_templateseditline,
      'cb_templates_insertdeleteline' : event_templatesinsertdeleteline,
      'btn_tmplt_delete_template_category' : event_tmpltdeletetemplatecategory,
      'tbl_compose_select_form'   : event_composeselectform,
      'option_outbox_fldigimode'  : event_outboxfldigimode,
      'btn_inbox_sendacknack'     : event_inboxsendacknack,
      'btn_outbox_pleaseconfirm'  : event_outboxpleaseconfirm,
      'btn_inbox_copyclipboard'   : event_inboxcopyclipboard,
      'btn_outbox_copytoclipboard'   : event_outboxcopyclipboard,
      'btn_outbox_importfromclipboard' :  event_outboximportfromclipboard,
      'btn_inbox_replytomsg'      : event_inboxreplytomsg,
      'btn_inbox_viewmsg'         : event_inboxviewmsg,
      'btn_tmplt_insertelement'   : event_fordesignerInsertElement,
      'btn_tmplt_deleteelement'   : event_fordesignerDeleteElement,
      'btn_tmplt_delete_row'      : event_tmpltdeleterow,
      'btn_tmplt_new_category'    : event_tmpltnewcategory,
      'btn_tmplt_duplicate_row'   : event_tmpltduplicaterow,
      'btn_tmplt_copytoclip'      : event_tmpltcopytoclip,
      'btn_tmplt_pastefromclip'   : event_tmpltpastefromclip,
      'option_outbox_txrig'       : event_outboxtxrig,
      #'btn_compose_qrysaam'       : event_compose_qrysaam,
      'btn_mainpanel_cqcqcq'      : event_compose_cqcqcq,
      'btn_mainpanel_copycopy'    : event_compose_copycopy,
      'btn_mainpanel_rr73'        : event_compose_rr73,
      'btn_mainpanel_73'          : event_compose_73,
      'btn_compose_checkin'       : event_compose_checkin,
      'btn_compose_standby'       : event_compose_standby,
      'btn_compose_qrt'           : event_compose_qrt,
      'btn_compose_saam'          : event_compose_saam,
      'btn_colors_update'         : event_colorsupdate,
      'tbl_compose_selectedstations' : event_composeselectedstations,
      'tbl_compose_selectedrelaystations' : event_composeselectedrelaystations,
      'tbl_compose_stationcapabilities' : event_composestationcapabilities,
      'btn_compose_abortsend'     : event_btncomposeabortsend,
      'btn_relay_sendreqm'        : event_btnrelaysendreqm,
      'btn_inbox_sendreqm'        : event_btninboxsendreqm,
      'combo_settings_channels'   : event_combosettingschannels,
      'option_outbox_js8callmode' : event_optionoutboxjs8callmode,
      'combo_main_signalwidth'    : event_combomainsignalwidth,

      'btn_mainpanel_previewimagefile' : event_btnmainpanelpreviewimagefile,
      'filexfer_slider_size'          :     event_btnmainpanelpreviewimagefile,
      'filexfer_slider_quality'       :     event_btnmainpanelpreviewimagefile,
      'cb_filexfer_grayscale'         :     event_btnmainpanelpreviewimagefile,
      'cb_filexfer_blackandwhite'     :     event_btnmainpanelpreviewimagefile,
      'in_mainpanel_sendimagefilename' :    event_btnmainpanelpreviewimagefile,

      'btn_mainpanel_relay'       : event_btnmainpanelrelay,

      'btn_mainarea_reset'        : event_btnmainareareset,

      'btn_mainpanel_updaterecent' : event_btnmainpanelupdaterecent,

       'btn_relay_copytooutbox'   : event_btnrelaycopytooutbox,

      'btn_mainpanel_clearstations' : event_btnmainpanelclearstations,

       'btn_myinfo_save'         : event_btnmyinfosave,

      'btn_winlink_list_emails'  : event_winlinklist,
      'winlink_inbox_table'      : event_winlinkinboxtable,
      'winlink_outbox_table'      : event_winlinkoutboxtable,

      'winlink_rmsmsg_table'      : event_winlinkrmsmsgtable,

      'btn_mainpanel_testprop'      : event_btnmainpaneltestprop,

      'btn_winlink_edit_selected'        : event_btnwinlinkeditselected,
      'btn_winlink_send_selected'        : event_btnwinlinksendselected,

      'btn_compose_goingqrtsaam'          : event_btncomposegoingqrtsaam,
      'btn_compose_confirmedhavecopy'     : event_btncomposeconfirmedhavecopy,
      'btn_compose_areyoureadytoreceive'  : event_btncomposeareyoureadytoreceive,
      'btn_compose_readytoreceive'        : event_btncomposereadytoreceive,
      'btn_compose_notreadytoreceive'     : event_btncomposenotreadytoreceive,
      'btn_compose_cancelalreadyhavecopy' : event_btncomposecancelalreadyhavecopy,
      'btn_outbox_viewform'       : event_btnoutboxviewform,
      'btn_mainarea_visitgithub'  : event_btnmainareavisitgithub,
      'btn_substation_connect_1'  : event_btnsubstationconnect1,
      'btn_substation_disconnect_1'  : event_btnsubstationdisconnect1,
      'btn_mainpanel_sendgfile'   : event_mainpanelsendfile,

      'btn_mainpanel_sendimagefile'   : event_mainpanelsendimagefile,

      #'btn_mainpanel_saveasfile'  : event_mainpanelsaveasfile,
      'in_mainpanel_saveasfilename'  : event_mainpanelsaveasfile,
      'in_mainpanel_saveasimagefilename'  : event_mainpanelsaveasimagefile,

      'combo_element1'            : event_comboelement1,
      'combo_element2'            : event_comboelement2,
      'combo_element3'            : event_comboelement3,
      'combo_element4'            : event_comboelement4,
      'combo_element5'            : event_comboelement5,
      'combo_element6'            : event_comboelement6,
      'combo_element7'            : event_comboelement7,
      'combo_element8'            : event_comboelement8,
      'combo_element9'            : event_comboelement9,
      'combo_element10'           : event_comboelement10,
      'combo_element11'           : event_comboelement11,
      'combo_element12'           : event_comboelement12,
      'combo_element13'           : event_comboelement13,
      'combo_element14'           : event_comboelement14,
      'combo_element15'           : event_comboelement15,
      'combo_element16'           : event_comboelement16,
      'combo_element17'           : event_comboelement17,
      'combo_element18'           : event_comboelement18,
  }


class PopupControlsProc(object):
  
  
  def __init__(self, view, window):  
    return
    
  def event_catchall(self, values):
    return()

  def event_exit_receive(self, values):
    return




