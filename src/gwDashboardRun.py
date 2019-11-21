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
import webbrowser
from datetime import datetime

import gwDashboardGobal as gv
import gwDashboardPanel as gp

PERIODIC = 500  # main thread periodically callback by 10ms.
WIN_SIZE = (1920, 1040) if gv.WIN_SYS else (1920, 1040)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class gwDsahboardFrame(wx.Frame):
    """ gateway dashboard main UI frame."""
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=WIN_SIZE)
        gv.iMainFrame = self
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        #self.SetBackgroundColour(wx.Colour(18, 86, 133))
        #self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.SetBackgroundColour(wx.Colour(30, 30, 30))
        
        gv.iTitleFont = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
        gv.iWeidgeClr = wx.Colour(46, 52, 66)
        self.tlsTimeStr = ''    # new tls time string.
        
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
    
        self.Maximize(True)

#-----------------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the main UI Sizer. """
        flagsR, fColour  = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, wx.Colour(200,200,200)
        mSizer = wx.BoxSizer(wx.VERTICAL)
        mSizer.AddSpacer(5)

        # Row Idx 0 : title line 
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.AddSpacer(5)
        hbox0.Add(wx.StaticBitmap(self, -1, wx.Bitmap(gv.LOGO_PATH, wx.BITMAP_TYPE_ANY)), flag=flagsR, border=2)
        hbox0.AddSpacer(20)
        titleT = wx.StaticText(self, label=" Quantum Safe Gateway Dashboard (Beta V1.0) ")
        titleT.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        titleT.SetForegroundColour(fColour)
        hbox0.Add(titleT, flag=flagsR, border=2)
        mSizer.Add(hbox0, flag=flagsR, border=2)
        self._addSplitLine(mSizer, wx.LI_HORIZONTAL, 1900)

        # Row Idx 1: colum 0 - bashboad server information and gateway table.
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.AddSpacer(5)
        ownInfoSzer = self._buildOwnInfoSizerWin(wx.VERTICAL) if gv.WIN_SYS else self._buildOwnInfoSizerLinux(wx.VERTICAL)
        hbox1.Add(ownInfoSzer, flag=flagsR, border=2)
        # split line
        self._addSplitLine(hbox1, wx.LI_VERTICAL, 205)

        #Row Idx 1: colum 1
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        gwLabel = wx.StaticText(self, label=" Deployed Gateway Information ")
        gwLabel.SetFont(gv.iTitleFont)
        gwLabel.SetForegroundColour(fColour)
        vbox1.Add(gwLabel, flag=flagsR, border=2)
        vbox1.AddSpacer(10)

        #  Row Idx 0: colum 1 - Deployed Gateway information.
        gv.iGWTablePanel = self.ownInfoPanel = gp.PanelGwInfo(self)
        vbox1.Add(self.ownInfoPanel, flag=flagsR, border=2)
        hbox1.AddSpacer(5)
        hbox1.Add(vbox1, flag=flagsR, border=2)

        mSizer.Add(hbox1, flag=flagsR, border=2)
        # split line
        self._addSplitLine(mSizer, wx.LI_HORIZONTAL, 1900)

        gwDetailLb = wx.StaticText(self, label=" Gateway Detail Information ")
        gwDetailLb.SetFont(gv.iTitleFont)
        gwDetailLb.SetForegroundColour(wx.Colour(200,200,200))
        mSizer.Add(gwDetailLb, flag=flagsR, border=2)
        mSizer.AddSpacer(10)

        # Row Idx 1: gateway display area.
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.AddSpacer(5)
        self.gwPanel = PanelGwData(self)


        hbox2.Add(self.gwPanel, flag=flagsR, border=2)
        mSizer.Add(hbox2, flag=flagsR, border=2)

        #mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(1530, -1),
        #                         style=wx.LI_HORIZONTAL), flag=flagsR, border=2)
        return mSizer


    def _addSplitLine(self, pSizer, lStyle, length):
        """ Add the split line to the input sizer. 
            pSizer: parent sizer, lStyle: line style, length: pixel length.
        """
        pSizer.AddSpacer(5)
        lSize = (length, -1) if lStyle == wx.LI_HORIZONTAL else (-1, length)
        pSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=lSize,
                                 style=lStyle), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=2)
        pSizer.AddSpacer(5)




