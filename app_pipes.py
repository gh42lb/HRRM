#!/usr/bin/env python
import sys
import constant as cn
import string
import struct

import FreeSimpleGUI as sg
import json
import threading
import os
import platform
import calendar
import xmlrpc.client
import debug as db
import getopt

from JSONPipe import JSONPipe

from gps import *

from datetime import datetime, timedelta
from datetime import time

from uuid import uuid4

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

class AppPipes(object):


  def __init__(self, debug):  
    self.debug = debug
    self.pipes = {}
    return

  def appClose(self):
    sys.stdout.write("IN APP CLOSE\n")
    for key, value in self.pipes.items():
      if(value.pipe_type == cn.JSON_PIPE_SERVER):
        self.pipe.conn.sendall(b'{"type": "APPCLOSE", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')
        sys.stdout.write("SENDING APPCLOSE TO CLIENT\n")
      elif(value.pipe_type == cn.JSON_PIPE_CLIENT):
        value.sendMsg("APPCLOSE", "", params={"SPEED":int(50), "_ID":-1} )
        sys.stdout.write("SENDING APPCLOSE TO CLIENT\n")
      value.close()

    self.pipes = {}


  def createServerPipe(self, name, ip_address, port):
    pipe = JSONPipe(name, (ip_address, int(port) ), cn.JSON_PIPE_SERVER)

    pipe_name = name + "_" + str(ip_address) + "_" + str(port)
    self.pipes[pipe_name] = pipe

    return pipe

  def connectServer(self, server):

    t2 = threading.Thread(target=server.listen, args=())
    t2.start()
    return
  
  def createClientPipe(self, name, ip_address, port):
    pipe = JSONPipe(name, (ip_address, int(port) ), cn.JSON_PIPE_CLIENT)

    pipe_name = name + "_" + str(ip_address) + "_" + str(port)
    self.pipes[pipe_name] = pipe

    return pipe

  def connectClient(self, substationClient):
    substationClient.connect()

    t1 = threading.Thread(target=substationClient.run, args=())
    t1.start()
    mysubstationcallback = JSONPipeSubstationCallback(substationClient)
    substationClient.setCallback(mysubstationcallback.json_callback)

  def getPipe(self, name, ip_address, port):
    pipe_name = name + "_" + str(ip_address) + "_" + str(port)
    return self.pipes[pipe_name]

  def removePipe(self, name, ip_address, port):
    pipe_name = name + "_" + str(ip_address) + "_" + str(port)
    del self.pipes[pipe_name]

  def disconnect(self, pipe):  
    pipe.stopThreads()
    return


class JSONPipeSubstationCallback(object):

  pipe = None

  def __init__(self, ps):  
    self.pipe = ps

  """
  callback function used by processing thread
  """
  def json_callback(self, json_string, txrcv, rigname, js8riginstance):

    if(self.pipe.pipe_type == cn.JSON_PIPE_SERVER):
      sys.stdout.write("SERVER PIPE\n")
      self.pipe.conn.sendall(b'{"type": "ABCDEFG_SPEED", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')
    elif(self.pipe.pipe_type == cn.JSON_PIPE_CLIENT):
      sys.stdout.write("CLIENT PIPE\n")
      sys.stdout.write("DATA RECEIVED AT CLIENT " + str(json_string) + "\n")
    elif(self.pipe.pipe_type == cn.JSON_PIPE_UNDEFINED):
      sys.stdout.write("UNDEFINED PIPE\n")

    return

