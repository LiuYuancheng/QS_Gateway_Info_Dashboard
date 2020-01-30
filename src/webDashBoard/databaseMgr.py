#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        databaseMgr.py
#
# Purpose:     This module will provide a influx database manager to collect the 
#              gateway feed back data by UDP and insert to influx database which
#              will be used for the grafana dashboard.
#
# Author:      Yuancheng Liu
#
# Created:     2019/01/15
# Copyright:   
# License:     
#-----------------------------------------------------------------------------

import time
import threading
from statistics import mean
from datetime import datetime

from influxdb import InfluxDBClient
from tcp_latency import measure_latency

import udpCom

UDP_PORT = 5005
TEST_MODE = False   # test mode flag.
LAT_PERIOD = 5      # latency periodic check time.
RPT_PERIOD = 2      # time period to insert the data to data base.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class InfluxCli(object):
    """ Client to connect to the influx db and insert data."""
    def __init__(self, ipAddr=None, dbInfo=None):
        """ Init the influx DB client to login to the data base. dbInfo: name, 
            password, databaseName. init example: 
            client = InfluxCli(ipAddr=('127.0.0.1', 8086), dbinfo=('root', 'root', 'gatewayDB'))
        """
        (ip, port) = ipAddr if ipAddr else ('localhost', 8086)
        (user, pwd, dbName) = dbInfo if dbInfo and len(
            dbInfo) == 3 else ('root', 'root', 'gatewayDB')
        #self.dbClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'quantumGWDB')
        self.dbClient = InfluxDBClient(ip, port, user, pwd, dbName)

#-----------------------------------------------------------------------------
    def writeGwData(self, gwName, dataDict):
        """ Write the gateway data to the related gateway table based on gateway 
            name. 
        """
        gwDatajson = [
            {
                "measurement": str(gwName),
                "tags": {
                    "Name": "time",
                },
                "fields": {
                    "ival": dataDict['inTP'],
                    "oval": dataDict['outTP'],
                    "latVal": dataDict['latency'],
                    "pctVal": dataDict['encptPct'],
                    "frgVal": dataDict['frgVal'],
                }
            }]
        self.dbClient.write_points(gwDatajson)

#-----------------------------------------------------------------------------
    def writeTLSData(self, dataDict):
        """ Write the TLS information. """
        tlsJson = [
            {
                "measurement": "tlsConn",
                "tags": {
                    "Name": "time",
                },
                "fields": {
                    "src": dataDict['srcIP'],
                    "dest": dataDict['dstIP'],
                    "ver": dataDict['tlsVer'],
                    "cipher": dataDict['cipher'],
                    "state": dataDict['state'],
                }
            }]
        self.dbClient.write_points(tlsJson)

#-----------------------------------------------------------------------------
    def writeKeyExData(self, keyVal):
        """ Write the key exchange data. """
        kexJson = [
            {
                "measurement": "keyEx",
                "tags": {
                    "Name": "time",
                },
                "fields": {
                    "val": keyVal,
                }
            }]
        self.dbClient.write_points(kexJson)

#-----------------------------------------------------------------------------
    def writeGPSData(self, dataDict):
        """ Write the gateway GPS information."""
        locationJson = [
            {
                "measurement": "location",
                "tags": {
                    "Name": "time",
                },
                "fields": {
                    "latitude": dataDict['lat'],
                    "longitude": dataDict['lon'],
                }
            }]
        self.dbClient.write_points(locationJson)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ServThread(threading.Thread):
    """ Server thread to generate a UDP server to handle the gateway client's
        feedback data.
    """ 
    def __init__(self, parent, threadID, name):
        threading.Thread.__init__(self)
        self.parent = parent
        self.server = udpCom.udpServer(None, UDP_PORT)

    def run(self):
        """ Start the udp server's main message handling loop."""
        print("Server thread run() start.")
        self.server.serverStart(handler=self.parent.msgHandler)
        print("Server thread run() end.")

    def stop(self):
        """ Stop the udp server. Create a endclient to bypass the revFrom() block."""
        self.server.serverStop()
        endClient = udpCom.udpClient(('127.0.0.1', UDP_PORT))
        endClient.disconnect()
        endClient = None

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class DataBaseMgr(object):
    """ Main database manger program."""
    def __init__(self, parent):
        """ Init the gateway information storage dictionary, all the parameters
            and the latency check thread.
        """
        self.gwDict = {}
        self.tlsFlag = False    # new tls data incomming flag.
        self.terminate = False
        self.latency = 0.0001   # tcp latency from host computer to google
        self.client = InfluxCli(
            ipAddr=('localhost', 8086), dbInfo=('root', 'root', 'gatewayDB'))
        # TCP server thread.
        server = ServThread(self, 0, "server thread")
        server.start()
        # laterncy check thread:
        latThread = threading.Thread(target=self.checkLatency) # Not work: threading.Thread(target=self.checkLatency()) 
        latThread.daemon = True # here need to use method referring instead of invoking.  
        latThread.start()       # https://stackoverflow.com/questions/30701983/new-thread-blocks-main-thread

