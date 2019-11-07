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
        self.SetBackgroundColour(wx.Colour(18, 86, 133))
        #self.SetBackgroundColour(wx.Colour(200, 210, 200))
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
        self.titleLb.SetForegroundColour(wx.Colour(200,200,200))
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

        gs = wx.GridSizer(2, 2, 5, 5)
        self.downPanel = gp.PanelChart(self)
        gs.Add(self.downPanel,flag=flagsR, border=2)

        self.uploadPanel = gp.PanelChart(self)
        gs.Add(self.uploadPanel,flag=flagsR, border=2)

        self.throuthPanel = gp.PanelChart(self)
        gs.Add(self.throuthPanel,flag=flagsR, border=2)

        self.percetPanel = gp.PanelChart(self)
        gs.Add(self.percetPanel,flag=flagsR, border=2)

        mSizer.Add(gs, flag=flagsR, border=2)



        return mSizer

#--GeoLFrame-------------------------------------------------------------------
    def _buildOwnInfoSizer(self):
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        box1 = wx.StaticBox(self, -1, label="DashBoard Own Information", size= (350, 300))
        bsizer1 = wx.StaticBoxSizer(box1, wx.VERTICAL)
        self.ownIPLb = wx.StaticText(self, label="Own IP address:")
        self.ownIPLb.SetForegroundColour(wx.Colour(200,200,200))
        bsizer1.Add(self.ownIPLb, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        self.ownMDLb = wx.StaticText(self, label="Own Mode:")
        bsizer1.Add(self.ownMDLb, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        self.ownGPSLb = wx.StaticText(self, label="Own PPS Pos: []")
        bsizer1.Add(self.ownGPSLb, flag=flagsR, border=2)
        bsizer1.AddSpacer(5)
        self.ownISPLb = wx.StaticText(self, label="Own ISP:")
        bsizer1.Add(self.ownISPLb, flag=flagsR, border=2)
        hSizer.Add(bsizer1, flag=flagsR, border=2)

        hSizer.AddSpacer(20)
        box2 = wx.StaticBox(self, -1, label="Own Network Information", size= (350, 300))

        bsizer2 = wx.StaticBoxSizer(box2, wx.VERTICAL)
        self.dnSpLb = wx.StaticText(self, label="DownLoad speed: 0Mbps")
        bsizer2.Add(self.dnSpLb, flag=flagsR, border=2)
        bsizer2.AddSpacer(5)
        self.upSpLb = wx.StaticText(self, label="upload Speed: 0Mbps")
        bsizer2.Add(self.upSpLb, flag=flagsR, border=2)
        bsizer2.AddSpacer(5)
        self.lateLb = wx.StaticText(self, label="latency: 0ms")
        bsizer2.Add(self.lateLb, flag=flagsR, border=2)
        bsizer2.AddSpacer(5)
        self.updateTLb = wx.StaticText(self, label="last update time:")
        bsizer2.Add(self.updateTLb, flag=flagsR, border=2)
        hSizer.Add(bsizer2, flag=flagsR, border=2)
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
