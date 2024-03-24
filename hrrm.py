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
    self.selected_relay_stations = []
    self.chat_data = []
    self.selected_template = 'General Message'
    self.debug = debug

    #self.active_station_checklist = []
    
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

  def clearSelectedStations(self):
    self.selected_stations = []	  
    return

  def addSelectedStation(self, station, num, grid, connect, rig, modulation, snr, ID):

    self.debug.info_message("addSelectedStation" )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign        = lineitem[0]
      prev_ID         = lineitem[7]
      if(callsign == station):
        """ test timestamp in here"""
        prev_timestamp_string = prev_ID.split('_',1)[1]
        prev_inttime = ((int(prev_timestamp_string,36))/100.0)

        timestamp_string = ID.split('_',1)[1]
        inttime = ((int(timestamp_string,36))/100.0)

        """ if prev station timestamp is more recent then ignore add...best guess within limitation of encoding!"""
        if(prev_inttime > inttime):
          return self.selected_stations
        else:
          self.selected_stations.remove(lineitem)
          self.selected_stations.append([station, num, grid, connect, rig, modulation, snr, ID])
          return self.selected_stations

    self.selected_stations.append([station, num, grid, connect, rig, modulation, snr, ID])
    return self.selected_stations


  def getSelectedStationIndex(self, station):
    self.debug.info_message("getSelectedStationIndex " )

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      if(callsign == station):
        return x

    return -1

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
        connect    = lineitem[3]
        rig        = lineitem[4]
        modulation = lineitem[5]
        last_heard = lineitem[7]

        self.selected_stations[x] = [callsign, num, grid, connect, rig, modulation, snr, last_heard]

        return 

  
  def getSelectedStations(self):
    return self.selected_stations

  def getSelectedStationsColors(self):
    selected_colors = []

    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      selected = lineitem[3]
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
    selected   = lineitem[3]
    rig        = lineitem[4]
    modulation = lineitem[5]
    snr        = lineitem[6]
    last_heard = lineitem[7]

    if(selected == 'X'):
      selected = ' '
    else:
      selected = 'X'
    self.selected_stations[index] = [callsign, num, grid, selected, rig, modulation, snr, last_heard]


  def selectSelectedStations(self, index):

    lineitem   = self.selected_stations[index]
    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    selected   = lineitem[3]
    rig        = lineitem[4]
    modulation = lineitem[5]
    snr        = lineitem[6]
    last_heard = lineitem[7]

    selected = 'X'
    self.selected_stations[index] = [callsign, num, grid, selected, rig, modulation, snr, last_heard]


  def getConnectToString(self):

    selected_callsigns = ''
    for x in range (len(self.selected_stations)):
      lineitem = self.selected_stations[x]
      callsign = lineitem[0]
      selected = lineitem[3]

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
      #msgto = lineitem[1].split(';')
      #for z in range (len(msgto)):
      #  if(msgto[z] in self.group_arq.active_station_checklist):
      #    msgconf = lineitem[7].split(';')
      #    found = False
      #    for y in range (len(msgconf)):
      #      if(msgconf[y] in self.group_arq.active_station_checklist):
      #        found = True
      #    if(found == False):
      #      selected_colors.append([x, 'green1'])
      #      flash_relay_button = True
      #      self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_relay', True)
      #      break
      #self.messages_relaybox[x] = [msgfrom, msgto, subject, timestamp, priority, msgtype, msgid, conf_rcvd, frag_size, verified]


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
    #elif(self.operating_mode == cn.JS8CALL or self.operating_mode == cn.JSDIGI):
    #  data = self.js8client.getMsg()
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
   
 
def usage():
  sys.exit(2)
 
 
