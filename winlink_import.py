from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import os
import platform
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

  def __init__(self, debug, form_gui):  
    self.debug = debug
    self.conversion_file_dictionary_data = {}
    self.winlink_outbox_folder_files = []
    self.winlink_inbox_folder_files = []
    self.winlink_outbox_checked_for_export_data = []
    self.winlink_inbox_checked_for_export_data = []
    self.form_gui = form_gui

    self.testCreateWinlinkXlateFiles()
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


  """ this method replaces the prior method and uses a more generic conversion file for xlate"""
  def parseWinlinkXmlConvString(self, xml_string):

    try:
      self.debug.info_message("parseWinlinkXml")
      self.debug.info_message("parseWinlinkXml xml string: " + xml_string)

      myroot = ET.fromstring(xml_string)

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

        conversion_string = self.dictionary.getHRRMWinlinkConvString(formname)

        form_content = []
        conv_list = conversion_string.split(',')
        for item in conv_list:
          form_content.append(x.find(str(item)).text)
 
        msgto         = x.find('msgto').text
        sender        = x.find('msgsender').text
        subjectline   = x.find('subjectline').text

        self.debug.info_message("parseWinlinkXml sender: " + str(sender) )
        self.debug.info_message("parseWinlinkXml message_text: " + str(message_text) )


      self.debug.info_message("parseWinlinkXml incident name: " + str(incident_name) )
      self.debug.info_message("parseWinlinkXml to name: " + str(to_name) )
      self.debug.info_message("parseWinlinkXml from name: " + str(from_name) )
      self.debug.info_message("parseWinlinkXml subject: " + str(subjectline) )

      return form_type + ' ' + form_name, form_content, msgto, subjectline

    except:
      self.debug.error_message("Exception in parseWinlinkXml: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


  def generateWinlinkParamFile(self, hrrm_content, form):

    self.debug.info_message("generateWinlinkParamFile")

    self.conversion_file_additional_params = { 'txtStr'          : 'test1',
                                               'FormTitle'       : 'test2',
                                               'Templateversion' : 'test3',
                                               'From'            : 'WH6ABC',
                                               'To'              : 'WH6DEF',
                                               'cc'              : '',
                                               'P2P'             : 'N',
                                               'Subject'         : 'Test Subject'}
   


    """extract all the variables from the file in sequence """
    try:

      the_vars = []

      before_split = self.conversion_file_dictionary_data.get(form)

      self.debug.info_message("returned data is :" + str(before_split) )

      """ test to see if this can be converted """
      if(before_split == None):
        return None

      full_conversion_string = before_split.split(',')

      self.debug.info_message("conversion string is :" + str(full_conversion_string) )

      winlink_filename = full_conversion_string[0]
      winlink_folder_templates  = self.form_gui.window['input_general_pattemplatesfolder'].get().strip()

      winlink_file = open(winlink_folder_templates + winlink_filename,'r')
      lines = winlink_file.readlines()
      for line in lines:
        if '<var ' in line:      
          data = line.split('<var ')
          for count in range(1,len(data)):  
            var = data[count].split('>')[0]
            the_vars.append(str(var))
            self.debug.info_message("var is :" + str(var) )

      with open('parameters_file.txt','w') as param_file:

        for count in range(0, len(the_vars)):
          index = self.getHRRMWinlinkConvIndexForParam(form, the_vars[count])
          if(index != -1):
            the_vars.append(str(var))
            self.conversion_file_additional_params[the_vars[count]] = hrrm_content[index]

        sequence_string = self.winlink_sequence_data.get(form).split(',')
        for count in range(0, len(sequence_string)):
          lookup_var = self.conversion_file_additional_params.get(sequence_string[count])
          param_file.write(lookup_var + '\n')
          self.debug.info_message("var is :" + str(sequence_string[count]) )
          self.debug.info_message("lookup value is :" + str(lookup_var) )

      template_file = self.conversion_file_dictionary_data.get(form).split(',')[0]
      self.debug.info_message("template file is :" + str(template_file) )

      return winlink_filename

    except:
      self.debug.error_message("Exception in generateWinlinkParamFile: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


  """
  Conversion lookups for HRRM to winlink
  """
  def readHRRMWinlinkConvFile(self, filename):

    self.conversion_file_dictionary_data = {}


    winlink_file = open(filename,'r')
    lines = winlink_file.readlines()
    for line in lines:
      form_data = ''
      split_string = line.split(' ', 1)
      formname = split_string[0]

      if (platform.system() == 'Windows'):
        form_data = split_string[1].replace('+', '\\')
      else:
        form_data = split_string[1].replace('+', '/')

      self.conversion_file_dictionary_data[formname] = form_data

    self.debug.info_message("read conversion data : " + str(self.conversion_file_dictionary_data) )

    return


  def writeHRRMWinlinkConvToFile(self, filename):

    self.debug.info_message("writeHRRMWinlinkConvToFile")
   
    #self.conversion_file_dictionary_data = { 'ICS213'  :  'Standard_Forms+ICS USA Forms+ICS213.txt,inc_name,To_Name,fm_name,Subjectline,Mdate,mtime,Message,Approved_Name,Approved_PosTitle',
    #                                         'ICS205'  :  'Standard_Forms+ICS USA Forms+ICS205-10 Row.txt,inc_name,to_name,fm_name,subjectline,mdate,mtime,message,approved_name,approved_postitle'}
    #self.conversion_file_dictionary_data = { 'ICS213'  :  'ICS USA Forms+ICS213.txt,inc_name,To_Name,fm_name,Subjectline,Mdate,mtime,Message,Approved_Name,Approved_PosTitle',
    #                                         'ICS205'  :  'ICS USA Forms+ICS205-10 Row.txt,inc_name,to_name,fm_name,subjectline,mdate,mtime,message,approved_name,approved_postitle'}

    self.conversion_file_dictionary_data = { 'ICS213'  :  'ICS USA Forms+ICS213.txt,inc_name,To_Name,fm_name,Subjectline,Mdate,mtime,Message,Approved_Name,Approved_PosTitle'}

    with open(filename, 'w') as convert_file:
      for key in self.conversion_file_dictionary_data:
        the_data = self.conversion_file_dictionary_data.get(key)
        line_to_write = str(key) + ' ' + str(the_data) + '\n'
        convert_file.write(line_to_write)
        self.debug.info_message("writing line: " + line_to_write )

    return


  def readHRRMWinlinkSeqFile(self, filename):

    self.winlink_sequence_data = {}

    winlink_file = open(filename,'r')
    lines = winlink_file.readlines()
    for line in lines:
      split_string = line.split(' ', 1)
      formname = split_string[0]
      form_data = split_string[1] 
      self.winlink_sequence_data[formname] = form_data

    self.debug.info_message("read sequence data : " + str(self.winlink_sequence_data) )

    return

  def writeHRRMWinlinkSeqToFile(self, filename):

    """ question sequence for the forms"""
    self.winlink_sequence_data = { 'ICS213'  :  'From,To,cc,P2P,Subjectline,inc_name,Mdate,mtime,FormTitle,To_Name,fm_name,Message,Approved_Name,Approved_PosTitle'}

    with open('HRRM_Winlink_Sequence.txt', 'w') as convert_file:
      for key in self.winlink_sequence_data:
        line_to_write = str(key) + ' ' + str(self.winlink_sequence_data.get(key)) + '\n'
        convert_file.write(line_to_write)
        self.debug.info_message("writing line: " + line_to_write )

    return


  def noteExistingWinlinkFiles(self, saamfram):

    try:
      self.debug.info_message("noteExistingWinlinkFiles" )
      directory = saamfram.main_params.get("params").get('WinlinkOutboxFolder')
      if(directory != ''):
        self.winlink_outbox_folder_files = os.listdir(directory)
        self.debug.info_message("existing wilink outbox files :" + str(self.winlink_outbox_folder_files) )
      directory = saamfram.main_params.get("params").get('WinlinkInboxFolder')
      if(directory != ''):
        self.winlink_inbox_folder_files = os.listdir(directory)
        self.debug.info_message("existing wilink inbox files :" + str(self.winlink_inbox_folder_files) )

    except:
      self.debug.error_message("Exception in noteExistingWinlinkFiles: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


  def getWinlinkBinary(self):

    winlink_binary  = 'pat'

    checked = self.form_gui.window['cb_general_patbinaryoverride'].get()
    if(checked):
      winlink_binary  = self.form_gui.window['input_general_patbinary'].get().strip()
      
    return winlink_binary


  """ convert specific forms from HRRM"""
  def post_HRRM_to_pat_winlink(self, header_info, actual_data, saamfram, fragtagmsg, text_format):

    """ Header info as follows...
        ID        = data[1]
        msgto     = data[2]
        priority  = data[3]
        fragsize  = data[4]
        subject   = data[5]
        formname  = data[6]
        version   = data[7]
    """

    """ use export format to build form from HRRM"""

    try:
      directory = saamfram.main_params.get("params").get('WinlinkOutboxFolder')

      self.debug.info_message("directory is:" + str(directory))

      if(directory == ''):
        self.debug.info_message("directory not specified aborting")
        return

      dir_before = os.listdir(directory)

      self.debug.info_message("directory before is:" + str(dir_before))

      winlink_binary = self.getWinlinkBinary()
      if (platform.system() == 'Windows'):
        templates_folder = self.form_gui.window['input_general_pattemplatesfolder'].get().strip()
        exe_string = winlink_binary + ' composeform --template \"ICS213 General Message.txt\" <fixed_params_file.txt'
        self.debug.info_message("string is :- " + str(exe_string))
        os.system(exe_string)
      else:
        os.system(winlink_binary + ' composeform --template \'ICS213 General Message.txt\' <fixed_params_file.txt')



      #os.system('/home/pi/patvar2/pat/pat composeform --template \'ICS USA Forms/ICS213.txt\' <fixed_params_file.txt')
      dir_after = os.listdir(directory)

      self.debug.info_message("directory after is:" + str(dir_after))

      set_1 = set(dir_before)
      set_2 = set(dir_after)
      set_3 = set_1.union(set_2) - set_1.intersection(set_2)

      self.debug.info_message("added file is:" + str(set_3))

      new_item_name = list(set_3)[0]
      new_item = directory + list(set_3)[0]

      self.debug.info_message("added file is:" + str(new_item))


      self.debug.info_message("post_HRRM_to_pat_winlink LOC 1")

      text_table = text_format
      text = ''
      for x in range(len(text_table)):
        text = text + text_table[x][0] + '\n'

      self.debug.info_message("post_HRRM_to_pat_winlink LOC 2")

      #self.debug.info_message("Exception:" + str(header_info))

      the_message      = text

      """ remove any existing export data as do not want nested export data"""
      if("HRRM_EXPORT" in the_message):
        self.debug.info_message("Found HRRM_EXPORT string in message content...removing")
        new_content = the_message.split("HRRM_EXPORT")
        the_message = new_content[0]

      self.debug.info_message("post_HRRM_to_pat_winlink LOC 3")
      self.debug.info_message("header info 0:- " + str(header_info[0]))
      self.debug.info_message("header info 1:- " + str(header_info[1]))
      self.debug.info_message("header info 2:- " + str(header_info[2]))



      complete_message = the_message + '\n\n\n\n\n' + 'HRRM_EXPORT = ' + fragtagmsg + '\n\n'
      #the_datetime     = saamfram.getDecodeTimestampAltFromUniqueId(header_info[1])
      the_datetime     = saamfram.getDecodeTimestampAltFromUniqueId(header_info[0])
      self.debug.info_message("post_HRRM_to_pat_winlink LOC 3a")
      #from_call        = saamfram.getDecodeCallsignFromUniqueId(header_info[1])
      from_call        = saamfram.getDecodeCallsignFromUniqueId(header_info[0])
      self.debug.info_message("post_HRRM_to_pat_winlink LOC 3b")
      #to_call          = header_info[2].replace('+', '@')
      to_call          = header_info[1].replace('+', '@')
      #the_subject      = header_info[5]
      the_subject      = header_info[4]

      self.debug.info_message("post_HRRM_to_pat_winlink LOC 3c")

      newline_count = 0
      if (platform.system() == 'Windows'):
        newline_count = complete_message.count('\n') 
      else:
        newline_count = 0

      self.debug.info_message("post_HRRM_to_pat_winlink LOC 4")

      with open(new_item, 'w') as new_file:
        #line_to_write = 'Mid: ' + new_item_name.strip('.b2f') + '\n'
        line_to_write = 'Mid: ' + new_item_name[:-4] + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Body: ' + str(len(complete_message)+ newline_count) + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Content-Transfer-Encoding: 8bit' + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Content-Type: text/plain; charset=ISO-8859-1' + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Date: ' + the_datetime + '\n'
        new_file.write(line_to_write)
        line_to_write = 'From: ' + from_call + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Mbo: ' + from_call + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Subject: ' + the_subject + '\n'
        new_file.write(line_to_write)
        line_to_write = 'To: ' + to_call + '\n'
        new_file.write(line_to_write)
        line_to_write = 'Type: Private' + '\n' + '\n'
        new_file.write(line_to_write)
        line_to_write = complete_message 
        new_file.write(line_to_write)

      self.debug.info_message("post_HRRM_to_pat_winlink LOC 5")

    except:
      self.debug.error_message("Exception in post_HRRM_to_pat_winlink: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))


    return


  def checkFilesForImportData(self, saamfram):
    self.debug.info_message("checkFilesForImportData")

    """ only process HRRM_EXPORT if it is in the winlink inbox """

    """
    directory = saamfram.main_params.get("params").get('WinlinkOutboxFolder')
    dir_outbox = os.listdir(directory)

    set_1 = set(self.winlink_outbox_folder_files)
    set_2 = set(dir_outbox)
    set_3 = set_1.union(set_2) - set_1.intersection(set_2)

    for item in list(set_3):
      if(item not in self.winlink_outbox_checked_for_export_data):
        winlink_file = open(directory + item,'r')
        lines = winlink_file.readlines()
        have_import = False
        line_data = ''
        for line in lines:
          if 'HRRM_EXPORT = ' in line:      
            have_import = True
          if (have_import == True):
            line_data = line_data + line.strip('HRRM_EXPORT = ')
        if(have_import == True):
          self.debug.info_message("found import string: " + str(line_data))
          saamfram.processIncomingMessage(str(line_data))
        self.winlink_outbox_checked_for_export_data.append(item)

    """
    try:
      directory = saamfram.main_params.get("params").get('WinlinkInboxFolder')
      dir_inbox = os.listdir(directory)

      set_1 = set(self.winlink_inbox_folder_files)
      set_2 = set(dir_inbox)
      set_3 = set_1.union(set_2) - set_1.intersection(set_2)

      for item in list(set_3):
        if(item not in self.winlink_inbox_checked_for_export_data):
          winlink_file = open(directory + item,'r')
          lines = winlink_file.readlines()
          have_import = False
          line_data = ''
          for line in lines:
            if 'HRRM_EXPORT = ' in line:      
              have_import = True
            if (have_import == True):
              line_data = line_data + line.strip('HRRM_EXPORT = ')
          if(have_import == True):
            self.debug.info_message("found import string: " + str(line_data))
            saamfram.processIncomingMessage(str(line_data))
          self.winlink_inbox_checked_for_export_data.append(item)

    except:
      self.debug.error_message("Exception in checkFilesForImportData: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return

  def winlinkConnect(self, callsign, override, connect_mode):
    self.debug.info_message("winlinkConnect")

    try:
      pat_binary = self.getWinlinkBinary()

      if(connect_mode == 'telnet'):
        self.debug.info_message(pat_binary + ' connect ' + connect_mode)
        os.system(pat_binary + ' connect ' + connect_mode)
      else:
        self.debug.info_message(pat_binary + ' connect ' + connect_mode + ':///' + callsign)
        os.system(pat_binary + ' connect ' + connect_mode + ':///' + callsign)
    except:
      self.debug.error_message("Exception in winlinkConnect: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))

    return


  def getHRRMWinlinkConvIndexForParam(self, form, parameter):

    full_conversion_string = self.conversion_file_dictionary_data.get(form).split(',')

    for count in range (1,len(full_conversion_string)):
      if(full_conversion_string[count] == parameter):
        return count-1

    return -1


  def getHRRMWinlinkConvParamForIndex(self, index):
    param = 'name'

    return param

  def getHRRMWinlinkConvString(self, formname):

    return self.conversion_file_dictionary_data[formname]



  def testCreateWinlinkXlateFiles(self):
    self.debug.info_message("testCreateWinlinkXlateFiles")

    #with open('parameters_file.txt','w') as param_file:

    try:
      self.readHRRMWinlinkConvFile('HRRM_Winlink_Conversion.txt')
    except:
      self.debug.error_message("Exception in testCreateWinlinkXlateFiles: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
      self.debug.info_message("creating winlink conversion file" )
      self.writeHRRMWinlinkConvToFile('HRRM_Winlink_Conversion.txt')

  
    try:
      self.readHRRMWinlinkSeqFile('HRRM_Winlink_Sequence.txt')
    except:
      self.debug.info_message("creating winlink sequence file" )
      self.writeHRRMWinlinkSeqToFile('HRRM_Winlink_Sequence.txt')


    try:
      with open('fixed_params_file.txt', 'r') as f:
        data = f.read()
      self.debug.info_message("fixed_params_file.txt exists" )
    except:
      self.debug.info_message("exception reading fixed params file" )

      with open('fixed_params_file.txt', 'w') as new_file:
        line_to_write = 'WH6ABC\n'
        new_file.write(line_to_write)
        line_to_write = 'WH6DEF\n'
        new_file.write(line_to_write)
        line_to_write = '\n'
        new_file.write(line_to_write)
        line_to_write = 'N\n'
        new_file.write(line_to_write)
        line_to_write = 'Subject\n'
        new_file.write(line_to_write)
        line_to_write = 'incident name\n'
        new_file.write(line_to_write)
        line_to_write = '2023//11//27\n'
        new_file.write(line_to_write)
        line_to_write = '00:23\n'
        new_file.write(line_to_write)
        line_to_write = 'test2\n'
        new_file.write(line_to_write)
        line_to_write = 'To\n'
        new_file.write(line_to_write)
        line_to_write = 'From\n'
        new_file.write(line_to_write)
        line_to_write = 'Hi there this is a message\n'
        new_file.write(line_to_write)
        line_to_write = 'Approved By\n'
        new_file.write(line_to_write)
        line_to_write = 'Person Title\n'
        new_file.write(line_to_write)

    return


