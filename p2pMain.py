import logging
import sys
import asyncio
import threading
import traceback
import random
import json
import constant as cn
import debug as db
import os
import time
import operator
import umsgpack

from rpcudp.protocol import RPCProtocol
from kademlia.network import Server
from kademlia.network import log
from kademlia.protocol import KademliaProtocol
from kademlia.routing import RoutingTable
from kademlia.storage import IStorage
from kademlia.utils import digest
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node
from kademlia.crawling import ValueSpiderCrawl
from crc import Calculator, Configuration
from datetime import datetime, timedelta
from base64 import b64encode
from collections import OrderedDict
from hashlib import sha1
from saamfram_core_utils import SaamframCoreUtils
from itertools import takewhile


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


LOG = logging.getLogger(__name__)
mynodeid = None

class SuperKademliaProtocol(KademliaProtocol):

    pipe = None
    debug = db.Debug(cn.DEBUG_P2PNODE)

    def __init__(self, source_node, storage, ksize):
        RPCProtocol.__init__(self, 5)
        self.router = RoutingTable(self, ksize, source_node)
        self.storage = storage
        self.source_node = source_node

    """
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    """

    def _accept_response(self, msg_id, data, address):
        msgargs = (b64encode(msg_id), address)
        if msg_id not in self._outstanding:
            LOG.warning("received unknown message %s "
                        "from %s; ignoring", *msgargs)
            return
        LOG.debug("received response %s for message "
                  "id %s from %s", data, *msgargs)
        future, timeout = self._outstanding[msg_id]
        timeout.cancel()

        if not future.done():
          future.set_result((True, data))
        del self._outstanding[msg_id]

    def rpc_find_node(self, sender, nodeid, key):
      retval = super().rpc_find_node(sender, nodeid, key)
      self.debug.info_message("rpc_find_node return value:  " + str(retval) )

      if(len(retval) > 0):
        for item in retval:
          params={"NODEID":int(str(item[0].hex()), 16), "ip": item[1], "port": item[2] }
          if(self.pipe != None):
            self.sendit(params)

          self.friendly_display(item[0])
          self.debug.info_message("tuple [1]: " + str(item[1]) )
          self.debug.info_message("tuple [2]: " + str(item[2]) )
      return retval

    def friendly_display(self, node):
      self.debug.info_message("in hex : " + str(node.hex()) )
      decimal_value = int(str(node.hex()), 16)
      self.debug.info_message("in decimal : " + str(decimal_value) )

    def sendit(self, params):
      message = json.dumps({'type': cn.P2P_IP_INFO, 'subtype': cn.P2P_IP_NEIGHBORS, 'params': params})
      self.pipe.conn.sendall((message + '\n').encode())

    def setPipe(self, pipe):
      self.pipe = pipe

    def __getattr__(self, name):
        if name.startswith("_") or name.startswith("rpc_"):
            return getattr(super(), name)

        try:
            return getattr(super(), name)
        except AttributeError:
            pass

        def func(address, *args):
            msg_id = sha1(os.urandom(32)).digest()
            data = umsgpack.packb([name, args])
            if len(data) > 65507:
                raise MalformedMessage("Total length of function "
                                       "name and arguments cannot exceed 64K")
            txdata = b'\x00' + msg_id + data

            self.debug.info_message("SuperKademlia:__getattr__ calling remote function : " + str(name) + ' ' + str(address) + ' ' + str(b64encode(msg_id)) )

            self.transport.sendto(txdata, address)

            loop = asyncio.get_event_loop()
            if hasattr(loop, 'create_future'):
                future = loop.create_future()
            else:
                future = asyncio.Future()
            timeout = loop.call_later(self._wait_timeout,
                                      self._timeout, msg_id)
            self._outstanding[msg_id] = (future, timeout)
            return future

        return func



