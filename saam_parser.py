#!/usr/bin/env python

import PySimpleGUI as sg

import sys
import JS8_Client
import debug as db
import threading
import json
import constant as cn
import random
import getopt

from datetime import datetime, timedelta
from datetime import time

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



class SaamParser(object):

  def __init__(self, debug, group_arq, form_dictionary, rig1, rig2, js8client_rig1, js8client_rig2, fldigiclient_rig1, fldigiclient_rig2, form_gui, saamfram):
    self.group_arq = group_arq
    self.form_dictionary = form_dictionary
    self.js8client = js8client_rig1
    self.fldigiclient = fldigiclient_rig1
    self.debug = debug
    self.form_gui = form_gui
    self.saamfram = saamfram


  def compareStrings(self, text1, text2, modetype):
    if(modetype == cn.JS8CALL):
      return self.js8client.isTextInMessage(text1, text2)
    elif(modetype == cn.FLDIGI):
      if(text1 in text2):
        return True

    return False
   
  def getFromToAddresses(self, text, command):
    remainder      = text.replace('  ', ' ')
    split_string   = remainder.split(command, 1)
    before_text    = split_string[0][-15:]
    after_text     = split_string[1][:15]
    pre_split      = before_text.split(' ')
    post_split     = after_text.split(' ')
    from_call_pre  = pre_split[len(pre_split)-2][:-1]
    toname         = pre_split[len(pre_split)-1]
    from_call_post = post_split[0]

    self.debug.info_message("from_call_pre : " + from_call_pre )
    self.debug.info_message("from_call_post : " + from_call_post )
    self.debug.info_message("to name : " + toname )

    if(from_call_pre == from_call_post):
      remainder = text.split(command,1)[1]
      return True, remainder, from_call_pre, toname
    else:
      return False, text, '', ''


  """
  data formats for the new parser...

  MSG_FORMAT_TYPE_1
  <From Call Sign>: <Group Name> COMMAND <From Call Sign>  
  WH6GGO: @HINET CQCQ WH6GGO

  MSG_FORMAT_TYPE_2
  <From Call Sign>: <To call sign> COMMAND <MSGID> <From Call Sign>  
  WH6GGO: WH6ABC REQM 123456_543545 WH6GGO

  MSG_FORMAT_TYPE_3
  <From Call Sign>: <Group Name> COMMAND <MSGID> <From Call Sign>  
  WH6GGO: @HINET QRYM 123456_543545 WH6GGO

  """
  def newParser(self, text, command_str, command, msg_format, modetype):

    succeeded = True
    while(succeeded):
      remainder = text
      succeeded, remainder = self.testAndDecodePreMessage(remainder, modetype)         

      #FIXME should not be fldigi specific!!
      if(succeeded):
        self.fldigiclient.setReceiveString(remainder)

      text = remainder

    remainder = text
    remainder = text.replace('  ', ' ')

    try:
      """
      MSG_FORMAT_TYPE_1
      <From Call Sign>: <Group Name> COMMAND <From Call Sign>  
      WH6GGO: @HINET CQCQ WH6GGO
      """
      if(msg_format == cn.MSG_FORMAT_TYPE_1):

        split_string   = remainder.split(command_str, 1)
        post_text      = split_string[1].split(' ', 1)
        from_call_post = post_text[0].strip()
        pre_text       = split_string[0].rsplit(' ', 2)
        from_call_pre  = pre_text[1].replace(':', '').strip()
        groupname      = pre_text[2].strip()

        self.debug.info_message("from_call_pre " + from_call_pre )
        self.debug.info_message("from_call_post " + from_call_post )
        self.debug.info_message("groupname " + groupname )
        self.debug.info_message("command " + command_str )

        if(from_call_pre == from_call_post):
          self.debug.info_message("processing command " + command_str )
          remainder = post_text[1]
          self.debug.info_message("LOC2 ")

          snr = self.saamfram.acquireSNR(self.fldigiclient)
          self.debug.info_message("LOC3 ")
          self.group_arq.updateSelectedStationSNR(from_call_post, snr)
          self.debug.info_message("LOC4 ")

          self.form_gui.refreshSelectedTables()

          self.debug.info_message("SNR during command = " + snr )

          return command, remainder, from_call_pre, groupname
        else:
          return cn.COMMAND_NONE, text, '', ''

      elif(msg_format == cn.MSG_FORMAT_TYPE_2):
        """
        MSG_FORMAT_TYPE_2
        <From Call Sign>: <To call sign> COMMAND <MSGID> <From Call Sign>  
        WH6GGO: WH6ABC REQM 123456_543545 WH6GGO
        """
        split_string   = remainder.split(command_str, 1)
        post_text      = split_string[1].split(' ', 2)
        msgid          = post_text[0].strip()
        from_call_post = post_text[1].strip()
        pre_text       = split_string[0].rsplit(' ', 2)
        from_call_pre  = pre_text[1].replace(':', '').strip()
        to_call        = pre_text[2].strip()

        self.debug.info_message("from_call_pre " + from_call_pre )
        self.debug.info_message("from_call_post " + from_call_post )
        self.debug.info_message("to call " + to_call )
        self.debug.info_message("command " + command_str )
        self.debug.info_message("msgid " + msgid )

        if(from_call_pre == from_call_post):
          remainder = post_text[2]

          snr = self.saamfram.acquireSNR(self.fldigiclient)
          self.group_arq.updateSelectedStationSNR(from_call_post, snr)

          self.form_gui.refreshSelectedTables()

          self.debug.info_message("SNR during command = " + snr )

          return command, remainder, from_call_pre, to_call, msgid
        else:
          return cn.COMMAND_NONE, text, '', ''


    except:
      self.debug.error_message("method: newParser. " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


  def testAndDecodeCommands(self, text, modetype):

    try:

      if( self.compareStrings(cn.COMM_SAAM_MSG, text, modetype) ):
        command, remainder, from_call_pre, groupname = self.newParser(text, cn.COMM_SAAM_MSG, cn.COMMAND_SAAM_MSG, cn.MSG_FORMAT_TYPE_1, modetype)
        return command, remainder, from_call_pre, groupname

      elif( self.compareStrings(cn.COMM_CQCQCQ, text, modetype) ):
        command, remainder, from_call_pre, groupname = self.newParser(text, cn.COMM_CQCQCQ, cn.COMMAND_CQCQCQ, cn.MSG_FORMAT_TYPE_1, modetype)
        return command, remainder, from_call_pre, groupname

      elif( self.compareStrings(cn.COMM_COPY, text, modetype) ):
        command, remainder, from_call_pre, groupname = self.newParser(text, cn.COMM_COPY, cn.COMMAND_COPY, cn.MSG_FORMAT_TYPE_1, modetype)
        return command, remainder, from_call_pre, groupname

      elif( self.compareStrings(cn.COMM_RR73, text, modetype) ):
        command, remainder, from_call_pre, groupname = self.newParser(text, cn.COMM_RR73, cn.COMMAND_RR73, cn.MSG_FORMAT_TYPE_1, modetype)
        return command, remainder, from_call_pre, groupname

      elif( self.compareStrings(cn.COMM_73, text, modetype) ):
        command, remainder, from_call_pre, groupname = self.newParser(text, cn.COMM_73, cn.COMMAND_73, cn.MSG_FORMAT_TYPE_1, modetype)
        return command, remainder, from_call_pre, groupname


      elif( self.compareStrings(cn.COMM_REQM_MSG, text, modetype) ):
        remainder = text.replace('  ', ' ')
        split_string = remainder.split(cn.COMM_REQM_MSG, 1)
        before_text = split_string[0][-15:]
        after_text = split_string[1]
        pre_split = before_text.split(' ')
        post_split = after_text.split(' ')
        from_call_pre = pre_split[len(pre_split)-2][:-1]
        msgid = post_split[0]
        from_call_post = post_split[1]
        self.debug.info_message("from_call_pre : " + from_call_pre )
        self.debug.info_message("from_call_post : " + from_call_post )

        if(from_call_pre == from_call_post):
          remainder = text.split(cn.COMM_REQM_MSG,1)[1]
          return cn.COMMAND_REQM, remainder, from_call_pre, msgid
        else:
          return cn.COMMAND_NONE, text, '', ''

      elif( self.compareStrings(cn.COMM_QRYSAAM_MSG, text, modetype) ):
        remainder = text.replace('  ', ' ')
        split_string = remainder.split(cn.COMM_QRYSAAM_MSG, 1)
        before_text = split_string[0][-15:]
        after_text = split_string[1][:15]
        pre_split = before_text.split(' ')
        post_split = after_text.split(' ')
        from_call_pre = pre_split[len(pre_split)-2][:-1]
        groupname = pre_split[len(pre_split)-1]
        from_call_post = post_split[0]
        self.debug.info_message("from_call_pre : " + from_call_pre )
        self.debug.info_message("from_call_post : " + from_call_post )
        self.debug.info_message("groupname : " + groupname )

        if(from_call_pre == from_call_post):
          remainder = text.split(cn.COMM_QRYSAAM_MSG,1)[1]
          return cn.COMMAND_QRY_SAAM, remainder, from_call_pre, groupname
        else:
          return cn.COMMAND_NONE, text, '', ''

      elif( self.compareStrings(' QRY RELAY ', text, modetype) ):
        split_string = text.split(' QRY RELAY ', 1)
        contents = split_string[1].split(' ')
        msgid     = contents[0]        
        fragments = contents[1]        
        remainder = text.split(' QRY RELAY '+ msgid + ' ' + fragments,1)[1]
        return cn.COMMAND_QRY_RELAY, remainder, msgid, fragments
      elif( self.compareStrings(' RELAY ', text, modetype) ):
        split_string = text.split(' RELAY ', 1)
        contents = split_string[1].split(' ')
        stationid = contents[0]        
        msgid     = contents[1]        
        fragments = contents[2]        
        remainder = text.split(' RELAY '+ stationid + ' ' + msgid + ' ' + fragments,1)[1]
        return cn.COMMAND_RELAY, remainder, stationid, msgid, fragments
      elif( self.compareStrings(' CONF ', text, modetype) ):
        split_string = text.split(' CONF ', 1)
        contents = split_string[1].split(' ')
        msgid     = contents[0]        
        fragments = contents[1]        
        remainder = text.split(' CONF '+ msgid + ' ' + fragments,1)[1]
        return cn.COMMAND_CONF, remainder, msgid, fragments
      elif( self.compareStrings(' RDY ', text, modetype) ):
        remainder = text.split(' RDY ',1)[1]
        return cn.COMMAND_RDY, remainder
      elif( self.compareStrings(' RDY? ', text, modetype) ):
        split_string = text.split(' RDY? ', 1)
        contents = split_string[1].split(' ')
        msgid     = contents[0]        
        calllist  = contents[1]        
        remainder = text.split(' RDY? '+ msgid + ' ' + calllist,1)[1]
        return cn.COMMAND_QRY_RDY, remainder, msgid, calllist
      elif( self.compareStrings(' SMT ', text, modetype) ):
        remainder = text.split(' SMT ',1)[1]
        return cn.COMMAND_SMT, remainder
      elif( self.compareStrings(' EMT ', text, modetype) ):
        remainder = text.split(' EMT ',1)[1]
        return cn.COMMAND_EMT, remainder
        self.debug.info_message("completed decode roster")
      elif( self.compareStrings(' REQCHK ', text, modetype) ):
        chksum_type = contents[0]        
        remainder = text.split(' REQCHK ',1)[1]
        return cn.COMMAND_CHKSUM, remainder, chksum_type
        self.debug.info_message("completed decode roster")
    except:
      self.debug.error_message("method: decodeCommands. " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return cn.COMMAND_NONE, text, '', ''


  def testPreMsgStartEnd(self, text, start, modetype):
    if( self.compareStrings(start, text, modetype) ):
      if( self.compareStrings('),', text, modetype) ):
        return '),'
      elif( self.compareStrings(')[', text, modetype) ):
        return ')'
      elif( self.compareStrings(') ', text, modetype) ):
        return ')'

    return ''

  def validateChecksum(self, message, checksum):
    if(self.saamfram.getChecksum(message) == checksum):
      return True
    else:
      return False

  def decodePreMsgPostNOTUSED(self, text, end_of_premsg):
      
    split_string = text.split(' POST( ', 1)
    split2 = split_string.split(end_of_premsg, 1)
    remainder = split2[1]
    content = split2[0]

    """ look for a two digit cheksum preceeded by a comma"""
    comma    = content[-3]
    checksum = content[-2:]
    if(comma == ',' and checksum[0] in cn.BASE32_CHARS and checksum[1] in cn.BASE32_CHARS):
      post_message = content.split(',' + checksum, 1)[0]
      if(self.validateChecksum(post_message, checksum)):
        return True, remainder, post_message

    self.debug.info_message("completed decode roster")
    """ dont assume anything return the original message intact """
    return False, text, ''

  def decodePreMsgCommon(self, text, end_of_premsg, findstr):
    split_string = text.split(findstr, 1)
    split2 = split_string.split(end_of_premsg, 1)
    remainder = split2[1]
    content = split2[0]

    """ look for a two digit cheksum preceeded by a comma"""
    comma    = content[-3]
    checksum = content[-2:]
    if(comma == ',' and checksum[0] in cn.BASE32_CHARS and checksum[1] in cn.BASE32_CHARS):
      content_2 = content.split(',' + checksum, 1)[0]
      if(self.validateChecksum(content_2, checksum)):
        split3  = content_2.split(',')
        msgid   = split3[0]
        rcvlist = split3[1]
        return True, remainder, msgid, rcvlist

    self.debug.info_message("completed decode roster")
    """ dont assume anything return the original message intact """
    return False, text, '', ''

  def decodePreMsgCommonN(self, text, end_of_premsg, findstr, numparams):
    split_string = text.split(findstr, 1)
    split2 = split_string[1].split(end_of_premsg, 1)

    remainder = split_string[0] + ' ' + split2[1]
    content = split2[0]

    """ look for a two digit cheksum preceeded by a comma"""

    try:
      self.debug.info_message("LOC 1")
      test_split = content.split(',')
      checksum = test_split[len(test_split)-1]

      self.debug.info_message("testing checksum")

      content_2 = content.split(',' + checksum, 1)[0]

      self.debug.info_message("content2 is: " + str(content_2) )

      if(self.validateChecksum(content_2, checksum)):
        self.debug.info_message("pre msg checksum validated OK!")
        split3  = content_2.split(',')
        if(numparams == 1):
          param1  = split3[0]
          return True, remainder, param1
        elif(numparams == 2):
          param1  = split3[0]
          param2  = split3[1]
          return True, remainder, param1, param2
        elif(numparams == 3):
          param1  = split3[0]
          param2  = split3[1]
          param3  = split3[2]
          return True, remainder, param1, param2, param3
        elif(numparams == 6):
          param1  = split3[0]
          param2  = split3[1]
          param3  = split3[2]
          param4  = split3[3]
          param5  = split3[4]
          param6  = split3[5]
          return True, remainder, param1, param2, param3, param4, param5, param6
      else:
        text = remainder
    except:
      self.debug.info_message("exception decoding pre message"  + str(sys.exc_info()[0]) + str(sys.exc_info()[1]) )

    self.debug.info_message("completed decode pre message part FAIL")
    """ dont assume anything return the original message intact """
    if(numparams == 1):
      return False, text, ''
    elif(numparams == 2):
      return False, text, '', ''
    elif(numparams == 3):
      return False, text, '', '', ''
    elif(numparams == 4):
      return False, text, '', '', '', ''
    elif(numparams == 5):
      return False, text, '', '', '', '', ''
    elif(numparams == 6):
      return False, text, '', '', '', '', '', ''

    return False, text, '', '', ''


  def decodePreMsgPost(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' POST(', 1)

  def decodePreMsgRelay(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' RELAY(', 2)

  def decodePreMsgPend(self, text, end_of_premsg):
    self.debug.info_message("DECODING PRE MSG PEND(")
    succeeded, remainder, msgid, rcv_list = self.decodePreMsgCommonN(text, end_of_premsg, ' PEND(', 2)

    test_split = rcv_list.split(';')
    add_to_inbox = False
    for x in range (0, len(test_split)):
      if(test_split[x].upper() == self.saamfram.getMyCall()):
        add_to_inbox = True
    timestamp = datetime.utcnow().strftime('%y%m%d%H%M%S')
    if(add_to_inbox == True):
      self.form_dictionary.createInboxDictionaryItem(msgid, rcv_list, '', '-', '-', timestamp, '-', {}, 'Stub' )
      self.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
      self.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())
    else:
      self.form_dictionary.createRelayboxDictionaryItem(msgid, rcv_list, '', '-', '-', timestamp, '-', '', '', {}, 'Stub')
      self.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
      self.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

    return succeeded, remainder

  def decodePreMsgQmsg(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' QMSG(', 6)

  def decodePreMsgQinfo(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' QINFO(', 1)

  def decodePreMsgCalls(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' CALLS(', 1)

  def decodePreMsgEndm(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' ENDM(', 3)

  def decodePreMsgInfoGrid(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' INFO(GRID,', 2)

  def decodePreMsgInfo(self, text, end_of_premsg):
    return self.decodePreMsgCommonN(text, end_of_premsg, ' INFO(', 2)

  def decodePreMsgBeac(self, text, end_of_premsg):
    self.debug.info_message("DECODING PRE MSG BEAC(")
    succeeded, remainder, msgid, grid_square, hop_count = self.decodePreMsgCommonN(text, end_of_premsg, ' BEAC(', 3)

    self.debug.info_message("msgid = " + msgid + " grid square = " + grid_square + " hop count = " + hop_count)
    self.debug.info_message("succeeded = " + str(succeeded) )

    decoded_call = '-'
    try:
      decoded_call = self.saamfram.getDecodeCallsignFromUniqueId(msgid)
      self.debug.info_message("decoded call = " + decoded_call)
    except:
      self.debug.error_message("Exception in decodePreMsgBeac: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    from_call = remainder.rsplit(':',1)[0].rsplit(' ',1)[1]
    self.debug.info_message("from call = " + from_call)

    if(succeeded and from_call != decoded_call and decoded_call != self.saamfram.getMyCall() ):
      self.group_arq.addSelectedRelayStation(decoded_call, '', grid_square, from_call, '', hop_count, msgid)
      table = self.group_arq.getSelectedRelayStations()
      self.form_gui.window['tbl_compose_selectedrelaystations'].update(values=table )

    #FIXME add to propagation / relay table
    return succeeded, remainder

  def decodePreMsgConf(self, text, end_of_premsg):
    self.debug.info_message("DECODING PRE MSG CONF(")
    succeeded, remainder, msgid = self.decodePreMsgCommonN(text, end_of_premsg, ' CONF(', 1)

    self.debug.info_message("msgid = " + msgid )
    self.debug.info_message("succeeded = " + str(succeeded) )

    #FIXME add to propagation / relay table
    return succeeded, remainder

  def decodePreMsgReqm(self, text, end_of_premsg):
    self.debug.info_message("DECODING PRE MSG REQM(")
    succeeded, remainder, msgid = self.decodePreMsgCommonN(text, end_of_premsg, ' REQM(', 1)

    self.debug.info_message("msgid = " + msgid )
    self.debug.info_message("succeeded = " + str(succeeded) )

    #FIXME add to propagation / relay table
    return succeeded, remainder



  def testAndDecodePreMessage(self, text, modetype):

    succeeded = False
    remainder = text

    """ pre message parts must always follow a set predefined order. This applies to send and receive"""
    try:
      end_of_premsg = self.testPreMsgStartEnd(text, ' POST(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode POST")
        succeeded, remainder = self.decodePreMsgPost(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' RELAY(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode RELAY")
        succeeded, remainder = self.decodePreMsgRelay(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' PEND(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode PEND")
        succeeded, remainder = self.decodePreMsgPend(text, end_of_premsg)
        return succeeded, remainder

      end_of_premsg = self.testPreMsgStartEnd(text, ' QMSG(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode QMSG")
        succeeded, remainder = self.decodePreMsgQmsg(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' QINFO(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode QINFO")
        succeeded, remainder = self.decodePreMsgQinfo(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' CALLS(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode CALLS")
        succeeded, remainder = self.decodePreMsgCalls(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' ENDM(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode ENDM")
        succeeded, remainder = self.decodePreMsgEndm(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' INFO(GRID,', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode INFO GRID")
        succeeded, remainder = self.decodePreMsgInfoGrid(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' INFO(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode INFO")
        succeeded, remainder = self.decodePreMsgInfo(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' BEAC(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode BEAC")
        succeeded, remainder = self.decodePreMsgBeac(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' CONF(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode CONF")
        succeeded, remainder = self.decodePreMsgConf(text, end_of_premsg)

      end_of_premsg = self.testPreMsgStartEnd(text, ' REQM(', modetype)
      if( end_of_premsg != ''):
        self.debug.info_message("decode REQM")
        succeeded, remainder = self.decodePreMsgReqm(text, end_of_premsg)

    except:
      self.debug.error_message("method: decodeCommands. " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return False, text

    return succeeded, remainder