def main():

    debug = db.Debug(cn.DEBUG_INFO)

    if (platform.system() == 'Windows'):
      appdata_folder = os.getenv('LOCALAPPDATA') 
      hrrm_appdata_folder = appdata_folder + '\HRRM'
      if(not os.path.exists(hrrm_appdata_folder)):
        os.chdir(appdata_folder)
        os.mkdir('HRRM')
        os.chdir(hrrm_appdata_folder)
        os.mkdir('received_images')
        os.mkdir('received_files')
        os.mkdir('hrrm_files')
      else:
        os.chdir(hrrm_appdata_folder)
    else:
      appdata_folder = os.getenv('HOME') 
      hrrm_appdata_folder = appdata_folder + '/.HRRM'
      if(not os.path.exists(hrrm_appdata_folder)):
        os.chdir(appdata_folder)
        os.mkdir('.HRRM')
        os.chdir(hrrm_appdata_folder)
        os.mkdir('received_images')
        os.mkdir('received_files')
        os.mkdir('hrrm_files')
      else:
        os.chdir(hrrm_appdata_folder)

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

    fldigi_address  = '127.0.0.1'
    fldigi_port     = 7362
    js8call_address = '127.0.0.1'
    js8call_port    = 2442
    
    (opts, args) = getopt.getopt(sys.argv[1:], "h:g:f:o:d:j",
      ["help", "gps", "formdesigner", "opmode=", "fldigi=","js8call="])
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
        elif(argval == "jsdigi"):
          group_arq.operating_mode = cn.JSDIGI

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

    if(group_arq.operating_mode == cn.FLDIGI or group_arq.operating_mode == cn.JSDIGI):
      try:
        group_arq.setDebug(debug)
        """ create the rig 1 fldigi instance and give it a name """
        fldigiClient = fldigi_client.FLDIGI_Client(debug, 'kenwood')
        group_arq.fldigiclient = fldigiClient
        server = (fldigi_address, fldigi_port)
        fldigiClient.connect(server)
        t1 = threading.Thread(target=fldigiClient.run, args=())
        t1.start()

        sfram = saamfram.SAAMFRAM(debug, group_arq, group_arq.form_dictionary, 'kenwood', '', group_arq.js8client, None, group_arq.fldigiclient, None, group_arq.form_gui, js)
        group_arq.saamfram = sfram
        fldigiClient.setCallback(sfram.fldigi_callback)
        group_arq.saamfram.setTxRig('Rig 1 - Fldigi')
        group_arq.saamfram.createAndSetRxRig('Rig 1 - Fldigi')

        sfram.switchToFldigiMode()


      except:
        debug.error_message("Exception in main. FLDIGI unable to connect:" + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    if(group_arq.operating_mode == cn.JS8CALL or group_arq.operating_mode == cn.JSDIGI):
      try:
        group_arq.setDebug(debug)
        js8Client = JS8_Client.JS8_Client(debug)
        group_arq.js8client = js8Client
        server = (js8call_address, js8call_port)
        js8Client.connect(server)
        t1 = threading.Thread(target=js8Client.run, args=())
        t1.start()

        sfram = saamfram.SAAMFRAM(debug, group_arq, group_arq.form_dictionary, 'kenwood', '', group_arq.js8client, None, group_arq.fldigiclient, None, group_arq.form_gui, js)
        group_arq.saamfram = sfram
        js8Client.setCallback(sfram.js8_callback)
        js8Client.setRigName('Rig1')
        group_arq.saamfram.setTxRig('Rig 1 - JS8')

        sfram.switchToJS8Mode()

      except:
        debug.error_message("Exception in main. JS8Call unable to connect: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    table = group_arq.form_gui.createTableFromNames()
    debug.info_message("TABLE: " + str(table) )
    reverse_lookup = group_arq.form_gui.createReverseLookup()
    debug.info_message("REVERSE LOOKUP: " + str(reverse_lookup) )
    group_arq.form_gui.createFieldLookup()
    group_arq.form_gui.table_lookup.append('-')

    group_arq.form_dictionary.readInboxDictFromFile('inbox.msg')
    group_arq.form_dictionary.readOutboxDictFromFile('outbox.msg')
    group_arq.form_dictionary.readSentDictFromFile('sentbox.msg')
    group_arq.form_dictionary.readRelayboxDictFromFile('relaybox.msg')

    group_arq.form_dictionary.readPeerstnDictFromFile('peerstn.sav')
    group_arq.form_dictionary.readRelaystnDictFromFile('relaystn.sav')

    window = group_arq.form_gui.createMainTabbedWindow(mylongstring, js)

    """ create the main gui controls event handler """
    dispatcher = js8_form_events.ReceiveControlsProc(group_arq, group_arq.form_gui, group_arq.form_dictionary, debug)

    dispatcher.setSaamfram(group_arq.saamfram)

    group_arq.form_events = dispatcher
    group_arq.form_dictionary.setFormEvents(dispatcher)
    group_arq.form_gui.setFormEvents(dispatcher)

    group_arq.form_gui.runReceive(group_arq, dispatcher)

if __name__ == '__main__':
    main()




