# coding=utf-8
from socket import socket, AF_INET, SOCK_STREAM

import json
import time
import sys
import select
import constant as cn
import threading

import debug as db

from JSONPipe import JSONPipe

from app_pipes import AppPipes


try:
  import PySimpleGUI as sg
except:
  import PySimpleGUI27 as sg

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


class JSONPipeDemoCallback(object):

  pipe = None

  def __init__(self, ps):  
    self.pipe = ps

  """
  callback function used by processing thread
  """
  def json_callback(self, json_string, txrcv, rigname, js8riginstance):

    sys.stdout.write("IN SERVER CALLBACK\n")
    sys.stdout.write("DATA RECEIVED AT SERVER " + str(json_string) + "\n")

    sys.stdout.write("SENDING DATA FROM External Server to HRRM Client\n")

    if(self.pipe.pipe_type == cn.JSON_PIPE_SERVER):
      sys.stdout.write("SERVER PIPE\n")
      self.pipe.conn.sendall(b'{"type": "ABCDEFG_SPEED", "value": "", "params": {"SPEED": 22, "_ID": -1}}\n')
    elif(self.pipe.pipe_type == cn.JSON_PIPE_CLIENT):
      sys.stdout.write("CLIENT PIPE\n")
    elif(self.pipe.pipe_type == cn.JSON_PIPE_UNDEFINED):
      sys.stdout.write("UNDEFINED PIPE\n")

    return


class FormGui(object):


  """
  debug level 0=off, 1=info, 2=warning, 3=error
  """
  def __init__(self, group_arq, debug):  
    return

  """
  create the main GUI window
  """

  def createMainTabbedWindow(self, text, js):

    combo_server_or_client = 'Server Listen,Client Connect'.split(',')

    self.layout_substation = [
                          [sg.Text('Station Name: ', size=(11, 1) ) ,
                           sg.InputText('Yaesu HF Fldigi', key='in_substation_name_1', size=(15, 1)),
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='in_substation_ipaddress_1', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='in_substation_port_1', size=(15, 1)),
                           sg.Combo(combo_server_or_client, default_value=combo_server_or_client[1], size=(11, 1), key='option_substation_svrcli_1', enable_events=True) ,
                           sg.Button('Connect', size=(11, 1), key='btn_substation_connect_1'),
                           sg.Button('Dis-Connect', size=(11, 1), key='btn_substation_disconnect_1', disabled = True)],


                          [sg.CBox('Accept All Incoming Connection Requests', key='cb_inbox_autoresendrequest')],

                          [sg.Text('='*130, size=(130, 1) ) ],

                          [sg.Text('Digital Ham Radio Net: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.CBox('Auto Accept Connection', key='cb_inbox_autoresendrequest')],

                          [sg.Text('='*130, size=(130, 1) ) ],

                          [sg.Text('Pat Winlink Client: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.Text('Pat Winlink VARA: ', size=(20, 1) ) ,
                           sg.Text('IP Address: ', size=(11, 1) ) ,
                           sg.InputText('127.0.0.1', key='sidebar_offset', size=(15, 1)),
                           sg.Text('Port #: ', size=(11, 1) ) ,
                           sg.InputText('2555', key='sidebar_offset', size=(15, 1)),
                           sg.Button('Connect', size=(11, 1), key='btn_inbox_requestchecksums')],

                          [sg.CBox('Auto Accept Connection', key='cb_inbox_autoresendrequest')],

                        ] 



    self.tabgrp = [

                       [sg.Button('CQ CQ CQ', size=(9, 1), key='btn_compose_cqcqcq'),
                        sg.Button('Checking In', size=(9, 1), key='btn_compose_checkin'),
                        sg.Button('Standing By', size=(9, 1), key='btn_compose_standby'),
                        sg.Button('Going QRT', size=(9, 1), key='btn_compose_qrt'),
                        sg.Button('Relay', size=(9, 1), key='btn_compose_confirmedhavecopy'),
                        sg.Button('Ready to Rcv', size=(9, 1), key='btn_compose_readytoreceive', disabled = True),
                        sg.Button('Not Ready', size=(9, 1), key='btn_compose_notreadytoreceive', disabled = True),
                        sg.Button('Already Have', size=(9, 1), key='btn_compose_cancelalreadyhavecopy', disabled = True),
                        sg.Button('Abort', size=(9, 1), key='btn_compose_abortsend')],

                       [sg.TabGroup([[
                             sg.Tab('Sub-Station', self.layout_substation, title_color='Blue',border_width =10, background_color='Gray' )]],
                       tab_location='centertop',
                       title_color='Blue', tab_background_color='Dark Gray', background_color='Dark Gray', size=(940, 450), selected_title_color='Black', selected_background_color='White', key='tabgrp_main' )], [sg.Button('Exit')]]  

    self.window = sg.Window("Ham Radio Relay Messenger de WH6GGO. v1.0.0 Beta", self.tabgrp, default_element_size=(40, 1), grab_anywhere=False, disable_close=True)                       

    return (self.window)

  def runReceive(self, form, dispatcher):

    try:
      while True:
        event, values = self.window.read(timeout=100)
       
        try:
          dispatcher.dispatch[event](self.form_events, values)
        except:
          dispatcher.event_catchall(values)

        if event in ('Exit', None):
          break

      dispatcher.event_exit_receive(values)
      self.window.close()
    except:
      sys.stdout.write("Exception in runReceive: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")

    self.window.close()


class ReceiveControlsProc(object):
  
  def __init__(self):  
    return

  def event_catchall(self, values):
    return()

  def event_btntmpltpreviewform(self, values):
    sys.stdout.write("BTN NEW TEMPLATE\n")
    return()

  def event_exit_receive(self, values):

    try:
      sys.stdout.write("IN event_exit_receive\n")

    except:
      sys.stdout.write("Exception in runReceive: " + str(sys.exc_info()[0]) + str(sys.exc_info()[1] ) + "\n")
      
    return()




  dispatch = {
      'btn_tmplt_preview_form'    : event_btntmpltpreviewform,
  }




"""
JSONPipeDemo can be run as a stand alone program
"""

def main():

  debug = db.Debug(cn.DEBUG_INFO)
  name = 'mailbox_server'
  ip_address = '127.0.0.1'
  port = '2555'
  pipes = AppPipes(debug)
  pipe = pipes.createServerPipe(name, ip_address, port )
  pipes.connectServer(pipe)
  mycallbackServer = JSONPipeDemoCallback(pipe)
  pipe.setCallback(mycallbackServer.json_callback)

  """ create the main gui controls event handler """
  form_gui = FormGui(None, None)
  window = form_gui.createMainTabbedWindow('', None)
  dispatcher = ReceiveControlsProc()
  form_gui.runReceive(window, dispatcher)

  time.sleep(10)

  pipe.close()
  time.sleep(3)

  pipe.stopThreads()
  pipes.removePipe(name, ip_address, port )

  sys.stdout.write("end of test\n")


if __name__ == '__main__':
    main()