class SuperServer(Server):

    global mynodeid
    debug = db.Debug(cn.DEBUG_P2PNODE)

    pipe = None

    protocol_class = SuperKademliaProtocol

    def __init__( self, ksize, alpha, node_id, storage):
        mynodeid = node_id
        self.debug.info_message("mynodeid in hex : " + str(node_id.hex()) )
        decimal_value = int(str(node_id.hex()), 16)
        self.debug.info_message("mynodeid in decimal : " + str(decimal_value) )
        super().__init__( ksize, alpha, node_id, storage)


    async def dumpLocalStorage(self):
      self.debug.info_message("Storage dump is: " + str(self.protocol.storage.dumpit()) )
      return None      

    async def getIgnoreLocal(self, key):
        """
        Get a key if the network has it.

        Returns:
            :class:`None` if not found, the value otherwise.
        """
        log.info("Looking up key %s", key)
        dkey = digest(key)
        node = Node(dkey)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to get key %s", key)
            return None
        spider = ValueSpiderCrawl(self.protocol, node, nearest,
                                  self.ksize, self.alpha)
        return await spider.find()


    def _create_protocol(self):
        proto = SuperKademliaProtocol(self.node, self.storage, self.ksize)
        proto.setPipe(self.pipe)
        return proto

    def bootstrappable_neighbors(self):
      retval = super().bootstrappable_neighbors()
      self.debug.info_message("return value bootstrappable_neighbors: " + str(retval) )
      return retval

    def setPipe(self, pipe):
      self.pipe = pipe



""" use containers for {keys}.{inbox{}, chat{}, requests{}}"""
""" any extracted messages to be sent out need to be less than 64k in size"""
""" please note: even though key can host multiple data types with different expirations, the data should be distributed """
""" across multiple keys for example...<key>_mailbox or <key>_message or <key>_test """
""" primarily, data items are removed after expiry...secondarily old data is shed based on priority order in unlikely event that data exceeds max"""
""" priority order (lowest to highest) for data types is text, message, mailbox"""

"""
    self.multiValueStorage = { 'mailbox'     :       {<Message ID>      :  {'tolist'            : [],
                                                                            'timestamp'         : <timestamp>,
                                                                           },
                                                     },
                               'message'     :       {<Message ID>      :  {'message'           : <message>,
                                                                            'timestamp'         : <timestamp>,
                                                                           },
                                                     },                         
                               'text'        :       {<Message ID>      :  {'discussion_group'  : <discussion_group>,
                                                                            'text'              : <text>,
                                                                            'timestamp'         : <timestamp>,
                                                                           },
                                                     },                         
                               'mailgroup'   :       {<mailgroup_name>  :  {'participants'      : [],
                                                                            'owner'             : <owner>,
                                                                            'owner_cert'        : <owner_cert>,
                                                                            'timestamp'         : <timestamp>},
                                                     },                         
                               'request'     :       {<request_type>'   :  {'dest_recipient'    : <recipient>,
                                                                            'from'              : <from>,
                                                                            'data'              : <data>,
                                                                            'timestamp'         : <timestamp>},
                                                     },                   
                             }
"""

