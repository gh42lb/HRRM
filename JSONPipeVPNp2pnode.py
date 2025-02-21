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
import asyncio

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
class JSONPipeVPNp2pnode(JSONPipeVPN):


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

    sys.stdout.write("IN CLIENT CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT CLIENT " + str(json_string) + "\n")
    self.ignore_processing = True

    dict_obj = json.loads(json_string)

    line = json_string.split('\n')
    length = len(line)

    return