#-----------------------------------------------------------------------------
    def _buildOwnInfoSizerWin(self, layout):
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
            wx.VERTICAL, " Host Server Information ", ownILbs, (400, 300))
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
    def _buildOwnInfoSizerLinux(self, layout):
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
                   ' UDP Host : ',
                   ' ISP Information :',
                   ' Server Start Time :', 
                   ' Total Gateway Reported :')
        bsizer1, self.ownInfoLbs = self._buildStateInfoBox(
            wx.VERTICAL, " Server Computer Information ", ownILbs, (400, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(5)
        self.networkLbs = None
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
        flagsR, tColour = wx.LEFT | wx.ALIGN_CENTER_VERTICAL, wx.Colour(200, 200, 200)
        outBox = wx.StaticBox(self, -1, label=mainLabel, size=bSize)
        outBox.SetForegroundColour(tColour)
        #outBox.SetBackgroundColour(gv.iWeidgeClr)
        bsizer = wx.StaticBoxSizer(outBox, layout)
        gs = wx.GridSizer(len(subLabels), 2, 5, 5) if layout == wx.VERTICAL else wx.GridSizer(
            1, len(subLabels)*2, 5, 5)
        valueLblist = []
        for val in subLabels:
            # Data label:
            titleLb = wx.StaticText(outBox, label=' %s' %val)
            gs.Add(titleLb, flag=flagsR, border=2)
            titleLb.SetForegroundColour(tColour)
            # Data value:
            dataLb = wx.StaticText(outBox, label=' -- ')
            dataLb.SetForegroundColour(tColour)
            valueLblist.append(dataLb)
            gs.Add(dataLb, flag=flagsR, border=2)
        bsizer.Add(gs, flag=wx.EXPAND, border=2)
        bsizer.AddSpacer(3)
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
            gv.iDataMgr.updateData(dataList[1], [float(i) for i in dataList[2:]])

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
            # Check the tls json file.
            self.checkTLSRpt()

            if gv.iSelectedGW:
                dataDict = gv.iDataMgr.getDataDict(gv.iSelectedGW)
                gv.iChartsPanel.updateData(dataDict['Data'])
                #self.chartPanel.updateDisplay()

                self.updateGateWayInfo(False)
                
            self.ownInfoPanel.updateGridState()
            self.lastPeriodicTime = now

        if gv.iChartsPanel: gv.iChartsPanel.updateDisplay()

#-----------------------------------------------------------------------------
    def updateOwnInfo(self, dataKey, args):
        """ Update the server information. 
            > dataKey: 0-Update server infomation 1-update network information.  
        """
        if dataKey == 0:
            for k, label in enumerate(self.ownInfoLbs):
                label.SetLabel(args[k])
            if gv.iMasterMode:
                with open('gwConfig.json', "r") as fh:
                    lines = fh.readlines()
                    line = lines[-1].rstrip()
                    dataDist = json.loads(line)
                    gv.iOwnID =  dataDist['gatewayID']
                gv.iDataMgr.addNewGW( (dataDist['gatewayID'], dataDist['ipAddr'], dataDist['gwVer'], dataDist['dpdk_v'], dataDist['dpdk_c'], dataDist['dpdk_e'], dataDist['keyE'], dataDist['GPS'] ))
        elif dataKey == 1:
            for k, label in enumerate(self.networkLbs):
                label.SetLabel(args[k])
        elif dataKey == 2:
            self.ownInfoLbs[-1].SetLabel(str(args[0]))

    def checkTLSRpt(self):
        """ read the json file to get the TLS data."""
        tlsDict = None
        with open('tls01_info.json', "r") as fh:
            lines = fh.readlines()
            line = lines[-1].rstrip()
            tlsDict = json.loads(line)
        
        if self.tlsTimeStr != tlsDict['Time']:
            self.tlsTimeStr = tlsDict['Time']
            self.gwPanel.appendTlsInfo((tlsDict['Src_IP_address'], tlsDict['Dest_IP_address'], tlsDict['TLS_Version'], tlsDict['TLS_Cipher_Suite']))

#-----------------------------------------------------------------------------
    def updateGateWayInfo(self, newGwFlag):
        """ Update the gateway information.
        """
        dataSet = gv.iDataMgr.getDataDict(gv.iSelectedGW)
        if newGwFlag:
            datalist = (gv.iSelectedGW,
                        dataSet['IpMac'],
                        'Intel(R)i7-8700',
                        '8GB-DDR4 1333Hz',
                        str(datetime.fromtimestamp(int(dataSet['ReportT']))))
            for k, label in enumerate(datalist):
                self.gwPanel.gwInfoLbs[k].SetLabel(str(label))
        else:
            self.gwPanel.gwInfoLbs[-1].SetLabel(str(datetime.fromtimestamp(int(dataSet['ReportT']))))

#-----------------------------------------------------------------------------
    def onClose(self, event):
        """ Stop all the thread and close the UI."""
        self.speedTestServ.stop()
        self.reportServ.stop()
        self.Destroy()

class PanelGwData(wx.Panel):
    """ gateway information."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(gv.iWeidgeClr)
        self.tlsCount = 0
        self.gwClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SetSizer(self._buildGatewaySizer())
        self.SetDoubleBuffered(True)

    #-----------------------------------------------------------------------------
    def _buildGatewaySizer(self):
        """ Build the gate information sizer."""
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        vSizer = wx.BoxSizer(wx.VERTICAL)

        vSizer.AddSpacer(10)
        gwILbs =(' GateWay ID :', ' IP Address :',  ' CPU Info :', ' RAM Info :', ' UpdateTime:')
        bsizer1, self.gwInfoLbs = self._buildStateInfoBox(wx.VERTICAL," GateWay Computer Information ", gwILbs, (400, 300))
        vSizer.Add(bsizer1, flag=flagsR, border=2)

        vSizer.AddSpacer(10)
        vSizer.Add(self._buildGwCtrlBox(), flag=flagsR, border=2)
        
        vSizer.AddSpacer(10)
        vSizer.Add(self._buildTlsCtrlBox(), flag=flagsR, border=2)


        
        vSizer.AddSpacer(10)
        #vSizer.Add(wx.StaticBitmap(self, -1, wx.Bitmap(gv.LOGO_PATH, wx.BITMAP_TYPE_ANY)),flag=flagsR, border=2)
        mSizer.Add(vSizer, flag=flagsR, border=2)

        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 700),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)

        gv.iChartsPanel = gp.ChartDisplayPanelWin(self) if gv.WIN_SYS else gp.ChartDisplayPanelLinux(self)
        mSizer.Add(gv.iChartsPanel, flag=flagsR, border=2)
        return mSizer


    def _buildTlsCtrlBox(self):
        """ build the gateway control box.
        """
        flagsR, tColour = wx.LEFT | wx.ALIGN_CENTER_VERTICAL, wx.Colour(200, 200, 200)
        outBox = wx.StaticBox(self, -1, label=' TLS Connection ', size=(400, 200))
        outBox.SetForegroundColour(tColour)
        outBox.SetBackgroundColour(gv.iWeidgeClr)
        vbox = wx.StaticBoxSizer(outBox, wx.VERTICAL)
        
        self.tlsCountLb = wx.StaticText(outBox, label=" Total TLS Connection Number: 0 ")
        self.tlsCountLb.SetForegroundColour(tColour)

        vbox.Add(self.tlsCountLb, flag=flagsR, border=2)
        vbox.AddSpacer(5)


        self.tlsTF = wx.TextCtrl(outBox, size=(370, 350), style=wx.TE_MULTILINE)
        self.tlsTF .SetBackgroundColour(wx.Colour(200, 200, 210))
        vbox.Add(self.tlsTF, flag=flagsR, border=2)
        self.tlsTF.AppendText("----------- Gateway TLS connection information ---------- \n")
        vbox.AddSpacer(3)
        return vbox

    def _buildGwCtrlBox(self):
        """ build the gateway control box.
        """
        flagsR, tColour = wx.LEFT | wx.ALIGN_CENTER_VERTICAL, wx.Colour(200, 200, 200)
        outBox = wx.StaticBox(self, -1, label='Gateway Control', size=(400, 200))
        outBox.SetForegroundColour(tColour)
        outBox.SetBackgroundColour(gv.iWeidgeClr)
        vbox = wx.StaticBoxSizer(outBox, wx.VERTICAL)

        self.tlsCB = wx.CheckBox(outBox, label = ' Enable Gateway TLS Quantum Safty Check') 
        self.tlsCB.SetForegroundColour(tColour)
        self.tlsCB.SetValue(True)
        vbox.Add(self.tlsCB, flag=wx.EXPAND, border=2)
        vbox.AddSpacer(5)
        


        self.crypCB = wx.CheckBox(outBox, label = ' Enable Gateway Quantum Encryption Function') 
        self.crypCB.SetForegroundColour(tColour)
        self.crypCB.SetValue(True)
        vbox.Add(self.crypCB, flag=wx.EXPAND, border=2)
        vbox.AddSpacer(5)
        


        self.mapCB = wx.CheckBox(outBox, label = ' Show Gateway GPS Position on Google Map') 
        self.mapCB.SetForegroundColour(tColour)
        self.mapCB.SetValue(False)
        vbox.Add(self.mapCB, flag=wx.EXPAND, border=2)
        
        self.Bind(wx.EVT_CHECKBOX, self.onCheckBox)
        vbox.AddSpacer(3)
        return vbox

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
        flagsR, tColour = wx.LEFT | wx.ALIGN_CENTER_VERTICAL, wx.Colour(200, 200, 200)
        outBox = wx.StaticBox(self, -1, label=mainLabel, size=bSize)
        outBox.SetForegroundColour(tColour)
        outBox.SetBackgroundColour(gv.iWeidgeClr)
        bsizer = wx.StaticBoxSizer(outBox, layout)
        gs = wx.GridSizer(len(subLabels), 2, 5, 5) if layout == wx.VERTICAL else wx.GridSizer(
            1, len(subLabels)*2, 5, 5)
        valueLblist = []
        for val in subLabels:
            # Data label:
            titleLb = wx.StaticText(outBox, label=' %s' %val)
            gs.Add(titleLb, flag=flagsR, border=2)
            titleLb.SetForegroundColour(tColour)
            # Data value:
            dataLb = wx.StaticText(outBox, label=' -- ')
            dataLb.SetForegroundColour(tColour)
            valueLblist.append(dataLb)
            gs.Add(dataLb, flag=flagsR, border=2)
        bsizer.Add(gs, flag=wx.EXPAND, border=2)
        bsizer.AddSpacer(3)
        return (bsizer, valueLblist)


    def appendTlsInfo(self, tlsList):
        self.updateTlsDetail(' New TLS connection [idx : %s] ' %str(self.tlsCount))
        self.updateTlsDetail(' Time Stamp       : %s' %str(datetime.now().strftime("%m_%d_%Y_%H:%M:%S")))
        lbList = (' Src IP Address   : ',
                  ' Dest IP Address  : ',
                  ' TLS Version      : ',
                  ' TLS Cipher Suite : ')
        for i, val in enumerate(lbList):
            self.updateTlsDetail(val+str(tlsList[i]))
        
        if any(x in str(tlsList[i]) for x in ['AES', '128', 'ICDH', 'RSA', '3DES']):
            self.updateTlsDetail(' Quantum Safe     : %s' %'Not Safe')
        else:
            self.updateTlsDetail(' Quantum Safe     : %s' %'Safe')

        self.updateTlsDetail('--'*30)
        self.tlsCount += 1
        self.tlsCountLb.SetLabel(" Total TLS Connection Number : %s " %str(self.tlsCount))


    def updateTlsDetail(self, data):
        """ Update the data in the detail text field. Input 'None' will clear the 
            detail information text field.
        """
        if data is None:
            self.tlsTF.Clear()
        else:
            self.tlsTF.AppendText(" - %s \n" %str(data))

    def onCheckBox(self, event):
        """ Creat the google map gps position marked url and open the url by the 
            system default browser.
        """
        cb = event.GetEventObject()
        if cb.GetLabel() == ' Show Gateway GPS Position on Google Map' and self.mapCB.IsChecked():
            url = "http://maps.google.com/maps?z=12&t=m&q=loc:" + \
                str(1.2988)+"+"+str(103.836)
            print(url)
            webbrowser.open_new(url)
        
        if cb.GetLabel() == ' Enable Gateway Quantum Encryption Function':
            msg = 'T;1' if self.crypCB.IsChecked() else 'T;0'
            ip = self.gwInfoLbs[1].GetLabel()
            print('send message %s' %str(ip))
            self.gwClient.sendto(msg.encode('utf-8'), (gv.CT_IP[0], gv.CT_IP[1]))
            if gv.iGWTablePanel:
                gv.iGWTablePanel.updateSafe(self.crypCB.IsChecked())

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
        gwID, ipStr, version, dpdk_v, dpdk_c, dpdk_e, keyE,  gps = dataList
        if gwID in self.dataDict.keys(): return False
        dataVal = {
            'Idx':      self.gwCount, 
            'IpMac':    ipStr,
            'qcrypt':   'Enabled',
            'version':  version,
            'pdpkVer':  (dpdk_v, dpdk_c, dpdk_e),
            'keyExch':  keyE,
            'GPS':      gps,
            'LoginT':   datetime.now().strftime("%m_%d_%Y_%H:%M:%S"),
            'ReportT':  time.time(),
            'Data':     [[0]*self.dataSize[1] for i in range(self.dataSize[0])]
        }
        self.dataDict[gwID] = dataVal
        self.gwCount += 1
        gv.iGWTablePanel.addToGrid(gwID, dataVal)
        gv.iMainFrame.updateOwnInfo(2,[self.gwCount])
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
        if not gv.iMasterMode:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ipAddr = str(s.getsockname()[0])
            s.close()
            mode = 'MasterMode' if gv.iMasterMode else 'SlaveMode'
            gps = '[1.2988,103.836]'
            isp = 'Singtel'
            if gv.WIN_SYS:
                gv.iMainFrame.updateOwnInfo(0,(ipAddr, mode, gps, isp))
                downloadSp =  str(random.randint(200,400))+'.0Mbps'
                uploadSp = str(random.randint(100,250))+'.0Mbps'
                lantency = str(10+random.randint(1,20))+'ms'
                timeStr = datetime.now().strftime("%H:%M:%S")
                gv.iMainFrame.updateOwnInfo(1,(downloadSp, uploadSp, lantency, timeStr))
            else: 
                gv.iMainFrame.updateOwnInfo(0,(ipAddr, mode, gps, str(gv.SE_IP), isp, datetime.now().strftime("%H:%M:%S"), '0'))
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
        print('Dash board server terminated.')

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
        #self.terminate = True

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
        print('Gateway report server terminated.')

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
