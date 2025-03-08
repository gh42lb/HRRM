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

from saamfram_core_utils import SaamframCoreUtils
from PIL import Image
from datetime import datetime, timedelta
from crc import Calculator, Configuration
from saamfram import SAAMFRAM

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



"""
This class handles communicating back and forth with JS8 Call application
"""
class SAAMFRAM_js8(SAAMFRAM):
	
  def test(self):
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


  def extractFrameContentsJS8(self, start_frame_tag, next_frame_tag, receive_string):
    substring = receive_string.split(start_frame_tag, 1)[1]
    substring2 = substring.split(next_frame_tag, 1)[0]

    """ pull this out of the receive string so that it is not decoded again """
    self.setRcvString(self.active_rig, self.active_channel, '[' + substring.split(next_frame_tag, 1)[1])

    self.debug.info_message("contents is: " + substring2 )
    return substring2


  def sendFormJS8(self, message, tolist):

    self.debug.info_message("send form JS8 sending form: " + message )

    self.setInSession(self.tx_rig, self.tx_channel, True)

    if(tolist != ''):
      recipient_stations = tolist.split(';')
      self.setRecipientStations(self.tx_rig, self.tx_channel, recipient_stations)

    mycall = self.getMyCall()
    mygroup = self.getMyGroup()

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      self.setPreMessage('', '')
      self.pre_message = self.buildPreMessageGeneral(mycall, mygroup, 'pre-message', None)
      pre_message = self.getPreMessage()
    else:
      pre_message = ''

    message = pre_message + message

    """ send the full message to the group first """
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
          self.appendRcvString(rigname, channel, text)
          self.debug.info_message("total rcvd string: " + self.getRcvString(rigname, channel))
          frame_rcv_time = datetime.now()
          self.setFrameRcvTime(rigname, channel, frame_rcv_time)

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
      self.processTheCommands(command, remainder, from_call, param_1)
      """ this was a command so we are done"""
      return

    succeeded, remainder = self.saam_parser.testAndDecodePreMessage(rcv_string, cn.JS8CALL)
    if(succeeded):
      self.setRcvString(self.active_rig, self.active_channel, remainder)

    """ now continue to decode the rest of the mssage"""

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


  def listenForAckNackJS8(self):

    #LOOP AROUND ALL THE CHANNELS AND TEST TIMESTAMP FOR LESS THAN 3 SECONDS
    # IF SO THEN PROCESS MISSING FRAMES AND ADD TO MISSING FRAMES ON TX CHANNEL PARAMETERS

    rigname = self.active_rig
    rigdictionaryitem = self.rig_channel_dictionary[rigname]
    channeldict = rigdictionaryitem.get('channels')
    for key in channeldict:
      channelitem = channeldict.get(key)
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

        self.addReceivedString(start_frame_tag, start_frame_tag + extracted_frame_contents, self.active_rig, self.active_channel)

        #FIXME NEEDED?

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

        self.debug.info_message("testing frame")

      else:
        success = False			    

    return start_frame_tag


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
