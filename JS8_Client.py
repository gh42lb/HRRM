# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import select
import constant as cn


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
JS8_CALL ip / port
"""
server = ('127.0.0.1', 2442)

debug = 1
stopThreads = False
callback = None

def from_message(content):
  try:
    return json.loads(content)
  except ValueError:
    return {}

def to_message(typ, value='', params=None):
  if params is None:
    params = {}
  return json.dumps({'type': typ, 'value': value, 'params': params})

"""
This class handles communicating back and forth with JS8 Call application
"""
class JS8_Client(object):

  connected = False

  def __init__(self, debug):  
    self.debug = debug
    self.receive_string = ''
    self.rigname = ''

  def setRigName(self, rigname):
    self.rigname = rigname


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
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect(server)
        sys.stdout.write("CONNECTING to " + str(server) + "\n")
        self.connected = True
      except:
        time.sleep(5)

  """
  close the connection with JS8_CALL
  """
  def close(self):
    if(self.connected == True):
      self.sock.close()
      sys.stdout.write("DIS-CONNECTING\n")
      self.connected = False

  def getMsg(self):
    if not self.connected:
      self.connect(self.server)  

    if self.connected:
      self.sock.setblocking(0)
      ready = select.select([self.sock], [], [], 1)
      if ready[0]:
        content = self.sock.recv(65535)
        callback = self.getCallback()
        try:
          callback(content.decode('utf-8'), cn.RCV, self.rigname, self)  
        except:
          sys.stdout.write("except in JS8_Client getMsg: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
          return			  
    return

  """
  send a message to JS8_CALL
  """
  def sendMsg(self, *args, **kwargs):
    sys.stdout.write("Method JS8_Client.sendMsg\n")

    if self.connected:
      params = kwargs.get('params', {})
      if '_ID' not in params:
        params['_ID'] = '{}'.format(int(time.time()*1000))
        kwargs['params'] = params
      message = to_message(*args, **kwargs)
      try:
        """ remember to send the newline at the end :) """
        self.sock.send((message + '\n').encode()) 
      except:
        sys.stdout.write("EXCEPT IN sendMsg\n")
        self.close()

  """
  test if message contains text
  unicode encode necessary for correct functioning otherwise throws unicode exception
  """
  def isTextInMessage(self, text, message):
    try:
      newtext = text.encode('utf-8')
      if newtext in message.encode('utf-8'):
        return (1)
      else:
        return (0)
    except:    
      sys.stdout.write("EXCEPTION\n")

  """
  test if message end with and EOM unicode character
  """
  def isEndOfMessage(self, message):
    
    eom = u'♢'.encode('utf-8')
    if eom in message:
      return (1)
      sys.stdout.write("END OF MESSAGE\n")
    else:
      return (0)


  def stripEndOfMessage(self, message):
    retstring = ''
    try:    
      eom = u'♢'.encode('utf-8')
      retstring = message.split(eom, 1)[0]
    except:    
      sys.stdout.write("EXCEPTION\n")

    return retstring

  """
  test if message contains missing frame unicode character(s)
  """
  def areFramesMissing(self, message):
    
    frame_missing = u'……'.encode('utf-8')

    count = start = 0
    flag = True
    while flag:
      a = message.find(frame_missing, start)
      if a == -1:
        flag = False
      else:
        count += 1
        start = a+1
    return (count)

  """
  loop until the thread is stopped
  """
  def run(self):

    try:
      self.connect(self.server)
      while True:
        self.getMsg()
        time.sleep(1)
 
        if (self.getStopThreads()):
            sys.stdout.write("stop threads id true\n")
            self.close()
            break
    except:
      sys.stdout.write("except in run: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
      time.sleep(5)
    finally:
      sys.stdout.write("close in run\n")
      self.close()

  """
  each reply is held as a \n delimited line. Calculate how many separate replies and return #
  """
  def getNumberOfReplies(self, json_string):
    return(len(json_string.split('\n')))

  """
  get the contents of a named parameter from the return string
  """
  def getParam(self, dict_obj, paramname):
    subdict  = dict_obj.get('params')
    param_value = subdict.get(paramname)
    return(str(param_value))

  """
  return the value of json string item
  """
  def getValue(self, dict_obj, objname):
    value  = dict_obj.get(objname)
    return (value.encode('utf-8'))


  def getByCallsign(self, json_string, callsign):
    found_index=-1
    line = json_string.split('\n')
    length = len(line)
    for x in range(length-1):
      dict_obj = json.loads(line[x])
      type = self.getValue(dict_obj, "type")
      myvar = self.getParam(dict_obj, "FROM")
      call = self.getParam(dict_obj, "CALL")
      if (type == "RX.DIRECTED"):
        if( (self.getValue(dict_obj, "value")).split(":")[0]==callsign):
          found_index=x
      elif (type == "RX.ACTIVITY"):
        if( (self.getValue(dict_obj, "value")).split(":")[0]==callsign):
          found_index=x
      elif(len(myvar)):
        found_index=x
      elif(len(call)):
        found_index=x

    return (found_index)

  def getByOffset(self, json_string, offset):
    found_index=-1
    line = json_string.split('\n')
    length = len(line)
    for x in range(length-1):
      dict_obj = json.loads(line[x])
      rtnoffset = self.getParam(dict_obj, "OFFSET")
      if( rtnoffset==offset):
          found_index=x

    return (found_index)
  
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
    
    
  def testReceiveString(self, msg):
    if(msg in self.receive_string):
      return True
    else:
      return False  		

  def appendReceiveString(self, msg):
    self.receive_string = self.receive_string + msg
    return
    
  def resetReceiveString(self):
    self.receive_string = ''
    return

  def getReceiveString(self):
    return self.receive_string
    

