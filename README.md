## Overview

Ham Radio Relay Messenger v2.0.5 alpha release de WH6GGO. The software is currently in active development and early release testing phase.


#### Features
* Distributed Peer To Peer IP Layer: v2.0.5 includes a distributed peer to peer ip layer for decentralized IP communications via satellite and terrestrial internet.
* Support for JS8: Send messages, email, forms and ICS forms via JS8 and JS8call
* Dynamic Routing: Builds routing information from active relay stations. Relay messages directed to stations with fewest hops.
* Self Organizing Radio Mesh: HRRM allows active stations to form a Dynamic Self Organizing Radio Mesh for message transfer either directly or via relay.
* Critical Messages: Enables transfer of fully verified, error-corrected chats/emails/forms/files/messages to ham radio stations in real time.
* File Transfer: Capable of sending files and images.
* Winlink over fldigi: Capable of sending Winlink message files directly from winlink outbox of sending station to winlink inbox of receiving station(s).
* Cross Platfrom: HRRM is confirmed to work well on both the raspberry pi and the Windows Beelink mini computing platform, both of which are ideal for off-grid and/or mobile setups.
* Group Communication: Capable of real time Peer to Peer, Peer to Group mode communications with group mode ARQ.
* Resilience: Optimized data transfer protocol for increased performance and resilience to adverse band conditions.
* Integration: Integrates with Fldigi, Winlink and Pat Winlink applications.
* Cross-Platform: Runs on Windows, Linux and any other platform supporting python + related libraries.
* Flexibility: Multiple message delivery techniques including push, pull, store and forward, relay, active session, passive mode.
* Mesh Node: Ad-hoc mesh node functionality provided out-of-the-box, including: relay, hub, gateway, RX or TX end node,
* Notifications: Stub messages provide notification to the group of any pending messages waiting to be sent.
* Data Compression: Uses a variety of data compression techniques inluding dictionary compression and run length encoding.
* Customized Interface: Email style interface with inbox, outbox, relay box and sent box, utilizing notebook style and customized GUI controls.
* 44 Modulation Modes: Supports a wide variety of underlying modulations including OFDM, MT63, THOR, MFSK, PSK, QPSK, BPSK, DominoEX, 8PSK and Olivia.
* Extendable: Form designer built-in with many pre-built ICS form templates and standard templates included.


## Quick Start Guide

### Required Software

Download the following:

* JS8Call
* Fldigi
* HRRM v2.0.5 binary or HRRM_setup windows installer: github.com/gh42lb/HRRM
* p2pnode binary from github.com/gh42lb/HRRM

run the windows installer or create a folder on the desktop called HRRM and add the binary file

### Configuration

Fldigi XmlRpc: HRRM requires fldigi XmlRpc. This is usually configured by default in fldigi. If you are having issues connecting, check Fldigi XmlRpc external api is enabled and the ip and port are set to 127.0.0.1 and 7362 respectively. If you wish to use a different fldigi XmlRpc port or ip this can be specified using the fldigi=<IP>:<port> command line optionin HRRM as follows:   .\hrrm.exe fldigi=127.0.0.1:7362

Fldigi Soundcard: In fldigi, Configure / Soundcard / Devices. Check the sound card device settings in fldigi and ensure they are set correctly for your soundcard / radio

Fldigi RsID: In fldigi, Configure / IDs / RsID. Uncheck 'Retain tx freq lock'. Check 'Searches passband'

Fldigi Operator: in fldigi, Configure / Misc / Operator Station. Set 'Station Callsign' and 'Operator Callsign'

HRRM Callsign: In HRRM, 'MyInfo' tab / Callsign. Enter your callsign

HRRM Group Name: In HRRM, 'MyInfo' tab / Group Name. Enter the chosen group name (must have a preceeding @ character) that you will be communicating with. You can leave this at the default '@HRRM'

HRRM Grid Square: in HRRM, 'MyInfo' tab / Grid Square. Enter you grid square into the field.

JS8Call 
File/Settings/Reporting tab
under the API section:

TCP Server Hostname: 127.0.0.1   Enable TCP Server API - checked

TCP Server Port:     2442        Accept TCP Requests   - checked

TCP Max Connections: 1 or 2

on pi\linux, copy the hrrm.key and hrrm.crt files to the ~/.HRRM folder

### Running the Application

start the modem application first...this can be either js8call or fldigi

start the p2pnode application

Now start hrrm by running the exe\binary from the command line or double clicking on the icon on the desktop

if everything is installed correctly, hrrm will connect to fldigi and display the main window.



### Calling CQ

Click the 'CQ CQ' button to call CQ.

A station that hears the CQ can click 'Copy' to reply back.

The 'Connect To:' field is the callsign of the station you are connecting to. If blank, enter the callsign for the station you wish to connect to.

The receiving station should also enter your callsign into the same field on their application if it is blank.

Click the chat tab and type some text and hit send.




enjoy :)

73 de WH6GGO


## Copyright/License

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


