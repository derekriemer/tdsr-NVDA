#!/bin/bash
#By default, we open up a server on localhost 64111
# Pass this file to tdsr with the -s option like so.
#tdsr -s server_sock.sh
#If you run this file on your own without tdsr, you should be able to execute it and type things like "sI'm talking"
#without the quotes and get NVDA or any compatable implementation to yield speech.
#The protocol is undocumented, but it is pretty simple.
#A cursory look at the code will explain it to you.
exec socat - TCP4:127.0.0.1:64111,nodelay