#-----------------------------------------------------------------------------
    def msgHandler(self, msg=None, ipAddr=None):
        """ handle the feed back message."""
        if isinstance(msg, bytes): msg = msg.decode('utf-8')
        dataList = msg.split(';')
        #print(dataList)
        if dataList[0] == 'L':
            resp = 'R;L' if self.addNewGw(msgList=dataList[1:], ipAddr=ipAddr) else 'R;E'
            return resp
        elif dataList[0] == 'D':
            self.updateData(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'T':
            self.updateTls(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'A':
            self.updateLatency(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'K':
            self.updateKeyEx(msgList=dataList[1:], ipAddr=ipAddr)

#-----------------------------------------------------------------------------
    def checkLatency(self):
        """ Check latency every periodic time. """
        while not self.terminate:
            time.sleep(LAT_PERIOD)
            self.latency = mean(measure_latency(host='google.com'))
            
#-----------------------------------------------------------------------------
    def addNewGw(self, msgList=None, ipAddr=None):
        """ Add a new gateway in the gateway dictionary."""
        if ipAddr in self.gwDict.keys(): return False
        name, lat, lon = msgList
        gwDict = {
            'Name'      : 'GateWay_00',         # Gateway name 
            'ip'        : ('127.0.0.1', 5005),  # IP address
            'lat'       : '1.2988',             # GPS latitude 
            'lon'       : '103.836',            # GPS longitude 
            'inTP'      : 0.0001,               # Incoming throughtput
            'outTP'     : 0.0001,               # Outgoing throughtput
            'latency'   : 0.0001,               # Latency: (gateway latency - host latency)/2
            'encptPct'  : 0.0001,               # Data packet encription rate.
            'frgVal'    : 0.0001,               # Fragment value
            'srcIP'     : '137.132.213.225',    # TLS source ip address
            'dstIP'     : '136.132.213.218',    # TLS destination ip address
            'tlsVer'    : 'TLS 1.2',            # TLS version
            'cipher'    : 'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256', # TLS cipher data.
            'state'     : 0,                    # Quantum saft level: 0 not safe, >0 safe
            'updateT'   : time.time()           # Gateway last report time.
        }
        gwDict['ip'] = ipAddr
        gwDict['Name'] = name
        gwDict['lat'] = lat
        gwDict['lon'] = lon
        print("Add the new gw <%s> " %str(gwDict))
        self.gwDict[ipAddr[0]] = gwDict
        self.client.writeGPSData(gwDict)
        return True

#-----------------------------------------------------------------------------
    def updateData(self, msgList=None, ipAddr=None):
        """ Update the gateway data. """
        _, inTP, outTP, encptPct, latency = msgList
        self.gwDict[ipAddr[0]]['inTP'] = float(inTP)
        self.gwDict[ipAddr[0]]['outTP'] = float(outTP)
        self.gwDict[ipAddr[0]]['encptPct'] = float(encptPct)
        print((float(latency), self.latency))
        self.gwDict[ipAddr[0]]['latency'] = abs(float(latency)-self.latency)/2000.0

#-----------------------------------------------------------------------------
    def updateTls(self, msgList=None, ipAddr=None):
        """ Update the TLS data. """
        srcIP, dstIP, tlsVer, cipher = msgList
        self.gwDict[ipAddr[0]]['srcIP'] = srcIP
        self.gwDict[ipAddr[0]]['dstIP'] = dstIP
        self.gwDict[ipAddr[0]]['tlsVer'] = tlsVer
        self.gwDict[ipAddr[0]]['cipher'] = cipher
        self.tlsFlag = True

#-----------------------------------------------------------------------------
    def updateLatency(self, msgList=None, ipAddr=None):
        """ Update the latency data. """
        latency = float(msgList[0])
        for key in self.gwDict.keys():
            self.gwDict[key]['latency'] = latency

#-----------------------------------------------------------------------------
    def updateKeyEx(self, msgList=None, ipAddr=None):
        """ Update the key exchange record."""
        keyVal = msgList[0]
        self.client.writeKeyExData(keyVal)

#-----------------------------------------------------------------------------
    def startServer(self):
        while not self.terminate:
            time.sleep(RPT_PERIOD)
            print('update data.')
            #continue
            # update data every 2 sec
            for key in self.gwDict.keys():
                self.client.writeGwData(self.gwDict[key]['Name'], self.gwDict[key])
                if self.tlsFlag:
                    self.client.writeTLSData(self.gwDict[key])
                    self.tlsFlag = False

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    dataMgr = DataBaseMgr(None)
    dataMgr.startServer()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

