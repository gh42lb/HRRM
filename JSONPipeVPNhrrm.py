# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
import ssl
import json
import time
import sys
import select
import constant as cn
import threading
import asyncio

from kademlia.utils import digest
from JSONPipeVPN import JSONPipeVPN

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
This is a generic JSON class for handling inter application communications
The class can be instantiated as a server listening socket or as a client connecting to a server
"""
class JSONPipeVPNhrrm(JSONPipeVPN):

  form_gui = None

  def __init__(self, rigname, ip_port, pipe_ty, form_gui):  
    super().__init__( rigname, ip_port, pipe_ty)  
    self.form_gui = form_gui

  def connect(self):
    super().connect()
    if(self.connected):

      if self.form_gui.group_arq.listenonly == True:
        ID_string = self.form_gui.window['in_mystationname'].get().split('GUID: ')[1]
        ID = digest(ID_string)
      else:
        ID_string = self.form_gui.window['input_myinfo_callsign'].get()
        ID = digest(ID_string)
      sys.stdout.write("mynodeid in hex : " + str(ID.hex()) + "\n")
      decimal_value = int(str(ID.hex()), 16)
      sys.stdout.write("Digest is " + str(decimal_value) + "\n")
      message = json.dumps({'type': cn.P2P_IP_INFO, 'subtype': cn.P2P_IP_NONE, 'params': {"ID":decimal_value}})
      self.sock.send((message + '\n').encode()) 

  def p2pNodeCommand(self, command, address, params):
    sys.stdout.write("p2pNodeCommand\n")

    try:
      defparams = {"vpnpipe_address":address}

      if(params != {}):
        sys.stdout.write("params = " + str(params) + "\n")
        for key in params:
          defparams[key] = params.get(key)


      if(self.pipe_type == cn.JSON_PIPE_CLIENT):
        self.sendMsg( cn.P2P_IP_COMMAND, command, params=defparams )

    except:
      sys.stdout.write("Exception in p2pNodeCommand: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + '\n')


  def set_digest(self, digestkey, value):
    sys.stdout.write("in SET DIGEST method\n")
    params = {"SPEED":123, "_ID":-1}

    if(self.pipe_type == cn.JSON_PIPE_CLIENT):
      self.sendMsg( cn.P2P_IP_SET_DIGEST, cn.P2P_IP_NONE, params={"DIAL":digestkey, "OFFSET":value, "_ID":-1} )

  def set(self, key, value):
    sys.stdout.write("in SET method\n")

    params = {"SPEED":123, "_ID":-1}

    if(self.pipe_type == cn.JSON_PIPE_CLIENT):
      self.sendMsg( cn.P2P_IP_SET, cn.P2P_IP_AVAILABLE_NODES, params={"DIAL":key, "OFFSET":value, "_ID":-1} )

  def get(self, key):
    sys.stdout.write("in GET method\n")

    params = {"SPEED":123, "_ID":-1}
    if(self.pipe_type == cn.JSON_PIPE_CLIENT):
      self.sendMsg( cn.P2P_IP_GET, cn.P2P_IP_AVAILABLE_NODES, params={"DIAL":key, "OFFSET":456, "_ID":-1} )

  def delete(self, key):
    sys.stdout.write("in DELETE method\n")


    


