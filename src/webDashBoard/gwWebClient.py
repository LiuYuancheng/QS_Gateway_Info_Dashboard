#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        gwWebClient.py
#
# Purpose:     This module will provide a UDP client and server communication API.
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

# Set the constants.
TEST_MODE = True # test mode flag, set to False when deploy the client.
DATA_DIR = 'testData' if TEST_MODE else ''
SEV_IP = ('127.0.0.1', 5005) if TEST_MODE else ('10.0.0.1', 5005)
GW_CONFIG = os.path.join(DATA_DIR,'gwConfig.json')
GW_IN_JSON = os.path.join(DATA_DIR,'tp01_in_info.json')
GW_OUT_JSON = os.path.join(DATA_DIR,'tp01_out_info.json')
TLS_CM_JSON = os.path.join(DATA_DIR,'tls01_info.json.json')
KEY_EX_JSON = os.path.join(DATA_DIR,'key_ex_info.jsonn')
PERIODIC = 1    # Time periodic to submit the data to the server.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class gwWebClient(object):
    """ UDP client module."""
    def __init__(self, parent):
        """ Create an ipv4 (AF_INET) socket object using the udp protocol (SOCK_DGRAM)
            init example: client = udpClient(('127.0.0.1', 502))
        """
        self.showConstant()
        self.gwClient = udpCom.udpClient(SEV_IP)
        self.termiate = False
        print("load the configure file and login.")
        self.dataDist = None
        with open(GW_CONFIG, "r") as fh:
            self.dataDist = json.loads(fh.readlines()[-1].rstrip()) # load the last line of the json.
        lat, lon = self.dataDist['GPS'].split(',')
        loginStr = ";".join(('L', self.dataDist['gatewayID'], lat, lon))
        print("send the login message: <%s>" %str(loginStr))
        resp = self.gwClient.sendMsg(loginStr, resp=True)
        if resp.decode('utf-8') == 'R;L':
            print('Loged in the server as a new gateway.')
        else:
            print('Server replay: %s' %str(resp))

#-----------------------------------------------------------------------------
    def showConstant(self):
        """ Show all the constants
        """
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
    def loadJsonData(self, filePath):
        jsonRe = None
        with open(filePath, "r") as fh:
            lines = fh.readlines()
            idx = random.randint(0, len(lines)-1) if TEST_MODE else -1
            jsonRe = json.loads(lines[idx].rstrip())
        return jsonRe

#-----------------------------------------------------------------------------
    def startSubmit(self):
        """ submit the data every 1/2 second.
        """
        count = -1 
        while not self.termiate:
            time.sleep(PERIODIC)
            # Check the trhought put data.
            thrIn = self.loadJsonData(GW_IN_JSON)
            thrOut = self.loadJsonData(GW_OUT_JSON)
            thrMsg = ';'.join(('D', self.dataDist['gatewayID'],
                               str(thrIn["throughput_mbps"]),
                               str(thrOut["throughput_mbps"]),
                               str(thrIn["percent_enc"])))
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

def main():
    client = gwWebClient(None)
    client.startSubmit()

if __name__== "__main__":
    main()
# Create a UDP socket





