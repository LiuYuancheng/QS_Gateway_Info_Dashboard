#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        geoLRun.py
#
# Purpose:     This module is used to convert a url to the IP address then 
#              find the GPS position it and draw it on the google map.
#
# Author:      Yuancheng Liu
#
# Created:     2019/10/14
# Copyright:   YC @ Singtel Cyber Security Research & Development Laboratory
# License:     YC
#-----------------------------------------------------------------------------
import os, sys
import wx

import gwDashboardGobal as gv
import gwDashboardPanel as gp

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class GeoLFrame(wx.Frame):
    """ URL/IP gps position finder main UI frame."""
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=(1900, 1060))
        #self.SetBackgroundColour(wx.Colour(18, 86, 133))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        gv.iTitleFont = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.SetSizer(self._buidUISizer())

#--GeoLFrame-------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the main UI Sizer. """
        flagsR = wx.RIGHT
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        mSizer.AddSpacer(5)
        vbox0 = wx.BoxSizer(wx.VERTICAL)
        self.titleLb = wx.StaticText(self, label="DashBoad Server Information")
        self.titleLb.SetFont(gv.iTitleFont)
        #self.titleLb.SetForegroundColour(wx.Colour(200,200,200))
        vbox0.Add(self.titleLb, flag=flagsR, border=2)

        vbox0.AddSpacer(5)
        vbox0.Add(self._buildOwnInfoSizer(), flag=flagsR, border=2)

        vbox0.AddSpacer(5)
        self.ownInfoPanel = gp.PanelOwnInfo(self)
        vbox0.Add(self.ownInfoPanel, flag=flagsR, border=2)

        mSizer.Add(vbox0, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 1060),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.gwtitleLb = wx.StaticText(self, label="GateWay data display")
        self.gwtitleLb.SetFont(gv.iTitleFont)
        #self.gwtitleLb.SetForegroundColour(wx.Colour(200,200,200))

        vbox1.Add(self.gwtitleLb, flag=flagsR, border=2)    
        vbox1.AddSpacer(5)
        vbox1.Add(self._buildGatewaySizer(), flag=flagsR, border=2)

        vbox1.AddSpacer(5)

        self.chartPanel = gp.ChartDisplayPanel(self)

        vbox1.Add(self.chartPanel, flag=flagsR, border=2)

        mSizer.Add(vbox1, flag=flagsR, border=2)


        return mSizer

    def _buildStateInfoBox(self, mainLabel, subLabels, bSize):
        """ Build a static box hold the data the list 
        """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        bsizer = wx.StaticBoxSizer(wx.StaticBox(
            self, -1, label=mainLabel, size=bSize), wx.VERTICAL)
        gs = wx.GridSizer(len(subLabels), 2, 5, 5)
        valueLblist = []
        for val in subLabels:
            gs.Add(wx.StaticText(self, label=val), flag=flagsR, border=2)
            dataLb = wx.StaticText(self, label=' -- ')
            valueLblist.append(dataLb)
            gs.Add(dataLb, flag=flagsR, border=2)
        bsizer.Add(gs, flag=flagsR, border=2)
        return (bsizer, valueLblist)

#--GeoLFrame-------------------------------------------------------------------
    def _buildOwnInfoSizer(self):
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        ownILbs =(' IP Address:', ' Running Mode:', ' GPS Position:', ' ISP Information:')
        bsizer1, self.ownInfoLbs = self._buildStateInfoBox("DashBoard Own Information", ownILbs, (250, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(20)
        netwLbs = (' DownLoad Speed [Mbps]:', ' Upload Speed [Mbps]:', ' Network Latency [ms]', ' Last Update Time:')
        bsizer2, self.networkLbs = self._buildStateInfoBox("Host Network Information", netwLbs, (400, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        return hSizer

#-----------------------------------------------------------------------------
    def _buildGatewaySizer(self):
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        gwILbs =(' Gateway IPAddr:', ' GateWay Mac:', ' GateWay GPS Pos:', ' Last Report Time:')
        bsizer1, self.gwInfoLbs = self._buildStateInfoBox("GateWay Information", gwILbs, (250, 300))
        hSizer.Add(bsizer1, flag=flagsR, border=2)
        hSizer.AddSpacer(20)
        gwDLbs =(' Data 0:', ' Data 1:', ' Data 2:', ' Data 3:')
        bsizer2, self.gwDataLbs = self._buildStateInfoBox("GateWay Data", gwDLbs, (650, 300))
        hSizer.Add(bsizer2, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        return hSizer

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        mainFrame = GeoLFrame(None, -1, gv.APP_NAME)
        mainFrame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
