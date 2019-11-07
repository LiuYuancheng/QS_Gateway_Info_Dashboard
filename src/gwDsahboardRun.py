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
        wx.Frame.__init__(self, parent, id, title, size=(1150, 560))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        self.SetSizer(self._buidUISizer())

#--GeoLFrame-------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the main UI Sizer. """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        mSizer.AddSpacer(5)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(-1, 560),
                                 style=wx.LI_VERTICAL), flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        return mSizer
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        mainFrame = GeoLFrame(None, -1, gv.APP_NAME)
        mainFrame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
