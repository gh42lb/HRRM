#!/usr/bin/env python
import sys
import constant as cn
import string
import struct

import json
import threading
import os
import platform
import calendar
import xmlrpc.client

import base64
import bz2 as bz2

import debug as db
import JS8_Client
import fldigi_client
import getopt
import random

import js8_form_gui
import js8_form_events
import js8_form_dictionary
import saam_parser

from PIL import Image

from datetime import datetime, timedelta

from crc import CrcCalculator, Configuration

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



"""
This class handles communicating back and forth with JS8 Call application
"""
class SAAMFRAM(object):

  checksum_value=0XFFFF


  def __init__(self, debug, group_arq, form_dictionary, rig1, rig2, js8client_rig1, js8client_rig2, fldigiclient_rig1, fldigiclient_rig2, form_gui, js):

    if(group_arq.operating_mode == cn.JS8CALL):
      self.max_frag_retransmits = 5
      self.max_qry_acknack_retransmits = 5
    else:
      self.max_frag_retransmits = 10
      self.max_qry_acknack_retransmits = 2

    self.delimiter_char = cn.DELIMETER_CHAR
    self.group_arq = group_arq
    self.form_dictionary = form_dictionary
    self.js8client = js8client_rig1
    self.fldigiclient = fldigiclient_rig1
    self.debug = debug
    self.form_gui = form_gui
    self.recipient_stations_str = 'WH6ABC;WH6DEF;WH6GHI'
    self.announce = ''
    self.pre_message = 'WH6GGO: @HINET ' + self.announce
    self.groupname = "@HINET"
    self.chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    self.js8_tx_speed = 'TURBO'
    self.tx_mode = ''
    self.last_selected_channel_view_line = -1
    self.main_params = js

    self.last_displayed_debug_message = ''

    self.base32_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUV"

    self.ignore_processing = False
    self.eom_marker = cn.EOM_FLDIGI

    self.rig_channel_dictionary = {}
    self.active_rig = ''

    self.mycall_from_file = js.get("params").get('CallSign')

    self.fldigi_modes = ''
    self.debug.info_message("getting fldigi modes\n")
    if(self.fldigiclient != None):
      self.fldigi_modes = self.fldigiclient.getModes()
      self.debug.info_message("FLDIGI MODES: " + self.fldigi_modes )

    self.saam_parser = saam_parser.SaamParser(debug, group_arq, form_dictionary, rig1, rig2, js8client_rig1, js8client_rig2, fldigiclient_rig1, fldigiclient_rig2, form_gui, self)
    self.command_strings = 'COMMAND_NONE,COMMAND_SAAM,COMMAND_QRY_SAAM,COMMAND_QRY_RELAY,COMMAND_RELAY,COMMAND_CONF,COMMAND_RDY,COMMAND_QRY_RDY,COMMAND_SMT,COMMAND_EMT,COMMAND_CHKSUM'.split(',')
    self.comm_strings = 'COMM_NONE,COMM_LISTEN,COMM_RECEIVING,COMM_QUEUED_TXMSG,COMM_SENDING,COMM_AWAIT_REPLY,COMM_AWAIT_ACKNACK,COMM_AWAIT_RESEND'.split(',')

  def getSenderCall(self):
    if(self.form_gui.window != None and self.form_gui.form_events.window_initialized == True and self.group_arq.formdesigner_mode == False):
      return self.form_gui.window['in_inbox_listentostation'].get().strip().upper()
    else:
      return '' 

  def getMyCall(self):
    if(self.form_gui.window != None and self.form_gui.form_events.window_initialized == True):
      return self.form_gui.window['input_myinfo_callsign'].get().strip().upper()
    else:
      return '' 

  def getMyGroup(self):
    if(self.form_gui.window != None and self.form_gui.form_events.window_initialized == True):
      return self.form_gui.window['input_myinfo_group_name'].get().strip().upper()
    else:
      return '' 

  def inSession(self):
    if(self.getInSession(self.tx_rig, self.tx_channel) == True or self.getInSession(self.active_rig, self.active_channel) == True):
      return True
    else: 
      return False

  def switchToJS8Mode(self):
    self.group_arq.send_mode_rig1 = cn.SEND_JS8CALL
    self.tx_mode = 'JS8CALL'
    self.eom_marker = cn.EOM_JS8
    return

  def switchToFldigiMode(self):
    self.group_arq.send_mode_rig1 = cn.SEND_FLDIGI
    self.tx_mode = 'FLDIGI'
    self.eom_marker = cn.EOM_FLDIGI
    return

  def updateChannelView(self, values):
    line_index = -1
    garq_stations = self.group_arq.getGarqStations()
    if(values != None):
      line_index = int(values['tbl_compose_stationcapabilities'][0])
      self.last_selected_channel_view_line = line_index
      line_item = garq_stations[line_index]
      rigname = line_item[0]
      channel_name = line_item[1]
    elif(self.last_selected_channel_view_line != -1):
      line_index = self.last_selected_channel_view_line
      line_item = garq_stations[line_index]
      rigname = line_item[0]
      channel_name = line_item[1]
    else:
      return ''

    text = 'Correct Frames:   ' + str(self.getCorrectFrames(rigname, channel_name)) + '\n'
    text = text+ 'Received:         ' + str(self.getRcvString(rigname, channel_name)) + '\n'
    text = text+ 'Comm Status:      ' + str(self.comm_strings[self.getCommStatus(rigname, channel_name)]) + '\n'
    text = text+ 'Expected Reply:   ' + str(self.getExpectedReply(rigname, channel_name)) + '\n'
    text = text+ 'In Session:       ' + str(self.getInSession(rigname, channel_name)) + '\n'
    text = text+ 'Num Fragments:    ' + str(self.getNumFragments(rigname, channel_name)) + '\n'
    text = text+ 'Sender Callsign:  ' + str(self.getSenderCallsign(rigname, channel_name)) + '\n'
    text = text+ 'Message:          ' + str(self.getMessage(rigname, channel_name)) + '\n'
    callsign = self.getChannelCallsign(rigname, channel_name)
    text = text+ 'Channel Callsign: ' + str(callsign) + '\n'

    frame_rcv_time = str(self.getFrameRcvTime(rigname, channel_name)).split('.')[0]
    text2 = 'Received Strings:      ' + str(self.getReceivedStrings(rigname, channel_name) ) + '\n'
    text2 = text2+ 'Frame Rcv Time:        ' + str(frame_rcv_time) + '\n'
    text2 = text2+ 'EOM Received:          ' + str(self.getEOMReceived(rigname, channel_name)) + '\n'
    text2 = text2+ 'AckNack Code:          ' + str(self.getAckNackCode(rigname, channel_name)) + '\n'
    text2 = text2+ 'Recipient Stations:    ' + str(self.getRecipientStations(rigname, channel_name)) + '\n'
    text2 = text2+ 'Frame Timing Seconds:  ' + str(self.getFrameTimingSeconds(rigname, channel_name)) + '\n'
    text2 = text2+ 'Nack Retransmit Count: ' + str(self.getQryAcknackRetransmitCount(rigname, channel_name)) + '\n'
    text2 = text2+ 'Retransmit Count:      ' + str(self.getRetransmitCount(rigname, channel_name)) + '\n'

    self.form_gui.window['ml_mainwindow_textarea_1'].update(value=text)
    self.form_gui.window['ml_mainwindow_textarea_2'].update(value=text2)

    return callsign, channel_name


  def createPreMessagePost(self, message):
    return 'post(' + message + ')'

  #this used to passively request message via relay stations
  def createPreMessageReqm(self):
    self.debug.info_message("CREATE PRE MSG REQM\n")
    #FIXME hardcoded

    from_callsign = self.getMyCall()
    msgid = self.getEncodeUniqueId(from_callsign)

    message = 'REQM(' + msgid   
    self.debug.info_message("LOC 2\n")
    checksum = self.getChecksum(msgid)
    self.debug.info_message("FINISH CREATE PRE MSG REQM\n")
    return message + ',' + checksum +  ')'


  #this used to confirm that message has been received by its intended recipient
  def createPreMessageConf(self):
    self.debug.info_message("CREATE PRE MSG CONF\n")
    #FIXME hardcoded

    from_callsign = self.getMyCall()
    msgid = self.getEncodeUniqueId(from_callsign)

    message = 'CONF(' + msgid   
    self.debug.info_message("LOC 2\n")
    checksum = self.getChecksum(msgid)
    self.debug.info_message("FINISH CREATE PRE MSG conf\n")
    return message + ',' + checksum +  ')'

  def createPreMessageBeac(self):
    self.debug.info_message("CREATE PRE MSG BEAC\n")
    #FIXME hardcoded

    from_callsign = self.getMyCall()
    msgid = self.getEncodeUniqueId(from_callsign)
    grid_square = self.form_gui.window['input_myinfo_gridsquare'].get()

    hop_count = '2'

    self.debug.info_message("LOC 1\n")
    message = 'BEAC(' + msgid + ',' + grid_square + ',' + hop_count 
    self.debug.info_message("LOC 2\n")
    checksum = self.getChecksum(msgid + ',' + grid_square + ',' + hop_count)
    self.debug.info_message("FINISH CREATE PRE MSG BEAC\n")
    return message + ',' + checksum +  ')'

  def createPreMessageDataFlecBeac(self, msgid, grid_square, hop_count):
    self.debug.info_message("createPreMessageDataFlecBeac")
    message = 'BEAC(' + msgid + ',' + grid_square + ',' + hop_count 
    checksum = self.getChecksum(msgid + ',' + grid_square + ',' + hop_count)
    return message + ',' + checksum +  ')'

  """ This is a non-directed data fleck"""
  def createPreMessageInfoGRIDDataFlec(self, msgid, grid_square):
    self.debug.info_message("createPreMessageInfoGRIDDataFlec")
    message = 'INFO(GRID,' + grid_square + ','+ msgid  
    checksum = self.getChecksum('GRID,' + grid_square + ','+ msgid)
    return message + ',' + checksum +  ')'

  """ This is a directed data fleck"""
  def createPreMessageInfoSNRDataFlec(self, snr):
    self.debug.info_message("createPreMessageInfoSNRDataFlec")
    message = 'INFO(SNR,' + snr
    checksum = self.getChecksum(snr)
    return message + ',' + checksum +  ')'

  def createPreMessagePend(self):

    self.debug.info_message("CREATE PRE MSG PEND\n")

    items = self.group_arq.getMessageOutbox()

    if(items == []):
      return ''

    selected_item = random.choice(items)
    to_list  = selected_item[1]
    priority = selected_item[4]
    msgid    = selected_item[6]

    """ give additional wight to higher priority messages"""
    stop = False
    for x in range (3):
      if(priority == 'Low' and stop == False):
        selected_item = random.choice(items)
        to_list  = selected_item[1]
        priority = selected_item[4]
        msgid    = selected_item[6]
      else:
        stop = True

    """ give additional wight to higher priority messages"""
    stop = False
    for x in range (3):
      if(priority == 'Medium' and stop == False):
        selected_item = random.choice(items)
        to_list  = selected_item[1]
        priority = selected_item[4]
        msgid    = selected_item[6]
      else:
        stop = True

    message = 'PEND(' + msgid + ',' + to_list 

    checksum = self.getChecksum(msgid + ',' + to_list)

    self.debug.info_message("FINISH CREATE PRE MSG PEND\n")

    return message + ',' + checksum +  ')'

  def createPreMessageRelay(self):

    items = self.group_arq.getMessageRelaybox()

    selected_item = random.choice(items)
    to_list  = selected_item[1]
    priority = selected_item[4]
    msgid    = selected_item[6]

    """ give additional wight to higher priority messages"""
    stop = False
    for x in range (3):
      if(priority == 'Low' and stop == False):
        selected_item = random.choice(items)
        to_list  = selected_item[1]
        priority = selected_item[4]
        msgid    = selected_item[6]
      else:
        stop = True

    """ give additional wight to higher priority messages"""
    stop = False
    for x in range (3):
      if(priority == 'Medium' and stop == False):
        selected_item = random.choice(items)
        to_list  = selected_item[1]
        priority = selected_item[4]
        msgid    = selected_item[6]
      else:
        stop = True

    message = 'relay(' + msgid + ',' + to_list + ',' + priority + ')'

    return message


  """
  to avoid unnecessary complexity, assume a worst case 8 bit character size for CRC calculations
  """
  def calcFragmentCRC(self, string):
    if(len(string)<=60):
      return self.calcTwoDigitCRCShort(string)
    elif(len(string)<=120):
      return self.calcTwoDigitCRCLong(string)
    else:
      return self.calcThreeDigitCRC(string)

  """ always use a 20 bit / 4 digit CRC for end of message checksum"""
  def calcEOMCRC(self, string):
    return self.calcFourDigitCRC(string)

  """
  CRC calculation uses 5 bit nibbles in base 32 so two digits is 10 bits
  This is used for the short fragments 10 thru 60 characters
  0x247 polynomial protects up to 501 bit data word (62 x 8 bit characters) length at HD=4
  """
  def calcTwoDigitCRCShort(self, string):
    return self.calcCRC(10, 0x247, string)

  """
  CRC calculation uses 5 bit nibbles in base 32 so two digits is 10 bits
  This is used for the longer fragments 70 thru 120 characters
  0x327 polynomial protects up to 1013 bit data word (126 x 8 bit characters) length at HD=3
  """
  def calcTwoDigitCRCLong(self, string):
    return self.calcCRC(10, 0x327, string)

  """
  CRC calculation uses 5 bit nibbles in base 32 so three digits is 15 bits
  0x4306 polynomial protects up to 16368 bit data word (2046 x 8 bit characters) length at HD=4
  this is used for longer fragments and end of message checksum for messages <= 2046 characters
  """
  def calcThreeDigitCRC(self, string):
    return self.calcCRC(15, 0x4306, string)

  """
  CRC calculation uses 5 bit nibbles in base 32 so four digits is 20 bits
  0xc1acf polynomial protects up to 524267 bit data word (65533 x 8 bit characters) length at HD=4
  this is used for end of message checksum for messages > 2046 characters
  """
  def calcFourDigitCRC(self, string):
    return self.calcCRC(20, 0xc1acf, string)


  def calcCRC(self, width, poly, string):

    #self.debug.info_message('calcCRC for string: ' + string)
    self.debug.info_message('calcCRC')

    data = bytes(string,"ascii")

    init_value=0x00
    final_xor_value=0x00
    reverse_input=False
    reverse_output=False

    configuration = Configuration(width, poly, init_value, final_xor_value, reverse_input, reverse_output)

    use_table = True
    crc_calculator = CrcCalculator(configuration, use_table)

    checksum = crc_calculator.calculate_checksum(data)
    self.debug.info_message(str(checksum))

    if(width == 10):
      high, low = checksum >> 5, checksum & 0x1F
      self.debug.info_message('10 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[low]
    elif(width == 15):
      high, mid, low = checksum >> 10, (checksum >> 5) & 0x1F, checksum & 0x1F
      self.debug.info_message('15 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[mid] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[mid] + self.base32_chars[low]
    elif(width == 20):
      high, mid_high, mid_low, low = checksum >> 15, (checksum >> 10) & 0x1F, (checksum >> 5) & 0x1F, checksum & 0x1F
      self.debug.info_message('20 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[mid_high] + self.base32_chars[mid_low] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[mid_high] + self.base32_chars[mid_low] + self.base32_chars[low]

    return ''

  def getRunLengthEncode(self, message):
    complete_outer = False

    find_it = cn.DELIMETER_CHAR + cn.DELIMETER_CHAR

    self.debug.info_message("RUN LENGTH ENCODE\n")

    while(complete_outer == False):
      inner_count = 2
      complete_inner = False
      while(complete_inner == False):
        if( find_it in message):
          message = message.replace(find_it, cn.ESCAPE_CHAR + str(inner_count) + cn.DELIMETER_CHAR,1 )
          find_it = cn.ESCAPE_CHAR + str(inner_count) + cn.DELIMETER_CHAR + cn.DELIMETER_CHAR
          inner_count = inner_count + 1
        else:
          complete_inner = True

      find_it = cn.DELIMETER_CHAR + cn.DELIMETER_CHAR
      if( find_it not in message):
        complete_outer = True

    """ replace the 2 character ones with the original as it is shorter."""
    message = message.replace(cn.ESCAPE_CHAR + '2' + cn.DELIMETER_CHAR, cn.DELIMETER_CHAR + cn.DELIMETER_CHAR)

    return message

  def getEncodeEscapes(self, message):

    try:
      """ process the forward slahs first"""
      message = message.replace('/','//')

      if (platform.system() == 'Windows'):
        message = message.replace('\r\n','/N')
        message = message.replace('\r','/N')
        message = message.replace('\n','/N')
      else:
        message = message.replace('\r','/N')
        message = message.replace('\n','/N')

      message = message.replace('[','/A')
      message = message.replace(']','/B')
      message = message.replace('{','/C')
      message = message.replace('}','/D')
      #message = message.replace('~','/F')

    except:
      self.debug.error_message("Exception in getEncodeEscapes: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return message


  """ combined with the RLE decode processing"""
  def getDecodeEscapes(self, message):

    self.debug.info_message("getDecodeEscapes")

    string_out = ''
    char_count = 0
    message_len = len(message)
    while char_count < message_len:
      if(char_count+1 < message_len):
        if(message[char_count] == '/'):
          """ test to see if this is an escape sequence"""
          if(message[char_count+1] == 'D'):
            string_out = string_out + '}'
            char_count = char_count + 2
          elif(message[char_count+1] == 'C'):
            string_out = string_out + '{'
            char_count = char_count + 2
          elif(message[char_count+1] == 'B'):
            string_out = string_out + ']'
            char_count = char_count + 2
          elif(message[char_count+1] == 'A'):
            string_out = string_out + '['
            char_count = char_count + 2
          elif(message[char_count+1] == 'N'):
            if (platform.system() == 'Windows'):
              string_out = string_out + '\r\n'
            else:
              string_out = string_out + '\n'
            char_count = char_count + 2
          elif(message[char_count+1] == '/'):
            string_out = string_out + '/'
            char_count = char_count + 2
          else:
            """ make sure this is an RLE escape sequence """
            if(message[char_count+1].isdigit()):
              if(message[char_count+2].isdigit()):
                if(message[char_count+3].isdigit()):
                  """ four digit RLE codes and up not supported"""
                  if(message[char_count+4].isdigit()):
                    self.debug.info_message("do nothing")
                  elif(message[char_count+4] == cn.DELIMETER_CHAR):
                    """ process triple digit RLE code"""
                    string_out = string_out + (cn.DELIMETER_CHAR * ((int(message[char_count+1])*100) + (int(message[char_count+2])*10)+ (int(message[char_count+3]))) )
                    char_count = char_count + 5

                elif(message[char_count+3] == cn.DELIMETER_CHAR):
                  """ process double digit RLE code"""
                  string_out = string_out + (cn.DELIMETER_CHAR * ((int(message[char_count+1])*10) + (int(message[char_count+2]))) )
                  char_count = char_count + 4

              elif(message[char_count+2] == cn.DELIMETER_CHAR):
                """ process single digit RLE code"""
                string_out = string_out + (cn.DELIMETER_CHAR * int(message[char_count+1]) )
                char_count = char_count + 3
            else:
              string_out = string_out + message[char_count]
              char_count = char_count + 1

        else:
          string_out = string_out + message[char_count]
          char_count = char_count + 1
      else:
        string_out = string_out + message[char_count]
        char_count = char_count + 1

    message = string_out
    self.debug.info_message("completed getDecodeEscapes. unescaped message: " + str(message) )

    return message

  def createAndSetRxRig(self, rig):
    self.debug.info_message("CREATE AND SET RX RIG\n")
    self.active_rig = 'Rig1'
    self.active_channel = self.addChannelItem('Rig1', 'FLDIGI', 'Fldigi RX', '1500', '', '')

    self.debug.info_message("active channel: " + self.active_channel )
    return

  def setTxRig(self, txrig):

    callsign = ''

    if(txrig == 'Rig 1 - JS8'):
      tx_rig = 'Rig1'
      self.tx_mode = 'JS8CALL'
      self.js8_tx_speed = 'TURBO'

      if(self.doesRigItemExist(tx_rig) == False):
        self.createRigItem(tx_rig, self.fldigiclient, self.js8client)
        self.tx_rig = tx_rig

      if(self.queryChannelItem(tx_rig, self.tx_mode, self.js8_tx_speed, 'TX',) == False):
        tx_channel = self.addChannelItem(tx_rig, self.tx_mode, self.js8_tx_speed, 'TX', '', callsign)
        self.tx_channel = tx_channel

    elif(txrig == 'Rig 1 - Fldigi'):
      self.debug.info_message("SET TX RIG: " + txrig )
      tx_rig = 'Rig1'
      self.tx_mode = 'FLDIGI'
      self.tx_mode_name = 'Fldigi TX'

      if(self.doesRigItemExist(tx_rig) == False):
        self.createRigItem(tx_rig, self.fldigiclient, self.js8client)
        self.tx_rig = tx_rig

      if(self.queryChannelItem(tx_rig, self.tx_mode, self.tx_mode_name, 'TX',) == False):
        tx_channel = self.addChannelItem(tx_rig, self.tx_mode, self.tx_mode_name, 'TX', '', callsign)
        self.tx_channel = tx_channel

    elif(txrig == 'Rig 2 - JS8'):
      tx_rig = 'Rig2'
      self.tx_mode = 'JS8CALL'
      self.js8_tx_speed = 'TURBO'

      if(self.doesRigItemExist(tx_rig) == False):
        self.createRigItem(tx_rig, self.fldigiclient, self.js8client)
        self.tx_rig = tx_rig

      if(self.queryChannelItem(tx_rig, self.tx_mode, self.js8_tx_speed, 'TX',) == False):
        tx_channel = self.addChannelItem(tx_rig, self.tx_mode, self.js8_tx_speed, 'TX', '', callsign)
        self.tx_channel = tx_channel

    elif(txrig == 'Fig 2 - Fldigi'):
      tx_rig = 'Rig2'
      self.tx_mode = 'FLDIGI'
      self.tx_mode_name = 'Fldigi TX'

      if(self.doesRigItemExist(tx_rig) == False):
        self.createRigItem(tx_rig, self.fldigiclient, self.js8client)
        self.tx_rig = tx_rig
      if(self.queryChannelItem(tx_rig, self.tx_mode, self.tx_mode_name, 'TX',) == False):
        tx_channel = self.addChannelItem(tx_rig, self.tx_mode, self.tx_mode_name, 'TX', '', callsign)
        self.tx_channel = tx_channel

    self.active_rig     = self.tx_rig
    self.active_channel = self.tx_channel

    return

  def queryTransmitChannelJS8(self, rigname):
    return self.queryChannelItem(rigname, 'JS8CALL', self.js8_tx_speed, 'TX' )


  def createNackCodeJS8(self, string, num_fragments):
    self.debug.info_message("create nack code num frags: " + str(num_fragments) )
    if(num_fragments == 0):
      return self.createNackCodeReceivedJS8(string, num_fragments)
    else:
      test1 = self.createNackCodeReceivedJS8(string, num_fragments)
      test2 = self.createNackCodeMissingJS8(string, num_fragments)
      if(test1 == ''):
        return test2
      if(test2 == ''):
        return test1
      if(len(test1) < len(test2)):
        return test1
      else:
        return test2

  def createNackCodeReceivedJS8(self, string, num_fragments):
    received_fragments = '+'
    part = ''
    if(string != ''):
      for x in range(len(string)):
        if(string[x] in self.chars):
          if(part == ''):
            self.debug.info_message("settings part to: " + string[x] )
            part = string[x]
          elif(self.getIndexForChar(part[len(part)-1]) == self.getIndexForChar(string[x])-1):
            part = part + string[x]
            self.debug.info_message("appended to part: " + part )
          else:
            if(len(part) == 1 or len(part) == 2):
              received_fragments = received_fragments + part
              self.debug.info_message("setting received : " + received_fragments )
            else:
              received_fragments = received_fragments + '[' + part[0] + part[len(part)-1]
              self.debug.info_message("setting received 2: " + received_fragments )
            part = string[x]
      if(part != ''):
        if(len(part) == 1 or len(part) == 2):
          received_fragments = received_fragments + part
          self.debug.info_message("setting received 3: " + received_fragments )
        else:
          received_fragments = received_fragments + '[' + part[0] + part[len(part)-1]
          self.debug.info_message("setting received 4: " + received_fragments )
    else:
      received_fragments = received_fragments + '+'
   
    return received_fragments

  def createNackCodeMissingJS8(self, string, num_fragments):
    missing_fragments = '-'
    part = ''
    if(num_fragments > 0):
      for x in range(num_fragments):
        if(self.chars[x] not in string):
          if(part == ''):
            self.debug.info_message("settings part to: " + self.chars[x] )
            part = self.chars[x]
          elif(self.getIndexForChar(part[len(part)-1]) == self.getIndexForChar(self.chars[x])-1):
            part = part + self.chars[x]
            self.debug.info_message("appended to part: " + part )
          else:
            if(len(part) == 1):
              missing_fragments = missing_fragments + part
            elif(len(part) == 2):
              missing_fragments = missing_fragments + part
              self.debug.info_message("setting received : " + missing_fragments )
            else:
              missing_fragments = missing_fragments + '[' + part[0] + part[len(part)-1]
              self.debug.info_message("setting received 2: " + missing_fragments )
            part = self.chars[x]
      if(part != ''):
        if(len(part) <= 2):
          missing_fragments = missing_fragments + part
          self.debug.info_message("setting received 3: " + missing_fragments )
        else:
          missing_fragments = missing_fragments + '[' + part[0] + part[len(part)-1]
          self.debug.info_message("setting received 4: " + missing_fragments )

    return missing_fragments


  def expandNackCodeJS8(self, nack_code, rigname):
    self.debug.info_message("expandNackCodeJS8. nack code: " + nack_code )

    start_char = ''
    end_char = ''
    full_list = ''
    index = 0
    count = 1
    expand = False
    start_include = False
    while(index<36 and count < len(nack_code)):
      if(expand == True):
        if(self.chars[index] == start_char):
          start_include = True
          full_list = full_list + self.chars[index]
          count = count + 1
        elif(self.chars[index] == end_char):
          start_include = False
          expand = False
          full_list = full_list + self.chars[index]
          count = count + 1
        elif(start_include == True):
          full_list = full_list + self.chars[index]
        index = index + 1
      else:
        if(nack_code[count] == '['):
          start_char = nack_code[count+1]
          end_char = nack_code[count+2]
          expand = True
          count = count + 1
        else:
          full_list = full_list + nack_code[count]
          count = count + 1
          index = index + 1

    self.debug.info_message("expandNackCodeJS8. full_list: " + full_list )

    return full_list

  def decodeNackCodeReceivedJS8(self, nack_code, rigname):
    self.debug.info_message("decodeNackCodeReceivedJS8. nack code: " + nack_code )

    """ get the number of fragments in the TX message"""
    num_fragments = len(self.getReceivedStrings(self.tx_rig, self.tx_channel))

    self.debug.info_message("number of fragments transmitted : " + str(num_fragments) )

    all_missing = ''
    if(nack_code == '++'):
      for x in range(num_fragments):
        all_missing = all_missing + self.chars[x]
      return all_missing
    else:
      all_received = self.expandNackCodeJS8(nack_code, rigname)
      self.debug.info_message("all_received: " + str(all_received) )
      for x in range(num_fragments):
        if(self.chars[x] not in all_received):
          self.debug.info_message("chars[x] not in all_received: " + str(self.chars[x])  + ' ' +  all_received )
          all_missing = all_missing + self.chars[x]
      self.debug.info_message("all_missing: " + str(all_missing) )
      return all_missing


  def decodeNackCodeMissingJS8(self, nack_code, rigname):
    self.debug.info_message("decodeNackCodeMissingJS8. nack code: " + nack_code )

    """ get the number of fragments in the TX message"""
    num_fragments    = self.getNumFragments(self.tx_rig, self.tx_channel) 
    self.debug.info_message("number of fragments transmitted : " + str(num_fragments) )
    all_missing = self.expandNackCodeJS8(nack_code, self.active_rig)

    return all_missing


  def getIndexForChar(self, char):
    return self.chars.index(char)

  def getCharForIndex(self, index):
    return self.chars[index]

  def getEomMarker(self):
    return self.eom_marker

  def getEosMarker(self):
    return 'EOS'

  def getBosMarker(self):
    return 'BOS'

  def getPreMessage(self):
    return self.pre_message

  def setPreMessage(self, toCallsign, toGroup):
    self.pre_message = self.createPreMessagePend()
    return

    
  def resetAllConfirmedStations(self):
    return

  def setCurrentConfirmStation(self):
    return

  def stationConfirmed(self):
    return

  def getCurrentConfirmStation(self):
    return

  def incCurrentConfirmStation(self):
    return

  def getConfirmStationCount(self):
    return

  def doesRigItemExist(self, rigname):

    for keyname in self.rig_channel_dictionary:
      if(keyname == rigname):
        return True

    return False



  def createRigItem(self, rigname, fldigiclient, js8client):

    self.debug.info_message("create rig item SDFGDSFGSDFGDSFG\n")
    
    self.debug.info_message("create rig item name:" + rigname )

    if(rigname != ''):
      if(fldigiclient != None):
        fldigiclient.setRigName(rigname)
      #if(js8client != None):
      #  js8client.setRigName(rigname)

      rigdictionaryitem = { 'fldigiclient'  : fldigiclient,
                            'js8client'     : js8client,
                            'channels'      : {},
                          }       

      self.rig_channel_dictionary[rigname] = rigdictionaryitem

    return


  def addChannelItem(self, rigname, modetype, modename, offset, recipient_stations, station_callsign):

    rigdictionaryitem = self.rig_channel_dictionary[rigname]

    channel_name = str(offset) + '_' + modetype  + '_' + modename

    dictionary_channel  =  { 'received_strings'        : {},
                             'correct_frames'          : {},
                             'callsigns_confirmed'     : '',
                             'comm_status'             : cn.COMM_LISTEN,
                             'expected_reply'          : cn.COMM_NONE,
                             'recipient_stations'      : [],
                             'message_id'              : None,
                              'in_session'             : False,
                             'num_frames'              : 0,
                             'retransmit_count'        : 0,
                             'qry_acknack_retransmits' : 0,
                             'current_recipient'       : 0,
                             'frame_timing_seconds'    : 0,
                             'sender_callsign'         : self.mycall_from_file,
                             'channel_callsign'        : station_callsign,
                             'message'                 : '',
                             'sendto_group_individual' : cn.SENDTO_NONE,
                             'rcv_string'              : '',
                             'ack_nack_code'           : '',
                             'stub'                    : '',
                             'best_snr'                : -50,
                             'what_where'              : cn.WHAT_WHERE_NONE,
                             'txid_state'              : False,
                             'EOM_received'            : False,
                             'frame_rcv_time'          : datetime.now(),
                           }       


    all_recipients = recipient_stations.split(';')
    dictionary_channel['recipient_stations'] = all_recipients

    rigdictionaryitem.get('channels')[channel_name] = dictionary_channel

    self.debug.info_message("rig channel dictionary : " + str(self.rig_channel_dictionary) )

    """ channel name, station callsign, mode type, mode, offset, comm status, in session, last_heard, SAAM capable, """
    comm_status = cn.COMM_NONE
    in_session = False
    last_heard = datetime.now()
    saam_capable = cn.SAAM_CAPABLE
    self.group_arq.addGarqStation(rigname, channel_name, station_callsign, modetype, modename, offset, comm_status, in_session, last_heard, saam_capable)

    try:
      self.debug.info_message("garq stations: " + str(self.group_arq.getGarqStations()) )
      table = self.group_arq.getGarqStations()

      if(self.form_gui.window != None):
        self.form_gui.window['tbl_compose_stationcapabilities'].update(values=table )
    except:
      self.debug.error_message("Exception in saamfram addChannelItem: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return channel_name

  def queryChannelForCallSign(self, rigname, call_sign_lookup):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channels = rigdictionaryitem.get('channels')
    for channel_name in channels:
      call_sign = self.getChannelCallsign(rigname, channel_name)
      if(call_sign == call_sign_lookup):
        return channel_name
    return ''

  def queryChannelItem(self, rigname, modetype, modename, offset):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]

    channel_name = str(offset) + '_' + modetype  + '_' + modename

    if(channel_name in rigdictionaryitem.get('channels')):
      return True
    else:
      return False

  def getChannelItem(self, rigname, modetype, modename, offset):
    self.debug.info_message("GET CHANNEL ITEM\n")
    channel_name = str(offset) + '_' + modetype  + '_' + modename
    return channel_name

  def getChannelItemDict(self, rigname, modetype, modename, offset):
    self.debug.info_message("GET CHANNEL ITEM\n")
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channel_name = str(offset) + '_' + modetype  + '_' + modename
    channeldict = rigdictionaryitem.get('channels')
    channel = channeldict.get(channel_name)
    self.debug.info_message("GET CHANNEL ITEM for channel: " + str(channel_name) )
    return channel


  def getReceivedString(self, header, rigname, channel_name):
    received_strings = self.getReceivedStrings(rigname, channel_name)
    return received_strings[header]

  def addReceivedString(self, header, rcvd_string, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]

    if(header not in channeldictionaryitem):
      channeldictionaryitem.get('received_strings')[header] = rcvd_string
    return

  def getReceivedStrings(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('received_strings')

  def resetReceivedStrings(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['received_strings'] = {}

  def getCorrectFrames(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('correct_frames')

  def getCallsignsConfirmed(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('callsigns_confirmed')

  def setCallsignsConfirmed(self, rigname, channel_name, confirmed):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['callsigns_confirmed'] = confirmed


  def getCommStatus(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('comm_status')

  def setCommStatus(self, rigname, channel_name, status):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['comm_status'] = status

  def getExpectedReply(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('expected_reply')

  def setExpectedReply(self, rigname, channel_name, expected_reply):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['expected_reply'] = expected_reply

  def setInSession(self, rigname, channel_name, in_session):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['in_session'] = in_session

  def getInSession(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('in_session')

  def setNumFragments(self, rigname, channel_name, num_frames):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['num_frames'] = num_frames
    
  def getNumFragments(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('num_frames')

  def setSenderCallsign(self, rigname, channel_name, sender_callsign):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['sender_callsign'] = sender_callsign

  def getSenderCallsign(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('sender_callsign')

  def getCurrentRecipient(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('current_recipient')

  def setCurrentRecipient(self, rigname, channel_name, current_recipient):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['current_recipient'] = current_recipient

  def getRecipientStations(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('recipient_stations')

  def setRecipientStations(self, rigname, channel_name, recipient_stations):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['recipient_stations'] = recipient_stations


  def getMessageID(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('message_id')

  def setMessageID(self, rigname, channel_name, msgid):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['message_id'] = msgid


  def getRetransmitCount(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('retransmit_count')

  def setRetransmitCount(self, rigname, channel_name, retransmit_count):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['retransmit_count'] = retransmit_count

  def getQryAcknackRetransmitCount(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('qry_acknack_retransmits')

  def setQryAcknackRetransmitCount(self, rigname, channel_name, qry_acknack_retransmits):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['qry_acknack_retransmits'] = qry_acknack_retransmits

  def setMessage(self, rigname, channel_name, message):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['message'] = message

  def getMessage(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('message')

  def setRcvString(self, rigname, channel_name, rcv_string):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['rcv_string'] = rcv_string

  def resetRcvString(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['rcv_string'] = ''

  def appendRcvString(self, rigname, channel_name, rcv_string):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    prev_rcv_string = channeldictionaryitem.get('rcv_string')
    channeldictionaryitem['rcv_string'] = prev_rcv_string + rcv_string

  def getRcvString(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('rcv_string')

  def setFrameRcvTime(self, rigname, channel_name, frame_rcv_time):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['frame_rcv_time'] = frame_rcv_time

  def getFrameRcvTime(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('frame_rcv_time')

  def setEOMReceived(self, rigname, channel_name, EOM_received):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['EOM_received'] = EOM_received

  def getEOMReceived(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('EOM_received')

  def setFrameTimingSeconds(self, rigname, channel_name, frame_timing_seconds):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['frame_timing_seconds'] = frame_timing_seconds

  def getFrameTimingSeconds(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('frame_timing_seconds')

  def setChannelCallsign(self, rigname, channel_name, channel_callsign):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['channel_callsign'] = channel_callsign

  def getChannelCallsign(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('channel_callsign')

  def setAckNackCode(self, rigname, channel_name, ack_nack_code):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['ack_nack_code'] = ack_nack_code

  def getAckNackCode(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('ack_nack_code')


  def setTxidState(self, rigname, channel_name, txid_state):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['txid_state'] = txid_state

  def getTxidState(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('txid_state')

  def setSendToGroupIndividual(self, rigname, channel_name, sendto_group_individual):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['sendto_group_individual'] = sendto_group_individual

  def getSendToGroupIndividual(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('sendto_group_individual')

  def setStub(self, rigname, channel_name, stub):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['stub'] = stub

  def getStub(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('stub')

  def setWhatWhere(self, rigname, channel_name, what_where):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['what_where'] = what_where

  def getWhatWhere(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('what_where')

  def setBestSNR(self, rigname, channel_name, best_snr):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['best_snr'] = best_snr

  def getBestSNR(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('best_snr')


  def setTxMsgType(self, rigname, channel_name, msg_type):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    channeldictionaryitem['tx_msg_type'] = msg_type

  def getTxMsgType(self, rigname, channel_name):
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldictionaryitem = rigdictionaryitem.get('channels')[channel_name]
    return channeldictionaryitem.get('tx_msg_type')


  """ this method fragments the text into a list"""
  def frag(self, line, num):
    return [line[i:i+num] for i in range(0, len(line), num)]

  """ this method defragments the list into a string"""
  def defrag(self, split_string):
    retstring = ""
    for x in range(len(split_string)):
      retstring = retstring + split_string[x]
      
    return retstring

  def buildFragment(self, text, numfrag, totalfrag):
    return text + '[' + self.getChecksum(text) + ']'
    return

  def extractText(self, text):
    return


  def calcRepeatFragSpecifics(self, repeat_mode, text, frag_string, fragsize, num_times_repeat):

    if(repeat_mode != cn.REPEAT_FRAGMENTS):
      return 0, -1, -1, 0, -1, -1

    """ calculate how fragments the msgid and to callsigns list spans"""
    temporary_locate = text.split(cn.DELIMETER_CHAR, 4)
    how_many = len(temporary_locate[0]) + len(temporary_locate[1]) + len(temporary_locate[2]) + 2
    self.debug.info_message("HOW MANY : " + str(how_many) )
    how_many_frags = int((how_many + fragsize - 1) / fragsize)
    self.debug.info_message("HOW MANY FRAGE: " + str(how_many_frags) )
    """ only allow a max of 3 fragments to be repeated. this may not encompass the entire send list. sender should use slightly larger frag size."""
    how_many_frags = min(how_many_frags, 3)

    self.debug.info_message("HOW MANY FRAGE: " + str(how_many_frags) )

    """ number of times fragments are to be repeated"""
    repeat_fragments = num_times_repeat

    third_count      = -1
    two_third_count  = -1
    repeat_thirds    = 0
    mid_count = -1
    end_count = -1
    repeat_mid = 0

    if(repeat_fragments == 3):
      third_count = int(len(frag_string)/3)
      two_third_count = int((len(frag_string)*2)/3)
      end_count = len(frag_string)-1
      if(third_count>=6):
        """OK to repeat fragments 1, 2 and 3 at 3rd, 2/3rd and end"""
        repeat_thirds = 3
      elif(third_count>=4):
        """OK to repeat fragments 1 and 2 at 3rd, 2/3rd and end"""
        repeat_thirds = 2
      elif(third_count>=2):
        """OK to repeat fragments 1 at 3rd, 2/3rd and end"""
        repeat_thirds = 1
    elif(repeat_fragments == 2):
      mid_count = int(len(frag_string)/2)
      end_count = len(frag_string)-1
      if(mid_count>=6):
        """OK to repeat fragments 1, 2 and 3 at midpoint and end"""
        repeat_mid = 3
      elif(mid_count>=4):
        """OK to repeat fragments 1, 2 at midpoint and end"""
        repeat_mid = 2
      elif(mid_count>=2):
        """OK to repeat fragments 1, at midpoint and end"""
        repeat_mid = 1
    elif(repeat_fragments == 1):
      mid_count = int(len(frag_string)/2)
      end_count = len(frag_string)-1
      if(mid_count>=6):
        """OK to repeat fragments 1, 2 and 3 at midpoint and end"""
        repeat_mid = 3
      elif(mid_count>=4):
        """OK to repeat fragments 1, 2 at midpoint and end"""
        repeat_mid = 2
      elif(mid_count>=2):
        """OK to repeat fragments 1, at midpoint and end"""
        repeat_mid = 1
      mid_count = -1

    repeat_mid    = min(repeat_mid, how_many_frags)
    repeat_thirds = min(repeat_thirds, how_many_frags)

    return repeat_thirds, third_count, two_third_count, repeat_mid, mid_count, end_count
    

  def doRepeatFrag(self, x, repeat_thirds, third_count, two_third_count, repeat_mid, mid_count, end_count):

    fragtagmsg = ''

    if(x == third_count):
      if(repeat_thirds >= 3):
        """ sequence 2,3,1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(2), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >= 2):
        """ sequence 2,1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >= 1):
        """ sequence 1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
    elif(x == two_third_count):
      if(repeat_thirds >= 3):
        """ sequence 2,1,3"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(2), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >= 2):
        """ sequence 1,2"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >= 1):
        """ sequence 1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
    elif(x == mid_count):
      if(repeat_mid >= 2):
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
      elif(repeat_mid >= 1):
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
      elif(repeat_mid >= 3):
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(2), self.tx_rig, self.tx_channel)
    elif(x == end_count):
      if(repeat_thirds >=3 or repeat_mid >= 3):
        """ sequence 3,2,1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(2), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >=2 or repeat_mid >= 2):
        """ sequence 2,1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(1), self.tx_rig, self.tx_channel)
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)
      elif(repeat_thirds >=1 or repeat_mid >= 1):
        """ sequence 1"""
        fragtagmsg = fragtagmsg + self.getReceivedString('[' + self.getCharForIndex(0), self.tx_rig, self.tx_channel)

    return fragtagmsg

  """ fragment encoding for 36 frames or less"""
  def buildFragTagMsgJS8n(self, text, fragsize, sender_callsign):
    fragtagmsg = ''

    """ checksum the entire message to make sure all fragments are authentic"""  
    check = self.getEOMChecksum(text.upper())

    frag_string = self.frag(text.upper(), fragsize)

    repeat_mode = cn.REPEAT_NONE
    repeat_mode = cn.REPEAT_FRAGMENTS

    checked = self.form_gui.window['cb_outbox_repeatfrag'].get()
    if(checked):
      num_times_repeat = 3
      repeat_mode = cn.REPEAT_FRAGMENTS
    else:
      num_times_repeat = 0
      repeat_mode = cn.REPEAT_NONE

    repeat_thirds, third_count, two_third_count, repeat_mid, mid_count, end_count = self.calcRepeatFragSpecifics(repeat_mode, text.upper(), frag_string, fragsize, num_times_repeat)

    self.resetReceivedStrings(self.tx_rig, self.tx_channel)
    for x in range(len(frag_string)):
      start_frame = '[' + self.getCharForIndex(x) 
      part_string = start_frame + frag_string[x] 

      if(repeat_mode == cn.REPEAT_FRAGMENTS):
        fragtagmsg = fragtagmsg + self.doRepeatFrag(x, repeat_thirds, third_count, two_third_count, repeat_mid, mid_count, end_count)

      fragtagmsg = fragtagmsg + part_string

      self.addReceivedString(start_frame, part_string , self.tx_rig, self.tx_channel)
   
    """ checksum the entire message to make sure all fragments are authentic"""  
    self.debug.info_message("EOM checksum is: " + str(check) )

    start_frame = '[' + self.getCharForIndex(len(frag_string) ) 
    part_string = start_frame + check
    fragtagmsg = fragtagmsg + part_string + self.getEomMarker()  + ' ' + sender_callsign + ' '
    self.addReceivedString(start_frame, part_string , self.tx_rig, self.tx_channel)

    self.debug.info_message("fragtagmsg: " + fragtagmsg )

    return fragtagmsg



  def buildFragTagMsg(self, text, fragsize, send_type, sender_callsign):

    try:
      if(self.group_arq.getSendModeRig1() == cn.SEND_JS8CALL): 
        self.debug.info_message("buildFragTagMsg SEND_JS8CALL\n")
        return self.buildFragTagMsgJS8n(text, fragsize, sender_callsign)
      elif(self.group_arq.getSendModeRig1() == cn.SEND_FLDIGI): 
        self.debug.info_message("buildFragTagMsg SEND_FLDIGI\n")
        return self.buildFragTagMsgFldigi(text, fragsize, sender_callsign)
    except:
      self.debug.error_message("Exception in buildFragTagMsg: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
    return ''


  def buildFragTagMsgFldigi(self, text, fragsize, sender_callsign):

    EOM_checksum = self.getEOMChecksum(text)
    text = text + EOM_checksum

    repeat_mode = cn.REPEAT_MESSAGE
    repeat_mode = cn.REPEAT_NONE
    num_times_repeat = 3
     
    checked = self.form_gui.window['cb_outbox_repeatmsg'].get()

    if(checked):
      if(self.form_gui.window['option_repeatmessagetimes'].get() == 'x1'):
        repeat_mode = cn.REPEAT_MESSAGE
        num_times_repeat = 1
      elif(self.form_gui.window['option_repeatmessagetimes'].get() == 'x2'):
        repeat_mode = cn.REPEAT_MESSAGE
        num_times_repeat = 2
      elif(self.form_gui.window['option_repeatmessagetimes'].get() == 'x3'):
        repeat_mode = cn.REPEAT_MESSAGE
        num_times_repeat = 3

    fragtagmsg = ''
    frag_string = self.frag(text, fragsize)
    self.resetReceivedStrings(self.tx_rig, self.tx_channel)

    """ create a set of receive strings"""
    for x in range(len(frag_string)):
      start_frame = '[F' + str(x+1) + ',' + str(len(frag_string)) + ']'
      part_string = start_frame + frag_string[x] 
      check = self.getChecksum(frag_string[x] )
      end_frame = '[' + check + ']'
      self.addReceivedString(start_frame, part_string + end_frame, self.tx_rig, self.tx_channel)

    repeat_one   = 0
    repeat_two   = 0
    repeat_three = 0
    if(repeat_mode == cn.REPEAT_MESSAGE):
      """ repeat one is forward / backward interlaced"""
      repeat_one = len(frag_string)-1
      """ repeat two is 120' offset and forward backward interlaced"""
      repeat_two   = int((len(frag_string)-1) / 3)
      """ repeat three is 240' offset forward, 270' offset backward and forward backward interlaced"""
      repeat_three = int(((len(frag_string)-1) * 2) / 3)

    for x in range(len(frag_string)):
      start_frame = '[F' + str(x+1) + ',' + str(len(frag_string)) + ']'
      fragtagmsg = fragtagmsg + self.getReceivedString(start_frame, self.tx_rig, self.tx_channel)
 
      if(repeat_mode == cn.REPEAT_MESSAGE):
        if(num_times_repeat >= 1):
          start_frame_one = '[F' + str(repeat_one+1) + ',' + str(len(frag_string)) + ']'
          fragtagmsg = fragtagmsg + self.getReceivedString(start_frame_one, self.tx_rig, self.tx_channel)
          repeat_one = repeat_one - 1
        if(num_times_repeat >= 2):
          start_frame_two = '[F' + str(repeat_two+1) + ',' + str(len(frag_string)) + ']'
          fragtagmsg = fragtagmsg + self.getReceivedString(start_frame_two, self.tx_rig, self.tx_channel)
          repeat_two = repeat_two + 1
          if(repeat_two == len(frag_string)):
            repeat_two = 0
        if(num_times_repeat == 3):
          start_frame_three = '[F' + str(repeat_three+1) + ',' + str(len(frag_string)) + ']'
          fragtagmsg = fragtagmsg + self.getReceivedString(start_frame_three, self.tx_rig, self.tx_channel)
          repeat_three = repeat_three - 1
          if(repeat_three == -1):
            repeat_three = len(frag_string)-1
    
    """ checksum the entire message to make sure all fragments are authentic"""  
    fragtagmsg = fragtagmsg + self.getEomMarker() + ' ' + sender_callsign + ' '

    self.debug.info_message("fragtagmsg: " + fragtagmsg )

    return fragtagmsg


  def deconstructFragTagMsg(self, text, send_type):
    if(self.group_arq.getSendModeRig1() == cn.SEND_JS8CALL): 
      return self.deconstructFragTagMsgJS8n(text)
    elif(self.group_arq.getSendModeRig1() == cn.SEND_FLDIGI): 
      return self.deconstructFragTagMsgFldigi(text)

    
  def deconstructFragTagMsgFldigi(self, fragtagmsg):

    reconstruct = ''

    completed = False
    remainder = fragtagmsg
    while completed == False:
      split_string = remainder.split('[F', 1)
      numbers_and_remainder = split_string[1].split(']', 1)
      numbers = numbers_and_remainder[0].split(',', 1)
      part_number = numbers[0]
      parts_total = numbers[1]
      remainder = numbers_and_remainder[1]
      self.debug.info_message("part number and total: " + part_number + "," + parts_total )

      if(part_number == parts_total):
        completed = True
        
      """ deconstruct message text """
      split_string = remainder.split('[', 1)
      checksum_and_remainder = split_string[1].split(']', 1)
      message_text = split_string[0]
      reconstruct = reconstruct + message_text
      message_checksum = checksum_and_remainder[0]
      remainder = checksum_and_remainder[1]
      self.debug.info_message("message text: " + message_text )
      self.debug.info_message("message checksum: " + message_checksum )

      if(remainder == '' ):
        completed = True

    self.debug.info_message("reconstructed string: " + reconstruct )

    """ pull the 4 digit checksum off the end of the completed string. """
    EOM_checksum = reconstruct[-4:]
    reconstruct  = reconstruct[:-4]

    try:
      self.debug.info_message("reconstructed string 2: " + reconstruct )
      self.debug.info_message("EOM checksum 1 is: " + str(EOM_checksum.upper() ) )
      self.debug.info_message("EOM checksum 2 is: " + str(self.getEOMChecksum(reconstruct).upper()) )
    except:
      self.debug.error_message("Exception in deconstructFragTagMsgFldigi: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
 
    if(EOM_checksum.upper() == self.getEOMChecksum(reconstruct).upper() ):
      return True, reconstruct
    else:
      return False, reconstruct

    return True, reconstruct

  def deconstructFragTagMsgJS8n(self, fragtagmsg):

    self.debug.info_message("deconstruct fragtagmsg JS8\n")

    try:
      reconstruct = ''
      num_fragments = 0
      completed = False
      remainder = fragtagmsg
      while completed == False:
        numbers_and_remainder = remainder.split('[', 1)[1]

        """ test to see if this is the end of the mssage"""
        if('[' in numbers_and_remainder):
          part_number = numbers_and_remainder[0]
          remainder = numbers_and_remainder[1:]
          self.debug.info_message("part number and remainder: " + part_number + "," + remainder )

          """ deconstruct message text """
          split_string = remainder.split('[', 1)
          message_text = split_string[0]
          reconstruct = reconstruct + message_text
          self.debug.info_message("message text: " + message_text )
        else:
          self.debug.info_message("processing end of message: " + str(numbers_and_remainder))

          num_fragments = self.getIndexForChar(numbers_and_remainder[0])+1
          checksum = numbers_and_remainder[1:5]
          eom_text = numbers_and_remainder[5:7]
          self.debug.info_message("checksum, eom_text, eom_callsign: " + checksum + "," + eom_text )
          self.debug.info_message("num_fragments: " + str(num_fragments) )
          completed = True

        if(remainder == '' ):
          completed = True

    except:
      self.debug.error_message("Exception in deconstructFragTagMsgJS8n: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("reconstructed string: " + reconstruct )

    if(checksum.upper() == self.getEOMChecksum(reconstruct).upper() ):
      return True, reconstruct
    else:
      return False, reconstruct

    return True, reconstruct

    
  def getAckNack(self, text):
    return  


  """ This method will see how many frames failed and construct either an ACK for the frames that succeeded or
  an NACK for the frames that failed. If there are more failed frames than success frames then send an ACK
  otherswise send an NACK
  ACK[1,3,4]
  NACK[4,5]
  if everything is received succesfully send an  ACK[ALL]
  if everything failed send an NACK[ALL]
  """

  """ Checksum code """    
  def resetChecksum(self):
    self.checksum_value=0xFFFF

  def calculateChecksum(self, c):
    self.checksum_value ^= c; 
    for i in range(8):   
      if (self.checksum_value & 1):
        self.checksum_value = (self.checksum_value >> 1) ^ 0xA001
      else:
        self.checksum_value = (self.checksum_value >> 1)

  def checksum(self, text):
    self.resetChecksum()
    for i in range(len(text)):   
      self.calculateChecksum((ord(text[i]) & 0xFF)) 
    return (self.checksum_value)



  def getEOMChecksum(self, mystr):
    return self.calcEOMCRC(mystr)

  def getChecksum(self, mystr):
    return self.calcFragmentCRC(mystr)


  def getFileSendString(self, msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):

    self.debug.info_message("getFileSendString: " + content )

    content_string = content
    """ only process the content for escapes"""
    
    send_string = '{' + cn.FORMAT_FILE + self.delimiter_char + msgid + self.delimiter_char + tolist + self.delimiter_char + priority + self.delimiter_char + \
                            str(frag_size)+ self.delimiter_char + subject + self.delimiter_char + formname + self.delimiter_char + version + self.delimiter_char 
                            
    send_string = send_string + content_string
    send_string = send_string + '}'

    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("buildFragTagMsg: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string

  def getImageFileSendString(self, msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):

    self.debug.info_message("getImageFileSendString: " + content )

    content_string = content
    """ only process the content for escapes"""
    
    send_string = '{' + cn.FORMAT_IMAGE + self.delimiter_char + msgid + self.delimiter_char + tolist + self.delimiter_char + priority + self.delimiter_char + \
                            str(frag_size)+ self.delimiter_char + subject + self.delimiter_char + formname + self.delimiter_char + version + self.delimiter_char 
                            
    send_string = send_string + content_string
    send_string = send_string + '}'

    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("buildFragTagMsg: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string

  def getWL2KSendString(self, msgid, content, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):

    self.debug.info_message("getWL2KSendString: " + content )

    content_string = content
    """ only process the content for escapes"""
    
    send_string = '{' + cn.FORMAT_WL2K + self.delimiter_char + msgid + self.delimiter_char + tolist + self.delimiter_char + priority + self.delimiter_char + \
                            str(frag_size)+ self.delimiter_char + subject + self.delimiter_char + formname + self.delimiter_char + version + self.delimiter_char 
                            
    send_string = send_string + content_string
    send_string = send_string + '}'

    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("buildFragTagMsg: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string

  def getHRRMSendString(self, msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):
    content = self.form_dictionary.getContentByIdFromOutboxDictionary(msgid)

    content_string = ''
    for x in range (len(content)):
      if(x>0):
        content_string = content_string + self.delimiter_char + str(content[x])
      else:
        content_string = content_string + str(content[x])
    """ only process the content for escapes"""
    content_string = self.getEncodeEscapes(content_string)
    
    send_string = '{' + cn.FORMAT_HRRM + self.delimiter_char + msgid + self.delimiter_char + tolist + self.delimiter_char + priority + self.delimiter_char + \
                            str(frag_size)+ self.delimiter_char + subject + self.delimiter_char + formname + self.delimiter_char + version + self.delimiter_char 
                            
    send_string = send_string + content_string

    send_string = send_string + '}'
    send_string = self.getRunLengthEncode(send_string)

    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("buildFragTagMsg: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string




  def base64Encode(self, binaryData):
    self.debug.info_message("base64Encode: " + str(binaryData))
    encoded_data = ''

    try:
      encoded_data = base64.b64encode(binaryData)
      self.debug.info_message("base64Encode encoded binary data is: " + str(encoded_data) )

    except:
      self.debug.error_message("Exception in base64Encode: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return str(encoded_data)



  def getContentAndTemplateSendString(self, msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):
      send_string_content = self.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign)
      send_string_template = self.getTemplateSendString(formname, sender_callsign, frag_size)
      complete_send_string = send_string_content + send_string_template
      return complete_send_string

  """
outbox dictionary items formatted as...
[u'ICS-213', u'v1.0', u'750cc9d8_2fc1d3d0', u'High', u'WH6ABC,WH6DEF,WH6GHI', u'I AM THE SUBJECT', 'Test', 'Lawrence', 'something important', 'Peter', 'nobody', 'Hello from rainy hawaii', '', '', u'This is a short message to show how the formatting works', '', '']
<FORMNAME> <Version> <ID> <PRIORITY> <TO list> <Subject> <contents.....>
  """
  def getContentSendString(self, msgid, formname, priority, tolist, subject, frag_size, tagfile, version, sender_callsign):
    content = self.form_dictionary.getContentByIdFromOutboxDictionary(msgid)


    content_string = ''
    for x in range (len(content)):
      if(x>0):
        content_string = content_string + self.delimiter_char + str(content[x])
      else:
        content_string = content_string + str(content[x])
    """ only process the content for escapes"""
    content_string = self.getEncodeEscapes(content_string)
    
    
    send_string = '{' + cn.FORMAT_CONTENT + self.delimiter_char + msgid + self.delimiter_char + tolist + self.delimiter_char + priority + self.delimiter_char + \
                            str(frag_size)+ self.delimiter_char + subject + self.delimiter_char + formname + self.delimiter_char + version + self.delimiter_char 
                            
    send_string = send_string + content_string

    send_string = send_string + '}'
    send_string = self.getRunLengthEncode(send_string)

    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("buildFragTagMsg: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string

  def getTemplateSendString(self, formname, sender_callsign, frag_size):
    template = self.form_dictionary.getTemplateByFormFromTemplateDictionary(formname)

    #FIXME SHOULD NOT BE HARDCODED
    version = 1.2
    tagfile = 'ICS'

    """IGNORE TEMPLATE ONLY FORMAT AS NOT SUPPORTED IN BETA 1 RELEASE."""
    """ TEMPLATE_ONLY *does* include formname and version as content is not being sent"""
    message_format = cn.FORMAT_TEMPLATE_ONLY

    """ TEMPLATE_AND_CONTENT does not include formname or version as this is sent with the content"""
    message_format = cn.FORMAT_TEMPLATE_AND_CONTENT
    
    send_string = ''
    if(message_format == cn.FORMAT_TEMPLATE_AND_CONTENT):
      send_string = '{' + cn.FORMAT_TEMPLATE + self.delimiter_char + tagfile + self.delimiter_char  
    elif(message_format == cn.FORMAT_TEMPLATE_ONLY):
      send_string = '{' + cn.FORMAT_TEMPLATE + self.delimiter_char + tagfile + self.delimiter_char + formname + self.delimiter_char  + version + self.delimiter_char 

    for x in range (len(template)):
      if(x>0):
        send_string = send_string + self.delimiter_char + str(template[x])
      else:
        send_string = send_string + str(template[x])

    send_string = send_string + '}'
    fragtagmsg = self.buildFragTagMsg(send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
    self.debug.info_message("reconstructed string: " + fragtagmsg )
    self.deconstructFragTagMsg(fragtagmsg, self.group_arq.getSendModeRig1())
      
    return send_string


  def mergeTags(self, existing_tags, tags):

    num_fragments = -1
    for key in existing_tags:
      if(self.group_arq.operating_mode == cn.FLDIGI):
        if(num_fragments == -1):
          num_fragments = key.split(',')[1].split(']')[0]
      if(key not in tags):
        tags[key] = existing_tags[key]

    return tags, num_fragments

  """ if only the first 3 frames of content are received create a stub message in the inbox with status 'PARTIAL' or 'STUB' """
  def processIncomingStubMessage(self, stub, tags):
    try:
      if(self.testStubHasMsgidAndRcvList(stub) == True):
        msgid, rcv_list = self.extractFromStub(stub)
        msgfrom = self.getSenderCall()
        timestamp = datetime.utcnow().strftime('%y%m%d%H%M%S')
        self.debug.info_message("creating stub in dictionary and inbox\n")

        mycall = self.getMyCall()

        self.debug.info_message("processIncomingStubMessage stub is: " + stub)
        self.debug.info_message("processIncomingStubMessage msgid is: " + msgid)
        self.debug.info_message("processIncomingStubMessage rcv_list is: " + rcv_list)

        which_box = cn.NO_BOX

        if(self.testAnywhereOnReceiveList(rcv_list, mycall) == True):
          which_box = cn.IN_BOX
          self.form_dictionary.createInboxDictionaryItem(msgid, rcv_list, msgfrom, '-', '-', timestamp, '-', tags, 'Partial')
          self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
          self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())
        else:
          which_box = cn.RELAY_BOX
          self.form_dictionary.createRelayboxDictionaryItem(msgid, rcv_list, msgfrom, '-', '-', timestamp, '-', '', '', tags, 'Partial')
          self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
          self.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

        #FIXME PROCESS FOR RELAYBOX AND INBOX
        if(self.form_dictionary.doesInboxDictionaryItemExist(msgid)):
          if(self.form_dictionary.getVerifiedFromInboxDictionary(msgid) == 'Partial'):
            existing_tags = self.form_dictionary.getContentFromInboxDictionary(msgid)
            received_strings, num_strings = self.mergeTags(existing_tags, tags)
            if(num_strings == len(received_strings) ):
              rebuilt_string = ''
              if(self.group_arq.operating_mode == cn.FLDIGI):
                for x in range(1, num_strings+1):
                  extracted_string = received_strings['[F' + str(x) + ',' + str(num_strings) + ']']			
                  rebuilt_string = rebuilt_string + extracted_string
              elif(self.group_arq.operating_mode == cn.JS8CALL):
                for x in range(num_strings):
                  extracted_string = received_strings['[' + self.getCharForIndex(x) ]			
                  rebuilt_string = rebuilt_string + extracted_string

              self.debug.info_message("rebuilt string is: " + rebuilt_string )
              self.debug.info_message("ALL PARTIAL TAGS NOW RECEIVIED SENDING TO PROCESS\n")
              self.processIncomingMessageCommon(rebuilt_string, which_box)

    except:
      self.debug.error_message("Exception in processIncomingStubMessage: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return

  def processIncomingMessage(self, received_text):
    self.debug.info_message("processIncomingMessage. Received text: " + received_text )
    return self.processIncomingMessageCommon(received_text, cn.UNKNOWN_BOX)


  def getBinaryFile(self, filename):

    try:
      compressionlevel=9

      with open(filename,'rb') as image_file:
        encoded_string = base64.b64encode(bz2.compress(image_file.read(), compressionlevel))

      self.debug.info_message("getBinaryFile. encoded string = " + str(encoded_string.decode()) )

    except:
      self.debug.error_message("Exception in getBinaryFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return str(encoded_string.decode())


  def processIncomingMessageCommon(self, received_text, which_box):
    self.debug.info_message("processIncomingMessageCommon. Received text: " + received_text )

    reconstruct = ''

    completed = False
    content_processed = False
    template_processed = False
    message_format = cn.FORMAT_NONE 
    """ CONTENT must always be sent first then template can determine the format"""
       
    success, remainder = self.deconstructFragTagMsg(received_text, self.group_arq.getSendModeRig1())
    while completed == False:
      if('{' + cn.FORMAT_TEMPLATE in remainder):
        if(content_processed == True):
          message_format = cn.FORMAT_TEMPLATE_AND_CONTENT
        else:
          message_format = cn.FORMAT_TEMPLATE_ONLY
        template_processed = True

        split_string = remainder.split('{' + cn.FORMAT_TEMPLATE + self.delimiter_char, 1)

        params_data_and_remainder = split_string[1].split('}', 1)
        if(message_format == cn.FORMAT_TEMPLATE_AND_CONTENT):
          params_and_data = params_data_and_remainder[0].split(self.delimiter_char,1)
          tagfile  = params_and_data[0] 
          data     = params_and_data[1].split(self.delimiter_char)
        elif(message_format == cn.FORMAT_TEMPLATE_ONLY):
          params_and_data = params_data_and_remainder[0].split(self.delimiter_char,3)
          tagfile  = params_and_data[0] 
          formname = params_and_data[1] 
          version  = params_and_data[2] 
          data     = params_and_data[3].split(self.delimiter_char)

        
        """ need to save the received template"""

        #FIXME NEED TO SAVE RECEIVED TEMPLATE!!!!!!!!!!!!!!!!!!!!!
        #change the form name before saving to includ last 3 of sending callsign to avoid confusion with ecisting templates use category of rcvd_templates
        #  self.createNewTemplateInDictionary('received_templates', 'tmpl_rcvd', formname, version, 'template received from ggo', data)

        for x in range(len(data)):
          self.debug.info_message(cn.FORMAT_TEMPLATE + ": data[x] is: " + data[x] )
        remainder = params_data_and_remainder[1]
      elif('{' + cn.FORMAT_CONTENT in remainder):
        content_processed = True

        content   = []
        split_string = remainder.split('{'  + cn.FORMAT_CONTENT + self.delimiter_char, 1)
        data_and_remainder = split_string[1].split('}', 1)

        rleDecodedString = self.getDecodeEscapes(data_and_remainder[0])

        """ only process the content for escapes"""
        data = rleDecodedString.split(self.delimiter_char)

        for x in range(len(data)):
          self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
        remainder = data_and_remainder[1]

        ID        = data[0]
        msgto     = data[1]
        priority  = data[2]
        fragsize  = data[3]
        subject   = data[4]
        formname  = data[5]
        version   = data[6]

        timestamp = self.getDecodeTimestampFromUniqueId(ID)
        msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

        """ must also pass 2nd CRC check"""
        if(success):
          verified  = 'Verified'
        else:
          verified  = 'CRC'


        #do the following as soon as the stub with msgid is received...
        #existing_tags = 
        #content = mergeTags(existing_tags, new_tags)

        for x in range(7,len(data)):
          content.append(data[x])			
          self.debug.info_message("CONTENT is: " + data[x] )

        if(which_box == cn.UNKNOWN_BOX):
          if(self.testAnywhereOnReceiveList(msgto, self.getMyCall()) == True):
            which_box = cn.IN_BOX
          else:
            which_box = cn.RELAY_BOX


        ##FIXME
        self.debug.info_message("data 5 == " + data[5])
        if(data[5] == 'QUICKMSG'):

          received_data = data[12]
          if(len(received_data)>100):
            self.group_arq.addChatData(msgfrom, received_data[:90].strip(), data[0])
            self.group_arq.addChatData('', received_data[90:180].strip(), data[0])
            self.group_arq.addChatData('', received_data[180:].strip(), data[0])
          elif(len(received_data)>50):
            self.group_arq.addChatData(msgfrom, received_data[:90].strip(), data[0])
            self.group_arq.addChatData('', received_data[90:].strip(), data[0])
          else:
            self.group_arq.addChatData(msgfrom, received_data[:90].strip(), data[0])

          self.form_gui.window['table_chat_received_messages'].update(values=self.group_arq.getChatData())
          self.form_gui.window['table_chat_received_messages'].set_vscroll_position(1.0)


        """ priority of none indicates the message is not to be saved anywhere. """
        if(priority != 'None'):
          if(which_box == cn.IN_BOX):
            self.debug.info_message("processIncomingMessageCommon adding to INBOX")
            self.form_dictionary.createInboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content, verified)

            try:
              self.form_gui.window['tab_inbox'].select()
            except:
              self.debug.info_message("method: processIncomingMessageCommon exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

          elif(which_box == cn.RELAY_BOX):
            self.debug.info_message("processIncomingMessageCommon adding to RELAYBOX")
            confrcvd = ''
            self.form_dictionary.createRelayboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, confrcvd, fragsize, content, verified)

            try:
              self.form_gui.window['tab_relaybox'].select()
            except:
              self.debug.info_message("method: processIncomingMessageCommon exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

        else:
            try:
              self.form_gui.window['tab_chat'].select()
            except:
              self.debug.info_message("method: processIncomingMessageCommon exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

      elif('{' + cn.FORMAT_HRRM in remainder):

        content_processed = True
        content   = []
        split_string = remainder.split('{'  + cn.FORMAT_HRRM + self.delimiter_char, 1)
        data_and_remainder = split_string[1].split('}', 1)

        rleDecodedString = data_and_remainder[0]
        data = rleDecodedString.split(self.delimiter_char)

        for x in range(len(data)):
          self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
        remainder = data_and_remainder[1]

        ID        = data[0]
        msgto     = data[1]
        priority  = data[2]
        fragsize  = data[3]
        subject   = data[4]
        formname  = data[5]
        version   = data[6]

        timestamp = self.getDecodeTimestampFromUniqueId(ID)
        msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

        """ must also pass 2nd CRC check"""
        if(success):
          verified  = 'Verified'
        else:
          verified  = 'CRC'

        """
        process the incoming file here...
        """
        self.debug.info_message("incoming base64 encoded data is : " + data[7] )

        data2 = bz2.decompress(base64.b64decode(data[7]))
        data = data2.split(self.delimiter_char)

        for x in range(len(data)):
          content.append(data[x])			
          self.debug.info_message("CONTENT is: " + data[x] )

        if(which_box == cn.UNKNOWN_BOX):
          if(self.testAnywhereOnReceiveList(msgto, self.getMyCall()) == True):
            which_box = cn.IN_BOX
          else:
            which_box = cn.RELAY_BOX

        """ priority of none indicates the message is not to be saved anywhere. """
        if(which_box == cn.IN_BOX):
          self.debug.info_message("processIncomingMessageCommon adding to INBOX")
          self.form_dictionary.createInboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content, verified)

          try:
            self.form_gui.window['tab_inbox'].select()
          except:
            self.debug.info_message("method: processIncomingMessageCommon exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

        elif(which_box == cn.RELAY_BOX):
          self.debug.info_message("processIncomingMessageCommon adding to RELAYBOX")
          confrcvd = ''
          self.form_dictionary.createRelayboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, confrcvd, fragsize, content, verified)

          try:
            self.form_gui.window['tab_relaybox'].select()
          except:
            self.debug.info_message("method: processIncomingMessageCommon exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

        completed = True		

      elif('{' + cn.FORMAT_FILE in remainder):
        content_processed = True

        content   = []
        split_string = remainder.split('{'  + cn.FORMAT_FILE + self.delimiter_char, 1)
        data_and_remainder = split_string[1].split('}', 1)

        rleDecodedString = data_and_remainder[0]

        """ only process the content for escapes"""
        data = rleDecodedString.split(self.delimiter_char)

        for x in range(len(data)):
          self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
        remainder = data_and_remainder[1]

        ID        = data[0]
        msgto     = data[1]
        priority  = data[2]
        fragsize  = data[3]
        subject   = data[4]
        formname  = data[5]
        version   = data[6]

        timestamp = self.getDecodeTimestampFromUniqueId(ID)
        msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

        """ must also pass 2nd CRC check"""
        if(success):
          verified  = 'Verified'
        else:
          verified  = 'CRC'

        """
        process the incoming file here...
        """
        self.debug.info_message("incoming base64 encoded data is : " + data[7] )

        with open('./sent_data.dat', 'wb') as f:
          f.write(bz2.decompress(base64.b64decode(data[7])))

        content.append(data[7])			
        self.debug.info_message("CONTENT is: " + data[7] )

        completed = True		

        self.form_gui.form_events.changeFlashButtonState('in_mainpanel_saveasfilename', True)

        self.form_gui.window['tab_filexfer'].select()

          
      elif('{' + cn.FORMAT_IMAGE in remainder):
        content_processed = True

        content   = []
        split_string = remainder.split('{'  + cn.FORMAT_IMAGE + self.delimiter_char, 1)
        data_and_remainder = split_string[1].split('}', 1)

        rleDecodedString = data_and_remainder[0]

        """ only process the content for escapes"""
        data = rleDecodedString.split(self.delimiter_char)

        for x in range(len(data)):
          self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
        remainder = data_and_remainder[1]

        ID        = data[0]
        msgto     = data[1]
        priority  = data[2]
        fragsize  = data[3]
        subject   = data[4]
        formname  = data[5]
        version   = data[6]

        timestamp = self.getDecodeTimestampFromUniqueId(ID)
        msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

        """ must also pass 2nd CRC check"""
        if(success):
          verified  = 'Verified'
        else:
          verified  = 'CRC'

        """
        process the incoming file here...
        """
        self.debug.info_message("incoming base64 encoded data is : " + data[7] )

        with open('./received_image.jpg', 'wb') as f:
          f.write(bz2.decompress(base64.b64decode(data[7])))

        im = Image.open('received_image.jpg')
        im.save('preview.png')
        filename =  'preview.png'
        self.form_gui.window['filexfer_image'].update(filename)


        content.append(data[7])			
        self.debug.info_message("CONTENT is: " + data[7] )

        completed = True		

        self.form_gui.form_events.changeFlashButtonState('in_mainpanel_saveasimagefilename', True)

        self.form_gui.window['tab_filexfer'].select()

      elif('{' + cn.FORMAT_WL2K in remainder):

        try:
          content_processed = True

          content   = []
          split_string = remainder.split('{'  + cn.FORMAT_WL2K + self.delimiter_char, 1)
          data_and_remainder = split_string[1].split('}', 1)

          rleDecodedString = data_and_remainder[0]

          """ only process the content for escapes"""
          data = rleDecodedString.split(self.delimiter_char)

          for x in range(len(data)):
            self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
          remainder = data_and_remainder[1]

          ID        = data[0]
          msgto     = data[1]
          priority  = data[2]
          fragsize  = data[3]
          subject   = data[4]
          formname  = data[5]
          version   = data[6]

          timestamp = self.getDecodeTimestampFromUniqueId(ID)
          msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

          """ must also pass 2nd CRC check"""
          if(success):
            verified  = 'Verified'
          else:
            verified  = 'CRC'

          """
          process the incoming file here...
          """
          self.debug.info_message("incoming base64 encoded data is : " + data[7] )

          inbox_folder = self.form_gui.window['in_winlink_inboxfolder'].get()

          with open(inbox_folder + formname, 'wb') as f:
            f.write(bz2.decompress(base64.b64decode(data[7])))

          content.append(data[7])			
          self.debug.info_message("CONTENT is: " + data[7] )

          completed = True		  
        except:
          self.debug.info_message("method: processIncomingMessageCommon WL2K exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

        self.form_gui.window['tab_winlink'].select()


      else:
        completed = True		  

      if(remainder == '' ):
        completed = True

    self.debug.info_message("DEFRAGGED AND RECONSTRUCTED MESSAGE IS: " + reconstruct )

    return

  def isReply(self, id_string):
    if('-' in id_string):
      return True
    else:
      return False

  """ original sender ID is always the irst ID"""
  def getOriginalSenderID(self, id_string):
    split_string = id_string.split('-', 1)
    return split_string[0]

  """ reply ID is always the second of the two IDs"""
  def getReplyID(self, id_string):
    split_string = id_string.split('-', 1)
    return split_string[1]

  def extractFromStub(self, stub):
    try:
      split_string = stub.split(cn.DELIMETER_CHAR)
      msgid        = split_string[1]
      receive_list = split_string[2]
      return msgid, receive_list

    except:
      self.debug.error_message("Exception in extractFromStub: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return '', ''

    return '', ''

  def testStubHasMsgidAndRcvList(self, stub):

    self.debug.info_message("testStubHasMsgidAndRcvList\n")

    split_string = stub.split(cn.DELIMETER_CHAR)

    if(len(split_string) >= 3):
      return True
    else:
      return False
  
  def testFirstOnReceiveList(self, stub, mycall):

    self.debug.info_message("TEST RECEIVE LIST\n")

    try:
      msgid, receive_list = self.extractFromStub(stub)
      split_string = receive_list.split(';')

      if(mycall == split_string[0] ):
        self.debug.info_message("YES MY CALL IS FIRST ON THE LIST\n")
        return True

    except:
      self.debug.error_message("Exception in testFirstOnReceiveList: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return False

    self.debug.info_message("NO MY CALL IS NOT FIRST ON THE LIST\n")
    return False



  def testAnywhereOnReceiveList(self, receive_list, mycall):
    try:
      split_string = receive_list.split(';')

      for x in range (0, len(split_string)):
        if(mycall == split_string[x].upper() ):
          self.debug.info_message("YES MY CALL IS SOMEWHERE ON THE LIST\n")
          return True

    except:
      self.debug.error_message("Exception in testAnywhereOnReceiveList: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return False

    self.debug.info_message("NO MY CALL IS NOT ANYWHERE ON THE LIST\n")
    return False


  def decodeAndSaveStub(self):
    self.debug.info_message("DECODE AND SAVE STUB\n")

    try:
      received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
      num_strings = self.getNumFragments(self.active_rig, self.active_channel) 

      fail = False
      got_how_many = 0
      while(got_how_many+1 <= num_strings and fail == False):
        if(self.group_arq.operating_mode == cn.FLDIGI):
          key = '[F' + str(got_how_many + 1) + ',' + str(num_strings) + ']'
          self.debug.info_message("testing stub. testing key: " + str(key) )
        elif(self.group_arq.operating_mode == cn.JS8CALL):
          key = '[' + self.getCharForIndex(got_how_many) 
          self.debug.info_message("testing stub. testing key: " + str(key) )

        if(key not in received_strings):
          fail = True
        else:
          got_how_many = got_how_many + 1

      stub = ''
      for x in range(1, got_how_many + 1):
        if(self.group_arq.operating_mode == cn.FLDIGI):
          key = '[F' + str(x) + ',' + str(num_strings) + ']'
          substring = received_strings[key].split(key, 1)[1]
          substring2 = substring.split('[', 1)[0]
          stub = stub + substring2
        elif(self.group_arq.operating_mode == cn.JS8CALL):
          key = '[' + self.getCharForIndex(x-1) 
          substring = received_strings[key].split(key, 1)[1]
          stub = stub + substring

      self.setStub(self.active_rig, self.active_channel, stub)
      self.debug.info_message("SETTING STUB TO: " + str(stub) )
      return stub

    except:
      self.debug.error_message("Exception in decodeAndSaveStub: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''

    return ''

  def testForStartFrame(self, receive_string):
    if('[F' in receive_string):
      split_string = receive_string.split('[F', 1)
      self.debug.info_message("LOOKS LIKE A START FRAME TAG TO ME\n")
      if(']' in split_string[1]):
        split_string2 = split_string[1].split(']', 1)
        numbers = split_string2[0].split(',', 1)
        try:
          frame_number = int(numbers[0])
          num_frames   = int(numbers[1])
          if(frame_number !=0 and num_frames != 0):
            self.debug.info_message("YES WE HAVE A FRAME TAG: " + str(frame_number) + ' ' + str(num_frames) )
            return '[F' + str(frame_number) + ',' + str(num_frames) + ']'
        except:
          #self.debug.info_message("Exception in testForStartFrame: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
          #self.debug.info_message("Exception in testForStartFrame")
          if('[F' in receive_string):
            split_string = receive_string.split('[F', 1)
            if(']' in split_string[1]):
              self.debug.info_message("DISCARDING ERRONEOUS TEXT\n")
              split_string2 = split_string[1].split(']', 1)
              self.discardErroneousText(split_string2[1])

          return ''			       

    if('[F' in receive_string):
      split_string = receive_string.split('[F', 1)
      if(']' in split_string[1]):
        self.debug.info_message("DISCARDING ERRONEOUS TEXT\n")
        split_string2 = split_string[1].split(']', 1)
        self.discardErroneousText(split_string2[1])

    return ''

  def testForStartFrameJS8(self, receive_string):
    try:
      if('[' in receive_string):
        split_string = receive_string.split('[', 1)
        if('[' in split_string[1]):
          frame_number = split_string[1][0]
          self.debug.info_message("YES WE HAVE A START FRAME TAG: \n")
          return '[' + frame_number
        else:
          return ''
    except:
      self.debug.info_message("Exception in testForStartFrameJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''
    return ''


  def testForEndFrame(self, start_frame_tag, receive_string):
    substring = receive_string.split(start_frame_tag, 1)[1]
    #self.debug.info_message("test for end frame: " + substring )
    if('[' in substring):
      split_string = substring.split('[', 1)
      if(']' in split_string[1]):
        split_string2 = split_string[1].split(']', 1)
        """ test to make sure this is not another start frame tag"""
        if(',' in split_string2[0]):
          self.debug.info_message("FAIL CONTAINED , so is a start frame\n")
          self.discardErroneousText('[' + split_string[1])
          return ''
          
        checksum = split_string2[0]

        self.debug.info_message("YES WE HAVE AN END FRAME TAG" )
        #self.debug.info_message("YES WE HAVE AN END FRAME TAG: " + str(checksum) )
        return '[' + str(checksum) + ']'
    
    #self.debug.info_message("FAIL")
    return ''

  def testForNextFrameJS8(self, start_frame_tag, receive_string):
    try:
      substring = receive_string.split(start_frame_tag, 1)[1]
      if('[' in substring):
        self.debug.info_message("YES WE HAVE A NEXT FRAME ([)")
        return '[' 
      elif(cn.EOM_JS8 in substring):
        self.debug.info_message("YES WE HAVE A NEXT FRAME (/E)")
        return cn.EOM_JS8 
   
      self.debug.info_message("FAIL")
    except:
      self.debug.info_message("Exception in testForNextFrameJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''
    return ''


  def testForEndMessage(self, receive_string):

    if(']' + self.getEomMarker() + ' ' + self.getSenderCall() in receive_string):
      split_string = receive_string.split(']' + self.getEomMarker() + ' ' + self.getSenderCall(), 1)
      eom_tag  = split_string[0][-5:] + ']'
      split_string = receive_string.split(']' + self.getEomMarker() + ' ', 1)
      eom_call = split_string[1].split(' ')[0]
      if(eom_tag[0] == '[' and eom_tag[5] == ']' and eom_call == self.getSenderCall() ):
        #self.debug.info_message("EOM TAG: " + eom_tag + ' ' + eom_call )
        return eom_tag

    return ''

  """ This version of the EOM test assumes a 4 character CRC between EOM marker and callsign"""
  def testForEndMessageJS8(self, receive_string):
    try:
      if('[' in receive_string):
        split_string = receive_string.split('[', 1)[1]
        eom_text = split_string[5:7]

        sender_call_split = split_string.split(' ')
        if(len(sender_call_split) >= 2 and sender_call_split[1] == self.getSenderCall() and eom_text == self.getEomMarker()):
          self.debug.info_message("sender call is: " + sender_call_split[1])

          frag_num = split_string[0]
          self.debug.info_message("YES WE HAVE AN EOM TAG\n")
          return '[' + frag_num 
        else:
          return ''
    except:
      self.debug.info_message("Exception in testForEndMessageJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''
    return ''

  """ This version of the EOM test tests only for EOM marker + callsign"""
  def testForEndMessageAltJS8(self, receive_string):

    if(cn.EOM_JS8 + ' ' + self.getSenderCall() in receive_string):
      return cn.EOM_JS8

    return ''


  def testForQryAckMessageJS8(self, receive_string):
    if(cn.COMM_QRYACK_MSG + self.getSenderCall() in receive_string):
      return cn.COMM_QRYACK_MSG
    return ''



  def extractEndMessageContentsJS8(self, receive_string):
    try:
      if('[' in receive_string):
        split_string = receive_string.split('[', 1)[1]
        eom_text = split_string[5:7]
        if(eom_text == self.getEomMarker()):

          #FIXME!!!!!!!!!!!!!!!!!!NEEDS TO HANDLE DIFFERENT LENGTH CHECKSUMS

          checksum = split_string[1:5]
          #self.debug.info_message("checksum, eom_text, eom_callsign: " + checksum + "," + eom_text )
          self.debug.info_message("YES WE HAVE AN EOM TAG\n")

          self.setRcvString(self.active_rig, self.active_channel, split_string[7:])

          return checksum + eom_text
        else:
          return ''
    except:
      self.debug.info_message("Exception in extractEndMessageContentsJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''
    return ''


  def extractEndMessageAltContentsJS8(self, receive_string):
    try:
      if(cn.EOM_JS8 in receive_string):
        split_string = receive_string.split(cn.EOM_JS8 + ' ' + self.getSenderCall() )
        self.debug.info_message("YES WE HAVE AN EOM TAG\n")
        self.setRcvString(self.active_rig, self.active_channel, split_string[1])
        return cn.EOM_JS8
    except:
      self.debug.info_message("Exception in extractEndMessageContentsJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''
    return ''


  def discardErroneousText(self, newtext):
    self.fldigiclient.setReceiveString(newtext)
    return
    
  def extractFrameContents(self, start_frame_tag, end_frame_tag, receive_string):
    substring = receive_string.split(start_frame_tag, 1)[1]
    substring2 = substring.split(end_frame_tag, 1)[0]

    """ pull this out of the receive string so that it is not decoded again """
    self.fldigiclient.setReceiveString(substring.split(end_frame_tag, 1)[1])
    return substring2

  def extractFrameContentsJS8(self, start_frame_tag, next_frame_tag, receive_string):
    substring = receive_string.split(start_frame_tag, 1)[1]
    substring2 = substring.split(next_frame_tag, 1)[0]

    """ pull this out of the receive string so that it is not decoded again """
    self.setRcvString(self.active_rig, self.active_channel, '[' + substring.split(next_frame_tag, 1)[1])

    self.debug.info_message("contents is: " + substring2 )
    return substring2


  """ this method validates the full received string """  
  def validateFrame(self, text, checksum):
    self.debug.info_message("validateFrame")
    return (self.getChecksum(text) == checksum)


  def getNumFramesTag(self, start_frame_tag):
    split_string = start_frame_tag.split('[F', 1)
    split_string2 = split_string[1].split(']', 1)
    numbers = split_string2[0].split(',', 1)
    num_frames   = int(numbers[1])
    return num_frames


  def sendFormJS8(self, message, tolist):

    self.debug.info_message("send form JS8 sending form: " + message )

    self.setInSession(self.tx_rig, self.tx_channel, True)

    if(tolist != ''):
      recipient_stations = tolist.split(';')
      self.setRecipientStations(self.tx_rig, self.tx_channel, recipient_stations)

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      self.setPreMessage('', '')
      pre_message = self.getPreMessage()
    else:
      pre_message = ''

    message = pre_message + message

    """ send the full message to the group first """
    mycall = self.getMyCall()
    mygroup = self.getMyGroup()
    msg_addressed_to = ' ' + mycall + ': ' + mygroup + ' '

    self.setMessage(self.tx_rig, self.tx_channel, msg_addressed_to + ' BOS ' + message)
    self.setCurrentRecipient(self.tx_rig, self.tx_channel, 0)

    self.setTxidState(self.tx_rig, self.tx_channel, True)
    """ send the full message to the group first """

    #FIXME NOT NEEDED NOW!
    self.setSendToGroupIndividual(self.tx_rig, self.tx_channel, cn.SENDTO_GROUP)

    self.sendFormJS8Common(message, msg_addressed_to)

  def sendFormJS8Common(self, message, msg_addressed_to):
    self.debug.info_message("sendFormJS8. message: " + message)

    self.setRetransmitCount(self.tx_rig, self.tx_channel, 0)
    self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, 0)

    current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
    num_recipients = len(recipient_stations)
    self.debug.info_message("loc 1 current_recipient, num_recipients: " + str(current_recipient) + ',' + str(num_recipients)  )

    if(current_recipient < num_recipients):

      """ reset the tx timer """
      self.setFrameRcvTime(self.tx_rig, self.tx_channel, datetime.now())

      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_ACKNACK)
    else:
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)

    return


  def setTransmitType(self, msg_type):
    self.setTxMsgType(self.tx_rig, self.tx_channel, msg_type)

  def getTransmitType(self):
    return self.getTxMsgType(self.tx_rig, self.tx_channel)


  def ifSeqSetMode(self, modetype):

    transmitType = self.getTransmitType()

    self.debug.info_message("resendFrames. transmit type: " + str(transmitType) )

    checked = False
    selected_mode = ''
    if( transmitType == cn.FORMAT_FILE or transmitType == cn.FORMAT_IMAGE):
      checked = self.form_gui.window['cb_filexfer_useseq'].get()
      if(checked):
        selected_mode = self.form_gui.window['option_filexfer_selectedseq'].get()
    elif( transmitType == cn.FORMAT_HRRM):
      checked = self.form_gui.window['cb_outbox_useseq'].get()
      if(checked):
        selected_mode = self.form_gui.window['option_outbox_selectedseq'].get()
    elif( transmitType == cn.FORMAT_WL2K):
      checked = self.form_gui.window['cb_winlink_useseq'].get()
      if(checked):
        selected_mode = self.form_gui.window['option_winlink_selectedseq'].get()
    if(checked):
      self.debug.info_message("resendFrames. Sequence: " + str(selected_mode) )
      self.setTxidState(self.tx_rig, self.tx_channel, True)
      seq = self.form_dictionary.retrieveSequenceByName(self.main_params, selected_mode)

      if(modetype == cn.TYPE_FRAG):
        modes = seq.get('frag_modes').split(',')
        self.max_frag_retransmits = seq.get('fragment_retransmits')
        self.max_qry_acknack_retransmits = seq.get('acknack_retransmits')
        retransmit_count = self.getRetransmitCount(self.tx_rig, self.tx_channel)
        self.debug.info_message("resendFrames. Retransmit count: " + str(retransmit_count) )
        self.fldigiclient.setMode(modes[retransmit_count])
        self.debug.info_message("resendFrames. Mode: " + str(modes[retransmit_count]) )
      elif(modetype == cn.TYPE_CONTROL):
        mode = seq.get('control_mode')
        self.fldigiclient.setMode(mode)
        self.debug.info_message("requestConfirm. Mode: " + str(mode) )

    else:
      self.max_frag_retransmits = 10
      self.max_qry_acknack_retransmits = 2

    return

  def sendFormFldigi(self, message, tolist, msgid):
    self.debug.info_message("send form fldigi sending form: " + message )

    self.debug.info_message("send form fldigi tolist is : " + tolist )

    self.setInSession(self.tx_rig, self.tx_channel, True)

    if(tolist != ''):
      recipient_stations = tolist.split(';')
      self.setRecipientStations(self.tx_rig, self.tx_channel, recipient_stations)

    self.setMessageID(self.tx_rig, self.tx_channel, msgid)

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      self.setPreMessage('', '')
      pre_message = self.getPreMessage()
    else:
      pre_message = ''

    message = pre_message + message

    """ send the full message to the group first """
    mycall = self.getMyCall()
    mygroup = self.getMyGroup()

    connect_to_list = self.group_arq.getRelayListFromSendList(tolist)

    msg_addressed_to = ' ' + mycall + ': ' + connect_to_list + mygroup + ' '

    self.setMessage(self.tx_rig, self.tx_channel, msg_addressed_to + ' BOS ' + message)
    self.setCurrentRecipient(self.tx_rig, self.tx_channel, 0)

    self.setTxidState(self.tx_rig, self.tx_channel, True)
    """ send the full message to the group first """

    self.ifSeqSetMode(cn.TYPE_FRAG)

    #FIXME NOT NEEDED NOW!
    self.setSendToGroupIndividual(self.tx_rig, self.tx_channel, cn.SENDTO_GROUP)

    self.sendFormFldigi2(message, msg_addressed_to)

  def sendFormFldigi2(self, message, msg_addressed_to):
    self.debug.info_message("send form fldigi sending form: " + message )

    self.setRetransmitCount(self.tx_rig, self.tx_channel, 0)
    self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, 0)

    current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
    num_recipients = len(recipient_stations)
    self.debug.info_message("loc 1 current_recipient, num_recipients: " + str(current_recipient) + ',' + str(num_recipients)  )

    if(current_recipient < num_recipients):
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.fldigiclient.sendItNowFldigi(msg_addressed_to + ' BOS ' + message)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_ACKNACK)

    else:
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)

    return


  def getRunLengthEncodeNackFldigi(self, message):

    self.debug.info_message("getRunLengthEncodeNackFldigi")

    self.debug.info_message("getRunLengthEncodeNackFldigi message:" + str(message))

    if(message == 'ALL'):
      return message

    frames = message.split(',')
    rle_frames = ''
    num_frames = len(frames)

    in_sequence = False
    last_number = -1
    for frame_count in range(0, num_frames):
      next_number = int(frames[frame_count][1:])
      self.debug.info_message("next_number: " + str(next_number) )
      if(next_number == last_number + 1 and in_sequence == False):
        self.debug.info_message("LOC 1\n")
        in_sequence = True
        rle_frames = rle_frames + 'F' + str(last_number) + '-'
        last_number = next_number
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + str(next_number)
      elif(next_number == last_number + 1 and in_sequence == True):
        self.debug.info_message("LOC 2\n")
        last_number = next_number
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + str(next_number)
      elif(next_number != last_number + 1 and in_sequence == True):
        self.debug.info_message("LOC 3\n")
        in_sequence = False
        rle_frames = rle_frames + str(last_number) + ','
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + 'F' + str(next_number)

        last_number = next_number
      else:
        self.debug.info_message("LOC 4\n")
        if(last_number != -1):
          rle_frames = rle_frames + 'F' + str(last_number)
          if(frame_count < num_frames-1):
            rle_frames = rle_frames + ','
        else:
          if(frame_count == num_frames-1):
            rle_frames = rle_frames + 'F' + str(next_number)

        last_number = next_number

    return rle_frames


  def getRunLengthDecodeNackFldigi(self, message):

    self.debug.info_message("getRunLengthDecodeNackFldigi\n")

    frames = message.split(',')
    rld_frames = ''
    num_frames = len(frames)

    in_sequence = False
    last_number = -1
    for frame_count in range(0, num_frames):
      if('-' in frames[frame_count]):
        nums = frames[frame_count].split('-',1)
        first_num  = int(nums[0][1:])
        second_num = int(nums[1])
        for x in range(first_num, second_num+1):
          rld_frames = rld_frames + 'F' + str(x)
          if(x < second_num or frame_count < num_frames-1):
            rld_frames = rld_frames + ','

      else:
        rld_frames = rld_frames + frames[frame_count]
        if(frame_count < num_frames-1):
          rld_frames = rld_frames + ','

    return rld_frames


  def sendQuerySAAM(self, from_callsign, group_name):
    message = ' ' + from_callsign + ': ' + group_name + cn.COMM_QRYSAAM_MSG + from_callsign + ' '
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return


  def sendTestProp(self, from_callsign, group_name):

    selection_list = self.fldigiclient.getModeSelectionList()
    self.debug.info_message("sendTestProp. selection list is: " + str(selection_list) )

    random_mode = (random.choice(selection_list)).split(' ')[3]
    self.debug.info_message("random item is: " + str(random_mode) )

    self.fldigiclient.setMode(random_mode)

    message = ''

    ID, grid, hop = self.form_dictionary.getRandomPeerstnDictItem()
    self.pre_message = self.createPreMessageDataFlecBeac(ID, grid, hop)

    pending = self.createPreMessagePend() 
    if(pending != ''):
      self.pre_message = self.pre_message + ',' + pending

    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + group_name + ' ' + pre_message + cn.COMM_TESTPROP + from_callsign + ' '

    """
    set the Txid on for CQ messages
    """
    self.setTxidState(self.tx_rig, self.tx_channel, True)

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return


  """
  creates three types of data flec for each CQ message...
  BEAC for my station
  BEAC for my peer stations
  BEAC for my relay stations
  """
  def buildPreMessageForCQCOPYRR73_TYPE1(self, from_callsign, group_name):

    """ BEAC for my peer stations"""
    ID, grid, hop = self.form_dictionary.getRandomPeerstnDictItem()
    sendstring = ''
    delimeter = ''
    if(ID != ''):  
      sendstring = sendstring + self.createPreMessageDataFlecBeac(ID, grid, hop)

    """ BEAC for my relay stations"""
    if(sendstring != ''):
      delimeter = ','
    relaycall, relayID, relaygrid, relayhops = self.form_dictionary.getRandomRelaystnDictItem()
    if(relaycall != ''):  
      sendstring = sendstring + delimeter + self.createPreMessageDataFlecBeac(relayID, relaygrid, relayhops)

    """ BEAC for my station """
    if(sendstring != ''):
      delimeter = ','
    from_callsign = self.getMyCall()
    myStnID = self.getEncodeUniqueId(from_callsign)
    mygrid = self.form_gui.window['input_myinfo_gridsquare'].get()
    self.debug.info_message("buildPreMessageForCQCOPYRR73_TYPE1 MYGRID = " + mygrid)
    myhops = '1'
    sendstring = sendstring + delimeter + self.createPreMessageDataFlecBeac(myStnID, mygrid, myhops)

    return sendstring


  """
  sends grid square info
  INFO(GRID   for my station
  INFO(SNR    for station in QSO
  """
  def buildPreMessageForCQCOPYRR73_TYPE2(self, from_callsign, group_name):

    talking_to_station = self.form_gui.window['in_inbox_listentostation'].get()

    num, grid, connect, rig, modulation, snr, last_heard = self.form_dictionary.getItemsForPeerstnDictItem(talking_to_station)

    mygrid = self.form_gui.window['input_myinfo_gridsquare'].get()
    from_callsign = self.getMyCall()
    myStnID = self.getEncodeUniqueId(from_callsign)

    """ INFO(GRID for my station"""
    sendstring = ''
    delimeter = ''
    part_msg = self.createPreMessageInfoGRIDDataFlec(myStnID, mygrid)
    if(part_msg != ''):  
      sendstring = sendstring + part_msg
      delimeter = ','

    """ INFO(SNR for station in QSO"""
    if(snr != ''):
      part_msg = self.createPreMessageInfoSNRDataFlec(snr)
      if(part_msg != ''):  
        sendstring = sendstring + delimeter + part_msg
        delimeter = ','

    return sendstring


  def sendCQCQCQ(self, from_callsign, group_name):

    selected_mode = self.form_gui.window['option_main_fldigimode'].get().split(' - ')[1]
    self.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected main mode is: " + selected_mode)

    message = ''
    self.pre_message = self.buildPreMessageForCQCOPYRR73_TYPE1(from_callsign, group_name)
    self.debug.info_message("sendstring is " + self.pre_message)
    message = ' ' + from_callsign + ': ' + group_name + ' ' + self.getPreMessage() + cn.COMM_CQCQCQ + from_callsign + ' '

    """
    set the Txid on for CQ messages
    """
    self.setTxidState(self.tx_rig, self.tx_channel, True)
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  """
  MSG_FORMAT_TYPE_3
  <From Call Sign>: <To call sign> COMMAND <From Call Sign>  
  WH6GGO: WH6ABC COPY WH6GGO
  """
  def sendCopy(self, from_callsign, group_name):
    message = '' 
    send_to = self.form_gui.window['in_inbox_listentostation'].get().strip()
    self.pre_message = self.buildPreMessageForCQCOPYRR73_TYPE1(from_callsign, group_name)
    self.debug.info_message("sendstring is " + self.pre_message)
    message = ' ' + from_callsign + ': ' + send_to + ' ' + self.getPreMessage() + cn.COMM_COPY + from_callsign + ' '

    """
    set the Txid on for CQ messages
    """
    self.setTxidState(self.tx_rig, self.tx_channel, True)
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendRR73(self, from_callsign, group_name):
    message = ''

    send_to = self.form_gui.window['in_inbox_listentostation'].get().strip()

    self.pre_message = self.buildPreMessageForCQCOPYRR73_TYPE2(from_callsign, group_name)
    self.debug.info_message("sendstring is " + self.pre_message)

    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + send_to + ' ' + pre_message + cn.COMM_RR73 + from_callsign + ' '

    """
    set the Txid on for CQ messages
    """
    self.setTxidState(self.tx_rig, self.tx_channel, True)

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def send73(self, from_callsign, group_name):
    message = ''

    send_to = self.form_gui.window['in_inbox_listentostation'].get().strip()

    self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_73', False)

    self.pre_message = self.buildPreMessageForCQCOPYRR73_TYPE2(from_callsign, group_name)
    self.debug.info_message("sendstring is " + self.pre_message)

    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + send_to + ' ' + pre_message + cn.COMM_73 + from_callsign + ' '

    """
    set the Txid on for CQ messages
    """
    self.setTxidState(self.tx_rig, self.tx_channel, True)

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendCheckin(self, from_callsign, group_name):

    message = ''
    self.pre_message = self.createPreMessageBeac() + ',' + self.createPreMessagePend() + ',' + self.createPreMessageConf() + ',' + self.createPreMessageReqm()
    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + group_name + ' ' + pre_message + cn.COMM_CHECKIN + from_callsign + ' '

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendStandby(self, from_callsign, group_name):

    selected_mode = self.form_gui.window['option_main_fldigimode'].get().split(' - ')[1]
    self.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected main mode is: " + selected_mode)

    message = ''
    self.pre_message = self.createPreMessageBeac()

    pending = self.createPreMessagePend() 
    if(pending != ''):
      self.pre_message = self.pre_message + ',' + pending

    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + group_name + ' ' + pre_message + cn.COMM_STANDBY + from_callsign + ' '

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendQrt(self, from_callsign, group_name):

    selected_mode = self.form_gui.window['option_main_fldigimode'].get().split(' - ')[1]
    self.fldigiclient.setMode(selected_mode)
    self.debug.info_message("selected main mode is: " + selected_mode)

    message = ''
    self.pre_message = ''
    pre_message = self.getPreMessage()
    message = ' ' + from_callsign + ': ' + group_name + cn.COMM_QRT + from_callsign + ' '

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendSAAM(self, from_callsign, group_name):

    message = '' 

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      self.pre_message = self.createPreMessageBeac() + ',' + self.createPreMessagePend() + ',' + self.createPreMessageConf() + ',' + self.createPreMessageReqm()
      pre_message = self.getPreMessage()
      message = ' ' + from_callsign + ': ' + group_name + ' ' + pre_message + cn.COMM_SAAM_MSG + from_callsign + ' '
    else:
      pre_message = ''
      message = ' ' + from_callsign + ': ' + group_name + cn.COMM_SAAM_MSG + from_callsign + ' '

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendAbort(self, from_callsign, group_name):

    self.setInSession(self.tx_rig, self.tx_channel, False)
    self.setInSession(self.active_rig, self.active_channel, False)

    #self.group_arq.fldigiclient.setReceiveString('')
    #self.group_arq.fldigiclient.resetLastTwenty()

    self.debug.info_message("ABORT BUTTON PRESSED\n")
    if(self.group_arq.operating_mode == cn.FLDIGI):
      self.group_arq.fldigiclient.abortTransmit()

    self.resetRcvString(self.active_rig, self.active_channel)
    self.resetReceivedStrings(self.active_rig, self.active_channel)
    self.setEOMReceived(self.active_rig, self.active_channel, False)
    self.setCommStatus(self.active_rig, self.active_channel, cn.COMM_LISTEN)

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)

    #self.form_gui.form_events.changeFlashButtonState('text_mainarea_insession', False)

    return


  def sendREQM(self, from_callsign, to_callsign, msgid):
    message = ' ' + from_callsign + ': ' + to_callsign + cn.COMM_REQM_MSG + ' ' + msgid + ' ' + from_callsign + ' '
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return



  def sendCommon(self, command, msgid):
    from_callsign = self.getMyCall()
    to_callsign   = self.getSenderCall()

    if(msgid == None):
      message = ' ' + from_callsign + ': ' + to_callsign + command + ' ' + from_callsign + ' '
    else:
      message = ' ' + from_callsign + ': ' + to_callsign + command + ' ' + msgid + ' ' + from_callsign + ' '

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.group_arq.sendItNowRig1(message)
    return

  def sendSaamQrt(self):
    self.sendCommon(cn.COMM_SAAMQRT_MSG, None)

  def sendConf(self):
    self.sendCommon(cn.COMM_CONF_MSG, None)

  def sendQryReady(self):
    self.sendCommon(cn.COMM_QRYRDY_MSG, None)

  def sendReadyToReceive(self):
    self.sendCommon(cn.COMM_RR_MSG, None)

  def sendNotReady(self):
    self.sendCommon(cn.COMM_NR_MSG, None)

  def sendCancelHaveCopy(self):
    self.sendCommon(cn.COMM_CCL_MSG, None)


  def toSendOrNotToSend(self):
    sendit = False

    self.debug.info_message("toSendOrNotToSend. senderCall: " + self.getSenderCall() )
    """ if the field is empty then do not reply back we are listening only"""
    if(self.getSenderCall() == ''):
      return False

    if( self.getWhatWhere(self.active_rig, self.active_channel) == cn.FRAGMENTS_TO_GROUP):
      self.debug.info_message("toSendOrNotToSend addressed to GROUP")
      """ now check the stub to see if I am the first callsign in the list"""

      #FIXME remove the following line as already processed....
      stub = self.decodeAndSaveStub()

      mycall = self.getMyCall() 
      if(stub != '' and self.testFirstOnReceiveList(stub, mycall)==True):
        sendit = True
        self.debug.info_message("toSendOrNotToSend. I am first on receive list")

    elif( self.getWhatWhere(self.active_rig, self.active_channel) == cn.QRYACKNACK_TO_ME):
      sendit = True
      self.debug.info_message("toSendOrNotToSend. QRYACKNACK_TO_ME")
    elif( self.getWhatWhere(self.active_rig, self.active_channel) == cn.FRAGMENTS_TO_ME):
      sendit = True
      self.debug.info_message("toSendOrNotToSend. FRAGMENTS_TO_ME")

    self.debug.info_message("toSendOrNotToSend sendit is: " + str(sendit) )
    return sendit

  """ 
  format:
  ACK <TOCALL> <FROMCALL>
  """
  def sendAck(self, from_callsign, to_callsign):

    try:
      sendit = self.toSendOrNotToSend()
      if(sendit == False):
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
      else:
        ack_message = to_callsign + cn.COMM_ACK_MSG + from_callsign + ' '
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
        self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)
        self.group_arq.sendItNowRig1(ack_message)
    except:
      self.debug.error_message("Exception in sendAck: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return


  def sendNack(self, frames, from_callsign, to_callsign):

    sendit = self.toSendOrNotToSend()
    if(sendit == False):
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    else:
      self.debug.info_message("sendNack frames:" + str(frames))
      frames = self.getRunLengthEncodeNackFldigi(frames)
      nack_message = to_callsign + cn.COMM_NACK_MSG + '(' + frames + ') ' + from_callsign + ' '
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_RESEND)
      self.group_arq.sendItNowRig1(nack_message)
    return

  def sendAckJS8(self, from_callsign, to_callsign):
    sendit = self.toSendOrNotToSend()
    if(sendit == False):
      self.resetRcvString(self.active_rig, self.active_channel)
      self.resetReceivedStrings(self.active_rig, self.active_channel)
      self.setEOMReceived(self.active_rig, self.active_channel, False)
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    else:
      ack_message = to_callsign + cn.COMM_ACK_MSG + from_callsign + ' '
      comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)
      if(comm_status == cn.COMM_RECEIVING):
        self.setMessage(self.tx_rig, self.tx_channel, ack_message)
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
        self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)

        """ the following relate to the receive channel and not the TX channel"""
        self.resetReceivedStrings(self.active_rig, self.active_channel)
        self.setEOMReceived(self.active_rig, self.active_channel, False)
        self.resetRcvString(self.active_rig, self.active_channel)
    return

  def sendNackJS8(self, frames, num_fragments, from_callsign, to_callsign):
    sendit = self.toSendOrNotToSend()
    if(sendit == False):
      self.resetRcvString(self.active_rig, self.active_channel)
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    else:
      self.debug.info_message("sendNackJS8")

      nack_message = to_callsign + cn.COMM_NACK_MSG + self.createNackCodeJS8(frames, num_fragments) + cn.EOM_JS8 + ' ' + from_callsign + ' '

      comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)
      if(comm_status == cn.COMM_RECEIVING or comm_status == cn.COMM_AWAIT_RESEND):
        self.resetRcvString(self.active_rig, self.active_channel)
        self.setMessage(self.tx_rig, self.tx_channel, nack_message)
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
        self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_RESEND)
    return

  def sendDirected(self, message, to_callsign):
    if(self.tx_mode == 'JS8CALL'):
      self.debug.info_message("CALLING SEND DIRECTED JS8\n")
      self.sendDirectedJS8(message, to_callsign)

  def send(self, message):
    if(self.tx_mode == 'JS8CALL'):
      self.debug.info_message("CALLING SEND JS8\n")
      self.sendJS8(message)

  def sendDirectedJS8(self, message, to_callsign):
    self.debug.info_message("SEND DIRECTED JS8\n")
    send_string = to_callsign + ' ' + message

    comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)
    if(comm_status == cn.COMM_RECEIVING):
      self.setMessage(self.tx_rig, self.tx_channel, send_string)
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)

    return

  def sendJS8(self, message):

    comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)
    if(comm_status == cn.COMM_RECEIVING):
      self.setMessage(self.tx_rig, self.tx_channel, message)
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)

    return

  def requestConfirm(self, from_callsign, to_callsign):

    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
    to_callsign = recipient_stations[self.getCurrentRecipient(self.tx_rig, self.tx_channel)]

    self.setTxidState(self.tx_rig, self.tx_channel, False)

    self.ifSeqSetMode(cn.TYPE_CONTROL)

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_ACKNACK)
    """ add an extra space on the end making a total of two spaces following the ?"""
    if(self.tx_mode == 'FLDIGI'):
      self.group_arq.sendItNowRig1('      ' + to_callsign + cn.COMM_QRYACK_MSG + from_callsign + ' '  )
    else:
      self.group_arq.sendItNowRig1(to_callsign + cn.COMM_QRYACK_MSG + from_callsign + ' '  )
    return 

  def resendFrames(self, frames, from_callsign, to_callsign):
    self.debug.info_message("resendFrames. frames: " + str(frames) )

    self.ifSeqSetMode(cn.TYPE_FRAG)

    frames_list = frames.split(',')
    received_strings = self.getReceivedStrings(self.tx_rig, self.tx_channel)
    resend_string = ''

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      self.setPreMessage('', '')
      pre_message = self.getPreMessage()
    else:
      pre_message = ''

    resend_string = pre_message + resend_string

    self.debug.info_message("RESEND FRAMES 2\n")
    for x in range (len(frames_list)):
      self.debug.info_message("RESEND FRAMES 3\n")
      resend_frame = received_strings['[' + frames_list[x] + ',' + str(len(received_strings)) + ']'] 
      resend_string = resend_string + resend_frame
    
    self.debug.info_message("RESEND FRAMES 4\n")

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_ACKNACK)
    self.group_arq.sendItNowRig1(from_callsign + ': ' + to_callsign + ' ' + resend_string + ' ' + from_callsign + ' ')

    return

  def resendFramesJS8(self, frames, from_callsign, to_callsign):
    self.debug.info_message("resendFramesJS8. frames: " + str(frames))
    received_strings = self.getReceivedStrings(self.tx_rig, self.tx_channel)

    self.debug.info_message("resendFramesJS8. received strings: " + str(received_strings))

    resend_string = to_callsign + ' ' 
    self.debug.info_message("RESEND FRAMES 2\n")
    for x in range (len(frames)):
      self.debug.info_message("RESEND FRAMES 3\n")
      resend_frame = received_strings['[' + frames[x] ] 
      resend_string = resend_string + resend_frame
    
    self.debug.info_message("RESEND FRAMES 4\n")
    self.debug.info_message("resend string: " + str(resend_string) )

    self.setMessage(self.tx_rig, self.tx_channel, resend_string + cn.EOM_JS8 + ' ' + from_callsign + ' ')
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_AWAIT_ACKNACK)

    return

  def processAck(self, rig, channel):

    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)

    current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)


    #"""
    try:
      self.debug.info_message("processAck recipient station that confirmed is : " + str(recipient_stations[current_recipient])  )
    
      msgid = self.getMessageID(self.tx_rig, self.tx_channel)
      dictionary_item = self.form_dictionary.getRelayboxDictionaryItem(msgid)
      confrcvd  = dictionary_item.get('confrcvd')

      for count in range(5):
        confrcvd = confrcvd.replace(recipient_stations[current_recipient], '')
        confrcvd = (confrcvd.replace(';;', ';')).strip(';')
      calls_confirmed = confrcvd + ';' + recipient_stations[current_recipient]
      calls_confirmed = (calls_confirmed.replace(';;', ';')).strip(';')

      dictionary_item['confrcvd'] = calls_confirmed

      self.debug.info_message("to: " + dictionary_item.get('to') )
      self.debug.info_message("calls confirmed: " + calls_confirmed )

      if( dictionary_item.get('to') == calls_confirmed):
        self.form_dictionary.transferRelayboxMsgToSentbox(msgid)


      self.setCallsignsConfirmed(self.tx_rig, self.tx_channel, calls_confirmed)

      self.group_arq.updateRelayboxValue(msgid, 7, calls_confirmed)
      self.group_arq.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
      self.group_arq.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())
    except:
      self.debug.error_message("Exception in processAck: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    num_recipients = len(recipient_stations)
    self.debug.info_message("loc 2 current_recipient, num_recipients: " + str(current_recipient) + ',' + str(num_recipients)  )

    self.setRetransmitCount(self.tx_rig, self.tx_channel, 0)

    if(current_recipient < num_recipients):
      self.advanceToNextRecipient()
    
    return

  def processAckJS8(self, rig, channel):
    self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
    self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_NONE)

    current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
    num_recipients = len(recipient_stations)
    self.debug.info_message("loc 2 current_recipient, num_recipients: " + str(current_recipient) + ',' + str(num_recipients)  )

    self.setRetransmitCount(self.tx_rig, self.tx_channel, 0)

    #FIXME
    self.resetRcvString(self.active_rig, self.active_channel)

    if(current_recipient < num_recipients):
      self.advanceToNextRecipient()
    
    return

  def processNack(self, from_callsign, to_callsign, rig, channel):

    receive_string = self.group_arq.getReceiveStringRig1()  
    tx_strings = self.getReceivedStrings(self.tx_rig, self.tx_channel)

    self.setTxidState(self.tx_rig, self.tx_channel, False)
    """ send the full message to the group first """
    self.setSendToGroupIndividual(self.tx_rig, self.tx_channel, cn.SENDTO_INDIVIDUAL)

    split_string = receive_string.split(cn.COMM_NACK_MSG + '(', 1)
    split_string2 = split_string[1].split(')', 1)
    missing_frames = self.getRunLengthDecodeNackFldigi(split_string2[0] ) +')'

    verified_missing_frames = ''

    if(split_string2[0] == 'All'):
      self.debug.info_message("All fragments need to be re-transmitted")
      for frame_key in tx_strings:
        trimmed_frame_key = frame_key.split('[',1)[1].split(',',1)[0]
        if(verified_missing_frames == ''):
          verified_missing_frames = trimmed_frame_key
        else:
          verified_missing_frames = verified_missing_frames + ',' + trimmed_frame_key
    else:
    #if(True):
      for frame_key in tx_strings:
        trimmed_frame_key = frame_key.split('[',1)[1].split(',',1)[0]
        self.debug.info_message("checking frame key: " + str(trimmed_frame_key) )
        if(trimmed_frame_key + ',' in missing_frames or trimmed_frame_key + ')' in missing_frames or 'ALL' in missing_frames):
          self.debug.info_message("adding to verified missing frames: " + str(trimmed_frame_key) )
          if(verified_missing_frames == ''):
            verified_missing_frames = trimmed_frame_key
          else:
            verified_missing_frames = verified_missing_frames + ',' + trimmed_frame_key


    self.debug.info_message("verified missing frames: " + str(verified_missing_frames) )
    self.resendFrames(verified_missing_frames, from_callsign, to_callsign)
    return verified_missing_frames

  def processNackJS8(self, from_callsign, to_callsign, rig, channel):
    self.debug.info_message("process nack JS8\n")
    receive_string = self.getAckNackCode(self.active_rig, self.active_channel).strip().split(cn.EOM_JS8, 1)[0]
    self.debug.info_message("received string is: " + str(receive_string) )
    tx_strings = self.getReceivedStrings(self.tx_rig, self.tx_channel)
    split_string = receive_string.split((cn.COMM_NACK_MSG).strip() + ' ', 1)
    nack_code = split_string[1]
    
    verified_missing_frames = ''

    if(nack_code[0]== '+'):
      verified_missing_frames = self.decodeNackCodeReceivedJS8(nack_code, rig)
    elif(nack_code[0]== '-'):
      verified_missing_frames = self.decodeNackCodeMissingJS8(nack_code, rig)

    self.resendFramesJS8(verified_missing_frames, from_callsign, to_callsign)
    self.debug.info_message("verified missing frames :" + verified_missing_frames )
    return verified_missing_frames


  """ This method creates a unique ID based on the callsign and the month, day, hour, minute, second"""
  def getEncodeUniqueId(self, callsign):
    self.debug.info_message("getEncodeUniqueId\n")

    """ new encode for timestamp """
    base_36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    encoded = ''
    temp_var = int(round(datetime.utcnow().timestamp()*100))

    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp((temp_var)/100.0)))
    self.debug.info_message("temp var is " + str(temp_var))

    while (temp_var != 0):
      temp_var, i = divmod(temp_var, 36)
      encoded = base_36[i] + encoded

    self.debug.info_message("encoded = " + encoded)
    self.debug.info_message("original number = " + str(int(encoded,36)))
    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp((int(encoded,36))/100.0)))

    """ prepare callsign encoding """
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
    charsLen = len(chars)
    num = 0
    for i, c in enumerate(reversed(callsign.upper())):
      num += chars.index(c) * (charsLen ** i)

    ID = '{:02x}'.format(num) + '_' + encoded

    return (ID)

  """ This method decodes the callsign from the ID string"""
  def getDecodeCallsignFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""

    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
    charsLen = len(chars)
    hexnum = '0x' + ID.split('_',1)[0]

    timestamp_string = ID.split('_',1)[1]

    inttime = ((int(timestamp_string,36))/100.0)
    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )

    intnum = int(hexnum,16)
    callsign = ""
    while intnum:
      callsign = chars[intnum % charsLen] + callsign
      intnum //= charsLen
    return callsign

  """ This method decodes the callsign from the ID string"""
  def getDecodeTimestampFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
    charsLen = len(chars)

    timestamp_string = ID.split('_',1)[1]

    inttime = ((int(timestamp_string,36))/100.0)
    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )
    timestamp = str(datetime.utcfromtimestamp(inttime) )

    self.debug.info_message("reverse encoded timestamp is: " + timestamp )
                                                                                        
    return timestamp


  """ This method decodes the callsign from the ID string"""
  def getDecodeIntTimeFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""
    timestamp_string = ID.split('_',1)[1]
    inttime = ((int(timestamp_string,36))/100.0)

    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )
                                                                                        
    return inttime
    

  """
  this method stores a record of which frames have been confirmed by a station
  frames confirmed:  F1,F3,F4
  """
  #NOT USED ?????!!!!!
  def setConfirmationStatus(self, callsign, ID, frames_confirmed):

    key = callsign + '_' + ID
    already_confirmed = ''
    callsigns_confirmed = self.getCallsignsConfirmed(self.active_rig, self.active_channel)
    if (key in callsigns_confirmed):
      already_confirmed = callsigns_confirmed[key]
      callsigns_confirmed[key] = already_confirmed + ',' + frames_confirmed
    else:
      callsigns_confirmed[key] = frames_confirmed
       
    return


  def getSetCallsignJS8(self, dict_obj, text, rigname, channel_name):
    # NEED TO FIGURE OUT CALLSIGN FROM TRANSMIT CHARS AS CALL ONLY PRESENT ON RX.DIRECTED?????

    callsign = self.getChannelCallsign(rigname, channel_name)
    if(callsign == '' or callsign == None or callsign == 'None'):
      callsign = self.js8client.getParam(dict_obj, "CALL")
      if(callsign != '' and callsign != None and callsign != 'None'):
        self.setChannelCallsign(rigname, channel_name, callsign)
        self.group_arq.addSelectedStation(callsign, ' ')
        self.debug.info_message("Channel callsign: " + callsign)
        return callsign

      if(": " in text):
        callsign = text.split(": ")[0]
        self.setChannelCallsign(rigname, channel_name, callsign)
        self.group_arq.addSelectedStation(callsign, ' ')
        self.debug.info_message("Channel callsign: " + callsign)
        return callsign

    return callsign


  def findCreateChannelJS8(self, dict_obj, rigname):

    offsetstr = self.js8client.getParam(dict_obj, "OFFSET")
    int_offset = int(offsetstr)

    js8_mode = ''
    frame_timing_seconds = 0
    js8_speed = self.js8client.getParam(dict_obj, "SPEED")
    if(js8_speed == cn.JS8CALL_SPEED_TURBO):
      self.debug.info_message("JS8 Speed TURBO") #6 seconds
      js8_mode = 'TURBO'
      frame_timing_seconds = 6
    elif(js8_speed == cn.JS8CALL_SPEED_FAST):
      self.debug.info_message("JS8 Speed FAST") #10 seconds
      js8_mode = 'FAST'
      frame_timing_seconds = 10
    elif(js8_speed == cn.JS8CALL_SPEED_NORMAL):
      self.debug.info_message("JS8 Speed NORMAL") #15 seconds
      js8_mode = 'NORMAL'
      frame_timing_seconds = 15
    elif(js8_speed == cn.JS8CALL_SPEED_SLOW):
      self.debug.info_message("JS8 Speed SLOW") #30 seconds
      js8_mode = 'SLOW'
      frame_timing_seconds = 30

    channel_name = str((round(int_offset / 25))*25) + '_' + 'JS8CALL' + '_' + js8_mode
    self.debug.info_message("Channel: " + channel_name)

    if(self.queryChannelItem(rigname,'JS8CALL', js8_mode, str((round(int_offset / 25))*25) ) == False):
      self.debug.info_message("ADDING NEW CHANNEL: " + channel_name)
      callsign = ''
      self.active_channel = self.addChannelItem(rigname,'JS8CALL', js8_mode, str((round(int_offset / 25))*25), '', callsign)
    else:
      self.active_channel = self.getChannelItem(rigname,'JS8CALL', js8_mode, str((round(int_offset / 25))*25) )

    self.setFrameTimingSeconds(rigname, channel_name, frame_timing_seconds)

    return self.active_channel
   
  """
  callback function used by JS8_Client processing thread
  """
  def js8_callback(self, json_string, txrcv, rigname, js8riginstance):

    self.ignore_processing = True

    line = json_string.split('\n')
    length = len(line)

    for x in range(length-1):
      dict_obj = json.loads(line[x])
      text = self.js8client.stripEndOfMessage(self.js8client.getValue(dict_obj, "value")).decode('utf-8')
      
      message_type = self.js8client.getValue(dict_obj, "type").decode('utf-8')
      last_call = None
     
      """ test to see if there are any missing frames """
      self.js8client.areFramesMissing(self.js8client.getValue(dict_obj, "value") )

      if (message_type == "STATION.CALLSIGN"):
        self.debug.info_message("my_new_callback. STATION.CALLSIGN")

      elif (message_type == "RIG.FREQ"):
        dialfreq = int(self.js8client.getParam(dict_obj, "DIAL"))
        freqstr = str(float(dialfreq)/1000000.0)
        offsetstr = self.js8client.getParam(dict_obj, "OFFSET")
          			
        self.debug.info_message("my_new_callback. RIG.FREQ. Dial: " + freqstr)
        self.debug.info_message("my_new_callback. RIG.FREQ, Offset: " + offsetstr)

      elif (message_type == "RX.SPOT"):
        self.debug.info_message("my_new_callback. RX.SPOT")
        self.updateChannelView(None)

      elif (message_type == "RX.DIRECTED"):

        self.debug.info_message("js8_callback. RX.DIRECTED")
        self.debug.info_message("message text received: " + text)

        channel = self.findCreateChannelJS8(dict_obj, rigname)
        self.debug.info_message("active rig:" + str(rigname) + '\n\n' )
        self.debug.info_message("active channel:" + str (channel)  )

        channel_callsign = self.getSetCallsignJS8(dict_obj, text, rigname, channel)
        self.debug.info_message("Channel callsign: " + channel_callsign)

        self.active_channel = channel

        self.debug.info_message("RX.DIRECTED ACKNACK CODE IS: " + text )
        frame_rcv_time = datetime.now()
        self.setFrameRcvTime(rigname, channel, frame_rcv_time)

        self.updateChannelView(None)

        
      elif (message_type == "RX.ACTIVITY"):
        self.debug.info_message("js8_callback. RX.ACTIVITY")

        channel = self.findCreateChannelJS8(dict_obj, rigname)
        self.debug.info_message("active rig:" + str(rigname) + '\n\n' )
        self.debug.info_message("active channel:" + str (channel)  )

        channel_callsign = self.getSetCallsignJS8(dict_obj, text, rigname, channel)
        self.debug.info_message("Channel callsign: " + channel_callsign)

        self.active_channel = channel

        missing_frames = self.js8client.areFramesMissing(text.encode() )
        if missing_frames>0:
          self.debug.info_message("RX.ACTIVITY. MISSING FRAMES: " + str(missing_frames) )
          """ blank out the rcv string as nothing guaranteed if frame is dropped """
          self.setRcvString(rigname, channel, '')
        else:
          self.debug.info_message("LOC GHI")

          self.appendRcvString(rigname, channel, text)
          self.debug.info_message("total rcvd string: " + self.getRcvString(rigname, channel))
          frame_rcv_time = datetime.now()
          self.setFrameRcvTime(rigname, channel, frame_rcv_time)
          self.debug.info_message("LOC JKL")

        comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)
        if(comm_status == cn.COMM_AWAIT_ACKNACK ):
          rcv_string = self.getRcvString(rigname, channel)
          if(cn.EOM_JS8 in rcv_string):
            self.setAckNackCode(rigname, channel, rcv_string.split(cn.EOM_JS8, 1)[0])

        self.updateChannelView(None)

      elif (message_type == "MODE.SPEED"):
        self.debug.info_message("js8 callback mode.speed")
        js8_speed = self.js8client.getParam(dict_obj, "SPEED")
        if(js8_speed == cn.JS8CALL_SPEED_TURBO):
          self.form_gui.window['option_outbox_js8callmode'].update('TURBO')
        elif(js8_speed == cn.JS8CALL_SPEED_FAST):
          self.form_gui.window['option_outbox_js8callmode'].update('FAST')
        elif(js8_speed == cn.JS8CALL_SPEED_NORMAL):
          self.form_gui.window['option_outbox_js8callmode'].update('NORMAL')
        elif(js8_speed == cn.JS8CALL_SPEED_SLOW):
          self.form_gui.window['option_outbox_js8callmode'].update('SLOW')
        
      elif (message_type == "RIG.PTT"):
        self.debug.info_message("my_new_callback. RIG.PTT")
        pttstate = self.js8client.getParam(dict_obj, "PTT")
        if(str(pttstate) =="False" ):
          self.debug.info_message("my_new_callback. RIG.PTT Start Timer")

          """ reset the tx timer """
          self.setFrameRcvTime(self.tx_rig, self.tx_channel, datetime.now())

        self.debug.info_message("my_new_callback. RIG.PTT PTT State: " + str(pttstate))
      elif (message_type == "TX.TEXT"):
        self.debug.info_message("my_new_callback. TX.TEXT")
      elif (message_type == "TX.FRAME"):
        self.debug.info_message("my_new_callback. TX.FRAME")
      elif (message_type == "STATION.STATUS"):
        dialfreq = int(self.js8client.getParam(dict_obj, "DIAL"))
        freqstr = str(float(dialfreq)/1000000.0)
        offsetstr = self.js8client.getParam(dict_obj, "OFFSET")
          			
        self.debug.info_message("my_new_callback. STATION.STATUS. Dial: " + freqstr)
        self.debug.info_message("my_new_callback. STATION.STATUS, Offset: " + offsetstr)
      else:
        self.debug.warning_message("my_new_callback. unhandled type: " + str(message_type) )

    self.ignore_processing = False

    return


  def js8_process_rcv(self): 

    rcv_string = self.getRcvString(self.active_rig, self.active_channel)

    msgfrom = self.getSenderCall()
    msggroup = self.getSentToGroup()
    msgme = self.getSentToMe()
    if(msgfrom + ':' + msggroup in rcv_string):
      self.debug.info_message("js8_process_rcv. FRAGMENTS_TO_GROUP")
      self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_GROUP)
    elif(msgfrom + ': ' + msggroup in rcv_string):
      self.debug.info_message("js8_process_rcv. FRAGMENTS_TO_GROUP")
      self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_GROUP)
    elif(msgfrom + ':' + msgme in rcv_string):
      self.debug.info_message("js8_process_rcv. FRAGMENTS_TO_ME")
      self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_ME)
    elif(msgfrom + ': ' + msgme in rcv_string):
      self.debug.info_message("js8_process_rcv. FRAGMENTS_TO_ME")
      self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_ME)

    command, remainder, from_call, param_1 = self.saam_parser.testAndDecodeCommands(rcv_string, cn.JS8CALL)
    if(command != cn.COMMAND_NONE):
      self.debug.info_message("process the commands in here\n")
      self.setRcvString(self.active_rig, self.active_channel, remainder)
      """ this was a command so we are done"""
      return
    succeeded, remainder = self.saam_parser.testAndDecodePreMessage(rcv_string, cn.JS8CALL)
    if(succeeded):
      self.setRcvString(self.active_rig, self.active_channel, remainder)

    """ now continue to decode the reset of the mssage"""

    start_frame_tag = self.testForStartFrameJS8(rcv_string)
    
    if(start_frame_tag != ''):
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_RECEIVING)
      start_frame_tag = self.gotStartFrameJS8(start_frame_tag)

    elif(self.testForEndMessageJS8(rcv_string) != '' ):
      self.debug.info_message("calling message ended\n")

      end_message_tag = self.testForEndMessageJS8(rcv_string)
      end_message_contents = self.extractEndMessageContentsJS8(rcv_string)
      self.addReceivedString(end_message_tag, end_message_tag + end_message_contents, self.active_rig, self.active_channel)
      num_strings = self.getIndexForChar(end_message_tag[1]) + 1
      self.setNumFragments(self.active_rig, self.active_channel, num_strings)
      self.setEOMReceived(self.active_rig, self.active_channel, True)
      received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
      self.messageEndedJS8(rcv_string)

    elif(self.testForEndMessageAltJS8(rcv_string) != '' ):
      self.debug.info_message("acknack message ended")

      #FIXME NOT NEEDED
      end_message_contents = self.extractEndMessageAltContentsJS8(rcv_string)

      self.messageEndedJS8(rcv_string)
    elif(self.testForQryAckMessageJS8(rcv_string) != '' ):
      self.debug.info_message("qry ack message")
      self.messageEndedJS8(rcv_string)
	  
    return()

  def recentNoData(self, instance, count):
    counter_value = instance.getNoDataCounter()
    if(counter_value < 100 and counter_value > count):
      return True
    else:
      return False

  def countAfterTransmit(self, instance, count):
    counter_value = instance.getRcvWaitTimer()
    if(counter_value < 100 and counter_value > count):
      return True
    else:
      return False


  """
  this is most relevant for modes that have very little spurious / noise decodes 
  The timings relate to elapsed time where there have been no characters / data / decodes received
  delay2 is the time slot in which the comparison occurrs.
  delay is the amount of time in milliseconds within that time slot that must elapse to trigger a True return
  """
  def recentNoDataDiff(self, instance, delay, delay2):

    delay2, delay = instance.getNoDataTimings()

    diff_sec, diff_millis = instance.getNoDataDiff()
    """ important TIMING value. silence period to make sure there is no additional data arriving"""
    if(diff_sec < delay2 and diff_millis > delay):
      return True
    else:
      return False

  """
  This is most relevant for modes that are noisy and have many spurious / noise decodes 
  The timings relate to elapsed time since end of transmit
  delay2 is the time slot in which the comparison occurrs.
  delay is the amount of time in milliseconds within that time slot that must elapse to trigger a True return
  """
  def countAfterTransmitDiff(self, instance, delay, delay2):

    delay2, delay = instance.getAfterXmitTimings()

    diff_sec, diff_millis = instance.getRcvWaitDiff()
    """ important TIMING value. 10 seconds. window after transmit where we need to see a reply"""
    if(diff_sec < delay2 and diff_millis > delay):
      return True
    else:
      return False


  def advanceToNextRecipient(self):
    current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
    recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
    num_recipients = len(recipient_stations)
    if(current_recipient < num_recipients):
      self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, 0)
      self.debug.info_message("advancing to next station: " + str(current_recipient+1) )

      while(current_recipient+1 < num_recipients):
        self.debug.info_message("advanceToNextRecipient LOC3")
        current_recipient = current_recipient + 1
        self.setCurrentRecipient(self.tx_rig, self.tx_channel, current_recipient)
        if( self.group_arq.isRecipientPresent(recipient_stations[self.getCurrentRecipient(self.tx_rig, self.tx_channel)]) == True):
          self.debug.info_message("advanceToNextRecipient LOC4")
          if(current_recipient < num_recipients):
            self.debug.info_message("advanceToNextRecipient LOC5")
            self.setPreMessage(recipient_stations[current_recipient], self.groupname)
            self.requestConfirm(self.getMyCall(), self.getSenderCall())
            return
          else:
            self.debug.info_message("advanceToNextRecipient LOC6")
            self.setInSession(self.tx_rig, self.tx_channel, False)
            from_callsign = self.getMyCall()
            to_callsign = self.getMyGroup()
            self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
            self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
            self.group_arq.sendItNowRig1(from_callsign + ': ' + to_callsign + ' EOS ' + from_callsign + ' ')
            return

      self.debug.info_message("advanceToNextRecipient: " + str(current_recipient)  )

      if(current_recipient+1 == num_recipients):
        self.debug.info_message("advanceToNextRecipient LOC7")
        self.setInSession(self.tx_rig, self.tx_channel, False)
        from_callsign = self.getMyCall()
        to_callsign = self.getMyGroup()
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
        self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
        self.group_arq.sendItNowRig1(from_callsign + ': ' + to_callsign + ' EOS ' + from_callsign + ' ')
        return

    else:
      """ abort station retransmits and move onto the next station """
      self.setInSession(self.tx_rig, self.tx_channel, False)

      from_callsign = self.getMyCall()
      to_callsign = self.getMyGroup()
      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_QUEUED_TXMSG)
      self.setExpectedReply(self.tx_rig, self.tx_channel, cn.COMM_LISTEN)
      self.group_arq.sendItNowRig1(from_callsign + ': ' + to_callsign + ' EOS ' + from_callsign + ' ')
    
  """
  callback function used by JS8_Client processing thread
  """
  def fldigi_callback(self, json_string, txrcv, rigname, fldigi_instance):

    comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)

    if(comm_status == cn.COMM_LISTEN or comm_status == cn.COMM_NONE):
      self.fldigi_callback2(json_string, txrcv, fldigi_instance)

    elif(comm_status == cn.COMM_RECEIVING):
      self.fldigi_callback2(json_string, txrcv, fldigi_instance)
      self.debug.info_message("comm status receiving\n")

    elif(comm_status == cn.COMM_QUEUED_TXMSG):
      fldigi_instance.setTimings()

      self.fldigiclient.setTxidState(self.getTxidState(self.tx_rig, self.tx_channel))

      self.fldigiclient.sendItNowFldigiThread(self.fldigiclient.send_string)
      expected_reply = self.getExpectedReply(self.tx_rig, self.tx_channel)
      self.setCommStatus(self.tx_rig, self.tx_channel, expected_reply)
      self.debug.info_message("comm status queued txmsg\n")

    elif(comm_status == cn.COMM_AWAIT_RESEND):
      self.debug.info_message("comm status await resend of fragments\n")
      self.fldigi_callback2(json_string, txrcv, fldigi_instance)

    elif(comm_status == cn.COMM_AWAIT_ACKNACK):

      """ used for testing timing 
      #self.debug.info_message("no data diff: " + str(fldigi_instance.getNoDataDiff()) )
      #self.debug.info_message("rcv wait diff: " + str(fldigi_instance.getRcvWaitDiff()) )
      """

      if(self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) < self.max_qry_acknack_retransmits):
        if( self.countAfterTransmitDiff(fldigi_instance, 1500, 10) == True and self.testForAckNack(fldigi_instance)==False ):
          """ first increase the request confirm count """
          self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) + 1)
          """ now test to see if exceeds max retries before sending a request."""
          if(self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) < self.max_qry_acknack_retransmits):
            self.requestConfirm(self.getMyCall(), self.getSenderCall())
          else:
            self.advanceToNextRecipient()
        elif( self.countAfterTransmitDiff(fldigi_instance, 1500, 10) == False or self.recentNoDataDiff( fldigi_instance, 1000, 2) == False ):
          self.listenForAckNack(json_string, txrcv, fldigi_instance)
        else:
          self.debug.info_message("REQUESTING ACKNAK INFO\n")

          """ first increase the request confirm count """
          self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) + 1)
          """ now test to see if exceeds max retries before sending a request."""
          if(self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) < self.max_qry_acknack_retransmits):
            self.requestConfirm(self.getMyCall(), self.getSenderCall())
          else:
            self.advanceToNextRecipient()
      else:
        """ abort acknack query"""
        self.advanceToNextRecipient()

      if(self.last_displayed_debug_message != 'comm status await acknack'):
        self.last_displayed_debug_message = 'comm status await acknack'
        self.debug.info_message(self.last_displayed_debug_message)

  def testForAckNack(self, fldigi_instance):

    if(fldigi_instance.testReceiveString(cn.COMM_NACK_MSG + '(' ) == True):
      return True
    elif(fldigi_instance.testReceiveString(cn.COMM_ACK_MSG  ) == True):
      return True

    return False

  def listenForAckNack(self, json_string, txrcv, fldigi_instance):

    if(self.fldigiclient.testRcvSignalStopped() == True):
      if(fldigi_instance.testReceiveString(cn.COMM_NACK_MSG + '(' ) == True):
        self.debug.info_message("NACK \n")

        #FIXME CHECK THESE TWO LINES ARE CORRECT?????????????
        from_callsign =  self.getMyCall()

        recipient_stations = self.getRecipientStations(self.tx_rig, self.tx_channel)
        current_recipient  = self.getCurrentRecipient(self.tx_rig, self.tx_channel)
        to_callsign = recipient_stations[int(current_recipient)]  

        retransmit_count = self.getRetransmitCount(self.tx_rig, self.tx_channel)
        self.debug.info_message("retransmit count is : " + str(retransmit_count) )
        if(retransmit_count < self.max_frag_retransmits):
          self.debug.info_message("retransmitting\n")
          self.setRetransmitCount(self.tx_rig, self.tx_channel, retransmit_count + 1)

          missing_frames = self.processNack(from_callsign, to_callsign, self.active_rig, self.active_channel)
          self.fldigiclient.resetReceiveString()
        else:
          """ abort station retransmits and move onto the next station """
          self.advanceToNextRecipient()
      
      elif(fldigi_instance.testReceiveString(cn.COMM_ACK_MSG) == True):
        self.debug.info_message("ACK \n")
        self.debug.info_message("rcv string: " + fldigi_instance.getReceiveString() )
        self.debug.info_message("compare to ---" + cn.COMM_ACK_MSG + "---\n")
        self.processAck(self.active_rig, self.active_channel)


  def listenForAckNackJS8(self):

    #LOOP AROUND ALL THE CHANNELS AND TEST TIMESTAMP FOR LESS THAN 3 SECONDS
    # IF SO THEN PROCESS MISSING FRAMES AND ADD TO MISSING FRAMES ON TX CHANNEL PARAMETERS

    rigname = self.active_rig
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldict = rigdictionaryitem.get('channels')
    for key in channeldict:
      channelitem = channeldict.get(key)
    #  for callsign in ...
    #    if(channelitem.get('channel_callsign') == )
    #      #this is one of the interested callsigns....
    self.listenForAckNackJS82()

  def listenForAckNackJS82(self):

    rcv_string = self.getRcvString(self.active_rig, self.active_channel)

    self.debug.info_message("listenForAckNackJS82. rcv string: " + rcv_string)
    diff = datetime.now() - self.getFrameRcvTime(self.active_rig, self.active_channel)
    self.debug.info_message("listenForAckNackJS82. diff active rig: " + str(diff.seconds) + ' ' + str((diff.seconds *1000) + (diff.microseconds / 1000) ))
    diff2 = datetime.now() - self.getFrameRcvTime(self.tx_rig, self.tx_channel)
    self.debug.info_message("listenForAckNackJS82. diff tx rig: " + str(diff2.seconds) + ' ' + str((diff2.seconds *1000) + (diff2.microseconds / 1000) ))

    default_timing_wait = 15
    recipient_channel = self.queryChannelForCallSign(self.active_rig, self.getSenderCall())
    if(recipient_channel != ''):
      self.debug.info_message("listenForAckNackJS82. recipient_channel: " + recipient_channel)
      default_timing_wait = self.getFrameTimingSeconds(self.active_rig, recipient_channel) * 2
      self.debug.info_message("listenForAckNackJS82. default timing wait: " + str(default_timing_wait) )

    if(diff.seconds > default_timing_wait and diff2.seconds > default_timing_wait):
      self.debug.info_message("listenForAckNackJS82. query ack nack")
      self.setFrameRcvTime(self.tx_rig, self.tx_channel, datetime.now())

      """ first increase the request confirm count """
      self.setQryAcknackRetransmitCount(self.tx_rig, self.tx_channel, self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) + 1)
      """ now test to see if exceeds max retries before sending a request."""
      if(self.getQryAcknackRetransmitCount(self.tx_rig, self.tx_channel) < self.max_qry_acknack_retransmits):
        self.requestConfirm(self.getMyCall(), self.getSenderCall())
      else:
        self.advanceToNextRecipient()

      return
      
    sender_call = ''
    if(cn.EOM_JS8 in rcv_string):
      split_string = rcv_string.split(cn.EOM_JS8 + ' ', 1)[1]
      sender_call_split = split_string.split(' ')
      if(sender_call_split[0] == self.getSenderCall() ):
        sender_call = sender_call_split[0]
        self.debug.info_message("sender call is: " + sender_call)

    if(cn.COMM_NACK_MSG in rcv_string and sender_call == self.getSenderCall() ):

      self.debug.info_message("NACK \n")
      from_callsign = self.getMyCall()
      to_callsign = self.getSenderCall()

      retransmit_count = self.getRetransmitCount(self.active_rig, self.active_channel)
      self.debug.info_message("retransmit count is : " + str(retransmit_count) )
      if(retransmit_count < self.max_frag_retransmits):
        self.debug.info_message("retransmitting\n")
        self.setRetransmitCount(self.active_rig, self.active_channel, retransmit_count + 1)

        self.debug.info_message("calling process nack JS8\n")

        missing_frames = self.processNackJS8(from_callsign, to_callsign, self.active_rig, self.active_channel)
        self.resetRcvString(self.active_rig, self.active_channel)
      else:
        """ abort station retransmits and move onto the next station """
        self.advanceToNextRecipient()
      
    elif(cn.COMM_ACK_MSG in rcv_string):
      self.debug.info_message("ACK \n")
      self.debug.info_message("compare to ---" + cn.COMM_ACK_MSG + "---\n")
      self.processAckJS8(self.active_rig, self.active_channel)


  def getSentToMe(self):
    return self.getMyCall() + ' '

  def getSentToMeAlt(self):
    return self.getMyCall() + ' '

  def getSentToGroup(self):
    return ' ' + self.getMyGroup() + ' ' 

  def getSentToRelayTest1(self):
    return self.getMyGroup() + ' ' 

  def getSentToRelayTest2(self):
    return self.getMyCall() 


  def resetSNR(self):
    self.setBestSNR(self.active_rig, self.active_channel, '-50')
    return

  def acquireSNR(self, fldigi_instance):

    try:

      snr = fldigi_instance.getSNR().strip()
      if(snr != ''):
        part2 = snr.split('S/N ')[1].strip()
        the_snr = part2.split(' ')[0]
        if(self.getBestSNR(self.active_rig, self.active_channel) == None):
          self.setBestSNR(self.active_rig, self.active_channel, the_snr)
        if(int(the_snr) > int(self.getBestSNR(self.active_rig, self.active_channel) ) ):
          self.setBestSNR(self.active_rig, self.active_channel, the_snr)
          self.debug.info_message("fldid_callback2 BEST SNR is: " + the_snr )

    except:
      self.debug.error_message("Exception in acquireSNR: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return self.getBestSNR(self.active_rig, self.active_channel)
 

  """
  callback function used by JS8_Client processing thread
  """
  def fldigi_callback2(self, json_string, txrcv, fldigi_instance):

    rcv_string = self.fldigiclient.getReceiveString()
    start_frame_tag = self.testForStartFrame(self.fldigiclient.getReceiveString())

    command = cn.COMMAND_NONE 
    if(start_frame_tag == ''):
      command, remainder, from_call, param_1 = self.saam_parser.testAndDecodeCommands(self.fldigiclient.getLastTwenty(), cn.FLDIGI)
      fldigi_instance.setLastTwenty(remainder)

    if(command != cn.COMMAND_NONE):
      self.debug.info_message("process the commands in here\n")
      self.fldigiclient.setReceiveString(remainder)

      fldigi_instance.resetLastTwenty()

      try:
        if(command == cn.COMMAND_QRY_SAAM):
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("heard query saam\n")
          group_name = param_1
          self.form_gui.form_events.changeFlashButtonState('btn_compose_saam', True)

        if(command == cn.COMMAND_CQCQCQ):
          snr = self.acquireSNR(fldigi_instance)
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("heard CQCQCQ\n")
          group_name = param_1
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_cqcqcq', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_copycopy', True)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_rr73', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_73', False)

          newID = self.getEncodeUniqueId(from_call)
          newMode = self.fldigiclient.current_mode
          rigname = ''
          self.group_arq.addSelectedStation(from_call, '', '', '', rigname, newMode, snr, newID)

          index = self.group_arq.getSelectedStationIndex(from_call)
          if(index != -1):
            self.group_arq.selectSelectedStations(index)

          self.form_gui.refreshSelectedTables()
          self.form_gui.window['in_inbox_listentostation'].update(from_call)

        if(command == cn.COMMAND_COPY):
          snr = self.acquireSNR(fldigi_instance)
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("heard COPY\n")
          group_name = param_1
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_cqcqcq', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_copycopy', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_rr73', True)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_73', False)

          newID = self.getEncodeUniqueId(from_call)
          newMode = self.fldigiclient.current_mode
          rigname = ''
          self.group_arq.addSelectedStation(from_call, '', '', '', rigname, newMode, snr, newID)
          self.form_gui.refreshSelectedTables()
          self.form_gui.window['in_inbox_listentostation'].update(from_call)

          """ If full auto is selected then send reply"""
          checked = self.form_gui.window['cb_mainpanel_ft8stylefullauto'].get()
          if(checked):
            from_call = self.getMyCall()
            group_name = self.getMyGroup()
            self.sendRR73(from_call, group_name)

        if(command == cn.COMMAND_RR73):
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("heard RR73\n")
          group_name = param_1
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_cqcqcq', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_copycopy', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_rr73', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_73', True)
          self.form_gui.refreshSelectedTables()

          self.form_gui.window['in_inbox_listentostation'].update(from_call)

          """ If full auto is selected then send reply"""
          checked = self.form_gui.window['cb_mainpanel_ft8stylefullauto'].get()
          if(checked):
            from_call = self.getMyCall()
            group_name = self.getMyGroup()
            self.send73(from_call, group_name)


        if(command == cn.COMMAND_73):
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("heard 73\n")
          group_name = param_1
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_cqcqcq', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_copycopy', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_rr73', False)
          self.form_gui.form_events.changeFlashButtonState('btn_mainpanel_73', False)
          self.form_gui.refreshSelectedTables()
          self.form_gui.window['in_inbox_listentostation'].update(from_call)

        if(command == cn.COMMAND_SAAM):
          """ Do not send an automatic reply as all stations potentially use the same channel in fldigi"""
          """ self.sendSAAM(from_call, group_name) """
          self.debug.info_message("Do something\n")
          group_name = param_1
          self.group_arq.addSelectedStation(from_call, 'X')
          self.form_gui.refreshSelectedTables()

          if(self.group_arq.formdesigner_mode == False ):
            self.form_gui.window['in_inbox_listentostation'].update(from_call)

        elif(command == cn.COMMAND_REQM):
          self.debug.info_message("Received REQM\n")
          msgid = param_1

          #THIS IS FOR TESTING ONLY!!!!
          #"""
          if(self.form_dictionary.doesOutboxDictionaryItemExist(msgid) == True):
            self.debug.info_message("outbox dictionary item exists\n")
            if(self.form_dictionary.getVerifiedFromOutboxDictionary(msgid) == 'yes'):
              self.debug.info_message("verified is yes\n")
              dict_item = self.form_dictionary.getOutboxDictionaryItem(msgid)
              content  = dict_item.get('content')	
              formname = dict_item.get('formname')	
              priority = dict_item.get('priority')	
              subject  = dict_item.get('subject')	
              tolist   = dict_item.get('to')	
              frag_size = 20
              tag_file = 'ICS'
              version = '1.0'
              sender_callsign = self.getMyCall()
              content = self.form_dictionary.getContentFromOutboxDictionary(msgid)
              complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tag_file, version, sender_callsign)
              message = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
              self.sendFormFldigi(message, from_call, msgid)
          #"""
          """ Only check the relay box for any REQM requests """
          if(self.form_dictionary.doesRelayboxDictionaryItemExist(msgid) == True):
            if(self.form_dictionary.getVerifiedFromRelayboxDictionary(msgid) == 'yes'):
              dict_item = self.form_dictionary.getRelayboxDictionaryItem(msgid)
              content  = dict_item.get('content')	
              formname = dict_item.get('formname')	
              priority = dict_item.get('priority')	
              subject  = dict_item.get('subject')	
              tolist   = dict_item.get('to')	
              frag_size = 20
              tag_file = 'ICS'
              version = '1.0'
              sender_callsign = self.getMyCall()
              content = self.form_dictionary.getContentFromRelayboxDictionary(msgid)
              complete_send_string = self.group_arq.saamfram.getContentSendString(msgid, formname, priority, tolist, subject, frag_size, tag_file, version, sender_callsign)
              message = self.group_arq.saamfram.buildFragTagMsg(complete_send_string, frag_size, self.group_arq.getSendModeRig1(), sender_callsign)
              self.sendFormFldigi(message, from_call, msgid)

      except:
        self.debug.error_message("Exception in fldigi_callback2: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

      """ this was a command so we are done"""
      return

    succeeded, remainder = self.saam_parser.testAndDecodePreMessage(rcv_string, cn.FLDIGI)
    if(succeeded):
      self.fldigiclient.setReceiveString(remainder)
      ##???
      self.fldigiclient.setLastTwenty(remainder)
    
    if(start_frame_tag != ''):
      self.debug.info_message("GOT START FRAME TAG\n")

      if(self.getCommStatus(self.tx_rig, self.tx_channel) ==  cn.COMM_LISTEN):
        fldigi_instance.setTimings()

        #self.debug.info_message("LAST TWWENTY IS: " + fldigi_instance.last_twenty_chars )

        if( fldigi_instance.testLastTwenty(self.getSentToGroup()) ):
          self.debug.info_message("ADDRESSED TO GROUP")
          fldigi_instance.resetLastTwenty()
          """ this is relevant for the active channel and the tx channel"""
          self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_GROUP)
        elif( fldigi_instance.testLastTwenty(self.getSentToMe()) ):
          self.debug.info_message("ADDRESSED TO ME")
          fldigi_instance.resetLastTwenty()
          """ this is relevant for the active channel and the tx channel"""
          self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_ME)
        elif( fldigi_instance.testLastTwenty(self.getSentToRelayTest1()) and fldigi_instance.testLastTwenty(self.getSentToRelayTest2()) ):
          self.debug.info_message("ADDRESSED TO ME as RELAY")
          fldigi_instance.resetLastTwenty()
          """ this is relevant for the active channel and the tx channel"""
          self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_ME)
        else:
          self.setWhatWhere(self.active_rig, self.active_channel, cn.WHAT_WHERE_NONE)

      self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_RECEIVING)
      start_frame_tag = self.gotStartFrame(start_frame_tag)

    elif(fldigi_instance.testReceiveString(']' + self.getEomMarker() + ' ' + self.getSenderCall() ) == True and self.fldigiclient.testRcvSignalStopped() == True):
      self.debug.info_message("calling message ended\n")
      self.messageEnded()

    elif(fldigi_instance.testReceiveString(self.getSenderCall() + ': ' + self.getMyGroup() + '  ' + self.getBosMarker() ) == True):
      self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_GROUP)
      self.debug.info_message("message addressed to group")

    elif(fldigi_instance.testReceiveString(self.getMyGroup() + ' ' + self.getEosMarker() + ' ' ) == True and self.fldigiclient.testRcvSignalStopped() == True):
      self.debug.info_message("session ended 1")
      self.resetReceivedStrings(self.active_rig, self.active_channel)
      self.fldigiclient.resetReceiveString()
    elif(fldigi_instance.testReceiveString(' ' + self.getEosMarker() + ' ' + self.getSenderCall() ) == True and self.fldigiclient.testRcvSignalStopped() == True):
      self.debug.info_message("session ended 2")
      self.resetReceivedStrings(self.active_rig, self.active_channel)
      self.fldigiclient.resetReceiveString()

    elif(fldigi_instance.testReceiveString(cn.COMM_QRYACK_MSG) == True and self.fldigiclient.testRcvSignalStopped() == True):
      self.debug.info_message("proc for ack?\n")

      if( fldigi_instance.testLastTwenty(self.getSentToMeAlt()) ):
        self.debug.info_message("ADDRESSED TO ME")
        fldigi_instance.resetLastTwenty()
        """ this is relevant for the active channel and the tx channel"""
        self.setWhatWhere(self.active_rig, self.active_channel, cn.QRYACKNACK_TO_ME)
      else:
        self.setWhatWhere(self.active_rig, self.active_channel, cn.WHAT_WHERE_NONE)

      received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
      num_strings = self.getNumFragments(self.active_rig, self.active_channel) 

      missing_frames = ''
      for x in range(1, num_strings+1):
        key = '[F' + str(x) + ',' + str(num_strings) + ']'
        if(key not in received_strings):
          self.debug.info_message("MISSING FRAME: " + key )
          if(missing_frames != ''):
            missing_frames = missing_frames + ','
          missing_frames = missing_frames + 'F' + str(x)
          self.form_gui.window['in_inbox_errorframes'].update(missing_frames)

      """ There are no missing frames so the mssage should now decode"""
      if(missing_frames == '' and num_strings > 0):
        self.fldigiclient.resetReceiveString()
        from_callsign = self.getMyCall()
        to_callsign = self.getSenderCall()
        self.sendAck(from_callsign, to_callsign)

      else:  
        self.fldigiclient.resetReceiveString()
        from_callsign = self.getMyCall()
        to_callsign = self.getSenderCall()
        if(missing_frames == ''):
          missing_frames = 'ALL'

        stub = self.decodeAndSaveStub()
        self.processIncomingStubMessage(stub, received_strings)
        self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
        self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

        self.sendNack(missing_frames, from_callsign, to_callsign)

    elif( self.getInSession(self.active_rig, self.active_channel) == True and self.fldigiclient.testRcvSignalStopped() == True and self.getCommStatus(self.tx_rig, self.tx_channel) == cn.COMM_RECEIVING):
      self.debug.info_message("calling message ended rcv signal stopped\n")
      self.messageEnded()
	  
    return()


  def gotStartFrame(self, start_frame_tag):

    self.debug.info_message("in gotStartFrame" )

    success = True
    self.setInSession(self.active_rig, self.active_channel, True)

    while(success and start_frame_tag != ''):
      self.debug.info_message("gotStartFrame - test for end frame" )
      end_frame_tag = self.testForEndFrame(start_frame_tag, self.fldigiclient.getReceiveString())

      rcv_string = self.fldigiclient.getReceiveString()
        
      if(end_frame_tag != '' ):
        self.debug.info_message("gotStartFrame - processing end frame" )
        extracted_frame_contents = self.extractFrameContents(start_frame_tag, end_frame_tag, self.fldigiclient.getReceiveString())

        rcv_string = self.fldigiclient.getReceiveString()

        self.debug.info_message("processing end frame")
        #self.debug.info_message("processing end frame: " + rcv_string )

        if(self.validateFrame(extracted_frame_contents, end_frame_tag.split('[', 1)[1].split(']', 1)[0]) == True):

          self.addReceivedString(start_frame_tag, start_frame_tag + extracted_frame_contents + end_frame_tag, self.active_rig, self.active_channel)
          self.setNumFragments(self.active_rig, self.active_channel, self.getNumFramesTag(start_frame_tag))

          rebuilt_string = ''
          received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
          num_strings = self.getNumFragments(self.active_rig, self.active_channel) 

          self.debug.info_message("num strings: " + str(num_strings) )
          self.debug.info_message("# received strings: " + str(len(received_strings)) )

          """ we have a full set now. send for processing."""
          if(num_strings == len(received_strings) and self.fldigiclient.testRcvSignalStopped() == True):
            for x in range(1, num_strings+1):
              extracted_string = received_strings['[F' + str(x) + ',' + str(num_strings) + ']']			
              rebuilt_string = rebuilt_string + extracted_string
            self.debug.info_message("rebuilt string is: " + rebuilt_string )
            self.processIncomingMessage(rebuilt_string)
            self.setInSession(self.active_rig, self.active_channel, False)
            self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
            self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())
            self.fldigiclient.resetReceiveString()

            from_callsign = self.getMyCall()
            to_callsign = self.getSenderCall()
            self.sendAck(from_callsign, to_callsign)

        else:
          success = False	

        self.debug.info_message("gotStartFrame - test for start frame" )
          		    
        start_frame_tag = self.testForStartFrame(self.fldigiclient.getReceiveString())

        rcv_string = self.fldigiclient.getReceiveString()

        #self.debug.info_message("testing frame: " + rcv_string )
        self.debug.info_message("testing frame")

      else:
        success = False			    
        self.debug.info_message("gotStartFrame - success = false" )
        if(self.fldigiclient.testRcvSignalStopped() == True):
          self.messageEnded()

    return start_frame_tag

  def gotStartFrameJS8(self, start_frame_tag):

    self.debug.info_message("gotStartFrameJS8\n")

    success = True
    self.setInSession(self.active_rig, self.active_channel, True)

    while(success and start_frame_tag != ''):
      self.debug.info_message("testing for next frame \n")

      next_frame_tag = self.testForNextFrameJS8(start_frame_tag, self.getRcvString(self.active_rig, self.active_channel))

      self.debug.info_message("tested for next frame \n")

      rcv_string = self.getRcvString(self.active_rig, self.active_channel)
        
      if(next_frame_tag != '' ):
        self.debug.info_message("next frame exists\n")

        extracted_frame_contents = self.extractFrameContentsJS8(start_frame_tag, next_frame_tag, rcv_string)

        self.debug.info_message("extracted frame contents: " + extracted_frame_contents )

        rcv_string = self.getRcvString(self.active_rig, self.active_channel)

        self.debug.info_message("processing end frame")
        #self.debug.info_message("processing end frame: " + rcv_string )

        self.addReceivedString(start_frame_tag, start_frame_tag + extracted_frame_contents, self.active_rig, self.active_channel)

        #FIXME NEEDED?
        #self.setNumFrames(self.active_rig, self.active_channel, self.getNumFramesTag(start_frame_tag))

        rebuilt_string = ''
        received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
        num_strings = self.getNumFragments(self.active_rig, self.active_channel) 
        eom_received = self.getEOMReceived(self.active_rig, self.active_channel) 

        self.debug.info_message("num strings: " + str(num_strings) )
        self.debug.info_message("# received strings: " + str(len(received_strings)) )

        """ we have a full set now. send for processing."""
        if(num_strings >0 and num_strings == len(received_strings) and eom_received):
          for x in range(0, num_strings):
            extracted_string = received_strings['[' + self.getCharForIndex(x) ]			
            self.debug.info_message("extracted string: " + str(extracted_string) )
            rebuilt_string = rebuilt_string + extracted_string
          self.debug.info_message("rebuilt string is: " + rebuilt_string )
          self.processIncomingMessage(rebuilt_string)
          self.setInSession(self.active_rig, self.active_channel, False)
          self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
          self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())
          		    
        start_frame_tag = self.testForStartFrameJS8(self.getReceivedStrings(self.active_rig, self.active_channel))
        rcv_string = self.getReceivedStrings(self.active_rig, self.active_channel)

        #self.debug.info_message("testing frame: " + str(rcv_string) )
        self.debug.info_message("testing frame")

      else:
        success = False			    

    return start_frame_tag

  def messageEnded(self):
    try:
      rebuilt_string = ''
      received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
      num_strings = self.getNumFragments(self.active_rig, self.active_channel) 

      self.debug.info_message("message ended. num strings: " + str(num_strings) )

      missing_frames = ''
      for x in range(1, num_strings+1):
        key = '[F' + str(x) + ',' + str(num_strings) + ']'
        self.debug.info_message("message ended. testing key: " + str(key) )
        if(key not in received_strings):
          self.debug.info_message("MISSING FRAME: " + key )
          if(missing_frames != ''):
            missing_frames = missing_frames + ','
          missing_frames = missing_frames + 'F' + str(x)
          self.form_gui.window['in_inbox_errorframes'].update(missing_frames)

      """ There are no missing frames so the mssage should now decode"""
      if(missing_frames == '' and num_strings > 0):
        try:
          for x in range(1, num_strings+1):
            extracted_string = received_strings['[F' + str(x) + ',' + str(num_strings) + ']']			
            rebuilt_string = rebuilt_string + extracted_string
          self.debug.info_message("rebuilt string is: " + rebuilt_string )
          self.processIncomingMessage(rebuilt_string)
          self.setInSession(self.active_rig, self.active_channel, False)
          self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
          self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())
          self.fldigiclient.resetReceiveString()

          from_callsign = self.getMyCall()
          to_callsign = self.getSenderCall()
          self.sendAck(from_callsign, to_callsign)

        except:
          self.debug.error_message("Exception in messageEnded: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


      else:  
        self.fldigiclient.resetReceiveString()
        from_callsign = self.getMyCall()
        to_callsign = self.getSenderCall()
        if(missing_frames == ''):
          missing_frames = 'ALL'

        stub = self.decodeAndSaveStub()
        self.processIncomingStubMessage(stub, received_strings)
        self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
        self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

        self.sendNack(missing_frames, from_callsign, to_callsign)

    except:
      self.debug.error_message("Exception in messageEnded: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.fldigiclient.resetReceiveString()
      self.resetReceivedStrings(self.active_rig, self.active_channel)

  def messageEndedJS8(self, rcv_string):

    self.debug.info_message("messageEndedJS8")

    try:
      rebuilt_string = ''
      eom_received = self.getEOMReceived(self.active_rig, self.active_channel) 
      received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)
      num_strings = self.getNumFragments(self.active_rig, self.active_channel) 
      self.debug.info_message("message ended. num strings: " + str(num_strings) )

      missing_frames = ''
      self.debug.info_message("received strings: " + str(received_strings) )
      for x in range(num_strings):
        key = '[' + self.getCharForIndex(x) 
        self.debug.info_message("message ended. testing key: " + str(key) )
        if(key not in received_strings):
          self.debug.info_message("MISSING FRAME: " + key )
          missing_frames = missing_frames + self.getCharForIndex(x) 
          self.form_gui.window['in_inbox_errorframes'].update(missing_frames)

      """ There are no missing frames so the mssage should now decode"""
      if(missing_frames == '' and num_strings == len(received_strings) and eom_received):
        for x in range(num_strings):
          extracted_string = received_strings['[' + self.getCharForIndex(x) ]			
          rebuilt_string = rebuilt_string + extracted_string

        self.debug.info_message("rebuilt string is: " + rebuilt_string )
        self.processIncomingMessage(rebuilt_string)
        self.debug.info_message("DONE PROCESS INCOMING MESSAGE\n")

        self.setInSession(self.active_rig, self.active_channel, False)
        self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
        self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

        from_callsign = self.getMyCall()
        to_callsign = self.getSenderCall()
        self.sendAckJS8(from_callsign, to_callsign)
        self.debug.info_message("calling sendAckJS8")
      else:  
        from_callsign = self.getMyCall()
        to_callsign = self.getSenderCall()

        num_fragments = 0
        if(self.getEOMReceived(self.active_rig, self.active_channel) == True):
          num_fragments = self.getNumFragments(self.active_rig, self.active_channel)

        fragments_received = self.queryFragmentsReceived()  

        self.debug.info_message("FRAGMENTS RECEIVED: " + str(fragments_received) )

        stub = self.decodeAndSaveStub()
        self.processIncomingStubMessage(stub, received_strings)
        self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
        self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

        #FIXME
        self.debug.info_message("messageEndedJS8. rcv_string: " + rcv_string)
        self.debug.info_message("messageEndedJS8. group: " + self.getSentToGroup())
        self.debug.info_message("messageEndedJS8. me: " + self.getSentToMe())
        if(self.getSentToGroup() in rcv_string):
          self.debug.info_message("messageEndedJS8. FRAGMENTS_TO_GROUP")
          self.setWhatWhere(self.active_rig, self.active_channel, cn.FRAGMENTS_TO_GROUP)
        elif(self.getSentToMe() in rcv_string):
          self.debug.info_message("messageEndedJS8. QRYACKNACK_TO_ME")
          self.setWhatWhere(self.active_rig, self.active_channel, cn.QRYACKNACK_TO_ME)
        else:
          self.debug.info_message("messageEndedJS8. WHAT_WHERE_NONE")
          self.setWhatWhere(self.active_rig, self.active_channel, cn.WHAT_WHERE_NONE)

        self.sendNackJS8(fragments_received, num_fragments, from_callsign, to_callsign)
        self.debug.info_message("calling sendNackJS8")

    except:
      self.debug.error_message("Exception in messageEndedJS8: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.resetReceivedStrings(self.active_rig, self.active_channel)

  """ this method is called by the window event thread from method catchall"""
  def processSendJS8(self):

    if(self.ignore_processing == False):
      comm_status = self.getCommStatus(self.tx_rig, self.tx_channel)

      if(comm_status == cn.COMM_LISTEN or comm_status == cn.COMM_NONE):
        self.debug.info_message("comm status cn.COMM_LISTEN")
        self.js8_process_rcv() 
        self.setCommStatus(self.tx_rig, self.tx_channel, cn.COMM_RECEIVING)

      elif(comm_status == cn.COMM_RECEIVING):
        self.debug.info_message("comm status cn.COMM_RECEIVING")
        self.js8_process_rcv() 
        timing = self.getFrameTimingSeconds(self.active_rig, self.active_channel)
        last_frame_rcv_time = self.getFrameRcvTime(self.active_rig, self.active_channel)
        diff = (datetime.now() - last_frame_rcv_time)
        """ test to see if the transmission has stopped """

      elif(comm_status == cn.COMM_QUEUED_TXMSG):
        self.debug.info_message("comm status queued txmsg\n")
        message = self.getMessage(self.tx_rig, self.tx_channel)
        self.group_arq.sendItNowRig1(message)
        self.setCommStatus(self.tx_rig, self.tx_channel, self.getExpectedReply(self.tx_rig, self.tx_channel) )

      elif(comm_status == cn.COMM_AWAIT_RESEND):
        self.debug.info_message("comm status await resend of fragments\n")
        self.js8_process_rcv() #text, txrcv)
        timing = self.getFrameTimingSeconds(self.active_rig, self.active_channel)
        last_frame_rcv_time = self.getFrameRcvTime(self.active_rig, self.active_channel)
        diff = (datetime.now() - last_frame_rcv_time)

      elif(comm_status == cn.COMM_AWAIT_ACKNACK):
        if(self.last_displayed_debug_message != 'comm status await acknack'):
          self.last_displayed_debug_message = 'comm status await acknack'
          self.debug.info_message(self.last_displayed_debug_message)

        if(self.getQryAcknackRetransmitCount(self.active_rig, self.active_channel) < self.max_qry_acknack_retransmits):
          self.listenForAckNackJS8()
        else:
          """ abort acknack query"""
          self.advanceToNextRecipient()


    return
    
  def queryFragmentsReceived(self):
    eom_received     = self.getEOMReceived(self.active_rig, self.active_channel) 
    num_fragments    = self.getNumFragments(self.active_rig, self.active_channel) 
    received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)

    received_fragments = ''
    index = 0
    count = 0

    while(index < 36 and count < len(received_strings)):
      key = '[' + self.getCharForIndex(index) 
      if(key in received_strings):
        self.debug.info_message("index: " + str(index))
        self.debug.info_message("char: " + self.getCharForIndex(index)  )

        received_fragments = received_fragments + self.getCharForIndex(index) 
        count = count + 1
      index = index + 1

    return received_fragments
    
    
  def sendAckOrNackJS8(self):
    eom_received     = self.getEOMReceived(self.active_rig, self.active_channel) 
    num_fragments    = self.getNumFragments(self.active_rig, self.active_channel) 
    received_strings = self.getReceivedStrings(self.active_rig, self.active_channel)

    received_fragments = ''
    highest_index = 0
    index = 0
    count = 0

    while(index < 36 and count < len(received_strings)):
      key = '[' + self.getCharForIndex(index) 
      if(key in received_strings):
        received_fragments = received_fragments + self.getCharForIndex(index) 
        count = count + 1
        if(index > highest_index):
          highest_index = index

    from_callsign = self.getMyCall()
    to_callsign   = self.getSenderCall()
    if(eom_received and num_fragments == highest_index+1):
      self.sendAckJS8(from_callsign, to_callsign)

    return
