# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR

import json
import time
import sys
import select
import constant as cn
import threading

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

def xlateRcv(content):
  try:
    return json.loads(content)
  except ValueError:
    return {}

def xlateSend(typ, value='', params={}):
  return json.dumps({'type': typ, 'value': value, 'params': params})


"""
This is a generic JSON class for handling inter application communications
The class can be instantiated as a server listening socket or as a client connecting to a server
"""
class JSONPipe(object):

  connected = False
  conn = None
  callback = None
  ip_port = ''
  stopConnThreads = False
  pipe_type = cn.JSON_PIPE_UNDEFINED

  def __init__(self, rigname, ip_port, pipe_ty):  
    self.rigname = rigname
    self.ip_port = ip_port
    self.stopConnThreads = False
    self.pipe_type = pipe_ty

  def setRigName(self, rigname):
    self.rigname = rigname

  def isConnected(self):
    if(self.connected == False):	  
      time.sleep(2)
    return self.connected

  def isInterested(self, interest): 
    if(self.interested == interest):
      return True
    else:
      return False


  """
  listen and bind
  """
  def listen(self):
    self.sock = socket(AF_INET, SOCK_STREAM)

    self.sock.settimeout(5)

    self.sock.bind(self.ip_port)
    self.sock.listen()
    sys.stdout.write("Server listening on " + str(self.ip_port)+ "\n")

    while (self.getStopThreads() == False):
      sys.stdout.write("Witing for connection\n")
      try:
        conn, addr = self.sock.accept()

        sys.stdout.write("Server accepted connection\n")

        self.conn = conn

        while (True):
          sys.stdout.write("Server waiting for data\n")
          data = conn.recv(1024)
          sys.stdout.write("Server received data\n")

          if not data:
            return

          callback = self.getCallback()
          try:
            callback(data.decode('utf-8'), cn.RCV, self.rigname, self)  
          except:
            sys.stdout.write("except in JSONPipe listen: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
            self.close()
            return			  

          if (self.getStopThreads()):
              sys.stdout.write("stop threads id true\n")
              self.close()
              break

      except:
        sys.stdout.write("SOCKET TIMEOUT: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")


  """
  open a connection
  """
  def connect(self):

    if(self.connected == False):
      try:
        sys.stdout.write("Client connecting to " + str(self.ip_port) + "\n")
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect(self.ip_port)
        sys.stdout.write("Client connected\n")
        self.connected = True
      except:
        time.sleep(5)

  """
  close the connection
  """
  def close(self):
    if(self.connected == True):
      self.sock.close()
      sys.stdout.write("DIS-CONNECTING\n")
      self.connected = False

  def getMsg(self):
    if not self.connected:
      self.connect()  

    if self.connected:
      self.sock.setblocking(0)
      ready = select.select([self.sock], [], [], 1)
      if ready[0]:
        content = self.sock.recv(65535)
        callback = self.getCallback()
        try:
          callback(content.decode('utf-8'), cn.RCV, self.rigname, self)  
        except:
          sys.stdout.write("except in JSONPipe getMsg: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
          return			  
    return

  """
  send a message
  """
  def sendMsg(self, *args, **kwargs):

    sys.stdout.write("in sendMsg args = " + str(args) + "\n")
    sys.stdout.write("in sendMsg kwargs = " + str(kwargs) + "\n")

    if self.connected:
      params = kwargs.get('params', {})
      if '_ID' not in params:
        params['_ID'] = '{}'.format(int(time.time()*1000))
        kwargs['params'] = params
      message = xlateSend(*args, **kwargs)
      try:
        """ remember to send the newline at the end :) """
        self.sock.send((message + '\n').encode()) 
        sys.stdout.write("sending message: " + str(message) + "\n")
      except:
        sys.stdout.write("EXCEPT IN sendMsg\n")
        self.close()



  """
  loop until the thread is stopped
  """
  def run(self):

    try:
      self.connect()
      while True:
        self.getMsg()
        time.sleep(1)
 
        if (self.getStopThreads()):
            sys.stdout.write("stop threads is true\n")
            self.close()
            break
    except:
      sys.stdout.write("except in run: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
      time.sleep(5)
    finally:
      sys.stdout.write("close in run\n")
      self.close()

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
  
  """
  activate stop thread condition
  """
  def stopThreads(self):
    self.sock.shutdown(SHUT_RDWR)
    self.stopConnThreads=True

  """
  test if a thread stop request has been sent
  """
  def getStopThreads(self):
    return(self.stopConnThreads)

  """
  set the callback method to be used for processing data received by js8 call
  """
  def setCallback(self, cb):
    self.callback = cb

  """
  return the callback method used from processing data returned by js8 call
  """
  def getCallback(self):
    return (self.callback)
    

  """
  callback function used by processing thread
  """
  def json_server_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("IN SERVER CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT SERVER " + str(json_string) + "\n")

    sys.stdout.write("SENDING DATA TO CLIENT FROM SERVER\n")
    self.conn.sendall(b'{"type": "ABCDEFG_SPEED", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')

    return


  """
  callback function used by processing thread
  """
  def json_client_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("JSONPipe.py: IN CLIENT CALLBACK\n")
    sys.stdout.write("JSONPipe.py: DATA RECEIVED AT CLIENT " + str(json_string) + "\n")

    self.ignore_processing = True

    line = json_string.split('\n')
    length = len(line)

    return




