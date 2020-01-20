from influxdb import InfluxDBClient
from datetime import datetime
import random
import time

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
        (user, pwd, dbName) = dbInfo if dbInfo and len(dbInfo)==3 else ('root', 'root', 'quantumGWDB')
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
                    "ver": dataDict['ver'],
                    "cipher": dataDict['cipher'],
                    "state": dataDict['state'],
                }
            }]
        self.dbClient.write_points(tlsJson)

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
                    "longitude": dataDict['long'],
                }
            }]
        self.dbClient.write_points(locationJson)
    
