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
class SAAMFRAM_fldigi(SAAMFRAM):

  def test(self):
    return


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


  def sendFormFldigi(self, message, tolist, msgid):
    self.debug.info_message("send form fldigi sending form: " + message )

    self.debug.info_message("send form fldigi tolist is : " + tolist )

    self.setInSession(self.tx_rig, self.tx_channel, True)

    if(tolist != ''):
      recipient_stations = tolist.split(';')
      self.setRecipientStations(self.tx_rig, self.tx_channel, recipient_stations)

    self.setMessageID(self.tx_rig, self.tx_channel, msgid)

    mycall = self.getMyCall()
    mygroup = self.getMyGroup()

    checked = self.form_gui.window['cb_outbox_includepremsg'].get()
    if(checked):
      #self.setPreMessage('', '')
      self.pre_message = self.buildPreMessageGeneral(mycall, mygroup, 'pre-message', None)
      pre_message = self.getPreMessage()
    else:
      pre_message = ''

    message = pre_message + message

    """ send the full message to the group first """
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
        in_sequence = True
        rle_frames = rle_frames + 'F' + str(last_number) + '-'
        last_number = next_number
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + str(next_number)
      elif(next_number == last_number + 1 and in_sequence == True):
        last_number = next_number
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + str(next_number)
      elif(next_number != last_number + 1 and in_sequence == True):
        in_sequence = False
        rle_frames = rle_frames + str(last_number) + ','
        if(frame_count == num_frames-1):
          rle_frames = rle_frames + 'F' + str(next_number)

        last_number = next_number
      else:
        if(last_number != -1):
          rle_frames = rle_frames + 'F' + str(last_number)
          if(frame_count < num_frames-1):
            rle_frames = rle_frames + ','
          else:
            rle_frames = rle_frames + ',F' + str(next_number)

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
      self.processTheCommands(command, remainder, from_call, param_1)
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

