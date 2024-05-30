#!/usr/bin/env python
import sys
import constant as cn
import string
import struct

try:
  import PySimpleGUI as sg
except:
  import PySimpleGUI27 as sg

import json
import threading
import os
import platform
import calendar
import xmlrpc.client
import random

import hrrm
import js8_form_gui
import js8_form_events

from datetime import datetime, timedelta
from datetime import time

from uuid import uuid4

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

class FormDictionary(object):

  """
  debug level 0=off, 1=info, 2=warning, 3=error
  """
  def __init__(self, debug):  

    self.template_file_dictionary_data = {}
    self.inbox_file_dictionary_data = {}
    self.outbox_file_dictionary_data = {}
    self.relaybox_file_dictionary_data = {}
    self.sentbox_file_dictionary_data = {}
    self.peerstn_file_dictionary_data = {}
    self.relaystn_file_dictionary_data = {}
#    self.conversion_file_dictionary_data = {}
    self.form_events = None
    self.group_arq = None
    self.debug = debug

    #self.recent_data_flecs_pend = []
    #self.recent_data_flecs_pend_timestamp = 0
    #self.rts_calsign = ''
    #self.rts_data = []
    #self.rtsrly_calsign = ''
    #self.rtsrly_data = []
    #self.dict_pend_rly_data = {}
    #self.dict_reqm_rly_data = {}

    self.dataFlecCache = {}
    self.dataFlecCache_clearAll()


    return

  def setFormEvents(self, form_events):
    self.form_events = form_events
    return

  def setGroupArq(self, group_arq):
    self.group_arq = group_arq
    return


  def dataFlecCache_addMsgPendPeer(self, ID, station, selected_item):

    self.debug.info_message("dataFlecCache_addMsgPendPeer")

    primary_key = station + '_' + ID
    current_dict = self.dataFlecCache.get('pending_peer')

    if(primary_key not in current_dict):
      current_dict[primary_key] = {'timestamp' : int(round(datetime.utcnow().timestamp())) ,
                                   'item'      : selected_item }

    return

  def dataFlecCache_addMsgPendRelay(self, ID, station, selected_item):

    self.debug.info_message("dataFlecCache_addMsgPendRelay")

    primary_key = station + '_' + ID
    current_dict = self.dataFlecCache.get('pending_relay')

    if(primary_key not in current_dict):
      current_dict[primary_key] = {'timestamp' : int(round(datetime.utcnow().timestamp())) ,
                                   'item'      : selected_item }

    return

  def dataFlecCache_addActivePeer(self, station):

    self.debug.info_message("dataFlecCache_addActivePeer")

    current_list = self.dataFlecCache.get('active_peer_calls')

    if(station not in current_list):
      current_list.append(station)
      self.dataFlecCache['active_peer_calls'] = current_list

    self.debug.info_message("dataFlecCache_addActivePeer: " + str(self.dataFlecCache) )

    return


  def dataFlecCache_addActiveRelay(self, station):

    self.debug.info_message("dataFlecCache_addActiveRelay")

    current_list = self.dataFlecCache.get('active_relay_calls')

    if(station not in current_list):
      current_list.append(station)
      self.dataFlecCache['active_relay_calls'] = current_list

    self.debug.info_message("dataFlecCache_addActiveRelay: " + str(self.dataFlecCache) )

    return

  def dataFlecCache_addRtsPeer(self, station, data_flecs):

    self.debug.info_message("dataFlecCache_addRtsPeer")

    timestamp = int(round(datetime.utcnow().timestamp()))
    current_dict = self.dataFlecCache.get('rts_peer')
    current_dict[station] = [timestamp, data_flecs]

    self.debug.info_message("dataFlecCache_addRtsPeer completed" )

    return

  def dataFlecCache_getRtsPeer(self, station):

    self.debug.info_message("dataFlecCache_getRtsPeer")

    current_dict = self.dataFlecCache.get('rts_peer')
    list_item = current_dict.get(station)

    data_flecs = list_item[1]
    self.debug.info_message("dataFlecCache_getRtsPeer completed" )

    return data_flecs

  def dataFlecCache_getRtsRelay(self, station):

    self.debug.info_message("dataFlecCache_getRtsRelay")

    current_dict = self.dataFlecCache.get('rts_relay')
    list_item = current_dict.get(station)

    data_flecs = list_item[1]
    self.debug.info_message("dataFlecCache_getRtsRelay completed" )

    return data_flecs

  def dataFlecCache_removeItemRtsPeer(self, station, rts_msgid):

    self.debug.info_message("dataFlecCache_removeItemRtsPeer")

    current_dict = self.dataFlecCache.get('rts_peer')
    list_item = current_dict.get(station)
    timestamp = list_item[0]
    data_flecs = list_item[1]
    data_flecs.remove(rts_msgid)
    #timestamp = int(round(datetime.utcnow().timestamp()))
    current_dict[station] = [timestamp, data_flecs]

    self.debug.info_message("dataFlecCache_removeItemRtsPeer completed" )

    return

  def dataFlecCache_removeItemRtsRelay(self, station, rts_msgid):

    self.debug.info_message("dataFlecCache_removeItemRtsRelay")

    current_dict = self.dataFlecCache.get('rts_relay')
    list_item = current_dict.get(station)
    timestamp = list_item[0]
    data_flecs = list_item[1]
    data_flecs.remove(rts_msgid)
    current_dict[station] = [timestamp, data_flecs]

    self.debug.info_message("dataFlecCache_removeItemRtsRelay completed" )

    return

  def dataFlecCache_addRtsRelay(self, station, data_flecs):

    self.debug.info_message("dataFlecCache_addRtsRelay")

    timestamp = int(round(datetime.utcnow().timestamp()))
    current_dict = self.dataFlecCache.get('rts_relay')
    current_dict[station] = [timestamp, data_flecs]

    self.debug.info_message("dataFlecCache_addRtsRelay completed" )

    return

  def dataFlecCache_clearActive(self):

    self.debug.info_message("dataFlecCache_clearActive")

    self.dataFlecCache['active_peer_calls']  = []
    self.dataFlecCache['active_relay_calls'] = []

    return

  def dataFlecCache_clearAll(self):

    self.debug.info_message("dataFlecCache_clearAll")

    self.dataFlecCache = {}

    self.dataFlecCache['active_peer_calls']  = []
    self.dataFlecCache['active_relay_calls'] = []
    self.dataFlecCache['pending_peer']       = {}
    self.dataFlecCache['requested_peer']     = {}
    self.dataFlecCache['pending_relay']      = {}
    self.dataFlecCache['requested_relay']    = {}
    self.dataFlecCache['confirmed_relay']    = {}
    self.dataFlecCache['rts_peer']           = {}
    self.dataFlecCache['rts_relay']          = {}

    return

  def dataFlecCache_rebuild(self, how_recent):

    self.debug.info_message("dataFlecCache_rebuild")

    self.selectRecentFromPeerstnDicttionaryItems(how_recent)
    self.selectRecentFromRelaystnDicttionaryItems(how_recent)

    self.dataFlecCache['pending_peer']       = {}
    self.dataFlecCache['pending_relay']      = {}

    self.dataFlecCache_rebuildMsgPendPeer()
    self.dataFlecCache_rebuildMsgPendRelay()

    self.debug.info_message("dataFlecCache_rebuild. Dictionary is: " + str(self.dataFlecCache) )

    return

  def dataFlecCache_rebuildMsgPendPeer(self):
    
    self.debug.info_message("dataFlecCache_rebuildMsgPendPeer")

    try:
      items = self.group_arq.getMessageOutbox()

      if(items == []):
        return

      current_list = self.dataFlecCache.get('active_peer_calls')

      for selected_item in items:
        to_list  = selected_item[1].split(';')
        priority = selected_item[4]
        msgid    = selected_item[6]


        for count in range(0,len(to_list)):
          station = to_list[count]
          if(station in current_list):
            self.dataFlecCache_addMsgPendPeer(msgid, station, selected_item)


    except:
      self.debug.error_message("Exception in dataFlecCache_rebuildMsgPendPeer: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return          

  def dataFlecCache_rebuildMsgPendRelay(self):
    
    self.debug.info_message("dataFlecCache_rebuildMsgPendRelay")

    items = self.group_arq.getMessageRelaybox()

    if(items == []):
      return

    current_list = self.dataFlecCache.get('active_relay_calls')

    for selected_item in items:
      to_list  = selected_item[1].split(';')
      priority = selected_item[4]
      msgid    = selected_item[6]

      for count in range(0,len(to_list)):
        station = to_list[count]
        if(station in current_list):
          self.dataFlecCache_addMsgPendRelay(msgid, station, selected_item)

    return          

  def dataFlecCache_selectRandomMsgPendPeer(self, num_msgs):

    self.debug.info_message("dataFlecCache_selectRandomMsgPendPeer")

    complete_message = ''

    try:

      current_dict = self.dataFlecCache.get('pending_peer')

      self.debug.info_message("pending peer messages:- " + str(current_dict))

      list_one = list(current_dict.items())
      list_two = []

      if(len(list_one) > num_msgs):
        for count in range(0, num_msgs):
          key = random.choice(list_one)
          list_two.append(key)
          list_one.remove(key)
      else:
        for key in current_dict:
          list_two.append(key)


      for count in range(0, len(list_two) ):
        self.debug.info_message("key is: " + str(list_two[count]))
        val = current_dict.get(list_two[count])
        selected_item = val.get('item')
        to_list  = selected_item[1]
        priority = selected_item[4]
        msgid    = selected_item[6]

        message = 'PEND(' + msgid + ',' + to_list 
        checksum = self.group_arq.saamfram.getChecksum(msgid + ',' + to_list)
        complete_message = complete_message + message + ',' + checksum +  '),'

      self.debug.info_message("dataFlecCache_selectRandomMsgPendPeer complete message: " + str(complete_message.strip(',')))

    except:
      self.debug.error_message("Exception in dataFlecCache_selectRandomMsgPendPeer: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    return complete_message.strip(',')


  def dataFlecCache_selectRandomMsgPendRelay(self, num_msgs):

    self.debug.info_message("dataFlecCache_selectRandomMsgPendRelay")

    complete_message = ''

    current_dict = self.dataFlecCache.get('pending_relay')
    list_one = list(current_dict.items())
    list_two = []

    if(len(list_one) > num_msgs):
      for count in range(0, num_msgs):
        key = random.choice(list_one)
        list_two.append(key)
        list_one.remove(key)
    else:
      for key in current_dict:
        list_two.append(key)
      #list_two = list_one

    for count in range(0, len(list_two) ):
      #key, val = current_dict.get(list_two[count])
      val = current_dict.get(list_two[count])
      selected_item = val.get('item')
      to_list  = selected_item[1]
      priority = selected_item[4]
      msgid    = selected_item[6]

      #FIXME HARDCODED
      dest_call = 'WH6TEST'
      total_hops = 0
      hops_from_source = 0
      conf_required = 0

      message_part = msgid + ',' + dest_call + ',' + str(total_hops) + ',' + str(hops_from_source) + ',' + str(conf_required) 
      message = 'PNDR(' + message_part
      checksum = self.group_arq.saamfram.getChecksum(message_part)
      complete_message = complete_message + message + ',' + checksum +  '),'

    return complete_message.strip(',')



  def dataFlecCache_create(self):

    self.debug.info_message("dataFlecCache_create")

    """
    self.dataFlecCache = { 'pending_peer'    :       {'destcallsign_ID'    : {'timestamp'     : '123',
                                                                              'source'        : 'abc',
                                                                              'conf_required' : 'abc',
                                                                              'hop_count'     : 'abc',
                                                                              'total_hops'    : 'abc'},
                                                     },
                           'requested_peer'  :       {'destcallsign_ID'    : {'timestamp' : '123',
                                                                           'source' : 'abc'},
                                                     },                         
                           'pending_relay'   :       {'destcallsign_ID'    : {'timestamp' : '123',
                                                                           'source' : 'abc'},
                                                     },                         
                           'requested_relay' :       {'destcallsign_ID'    : {'timestamp' : '123',
                                                                           'source' : 'abc'},
                                                     },                   
                           'confirmed_relay' :       {'destcallsign_ID'    : {'timestamp' : '123',
                                                                           'source' : 'abc'},
                                                     },                   
                         }
    """

    self.dataFlecCache_clearAll()


    #if(dest_call not in self.dict_pend_rly_data):
    #  self.dict_pend_rly_data[dest_call] = []

    #items = self.dict_pend_rly_data.get(dest_call)
    #items.append(str(msgid) + ',' + str(total_hops) + ',' + str(hops_from_source) + ',' + str(conf_required))
    #self.dict_pend_rly_data[dest_call] = items

    #self.debug.info_message("pend dictionary is: " + str(self.dict_pend_rly_data))
    #    timestamp_now = int(round(datetime.utcnow().timestamp()))
    #    self.debug.info_message("success")
    #    if(self.recent_data_flecs_pend_timestamp == 0):
    #      self.debug.info_message("LOC5")
    #      self.recent_data_flecs_pend_timestamp = timestamp_now
    #    elif(self.recent_data_flecs_pend_timestamp + 60 < timestamp_now):
    #      self.debug.info_message("LOC6")
    #      self.recent_data_flecs_pend_timestamp = timestamp_now
    #      self.recent_data_flecs_pend = []



    return


  """
  Template dictionary section
  """
  def setDataInDictionary(self, formname, category, filename, data):

    js = self.template_file_dictionary_data[filename]
    self.debug.info_message("dictionary data is: " + str(self.template_file_dictionary_data[filename]) )

    description = ''
    version = 0

    data_dictionary = js.get(category)		  

    for key in data_dictionary:
      self.debug.info_message("form name: " + key )
      if(key == formname):
        data_dictionary[key] = data
        self.debug.info_message("data is: " + str(data) )
        break

    self.debug.info_message("returning : " + str(data) )

    return (js)

  def getDataFromDictionary(self, field1, field2, field3, field4):

    data = None
    
    filename = field4

    js = self.template_file_dictionary_data[filename]

    self.debug.info_message("dictionary data is: " + str(self.template_file_dictionary_data[filename]) )

    description = ''
    version = 0
    category = self.form_events.current_edit_category

    data_dictionary = js.get(category)		  

    for key in data_dictionary:
      self.debug.info_message("form name: " + key )
      if(key == field1):
        data = data_dictionary.get(key)		  
        self.debug.info_message("data is: " + str(data) )
        break

    self.debug.info_message("returning : " + str(data) )

    return (data)

  def getFileDescriptionFromTemplateDictionary(self, filename):
    js = self.template_file_dictionary_data[filename]
    description = js.get('description')		  
    return description

  def getFileVersionFromTemplateDictionary(self, filename):
    js = self.template_file_dictionary_data[filename]
    version = js.get('version')		  
    return version

  def getTemplatesFromCategory(self, category):

    self.debug.info_message("getTemplatesFromCategory" )

    self.group_arq.clearTemplates()

    for file_key in self.template_file_dictionary_data:
      js = self.template_file_dictionary_data.get(file_key)
     
      self.debug.info_message("dictionary data is: " + str(js) )

      description = ''
      version = 0

      self.debug.info_message("getTemplatesFromCategory js: " + str(js))
      self.debug.info_message("getTemplatesFromCategory category: " + str(category))

      data_dictionary = js.get(category)		  

      self.debug.info_message("getTemplatesFromCategory data_dictionary: " + str(data_dictionary))

      if(data_dictionary != None):
        for key in data_dictionary:
          self.debug.info_message("form name: " + key )
          data = data_dictionary.get(key)		  

          self.debug.info_message("data: " + str(data) )

          version = data[0]		  
          self.debug.info_message("version: " + str(version) )
          description = data[1]
          self.debug.info_message("description: " + description )

          self.group_arq.addTemplate(key, description, str(version), file_key)

    return

    """
    details = { 'STD FORMS'   : {'General Message'    : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'OTHER FORM'         : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},
                'ICS FORMS'   : {'ICS Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ICS-213'            : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},                              
                'ABC FORMS'   : {'ABC Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ABC other'          : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},                              
                'GHI FORMS'   : {'ABC Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ABC other'          : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},
                'version'     : 1.3,
                'description' : 'my test forms' }
    """

  #FIXME add reply form to the format for a template
  #def createNewTemplateInDictionary(self, filename, category, formname, version, description, data, reply_formname):
  def createNewTemplateInDictionary(self, filename, category, formname, version, description, data):

    self.debug.info_message("createNewTemplateInDictionary 1 \n")

    dictionary = self.template_file_dictionary_data[filename]
    self.debug.info_message("dictionary data is: " + str(self.template_file_dictionary_data[filename]) )

    data_dictionary = {}

    self.debug.info_message("createNewTemplateInDictionary 2 \n")
    
    if(category in dictionary):
      self.debug.info_message("createNewTemplateInDictionary 3 \n")
      data_dictionary = dictionary.get(category)		  
      data_dictionary[formname] = data
    else:
      self.debug.info_message("createNewTemplateInDictionary 4 \n")
      data_dictionary[formname] = data
      dictionary[category] = data_dictionary
      
    self.debug.info_message("createNewTemplateInDictionary 5 \n")

    self.debug.info_message("new dictionary is: " + str(data_dictionary) )
      
    return (data_dictionary)


  def getTemplateFromTemplateDictionary(self, formname, category, filename):

    details = self.template_file_dictionary_data[filename]

    for key in details:
      if(key == 'description'):
        description = details.get("description")		  
        self.debug.info_message("description: " + description )
      elif(key == 'version'):
        version = details.get("version")		  
        self.debug.info_message("version: " + str(version) )
      else:
        if(key == category):
          template_dictionary = details.get(category)		  
          for template_key in template_dictionary:
            if(template_key == formname):
              template = template_dictionary.get(formname)
              return template			  
    return (None)

  def removeTemplatesFileFromTemplateDictionary(self, filename):
    self.debug.info_message("REMOVEING FILE: " + filename )
    self.template_file_dictionary_data.pop(filename, None)
    self.debug.info_message("REMOVED FILE\n")
    return (None)

  def removeTemplateFromTemplateDictionary(self, filename, category, formname):
    details = self.template_file_dictionary_data[filename]
    template_dictionary = details.get(category)		  
    template_dictionary.pop(formname, None)
    return (None)

  def removeCategoryFromTemplateDictionary(self, filename, category):
    details = self.template_file_dictionary_data[filename]
    details.pop(category, None)		  
    return (None)


  def getTemplateByFormFromTemplateDictionary(self, formname):

    for file_key in self.template_file_dictionary_data:
      category_dictionary = self.template_file_dictionary_data.get(file_key)		  

      for category_key in category_dictionary:
        if(category_key == 'description'):
          description = category_dictionary.get("description")		  
          self.debug.info_message("description: " + description )
        elif(category_key == 'version'):
          version = category_dictionary.get("version")		  
          self.debug.info_message("version: " + str(version) )
        else:
          template_dictionary = category_dictionary.get(category_key)		  
          for template_key in template_dictionary:
            if(template_key == formname):
              template = template_dictionary.get(formname)
              return template			  
    return (None)


  def getCategoryAndFilenameFromFormname(self, formname):

    for file_key in self.template_file_dictionary_data:
      category_dictionary = self.template_file_dictionary_data.get(file_key)		  

      for category_key in category_dictionary:
        if(category_key == 'description'):
          description = category_dictionary.get("description")		  
          self.debug.info_message("description: " + description )
        elif(category_key == 'version'):
          version = category_dictionary.get("version")		  
          self.debug.info_message("version: " + str(version) )
        else:
          template_dictionary = category_dictionary.get(category_key)		  
          for template_key in template_dictionary:
            if(template_key == formname):
              return category_key, file_key			  
    
    return None, None


  def writeTemplateDictToFile(self, filename):
 
    """ individual fields first """	  
    """
    details = { 'STD FORMS'   : {'General Message'    : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'OTHER FORM'         : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},
                'ICS FORMS'   : {'ICS Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ICS-213'            : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},                              
                'ABC FORMS'   : {'ABC Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ABC other'          : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},                              
                'GHI FORMS'   : {'ABC Message'        : ['v1.0','my description','T1,I1','T2,I2,T5,I3','T3,I2,T6,I3','T4,I2','T7','I4'],
                              'ABC other'          : ['v1.0','my description','T8,I1','T2,I5,T9,I5','T3,I5,T9,I5','T4,I1','T7,T5,I3,T6,I3','I4', 'T10,I5,T9,I5']},
                'version'     : 1.3,
                'description' : 'my test forms' }
    """
    
    details = self.template_file_dictionary_data[filename]

    self.debug.info_message("writeTemplateDictToFile: " + str(filename) )
    self.debug.info_message("writeTemplateDictToFile: " + str(details) )
 
    try:
      with open(filename, 'w') as convert_file:
                convert_file.write(json.dumps(details))
    except:
      self.debug.error_message("Exception in writeTemplateDictToFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
              
    return()


  def readTemplateDictFromFile(self, filename):

    with open(filename) as f:
      data = f.read()
  
    """  
    reconstructing the data as a dictionary
    """
    js = json.loads(data)

    """ now add the edited data object """	  
    self.template_file_dictionary_data[filename] = js

    self.debug.info_message("dictionary data is: " + str(self.template_file_dictionary_data[filename]) )

    description = ''
    version = 0
    for key in js:
      if(key == 'description'):
        description = js.get("description")		  
        self.debug.info_message("description: " + description )
      elif(key == 'version'):
        version = js.get("version")		  
        self.debug.info_message("version: " + str(version) )
      else:
        self.group_arq.addCategory(key)
        self.debug.info_message("category: " + key )

    """ add the loaded template to the list """
    self.group_arq.addLoadedTemplateFile(filename, description, version)
   
    return(js)


  """ fail safe. code standard form templates in memory"""
  def readTemplateDictFromMemory(self, filename):

    self.debug.info_message("readTemplateDictFromMemory: " + filename )

    data= {}

    if(filename == 'standard_templates.tpl'):
      data = {"version": 1.0, "description": "my test forms", "GENERAL": {"EMAIL": ["v1.0", "EMAIL FORM", "0B,E4", "02", "@C,@C", "M1", "47", "01"],
                                                                          "BULLETIN": ["v1.0", "BULLETIN FORM", "0B,B9", "02", "@C", "FC,@1,23", "FB,@1,23", "S1,@3,23", "00", "@C", "B8,@2,24", "D3,@1,24", "@Q,IP", "01", "02", "@C,@D", "B9", "47", "01"],
                                                                          "QUICKMSG": ["v1.0", "QUICK MESSAGE FORM", "0B,Q2", "02", "@C", "AJ,@4,23", "FB,@1,23", "S1,@3,23", "00", "@C", "SJ,@1,23", "D3,@1,23", "01", "02", "@C,@D", "47", "01"]}}
    elif(filename == 'ICS_Form_Templates.tpl'):
      data = {"version": 1.0, "description": "my test forms", "ICS FORMS": {"ICS 213": ["v1.0", "ICS 213 Form", "0B,G5", "03", "0C,I1,@3,#8,42", "0C,T1,@2,42", "0C,F4,@1,42",\
                       "0C,S1,@4,26,@1,0C,D1,#9,10,@1,0C,T2,#A,42", "03", "0C,09,M1", "47", "03", "0C,A1,24,@1,P1,42"],
                                                                            "ICS 214": ["v1.0", "ICS 214 Form", "0B,AI", "02", "06,05", "0C,I1,@5,P2", "#8,24,10", "00", "06", "0C,O2",\
                       "DH,20,@1,T6,20", "01", "02", "06,05", "0C,N5,42", "0D,H5,42", "00", "06,05", "0E,IO,42", "01", "05", "0C,09,R4", "#2,N5,IO,H5", "05", "0C,09,AH", "#3,D3,NB", "0C,P9,22"],
                                                                            "ICS 206": ["v1.0", "ICS 206 Form", "0B,M8", "02", "06", "0C,I1", "#8,42", "06", "00", "06", "0C,O2", "D4,13,@1,D5,13",\
                       "T7,13,@1,T8,13", "01", "06", "0C,09,M6", "#1,N5,L3,CB,PE", "03", "0C,09,TE", "#1,AA,AB,CB,L9", "03", "0C,09,H1", "#1,H2,AD,CB,TF,TN,TM,BA,H6", "@C", "0C,09,M7", "44",\
                       "0C,P9,22", "0C,AF,20,D3,13,I2,5"],
                                                                            "ICS 204": ["v1.0", "ICS 204 Form", "0B,A4", "02", "0C,I1,@1,0C,O2", "#8,20,D4,13,D5,13", "0U,0K,T7,13,T8,13", "05",\
                       "0D,O3,@3,N1", "O4,@2,42", "B3,@4,42", "D7,@1,42", "00", "0E,B2", "20", "D6", "20", "G1", "20", "SA", "20", "01", "0C,09,R4", "#1,R4,L1,N2,C5,R5", "0C,09,W1", "44", "0C,09,S6",\
                       "44", "0C,09,C6", "#1,N5,F3,P3", "0C,P4,N5,#6,20,P1,#7,20,D3,#B,20", "I8,@4,I2,5"],
                                                                            "ICS 205": ["v1.0", "ICS 205 Form", "0B,I3", "02", "06,05", "0C,I1,0X,@5,0C,D2", "#8,24,@1,#B,21", "00", "06", "0C,O2",\
                       "D4,13,@1,D5,13", "T7,13,@1,T8,13", "01", "03", "0C,09,B1", "#2,Z1,C2,F3,CF,A2,R1,RH,T9,TK,M2,R3", "03", "0C,09,S6", "45", "03", "0C,A3,N5,22,D3,13,I2,5"],
                                                                            "ICS 309": ["v1.0", "ICS 309 Form", "0B,C4", "02", "07", "B4", "B4", "F2,@1,42", "O1,@3,#6,42", "00", "07",\
                       "TB,10,@1,D2,@1,#B,42", "B4", "T4,28", "S2,20,E1,#5,42", "01", "P2,2,@1,T5", "#4,D3,SK,SL,S1"], 
                                                                            "ICS 205A": ["v1.0", "ICS 205A Form", "02", "06", "0C,I1", "#8,42", "06", "00", "06", "0C,O2", "D4,13,@1,D5,13",\
                       "T7,13,@1,T8,13", "01,0F", "0C,B1,P2,5", "#3,A2,N5,MB", "0C,A3,22,D3,17"], 
                                                                            "ICS 202": ["v1.0", "ICS 202 Form", "0B,I5", "02", "06", "0C,I1", "#8,42", "06", "00", "06", "0C,O2", "D4,13,@1,D5,13",\
                       "T7,13,@1,T8,13", "01,0F", "03", "0C,09,O5", "44", "03", "0C,09,O6", "44", "03", "09,G2", "44", "0C,S7,@Q,Y2", "S8,42", "0C,I6", "02", "0T,I7", "0T,I8", "0T,I9", "0T,IB",\
                       "0T,IC", "00", "0T,ID", "0T,IE", "0T,M3", "0T,W2", "00", "O7", "A5,42", "A5,42", "A5,42", "A5,42", "01", "0C,P4,N5,20,P1,20,S9,20", "0C,A6,N5,20,S9,20", "D3,22", "IF,05,I2,10"], 
                                                                            "ICS 208": ["v1.0", "ICS 208 Form", "0B,SE", "02", "06", "0C,I1", "#8,42", "06", "00", "06", "0C,O2", "D4,13,@1,D5,13",\
                       "T7,13,@1,T8,13", "01", "03", "0C,09,SF", "45", "0C,S7,0S,Y1,0S,N6", "S8,42", "03", "0C,P4,N5,20,P1,20,S9,20", "D3,@1,#B,20", "03", "IE,I2,5"], 
                                                                            "ICS 210": ["v1.0", "ICS 210 Form", "0B,R7", "02", "06", "0C,I1", "#8,42", "06", "00", "06", "0C,O2", "D4,13,@1,D5,13",\
                       "T7,13,@1,T8,13", "01,0F", "#3,R8,N7,F1,T6,TH", "0C,CG", "43", "0C,P4,22,D3,#B,20"], 
                                                                            "ICS 213 RR": ["v1.0", "ICS 213 RR Form", "0B,R9", "02", "06,05", "0C,I1,#8,42", "0D,RA,42", "00", "06", "0E,D3,#B,20",\
                        "01", "03", "09,RB", "0C,OA", "DD", "#2,Q1,K1,TI,II,RC,E2,CC", "0C,DE,42", "0C,SG,43", "0C,RD,22,0C,PA,0S,L6,0S,RE,0S,U1", "0C,SH,42", "09,L7", "0C,L8,42", "0C,SI,42",\
                        "0C,N9,22,PB,42", "0C,N3,42", "0C,NA,22,0C,D3,20", "0C,OB,24", "09,F8", "0C,RF", "44", "0C,F9,22,0C,D3,20"], 
                                                                             "ICS 214A": ["v1.0", "ICS 214A Form", "0B,IM", "02", "06,05", "0C,I1,0X,@5,P2", "#8,24,@1,10", "00", "06", "0C,O2",\
                        "DH,13,@1,T6,13", "01", "03", "0C,IQ,15,0C,IN,20", "0C,AG,42", "0C,09,AH", "#3,T2,MA", "0C,P4,24"], 
                                                                             "ICS 215A": ["v1.0", "ICS 215A Form", "0B,IJ", "02", "06,05", "0C,09,I1", "#8,42", "06", "0D,09,D2", "D1,#9,13,T2,#A,13",\
                        "00", "06,05", "0E,09,IK", "42", "06", "0C,09,O2", "D4,13,D5,13", "T7,13,T8,13", "01,0F", "#2,IL,H4,M9", "02", "0C,PC", "PD", "D3,20", "00", "N5,20,S9,20", "N5,20,S9,20", "01"], 
                                                                             "ICS 217A": ["v1.0", "ICS 217A Form", "0B,CD", "02", "06", "B4", "W3,20", "00", "06,03", "FA,@R,Q4", "DG,#B,42", "00",\
                        "05", "DF,20", "01", "03", "#3,CE,CF,E3,RG,RI,RH,TJ,TO,TK,M2,R3"]}}

    else:
      return

    self.debug.info_message("readTemplateDictFromMemory got the data: " + str(data))

    """  
    reconstructing the data as a dictionary
    """

    try:

      js = data 

      """ now add the edited data object """	  
      self.template_file_dictionary_data[filename] = js

      self.debug.info_message("dictionary data is: " + str(self.template_file_dictionary_data[filename]) )

      description = ''
      version = 0
      for key in js:
        if(key == 'description'):
          description = js.get("description")		  
          self.debug.info_message("description: " + description )
        elif(key == 'version'):
          version = js.get("version")		  
          self.debug.info_message("version: " + str(version) )
        else:
          self.group_arq.addCategory(key)
          self.debug.info_message("category: " + key )

      """ add the loaded template to the list """
      self.group_arq.addLoadedTemplateFile(filename, description, version)
   
      return(js)

    except:
      self.debug.error_message("Exception in readTemplateDictFromMemory: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return None


    """
    This is the format of data in the oubox dictionary
    
    details = { 'ID_GGO_123654'   : {'content'            : ['fred','smith','100 great nothing road','everwhere','the moon','M34-345','Good afternnon I hope all is well 73 Fred'],
                                     'to'                 : ['WH6ABC','WH6DEF','WH6GHI'],
                                     'from'               : ['WH6GGO'],
                                     'subject'            : ['Hi there hope all is well'],
                                     'timestamp'          : ['WH6ABC'],
                                     'ID'                 : ['WH6ABC'],
                                     'priority'           : ['WH6ABC'],
                                     'formname'           : ['WH6ABC']},
                'ID_FGH_123654'   : {'content'            : ['fred','smith','100 great nothing road','everwhere','the moon','M34-345','Good afternnon I hope all is well 73 Fred'],
                                     'to'                 : ['WH6ABC','WH6DEF','WH6GHI'],
                                     'from'               : ['WH6GGO'],
                                     'subject'            : ['Hi there hope all is well'],
                                     'timestamp'          : ['WH6ABC'],
                                     'ID'                 : ['WH6ABC'],
                                     'priority'           : ['WH6ABC'],
                                     'formname'           : ['WH6ABC']},
              }
    """

  """
  Relaybox dictionary section
  """

  def getRelayboxDictionaryItem(self, msgid):
    dictionary = self.relaybox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    return dictionary2

  def getContentFromRelayboxDictionary(self, msgid):
    dictionary = self.relaybox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    content = dictionary2.get('content')		  
    return content

  def getFormnameFromRelayboxDictionary(self, msgid):
    dictionary = self.relaybox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    formname = dictionary2.get('formname')		  
    return formname


  def getVerifiedFromRelayboxDictionary(self, msgid):

    try:
      dictionary = self.relaybox_file_dictionary_data[msgid]
      dictionary2 = dictionary.get('0')
      verified = dictionary2.get('verified')		  
    except:
      self.debug.error_message("Exception in getVerifiedFromRelayboxDictionary: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      return ''

    return verified

  #FICME DELETE
  def getVerifiedFromRelayboxDictionary2(self, msgid):
    dictionary = self.relaybox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    verified = dictionary2.get('verified')		  

    #FIXME
    verified = 'yes'

    return verified


  def writeRelayboxDictToFile(self, filename):
   
    filename = 'relaybox.msg'
 
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(self.relaybox_file_dictionary_data))
    return()

  def readRelayboxDictFromFile(self, filename):

    try:
      with open(filename) as f:
        data = f.read()

      self.relaybox_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readRelayboxDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.relaybox_file_dictionary_data = {}

  

    self.group_arq.clearRelaybox()

    for key in self.relaybox_file_dictionary_data:
      ID = key
      pages = self.relaybox_file_dictionary_data.get(ID)
      message = pages.get('0')

      msgto     = message.get('to')
      msgfrom   = message.get('from')
      subject   = message.get('subject')
      timestamp = message.get('timestamp')
      priority  = message.get('priority')
      formname  = message.get('formname')
      verified  = message.get('verified')
      confrcvd  = message.get('confrcvd')
      fragsize  = message.get('fragsize')

      self.group_arq.addMessageToRelaybox(msgfrom, msgto, subject, timestamp, priority, formname, ID, confrcvd, fragsize, verified)
   
    return 

  def resetRelayboxDictionary(self):
    self.relaybox_file_dictionary_data = {}
    return


  def doesRelayboxDictionaryItemExist(self, msgid):

    if msgid in self.relaybox_file_dictionary_data:
      return True
    else:
      return False
    return


  def createRelayboxDictionaryItem(self, ID, msgto, msgfrom, subject, priority, timestamp, formname, confrcvd, fragsize, content, verified):

    if( ID in self.relaybox_file_dictionary_data):
      self.debug.info_message("createRelayboxDictionaryItem item already exists in relaybox")
      pages = self.relaybox_file_dictionary_data.get(ID)
      page_zero = pages.get('0')
      get_verified  = page_zero.get('verified')
      """ already have a verified copy so don't update anything"""
      if(get_verified == 'Verified'):
        return (self.relaybox_file_dictionary_data)
      
      """ partial is upgrade from stub so do not down-grade."""
      if(get_verified == 'Partial' and verified == 'Stub'):
        return (self.relaybox_file_dictionary_data)


    self.debug.info_message("createRelayboxDictionaryItem replacing the dictionary item")

    self.relaybox_file_dictionary_data[ID] = { '0' : {'content'            : content,
                                                      'to'                 : msgto,
                                                      'from'               : msgfrom,
                                                      'subject'            : subject,
                                                      'timestamp'          : timestamp,
                                                      'priority'           : priority,
                                                      'verified'           : verified,
                                                      'confrcvd'           : confrcvd,
                                                      'fragsize'           : fragsize,
                                                      'formname'           : formname} }

    self.group_arq.addMessageToRelaybox(msgfrom, msgto, subject, timestamp, priority, formname, ID, confrcvd, fragsize, verified)
    self.group_arq.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
    self.group_arq.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

    return (self.relaybox_file_dictionary_data)



  def removeRelayboxDictionaryItem(self, ID):
    if( ID in self.relaybox_file_dictionary_data):
      self.debug.info_message("removeRelayboxDictionaryItem item exists in relaybox")

      pages = self.relaybox_file_dictionary_data.get(ID)
      pages.pop('0', None)		  
      self.relaybox_file_dictionary_data.pop(ID)

    return (None)


  def getContentByIdFromRelayboxDictionary(self, ID):

    message_dictionary = self.relaybox_file_dictionary_data.get(ID)		  
    message_dictionary2 = message_dictionary.get('0')

    for message_key in message_dictionary2:
      if(message_key == 'description'):
        description = message_dictionary2.get("description")		  
        self.debug.info_message("description: " + description )
      elif(message_key == 'version'):
        version = message_dictionary2.get("version")		  
        self.debug.info_message("version: " + str(version) )
      else:
        content = message_dictionary2.get('content')
        return content
    return (None)



  """
  MainPanel Peer Station 
  """
  def createPeerstnDictionaryItem(self, callsign, number, grid, selected, rigname, modulation, snr, lastheard):

    self.peerstn_file_dictionary_data[callsign] = {'number'               : number,
                                                   'grid'                 : grid,
                                                   'selected'             : selected,
                                                   'rigname'              : rigname,
                                                   'modulations'          : modulation,
                                                   'snr'                  : snr,
                                                   'lastheard'            : lastheard}

    return (self.peerstn_file_dictionary_data)


  def getItemsForPeerstnDictItem(self, station):

    for x in range (len(self.group_arq.selected_stations)):
      lineitem = self.group_arq.selected_stations[x]
      callsign = lineitem[0]
      if(callsign == station):
        num        = lineitem[1]
        grid       = lineitem[2]
        memo       = lineitem[3]
        connect    = lineitem[4]
        rig        = lineitem[5]
        modulation = lineitem[6]
        snr        = lineitem[7]
        last_heard = lineitem[8]

        return num, grid, connect, rig, modulation, snr, last_heard

    return '','','','','','',''

  def getRandomPeerstnDictItem(self):

    items = self.group_arq.getSelectedStations()

    if(items == []):
      return '', '', ''

    lineitem = random.choice(items)

    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    memo       = lineitem[3]
    connect    = lineitem[4]
    rig        = lineitem[5]
    modulation = lineitem[6]
    snr        = lineitem[7]
    last_heard = lineitem[8]

    return last_heard, grid, '2'

  def writePeerstnDictToFile(self, filename):
   
    filename = 'peerstn.sav'

    """ clear out all the data from the dictionary then recreate it from the main panel view """ 

    for x in range (len(self.group_arq.selected_stations)):
      lineitem = self.group_arq.selected_stations[x]
      callsign   = lineitem[0]
      num        = lineitem[1]
      grid       = lineitem[2]
      memo       = lineitem[3]
      connect    = lineitem[4]
      rig        = lineitem[5]
      modulation = lineitem[6]
      snr        = lineitem[7]
      last_heard = lineitem[8]

      self.createPeerstnDictionaryItem(callsign, num, grid, connect, rig, modulation, snr, last_heard)
  
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(self.peerstn_file_dictionary_data))
    return()

  def readPeerstnDictFromFile(self, filename):

    filename = 'peerstn.sav'

    try:
      with open(filename) as f:
        data = f.read()
  
      self.peerstn_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readPeerstnDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.peerstn_file_dictionary_data = {}

    self.group_arq.clearSelectedStations()

    for key in self.peerstn_file_dictionary_data:
      station    = key
      message    = self.peerstn_file_dictionary_data.get(key)
      num        = message.get('number')
      grid       = message.get('grid')
      connect    = message.get('selected')
      rig        = message.get('rigname')
      modulation = message.get('modulation')
      snr        = message.get('snr')
      last_heard = message.get('lastheard')

      self.group_arq.addSelectedStation(station, num, grid, connect, rig, modulation, snr, last_heard)
   
    return 


  def selectRecentFromPeerstnDicttionaryItems(self, how_recent):

    self.debug.info_message("selectRecentFromPeerstnDicttionaryItems" )

    """ write them back first """
    for x in range (len(self.group_arq.selected_stations)):
      lineitem   = self.group_arq.selected_stations[x]
      callsign   = lineitem[0]
      num        = lineitem[1]
      grid       = lineitem[2]
      memo       = lineitem[3]
      connect    = lineitem[4]
      rig        = lineitem[5]
      modulation = lineitem[6]
      snr        = lineitem[7]
      last_heard = lineitem[8]

      self.createPeerstnDictionaryItem(callsign, num, grid, connect, rig, modulation, snr, last_heard)

    timenow = int(round(datetime.utcnow().timestamp()*100))

    self.group_arq.clearSelectedStations()

    try:

      for key in self.peerstn_file_dictionary_data:
        message    = self.peerstn_file_dictionary_data.get(key)
        ID         = message.get('lastheard')

        timestamp_string = ID.split('_',1)[1]
        inttime = int(timestamp_string,36)
        difference = timenow - inttime

        self.debug.info_message("Station is : " + str(key) )
        self.debug.info_message("Difference is : " + str(difference) )
        self.debug.info_message("How recent is: " + str(how_recent) )


        if(difference < how_recent):

          self.debug.info_message("ADDING stn : " + str(key) )
          station    = key
          num        = message.get('number')
          grid       = message.get('grid')
          connect    = message.get('selected')
          rig        = message.get('rigname')
          modulation = message.get('modulation')
          snr        = message.get('snr')
          self.group_arq.addSelectedStation(station, num, grid, connect, rig, modulation, snr, ID)

          self.dataFlecCache_addActivePeer(station)
          #if(station not in self.group_arq.active_station_checklist):
          #  self.group_arq.active_station_checklist.append(station)

    except:
      self.debug.error_message("Exception in selectRecentFromPeerstnDicttionaryItems: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    self.debug.info_message("selectRecentFromPeerstnDicttionaryItems: completed" )

    return 


  """
  MainPanel Relay Stations 
  """
  def createRelaystnDictionaryItem(self, callsign, number, grid, relay_callsign, selected, hops, lastheard):

    self.relaystn_file_dictionary_data[callsign] = {'number'                : number,
                                                    'grid'                  : grid,
                                                    'relaycallsign'         : relay_callsign,
                                                    'selected'              : selected,
                                                    'hops'                  : hops,
                                                    'lastheard'             : lastheard}

    return (self.relaystn_file_dictionary_data)

  def getRandomRelaystnDictItem(self):

    items = self.group_arq.getSelectedRelayStations()

    if(items == []):
      return '', '', '', ''

    lineitem = random.choice(items)

    callsign   = lineitem[0]
    num        = lineitem[1]
    grid       = lineitem[2]
    relay_stn  = lineitem[3]
    connect    = lineitem[4]
    hops       = lineitem[5]
    last_heard = lineitem[6]

    return callsign, last_heard, grid, str(int(hops)+1)



  def writeRelaystnDictToFile(self, filename):
   
    filename = 'relaystn.sav'

    """ clear out all the data from the dictionary then recreate it from the main panel view """ 

    for x in range (len(self.group_arq.selected_relay_stations)):
      lineitem = self.group_arq.selected_relay_stations[x]
      callsign       = lineitem[0]
      num            = lineitem[1]
      grid           = lineitem[2]
      relay_callsign = lineitem[3]
      connect        = lineitem[4]
      hops           = lineitem[5]
      last_heard     = lineitem[6]

      self.createRelaystnDictionaryItem(callsign, num, grid, relay_callsign, connect, hops, last_heard)
  
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(self.relaystn_file_dictionary_data))
    return()

  def readRelaystnDictFromFile(self, filename):

    filename = 'relaystn.sav'

    try:
      with open(filename) as f:
        data = f.read()
  
      self.relaystn_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readRelaystnDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.relaystn_file_dictionary_data = {}

    self.group_arq.clearSelectedRelayStations()

    for key in self.relaystn_file_dictionary_data:
      station        = key
      message        = self.relaystn_file_dictionary_data.get(key)
      num            = message.get('number')
      grid           = message.get('grid')
      relay_callsign = message.get('relaycallsign')
      connect        = message.get('selected')
      hops           = message.get('hops')
      last_heard     = message.get('lastheard')

      self.group_arq.addSelectedRelayStation(station, num, grid, relay_callsign, connect, hops, last_heard)
   
    return 

  def selectRecentFromRelaystnDicttionaryItems(self, how_recent):

    self.debug.info_message("selectRecentFromRelaystnDicttionaryItems" )

    """ write back first """
    for x in range (len(self.group_arq.selected_relay_stations)):
      lineitem   = self.group_arq.selected_relay_stations[x]
      callsign   = lineitem[0]
      num        = lineitem[1]
      grid       = lineitem[2]
      relay      = lineitem[3]
      selected   = lineitem[4]
      hops       = lineitem[5]
      last_heard = lineitem[6]

      self.createRelaystnDictionaryItem(callsign, num, grid, relay, selected, hops, last_heard)

    timenow = int(round(datetime.utcnow().timestamp()*100))

    self.group_arq.clearSelectedRelayStations()

    for key in self.relaystn_file_dictionary_data:
      message    = self.relaystn_file_dictionary_data.get(key)
      ID         = message.get('lastheard')

      timestamp_string = ID.split('_',1)[1]
      inttime = int(timestamp_string,36)
      difference = timenow - inttime

      self.debug.info_message("difference is: " + str(difference) )

      if(difference < how_recent):
        station    = key
        num            = message.get('number')
        grid           = message.get('grid')
        relay_callsign = message.get('relaycallsign')
        connect        = message.get('selected')
        hops           = message.get('hops')

        self.group_arq.addSelectedRelayStation(station, num, grid, relay_callsign, connect, hops, ID)

        self.dataFlecCache_addActiveRelay(station)
        #if(station not in self.group_arq.active_station_checklist):
        #  self.group_arq.active_station_checklist.append(station)


    self.debug.info_message("selectRecentFromRelaystnDicttionaryItems. completed" )
   
    return 



  """
  Outbox dictionary section
  """
  def writeOutboxDictToFile(self, filename):
   
    filename = 'outbox.msg'
 
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(self.outbox_file_dictionary_data))
    return()

  def readOutboxDictFromFile(self, filename):

    try:
      with open(filename) as f:
        data = f.read()
  
      self.outbox_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readOutboxDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.outbox_file_dictionary_data = {}


    self.group_arq.clearOutbox()

    for key in self.outbox_file_dictionary_data:
      ID = key
      message = self.outbox_file_dictionary_data.get(key)
      msgto     = message.get('to')
      msgfrom   = message.get('from')
      subject   = message.get('subject')
      timestamp = message.get('timestamp')
      priority  = message.get('priority')
      formname  = message.get('formname')

      self.group_arq.addMessageToOutbox(msgfrom, msgto, subject, timestamp, priority, formname, ID)
   
    return 

  def createOutboxDictionaryItem(self, ID, msgto, msgfrom, subject, priority, timestamp, formname, content):

    self.outbox_file_dictionary_data[ID] = {'content'            : content,
                                            'to'                 : msgto,
                                            'from'               : msgfrom,
                                            'subject'            : subject,
                                            'timestamp'          : timestamp,
                                            'priority'           : priority,
                                            'formname'           : formname}

    return (self.outbox_file_dictionary_data)

  def removeOutboxDictionaryItem(self, ID):
    if( ID in self.outbox_file_dictionary_data):
      self.debug.info_message("removeOutboxDictionaryItem item exists in outbox")
      self.outbox_file_dictionary_data.pop(ID)

    return (None)



  def getContentFromOutboxDictionary(self, msgid):
    dictionary = self.outbox_file_dictionary_data[msgid]
    content = dictionary.get('content')		  
    return content


  def getPagesKeyvalFromOutboxDictionary(self, mainID):
    self.debug.info_message("getPagesKeyvalFromOutboxDictionary")
    parent_keyval = self.outbox_file_dictionary_data.get(mainID)

    self.debug.info_message("parent_keyval: " + str(parent_keyval) )

    self.debug.info_message("completed getPagesKeyvalFromOutboxDictionary")

    return parent_keyval



  def getContentByIdFromOutboxDictionary(self, ID):

    message_dictionary = self.outbox_file_dictionary_data.get(ID)		  
    for message_key in message_dictionary:
      if(message_key == 'description'):
        description = message_dictionary.get("description")		  
        self.debug.info_message("description: " + description )
      elif(message_key == 'version'):
        version = message_dictionary.get("version")		  
        self.debug.info_message("version: " + str(version) )
      else:
        content = message_dictionary.get('content')
        return content
    return (None)

  def doesOutboxDictionaryItemExist(self, msgid):

    if msgid in self.outbox_file_dictionary_data:
      return True
    else:
      return False
    return

  """ currently used for testing purposes only"""
  def getVerifiedFromOutboxDictionary(self, msgid):
    dictionary = self.outbox_file_dictionary_data[msgid]

    verified = dictionary.get('verified')		  

    #verified = 'yes'
    return verified

  def getOutboxDictionaryItem(self, msgid):
    dictionary = self.outbox_file_dictionary_data[msgid]
    return dictionary

  """
  Inbox dictionary section
  """

  def getInboxDictionaryItem(self, msgid):
    dictionary = self.inbox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    return dictionary2


  def getContentFromInboxDictionary(self, msgid):
    dictionary = self.inbox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    content = dictionary2.get('content')		  
    return content

  def getFormnameFromInboxDictionary(self, msgid):
    dictionary = self.inbox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    formname = dictionary2.get('formname')		  
    return formname

  def getVerifiedFromInboxDictionary(self, msgid):
    dictionary = self.inbox_file_dictionary_data[msgid]
    dictionary2 = dictionary.get('0')
    verified = dictionary2.get('verified')		  
    return verified


  def resetInboxDictionary(self):
    self.inbox_file_dictionary_data = {}
    return

  def writeInboxDictToFile(self, filename):

    self.debug.info_message("Writing inbox to file\n")
   
    try:
      filename = 'inbox.msg'
 
      with open(filename, 'w') as convert_file:
                convert_file.write(json.dumps(self.inbox_file_dictionary_data))
    except:
      self.debug.error_message("Exception in writeInboxDictToFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return()

  def readInboxDictFromFile(self, filename):

    try:
      with open(filename) as f:
        data = f.read()
  
      self.inbox_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readInboxDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.inbox_file_dictionary_data = {}


    self.group_arq.clearInbox()

    for key in self.inbox_file_dictionary_data:
      ID = key
      pages = self.inbox_file_dictionary_data.get(ID)
      message = pages.get('0')
      msgto     = message.get('to')
      msgfrom   = message.get('from')
      subject   = message.get('subject')
      timestamp = message.get('timestamp')
      priority  = message.get('priority')
      formname  = message.get('formname')
      verified  = message.get('verified')
      missing_frames = message.get('missingframes')
      self.group_arq.addMessageToInbox(msgfrom, msgto, subject, timestamp, priority, formname, verified, ID)
   
    return 

  def doesInboxDictionaryItemExist(self, msgid):

    if msgid in self.inbox_file_dictionary_data:
      return True
    else:
      return False
    return

  def createInboxDictionaryItem(self, ID, msgto, msgfrom, subject, priority, timestamp, formname, content, verified):

    missing_frames = 'F1,F2,F3'

    if( ID in self.inbox_file_dictionary_data):
      self.debug.info_message("createInboxDictionaryItem item already exists in inbox")
      pages = self.inbox_file_dictionary_data.get(ID)
      page_zero = pages.get('0')
      get_verified  = page_zero.get('verified')
      """ already have a verified copy so don't update anything"""
      if(get_verified == 'Verified'):
        return (self.inbox_file_dictionary_data)
      
      """ partial is upgrade from stub so do not down-grade."""
      if(get_verified == 'Partial' and verified == 'Stub'):
        return (self.inbox_file_dictionary_data)

    """ either not present or not verified so take the new parameters and use them"""
    self.inbox_file_dictionary_data[ID] = { '0'  :  {'content'            : content,
                                                     'to'                 : msgto,
                                                     'from'               : msgfrom,
                                                     'subject'            : subject,
                                                     'timestamp'          : timestamp,
                                                     'priority'           : priority,
                                                     'formname'           : formname,
                                                     'verified'           : verified,
                                                     'missingframes'      : missing_frames} }

    self.group_arq.addMessageToInbox(msgfrom, msgto, subject, timestamp, priority, formname, verified, ID)
    self.group_arq.form_gui.window['table_inbox_messages'].update(values=self.group_arq.getMessageInbox() )
    self.group_arq.form_gui.window['table_inbox_messages'].update(row_colors=self.group_arq.getMessageInboxColors())

    return (self.inbox_file_dictionary_data)


  def addInboxDictionaryReply(self, mainID, replyID, msgto, msgfrom, subject, priority, timestamp, formname, content):
    missing_frames = ''

    verified = 'yes'

    parent_keyval = self.inbox_file_dictionary_data[mainID]

    page_num = len(parent_keyval)

    parent_keyval[page_num] = {'content'            : content,
                               'to'                 : msgto,
                               'from'               : msgfrom,
                               'subject'            : subject,
                               'timestamp'          : timestamp,
                               'priority'           : priority,
                               'formname'           : formname,
                               'verified'           : verified,
                               'missingframes'      : missing_frames,
                               'replyid'            : replyID} 

    self.inbox_file_dictionary_data[mainID] = parent_keyval

    self.debug.info_message("added page to inbox dictionary: " + str(self.inbox_file_dictionary_data)  )

    return (self.inbox_file_dictionary_data)

  def getPagesKeyvalFromInboxDictionary(self, mainID):
    self.debug.info_message("getPagesKeyvalFromInboxDictionary")
    parent_keyval = self.inbox_file_dictionary_data.get(mainID)

    self.debug.info_message("parent_keyval: " + str(parent_keyval) )

    self.debug.info_message("completed getPagesKeyvalFromInboxDictionary")

    return parent_keyval


  """
  Sendbox dictionary section
  """
  def getContentFromSentboxDictionary(self, msgid):
    dictionary = self.sentbox_file_dictionary_data[msgid]
    content = dictionary.get('content')		  
    return content

  def getFormnameFromSentboxDictionary(self, msgid):
    dictionary = self.sentbox_file_dictionary_data[msgid]
    formname = dictionary.get('formname')		  
    return formname

  def writeSentDictToFile(self, filename):
   
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(self.sentbox_file_dictionary_data))
    return()

  def readSentDictFromFile(self, filename):

    try:
      with open(filename) as f:
        data = f.read()
  
      self.sentbox_file_dictionary_data = json.loads(data)

    except:
      self.debug.error_message("Exception in readSentDictFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.sentbox_file_dictionary_data = {}



    self.group_arq.clearSentbox()

    for key in self.sentbox_file_dictionary_data:
      ID = key
      message = self.sentbox_file_dictionary_data.get(key)
      msgto     = message.get('to')
      msgfrom   = message.get('from')
      subject   = message.get('subject')
      timestamp = message.get('timestamp')
      priority  = message.get('priority')
      formname  = message.get('formname')
      confirmed = message.get('confirmed')

      self.group_arq.addMessageToSentbox(msgfrom, msgto, subject, timestamp, priority, formname, ID, confirmed)
   
    return 

  def createSentboxDictionaryItem(self, ID, msgto, msgfrom, subject, priority, timestamp, formname, content, confirmed):

    self.sentbox_file_dictionary_data[ID] = {'content'            : content,
                                             'to'                 : msgto,
                                             'from'               : msgfrom,
                                             'subject'            : subject,
                                             'timestamp'          : timestamp,
                                             'priority'           : priority,
                                             'formname'           : formname,
                                             'confirmed'          : confirmed}

    return (self.sentbox_file_dictionary_data)




  """
  Multiple dictioary categories section
  """
  def transferOutboxMsgToSentbox(self, ID):

    """ locate the message """
    message = self.outbox_file_dictionary_data.get(ID)
    msgto     = message.get('to')
    msgfrom   = message.get('from')
    subject   = message.get('subject')
    timestamp = message.get('timestamp')
    priority  = message.get('priority')
    formname  = message.get('formname')
    content   = message.get('content')

    confirmed = 'All'

    """ copy the message over """
    self.createSentboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content, confirmed)
    self.group_arq.addMessageToSentbox(msgfrom, msgto, subject, timestamp, priority, formname, ID, confirmed)

    return

  """
  Multiple dictioary categories section
  """
  def transferOutboxMsgToRelaybox(self, ID):

    try:
      """ locate the message """
      message = self.outbox_file_dictionary_data.get(ID)
      msgto     = message.get('to')
      msgfrom   = message.get('from')
      subject   = message.get('subject')
      timestamp = message.get('timestamp')
      priority  = message.get('priority')
      formname  = message.get('formname')
      content   = message.get('content')

      #FIXME DO NOT HARD CODE THESE!!!! 
      confirmed_received = 'yes'
      frag_size = 20
      verified = 'Verified'

      """ copy the message over """
      self.createRelayboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, confirmed_received, frag_size, content, verified)

    except:
      self.debug.error_message("Exception in transferOutboxMsgToRelaybox: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return


  def transferRelayboxMsgToOutbox(self, ID):

    self.debug.info_message("transferRelayboxMsgToOutbox")

    try:
      """ locate the message """
      message = self.relaybox_file_dictionary_data.get(ID)
      message_dictionary2 = message.get('0')

      content   = message_dictionary2.get('content')
      msgto     = self.group_arq.forwardMsgRemoveOwnCallsign(message_dictionary2.get('to'))
      msgfrom   = message_dictionary2.get('from')
      subject   = message_dictionary2.get('subject')
      timestamp = message_dictionary2.get('timestamp')
      priority  = message_dictionary2.get('priority')

      verified  = message_dictionary2.get('verified')
      confrcvd  = message_dictionary2.get('confrcvd')
      fragsize  = message_dictionary2.get('fragsize')

      formname  = message_dictionary2.get('formname')

      """ copy the message over """
      self.createOutboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content)
      self.group_arq.addMessageToOutbox(msgfrom, msgto, subject, timestamp, priority, formname, ID)

      self.debug.info_message("Adding message " + ID)

    except:
      self.debug.error_message("Exception in transferOutboxMsgToRelaybox: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return

  def transferRelayboxMsgToSentbox(self, ID):

    self.debug.info_message("transferRelayboxMsgToSentbox")

    try:
      """ locate the message """
      message = self.relaybox_file_dictionary_data.get(ID)
      message_dictionary2 = message.get('0')

      content   = message_dictionary2.get('content')
      msgto     = message_dictionary2.get('to')
      msgfrom   = message_dictionary2.get('from')
      subject   = message_dictionary2.get('subject')
      timestamp = message_dictionary2.get('timestamp')
      priority  = message_dictionary2.get('priority')

      verified  = message_dictionary2.get('verified')
      confrcvd  = message_dictionary2.get('confrcvd')
      fragsize  = message_dictionary2.get('fragsize')

      formname  = message_dictionary2.get('formname')

      """ copy the message over """
      self.createSentboxDictionaryItem(ID, msgto, msgfrom, subject, priority, timestamp, formname, content, 'All')
      self.group_arq.addMessageToSentbox(msgfrom, msgto, subject, timestamp, priority, formname, ID, 'All')

      self.removeRelayboxDictionaryItem(ID)
      self.group_arq.deleteMessageFromRelaybox(ID)

      self.removeOutboxDictionaryItem(ID)
      self.group_arq.deleteMessageFromOutbox(ID)

      self.group_arq.form_gui.window['table_relay_messages'].update(values=self.group_arq.getMessageRelaybox() )
      self.group_arq.form_gui.window['table_relay_messages'].update(row_colors=self.group_arq.getMessageRelayboxColors())

      self.group_arq.form_gui.window['table_sent_messages'].update(values=self.group_arq.getMessageSentbox() )
      self.group_arq.form_gui.window['table_outbox_messages'].update(values=self.group_arq.getMessageOutbox() )

      self.debug.info_message("Adding message " + ID)

    except:
      self.debug.error_message("Exception in transferRelayboxMsgToSentbox: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return


  def retrieveSequence(self, js, seqName):
    params  = js.get("params")
    sequences = params.get('Sequences')
    return sequences.get(seqName)

  def retrieveSequenceByName(self, js, seqName):
    params  = js.get("params")
    sequences = params.get('Sequences')

    for key in sequences: 
      value = sequences.get(key)
      if(value.get('name') == seqName):
        return value

    return None

  def createSequenceDefaults(self):

    self.debug.info_message("createSequenceDefaults")

    sequenceDefaults = { 'Sequence1'  :  {'name'                    : 'Test1',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'BPSK500',
                                          'frag_modes'              : 'PSK1000RC2,PSK125RC16,PSK63RC32,PSK250RC6,BPSK500'},
                         'Sequence2'  :  {'name'                    : 'Test2',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'BPSK500',
                                          'frag_modes'              : 'PSK250RC6,PSK500RC3,PSK125RC12,PSK1000R,BPSK500'},
                         'Sequence3'  :  {'name'                    : 'Test3',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK250RC3',
                                          'frag_modes'              : 'OFDM750F,PSK250RC7,PSK500RC2,8PSK125,PSK250RC3'},
                         'Sequence4'  :  {'name'                    : 'Test4',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK500R',
                                          'frag_modes'              : 'BPSK500,PSK250RC3,8PSK250FL,8PSK250F,PSK500R'},
                         'Sequence5'  :  {'name'                    : 'Test5',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : '8PSK125FL',
                                          'frag_modes'              : 'OFDM500F,QPSK250,BPSK250,THOR100,8PSK125FL'},
                         'Sequence6'  :  {'name'                    : 'Test6',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK250RC3',
                                          'frag_modes'              : 'OFDM750F,PSK250RC7,PSK125RC10,PSK63RC20,PSK250RC3'},
                         'Sequence7'  :  {'name'                    : 'Test7',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'DOMX44',
                                          'frag_modes'              : 'PSK1000RC2,BPSK500,PSK250RC3,8PSK250FL,DOMX44'},
                         'Sequence8'  :  {'name'                    : 'Test8',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK250RC3',
                                          'frag_modes'              : 'PSK63RC32,PSK500RC3,BPSK500,PSK800RC2,PSK250RC3'},
                         'Sequence9'  :  {'name'                    : 'Test9',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK250RC3',
                                          'frag_modes'              : 'PSK500RC3,PSK1000R,PSK125RC16,BPSK500,PSK250RC3'},
                         'Sequence10' :  {'name'                    : 'Test10',
                                          'acknack_retransmits'     : 4,
                                          'fragment_retransmits'    : 5,
                                          'control_mode'            : 'PSK250R',
                                          'frag_modes'              : 'THOR100,8PSK125FL,8PSK125F,MT63-2KL,MT63-2KS'},

                       }

    self.debug.info_message("end createSequenceDefaults")

    return sequenceDefaults

  def createMainDictionaryDefaults(self):
    js = { 'params': {
                           'ConnectTo'               : '',
                           'WinlinkInboxFolder'      : '',
                           'WinlinkOutboxFolder'     : '',
                           'WinlinkRMSMsgFolder'     : '',
                           'WinlinkPatBinary'        : '',
                           'WinlinkPatTemplatesFolder'   : '',
                           'WinlinkOverridePatBinary'   : '',
                           'WinlinkDefaultMode'   : 'Vara',
                           'WinlinkDefaultStation'   : '',

                           'ExtAppsJs8Net'           : '',
                           'ExtAppsJs8NetBinary'     : '' if (platform.system() == 'Linux') else 'c:\\Program Files (x86)\\HRRM\\js8_net_client.exe',

                           'GeneralRetries1'           : '10',
                           'GeneralRetries2'           : '2',

                           'InboxStationMemo'          : 'CQ POTA',

                           'AutoAnswer'                : True,

                           'RewriteFrom'             : False,
                           'IncludeHRRMExport'           : False,


                           'AutoReplyPeer'           : False,
                           'AutoReplyRelay'          : False,
                           'TXEnable'                : True,

                           'EmailForwardType'        : 'Internet',
                           'FormForwardType'         : 'None',

                           'DisplayTheme'            : 'DarkBlue14',
                           'EmailAutoForward'        : True,
                           'FormsAutoForward'        : True,

                           'Sequences'               : self.createSequenceDefaults(),

                           'Templates'           : ['ICS_Form_Templates.tpl'],
                           'UseAttachedGps'      : 'Rig1',
                           'AutoReceive'         : True,
                           'AutoLoadTemplate'    : True,

                           'UseConnectTo'        : True,

                           'TrustOrigSenderOnly' : False,
                           'TrustedRelays'       : '',  
                           'Rig1Vox'             : True,
                           'Rig1Js8callIp'       : '127.0.0.1',
                           'Rig1Js8callPort'     : '2442',
                           'Rig1Js8callMode'     : 'Turbo',
                           'Rig1FldigiIp'        : '127.0.0.1',
                           'Rig1FldigiPort'      : '7362',
                           'Rig1FldigiMode'      : 'MODE 16 - PSK500R',
                           'Rig2Vox'             : False,
                           'Rig2Js8callIp'       : '127.0.0.1',
                           'Rig2Js8callPort'     : '7442',
                           'Rig2Js8callMode'     : 'Turbo',
                           'Rig2FldigiIp'        : '172.0.0.1',
                           'Rig2FldigiPort'      : '7363',
                           'Rig2FldigiMode'      : 'MODE 16 - PSK500R',

                           'ComposeTabClr'       : 'slate gray',
                           'ChatTabClr'          : 'slate gray',
                           'InboxTabClr'         : 'slate gray',
                           'OutboxTabClr'        : 'slate gray',
                           'SentboxTabClr'       : 'slate gray',
                           'RelayboxTabClr'      : 'slate gray',
                           'InfoTabClr'          : 'slate gray',
                           'ColorsTabClr'        : 'slate gray',
                           'SettingsTabClr'      : 'slate gray',

                           'FldigChannelClr'     : 'Red',
                           'Js8CallChannelClr'   : 'Red',
                           'TxButtonClr'         : 'Red',
                           'MessagesBtnClr'      : 'Red',
                           'ClipboardBtnClr'     : 'Red',
                           'TabClr'              : 'Red',
                           'TxRig'               : 'Red',
                           'Flash1Clr'           : 'Red',
                           'Flash2Clr'           : 'Red',
                           'StubMsgClr'          : 'Red',
                           'PartialMsgClr'       : 'Red',
                           'CompleteMsgClr'      : 'Red',
                           'AllConfirmedMsgClr'       : 'Red',
                           'NotAllConfirmedMsgClr'    : 'Red',
                           'FormHeadingClr'           : 'Red',
                           'FormSubHeadingClr'        : 'Green1',
                           'NumberedSectionClr'       : 'Yellow',
                           'TableHeaderClr'           : 'Cyan',
                           'FormHeadingTextClr'       : 'white',
                           'FormSubHeadingTextClr'    : 'black',
                           'NumberedSectionTextClr'   : 'black',
                           'TableHeaderTextClr'       : 'black',
                           'FormPreviewBackgroundClr' : 'Red',

                           'TxRig'               : 'Rig1',
                           'TxModeType'          : 'FLDIGI',
                           'Rig1Name'            : 'Kenwood',
                           'Rig1Modem'           : 'FLDIGI',
                           'Rig1Mode'            : 'MODE 16 - PSK500R',
                           'Rig1FragmSize'       : '30',
                           'Rig2Name'            : 'Yaesu',
                           'Rig2Modem'           : 'JS8CALL',
                           'Rig2Mode'            : 'Turbo',
                           'Rig2FragmSize'       : '30',
                           'CallSign'            : 'WH6TEST',
                           'GroupName'           : '@HRRM',
                           'OperatorName'        : '<enter operator name here>',
                           'OperatorTitle'       : '<enter operator title here>',
                           'IncidentName'        : '<enter incident name here>',
                           'FirstName'           : '<enter first name here>',
                           'LastName'            : '<enter last name here>',
                           'Title'               : '<enter title here>',
                           'Position'            : '<enter position here>',
                           'GPSLat'              : '<enter GPS latitude here>',
                           'GPSLong'             : '<enter GPS longitude here>',
                           'GridSquare'          : 'BK34ZZ',
                           'Location'            : '<enter QTH name here>',} }

    return js

  """
  Main application settings dictionary
  """
  def readMainDictionaryFromFile(self, filename):

    js_defaults = self.createMainDictionaryDefaults()
    params_default = js_defaults.get("params")

    try:
      with open(filename) as f:
        data = f.read()
 
      js = json.loads(data)

      params_read    = js.get("params")

      for key in params_default: 
        value = params_default.get(key)
        if(key not in params_read):
          """ upgrade the file format set the new parama to a default value"""
          params_read[key]=value
          self.debug.info_message("UPGRADING FILE FORMAT")
          self.debug.info_message("adding key: " + str(key) )

    except:
      self.debug.error_message("Exception in readMainDictionaryFromFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      js = js_defaults

    auto_load_templates = js.get("params").get('AutoLoadTemplate')
    params = js.get("params")

    """ set these to hardcoded values for now """
    params['Templates'] = [['ICS_Form_Templates.tpl', 'ICS Forms', 1.0], ["standard_templates.tpl", "Standard Forms", 1.0]]

    if(auto_load_templates):
      self.group_arq.clearCategories()
      templates = js.get("params").get('Templates')
      for x in range (len(templates)):
        try:
          self.readTemplateDictFromFile(templates[x][0])
          self.debug.info_message("LOADING TEMPLATE: " + templates[x][0] )
        except:
          self.debug.info_message("UNABLE TO LOAD TEMPLATE: " + templates[x][0] )
          """ fail safe..."""
          self.readTemplateDictFromMemory(templates[x][0])

    return(js)


  """ writes the messages to the messages file """
  def writeMainDictionaryToFile(self, filename, values):

    details = self.group_arq.saamfram.main_params
    params  = details.get("params")
    params['Templates'] = self.group_arq.getLoadedTemplateFiles()

    """ individual fields first """	  
    details = { 'params': {
                           'ConnectTo'               : values['in_inbox_listentostation'],
                           'WinlinkInboxFolder'      : self.group_arq.form_gui.getWinlinkInboxFolder(),#values['in_winlink_inboxfolder'],
                           'WinlinkOutboxFolder'     : self.group_arq.form_gui.getWinlinkOutboxFolder(),#values['in_winlink_outboxfolder'],
                           'WinlinkRMSMsgFolder'     : self.group_arq.form_gui.getWinlinkRmsmsgFolder(),#values['in_winlink_rmsmsgfolder'],
                           'WinlinkPatBinary'        : values['input_general_patbinary'],
                           'WinlinkPatTemplatesFolder'   : '', #values['input_general_pattemplatesfolder'],
                           'WinlinkOverridePatBinary'   : values['cb_general_patbinaryoverride'],
                           'WinlinkDefaultMode'   : values['option_general_patmode'],
                           'WinlinkDefaultStation'   : values['input_general_patstation'],

                           'ExtAppsJs8Net'           : values['cb_general_extappsjs8net'],
                           'ExtAppsJs8NetBinary'     : values['input_general_extappsjs8netbinary'],

                           'GeneralRetries1'           : values['input_general_retries_1'],
                           'GeneralRetries2'           : values['input_general_retries_2'],

                           'InboxStationMemo'           : values['in_mainwindow_stationtext'],

                           'AutoAnswer'                : values['cb_mainwindow_autoanswer'],

                           'RewriteFrom'             : values['cb_general_rewrite_from'],
                           'IncludeHRRMExport'           : values['cb_general_include_HRRM_export'],

                           'AutoReplyPeer'           : values['cb_general_autoreply_peer'],
                           'AutoReplyRelay'          : values['cb_general_autoreply_relay'],
                           'TXEnable'                : values['cb_mainwindow_txenable'],

                           'EmailForwardType'        : values['option_general_forwardemailtype'],
                           'FormForwardType'         : values['option_general_forwardformtype'],

                           'DisplayTheme'            : values['listbox_theme_select'],
                           'EmailAutoForward'        : values['cb_general_autoforward'],
                           'FormsAutoForward'        : values['cb_general_autoforward_forms'],

                           'Sequences'               : self.group_arq.saamfram.main_params.get('params').get('Sequences'),

                           'Templates'           : self.group_arq.getLoadedTemplateFiles(), #['ICS_Form_Templates.tpl'],
                           'UseAttachedGps'      : 'Rig1',
                           'AutoReceive'         : values['cb_general_auto_receive_stub_from_rts'],
                           'AutoLoadTemplate'    : values['cb_settings_autoload'],

                           'UseConnectTo'        : values['cb_chat_useconnecto'],

                           'TrustOrigSenderOnly' : values['cb_settings_trustorigsndronly'],
                           'TrustedRelays'       : values['in_settings_trustedrelays'],  
                           'Rig1Vox'             : values['cb_settings_vox1'],
                           'Rig1Js8callIp'       : values['input_settings_js8callip1'],
                           'Rig1Js8callPort'     : values['input_settings_js8callport1'],
                           'Rig1Js8callMode'     : 'Turbo',  #values[''],
                           'Rig1FldigiIp'        : values['input_settings_fldigiip1'],
                           'Rig1FldigiPort'      : values['input_settings_fldigiport1'],
                           'Rig1FldigiMode'      : values['combo_settings_fldigimoode1'],
                           'Rig2Vox'             : values['cb_settings_vox2'],
                           'Rig2Js8callIp'       : values['input_settings_js8callip2'],
                           'Rig2Js8callPort'     : values['input_settings_js8callport2'],
                           'Rig2Js8callMode'     : 'Turbo',  #values[''],
                           'Rig2FldigiIp'        : values['input_settings_fldigiip2'],
                           'Rig2FldigiPort'      : values['input_settings_fldigiport2'],
                           'Rig2FldigiMode'      : values['combo_settings_fldigimoode2'],

                           'ComposeTabClr'      : values['option_colors_compose_tab'],
                           'ChatTabClr'         : values['option_colors_chat_tab'],
                           'InboxTabClr'        : values['option_colors_inbox_tab'],
                           'OutboxTabClr'       : values['option_colors_outbox_tab'],
                           'SentboxTabClr'      : values['option_colors_sentbox_tab'],
                           'RelayboxTabClr'     : values['option_colors_relay_tab'],
                           'InfoTabClr'         : values['option_colors_info_tab'],
                           'ColorsTabClr'       : values['option_colors_colors_tab'],
                           'SettingsTabClr'     : values['option_colors_settings_tab'],

                           'FldigChannelClr'    : 'Red',  #values[''],
                           'Js8CallChannelClr'  : 'Red',  #values[''],
                           'TxButtonClr'        : values['option_colors_tx_btns'],
                           'MessagesBtnClr'     : values['option_colors_msgmgmt_btns'],
                           'ClipboardBtnClr'    : values['option_colors_clipboard_btns'],
                           'TabClr'             : 'Red',  #values[''],
                           'TxRig'              : 'Red',  #values[''],
                           'Flash1Clr'          : 'Red',  #values[''],
                           'Flash2Clr'          : 'Red',  #values[''],
                           'StubMsgClr'         : 'Red',  #values[''],
                           'PartialMsgClr'      : 'Red',  #values[''],
                           'CompleteMsgClr'     : 'Red',  #values[''], 
                           'AllConfirmedMsgClr'       : 'Red',  #values[''],
                           'NotAllConfirmedMsgClr'    : 'Red',  #values[''],
                           'FormHeadingClr'           : values['option_main_heading_background_clr'],
                           'FormSubHeadingClr'        : values['option_sub_heading_background_clr'],
                           'NumberedSectionClr'       : values['option_numbered_section_background_clr'],
                           'TableHeaderClr'           : values['option_table_header_background_clr'],
                           'FormHeadingTextClr'           : values['option_main_heading_text_clr'],
                           'FormSubHeadingTextClr'        : values['option_sub_heading_text_clr'],
                           'NumberedSectionTextClr'       : values['option_numbered_section_text_clr'],
                           'TableHeaderTextClr'           : values['option_table_header_text_clr'],
                           'FormPreviewBackgroundClr' : 'Red',  #values[''],

                           'TxRig'           : 'Red',  #values[''],
                           'TxModeType'      : 'Red',  #values[''],
                           'Rig1Name'        : 'Red',  #values[''],
                           'Rig1Modem'       : 'Red',  #values[''],
                           'Rig1Mode'        : 'Red',  #values[''],
                           'Rig1FragmSize'   : 'Red',  #values[''],
                           'Rig2Name'        : 'Red',  #values[''],
                           'Rig2Modem'       : 'Red',  #values[''],
                           'Rig2Mode'        : 'Red',  #values[''],
                           'Rig2FragmSize'   : 'Red',  #values[''],
                           'CallSign'        : values['input_myinfo_callsign'],
                           'GroupName'       : values['input_myinfo_group_name'],
                           'OperatorName'    : values['input_myinfo_operator_name'],
                           'OperatorTitle'   : values['input_myinfo_operator_title'],
                           'IncidentName'    : values['input_myinfo_incident_name'],
                           'FirstName'       : values['input_myinfo_firstname'],
                           'LastName'        : values['input_myinfo_lastname'],
                           'Title'           : values['input_myinfo_title'],
                           'Position'        : 'Red',  #values[''],
                           'GPSLat'          : values['input_myinfo_gpslat'],
                           'GPSLong'         : values['input_myinfo_gpslong'],
                           'GridSquare'      : values['input_myinfo_gridsquare'],
                           'Location'        : values['input_myinfo_location'],} }

 
    with open(filename, 'w') as convert_file:
              convert_file.write(json.dumps(details))
    return()


