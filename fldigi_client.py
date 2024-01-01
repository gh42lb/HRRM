# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import select
import constant as cn
import xmlrpc.client
import re
from datetime import datetime, timedelta


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
FLDIGI ip / port
"""
server = ('127.0.0.1', 7362)

debug = 1
stopThreads = False
callback = None

def from_message(content):
  return {}

def to_message(typ, value='', params=None):
  return

"""
This class handles communicating back and forth with JS8 Call application
"""
class FLDIGI_Client(object):

  connected = False

  def __init__(self, debug, rigname):  
    self.server = None	  
    self.debug = debug
    self.connected = False
    self.receive_string = ''
    self.send_string = ''
    self.datarcv_timestamp = None
    self.endtransmit_timestamp = None
    self.starttransmit_timestamp = None
    self.rigname = rigname
    self.no_data_counter = 0
    self.prev_trx = 'RX'
    self.rcv_wait_timer = 0
    self.no_data_datetime = datetime.now()
    self.rcv_wait_datetime = datetime.now()
    self.modem_name = ''
    self.modem_bandwidth = 0
    self.timings = '1,500,2,1000,10,1500'.split(',') 
    self.last_twenty_chars = ''

    self.mode_selection_list = ''

    self.pending_change = True
    self.current_mode = ''
    """ set the default for startup"""
    self.requested_mode = 'PSK500R'
    self.current_channel = '1000'
    self.requested_channel = '1500'

    """ 
    first two digits are character timings to determine if signal being received
    second two are no data timings
    third two are diif after end of transmit timings
    the last number is the relative timing for a test message in seconds.
    """
    self.timing_lookup = {
                           'PSK1000RC2'  : '1,300,6,4000,12,8000,2400,MODE 1 - PSK1000RC2',  #13   512 = 7s     yes
                           'PSK125RC16'  : '1,300,6,4000,12,8000,2730,MODE 30 - PSK800C2',        #512 = 8s     yes
                           'PSK63RC32'   : '1,300,6,4000,12,8000,2750,MODE 30 - PSK800C2',        #512 = 8s     yes
                           'PSK800RC2'   : '1,300,6,4000,12,8000,1900,MODE 3 - PSK800RC2',   #15   512 = 9s     yes
                           'PSK250RC6'   : '1,300,6,4000,12,8000,2000,MODE 4 - PSK250RC6',   #16   512 = 9s     yes middle
                           'PSK500RC3'   : '1,300,6,4000,12,8000,1900,MODE 6 - PSK500RC3',   #16   512 = 9s     yes middle
                           'PSK125RC12'  : '1,300,6,4000,12,8000,2050,MODE 30 - PSK800C2',        #512 = 9s     yes middle
                           'BPSK500'     : '1,300,5,5000,10,6000,500,MODE 8 - BPSK500',      #19   512 = 9s     yes CONTROL MODE!!
                           'PSK1000R'    : '1,300,6,4000,12,8000,1000,MODE 9 - PSK1000R',    #19   512 = 10s    yes middle
                           'OFDM750F'    : '1,300,6,4000,16,12000,750,MODE 30 - OFDM750F',        #512 = 10s    yes
                           'PSK250RC5'   : '1,300,6,4000,12,8000,1650,MODE 7 - PSK250RC5',   #18   512 = 10s    yes middle
                           'PSK250RC7'   : '1,300,6,4000,12,8000,2350,MODE 30 - PSK800C2',        #512 = 10s    yes
                           'PSK125RC10'  : '1,300,6,4000,12,8000,1700,MODE 30 - PSK800C2',        #512 = 10s    yes middle
                           'PSK63RC20'   : '1,300,6,4000,12,8000,1700,MODE 30 - PSK800C2',        #512 = 10s    yes middle
                           'PSK500RC2'   : '1,300,6,4000,12,8000,1200,MODE 10 - PSK500RC2',  #20   512 = 11s    YES
                           'DOMX88'      : '1,500,4,3000,12,6000,1550,MODE 11 - DOMX88',     #23   512 = 12s    yes middle
                           'PSK250RC3'   : '1,300,6,4000,12,8000,900,MODE 12 - PSK250RC3',   #23   512 = 12s    YES CONTROL MODE!!
                           '8PSK125'     : '1,300,6,4000,12,8000,125,MODE 13 - 8PSK125',     #23   512 = 12s    yes
                           '8PSK250FL'   : '1,300,6,4000,12,8000,250,MODE 15 - 8PSK250FL',   #24   512 = 12s    YES CONTROL MODE!!
                           '8PSK250F'    : '1,300,6,4000,12,8000,250,MODE 14 - 8PSK250F',    #24   512 = 13s    yes CONTROL MODE!!
                           'PSK500R'     : '1,300,6,4000,12,8000,500,MODE 16 - PSK500R',     #31   512 = 14s    yes CONTROL MODE!!
                           'MFSK128L'    : '1,300,6,4000,16,12000,1800,MODE 30 - MFSK128L',       #512 = 14s    yes
                           'OFDM500F'    : '1,300,6,4000,16,12000,500,MODE 29 - OFDM500F',        #512 = 15s    yes CONTROL MODE!!
                           'QPSK250'     : '1,500,5,3000,12,3000,250,MODE 18 - QPSK250',     #32   512 = 15s    yes CONTROL MODE!!
                           'BPSK250'     : '1,500,5,3000,10,4000,250,MODE 19 - BPSK250',     #32   512 = 15s    yes CONTROL MODE!!
                           'PSK250RC2'   : '1,300,6,4000,12,8000,600,MODE 17 - PSK250RC2',   #32   512 = 16s
                           'PSK125RC4'   : '1,300,6,4000,12,8000,650,MODE 20 - PSK125RC4',   #33   512 = 16s
                           'PSK125RC5'   : '1,300,6,4000,12,8000,820,MODE 30 - PSK800C2',        #512 = 16s     yes
                           'PSK63RC10'   : '1,300,6,4000,12,8000,830,MODE 30 - PSK800C2',        #512 = 16s     yes
                           'THOR100'     : '1,300,6,4000,12,8000,1800,MODE 30 - THOR100',        #512 = 17s     yes CONTROL MODE!!
                           'DOMX44'      : '1,500,4,3000,12,6000,1550,MODE 21 - DOMX44',     #40   512 = 19s    yes middle
                           '8PSK125FL'   : '1,300,6,4000,12,8000,125,MODE 22 - 8PSK125FL',   #40   512 = 19s    yes CONTROL MODE!!
                           '8PSK125F'    : '1,300,6,4000,12,8000,125,MODE 23 - 8PSK125F',    #41   512 = 19s    yes CONTROL MODE!!
                           'MT63-2KL'    : '1,300,6,4000,16,12000,2000,MODE 30 - MT63-2KL',       #512 = 21s     yes CONTROL MODE!!
                           'MT63-2KS'    : '1,300,6,4000,12,8000,2000,MODE 30 - MT63-2KS',       #512 = 21s 
                           'PSK250R'     : '1,300,6,4000,12,8000,250,MODE 24 - PSK250R',     #54   512 = 24s    yes CONTROL MODE!!
                           'PSK63RC4'    : '1,300,6,4000,12,8000,320,MODE 25 - PSK63RC4',    #54   512 = 25s
                           'PSK63RC5'    : '1,300,6,4000,12,8000,400,MODE 30 - PSK800C2',        #512 = 27s    yes
                           'THOR50x2'    : '1,300,6,4000,12,8000,1800,MODE 30 - THOR50x2',       #512 = 30s     yes CONTROL MODE!!
                           'DOMX22'      : '1,500,6,6000,12,6000,380,MODE 26 - DOMX22',      #74   512 = 31s    yes CONTROL MODE!!   YES BEST FOR WEAK SIGNAL
                           'MT63-1KL'    : '1,300,6,4000,16,12000,1000,MODE 30 - MT63-1KL',       #512 = 37s     yes CONTROL MODE!!  YES BEST FOR WEAK SIGNAL
                           'MT63-1KS'    : '1,300,6,4000,16,12000,1000,MODE 30 - MT63-1KS',       #512 = 37s     yes CONTROL MODE!!  YES BEST FOR WEAK SIGNAL
                           'OLIVIA-4/1K' : '1,300,6,4000,12,8000,750,MODE 27 - OLIVIA-4/1K', #89   512 = 42s     yes CONTROL MODE!!
                           'DOMX16'      : '1,500,6,6000,12,6000,280,MODE 28 - DOMX16',      #101  512 = 42s     yes CONTROL MODE!!  YES BEST FOR WEAK SIGNAL

#                           'THOR25x4'    : '1,300,6,4000,16,12000,1800,MODE 30 - THOR25x4',       #512 = 55s    no 
#                           'MT63-500L'   : '1,300,6,4000,16,12000,500,MODE 30 - MT63-500L',       #512 = 68s    no 
#                           'MT63-500S'   : '1,300,6,4000,16,12000,500,MODE 30 - MT63-500S',       #512 = 68s    no 
#                           'PSK1000C2'    : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'PSK500C4'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'PSK500C2'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'PSK250C6'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'PSK125C12'    : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           '8PSK1200F'    : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           '8PSK1000F'    : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           '8PSK500F'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           '8PSK1000'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'BPSK1000'     : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 =     no
#                           'OFDM3500'    : '1,300,6,4000,16,12000,3500,MODE 31 - OFDM3500',  
                           #'PSK800C2'    : '1,300,6,4000,12,8000,2000,MODE 30 - PSK800C2',        #512 = 7s     no  no
                           #'QPSK500'     : '1,500,5,3000,12,3000,500,MODE 5 - QPSK500',      #16   512 = 7s     no  no 
                           #'PSK500RC4'   : '1,300,6,4000,12,8000,2600,MODE 2 - PSK500RC4',   #13   512 = 8s     no  no
                          }

  def getSelectionList(self, selected_width):

    self.debug.info_message("getSelectionList " + selected_width)

    new_selection_list = ''
    new_selection_list_mode_only = ''
    mode_count = 1
    delimeter = ''
    width = 500

    if(selected_width == 'HF - 500'):
      width = 500
    elif(selected_width == 'HF - 1000'):
      width = 1000
    elif(selected_width == 'HF - 1500'):
      width = 1500
    elif(selected_width == 'HF - 2000'):
      width = 2000
    elif(selected_width == 'HF - 2800'):
      width = 2800
    elif(selected_width == 'VHF/UHF - 3500'):
      width = 3500

    for key in self.timing_lookup: 
      value = self.timing_lookup.get(key)
      items = value.split(',')
        
      if(int(items[6]) <= width):
        new_selection_list = new_selection_list + delimeter + 'MODE ' + str(mode_count) + ' - ' + str(key) 
        new_selection_list_mode_only = new_selection_list_mode_only + delimeter + str(key) 
        delimeter = ','

      mode_count = mode_count + 1

    self.debug.info_message("new_selection_list " + new_selection_list)

    return new_selection_list, new_selection_list_mode_only

  def setRigName(self, rigname):
    self.rigname = rigname

  def resetReceiveString(self):
    self.receive_string = ''
    return

  def getReceiveString(self):
    return self.receive_string

  def setReceiveString(self, receive_string):
    self.receive_string = receive_string
    return

  def appendReceiveString(self, msg):
    self.receive_string = self.receive_string + msg
    return


  def appendToLastTwenty(self, msg):
    last_twenty_chars = self.last_twenty_chars + msg
    self.last_twenty_chars = last_twenty_chars[-300:]

  def resetLastTwenty(self):
    self.last_twenty_chars = ''
    return

  def setLastTwenty(self, msg):
    self.last_twenty_chars = msg
    return

  def getLastTwenty(self):
    return self.last_twenty_chars

  def testLastTwenty(self, msg):

    #self.debug.info_message("testLastTwenty. set to: " + str(self.last_twenty_chars) )

    if(msg in self.last_twenty_chars):
      return True
    else:
      return False  		



  def setModeSelectionList(self, mode_list):
    self.mode_selection_list = mode_list
    return

  def getModeSelectionList(self):
    return self.mode_selection_list


  """ any residuals from last decode need to be prepended """
  def prependReceiveString(self, msg):
    self.receive_string = msg + self.receive_string 
    return

  def testReceiveString(self, msg):
    if(msg in self.receive_string):
      return True
    else:
      return False  		

  def isConnected(self):
    if(self.connected == False):	  
      time.sleep(2)
    return self.connected
 
  """
  open a connection to JS8_CALL
  """
  def connect(self, server):
    self.server = server
    if(self.connected == False):
      try:
        address, port = server
        self.server = xmlrpc.client.ServerProxy('http://' + address + ':' + str(port) )
        self.debug.info_message("method connect CONNECTING to " + 'http://' + address + ':' + str(port) )
        self.connected = True

        self.server.main.set_txid(True)
        self.server.main.set_rsid(True)
        self.server.text.clear_rx()
        self.server.text.clear_tx()
        #self.server.main.set_squelch(True)
        self.server.main.set_squelch(False)
        self.setTimings()

        """ set the default offset (center)"""
        self.server.modem.set_carrier(1750)

        afc_search_range = self.server.modem.get_afc_search_range()
        self.debug.info_message("AFC search range: " + str(afc_search_range) )

        """ set the AFC to false so that no drift """
        self.server.main.set_afc(False)

      except:
        time.sleep(5)

  """
  close the connection with JS8_CALL
  """
  def close(self):
    if(self.connected == True):
      self.debug.info_message("DIS-CONNECTING\n")
      self.connected = False


  def setTxidState(self, txid_state):

    try:
      if self.connected:
        self.server.main.set_txid(txid_state)
    except:
      self.debug.info_message("method: setTxidState: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )

    return


  def getSNR(self):
    snr = ''  
    if self.connected:
      snr = self.server.main.get_status1()
    return snr

  def getTrx(self):
    trx = ''  
    if self.connected:
      trx = self.server.main.get_trx_state()
    return trx

  def abortTransmit(self):
    if self.connected:
      self.server.main.abort()
      self.server.main.rx()
      self.server.text.clear_tx()
  
  def testRcvSignalStopped2(self):
    if(self.getNoDataCounter() > 1):
      return True
    else:
      return False

  def testRcvSignalStopped(self):

    delay2, delay = self.getCharTimings()

    diff_sec, diff_millis = self.getNoDataDiff()
    """ important TIMING value. silence period to make sure there is no additional data arriving"""
    if(diff_sec < delay2 and diff_millis > delay):
      return True
    else:
      return False

  def getModes(self):
    modes = ''
    for key in self.timing_lookup:
      data = self.timing_lookup[key]
      self.debug.info_message("DATA IS :" + str(data) )
      modes = modes + data.split(',')[7] +','
    return modes

  def getCharTimings(self):
    return int(self.timings[0]), int(self.timings[1])

  def getNoDataTimings(self):
    return int(self.timings[2]), int(self.timings[3])

  def getAfterXmitTimings(self):
    return int(self.timings[4]), int(self.timings[5])

  def setTimings(self):
    if self.connected:
      try:
        self.modem_name = self.server.modem.get_name()
        self.debug.info_message("FLDIGI MODEM NAME IS: " + self.modem_name )

        self.timings = self.timing_lookup.get(self.modem_name).split(',') 

        self.debug.info_message("MODE FOUND - TIMINGS SET TO: " + str(self.timings) )

      except:
        self.timings = '1,500,2,1000,10,1500'.split(',') 
        self.debug.info_message("UNKNOWN MODE. TIMINGS SET TO DEFAULT: " + str(self.timings) )

    return

  def getNoDataCounter(self):
    return self.no_data_counter

  def getRcvWaitTimer(self):
    return self.rcv_wait_timer



  def getNoDataDiff(self):
    diff = (datetime.now() - self.no_data_datetime)
    return diff.seconds, (diff.seconds *1000) + (diff.microseconds / 1000)

  def getRcvWaitDiff(self):
    diff = (datetime.now() - self.rcv_wait_datetime)
    return diff.seconds, (diff.seconds *1000) + (diff.microseconds / 1000)

  def getMsg(self):
    if not self.connected:
      self.connect(self.server)  


    return_data = ''
    if self.connected:
      try:		  

        carrier_freq = self.server.modem.get_carrier()
        if(self.pending_change == False and self.current_channel == self.requested_channel and self.current_channel != carrier_freq):
          self.debug.info_message("getMsg changing carrier to: " + str(carrier_freq))
          self.requested_channel = carrier_freq
          self.pending_change = True


        fldigimode = self.server.modem.get_name()
        if(self.pending_change == False and self.current_mode == self.requested_mode and self.current_mode != fldigimode):
          self.debug.info_message("getMsg changing mode to: " + str(fldigimode))
          self.requested_mode = fldigimode
          self.pending_change = True


        trx_state = self.server.main.get_trx_state()
        if trx_state == 'RX':

          """ clear out spurious dtaa in rcv buffer immediately after end of transmit"""
          if(self.prev_trx == 'TX'):
            self.resetReceiveString()
            """ no data counter counts from the end of the last received data """
            self.no_data_counter = 100
            """ rcv_wait_timer counts from the time transmission ends """
            self.rcv_wait_timer = 0
            self.rcv_wait_datetime = datetime.now()
            self.debug.info_message("resetting receive buffer and counter\n")

          self.prev_trx = 'RX'
          data = (self.server.rx.get_data()).data

          if(len(data) != 0):
            return_data = data.decode('utf-8','replace')
            return_data = return_data.replace('\ufffd', '')
            self.no_data_counter = 0
            self.rcv_wait_timer = 0
            self.no_data_datetime = datetime.now()
          else:
            if( self.no_data_counter < 100):
              self.no_data_counter = self.no_data_counter + 1

          if( self.rcv_wait_timer < 100):
            self.rcv_wait_timer = self.rcv_wait_timer + 1

        else:
          self.resetReceiveString()
          self.prev_trx = 'TX'
          self.rcv_wait_timer = 0
          self.rcv_wait_datetime = datetime.now()
          self.no_data_datetime = datetime.now()
          self.no_data_counter = 100

      except:
        self.debug.info_message("method: fldigi getMsg exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )
        time.sleep(1)
        
      
    return (return_data)

  """
  send a message to JS8_CALL
  """
  def sendMsg(self, *args, **kwargs):
    return

  def sendItNowFldigi(self, message):
    self.send_string = message

  def sendItNowFldigiThread(self, message):
    if self.connected:
      self.send_string = ''
      self.debug.info_message("SENDING DATA TO FLDIGI: " + message )		
      self.server.text.add_tx_queu(message)
      self.server.main.tx()
      
    return


  def setChannel(self, channel):
    self.requested_channel = channel
    self.pending_change = True
    """
    if self.connected:
      self.debug.info_message("SETTING FLDIGI MODE TO: " + mode )		
      self.server.modem.set_by_name(mode)
      data = self.timing_lookup[mode]
      width = int(data.split(',')[6])
      self.server.modem.set_carrier(1500 + int(width/2))
    """
    return

  def setMode(self, mode):
    self.requested_mode = mode
    self.pending_change = True
    """
    if self.connected:
      self.debug.info_message("SETTING FLDIGI MODE TO: " + mode )		
      self.server.modem.set_by_name(mode)
      data = self.timing_lookup[mode]
      width = int(data.split(',')[6])
      self.server.modem.set_carrier(1500 + int(width/2))
    """
    return


  def effectChange(self):

    self.debug.info_message("effectChange start" )		

    try:
      if self.connected:
        if(self.current_mode != self.requested_mode):

          self.debug.info_message("current mode " + str(self.current_mode) )
          self.debug.info_message("requested mode " + str(self.requested_mode) )

          self.server.modem.set_by_name(self.requested_mode)
          data = self.timing_lookup[self.requested_mode]
          width = int(data.split(',')[6])

          """ set the default offset (center)"""
          self.server.modem.set_carrier(int(self.current_channel))
          self.current_mode = self.requested_mode

          self.debug.info_message("setting modem to: " + str(self.current_mode) )

        if(self.current_channel != self.requested_channel):

          self.debug.info_message("current channel " + str(self.current_channel) )
          self.debug.info_message("requested channel " + str(self.requested_channel) )

          self.server.modem.set_carrier( int(self.requested_channel) )
          self.current_channel = self.requested_channel

        self.pending_change = False

    except:
      self.debug.info_message("method: effectChange exception: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )
      self.debug.info_message("current mode " + str(self.current_mode) )
      self.debug.info_message("requested mode " + str(self.requested_mode) )
      self.server.modem.set_by_name(self.current_mode)
      self.requested_mode =  self.current_mode
      self.pending_change = False

    self.debug.info_message("effectChange end" )		

    return
      
  """
  test if message contains text
  unicode encode necessary for correct functioning otherwise throws unicode exception
  """
  def isTextInMessage(self, text, message):
    return (0)

  """
  test if message end with and EOM unicode character
  """
  def isEndOfMessage(self, message):
    return (0)

  """
  test if message contains missing frame unicode character(s)
  """
  def areFramesMissing(self, message):
   
    return (0)

  """
  loop until the thread is stopped
  """
  def run(self):

    while(self.getStopThreads() == False):
      data = self.getMsg()
      self.appendReceiveString(data)
      self.appendToLastTwenty(data)
      callback = self.getCallback()

      try:

        #FIXME
        if(self.pending_change == True):
          self.effectChange()

        if(callback != None):
          callback("", cn.RCV, self.rigname, self)  
      except:
        self.debug.info_message("except in fldigi getMsg: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) )
        self.debug.info_message("callback is: " + str(callback) )
      """
      DominoEX-88 use 0.05 (must be at least 0.04)
      DominoEX-44 use 0.1  (must be at least 0.08)
      DominoEX-22 use 0.15 (must be at least 0.14)
      DominoEX-16 use 0.2  (must be at least 0.18)
      """
      time.sleep(0.05)

    self.debug.info_message("thread complete. adios!")

    return

  """
  each reply is held as a \n delimited line. Calculate how many separate replies and return #
  """
  def getNumberOfReplies(self, json_string):
    return

  """
  get the contents of a named parameter from the return string
  """
  def getParam(self, dict_obj, paramname):
    return

  """
  return the value of json string item
  """
  def getValue(self, dict_obj, objname):
    return


  def getByCallsign(self, json_string, callsign):
    return

  def getByOffset(self, json_string, offset):
    return
  
  """
  activate stop thread condition
  """
  def stopThreads(self):
    global stopThreads
    stopThreads=True

  """
  test if a thread stop request has been sent
  """
  def getStopThreads(self):
    global stopThreads
    return(stopThreads)

  """
  set the callback method to be used for processing data received by js8 call
  """
  def setCallback(self, cb):
    global callback
    callback = cb

  """
  return the callback method used from processing data returned by js8 call
  """
  def getCallback(self):
    global callback
    return (callback)

