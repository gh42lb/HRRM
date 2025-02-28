import argparse
import logging
import asyncio
import time
import sys
import threading
import json
import random
import ctypes
import constant as cn
import getopt

from p2pMain import SuperServer
from JSONPipeVPNp2pnode import JSONPipeVPNp2pnode
from kademlia.utils import digest
from kademlia.storage import ForgetfulStorage
from p2pMain import MultiValueStorage

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

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class pNode(object):

  pipe = {}
  mainloop = None
  server = None
  fNodeStarted = False

  def setPipe(self, pipe, pipe_key):
    self.pipe[pipe_key] = pipe
    sys.stdout.write("Setting pipe for key: " + str(pipe_key) + "\n")
    if(self.server != None):
      self.server.setPipe(pipe)

  def getPipe(self,  pipe_key):
    sys.stdout.write("Getting pipe for key: " + str(pipe_key) + "\n")
    return self.pipe[pipe_key]

  def createServerObjectFromBytes(self, mydigest):
    sys.stdout.write("method: createServerObjectFromBytes\n")
    self.server = SuperServer(20, 3, mydigest, MultiValueStorage())

  def createServerObject(self, mydigest):
    sys.stdout.write("method: createServerObject\n")
    bytes_value = mydigest.to_bytes(20,byteorder='big')
    self.server = SuperServer(20, 3, bytes_value, MultiValueStorage())

  def restart(self):
    sys.stdout.write("RESTART CALLED\n")
    self.mainloop.stop()
    self.start_bootstrap_thread(self)

  def stop(self, vpnpipe_address):

    self.server.stop()

    pipe = self.getPipe(vpnpipe_address)

    sys.stdout.write("STOP CALLED\n")
    self.mainloop.stop()
    message = json.dumps({'type': cn.P2P_IP_CONNECT_UDP, 'subtype': cn.P2P_IP_STOPPED, 'params': {}})
    self.fNodeStarted = False
    pipe.conn.sendall((message + '\n').encode())

  def start(self, address, vpnpipe_address):
    self.start_bootstrap_thread(self, address, vpnpipe_address)

  def start_bootstrap_thread(self, node, address, vpnpipe_address):
    t2 = threading.Thread(target=self.bootstrap_the_server, args=(node,address, vpnpipe_address))
    t2.start()

  def bootstrap_the_server(self, node, address, vpnpipe_address):

    sys.stdout.write("in bootstrap_the_server. address: " + str(address) + "\n")

    ip   = address[0]
    port = int(address[1])

    loop=asyncio.new_event_loop()

    self.mainloop = loop
    asyncio.set_event_loop(loop)

    loop.run_until_complete(self.server.listen(port, ip))
   
    try:
      self.fNodeStarted = True
      message = json.dumps({'type': cn.P2P_IP_CONNECT_UDP, 'subtype': cn.P2P_IP_SUCCESS, 'params': {}})
      pipe = self.getPipe(vpnpipe_address)
      pipe.conn.sendall((message + '\n').encode())

      loop.run_forever()

    except KeyboardInterrupt:
      pass
    finally:
      sys.stdout.write("server.stop\n")
      self.server.stop()
      loop.close()

  def setValue(self, key, value):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()
      loop.run_until_complete(self.server.set(key, value))
      loop.close()

  def dumpLocalStorage(self, pipe_key):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()
      asyncio.run(self.dumpstorage(pipe_key))
      loop.close()

  def getdata(self, key, pipe_key):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()
      asyncio.run(self.getter(key, pipe_key))
      loop.close()

  def getNeighbors(self, pipe_key):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()
      asyncio.run(self.async_get_the_neighbors(pipe_key))
      loop.close()

  def getPing(self, pipe_key, ping_address):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()
      asyncio.run(self.async_go_get_ping(pipe_key, ping_address))
      loop.close()

  def bootstrap_connect_multi(self, bootstrap_nodes):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()

      asyncio.run(self.server.bootstrap(bootstrap_nodes))
      loop.close()

  def bootstrap_connect(self, bootstrap_node):
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop = asyncio.get_event_loop()

      asyncio.run(self.server.bootstrap([bootstrap_node]))
      loop.close()

  def connect_to_bootstrap_node(self, ip, port, serverport, delay):
    time.sleep(int(delay))
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(self.server.listen(int(serverport)))
    bootstrap_node = (ip, int(port))
    loop.run_until_complete(self.server.bootstrap([bootstrap_node]))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        self.server.stop()
        loop.close()


  async def delay(self, howlong):
    await asyncio.sleep(howlong)


  async def async_get_the_neighbors(self, pipe_key):
    result = self.server.bootstrappable_neighbors()
    print("Got result of bootstrappable neighbors:", result)
    sys.stdout.write("SENDING DATA TO CLIENT FROM SERVER\n")
    if(result != None):
      message = json.dumps({'type': cn.P2P_IP_QUERY_NEIGHBORS_RESULT, 'subtype': cn.P2P_IP_FOUND, 'params': {"result":result}})
    else:
      message = json.dumps({'type': cn.P2P_IP_QUERY_NEIGHBORS_RESULT, 'subtype': cn.P2P_IP_NOT_FOUND, 'params': {"result":result}})

    pipe = self.getPipe(pipe_key)
    pipe.conn.sendall((message + '\n').encode())
    return result


  async def async_go_get_ping(self, pipe_key, ping_address):
    result = await self.server.bootstrap_node((ping_address[0], ping_address[1]))
    print("Got result of ping:", result)
    sys.stdout.write("SENDING DATA TO CLIENT FROM SERVER\n")
    if(result != None):
      message = json.dumps({'type': cn.P2P_IP_QUERY_PING_RESULT, 'subtype': cn.P2P_IP_FOUND, 'params': {"result":'success', 'ping_address':ping_address}})
    else:
      message = json.dumps({'type': cn.P2P_IP_QUERY_PING_RESULT, 'subtype': cn.P2P_IP_NOT_FOUND, 'params': {"result":'fail', 'ping_address':ping_address}})

    pipe = self.getPipe(pipe_key)
    pipe.conn.sendall((message + '\n').encode())
    return result


  async def dumpstorage(self, pipe_key):
    result = await self.server.dumpLocalStorage()
    return None


  async def getter(self, key, pipe_key):
    result = await self.server.getIgnoreLocal(key)

    sys.stdout.write("Got Result: " + str(result)+ "\n")
    sys.stdout.write("Sending data to client from server\n")

    dict_obj = None
    if(result != None):
      dict_obj = json.loads(result)
      message = json.dumps({'type': cn.P2P_IP_QUERY_RESULT, 'subtype': cn.P2P_IP_FOUND, 'params': {"result":dict_obj}})

      pipe = self.getPipe(pipe_key)
      pipe.conn.sendall((message + '\n').encode())
      """ this needs to be retrieved at the hrrm application layer so that can check if already exists
      if(dict_obj != None and 'mailbox' in dict_obj and dict_obj['mailbox'] != None):
        for key in dict_obj['mailbox']:
          await self.getter2(key)
      """
    else:
      message = json.dumps({'type': cn.P2P_IP_QUERY_RESULT, 'subtype': cn.P2P_IP_NOT_FOUND, 'params': {}})

      pipe = self.getPipe(pipe_key)
      pipe.conn.sendall((message + '\n').encode())

    return dict_obj

  def create_bootstrap_node(self, args):
    sys.stdout.write("create_bootstrap_node\n")

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    self.mainloop = loop
    loop.run_until_complete(self.server.listen(int(args.serverport)))
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("server.stop\n")
        self.server.stop()
        loop.close()
    

