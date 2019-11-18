#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        gwDsahboardRun.py
#
# Purpose:     This module is used to create a dashboard to show the gateway 
#              network/dpdk test information.
#
# Author:      Yuancheng Liu
#
# Created:     2019/11/09
# Copyright:   YC @ Singtel Cyber Security Research & Development Laboratory
# License:     YC
#-----------------------------------------------------------------------------
import wx
import time
import random
import socket
import json
import threading
import speedtest
from datetime import datetime

import gwDashboardGobal as gv
import gwDashboardPanel as gp

PERIODIC = 500  # main thread periodically callback by 10ms.
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class gwDsahboardFrame(wx.Frame):
    """ gateway dashboard main UI frame."""
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=(1550, 960))
        gv.iMainFrame = self
        self.SetBackgroundColour(wx.Colour(18, 86, 133))
        #self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        gv.iTitleFont = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)
        # Init the data manager. 
        gv.iDataMgr = GWDataMgr(self, dataSize=(4, 80))
        # Build the UI.
        self.SetSizer(self._buidUISizer())
        # Init the own network speed test thread.
        self.speedTestServ = ownSpeedTest(0, "Server SpeedTest", 1)
        self.speedTestServ.start()
        # Init the UDP server.
        self.reportServ = GWReportServ(1, "Report server", 1)
        self.reportServ.start()
        # Set the periodic callback.
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(PERIODIC)  # every 0.5s
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.SetDoubleBuffered(True)

#-----------------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the main UI Sizer. """
        flagsR = wx.RIGHT
        mSizer = wx.BoxSizer(wx.VERTICAL)
        # Row Idx 0: colum 0 - bashboad server information and gateway table.
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.AddSpacer(5)
        hbox0.Add(self._buildOwnInfoSizer(wx.VERTICAL), flag=flagsR, border=2)
        # split line
        hbox0.AddSpacer(5)
        hbox0.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 245),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        hbox0.AddSpacer(5)
        #  Row Idx 0: colum 1 - Deployed Gateway information.
        gv.iGWTablePanel = self.ownInfoPanel = gp.PanelGwInfo(self)
        hbox0.Add(self.ownInfoPanel, flag=flagsR, border=2)
        mSizer.Add(hbox0, flag=flagsR, border=2)
        # split line
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(1530, -1),
                                 style=wx.LI_HORIZONTAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        # Row Idx 1: gateway display area.
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.AddSpacer(5)
        hbox2.Add(self._buildGatewaySizer(), flag=flagsR, border=2)
        hbox2.AddSpacer(5)
        hbox2.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 660),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        hbox2.AddSpacer(5)
        self.chartPanel = gp.ChartDisplayPanel(self)
        hbox2.Add(self.chartPanel, flag=flagsR, border=2)
        mSizer.Add(hbox2, flag=flagsR, border=2)
        return mSizer

#-----------------------------------------------------------------------------
    def _buildGatewaySizer(self):
        """ Build the gate information sizer."""
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        vSizer = wx.BoxSizer(wx.VERTICAL)
        self.gwtitleLb = wx.StaticText(self, label=" GateWay Detail Inforamtion ")
        self.gwtitleLb.SetFont(gv.iTitleFont)
        self.gwtitleLb.SetForegroundColour(wx.Colour(200,200,200))
        vSizer.Add(self.gwtitleLb, flag=flagsR, border=2)
        #vSizer.AddSpacer(5)
        #self.gwHardwareLb = wx.StaticText(self, label="[ Own_00: CPU-Intel(R) Core(TM) i7-8700 @3.2GHz, RAM-8GB ]")
        #self.gwHardwareLb.SetForegroundColour(wx.Colour(200,200,200))
        vSizer.AddSpacer(10)
        #vSizer.Add(self.gwHardwareLb, flag=wx.ALIGN_BOTTOM, border=2)
        vSizer.AddSpacer(5)
        gwILbs =(' GateWay ID :', ' IP Address :',  ' CPU Info :', ' RAM Info :', ' UpdateTime:' ,)
        bsizer1, self.gwInfoLbs = self._buildStateInfoBox(wx.VERTICAL," GateWay Computer Information ", gwILbs, (400, 300))
        vSizer.Add(bsizer1, flag=flagsR, border=2)
        vSizer.AddSpacer(5)
        self.tlsConnLb = wx.StaticText(self, label=" TLS Connection : ")
        self.tlsConnLb.SetForegroundColour(wx.Colour(200,200,200))
        vSizer.Add(self.tlsConnLb, flag=flagsR, border=2)
        vSizer.AddSpacer(5)
        self.tlsTF = wx.TextCtrl(self, size=(400, 250), style=wx.TE_MULTILINE)
        vSizer.Add(self.tlsTF, flag=flagsR, border=2)
        self.tlsTF.AppendText("----------- Gateway TLS connection information ---------- \n")
        return vSizer