class MultiValueStorage(IStorage):

  debug = db.Debug(cn.DEBUG_P2PNODE)

  """ expirations...mailbox 2 weeks, message 7 days, text, 15 minutes"""
  """ in sequence order of lowest priority first so that shedding occurs from least priority to highest priority"""
  table_expirations = [['text',900], ['message',604800], ['mailbox',1209600] ]

  max_data_size = 65507

  def __init__(self, ttl=604800):
        self.sfram = SaamframCoreUtils()
        self.structured_data = OrderedDict()

  def dumpit(self):

    for key in self.structured_data.keys():
      for expiration_item in self.table_expirations:
        if expiration_item[0] in self.structured_data[key] :
          for msgidkey in self.structured_data[key][expiration_item[0]].keys() :

            self.debug.info_message("structured data message part name: " + str(expiration_item[0]) )
            self.debug.info_message("structured data message part: " + str(self.structured_data[key][expiration_item[0]]) )
            self.debug.info_message("structured data msgid part: " + str(self.structured_data[key][expiration_item[0]][msgidkey]) )
            self.debug.info_message("structured data msgid part[0]: " + str(self.structured_data[key][expiration_item[0]][msgidkey][0]) )

    return 'yes'


  def __setitem__(self, key, value):

        self.debug.info_message("__setitem__ in MultiValueStorage: key = " + str(key) + " , value = " + str(value) )

        if key not in self.structured_data:
          self.structured_data[key] = OrderedDict()

        try:
          if not isinstance(value, dict):
            dict_obj     = json.loads(value)
          else:
            dict_obj     = value
          message_type = dict_obj.get("type")

        except:
          self.debug.error_message("Exception in __setitem__: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
          self.cull()
          return

        """
        'message'     :       {<Message ID>      :  (<timestamp>, {'data'           : <message>}),
                              },                         
        """

        if message_type == 'message':
          msg = dict_obj.get("message")
          self.debug.info_message("type == message. msg = " + str(msg) )
          success, remainder = self.sfram.deconstructFragTagMsg(msg)
          ID, msgto, priority, timestamp, fromcall = self.sfram.deconstructFragmentedMessage(remainder)

          if 'message' not in self.structured_data[key]: 
            self.structured_data[key]['message'] = OrderedDict()

          self.structured_data[key]['message'][ID] = (time.monotonic(), {'data' : msg})
          
          """
          'mailbox'     :       {<Message ID>      :  <timestamp>  },
          """
        elif message_type == 'mailbox':
          ID = dict_obj.get("msgid")
          if 'mailbox' not in self.structured_data[key]: 
            self.structured_data[key]['mailbox'] = OrderedDict()
          self.structured_data[key]['mailbox'][ID] = (time.monotonic(),{})

          """
          'text'        :       {<Message ID>      :  (<timestamp>, {'discussion_group'  : <discussion_group>,
                                                                     'text'              : <text>}),
                                },                         
          """
        elif message_type == 'text':
          ID         = dict_obj.get("msgid")
          disc_group = dict_obj.get("disc_group")
          msg        = dict_obj.get("text")
          if 'text' not in self.structured_data[key]: 
            self.structured_data[key]['text'] = OrderedDict()
          self.structured_data[key]['text'][ID] = (time.monotonic(), {'disc_group': disc_group, 'text':msg})

        else:
          self.debug.info_message("unknown message type: " + str(message_type) )

        self.debug.info_message("structured_data[key] = " + str(self.structured_data[key]) )
        self.debug.info_message("structured_data = " + str(self.structured_data) )

        self.cull()


  """ method sheds data if total exceeds max 64k or if section exceeds alloted allocation in the 64k...each section allocation has 1/3 of total space """
  def shed(self):
        self.debug.info_message("MultiValueStorage shed")

        try:
          for key in self.structured_data.keys():
            if sys.getsizeof(json.dumps(self.structured_data[key])) > self.max_data_size :
              self.debug.verbose_message("MultiValueStorage total excees max")
              for expiration_item in self.table_expirations:
                if(expiration_item[0] in self.structured_data[key]):
                  while (sys.getsizeof(json.dumps(self.structured_data[key][expiration_item[0]])) > (self.max_data_size/3)) and (sys.getsizeof(json.dumps(self.structured_data[key])) > self.max_data_size) :
                    self.debug.verbose_message("MultiValueStorage section excees max. popping first item")
                    self.structured_data[key][expiration_item[0]].popitem(last=False)

                if sys.getsizeof(json.dumps(self.structured_data[key])) <= self.max_data_size :
                  break
        except:
          self.debug.error_message("Exception in shed: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

        self.debug.info_message("MultiValueStorage shed complete")

  def cull(self):

        self.debug.info_message("MultiValueStorage cull")

        try:
          now = time.monotonic()

          for key in self.structured_data.keys():
            for expiration_item in self.table_expirations:
              if(expiration_item[0] in self.structured_data[key]):
                keys_to_delete = []
                for msgidkey in self.structured_data[key][expiration_item[0]].keys() :

                  self.debug.verbose_message("structured data message part name: " + str(expiration_item[0]) )
                  self.debug.verbose_message("structured data message part: " + str(self.structured_data[key][expiration_item[0]]) )
                  self.debug.verbose_message("structured data msgid part: " + str(self.structured_data[key][expiration_item[0]][msgidkey]) )
                  self.debug.verbose_message("structured data msgid part[0]: " + str(self.structured_data[key][expiration_item[0]][msgidkey][0]) )

                  if self.structured_data[key][expiration_item[0]][msgidkey][0] + expiration_item[1] < now:
                    keys_to_delete.append(msgidkey)

                for delkey in keys_to_delete:
                  del self.structured_data[key][expiration_item[0]][delkey]

        except:
          self.debug.error_message("Exception in cull: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

        self.shed()

  def get(self, key, default=None):

        self.cull()
        if key in self.structured_data:
            return self[key]
        return default

  def __getitem__(self, key):

        self.cull()
        value = json.dumps(self.structured_data[key])
        return ((value + '\n').encode())

  def __repr__(self):
        self.cull()
        return repr(self.structured_data)

  def iter_older_than(self, seconds_old):

        """ new code. republish all keys """
        ikeys = self.structured_data.keys()
        ivalues = self.structured_data.values()
        return zip(ikeys, ivalues)

  def _triple_iter(self):
        return None

  def __iter__(self):
        self.cull()
        ikeys = self.structured_data.keys()
        ivalues = self.structured_data.values()
        return zip(ikeys, ivalues)