class JSONPipeVPNp2pnodeCallback(object):

  pipeServer = None
  pnode = None
  p2pthread = None
  ID = None

  def __init__(self, ps, pnode, p2pthread):  
    self.pipeServer = ps
    self.pnode = pnode
    self.p2pthread = p2pthread

  def callback_helper(self, what_to_run):
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(what_to_run)


  """
  callback function used by processing thread
  """
  def json_server_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("IN SERVER CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT SERVER " + str(json_string) + "\n")

    try:
      dict_obj = json.loads(json_string)
      vartype     = dict_obj.get("type")
      varsubtype  = dict_obj.get("subtype")
      vpnpipe_address = dict_obj.get('params').get('vpnpipe_address')
      if(vartype == cn.P2P_IP_SET_DIGEST):
        sys.stdout.write("SET DIGEST COMMAND RECEIVED\n")
        dkey = dict_obj.get('params').get('DIAL')
        sys.stdout.write("DKEY = " + str(dkey) + "\n")
        value = dict_obj.get('params').get('OFFSET')
        sys.stdout.write("VALUE = " + str(value) + "\n")

        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        digest = bytes.fromhex(dkey)
        loop.run_until_complete(pnode.server.set_digest( digest, value))
        loop.close()
      elif(vartype == cn.P2P_IP_COMMAND):
        sys.stdout.write("COMMAND received\n")
        if(varsubtype == cn.P2P_IP_START):
          sys.stdout.write("COMMAND start received\n")
          address = dict_obj.get('params').get('address')
          self.pnode.start(address, vpnpipe_address)
        elif(varsubtype == cn.P2P_IP_STOP):
          sys.stdout.write("COMMAND stop received\n")
          self.pnode.stop(vpnpipe_address)
        elif(varsubtype == cn.P2P_IP_RESTART):
          sys.stdout.write("COMMAND restart received\n")
          self.pnode.restart()
        elif(varsubtype == cn.P2P_IP_QUERY_NEIGHBORS):
          if self.pnode.fNodeStarted == True:
            sys.stdout.write("Getting Neighbors in pnode\n")
            self.pnode.getNeighbors(vpnpipe_address)
          else:
            sys.stdout.write("Node Service not started...ignoring command\n")

        elif(varsubtype == cn.P2P_IP_QUERY_PING):
          sys.stdout.write("Pinging in pnode\n")
          address = dict_obj.get('params').get('ping_address')
          ping_address = (address[0],address[1])
          self.pnode.getPing(vpnpipe_address, ping_address)
        elif(varsubtype == cn.P2P_IP_CONNECT_UDP):
          sys.stdout.write("Connecting to udp node\n")
          address = dict_obj.get('params').get('address')
          bootstrap_node = (address[0],address[1])
          self.pnode.bootstrap_connect(bootstrap_node)
        elif(varsubtype == cn.P2P_IP_CONNECT_UDP_MULTI):
          sys.stdout.write("Connecting to multiple udp nodes\n")
          addresses = dict_obj.get('params').get('addresses')
          bootstrap_nodes = []
          for item in addresses:
            bootstrap_nodes.append((item[0], item[1]))
          sys.stdout.write("bootstrap nodes list: " + str(bootstrap_nodes) + "\n")
          self.pnode.bootstrap_connect_multi(bootstrap_nodes)
        elif(varsubtype == cn.P2P_IP_DUMP_LOCAL_STORAGE):
          sys.stdout.write("Dumping Local Storage\n")
          self.pnode.dumpLocalStorage(vpnpipe_address)

        elif(varsubtype == cn.P2P_IP_GET_MSG):
          sys.stdout.write("GET COMMAND RECEIVED AT SERVER\n")
          key = dict_obj.get('params').get('key')
          self.pnode.getdata(key, vpnpipe_address)
        elif(varsubtype == cn.P2P_IP_SEND_MSG):
          sys.stdout.write("SET COMMAND RECEIVED AT SERVER\n")
          msgid     = dict_obj.get('params').get('msgid')
          msg       = dict_obj.get('params').get('message')
          destid    = dict_obj.get('params').get('destid')
          destlist  = dict_obj.get('params').get('tolist')
          timestamp = dict_obj.get('params').get('timestamp')

          new_dictionary_message = {'type': 'message', 'version':'v1.0', 'msgid':msgid , 'timestamp':timestamp, 'message':msg}
          message = (json.dumps(new_dictionary_message) + '\n').encode()

          """ send the full message out to msgid"""
          self.pnode.setValue(msgid, message)

          """ each station has 2 ids....one for the call sign and one for the p2pip name"""
          """ destid is for the destination station p2p node id"""  
          if(destid != None):
            new_dictionary_message = {'type': 'mailbox', 'version':'v1.0', 'msgid':msgid , 'timestamp':timestamp}
            value = (json.dumps(new_dictionary_message) + '\n').encode()
            """ send msgid to destination p2p node id """
            self.pnode.setValue(destid, value)
          else:
            sys.stdout.write("destid is None\n")

          if(destlist != None):
            new_dictionary_message = {'type': 'mailbox', 'version':'v1.0', 'msgid':msgid , 'timestamp':timestamp}
            value = (json.dumps(new_dictionary_message) + '\n').encode()
            sys.stdout.write("destlist: " + str(destlist) + "\n")
            if(';' in destlist):
              newlist = destlist.split(';')
              for item in newlist:
                """ send msgid to callsign list"""  
                self.pnode.setValue(newlist[item], value)
            else:
              """ send msgid to callsign list"""  
              self.pnode.setValue(destlist, value)
          else:
            sys.stdout.write("destlist is None\n")

        elif(varsubtype == cn.P2P_IP_SEND_TEXT):
          sys.stdout.write("Command: P2P_IP_SEND_TEXT\n")
          msgid      = dict_obj.get('params').get('msgid')
          msg        = dict_obj.get('params').get('text')
          disc_group = dict_obj.get('params').get('tolist')
          timestamp  = dict_obj.get('params').get('timestamp')

          new_dictionary_message = {'type': 'text', 'version':'v1.0', 'msgid':msgid , 'disc_group':disc_group , 'timestamp':timestamp, 'text':msg}
          message = (json.dumps(new_dictionary_message) + '\n').encode()

          """ send the full message out to discussion group"""
          self.pnode.setValue(disc_group, message)

        elif(varsubtype == cn.P2P_IP_GET_TEXT):
          sys.stdout.write("Command: P2P_IP_GET_TEXT\n")
          key = dict_obj.get('params').get('disc_group')
          self.pnode.getdata(key, vpnpipe_address)


      elif(vartype == cn.P2P_IP_INFO):
        ID = dict_obj.get('params').get('ID')
        self.ID = str(ID)
        sys.stdout.write("received ID " + str(ID) + "\n")
        self.pnode.createServerObject(ID)


    except:
      sys.stdout.write("Exception in runReceive: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
  

    return


  """
  callback function used by processing thread
  """

def startvpn(ip, port, node, p2pthread):

  sys.stdout.write("startvpn\n")

  mypipeServer = JSONPipeVPNp2pnode('mailbox_server', (ip, port), cn.JSON_PIPE_SERVER)

  node.setPipe(mypipeServer, ip + ':' + str(port))
  t2 = threading.Thread(target=mypipeServer.listen)
  t2.start()
  mycallbackServer = JSONPipeVPNp2pnodeCallback(mypipeServer, node, p2pthread)
  mypipeServer.setCallback(mycallbackServer.json_server_callback)


def p2pThings(node, ip, port, serverport, delay):

  sys.stdout.write("p2pThings\n")

  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  if ip != None and port != None:
    node.createServerObjectFromBytes(digest(random.getrandbits(255)))
    node.connect_to_bootstrap_node(ip, port, serverport, delay)


def removeLoggers():
  logger = logging.getLogger('kademlia.network')
  for handler in logger.handlers[:]:
    logger.removeHandler(handler)
  logging.basicConfig()
  logger = logging.getLogger('kademlia.network')
  logger.propagate = False

def main():

  try:
    #removeLoggers()
    node = pNode()

    vpn = None
    ip = None
    port = None
    serverport = None
    delay = None
    (opts, args) = getopt.getopt(sys.argv[1:], "h:v:s:i:p:d",
      ["help", "vpn=", "server=", "ip=", "port=", "delay="])
    for option, argval in opts:
      if (option in ("-v", "--vpn")):
        vpn = argval
      elif (option in ("-i", "--ip")):
        ip = argval
      elif (option in ("-s", "--server")):
        serverport = argval
      elif (option in ("-p", "--port")):
        port = argval
      elif (option in ("-d", "--delay")):
        delay = argval

    sys.stdout.write("Delay is: " + str(delay) + "\n")

    t2 = threading.Thread(target=p2pThings, args=(node,ip, port, serverport,delay,))
    t2.start()

    sys.stdout.write("VPN is: " + str(vpn) + "\n")
    if vpn != None:
      vpn_if = vpn.split(':')[0]
      vpn_port = int(vpn.split(':')[1])
      startvpn(vpn_if, vpn_port, node, t2)
      #startvpn(vpn_if, vpn_port+1, node, t2)

  except:
    sys.stdout.write("Exception in main: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")



if __name__ == "__main__":
    main()