#-----------------------------------------------------------------------------
    def _buildOwnInfoSizer(self, layout):
        """ Build the server own information sizer: own information + network 
            information.
        """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(layout)
        self.titleLb = wx.StaticText(
            self, label=" DashBoard Server Information ")
        self.titleLb.SetFont(gv.iTitleFont)
        self.titleLb.SetForegroundColour(wx.Colour(200, 200, 200))
        hSizer.Add(self.titleLb, flag=flagsR, border=2)
        hSizer.AddSpacer(10)
        ownILbs = (' IP Address :',
                   ' Running Mode :',
                   ' GPS Position :',
                   ' ISP Information :')
        bsizer1, self.ownInfoLbs = self._buildStateInfoBox(
            wx.VERTICAL, " Host Computer Information ", ownILbs, (400, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(5)
        netwLbs = (' DownLoad Speed [Mbps] :',
                   ' Upload Speed [Mbps] :',
                   ' Network Latency [ms] :',
                   ' Last Update Time[H:M:S] :')
        bsizer2, self.networkLbs = self._buildStateInfoBox(
            wx.VERTICAL, " Host Network Information ", netwLbs, (400, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        return hSizer

#-----------------------------------------------------------------------------
    def _buildStateInfoBox(self, layout, mainLabel, subLabels, bSize):
        """ Build a static box hold the data the list 
            > layout :  labels layout ( wx.VERTICAL/wx.HORIONTAL)
            > mainLabel: static box title name(str)
            > subLabels: string list of subLabels.
            > bSize: boxSize(int, int)
            return: 
                > boxSizer
                > list of data label(used for update value parameters)
        """
        flagsR = wx.LEFT | wx.ALIGN_CENTER_VERTICAL
        bsizer = wx.StaticBoxSizer(wx.StaticBox(
            self, -1, label=mainLabel, size=bSize), layout)
        gs = wx.GridSizer(len(subLabels), 2, 5, 5) if layout == wx.VERTICAL else wx.GridSizer(
            1, len(subLabels)*2, 5, 5)
        valueLblist = []
        for val in subLabels:
            # Data label:
            titleLb = wx.StaticText(self, label=' %s' %val)
            gs.Add(titleLb, flag=flagsR, border=2)
            titleLb.SetForegroundColour(wx.Colour(200, 200, 200))
            # Data value:
            dataLb = wx.StaticText(self, label=' -- ')
            dataLb.SetForegroundColour(wx.Colour(200, 200, 200))
            valueLblist.append(dataLb)
            gs.Add(dataLb, flag=flagsR, border=2)
        bsizer.Add(gs, flag=wx.EXPAND, border=2)
        return (bsizer, valueLblist)

#-----------------------------------------------------------------------------
    def parseMsg(self, msg):
        """ parse the income message(login/data)."""
        dataList = msg.split(';')
        if dataList[0] == 'L':
            # handle the login message.
            gv.iDataMgr.addNewGW(dataList[1:])
        elif dataList[0] == 'D':
            # handle the data update message.
            gv.iDataMgr.updateData(dataList[1], [int(i) for i in dataList[2:]])

#-----------------------------------------------------------------------------
    def periodic(self, event):
        """ Periodic call back to handle all the functions."""
        now = time.time()
        if now - self.lastPeriodicTime >= 3:
            if gv.iSimuMode:
                x = {  "timestamp": str(datetime.now().strftime("%m_%d_%Y_%H:%M:%S")),
                        "throughput_mbps": random.randint(1,9),
                        "citpercent_ency": random.randint(1,9)
                    }
                y = json.dumps(x)
                with open('income.json', "a") as fh:
                    fh.write(y+'\n')
                with open('outcome.json', "a") as fh:
                    fh.write(y+'\n')
                
                random1 = None
                random2 = None

                with open('income.json', "r") as fh:
                    lines = fh.readlines()
                    line = lines[-1].rstrip()
                    random1 = json.loads(line)

                with open('outcome.json', "r") as fh:
                    lines = fh.readlines()
                    line = lines[-1].rstrip()
                    random2 = json.loads(line)

                gv.iDataMgr.updateData(gv.iOwnID, [random1["throughput_mbps"],  random2["throughput_mbps"], random1["citpercent_ency"], random2["citpercent_ency"]])


                #gv.iDataMgr.updateData(gv.iOwnID, [random.randint(1,20) for i in range(4)])
            if gv.iSelectedGW:
                dataDict = gv.iDataMgr.getDataDict(gv.iSelectedGW)
                self.chartPanel.updateData(dataDict['Data'])
                self.chartPanel.updateDisplay()
                self.updateGateWayInfo(False)
                
            self.ownInfoPanel.updateGridState()
            self.lastPeriodicTime = now

#-----------------------------------------------------------------------------
    def updateOwnInfo(self, dataKey, args):
        """ Update the server information. 
            > dataKey: 0-Update server infomation 1-update network information.  
        """
        if dataKey == 0:
            for k, label in enumerate(self.ownInfoLbs):
                label.SetLabel(args[k])
            if not gv.iMasterMode:
                gv.iDataMgr.addNewGW( (gv.iOwnID, args[0], 'v1.1', args[2]))
        elif dataKey == 1:
            for k, label in enumerate(self.networkLbs):
                label.SetLabel(args[k])

    def appendTlsInfo(self, tlsList):
        self.updateTlsDetail(' New TLS connection:')
        self.updateTlsDetail(' Time : %s' %str(datetime.now().strftime("%m_%d_%Y_%H:%M:%S")))
        lbList = (' Src IP address :',
                  ' Dist IP address : ',
                  ' TLS Version : ',
                  ' TLS Cipher Suite : ')
        for i, val in enumerate(lbList):
            self.updateTlsDetail(val+str(tlsList[i]))
        self.updateTlsDetail('---------------------------------------------------------\n\n')

    def updateTlsDetail(self, data):
        """ Update the data in the detail text field. Input 'None' will clear the 
            detail information text field.
        """
        if data is None:
            self.tlsTF.Clear()
        else:
            self.tlsTF.AppendText(" - %s \n" %str(data))

#-----------------------------------------------------------------------------
    def updateGateWayInfo(self, newGwFlag):
        """ Update the gateway information.
        """
        dataSet = gv.iDataMgr.getDataDict(gv.iSelectedGW)
        if newGwFlag:
            datalist = (gv.iSelectedGW,
                        dataSet['IpMac'],
                        'Intel(R)Core(TM)i7-8700@3.2GHz',
                        '8GB-DDR4 1333Hz',
                        str(datetime.fromtimestamp(int(dataSet['ReportT']))))
            for k, label in enumerate(datalist):
                self.gwInfoLbs[k].SetLabel(str(label))
        else:
            self.gwInfoLbs[-1].SetLabel(str(datetime.fromtimestamp(int(dataSet['ReportT']))))

#-----------------------------------------------------------------------------
    def onClose(self, event):
        """ Stop all the thread and close the UI."""
        self.speedTestServ.stop()
        self.reportServ.stop()
        self.Destroy()

#-----------------------------------------------------------------------------
    def x_buidUISizerOld(self):
        """ Build the main UI Sizer. (Currently not used.)"""
        flagsR = wx.RIGHT
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        mSizer.AddSpacer(5)
        vbox0 = wx.BoxSizer(wx.VERTICAL)
        vbox0.AddSpacer(5)
        vbox0.Add(self._buildOwnInfoSizer(wx.HORIZONTAL), flag=flagsR, border=2)
        vbox0.AddSpacer(5)
        self.ownInfoPanel = gp.PanelGwInfo(self)
        vbox0.Add(self.ownInfoPanel, flag=flagsR, border=2)
        mSizer.Add(vbox0, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 1120),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.gwtitleLb = wx.StaticText(self, label="GateWay data display")
        self.gwtitleLb.SetFont(gv.iTitleFont)
        self.gwtitleLb.SetForegroundColour(wx.Colour(200,200,200))
        vbox1.Add(self.gwtitleLb, flag=flagsR, border=2)    
        vbox1.AddSpacer(5)
        vbox1.Add(self._buildGatewaySizer(wx.HORIZONTAL), flag=flagsR, border=2)
        vbox1.AddSpacer(5)
        self.chartPanel = gp.ChartDisplayPanel(self)
        vbox1.Add(self.chartPanel, flag=flagsR, border=2)
        mSizer.Add(vbox1, flag=flagsR, border=2)
        return mSizer

#-----------------------------------------------------------------------------
    def x_buildOwnInfoSizerOld(self, layout):
        """ Build the main UI Sizer. (Currently not used.)"""
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(layout)
        ownILbs =(' IP Address:', ' Running Mode:', ' GPS Position:', ' ISP Information:')
        bsizer1, self.ownInfoLbs = self._buildStateInfoBox(wx.VERTICAL, "DashBoard Own Information", ownILbs, (250, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(20)
        netwLbs = (' DownLoad Speed [Mbps]:', ' Upload Speed [Mbps]:', ' Network Latency [ms]', ' Last Update Time:')
        bsizer2, self.networkLbs = self._buildStateInfoBox(wx.VERTICAL,"Host Network Information", netwLbs, (400, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        return hSizer

#-----------------------------------------------------------------------------
    def x_buildGatewaySizerOld(self, layout):
        """ Build the main UI Sizer. (Currently not used.)"""
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(layout)
        gwILbs =(' Gateway IPAddr:', ' GateWay Mac:', ' GateWay GPS Pos:', ' Last Report Time:')
        bsizer1, self.gwInfoLbs = self._buildStateInfoBox(wx.VERTICAL,"GateWay Information", gwILbs, (250, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(20)
        gwDLbs =(' Data 0:', ' Data 1:', ' Data 2:', ' Data 3:')
        bsizer2, self.gwDataLbs = self._buildStateInfoBox(wx.VERTICAL,"GateWay Data", gwDLbs, (650, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        return hSizer

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class GWDataMgr(object):
    """ Getway server data manager.
    """
    def __init__(self, parent, dataSize=(4 ,20)):
        self.dataDict = {}          # main data dictionary
        self.gwCount = 0            # gv Index in the gateway table.
        self.dataSize = dataSize    # gateway dataSet size (data category, data num)

#-----------------------------------------------------------------------------
    def getDataDict(self, sKey):
        """ Return the sub data dict based on the input key."""
        if sKey == 'keys()':
            return self.dataDict.keys()
        elif sKey == 'items()':
            return self.dataDict.items()
        elif sKey in self.dataDict.keys():
            return self.dataDict[sKey]
        return None

#-----------------------------------------------------------------------------
    def addNewGW(self, dataList):
        """ Add a new gateway in the data dict. """
        gwID, ipStr, version, gps = dataList
        if gwID in self.dataDict.keys(): return False
        dataVal = {
            'Idx':      self.gwCount, 
            'IpMac':    ipStr,
            'version':  version,
            'pdpkVer':  ('19.08', 'Openssl', 'AES-CBC 256'),
            'GPS':      gps,
            'LoginT':   datetime.now().strftime("%m_%d_%Y_%H:%M:%S"),
            'ReportT':  time.time(),
            'Data':     [[0]*self.dataSize[1] for i in range(self.dataSize[0])]
        }
        self.dataDict[gwID] = dataVal
        self.gwCount += 1
        gv.iGWTablePanel.addToGrid(gwID, dataVal)
        return True

#-----------------------------------------------------------------------------
    def updateData(self, gwID, dataList):
        """ Update the 
        """
        if gwID in self.dataDict.keys():
            self.dataDict[gwID]['ReportT'] = time.time()
            for k, dataSet in enumerate(self.dataDict[gwID]['Data']):
                dataSet.pop(0)
                dataSet.append(dataList[k])


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ownSpeedTest(threading.Thread):
    """ Thread to test the own speed.""" 
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.terminate = False
        servers = []
        self.counter = counter
        self.testServ = speedtest.Speedtest()
        self.testServ.get_servers(servers)
        self.testServ.get_best_server()
        # Load the simulation information if the 
        if gv.iSimuMode:
            ipAddr = '137.132.211.202'
            mode = 'MasterMode :'+str(gv.SE_IP[1]) if gv.iMasterMode else 'SlaveMode :'+str(gv.SE_IP[1])
            gps = '[1.36672, 103.81]'
            isp = 'National University of Singapore'
            gv.iMainFrame.updateOwnInfo(0,(ipAddr, mode, gps, isp))
            downloadSp = '337.0Mbps'
            uploadSp = '223.0Mbps'
            lantency = '28ms'
            timeStr = datetime.now().strftime("%H:%M:%S")
            gv.iMainFrame.updateOwnInfo(1,(downloadSp, uploadSp, lantency, timeStr))
            self.terminate = True # don't run the speed test loop.
        print("Speed test server connected")

    def run(self):
        """ Main loop to handle the data feed back."""
        while not self.terminate:
            time.sleep(1) # main video more smoth
            threads = None
            self.testServ.download(threads=threads)
            self.testServ.upload(threads=threads)
            self.testServ.results.share()
            results_dict = self.testServ.results.dict()
            if self.terminate: break
            if gv.iMainFrame and self.counter > 0:
                ownInfo = results_dict['client']
                ip = ownInfo['ip']
                mode = 'MasterMode :'+str(gv.SE_IP[1]) if gv.iMasterMode else 'SlaveMode :'+str(gv.SE_IP[1])
                gps = [ownInfo['lat'], ownInfo['lon']]
                isp = ownInfo['isp']
                gv.iMainFrame.updateOwnInfo(0,(ip, mode, str(gps), isp))
                self.counter -= 1

            downloadS = str(results_dict['download'] //1000000) + 'Mbps'
            uploadSpeed = str(results_dict['upload'] //1000000) + 'Mbps'
            lantency = str(results_dict['ping'])+'ms'
            timeStr = datetime.now().strftime("%H:%M:%S")
            gv.iMainFrame.updateOwnInfo(1,(downloadS, uploadSpeed, lantency, timeStr))
            time.sleep(5) # main video more smoth
            print(results_dict)
            if self.counter == 0: return
        print('Tello video server terminated.')

    def stop(self):
        self.terminate = True


class GWReportServ(threading.Thread):
    """ Tello state prameters feedback UDP reading server thread.""" 
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.terminate = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(gv.SE_IP)
        self.recvMsg = None

    def run(self):
        """ main loop to handle the data feed back."""
        while not self.terminate:
            data, _ = self.sock.recvfrom(2048) 
            if not data: break
            if isinstance(data, bytes):
                self.recvMsg = data.decode(encoding="utf-8")
                print(self.recvMsg)
                gv.iMainFrame.parseMsg(self.recvMsg)

        self.sock.close()
        print('Tello control server terminated')

    def stop(self):
        """ Send back a None message to terminate the buffer reading waiting part."""
        self.terminate = True
        closeClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        closeClient.sendto(b'', ("127.0.0.1", gv.SE_IP[1]))
        closeClient.close()


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        MainFrame = gwDsahboardFrame(None, -1, gv.APP_NAME)
        MainFrame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
