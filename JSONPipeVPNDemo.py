# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import select
import constant as cn
import threading

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



class JSONPipeVPNDemoCallback(object):

  pipeServer = None

  def __init__(self, ps):  
    self.pipeServer = ps

  """
  callback function used by processing thread
  """
  def json_server_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("IN SERVER CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT SERVER " + str(json_string) + "\n")
   
    sys.stdout.write("SENDING DATA TO CLIENT FROM SERVER\n")
    self.pipeServer.conn.sendall(b'{"type": "ABCDEFG_SPEED", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')

    return


  """
  callback function used by processing thread
  """
  def json_client_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("IN CLIENT CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT CLIENT " + str(json_string) + "\n")

    return


"""
JSONPipeVPNDemo can be run as a stand alone program
"""

def main():

  mypipeServer = JSONPipeVPN('mailbox_server', ('127.0.0.1', 2557), cn.JSON_PIPE_SERVER)
  mypipeClient = JSONPipeVPN('yaesu_radio', ('127.0.0.1', 2557), cn.JSON_PIPE_CLIENT)

  """
  open server thread
  """
  t2 = threading.Thread(target=mypipeServer.listen, args=())
  t2.start()
  mycallbackServer = JSONPipeVPNDemoCallback(mypipeServer)
  mypipeServer.setCallback(mycallbackServer.json_server_callback)

  """
  open client thread
  """
  mypipeClient.connect()
  t1 = threading.Thread(target=mypipeClient.run, args=())
  t1.start()
  mycallbackClient = JSONPipeVPNDemoCallback(None)
  mypipeClient.setCallback(mycallbackClient.json_client_callback)


  time.sleep(5)
  speed = 50
  mypipeClient.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )
  sys.stdout.write("sending message from client run() to server\n")

  time.sleep(5)
  mypipeClient.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )

  time.sleep(5)
  mypipeClient.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )

  time.sleep(5)
  mypipeClient.sendMsg("MODE.SET_SPEED", "", params={"SPEED":int(speed), "_ID":-1} )

  mypipeClient.stopThreads()
  mypipeServer.stopThreads()

  sys.stdout.write("end of test\n")


if __name__ == '__main__':
    main()




