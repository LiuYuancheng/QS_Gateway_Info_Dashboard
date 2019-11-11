#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        gwDsahboardRun.py
#
# Purpose:     This module is used to create a dashboard to show the gateway 
#              information.
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

from datetime import datetime
import threading
import speedtest

import gwDashboardGobal as gv
import gwDashboardPanel as gp

PERIODIC = 500  # main thread periodically callback by 10ms.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class gwDsahboardFrame(wx.Frame):
    """ URL/IP gps position finder main UI frame."""
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=(1120, 1040))
        #self.SetBackgroundColour(wx.Colour(18, 86, 133))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        gv.iTitleFont = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)

        self.speedTestServ = ownSpeedTest(0, "Own Speed test", 1)
        self.speedTestServ.start()
        gv.iDataMgr = GWDataMgr(self)

        self.SetSizer(self._buidUISizer())
        # Set the periodic callback.
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(PERIODIC)  # every 100 ms
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.SetDoubleBuffered(True)


#--GeoLFrame-------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the main UI Sizer. """
        flagsR = wx.RIGHT
        mSizer = wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self._buildOwnInfoSizer(wx.VERTICAL), flag=flagsR, border=2)
        hbox0.AddSpacer(5)
        hbox0.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 245),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        hbox0.AddSpacer(5)


        gv.iCtrlPanel = self.ownInfoPanel = gp.PanelOwnInfo(self)
        hbox0.Add(self.ownInfoPanel, flag=flagsR, border=2)
        mSizer.Add(hbox0, flag=flagsR, border=2)

        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(1100, -1),
                                 style=wx.LI_HORIZONTAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)

        self.gwtitleLb = wx.StaticText(self, label="GateWay data display")
        self.gwtitleLb.SetFont(gv.iTitleFont)
        #self.gwtitleLb.SetForegroundColour(wx.Colour(200,200,200))
        mSizer.Add(self.gwtitleLb, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(self._buildGatewaySizer(wx.HORIZONTAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        self.chartPanel = gp.ChartDisplayPanel(self)
        mSizer.Add(self.chartPanel, flag=flagsR, border=2)
        return mSizer

#--GeoLFrame-------------------------------------------------------------------
    def _buidUISizerOld(self):
        """ Build the main UI Sizer. """
        flagsR = wx.RIGHT
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        mSizer.AddSpacer(5)
        vbox0 = wx.BoxSizer(wx.VERTICAL)

        vbox0.AddSpacer(5)
        vbox0.Add(self._buildOwnInfoSizer(wx.HORIZONTAL), flag=flagsR, border=2)
        vbox0.AddSpacer(5)
        self.ownInfoPanel = gp.PanelOwnInfo(self)
        vbox0.Add(self.ownInfoPanel, flag=flagsR, border=2)
        mSizer.Add(vbox0, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 1120),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.gwtitleLb = wx.StaticText(self, label="GateWay data display")
        self.gwtitleLb.SetFont(gv.iTitleFont)
        #self.gwtitleLb.SetForegroundColour(wx.Colour(200,200,200))
        vbox1.Add(self.gwtitleLb, flag=flagsR, border=2)    
        vbox1.AddSpacer(5)
        vbox1.Add(self._buildGatewaySizer(wx.HORIZONTAL), flag=flagsR, border=2)
        vbox1.AddSpacer(5)
        self.chartPanel = gp.ChartDisplayPanel(self)
        vbox1.Add(self.chartPanel, flag=flagsR, border=2)
        mSizer.Add(vbox1, flag=flagsR, border=2)
        return mSizer

#-----------------------------------------------------------------------------
    def _buildStateInfoBox(self, layout, mainLabel, subLabels, bSize):
        """ Build a static box hold the data the list 
        """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        bsizer = wx.StaticBoxSizer(wx.StaticBox(
            self, -1, label=mainLabel, size=bSize), layout)
        gs = wx.GridSizer(len(subLabels), 2, 5, 5) if layout == wx.VERTICAL else wx.GridSizer(1, len(subLabels)*2, 5, 5)
        valueLblist = []
        for val in subLabels:
            gs.Add(wx.StaticText(self, label=val), flag=flagsR, border=2)
            dataLb = wx.StaticText(self, label=' -- ')
            valueLblist.append(dataLb)
            gs.Add(dataLb, flag=flagsR, border=2)
        bsizer.Add(gs, flag=flagsR, border=2)
        return (bsizer, valueLblist)

#--GeoLFrame-------------------------------------------------------------------

    def _buildOwnInfoSizer(self, layout):
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(layout)
        
        self.titleLb = wx.StaticText(self, label="DashBoad Server Information")
        self.titleLb.SetFont(gv.iTitleFont)
        #self.titleLb.SetForegroundColour(wx.Colour(200,200,200))
        hSizer.Add(self.titleLb, flag=flagsR, border=2)
        hSizer.AddSpacer(10)
        ownILbs =(' IP Address:', ' Running Mode:', ' GPS Position:', ' ISP Information:')
        bsizer1, self.ownInfoLbs = self._buildStateInfoBox(wx.VERTICAL, "DashBoard Own Information", ownILbs, (340, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(5)
        netwLbs = (' DownLoad Speed [Mbps]:', ' Upload Speed [Mbps]:', ' Network Latency [ms]', ' Last Update Time:')
        bsizer2, self.networkLbs = self._buildStateInfoBox(wx.VERTICAL, "Host Network Information", netwLbs, (340, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        return hSizer

    def _buildOwnInfoSizerOld(self, layout):
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
    def _buildGatewaySizer(self, layout):
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(layout)
        gwILbs =(' Gateway IPAddr:', ' GateWay Mac:', ' GateWay GPS Pos:', ' Last Report Time:')
        bsizer1, self.gwInfoLbs = self._buildStateInfoBox(wx.HORIZONTAL,"GateWay Information", gwILbs, (1130, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(20)
        #gwDLbs =(' Data 0:', ' Data 1:', ' Data 2:', ' Data 3:')
        #bsizer2, self.gwDataLbs = self._buildStateInfoBox(wx.HORIZONTAL,"GateWay Data", gwDLbs, (650, 300))
        #hSizer.Add(bsizer2, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        return hSizer

#-----------------------------------------------------------------------------
    def _buildGatewaySizerOld(self, layout):
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

    #--<telloFrame>----------------------------------------------------------------www
    def periodic(self, event):
        """ Periodic call back to handle all the functions."""
        now = time.time()
        if now - self.lastPeriodicTime >= 3:
            gv.iDataMgr.updateData(gv.iOwnID, [random.randint(1,20) for i in range(4)])
            if gv.iSelectedGW:
                dataDict = gv.iDataMgr.getDataDict()
                self.chartPanel.updateData(dataDict[gv.iSelectedGW]['Data'])
                self.chartPanel.updateDisplay()
            self.ownInfoPanel.updateGrid()
            self.lastPeriodicTime = now


    def updateOwnInfo(self, dataKey, args):
        if dataKey == 0:
            for k, label in enumerate(self.ownInfoLbs):
                label.SetLabel(args[k])
            if not gv.iMasterMode:
                gv.iDataMgr.addNewGW(gv.iOwnID, args[0], '8C-EC-4B-C2-71-48', args[2])

        elif dataKey == 1:
            for k, label in enumerate(self.networkLbs):
                label.SetLabel(args[k])

    def updateGateWayInfo(self):
        dataDict = gv.iDataMgr.getDataDict()
        dataSet = dataDict[gv.iSelectedGW]
        ipStr = dataSet['IpMac'][0]
        macStr = dataSet['IpMac'][1]
        gpsStr = dataSet['GPS']
        rpStr = dataSet['ReportT']
        for k, label in enumerate((ipStr, macStr, gpsStr, rpStr)):
            self.gwInfoLbs[k].SetLabel(str(label))

    def onClose(self, event):
        """ Stop all the thread and close the UI."""
        self.speedTestServ.stop()
        self.Destroy()

#class dataMgr(object):
class GWDataMgr(object):
    """ Interface to store the PLC information and control the PLC through 
        by hooking to the ModBus(TCPIP).
    """
    def __init__(self, parent):
        self.dataDict = {}
        self.gwCount = 0 


    def getDataDict(self):
        return self.dataDict

    def addNewGW(self, gwID, ipStr, macStr, GPSlist):
        dataVal = {
            'Idx': self.gwCount, 
            'IpMac': (ipStr, macStr),
            'GPS': GPSlist,
            'LoginT': datetime.now().strftime("%m_%d_%Y_%H:%M:%S"),
            'ReportT': time.time(),
            'Data':[[0]*20, [0]*20, [0]*20, [0]*20]
        }
        self.dataDict[gwID] = dataVal
        self.gwCount += 1
        gv.iCtrlPanel.addToGrid(gwID, dataVal)

    def updateData(self, gwID, dataList):
        if gwID in self.dataDict.keys():
            self.dataDict[gwID]['ReportT'] = time.time()
            for k, dataSet in enumerate(self.dataDict[gwID]['Data']):
                dataSet.pop(0)
                dataSet.append(dataList[k])

            print(self.dataDict[gwID]['Data'])

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
        print("Speed test server connected")

    def run(self):
        """ Main loop to handle the data feed back."""
        while not self.terminate:
            time.sleep(3) # main video more smoth
            threads = None
            self.testServ.download(threads=threads)
            self.testServ.upload(threads=threads)
            self.testServ.results.share()
            results_dict = self.testServ.results.dict()
            if self.terminate: break
            if gv.iMainFrame and self.counter > 0:
                ownInfo = results_dict['client']
                ip = ownInfo['ip']
                mode = 'MasterMode :'+str(gv.VD_IP[1]) if gv.iMasterMode else 'SlaveMode :'+str(gv.VD_IP[1])
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
        print('Tello video server terminated.')

    def stop(self):
        self.terminate = True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        gv.iMainFrame = gwDsahboardFrame(None, -1, gv.APP_NAME)
        gv.iMainFrame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
