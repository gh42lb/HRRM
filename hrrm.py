#!/usr/bin/env python
import sys
import constant as cn
import string
import struct

import FreeSimpleGUI as sg

import json
import threading
import os
import platform
import calendar
import xmlrpc.client
import debug as db
import JS8_Client
import fldigi_client
import getopt

import js8_form_gui
import js8_form_events
import js8_form_dictionary
import saamfram
from app_pipes import AppPipes
from gps import *
from datetime import datetime, timedelta
from datetime import time
from uuid import uuid4
from JSONPipeVPNhrrm import JSONPipeVPNhrrm
from saamfram_js8 import SAAMFRAM_js8
from saamfram_fldigi import SAAMFRAM_fldigi
from collections import OrderedDict

"""
MIT License

Copyright (c) 2022-2025 Lawrence Byng

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

class NetGarq(object):


  """
  debug level 0=off, 1=info, 2=warning, 3=error
  """
  def __init__(self, debug):  
    self.garq_stations = []
    self.recipient_stations=[]	  
    self.messages_inbox = []
    self.messages_outbox = []
    self.messages_relaybox = []	  
    self.messages_sentbox = []	  
    self.template_files = []
    self.winlink_inbox_files = []	  
    self.winlink_outbox_files = []	  
    self.winlink_rmsmsg_files = []	  
    self.loaded_template_files = []	  
    self.templates = []
    self.categories = []
    self.garq_stations = []
    self.selected_stations = []
    self.selected_p2pip_stations = []
    self.selected_relay_stations = []
    self.chat_data = []
    self.chat_data_colors = []

    self.p2pip_chat_data = ChatDataCache(self)

    self.selected_template = 'General Message'
    self.debug = db.Debug(cn.DEBUG_HRRM)

    self.form_gui = None
    self.form_events = None
    self.form_dictionary = None
    self.js8client = None
    self.fldigiclient = None
    self.debug = None
    self.saamfram = None
    self.pipes = None

    self.formdesigner_mode = False
    self.include_gps = False
    self.operating_mode = cn.FLDIGI
    self.station_call_sign = ''

    #FIXME THIS SHOULD NOT BE HARDCODED
    self.send_mode_rig1 = cn.SEND_JS8CALL
    self.send_mode_rig1 = cn.SEND_FLDIGI

    self.display_winlink = False
    self.include_templates = False
    self.include_experimental = False
    self.listenonly = False

    self.p2p_online = False
    
    return


  def setSendModeRig1(self, send_mode):
    self.send_mode_rig1 = send_mode
    return
    
  def getSendModeRig1(self):  
    return self.send_mode_rig1
    
  def setDebug(self, debug):
    self.debug = debug
    return

  def setFormGui(self, form_gui):
    self.form_gui = form_gui
    return

  def setFormEvents(self, form_events):
    self.form_events = form_events
    return

  def setFormDictionary(self, form_dictionary):
    self.form_dictionary = form_dictionary
    return
  
   
  def getRecipientStations(self):
    return self.recipient_stations	  

  def addRecipientStation(self, callsign):
    self.recipient_stations = self.recipient_stations + [callsign]	  
    return 

  def removeRecipientStation(self, key):
    return self.recipient_stations.pop(key, None)
   
  def clearRecipientStations(self):
    self.recipient_stations = []
    return
   
  def garqPartitionMessage(self, text):
    return self.debug_level

  def garqConfirmMesasgePart(self, text, crc):
    self.debug.info_message("Info: " + msg )

  def popupReceivedText(self, text):
    self.debug.info_message("Warning: " + msg )
    

  def areTemplateFieldsUnique(self, categoryname, templatename, description, version, filename):
    is_unique = True
    """ compare the filenames first as this is the primary key """
    
    """ now compare the category names as category is the secondary key """

    """ now compare template name """

    """ now compare version """
    	  
    return (is_unique)


  #FIXME
  def getIndexFromDisplayLine(self, line_index):
    return

  #FIXME
  def getDisplayLineFromIndex(self, line_index):
    return



  """
  peer stations section
  """
  def clearSelectedStations(self):
    self.selected_stations = []	  
    return


  def addSelectedStation(self, station, num, grid, connect, rig, modulation, snr, ID):

    self.debug.info_message("addSelectedStation" )

    signal_report = ''
    memo = ''

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign        = lineitem[0]
      prev_ID         = lineitem[8]
      if(callsign == station):
        """ test timestamp in here"""
        prev_timestamp_string = self.saamfram.extractTimestamp(prev_ID)
        prev_inttime = ((int(prev_timestamp_string,36))/100.0)
        self.debug.error_message("addSelectedStation previous timestamp: " + prev_timestamp_string)

        timestamp_string = self.saamfram.extractTimestamp(ID)
        inttime = ((int(timestamp_string,36))/100.0)
        self.debug.error_message("addSelectedStation this timestamp: " + timestamp_string)

        """ if prev station timestamp is more recent then ignore add...best guess within limitation of encoding!"""
        if(True):
          num        = lineitem[1]
          previous_grid = lineitem[2]
          memo       = lineitem[3]
          connect    = lineitem[4]
          rig        = lineitem[5]
          modulation = lineitem[6]
          snr        = lineitem[7]
          last_heard = lineitem[8]
          signal_report = lineitem[9]

          new_grid = ''
          if (grid.strip() != ''):
            new_grid = grid
          else:
            new_grid = previous_grid
          self.debug.error_message("addSelectedStation update grid to " + new_grid)
          self.selected_stations[x] = [callsign, num, new_grid, memo, connect, rig, modulation, snr, ID, signal_report]

          return self.selected_stations

    self.selected_stations.append([station, num, grid, memo, connect, rig, modulation, snr, ID, signal_report])
    return self.selected_stations


  def getSelectedStationIndex(self, station):
    self.debug.info_message("getSelectedStationIndex " )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      if(callsign == station):
        return x

    return -1

  
  def updateSelectedStationMemo(self, station, memo):

    self.debug.info_message("updateSelectedStationMemo " + station + ' ' + memo )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      self.debug.info_message("updateSelectedStationMemo callsign " + callsign + ' ' + station)
      if(callsign == station):
        self.debug.info_message("updateSelectedStationMemo updating Memo")

        num        = lineitem[1]
        grid       = lineitem[2]
        connect    = lineitem[4]
        rig        = lineitem[5]
        modulation = lineitem[6]
        snr        = lineitem[7]
        last_heard = lineitem[8]
        signal_report = lineitem[9]

        self.selected_stations[x] = [callsign, num, grid, memo, connect, rig, modulation, snr, last_heard, signal_report]

        return 
  

  def updateSelectedStationSNR(self, station, snr):

    self.debug.info_message("updateSelectedStationSNR " + station + ' ' + snr )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      self.debug.info_message("updateSelectedStationSNR callsign " + callsign + ' ' + station)
      if(callsign == station):
        self.debug.info_message("updateSelectedStationSNR updating SNR")

        num        = lineitem[1]
        grid       = lineitem[2]

        memo       = lineitem[3]
      
        connect    = lineitem[4]
        rig        = lineitem[5]
        modulation = lineitem[6]
        last_heard = lineitem[8]
        signal_report = lineitem[9]

        self.selected_stations[x] = [callsign, num, grid, memo, connect, rig, modulation, snr, last_heard, signal_report]

        return 

  def updateSelectedStationSignalReport(self, station, signal_report):

    self.debug.info_message("updateSelectedStationSignalReport " + station + ' ' + signal_report )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      self.debug.info_message("updateSelectedStationSignalReport callsign " + callsign + ' ' + station)
      if(callsign == station):
        self.debug.info_message("updateSelectedStationSignalReport updating sigrep")

        num        = lineitem[1]
        grid       = lineitem[2]
        memo       = lineitem[3]
        connect    = lineitem[4]
        rig        = lineitem[5]
        modulation = lineitem[6]
        snr        = lineitem[7]
        last_heard = lineitem[8]

        self.selected_stations[x] = [callsign, num, grid, memo, connect, rig, modulation, snr, last_heard, signal_report]

        return 

  
  def getSelectedStations(self):
    return self.selected_stations

  def getSelectedStationsColors(self):
    selected_colors = []

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      selected = lineitem[4]
      if(selected == 'X'):
        selected_colors.append([x, 'green1'])
      else:
        selected_colors.append([x, 'ivory2'])

    return selected_colors 


  def setSelectedStations(self, selectedstations):
    self.selected_stations = selectedstations
    return

  def toggleSelectedStations(self, index):

    lineitem   = self.selected_stations[index]
    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    memo       = lineitem[3]
    selected   = lineitem[4]
    rig        = lineitem[5]
    modulation = lineitem[6]
    snr        = lineitem[7]
    last_heard = lineitem[8]
    signal_report  = lineitem[9]

    if(selected == 'X'):
      selected = ' '
    else:
      selected = 'X'
    self.selected_stations[index] = [callsign, num, grid, memo, selected, rig, modulation, snr, last_heard, signal_report]


  def selectSelectedStations(self, index):

    lineitem   = self.selected_stations[index]
    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    memo       = lineitem[3]
    selected   = lineitem[4]
    rig        = lineitem[5]
    modulation = lineitem[6]
    snr        = lineitem[7]
    last_heard = lineitem[8]
    signal_report  = lineitem[9]

    selected = 'X'
    self.selected_stations[index] = [callsign, num, grid, memo, selected, rig, modulation, snr, last_heard, signal_report]


  def getConnectToString(self):

    selected_callsigns = ''
    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      selected = lineitem[4]

      if(selected == 'X'):
        if(selected_callsigns == ''):
          selected_callsigns = selected_callsigns + callsign
        else:
          selected_callsigns = selected_callsigns + ';' + callsign

    selected_callsigns2 = ''
    for x in range (len(self.selected_relay_stations)):
      lineitem = self.selected_relay_stations[x]
      callsign = lineitem[0]
      selected = lineitem[4]

      if(selected == 'X'):
        if(selected_callsigns2 == ''):
          selected_callsigns2 = selected_callsigns2 + callsign
        else:
          selected_callsigns2 = selected_callsigns2 + ';' + callsign

    returnval = ''
    if(selected_callsigns != '' and selected_callsigns2 != ''):
      returnval = selected_callsigns + ';' + selected_callsigns2
    elif(selected_callsigns == '' and selected_callsigns2 == ''):
      returnval = ''
    elif(selected_callsigns2 == ''):
      returnval = selected_callsigns
    else:
      returnval = selected_callsigns2

    return returnval



  """
  p2pip stations section
  headings=['Callsign', 'Nickname', 'City', 'State', 'Country', 'Selected', 'ID', 'Timestamp']
  """

  def clearSelectedP2pipStations(self):
    self.selected_p2pip_stations = []	  
    return


  def addSelectedP2pipStation(self, callsign, nickname, city, state, country, selected, ID, timestamp):

    self.debug.info_message("addSelectedP2pipStation" )

    for x in range (len(self.selected_p2pip_stations)):
      lineitem    = self.selected_p2pip_stations[x]
      station_ID      = lineitem[6]
      prev_timestamp  = lineitem[7]
      if(station_ID == ID):
        """ test timestamp in here"""
        prev_timestamp_string = prev_timestamp
        prev_inttime = ((int(prev_timestamp_string,36))/100.0)
        self.debug.error_message("addSelectedP2pipStation previous timestamp: " + prev_timestamp_string)

        timestamp_string = timestamp
        inttime = ((int(timestamp_string,36))/100.0)
        self.debug.error_message("addSelectedP2pipStation this timestamp: " + timestamp_string)

        """ if prev station timestamp is more recent then ignore add...best guess within limitation of encoding!"""

        if(prev_inttime >= inttime):
          self.debug.error_message("addSelectedP2pipStation discarding")
          return self.selected_p2pip_stations
        else:
          callsign      = lineitem[0]
          nickname      = lineitem[1]
          city          = lineitem[2]
          state         = lineitem[3]
          country       = lineitem[4]
          selected      = lineitem[5]
          ID            = lineitem[6]
          timestamp     = lineitem[7]
          self.selected_p2pip_stations[x] = [callsign, nickname, city, state, country, selected, ID, timestamp]

          return self.selected_p2pip_stations

    self.selected_p2pip_stations.append([callsign, nickname, city, state, country, selected, ID, timestamp])
    return self.selected_p2pip_stations


  def getSelectedP2pipStationIndex(self, station_ID):
    self.debug.info_message("getSelectedP2pipStationIndex " )

    for x in range (len(self.selected_p2pip_stations)):
      lineitem = self.selected_p2pip_stations[x]
      ID = lineitem[6]
      if(ID == station_ID):
        return x

    return -1
 
  def getSelectedP2pipStations(self):
    return self.selected_p2pip_stations

  def getSelectedP2pipStationsColors(self):
    selected_colors = []

    for x in range (len(self.selected_p2pip_stations)):
      lineitem = self.selected_p2pip_stations[x]
      selected = lineitem[5]
      if(selected == 'X'):
        selected_colors.append([x, 'green1'])
      else:
        selected_colors.append([x, 'ivory2'])

    return selected_colors 


  def setSelectedP2pipStations(self, selectedstations):
    self.selected_p2pip_stations = selectedstations
    return

  def toggleSelectedP2pipStations(self, index):

    lineitem   = self.selected_p2pip_stations[index]
    callsign      = lineitem[0]
    nickname      = lineitem[1]
    city          = lineitem[2]
    state         = lineitem[3]
    country       = lineitem[4]
    selected      = lineitem[5]
    ID            = lineitem[6]
    timestamp     = lineitem[7]

    if(selected == 'X'):
      selected = ' '
    else:
      selected = 'X'
    self.selected_p2pip_stations[index] = [callsign, nickname, city, state, country, selected, ID, timestamp]


  def selectSelectedP2pipStations(self, index):

    lineitem   = self.selected_p2pip_stations[index]
    callsign      = lineitem[0]
    nickname      = lineitem[1]
    city          = lineitem[2]
    state         = lineitem[3]
    country       = lineitem[4]
    selected      = lineitem[5]
    ID            = lineitem[6]
    timestamp     = lineitem[7]

    selected = 'X'
    self.selected_p2pip_stations[index] = [callsign, nickname, city, state, country, selected, ID, timestamp]



  """
  relay stations section
  """
  def clearSelectedRelayStations(self):
    self.selected_relay_stations = []	  
    return

  def addSelectedRelayStation(self, station, num, grid, relay, connect, hops, last_heard_1):

    self.debug.info_message("addSelectedRelayStation" )

    """ is the relay station already present in the peer list. if so ignore add request"""
    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      if(callsign == station):
        return self.selected_relay_stations

    """ is the relay station already present in the relay list. if previos station hops is less then ignore"""
    for x in range (len(self.selected_relay_stations)):
      lineitem     = self.selected_relay_stations[x]
      callsign     = lineitem[0]
      prev_hops    = lineitem[5]
      last_heard_2 = lineitem[6]
      if(callsign == station):
        if(prev_hops < hops):
          return self.selected_relay_stations
        else:
          """ test timestamp. higher number value is more recent """
          time_value_1 = self.saamfram.getDecodeIntTimeFromUniqueId(last_heard_1)
          time_value_2 = self.saamfram.getDecodeIntTimeFromUniqueId(last_heard_2)
          if(time_value_2 > time_value_1):
            return self.selected_relay_stations

          """ ok so relay station has same hops and is more recent or has less hops...ok so add it"""
          self.selected_relay_stations.remove(lineitem)
          self.selected_relay_stations.append([station, num, grid, relay, connect, hops, last_heard_1])
          return self.selected_relay_stations

    """ ok so relay station is either new ...ok so add it"""
    self.selected_relay_stations.append([station, num, grid, relay, connect, hops, last_heard_1])
    return self.selected_relay_stations
  
  def getSelectedRelayStations(self):
    return self.selected_relay_stations

  def getSelectedRelayStationsColors(self):
    selected_colors = []

    for x in range (len(self.selected_relay_stations)):
      lineitem = self.selected_relay_stations[x]
      selected = lineitem[4]
      if(selected == 'X'):
        selected_colors.append([x, 'green1'])
      else:
        selected_colors.append([x, 'plum1'])

    return selected_colors 


  def setSelectedRelayStations(self, selectedstations):
    self.selected_relay_stations = selectedstations
    return



  def toggleSelectedRelayStations(self, index):

    lineitem   = self.selected_relay_stations[index]
    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    relay      = lineitem[3]
    selected   = lineitem[4]
    hops       = lineitem[5]
    last_heard = lineitem[6]

    if(selected == 'X'):
      selected = ' '
    else:
      selected = 'X'
    self.selected_relay_stations[index] = [callsign, num, grid, relay, selected, hops, last_heard]

    selected_callsigns = ''
    for x in range (len(self.selected_relay_stations)):
      lineitem = self.selected_relay_stations[x]
      callsign = lineitem[0]
      selected = lineitem[4]

      if(selected == 'X'):
        if(selected_callsigns == ''):
          selected_callsigns = selected_callsigns + callsign
        else:
          selected_callsigns = selected_callsigns + ';' + callsign

    return selected_callsigns


  def getRelayListFromSendList(self, msgto):

    retval = ''
    calls = msgto.split(';')
    for x in range (len(self.selected_relay_stations)):
      lineitem = self.selected_relay_stations[x]
      callsign = lineitem[0]
      relay    = lineitem[3]

      for y in range (len(calls)):
        if(callsign == calls[y] and self.isRecipientPresent(relay)):
          retval = retval + ';' + relay
    

    return retval.strip(';')

  def isRecipientPresent(self, recipient):
    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      if(callsign == recipient):
        return True

    return False

  def removeGarqStation(self, key):
    return self.garq_stations.pop(key, None)

  """ this set of methods is used to display the main channel info at the top of main screen"""
  def clearGarqStations(self):
    self.garq_stations = []	  
    return

  """ channel name, station callsign, mode type, mode, offset, comm status, in session, last_heard, SAAM capable, """
  def addGarqStation(self, rigname, channel_name, station_callsign, mode_type, mode_name, offset, comm_status, in_session, last_heard, saam_capable):
    self.garq_stations.append([rigname, channel_name, station_callsign, mode_type, mode_name, offset, comm_status, in_session, last_heard, saam_capable])
    return self.garq_stations
  
  def getGarqStations(self):
    return self.garq_stations

  def setGarqStations(self, garqstations):
    self.garq_stations = garqstations
    return



  def clearChatData(self):
    self.chat_data = []	  
    return

  def addChatData(self, msg_from, message, msgid):
    self.chat_data.append([msg_from, message, msgid])
    return self.chat_data

  def getChatData(self):
    return self.chat_data

  def getChatDataColors(self):
    return self.chat_data_colors

  def appendChatDataColorTargeted(self):
    color_index = max(len(self.chat_data)-1, 0)
    self.chat_data_colors.append([color_index , 'green1'])

  def appendChatDataColorPassive(self):
    color_index = max(len(self.chat_data)-1, 0)
    self.chat_data_colors.append([color_index , 'dark gray'])


  def clearCategories(self):
    self.categories = []	  
    return

  def addCategory(self, category):

    """ make sure the cateogry is not already in the list """
    for x in range(len(self.categories)):
      if(self.categories[x][0] == category):
        return

    self.categories.append([category])
    return self.categories
  
  def getCategories(self):
    return self.categories

  def setCategories(self, categories):
    self.categories = categories
    return

  def deleteCategory(self, category):
    self.categories.remove([category])
    """
    for x in range(len(self.categories)):
      if(self.categories[x][0] == category):
        self.categories.remove(self.messages_outbox[x])
        return
    """    
    return



  def clearTemplates(self):
    self.templates = []	  
    return

  def addTemplate(self, templatename, description, version, filename):
    self.templates.append([templatename, description, version, filename])
    return self.templates
  
  def getTemplates(self):
    return self.templates

  def setTemplates(self, templates):
    self.templates = templates
    return


  """ Winlink Inbox Files """
  def clearWinlinkInboxFiles(self):
    self.winlink_inbox_files = []	  
    return


  def addWinlinkInboxFile(self, filename, msgfrom, msgto, subject, timestamp, msgtype, msgid):
    self.winlink_inbox_files.append([filename, msgfrom, msgto, subject, timestamp, msgtype, msgid])
    return self.winlink_inbox_files
  
  def getWinlinkInboxFiles(self):
    return self.winlink_inbox_files

  def setWinlinkInboxFiles(self, winlinkfiles):
    self.winlink_inbox_files = winlinkfiles
    return

  """ Winlink Outbox Files """
  def clearWinlinkOutboxFiles(self):
    self.winlink_outbox_files = []	  
    return

  def addWinlinkOutboxFile(self, filename, msgfrom, msgto, subject, timestamp, msgtype, msgid):
    self.winlink_outbox_files.append([filename, msgfrom, msgto, subject, timestamp, msgtype, msgid])
    return self.winlink_outbox_files
 
  def getWinlinkOutboxFiles(self):
    return self.winlink_outbox_files

  def setWinlinkOutboxFiles(self, winlinkfiles):
    self.winlink_outbox_files = winlinkfiles
    return

  def getWinlinkOutboxColors(self):
    selected_colors = []

    for x in range (len(self.winlink_outbox_files)):
      lineitem = self.winlink_outbox_files[x]
      filename = lineitem[0]

      if(filename in self.form_events.winlink_import.winlink_outbox_folder_files):
        selected_colors.append([x, 'white'])
      else:
        selected_colors.append([x, 'green1'])

    return selected_colors




  """ Winlink RMS message folder Files """
  def clearWinlinkRMSMsgFiles(self):
    self.winlink_rmsmsg_files = []	  
    return

  def addWinlinkRMSMsgFile(self, filename, msgfrom, msgto, subject, timestamp, msgtype, msgid):
    self.winlink_rmsmsg_files.append([filename, msgfrom, msgto, subject, timestamp, msgtype, msgid])
    return self.winlink_rmsmsg_files
 
  def getWinlinkRMSMsgFiles(self):
    return self.winlink_rmsmsg_files

  def setWinlinkRMSMsgFiles(self, winlinkfiles):
    self.winlink_rmsmsg_files = winlinkfiles
    return



  """ Template Files """
  def clearTemplateFiles(self):
    self.template_files = []	  
    return

  def addTemplateFile(self, filename):
    self.template_files.append([filename])
    return self.template_files
  
  def getTemplateFiles(self):
    return self.template_files

  def setTemplateFiles(self, templatefiles):
    self.template_files = templatefiles
    return

  """ loaded template files """
  def clearLoadedTemplateFiles(self):
    self.loaded_template_files = []	  
    return

  def addLoadedTemplateFile(self, filename, description, version):
    self.loaded_template_files.append([filename, description, version])
    return self.loaded_template_files
  
  def getLoadedTemplateFiles(self):
    return self.loaded_template_files

  def setLoadedTemplateFiles(self, loadedtemplatefiles):
    self.loaded_template_files = loadedtemplatefiles
    return


  """ outbox """

  def clearOutbox(self):
    self.messages_outbox = []	  
    return

  def addMessageToOutbox(self, msgfrom, msgto, subject, timestamp, priority, msgtype,  msgid):
    self.messages_outbox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, msgid])
    return self.messages_outbox

  def deleteMessageFromOutbox(self, msgid):
    for x in range(len(self.messages_outbox)):
      if(self.messages_outbox[x][6] == msgid):
        self.messages_outbox.remove(self.messages_outbox[x])
        return
    return
  
  def getMessageOutbox(self):
    return self.messages_outbox

  def setMessageOutbox(self, outbox):
    self.messages_outbox = outbox
    return


  def clearRelaybox(self):
    self.messages_relaybox = []	  
    return

  def addMessageToRelaybox(self, msgfrom, msgto, subject, timestamp, priority, msgtype,  msgid, conf_rcvd, frag_size, verified):

    for x in range(len(self.messages_relaybox)):
      if(self.messages_relaybox[x][6] == msgid):
        self.messages_relaybox.remove(self.messages_relaybox[x])
        self.messages_relaybox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, msgid, conf_rcvd, frag_size, verified])
        return self.messages_relaybox

    self.messages_relaybox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, msgid, conf_rcvd, frag_size, verified])
    return self.messages_relaybox

  def updateRelayboxValue(self, msgid, item_number, value):

    for x in range(len(self.messages_relaybox)):
      lineitem = self.messages_relaybox[x]
      if(lineitem[6] == msgid):

        lineitem[item_number] = value

        msgfrom   = lineitem[0]
        msgto     = lineitem[1]
        subject   = lineitem[2]
        timestamp = lineitem[3]
        priority  = lineitem[4]
        msgtype   = lineitem[5]
        msgid     = lineitem[6]
        conf_rcvd = lineitem[7]
        frag_size = lineitem[8]
        verified  = lineitem[9]

        self.messages_relaybox[x] = [msgfrom, msgto, subject, timestamp, priority, msgtype, msgid, conf_rcvd, frag_size, verified]

        return 



  def deleteMessageFromRelaybox(self, msgid):
    for x in range(len(self.messages_relaybox)):
      if(self.messages_relaybox[x][6] == msgid):
        self.messages_relaybox.remove(self.messages_relaybox[x])
        return
    return
  
  def getMessageRelaybox(self):
    return self.messages_relaybox

  def setMessageRelaybox(self, relaybox):
    self.messages_relaybox = relaybox
    return

  def getMessageRelayboxColors(self):
    self.debug.info_message("getMessageRelayboxColors")
    selected_colors = []
    flash_relay_button = False

    for x in range (len(self.messages_relaybox)):
      lineitem = self.messages_relaybox[x]
      selected = lineitem[9]

      """ check if the message recipients are in the active station list"""

      if(selected == 'Verified'):
        selected_colors.append([x, 'green1'])
      elif(selected == 'Stub'):
        selected_colors.append([x, 'cyan'])
      elif(selected == 'Partial'):
        selected_colors.append([x, 'blue'])
      elif(selected == 'CRC'):
        selected_colors.append([x, 'red'])

    if(flash_relay_button == True):
      self.form_gui.form_events.changeFlashButtonState('btn_compose_haverelaymsgs', True)
      self.debug.info_message("getMessageRelayboxColors set relay flash state True")
    else:
      self.form_gui.form_events.changeFlashButtonState('btn_compose_haverelaymsgs', False)
      self.debug.info_message("getMessageRelayboxColors set relay flash state False")

    return selected_colors



  def clearSentbox(self):
    self.messages_sentbox = []	  
    return

  def addMessageToSentbox(self, msgfrom, msgto, subject, timestamp, priority, msgtype,  msgid, confirmed):

    self.deleteMessageFromSentbox(msgid)
    self.messages_sentbox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, msgid, confirmed])
    return self.messages_sentbox
  
  def getMessageSentbox(self):
    return self.messages_sentbox

  def setMessageSentbox(self, sent):
    self.messages_sentbox = sent
    return

  def deleteMessageFromSentbox(self, msgid):
    for x in range(len(self.messages_sentbox)):
      if(self.messages_sentbox[x][6] == msgid):
        self.messages_sentbox.remove(self.messages_sentbox[x])
        return
    return


  def clearInbox(self):
    self.messages_inbox = []	  
    return


  def addMessageToInbox(self, msgfrom, msgto, subject, timestamp, priority, msgtype, verified, msgid):
    for x in range(len(self.messages_inbox)):
      if(self.messages_inbox[x][7] == msgid):
        self.messages_inbox.remove(self.messages_inbox[x])
        self.messages_inbox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, verified, msgid])
        return self.messages_inbox

    self.messages_inbox.append([msgfrom, msgto, subject, timestamp, priority, msgtype, verified, msgid])
    return self.messages_inbox

  def deleteMessageFromInbox(self, msgid):
    for x in range(len(self.messages_inbox)):
      if(self.messages_inbox[x][7] == msgid):
        self.messages_inbox.remove(self.messages_inbox[x])
        return
    return
  
  def getMessageInbox(self):
    return self.messages_inbox

  def setMessageInbox(self, inbox):
    self.messages_inbox = inbox
    return

  def getMessageInboxColors(self):
    selected_colors = []

    for x in range (len(self.messages_inbox)):
      lineitem = self.messages_inbox[x]
      selected = lineitem[6]
      if(selected == 'Verified'):
        selected_colors.append([x, 'green1'])
      elif(selected == 'Stub'):
        selected_colors.append([x, 'cyan'])
      elif(selected == 'Partial'):
        selected_colors.append([x, 'blue'])
      elif(selected == 'CRC'):
        selected_colors.append([x, 'red'])

    return selected_colors


  """ re-write the to-list callsigns as a filsafe. Used when forwarding messages """
  def forwardMsgRemoveOwnCallsign(self, tolist):

    my_call = self.saamfram.getMyCall()

    items = tolist.split(';')

    return_str = ''
    for x in range (len(items)):
      if(items[x] != my_call):
        return_str = return_str + items[x] + ';'

    return return_str.strip(';')


  def getMyGPSLocationFromDongle(self):
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 
    report = gpsd.next()
    for x in range(10):
      report = gpsd.next() #
      if report['class'] == 'TPV':  
        print (getattr(report,'lat',0.0),"\t")
        print (getattr(report,'lon',0.0))
        print (getattr(report,'time',''),"\t")
        print (getattr(report,'time',''),"\t",)
        print (getattr(report,'alt','nan'),"\t\t",)
        print (getattr(report,'epv','nan'),"\t",)
        print (getattr(report,'ept','nan'),"\t",)
        print (getattr(report,'speed','nan'),"\t",)
        print (getattr(report,'climb','nan'),"\t"   )

  def getMyGPSSatelliteInfo(self):
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 
    report = gpsd.next()
    for x in range(10):
      report = gpsd.next() #
      if report['class'] == 'SKY':
        print (' Satellites (total of', len(gpsd.satellites) , ' in view)')
        for i in gpsd.satellites:
          print ('t', i)
         
        print ('\n\n')
        print ('PRN = PRN ID of the satellite. 1-63 are GNSS satellites, 64-96 are GLONASS satellites, 100-164 are SBAS satellites')
        print ('E = Elevation in degrees')
        print ('As = Azimuth, degrees from true north')
        print ('ss = Signal stength in dB')
        print ('used = Used in current solution?')


  def getMsgRig1(self):
    data = ''
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      data = self.fldigiclient.getMsg()
    return data

  def testReceiveStringRig1(self, teststr):
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      return self.fldigiclient.testReceiveString(teststr)
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      return self.js8client.testReceiveString(teststr)

  def testRcvSignalStopped(self):
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      return self.fldigiclient.testRcvSignalStopped()
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      return False
      
  def appendReceiveStringRig1(self, data):
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      self.fldigiclient.appendReceiveString(data)
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      self.js8client.appendReceiveString(data)

  def getReceiveStringRig1(self):
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      return self.fldigiclient.getReceiveString()
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      return self.js8client.getReceiveString()
      		
  def resetReceiveStringRig1(self):      		
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      self.fldigiclient.resetReceiveString()
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      self.js8client.resetReceiveString()
      		

  def setSpeed(self, speed):
    self.js8client.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )
    return()

  def getSpeed(self):
    self.js8client.sendMsg("MODE.GET_SPEED", "")
    return()

  def setDialAndOffset(self, dial, offset):
    self.getSpeed()
    self.js8client.sendMsg("RIG.SET_FREQ", "", params={"DIAL":dial, "OFFSET":offset, "_ID":-1})
    return()

  def getDialAndOffset(self):
    self.js8client.sendMsg("RIG.GET_FREQ", "")
    return()
    
  def getStationCall(self):
    self.js8client.sendMsg("STATION.GET_CALLSIGN", "")
    return()

      		
  def sendItNowJS8(self, message):
    self.debug.info_message("JS8Call sendItNow. message: " + message)
    """need to blank the message box first so that send engages correctly"""

    self.getSpeed()
    self.js8client.sendMsg("TX.SET_TEXT", '')
    self.js8client.sendMsg("TX.SEND_MESSAGE", message)

    return ()

  def sendItNowFldigi(self, message):
    self.debug.info_message("Fldigi sendItNow. message: " + message)

    self.saamfram.resetSNR()

    self.fldigiclient.sendItNowFldigi(message)
    return ()


  def sendTheMessage(self, message, set_txid):

    checked = self.form_gui.window['cb_mainwindow_txenable'].get()
    self.debug.info_message("checked : " + str(checked))

    if(checked):
      if(set_txid):
        self.saamfram.setTxidState(self.saamfram.tx_rig, self.saamfram.tx_channel, True)

      self.saamfram.setCommStatus(self.saamfram.tx_rig, self.saamfram.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.saamfram.setExpectedReply(self.saamfram.tx_rig, self.saamfram.tx_channel, cn.COMM_LISTEN)
      self.sendItNowRig1(message)

    return

  def sendItNowRig1(self, fragtagmsg):

    self.debug.info_message("sendItNowRig1")

    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      self.debug.info_message("sendItNowRig1 FLDIGI\n")

      pre_message = ''

      self.sendItNowFldigi(pre_message + fragtagmsg)
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      self.debug.info_message("sendItNowRig1 JS8\n")
      self.sendItNowJS8(fragtagmsg)



  def sendFormRig1(self, fragtagmsg, tolist, msgid):
    if(self.operating_mode == cn.FLDIGI or self.operating_mode == cn.JSDIGI):
      self.debug.info_message("sendFormRig1 FLDIGI\n")

      self.debug.info_message("calling saamfram: " + fragtagmsg )
      pre_message = ''

      checked = self.form_gui.window['cb_mainwindow_txenable'].get()
      if(checked):
        self.saamfram.sendFormFldigi(pre_message + fragtagmsg, tolist, msgid)
    elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
      self.debug.info_message("sendFormRig1 JS8\n")
      self.saamfram.sendFormJS8(fragtagmsg, tolist)

    
  def my_new_callback2(self, json_string, txrcv):

    line = json_string.split('\n')
    length = len(line)

    for x in range(length-1):
      dict_obj = json.loads(line[x])
      text = self.js8client.stripEndOfMessage(self.js8client.getValue(dict_obj, "value")).decode('utf-8')
      
      type = self.js8client.getValue(dict_obj, "type").decode('utf-8')
      last_call = None
     
      """ test to see if there are any missing frames """
      self.js8client.areFramesMissing(self.js8client.getValue(dict_obj, "value") )

      if (type == "STATION.CALLSIGN"):
        self.debug.info_message("my_new_callback. STATION.CALLSIGN")
        self.station_call_sign = self.js8client.getValue(dict_obj, "value").decode('utf-8')

      elif (type == "RIG.FREQ"):
        dialfreq = int(self.js8client.getParam(dict_obj, "DIAL"))
        freqstr = str(float(dialfreq)/1000000.0)
        offsetstr = self.js8client.getParam(dict_obj, "OFFSET")
          			
        self.debug.info_message("my_new_callback. RIG.FREQ. Dial: " + freqstr)
        self.debug.info_message("my_new_callback. RIG.FREQ, Offset: " + offsetstr)

      elif (type == "RX.SPOT"):
        self.debug.info_message("my_new_callback. RX.SPOT")

      elif (type == "RX.DIRECTED"):
        self.debug.info_message("my_new_callback. RX.DIRECTED")
        
      elif (type == "RX.ACTIVITY"):
        self.debug.info_message("my_new_callback. RX.ACTIVITY")
        missing_frames = self.js8client.areFramesMissing(text.encode() )
        self.debug.info_message("processMsg. RX.ACTIVITY. missing frames: " + str(missing_frames) )
        
      elif (type == "RIG.PTT"):
        self.debug.info_message("my_new_callback. RIG.PTT")
        pttstate = self.js8client.getParam(dict_obj, "PTT")
        self.debug.info_message("my_new_callback. RIG.PTT PTT State: " + str(pttstate))
      elif (type == "TX.TEXT"):
        self.debug.info_message("my_new_callback. TX.TEXT")
      elif (type == "TX.FRAME"):
        self.debug.info_message("my_new_callback. TX.FRAME")
      elif (type == "STATION.STATUS"):
        dialfreq = int(self.js8client.getParam(dict_obj, "DIAL"))
        freqstr = str(float(dialfreq)/1000000.0)
        offsetstr = self.js8client.getParam(dict_obj, "OFFSET")
          			
        self.debug.info_message("my_new_callback. STATION.STATUS. Dial: " + freqstr)
        self.debug.info_message("my_new_callback. STATION.STATUS, Offset: " + offsetstr)
      else:
        self.debug.warning_message("my_new_callback. unhandled type: " + str(type) )
   


class JSONPipeVPNhrrmCallback(object):

  pipeServer = None
  form_gui = None

  def __init__(self, ps, form_gui):  
    self.pipeServer = ps
    self.form_gui = form_gui


  """
  callback function used by processing thread
  """
  def json_client_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("hrrm.py: JSONPipeVPNhrrmCallback json_client_callback\n")
    sys.stdout.write("hrrm.py: JSONPipeVPNhrrmCallback Data Received at Client: " + str(json_string) + "\n")

    try:
      dict_obj = json.loads(json_string)
      vartype     = dict_obj.get("type")
      varsubtype  = dict_obj.get("subtype")
      if(vartype == cn.P2P_IP_QUERY_NEIGHBORS_RESULT):
        if(varsubtype == cn.P2P_IP_FOUND):
          sys.stdout.write("hrrm.py: data returned by query neighbors\n")

          self.form_gui.neighbors_active_dict = {}
          the_list = dict_obj.get('params').get('result')

          if len(the_list) > 0 :
            self.form_gui.group_arq.p2p_online = True
            self.form_gui.window['btn_p2pipsatellite_getneighbors'].update(button_color=('black', 'green1'))
            self.form_gui.form_events.neighbors_cache.setTable(the_list, 2)
          else:
            self.form_gui.group_arq.p2p_online = False
            self.form_gui.window['btn_p2pipsatellite_getneighbors'].update(button_color=('black', 'red'))
            #self.form_gui.form_events.neighbors_cache.appendTable(the_list, 2)

          neighbors_table = self.form_gui.form_events.neighbors_cache.getTable()

          self.form_gui.window['tbl_selectedconnectionsp2pip'].update(values=neighbors_table)

          colors_table = []
          for list_item in the_list:
            sys.stdout.write("item = " + str(list_item[0]) + ":" + str(list_item[1]) + "\n")
            self.form_gui.neighbors_active_dict[str(list_item[0]) + ":" + str(list_item[1])] = True
          table = the_list 
          num_items = len(table)
          for line_index in range(num_items):
            ip_address = table[line_index][0]
            port       = int(table[line_index][1])
            key = (str(ip_address) + ":" + str(port))
            if key in self.form_gui.neighbors_active_dict:
              if self.form_gui.neighbors_active_dict[key] == True:
                colors_table.append((line_index, 'black', 'green1'))
              elif self.form_gui.neighbors_active_dict[key] == False:
                colors_table.append((line_index, 'black', 'red'))
          self.form_gui.window['tbl_selectedconnectionsp2pip'].update(row_colors=colors_table)
        else:
          sys.stdout.write("hrrm.py: no data returned by query neighbors\n")
          self.form_gui.group_arq.p2p_online = False
          self.form_gui.window['btn_p2pipsatellite_getneighbors'].update(button_color=('black', 'red'))


      if(vartype == cn.P2P_IP_QUERY_PING_RESULT):
        ping_address = dict_obj.get('params').get('ping_address')
        table = self.form_gui.getTable(self.form_gui.window['tbl_selectedconnectionsp2pip'], 2)
        num_items = len(table)
        sys.stdout.write("num items is: " + str(num_items) + "\n")
        colors_table = []
        for line_index in range(num_items):
          ip_address = table[line_index][0]
          port       = int(table[line_index][1])
          if(ip_address == ping_address[0] and str(port) == str(ping_address[1])):
            if(varsubtype == cn.P2P_IP_FOUND):
              self.form_gui.neighbors_active_dict[str(ip_address) + ":" + str(port)] = True
              colors_table.append((line_index, 'black', 'green1'))
            elif(varsubtype == cn.P2P_IP_NOT_FOUND):
              self.form_gui.neighbors_active_dict[str(ip_address) + ":" + str(port)] = False
              colors_table.append((line_index, 'black', 'red'))
          else:
            key = (str(ip_address) + ":" + str(port))
            if key in self.form_gui.neighbors_active_dict:
              if self.form_gui.neighbors_active_dict[key] == True:
                colors_table.append((line_index, 'black', 'green1'))
              elif self.form_gui.neighbors_active_dict[key] == False:
                colors_table.append((line_index, 'black', 'red'))
 

        sys.stdout.write("colors table: " + str(colors_table) + "\n")

        self.form_gui.window['tbl_selectedconnectionsp2pip'].update(values=table )
        self.form_gui.window['tbl_selectedconnectionsp2pip'].update(row_colors=colors_table)


        sys.stdout.write("hrrm: P2P_IP_QUERY_PING_RESULT\n")

      if(vartype == cn.P2P_IP_CONNECT_UDP):
        if(varsubtype == cn.P2P_IP_SUCCESS):
          sys.stdout.write("UDP Listen started successfully\n")
          self.form_gui.window['text_mainarea_p2pservicestarted'].Update(text_color='green1')

          self.form_gui.form_events.event_p2pCommandCommon(cn.P2P_IP_QUERY_NEIGHBORS, {})
          self.form_gui.form_events.event_p2pipsettings_connectstationmulti()

        elif(varsubtype == cn.P2P_IP_STOPPED):
          sys.stdout.write("UDP Service Stopped successfully\n")
          self.form_gui.window['text_mainarea_p2pservicestarted'].Update(text_color='red')

      if(vartype == cn.P2P_IP_QUERY_RESULT):
        if(varsubtype == cn.P2P_IP_FOUND):
          sys.stdout.write("QUERY RESULT received data\n")
          result_dict_obj = dict_obj.get('params').get('result')

          if(result_dict_obj != None and 'mailbox' in result_dict_obj ):
            for key in result_dict_obj['mailbox'].keys():
              sys.stdout.write("Retrieving message from id: " + str(result_dict_obj['mailbox'][key]) + "\n")

              exists = False
              address = self.form_gui.window['in_p2pipnode_ipaddr'].get()
              ID = key
              if( ID in self.form_gui.form_dictionary.inbox_file_dictionary_data):
                pages = self.form_gui.form_dictionary.inbox_file_dictionary_data.get(ID)
                page_zero = pages.get('0')
                get_verified  = page_zero.get('verified')
                if(get_verified == 'Verified'):
                  self.form_gui.debug.info_message("item exists in inbox")
                  exists = True
                else:
                  self.form_gui.debug.info_message("item does not exist in inbox")

              if(exists == False):
                mypipeclient = self.form_gui.getClientPipe()
                mypipeclient.p2pNodeCommand(cn.P2P_IP_GET_MSG, address, {'key':ID})

          elif(result_dict_obj != None and 'message' in result_dict_obj ):
            self.form_gui.debug.info_message("YAY message received")
            for key in result_dict_obj['message'].keys():
              sys.stdout.write("Retrieving message from id: " + str(result_dict_obj['message'][key]) + "\n")
              message = result_dict_obj['message'][key][1]['data']
              sys.stdout.write("Retrieved message: " + str(message) + "\n")

              self.form_gui.group_arq.saamfram.processIncomingMessage(message)
              self.form_gui.window['table_inbox_messages'].update(values=self.form_gui.group_arq.getMessageInbox() )
              self.form_gui.window['table_inbox_messages'].update(row_colors=self.form_gui.group_arq.getMessageInboxColors())
          elif(result_dict_obj != None and 'text' in result_dict_obj ):
            self.form_gui.debug.info_message("YAY text received")
            for key in result_dict_obj['text'].keys():
              sys.stdout.write("Retrieving text from id: " + str(result_dict_obj['text'][key]) + "\n")
              text = result_dict_obj['text'][key][1]['text']
              sys.stdout.write("Retrieved message: " + str(text) + "\n")
              self.form_gui.group_arq.saamfram.processIncomingMessageCommonExtended(text, cn.UNKNOWN_BOX, cn.P2PIP)

    except:
      sys.stdout.write("Exception in hrrm.py json_client_callback: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")

    self.form_gui.window['debug_window'].update(str(json_string) + "\n", append=True)
    return




class ChatDataCache(object):

  refresh_required = {}
  displayed_rows = {}
  chat_store = {}
  debug = db.Debug(cn.DEBUG_INFO)

  def __init__(self, group_arq):  
    sys.stdout.write("ChatDataCache: init\n")
    self.group_arq = group_arq

  def append(self, discussion_name, msgfrom, received_text, msgid, text_line_number, msgtype):
    sys.stdout.write("ChatDataCache: append\n")
    if discussion_name not in self.chat_store:
      self.chat_store[discussion_name] = OrderedDict()
      self.refresh_required[discussion_name] = True

    if (msgid + ':' + text_line_number) not in self.chat_store[discussion_name]:
      self.chat_store[discussion_name][msgid + ':' + text_line_number] = [msgfrom, received_text, msgid, msgtype]
      self.refresh_required[discussion_name] = True



  def getTableDelta(self, discussion_name, start_row, end_row):
    sys.stdout.write("ChatDataCache: getTableDelta\n")
    return self.getTable(discussion_name)[start_row:end_row]

  def getTable(self, discussion_name):
    sys.stdout.write("ChatDataCache: getTable\n")

    output_table = []
    try:
      if discussion_name in self.chat_store:
        dict_data = self.chat_store[discussion_name]
        for key in dict_data:
          msgfrom      = self.chat_store[discussion_name][key][0]
          rcvdtext     = self.chat_store[discussion_name][key][1]
          msgid        = self.chat_store[discussion_name][key][2]
          color_basis  = self.chat_store[discussion_name][key][3]
          output_table.append([msgfrom, rcvdtext, msgid, color_basis])

      sys.stdout.write("ChatDataCache: getTable output table: " + str(output_table) + "\n")
    except:
      self.debug.error_message("Exception in getTable: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return output_table

  def getTableColors(self, discussion_name):
    sys.stdout.write("ChatDataCache: getTableColors\n")

    output_table = []

    if discussion_name in self.chat_store:
      dict_data = self.chat_store[discussion_name]

      row_num = 0
      for key in dict_data:
        msgtype  = self.chat_store[discussion_name][key][3]

        if msgtype == cn.P2P_IP_CHAT_RCVD_FOR_ME:
          output_table.append([row_num, 'green1'])
        elif msgtype == cn.P2P_IP_CHAT_RCVD_FOR_OTHER:
          output_table.append([row_num, 'gray'])
        elif msgtype == cn.P2P_IP_CHAT_SENT:
          output_table.append([row_num, 'white'])

        row_num = row_num + 1

    sys.stdout.write("ChatDataCache: getTableColors output table: " + str(output_table) + "\n")

    return output_table

  def getSelectedDiscussion(self):
    table = self.group_arq.form_events.discussion_cache.getTable()
    line_data = self.group_arq.form_gui.window['table_chat_satellitediscussionname_plus_group'].get()
    self.debug.info_message("line_data is: " + str(line_data))
    if line_data != [] :
      line_index = int(self.group_arq.form_gui.window['table_chat_satellitediscussionname_plus_group'].get()[0])
      self.debug.info_message("line_index is: " + str(line_index))
      discname      = (table[line_index])[0]
      group_name    = (table[line_index])[1]
      discussion_name = str(discname + group_name.replace('@', '#') )

      self.debug.info_message("getSelectedDiscussion selected discussion: " + str(discussion_name) + "\n")
      return discussion_name

    self.debug.info_message("getSelectedDiscussion selected discussion: \n")
    return ''

  def refreshChatDisplay(self, force):

    if force == True:
      self.group_arq.form_gui.window['table_chat_received_messages_p2pip'].update('')

    discussion_name = self.getSelectedDiscussion()

    if discussion_name not in self.displayed_rows or force == True:
      delta_table = self.getTableDelta(discussion_name, 0, len(self.chat_store[discussion_name]))
    else:
      delta_table = self.getTableDelta(discussion_name, self.displayed_rows[discussion_name], len(self.chat_store[discussion_name]))
    self.displayed_rows[discussion_name] = len(self.chat_store[discussion_name])

    if discussion_name != '':
      if discussion_name not in self.refresh_required:
        self.refresh_required[discussion_name] = True

      if self.refresh_required[discussion_name] == True or force == True:
        self.debug.info_message("refreshChatDisplay refreshing data")

        for row in delta_table:
          string_row = f"{str(row[0]):<{20}}" + f"{str(row[1]):<{101}}" + f"{str(row[2]):<{30}}"
          color_basis = row[3]
          if color_basis == cn.P2P_IP_CHAT_SENT:
            self.group_arq.form_gui.window['table_chat_received_messages_p2pip'].print(string_row, text_color='black', background_color = 'white')
          elif color_basis == cn.P2P_IP_CHAT_RCVD_FOR_ME:
            self.group_arq.form_gui.window['table_chat_received_messages_p2pip'].print(string_row, text_color='black', background_color = 'green1')
          elif color_basis == cn.P2P_IP_CHAT_RCVD_FOR_OTHER:
            self.group_arq.form_gui.window['table_chat_received_messages_p2pip'].print(string_row, text_color='black', background_color = 'gray')

        self.refresh_required[discussion_name] = False
      else:
        self.debug.info_message("refreshChatDisplay not refreshing data")

 
def usage():
  sys.exit(2)


def guiThings(pipe, group_arq,dispatcher):
    dispatcher.setSaamfram(group_arq.saamfram)
    group_arq.form_events = dispatcher
    group_arq.form_dictionary.setFormEvents(dispatcher)
    group_arq.form_gui.setFormEvents(dispatcher)
    group_arq.form_gui.runReceive(group_arq, dispatcher)

    group_arq.form_gui.setVpnPipe_p2pNode(pipe)

def create_folders(instance_name):

    if (platform.system() == 'Windows'):
      appdata_folder = os.getenv('LOCALAPPDATA') 

      if(instance_name != ''):
        hrrm_appdata_folder = appdata_folder + '\HRRM' + "_" + instance_name
      else:
        hrrm_appdata_folder = appdata_folder + '\HRRM' 

      if(not os.path.exists(hrrm_appdata_folder)):
        os.chdir(appdata_folder)

        if(instance_name != ''):
          os.mkdir(('HRRM' + "_" + instance_name))
        else:
          os.mkdir(('HRRM'))

        os.chdir(hrrm_appdata_folder)
        os.mkdir('received_images')
        os.mkdir('received_files')
        os.mkdir('hrrm_files')
      else:
        os.chdir(hrrm_appdata_folder)
    else:
      appdata_folder = os.getenv('HOME') 

      if(instance_name != ''):
        hrrm_appdata_folder = appdata_folder + '/.HRRM' + "_" + instance_name
      else:
        hrrm_appdata_folder = appdata_folder + '/.HRRM'

      if(not os.path.exists(hrrm_appdata_folder)):
        os.chdir(appdata_folder)

        if(instance_name != ''):
          os.mkdir(('.HRRM' + "_" + instance_name))
        else:
          os.mkdir(('.HRRM'))

        os.chdir(hrrm_appdata_folder)
        os.mkdir('received_images')
        os.mkdir('received_files')
        os.mkdir('hrrm_files')
      else:
        os.chdir(hrrm_appdata_folder)
 
def main():

    instance_name = ''

    debug = db.Debug(cn.DEBUG_INFO)

    group_arq = NetGarq(debug)
    group_arq.form_gui = js8_form_gui.FormGui(group_arq, debug)
    group_arq.form_dictionary = js8_form_dictionary.FormDictionary(debug)
    group_arq.form_gui.setFormDictionary(group_arq.form_dictionary)
    group_arq.form_gui.setGroupArq(group_arq)
    group_arq.form_dictionary.setGroupArq(group_arq)
    group_arq.pipes = AppPipes(debug)

   
    mylongstring = "I am a very very long string of text that will be fragemnted into several sections. Each section will have its own tags." 
    frag_size = 10
    group_arq.addRecipientStation("WJ6XYZ")
    group_arq.addRecipientStation("WBZ546")
   
    group_arq.formdesigner_mode = False
    group_arq.include_gps = False
    group_arq.operating_mode = cn.FLDIGI

    group_arq.display_winlink = False

    fldigi_address  = '127.0.0.1'
    fldigi_port     = 7362
    js8call_address = '127.0.0.1'
    js8call_port    = 2442
    
    (opts, args) = getopt.getopt(sys.argv[1:], "h:g:f:o:d:j:i:s:e:l",
      ["help", "gps", "formdesigner", "opmode=", "fldigi=","js8call=", "instance=", "show=", "experimental=", 'listenonly='])
    rosterFile, macroFile = None, None
    for option, argval in opts:
      if (option in ("-h", "--help")):
        debug.info_message("main. usage")
        usage()

      elif (option in ("-g", "--gps")):
        debug.info_message("gps")
        group_arq.include_gps = True

      elif (option in ("-f", "--formdesigner")):
        debug.info_message("form designer only")
        group_arq.formdesigner_mode = True

      elif (option in ("-o", "--opmode")):
        debug.info_message("mode = " + argval)
        if(argval == "fldigi"):
          group_arq.operating_mode = cn.FLDIGI
        elif(argval == "js8call"):
          group_arq.operating_mode = cn.JS8CALL

      elif (option in ("-d", "--fldigi")):
        split_string = argval.split(':')
        fldigi_address = split_string[0]
        fldigi_port    = int(split_string[1])
        debug.info_message("fldigi address:port = " + fldigi_address + ":" + str(fldigi_port) )

      elif (option in ("-j", "--js8call")):
        split_string = argval.split(':')
        js8call_address = split_string[0]
        js8call_port = int(split_string[1])
        debug.info_message("js8 call address:port = " + js8call_address + ":" + str(js8call_port) )

      elif (option in ("-i", "--instance")):
        debug.info_message("instance = " + argval)
        instance_name = argval

      elif (option in ("-s", "--show")):
        debug.info_message("show = " + argval)
        if(argval == "winlink"):
          group_arq.display_winlink = True

      elif (option in ("-e", "--experimental")):
        debug.info_message("experimental = " + argval)
        if(argval == "include_template"):
          group_arq.include_templates = True

      elif (option in ("-l", "--listenonly")):
        debug.info_message("listenonly = " + argval)
        if(argval == "true"):
          group_arq.listenonly = True

    group_arq.include_experimental = False

    create_folders(instance_name)
    
    if(group_arq.include_gps == True):
      try:
        group_arq.getMyGPSLocationFromDongle()
        group_arq.getMyGPSSatelliteInfo()
      except:
        debug.error_message("Exception in main. Unable to load GPS: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    js = group_arq.form_dictionary.readMainDictionaryFromFile("saamcom_save_data.txt")

    params = js.get("params")
    group_arq.form_gui.main_heading_background_clr     = params.get('FormHeadingClr')
    group_arq.form_gui.sub_heading_background_clr      = params.get('FormSubHeadingClr')
    group_arq.form_gui.numbered_section_background_clr = params.get('NumberedSectionClr')
    group_arq.form_gui.table_header_background_clr     = params.get('TableHeaderClr')

    group_arq.form_gui.main_heading_text_clr     = params.get('FormHeadingTextClr')
    group_arq.form_gui.sub_heading_text_clr      = params.get('FormSubHeadingTextClr')
    group_arq.form_gui.numbered_section_text_clr = params.get('NumberedSectionTextClr')
    group_arq.form_gui.table_header_text_clr     = params.get('TableHeaderTextClr')

    debug.info_message("operating mode is: " + str(group_arq.operating_mode))

    if(group_arq.operating_mode == cn.FLDIGI):
      debug.info_message("processing for fldigi")
      try:
        group_arq.setDebug(debug)
        """ create the rig 1 fldigi instance and give it a name """
        fldigiClient = fldigi_client.FLDIGI_Client(debug, 'kenwood')
        group_arq.fldigiclient = fldigiClient
        server = (fldigi_address, fldigi_port)
        fldigiClient.connect(server)
        t1 = threading.Thread(target=fldigiClient.run, args=())
        t1.start()

        sfram = SAAMFRAM_fldigi(debug, group_arq, group_arq.form_dictionary, 'kenwood', '', group_arq.js8client, None, group_arq.fldigiclient, None, group_arq.form_gui, js)

        debug.info_message("sfram is :" + str(sfram))

        group_arq.saamfram = sfram
        fldigiClient.setCallback(sfram.fldigi_callback)
        group_arq.saamfram.setTxRig('Rig 1 - Fldigi')
        group_arq.saamfram.createAndSetRxRig('Rig 1 - Fldigi')

        sfram.switchToFldigiMode()


      except:
        debug.error_message("Exception in main. FLDIGI unable to connect:" + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    if(group_arq.operating_mode == cn.JS8CALL):
      debug.info_message("processing for js8call")
      try:
        group_arq.setDebug(debug)
        js8Client = JS8_Client.JS8_Client(debug)
        group_arq.js8client = js8Client
        server = (js8call_address, js8call_port)
        js8Client.connect(server)
        t1 = threading.Thread(target=js8Client.run, args=())
        t1.start()

        sfram = SAAMFRAM_js8(debug, group_arq, group_arq.form_dictionary, 'kenwood', '', group_arq.js8client, None, group_arq.fldigiclient, None, group_arq.form_gui, js)
        group_arq.saamfram = sfram
        js8Client.setCallback(sfram.js8_callback)
        js8Client.setRigName('Rig1')
        group_arq.saamfram.setTxRig('Rig 1 - JS8')

        sfram.switchToJS8Mode()

      except:
        debug.error_message("Exception in main. JS8Call unable to connect: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    table = group_arq.form_gui.createTableFromNames()
    debug.verbose_message("TABLE: " + str(table) )
    reverse_lookup = group_arq.form_gui.createReverseLookup()
    debug.verbose_message("REVERSE LOOKUP: " + str(reverse_lookup) )
    group_arq.form_gui.createFieldLookup()
    group_arq.form_gui.table_lookup.append('-')

    group_arq.form_dictionary.readInboxDictFromFile('inbox.msg')
    group_arq.form_dictionary.readOutboxDictFromFile('outbox.msg')
    group_arq.form_dictionary.readSentDictFromFile('sentbox.msg')
    group_arq.form_dictionary.readRelayboxDictFromFile('relaybox.msg')

    group_arq.form_dictionary.readPeerstnDictFromFile('peerstn.sav')
    group_arq.form_dictionary.readRelaystnDictFromFile('relaystn.sav')
    group_arq.form_dictionary.readPeerstnDictFromFile('p2pipstn.sav')

    window = group_arq.form_gui.createMainTabbedWindow(mylongstring, js)

    """ create the main gui controls event handler """
    dispatcher = js8_form_events.ReceiveControlsProc(group_arq, group_arq.form_gui, group_arq.form_dictionary, debug)


    mypipeClient = JSONPipeVPNhrrm('yaesu_radio', ('127.0.0.1', 2598), cn.JSON_PIPE_CLIENT, group_arq.form_gui)
    t2 = threading.Thread(target=guiThings, args=(mypipeClient,group_arq,dispatcher,))
    t2.start()

    group_arq.form_gui.setClientPipe(mypipeClient)

    t1 = threading.Thread(target=mypipeClient.run, args=())
    t1.start()
    mycallbackClient = JSONPipeVPNhrrmCallback(mypipeClient, group_arq.form_gui)
    mypipeClient.setCallback(mycallbackClient.json_client_callback)



if __name__ == '__main__':
    main()




