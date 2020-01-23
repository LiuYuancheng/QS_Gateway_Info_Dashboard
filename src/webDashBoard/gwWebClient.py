#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        gwWebClient.py
#
# Purpose:     This module will provide a UDP client to load the gateway local
#              log files and feed the parsed data to the server. 
#
# Author:      Yuancheng Liu
#
# Created:     2019/01/22
# Copyright:   
# License:     
#-----------------------------------------------------------------------------

import os
import sys
import time
import json
import socket
import random
import udpCom
import threading
from statistics import mean
from tcp_latency import measure_latency

# Set the constants.
TEST_MODE = True # test mode flag, set to False when deploy the client.
DATA_DIR = 'testData' if TEST_MODE else ''
SEV_IP = ('127.0.0.1', 5005) if TEST_MODE else ('10.0.0.1', 5005)
GW_CONFIG = os.path.join(DATA_DIR,'gwCliConfig.json')
GW_IN_JSON = os.path.join(DATA_DIR,'tp01_in_info.json')
GW_OUT_JSON = os.path.join(DATA_DIR,'tp01_out_info.json')
TLS_CM_JSON = os.path.join(DATA_DIR,'tls01_info.json')
KEY_EX_JSON = os.path.join(DATA_DIR,'key_ex_info.json')
LAT_PERIOD = 5      # latency periodic check time.
RPT_PERIOD = 2      # time period to insert the data to data base.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class gwWebClient(object):
    """ UDP client module."""
    def __init__(self, parent):
        """ Create a client to login to the server and submit the gateway log's data.
            init example: client = gwWebClient(None)
        """
        self.showConstant()
        self.gwClient = udpCom.udpClient(SEV_IP)
        self.latency = 0.0001
        self.terminate = False
        print("load the configure file and login.")
        self.dataDist = None
        with open(GW_CONFIG, "r") as fh:
            self.dataDist = json.loads(fh.readlines()[-1].rstrip()) # load the last line of the json.
        lat, lon = self.dataDist['GPS'].split(',')
        loginStr = ";".join(('L', self.dataDist['gatewayID'], lat, lon))
        print("send the login message: <%s>" %str(loginStr))
        resp = self.gwClient.sendMsg(loginStr, resp=True)
        if resp.decode('utf-8') == 'R;L':
            print('Login the server as a new gateway.')
        else:
            print('Server replay: %s' %str(resp))
        latThread = threading.Thread(target=self.checkLatency) # Not work: threading.Thread(target=self.checkLatency()) 
        latThread.daemon = True # here need to use method referring instead of invoking.  
        latThread.start()       # https://stackoverflow.com/questions/30701983/new-thread-blocks-main-thread

#-----------------------------------------------------------------------------
    def showConstant(self):
        """ Show all the configured constants. """
        print("Execution constants : ")
        print("Test mode : %s " %str(TEST_MODE))
        print("Server IP : %s " %str(SEV_IP))
        print("Gateway config file : %s " %str(SEV_IP))
        print("Data directory : %s " %str(DATA_DIR))
        print("incomming throughtput data file : %s " %str(GW_CONFIG))
        print("outgoing throughtput data file : %s " %str(GW_OUT_JSON))
        print("TLS connection record data file : %s " %str(TLS_CM_JSON))
        print("Key exchange data file : %s " %str(KEY_EX_JSON))
        print("===================")

#-----------------------------------------------------------------------------
    def checkLatency(self):
        """ Check latency every periodic time. """
        while not self.terminate:
            time.sleep(LAT_PERIOD)
            self.latency = mean(measure_latency(host='google.com'))
            print(self.latency)

#-----------------------------------------------------------------------------
    def loadJsonData(self, filePath):
        """ Load the Json file and return the Json object."""
        jsonRe = None
        with open(filePath, "r") as fh:
            lines = fh.readlines()
            idx = random.randint(0, len(lines)-1) if TEST_MODE else -1
            jsonRe = json.loads(lines[idx].rstrip())
        return jsonRe

#-----------------------------------------------------------------------------
    def startSubmit(self):
        """ Submit the data every 1/2 second. """
        count = -1
        print("Start sunmit the data to server.")
        while not self.terminate:
            time.sleep(RPT_PERIOD)
            # Check the trhought put data.
            thrIn = self.loadJsonData(GW_IN_JSON)
            thrOut = self.loadJsonData(GW_OUT_JSON)
            thrMsg = ';'.join(('D', self.dataDist['gatewayID'],
                               str(thrIn["throughput_mbps"]),
                               str(thrOut["throughput_mbps"]),
                               str(thrIn["percent_enc"]),
                               str(self.latency) ))
            self.gwClient.sendMsg(thrMsg, resp=False)
            # Check TLS information.
            tlsDict = self.loadJsonData(TLS_CM_JSON)
            if count % 20 == 0:
                tlsMsg = ';'.join( ('T', tlsDict['Src_IP_address'], 
                    str(tlsDict["Dest_IP_address"]),
                    str(tlsDict["TLS_Version"]),
                    str(tlsDict["TLS_Cipher_Suite"]) ))
                self.gwClient.sendMsg(tlsMsg, resp=False)
            # Check Key exchange information
            keyDict = self.loadJsonData(KEY_EX_JSON)
            if count % 20 == 0:
                keyMsg = ';'.join( ('K', keyDict['keyVal'] ))
                self.gwClient.sendMsg(keyMsg, resp=False)
            count += 1 

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    client = gwWebClient(None)
    client.startSubmit()

if __name__== "__main__":
    main()




