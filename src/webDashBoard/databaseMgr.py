
import time
import threading
from datetime import datetime
from influxdb import InfluxDBClient

import udpCom

UDP_PORT = 5005
TEST_MODE = False   # test mode flag.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class InfluxCli(object):
    """ UDP client module."""
    def __init__(self, ipAddr=None, dbInfo=None):
        """ Create an ipv4 (AF_INET) socket object using the udp protocol (SOCK_DGRAM)
            init example: client = udpClient(('127.0.0.1', 502))
        """
        (ip, port) = ipAddr if ipAddr else ('localhost', 8086)
        (user, pwd, dbName) = dbInfo if dbInfo and len(dbInfo)==3 else ('root', 'root', 'gatewayDB')
        #self.dbClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'quantumGWDB')
        self.dbClient = InfluxDBClient(ip, port, user, pwd, dbName)

#-----------------------------------------------------------------------------
    def writeGwData(self, gwName, dataDict):
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
class servThread(threading.Thread):
    """ Thread to test the UDP server/insert the tcp server in other program.""" 
    def __init__(self, parent, threadID, name):
        threading.Thread.__init__(self)
        self.parent = parent
        self.threadName = name
        self.server = udpCom.udpServer(None, UDP_PORT)

    def run(self):
        """ Start the udp server's main message handling loop."""
        print("Server thread run() start.")
        self.server.serverStart(handler=self.parent.msgHandler)
        print("Server thread run() end.")
        self.threadName = None # set the thread name to None when finished.

    def stop(self):
        """ Stop the udp server. Create a endclient to bypass the revFrom() block."""
        self.server.serverStop()
        endClient = udpCom.udpClient(('127.0.0.1', UDP_PORT))
        endClient.disconnect()
        endClient = None

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class DataBaseMgr(object):
    """ UDP client module."""
    def __init__(self, parent):
 
        self.gwDict = {}
        self.tlsFlag = False    # new tls data incomming flag.
        self.terminate = False
        self.client = InfluxCli(
            ipAddr=('localhost', 8086), dbInfo=('root', 'root', 'gatewayDB'))
        server = servThread(self, 0, "server thread")
        server.start()

#-----------------------------------------------------------------------------
    def msgHandler(self, msg=None, ipAddr=None):
        if isinstance(msg, bytes): msg = msg.decode('utf-8')
        dataList = msg.split(';')
        print(dataList)
        if dataList[0] == 'L':
            self.addNewGw(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'D':
            self.updateData(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'T':
            self.updateTls(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'A':
            self.updateLatency(msgList=dataList[1:], ipAddr=ipAddr)
        elif dataList[0] == 'K':
            self.updateKeyEx(msgList=dataList[1:], ipAddr=ipAddr)

#-----------------------------------------------------------------------------
    def addNewGw(self, msgList=None, ipAddr=None):
        if ipAddr in self.gwDict.keys(): return
        name, lat, lon = msgList
        gwDict = {
            'Name'      : 'GateWay_00',
            'ip'        : ('127.0.0.1', 5005),
            'lat'       : '1.2988',
            'lon'       : '103.836',
            'inTP'      : 0.0001,
            'outTP'     : 0.0001,
            'latency'   : 0.0001,
            'encptPct'  : 0.0001,
            'frgVal'    : 0.0001,
            'srcIP'     : '137.132.213.225',
            'dstIP'     : '136.132.213.218',
            'tlsVer'    : 'TLS 1.2',
            'cipher'    : 'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',
            'state'     : 0,
            'updateT'   : time.time()
        }
        gwDict['ip'] = ipAddr
        gwDict['Name'] = name
        gwDict['lat'] = lat
        gwDict['lon'] = lon
        print("Add the new gw <%s> " %str(gwDict))
        self.gwDict[ipAddr[0]] = gwDict
        self.client.writeGPSData(gwDict)

#-----------------------------------------------------------------------------
    def updateData(self, msgList=None, ipAddr=None):
        _, inTP, outTP, encptPct = msgList
        self.gwDict[ipAddr[0]]['inTP'] = float(inTP)
        self.gwDict[ipAddr[0]]['outTP'] = float(outTP)
        self.gwDict[ipAddr[0]]['encptPct'] = float(encptPct)

#-----------------------------------------------------------------------------
    def updateTls(self, msgList=None, ipAddr=None):
        srcIP, dstIP, tlsVer, cipher = msgList
        self.gwDict[ipAddr[0]]['srcIP'] = srcIP
        self.gwDict[ipAddr[0]]['dstIP'] = dstIP
        self.gwDict[ipAddr[0]]['tlsVer'] = tlsVer
        self.gwDict[ipAddr[0]]['cipher'] = cipher
        self.tlsFlag = True

#-----------------------------------------------------------------------------
    def updateLatency(self, msgList=None, ipAddr=None):
        latency = float(msgList[0])
        for key in self.gwDict.keys():
            self.gwDict[key]['latency'] = latency

#-----------------------------------------------------------------------------
    def updateKeyEx(self, msgList=None, ipAddr=None):
        keyVal = msgList[0]
        self.client.writeKeyExData(keyVal)

#-----------------------------------------------------------------------------
    def startServer(self):
        while not self.terminate:
            time.sleep(2)
            print('update data')
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

