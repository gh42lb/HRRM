import logging
import sys
import asyncio
import threading
import traceback
import random
import json
import constant as cn
import debug as db
import ipaddress

from crc import Calculator, Configuration
from datetime import datetime, timedelta
from getmac import get_mac_address
from collections import OrderedDict
import time
import uuid

class SaamframCoreUtils(object):

  debug = db.Debug(cn.DEBUG_INFO)
  base32_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
  delimiter_char = cn.DELIMETER_CHAR

  def getDecodeEscapes(self, message):

    self.debug.info_message("getDecodeEscapes")

    string_out = ''
    char_count = 0
    message_len = len(message)
    while char_count < message_len:
      if(char_count+1 < message_len):
        if(message[char_count] == '/'):
          """ test to see if this is an escape sequence"""
          if(message[char_count+1] == 'D'):
            string_out = string_out + '}'
            char_count = char_count + 2
          elif(message[char_count+1] == 'C'):
            string_out = string_out + '{'
            char_count = char_count + 2
          elif(message[char_count+1] == 'B'):
            string_out = string_out + ']'
            char_count = char_count + 2
          elif(message[char_count+1] == 'A'):
            string_out = string_out + '['
            char_count = char_count + 2
          elif(message[char_count+1] == 'N'):
            if (platform.system() == 'Windows'):
              string_out = string_out + '\r\n'
            else:
              string_out = string_out + '\n'
            char_count = char_count + 2
          elif(message[char_count+1] == '/'):
            string_out = string_out + '/'
            char_count = char_count + 2
          else:
            """ make sure this is an RLE escape sequence """
            if(message[char_count+1].isdigit()):
              if(message[char_count+2].isdigit()):
                if(message[char_count+3].isdigit()):
                  """ four digit RLE codes and up not supported"""
                  if(message[char_count+4].isdigit()):
                    self.debug.info_message("do nothing")
                  elif(message[char_count+4] == cn.DELIMETER_CHAR):
                    """ process triple digit RLE code"""
                    string_out = string_out + (cn.DELIMETER_CHAR * ((int(message[char_count+1])*100) + (int(message[char_count+2])*10)+ (int(message[char_count+3]))) )
                    char_count = char_count + 5

                elif(message[char_count+3] == cn.DELIMETER_CHAR):
                  """ process double digit RLE code"""
                  string_out = string_out + (cn.DELIMETER_CHAR * ((int(message[char_count+1])*10) + (int(message[char_count+2]))) )
                  char_count = char_count + 4

              elif(message[char_count+2] == cn.DELIMETER_CHAR):
                """ process single digit RLE code"""
                string_out = string_out + (cn.DELIMETER_CHAR * int(message[char_count+1]) )
                char_count = char_count + 3
            else:
              string_out = string_out + message[char_count]
              char_count = char_count + 1

        else:
          string_out = string_out + message[char_count]
          char_count = char_count + 1
      else:
        string_out = string_out + message[char_count]
        char_count = char_count + 1

    message = string_out
    self.debug.info_message("completed getDecodeEscapes. unescaped message: " + str(message) )

    return message

  """ This method decodes the int time from the ID string"""
  def getDecodeIntTimeFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""
    timestamp_string = ID.split('_',1)[1]
    inttime = ((int(timestamp_string,36))/100.0)

    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )
                                                                                        
    return inttime

  """ This method decodes the timestamp from the ID string"""
  def getDecodeTimestampFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
    charsLen = len(chars)

    if '_' in ID:
      timestamp_string = ID.split('_',1)[1]
    elif '#' in ID:
      timestamp_string = ID.split('#',1)[1]

    inttime = ((int(timestamp_string,36))/100.0)
    self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )
    timestamp = str(datetime.utcfromtimestamp(inttime) )

    self.debug.info_message("reverse encoded timestamp is: " + timestamp )
                                                                                        
    return timestamp

  """ This method decodes the callsign from the ID string"""
  def getDecodeCallsignFromUniqueId(self, ID):
    """ use the following to reverse the callsign from the ID string to show who created the email"""

    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
    charsLen = len(chars)

    if '_' in ID:
      hexnum = '0x' + ID.split('_',1)[0]
      timestamp_string = ID.split('_',1)[1]

      inttime = ((int(timestamp_string,36))/100.0)
      self.debug.info_message("datetime = " + str(datetime.utcfromtimestamp(inttime) ) )

      intnum = int(hexnum,16)
      callsign = ""
      while intnum:
        callsign = chars[intnum % charsLen] + callsign
        intnum //= charsLen
      return callsign
    elif '#' in ID:
      return ID.split('#',1)[0]


  def getEOMChecksum(self, mystr):
    return self.calcEOMCRC(mystr)

  """ always use a 20 bit / 4 digit CRC for end of message checksum"""
  def calcEOMCRC(self, string):
    return self.calcFourDigitCRC(string)

  """
  CRC calculation uses 5 bit nibbles in base 32 so four digits is 20 bits
  0xc1acf polynomial protects up to 524267 bit data word (65533 x 8 bit characters) length at HD=4
  this is used for end of message checksum for messages > 2046 characters
  """
  def calcFourDigitCRC(self, string):
    return self.calcCRC(20, 0xc1acf, string)

  def calcCRC(self, width, poly, string):

    self.debug.info_message('calcCRC')

    data = bytes(string,"ascii")

    init_value=0x00
    final_xor_value=0x00
    reverse_input=False
    reverse_output=False

    configuration = Configuration(width, poly, init_value, final_xor_value, reverse_input, reverse_output)

    use_table = True
    crc_calculator = Calculator(configuration, use_table)

    checksum = crc_calculator.checksum(data)
    self.debug.info_message(str(checksum))

    if(width == 10):
      high, low = checksum >> 5, checksum & 0x1F
      self.debug.info_message('10 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[low]
    elif(width == 15):
      high, mid, low = checksum >> 10, (checksum >> 5) & 0x1F, checksum & 0x1F
      self.debug.info_message('15 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[mid] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[mid] + self.base32_chars[low]
    elif(width == 20):
      high, mid_high, mid_low, low = checksum >> 15, (checksum >> 10) & 0x1F, (checksum >> 5) & 0x1F, checksum & 0x1F
      self.debug.info_message('20 bit checksum: ' + str(self.base32_chars[high] + self.base32_chars[mid_high] + self.base32_chars[mid_low] + self.base32_chars[low]))
      return self.base32_chars[high] + self.base32_chars[mid_high] + self.base32_chars[mid_low] + self.base32_chars[low]

    return ''


  def deconstructFragmentedMessage(self, remainder):

        content   = []
        split_string = remainder.split('{'  + cn.FORMAT_CONTENT + self.delimiter_char, 1)
        data_and_remainder = split_string[1].split('}', 1)

        rleDecodedString = self.getDecodeEscapes(data_and_remainder[0])

        """ only process the content for escapes"""
        data = rleDecodedString.split(self.delimiter_char)

        for x in range(len(data)):
          self.debug.info_message( cn.FORMAT_CONTENT + ": data[x] is: " + data[x] )
        remainder = data_and_remainder[1]

        ID        = data[0]
        msgto     = data[1]
        priority  = data[2]
        fragsize  = data[3]
        subject   = data[4]
        formname  = data[5]
        version   = data[6]

        timestamp = self.getDecodeIntTimeFromUniqueId(ID)
        msgfrom   = self.getDecodeCallsignFromUniqueId(ID)

        return ID, msgto, priority, timestamp, msgfrom


  def deconstructFragTagMsg(self, fragtagmsg):

    reconstruct = ''

    completed = False
    remainder = fragtagmsg
    while completed == False:
      split_string = remainder.split('[F', 1)
      numbers_and_remainder = split_string[1].split(']', 1)
      numbers = numbers_and_remainder[0].split(',', 1)
      part_number = numbers[0]
      parts_total = numbers[1]
      remainder = numbers_and_remainder[1]
      self.debug.info_message("part number and total: " + part_number + "," + parts_total )

      if(part_number == parts_total):
        completed = True
        
      """ deconstruct message text """
      split_string = remainder.split('[', 1)
      checksum_and_remainder = split_string[1].split(']', 1)
      message_text = split_string[0]
      reconstruct = reconstruct + message_text
      message_checksum = checksum_and_remainder[0]
      remainder = checksum_and_remainder[1]
      self.debug.info_message("message text: " + message_text )
      self.debug.info_message("message checksum: " + message_checksum )

      if(remainder == '' ):
        completed = True

    self.debug.info_message("reconstructed string: " + reconstruct )

    """ pull the 4 digit checksum off the end of the completed string. """
    EOM_checksum = reconstruct[-4:]
    reconstruct  = reconstruct[:-4]

    try:
      self.debug.info_message("reconstructed string 2: " + reconstruct )
      self.debug.info_message("EOM checksum 1 is: " + str(EOM_checksum.upper() ) )
      self.debug.info_message("EOM checksum 2 is: " + str(self.getEOMChecksum(reconstruct).upper()) )
    except:
      self.debug.error_message("Exception in deconstructFragTagMsgFldigi: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ))
 
    if(EOM_checksum.upper() == self.getEOMChecksum(reconstruct).upper() ):
      return True, reconstruct
    else:
      return False, reconstruct

    return True, reconstruct



  def isIpRoutable(self, ip):
    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
      return False
    else:
      return True
