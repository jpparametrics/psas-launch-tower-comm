#!/usr/bin/python

"""Rocket Commander - LTC side
Runs on the LTC and relays power commands to the rocket.

Starts a Phidgets Dictionary that receives KeyChange events from the
Phidgets Webservice and reacts by sending tty commands to the rocket.

It then changes the command keys back to their nuetral state as a
acknowledgement signal.

Uses code from the Phidget example `Dictionary-simple.py` version 2.1.8,
by Adam Stelmack.
"""

__author__ = 'John Boyle'
__version__ = '0.0.314'
__date__ = 'June 2013'


#Basic imports
from ctypes import *
import sys, subprocess
from time import sleep

#Phidget specific imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import ErrorEventArgs, KeyChangeEventArgs, ServerConnectArgs, ServerDisconnectArgs
from Phidgets.Dictionary import Dictionary, DictionaryKeyChangeReason, KeyListener

IP = "localhost"
cdict = dict()

###################
# commander setup #
###################

def capture_commands(e):
    key = e.key
    if '_on' in key or '_off' in key or 'LATCH' == key:
        cdict[key] = e.value


##################
# Phidgets setup #
##################

#Create a Dictionary object and a key listener object
try:
    dictionary = Dictionary()
    keyListener = KeyListener(dictionary, "\/*")
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)

#Event Handler Callback Functions
def DictionaryError(e):
    print("Dictionary Error %i: %s" % (e.eCode, e.description))
    return 0

def DictionaryServerConnected(e):
    print("Dictionary connected to server %s" % (e.device.getServerAddress()))
    try:
        keyListener.start()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
    return 0

def DictionaryServerDisconnected(e):
    print("Dictionary disconnected from server")
    try:
        keyListener.stop()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
    return 0

def KeyChanged(e):
    if e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_VALUE_CHANGED:
        reason = "Value Changed"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_ENTRY_ADDED:
        reason = "Entry Added"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_ENTRY_REMOVING:
        reason = "Entry Removed"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_CURRENT_VALUE:
        reason = "Current Value"

    if 'Heartbeat' not in e.key:
        print("%s -- Key: %s -- Value: %s" % (reason, e.key, e.value))

    capture_commands(e)
    return 0

def KeyRemoved(e):
    if e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_VALUE_CHANGED:
        reason = "Value Changed"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_ENTRY_ADDED:
        reason = "Entry Added"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_ENTRY_REMOVING:
        reason = "Entry Removed"
    elif e.reason == DictionaryKeyChangeReason.PHIDGET_DICTIONARY_CURRENT_VALUE:
        reason = "Current Value"

    if 'Heartbeat' not in e.key:
        print("%s -- Key: %s -- Value: %s" % (reason, e.key, e.value))

    capture_commands(e)
    return 0

####################
#   Main Program   #
####################

try:
    dictionary.setErrorHandler(DictionaryError)
    dictionary.setServerConnectHandler(DictionaryServerConnected)
    dictionary.setServerDisconnectHandler(DictionaryServerDisconnected)

    keyListener.setKeyChangeHandler(KeyChanged)
    keyListener.setKeyRemovalListener(KeyRemoved)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Opening Dictionary object....")

try:
    dictionary.openRemoteIP(IP, 5001)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

try:
    while dictionary.isAttachedToServer() == False:
        pass
    else:
        print("Connected: %s" % (dictionary.isAttachedToServer()))
        print("Server: %s:%s" % (dictionary.getServerAddress(), dictionary.getServerPort()))
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)


#############
# Main Loop #
#############
ORDERS = ['v360_on', 'v360_off', 'atv_on', 'atv_off', 'fc_on', 'fc_off',
          'rr_on', 'rr_off', 'wifi_on', 'wifi_off']

for order in ORDERS:
    cdict[order] = 'INITIALIZED'
    dictionary.addKey(order, 'INITIALIZED')

cdict['LATCH'] = 'INITIALIZED'
cdict['STATUS'] = 'INITIALIZED'

while(True):
    sleep(1)
    #~ print cdict.keys()
    #~ print '--------'
    #~ print cdict.values()

    for command in ORDERS:
        if cdict[command] == 'PLEASE':
            if cdict['LATCH'] == 'SET':
                try:
                    shell_command = command
                    results = subprocess.Popen(shell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    results = results.communicate()
                    if results[1]:
                        print "Error: {}".format(results[1])
                        dictionary.addKey('LATCH', 'UNSET')
                        dictionary.addKey('STATUS', 'ERROR, TRY AGAIN')
                        dictionary.addKey(command, 'ERROR')
                    else:
			results_msg = 'Yes' if not results[0] else results[0]
			print "Message: ", results_msg
                        print "Message Sent: %s" % results_msg
                        dictionary.addKey('LATCH', 'UNSET')
                        dictionary.addKey('STATUS', 'MESSAGE SENT')
                        dictionary.addKey(command, 'ready')
                        sleep(3)
                        dictionary.addKey('STATUS', 'READY')

                except PhidgetException as e:
                    print("Phidget Exception %i: %s" % (e.code, e.details))
            else:
                print "Incorrect command sequence"
                dictionary.addKey(command, 'I need latch')
                dictionary.addKey('STATUS', 'ENABLE LATCH')


# Graceful exit
print("Closing...")

try:
    keyListener.stop()
    dictionary.closeDictionary()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Done.")
exit(0)
