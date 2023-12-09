from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import select
import constant as cn
import xmlrpc.client
import re
import smtplib
import http.client
import socket
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

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

class WinlinkImport(object):

  def __init__(self, debug):  
    self.debug = debug
    return

  def parseBasicXmlInfo(self, xml_string):

    try:
      myroot = ET.fromstring(xml_string)

      for x in myroot.findall('variables'):
        formstring    = x.find('templateversion').text
        split_string  = formstring.split(' ')

        self.debug.info_message("length of split string = " + str(len(split_string)) )

        form_type     = split_string[0]

        form_name = ''
        form_version = ''
        if(len(split_string) > 1):
          form_name     = split_string[1]

        #form_name     = split_string[1]
          if(split_string[2]!=''):
            form_version  = split_string[2]
          else:
            form_version  = split_string[3]
 
        sender        = x.find('msgsender').text

      return form_type + ' ' + form_name, sender

    except:
      self.debug.error_message("Exception in parseBasicXmlInfo: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))



  def parseWinlinkXml(self, xml_string):

    try:
      self.debug.info_message("parseWinlinkXml")
      self.debug.info_message("parseWinlinkXml xml string: " + xml_string)

      myroot = ET.fromstring(xml_string)

      self.debug.info_message("parseWinlinkXml LOC1")
      self.debug.info_message("parseWinlinkXml root: " + str(myroot) )

      for x in myroot[0]:
        self.debug.info_message("parseWinlinkXml tag: " + str(x.tag) )
        self.debug.info_message("parseWinlinkXml attrib: " + str(x.attrib) )

      for x in myroot[0]:
        self.debug.info_message("parseWinlinkXml text: " + str(x.text) )

      for x in myroot.findall('variables'):
        formstring    = x.find('templateversion').text
        split_string  = formstring.split(' ')
        form_type     = split_string[0]
        form_name     = split_string[1]
        if(split_string[2]!=''):
          form_version  = split_string[2]
        else:
          form_version  = split_string[3]
 
        from_name     = x.find('fm_name').text
        to_name       = x.find('to_name').text
        msgto         = x.find('msgto').text
        #msgsubject    = x.find('msgsubject').text
        subjectline   = x.find('subjectline').text
        mtime         = x.find('mtime').text
        mdate         = x.find('mdate').text
        incident_name = x.find('inc_name').text
        approved_name = x.find('approved_name').text
        approved_pos  = x.find('approved_postitle').text
        sender        = x.find('msgsender').text
        message_text  = x.find('message').text
        self.debug.info_message("parseWinlinkXml sender: " + str(sender) )
        self.debug.info_message("parseWinlinkXml message_text: " + str(message_text) )

      self.debug.info_message("parseWinlinkXml incident name: " + str(incident_name) )
      self.debug.info_message("parseWinlinkXml to name: " + str(to_name) )
      self.debug.info_message("parseWinlinkXml from name: " + str(from_name) )
      self.debug.info_message("parseWinlinkXml subject: " + str(subjectline) )
      form_content = [incident_name, to_name, from_name, subjectline, mdate, mtime, message_text, approved_name, approved_pos]
      return form_type + ' ' + form_name, form_content, msgto, subjectline

    except:
      self.debug.error_message("Exception in parseWinlinkXml: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


