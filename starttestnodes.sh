#!/bin/bash


xterm -e "python3 ./p2pnode.py -i 127.0.0.1 -p 3000 -s 3001 --delay=5"  &
xterm -e "python3 ./p2pnode.py -i 127.0.0.1 -p 3000 -s 3002 --delay=5"  &
xterm -e "python3 ./p2pnode.py -i 127.0.0.1 -p 3000 -s 3003 --delay=5"  &

