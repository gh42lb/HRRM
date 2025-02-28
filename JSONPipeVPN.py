# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
import ssl

import json
import time
import sys
import select
import constant as cn
import threading
import os
import platform

import asyncio

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
  return json.dumps({'type': typ, 'subtype': value, 'params': params})


"""
This is a generic JSON class for handling inter application communications
The class can be instantiated as a server listening socket or as a client connecting to a server
"""
class JSONPipeVPN(object):

  connected = False
  conn = None
  callback = None
  ip_port = ''
  stopConnThreads = False
  pipe_type = cn.JSON_PIPE_UNDEFINED
  window = None
  client_request_connect = False
  client_request_stop = False
  client_connected = False
  clientaddress = None

  def __init__(self, rigname, ip_port, pipe_ty):  
    self.rigname = rigname
    self.ip_port = ip_port
    self.stopConnThreads = False
    self.pipe_type = pipe_ty

  def setClientAddress(self, ipaddr, port):
    self.clientaddress = (ipaddr, port)

  def getClientAddress(self):
    return self.clientaddress

  def setClientRequestConnect(self, client_request_connect):
    sys.stdout.write("method setClientRequestConnect. request: " + str(client_request_connect) + "\n")
    self.client_request_connect = client_request_connect

  def getClientRequestConnect(self):
    return self.client_request_connect

  def setClientRequestStop(self, client_request_stop):
    sys.stdout.write("method setClientRequestStop. request: " + str(client_request_stop) + "\n")
    self.client_request_stop = client_request_stop

  def getClientRequestStop(self):
    return self.client_request_stop

  def setWindow(self, window):
    self.window = window

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

  def create_server_socket(self):
    try:
      self.changeDefaultDirectory()

      context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
      context.load_cert_chain(certfile="hrrm.crt", keyfile="hrrm.key")

      sys.stdout.write("creating socket\n")

      self.sock = socket()

      self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

      sys.stdout.write("created socket\n")

      self.sock.bind(self.ip_port)

      sys.stdout.write("listening\n")

      self.sock.listen(5)
      sys.stdout.write("Server listening on " + str(self.ip_port)+ "\n")

    except FileNotFoundError:
      sys.stdout.write("File not found error. Make sure hrrm.crt and hrrm.key are copied to ~/.HRRM folder...cp ./hrrm.crt ./hrrm.key ~/.HRRM\n")
    except:
      sys.stdout.write("Exception in create_server_socket: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")

    return context  

  """
  listen and bind
  """
  def listen(self):

    connected = False

    try:
      while (self.getStopThreads() == False):
        try:

          if(connected == False):
            context = self.create_server_socket()

          sys.stdout.write("Waiting for connection\n")
          newconn, addr = self.sock.accept()
          sys.stdout.write("Server accepted connection\n")
          conn = context.wrap_socket(newconn, server_side=True)
          sys.stdout.write("Server socket wrapped\n")
          self.conn = conn

          #self.conn.settimeout(5)

          while (True):
            sys.stdout.write("Server waiting for data\n")
            data = conn.recv(1024)
            sys.stdout.write("Server received data: " + str(data) + "\n")

            if not data:
              sys.stdout.write("listen: connection closed by client\n")
              newconn.close()
              self.sock.close()
              connected = False
              time.sleep(5)
              break
            else: 
              callback = self.getCallback()
              try:
                callback(data.decode('utf-8'), cn.RCV, self.rigname, self)  
              except:
                sys.stdout.write("Socket Exception 3: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
                self.close()
                time.sleep(5)
                return			  

            if (self.getStopThreads()):
              sys.stdout.write("stop threads id true\n")
              self.close()
              return

        except:
          sys.stdout.write("Socket Exception 1: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
          time.sleep(2)
          self.sock.close()
          connected = False
    except:
      sys.stdout.write("Socket Exception 2: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
      time.sleep(5)


  """
  open a connection
  """
  def connect(self):

    """ get the base instance folders """
    if (platform.system() == 'Windows'):
      appdata_folder = os.getenv('LOCALAPPDATA') 
      hrrm_appdata_folder = appdata_folder + '\HRRM\\' 
    else:
      appdata_folder = os.getenv('HOME') 
      hrrm_appdata_folder = appdata_folder + '/.HRRM/'


    if(self.connected == False):
      try:
        sys.stdout.write("Current Working Directory: " + str(os.getcwd()) + "\n")

        self.changeDefaultDirectory()

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations(hrrm_appdata_folder + "hrrm.crt")

        self.ip_port = self.getClientAddress()
        ip_address, port = self.ip_port

        sys.stdout.write("Client connecting to " + str(self.ip_port) + "\n")
        raw_socket = socket(AF_INET, SOCK_STREAM)

        self.raw_socket = raw_socket

        raw_socket.connect(self.ip_port)

        self.sock = context.wrap_socket(raw_socket, server_hostname=ip_address)

        peer_cert = self.sock.getpeercert()
        sys.stdout.write("peer cert = " + str(peer_cert) + "\n")

        sys.stdout.write("Client connected\n")
        self.connected = True


      except:
        sys.stdout.write("Socket Exception in connect: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
        raw_socket.close()
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
      sys.stdout.write("getMsg set blocking\n")
      if(True):
        sys.stdout.write("getMsg try to receive data\n")
        content = self.sock.recv(1024)
        if not content:
          sys.stdout.write("getMsg: connection closed by server\n")
          self.close()
          self.connect()  
        else:  
          sys.stdout.write("getMsg received data\n")
          callback = self.getCallback()
          try:
            callback(content.decode('utf-8'), cn.RCV, self.rigname, self)  
          except:
            sys.stdout.write("except in JSONPipeVPN getMsg: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
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
      while True:

        if(self.getClientRequestStop() == True and self.client_connected == True):
          self.close()
          self.setClientRequestStop(False)

        if(self.getClientRequestConnect() == True and self.client_connected == False):
          sys.stdout.write("CONNECTING\n")
          self.connect()
          self.client_connected = True
          self.setClientRequestConnect(False)

          self.form_gui.window['text_mainarea_p2pconnected'].Update(text_color='green1')


        if(self.client_connected == True):
          self.getMsg()
          time.sleep(1)
 
          if (self.getStopThreads()):
              sys.stdout.write("stop threads is true\n")
              self.close()
              break
        else:
          time.sleep(5)

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

    dict_obj = json.loads(json_string)

    sys.stdout.write("json string : " +  str(json_string)  + "\n")

    sys.stdout.write("SENDING DATA TO CLIENT FROM SERVER\n")
    self.conn.sendall(b'{"type": "ABCDEFG_SPEED", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')

    return


  """
  callback function used by processing thread
  """
  def json_client_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("JSONPipeVPN.py: IN CLIENT CALLBACK\n")
    sys.stdout.write("JSONPipeVPN.py: DATA RECEIVED AT CLIENT " + str(json_string) + "\n")
    self.ignore_processing = True

    sys.stdout.write("sending to debug window\n")
    self.form_gui.window['debug_window'].update(str(json_string) + "\n", append=True)

    dict_obj = json.loads(json_string)

    line = json_string.split('\n')
    length = len(line)

    return


  def changeDefaultDirectory(self):
    if (platform.system() == 'Windows'):
      appdata_folder = os.getenv('LOCALAPPDATA') 
      hrrm_appdata_folder = appdata_folder + '\HRRM' 
      os.chdir(hrrm_appdata_folder)
    else:
      appdata_folder = os.getenv('HOME') 
      hrrm_appdata_folder = appdata_folder + '/.HRRM'
      os.chdir(hrrm_appdata_folder)

