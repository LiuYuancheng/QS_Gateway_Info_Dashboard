#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        gwDashboardPanel.py
#
# Purpose:     This module is used to create the control or display panel for
#              gateway dashboard system.
# Author:      Yuancheng Liu
#
# Created:     2019/10/14
# Copyright:   YC @ Singtel Cyber Security Research & Development Laboratory
# License:     YC
#-----------------------------------------------------------------------------
import wx
import time
import wx.grid
import wx.lib.sized_controls as sc
from datetime import datetime

import gwDashboardGobal as gv

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelGwInfo(wx.Panel):
    """ gateway information."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.selectedID = ''
        self.SetSizer(self._buidUISizer())

#-----------------------------------------------------------------------------
    def _buidUISizer(self):
        """ Build the panel's main UI Sizer. """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        mSizer = wx.BoxSizer(wx.VERTICAL)
        # Row idx 0: gateway title line.
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.gwLabel = wx.StaticText(self, label="Reported Gateway Information")
        self.gwLabel.SetFont(gv.iTitleFont)
        hbox.Add(self.gwLabel, flag=flagsR, border=2)
        hbox.AddSpacer(80)
        self.gwStLb = wx.StaticText(self, label="[Online/Total]: 0/0")
        hbox.Add(self.gwStLb, flag=wx.ALIGN_BOTTOM, border=2)
        hbox.AddSpacer(20)
        hbox.Add(wx.StaticBitmap(self, -1, wx.Bitmap(gv.NWSAM_PATH, wx.BITMAP_TYPE_ANY)),flag=flagsR, border=2)
        mSizer.Add(hbox, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        # Row idx 1: Add the client connection grid.
        collumNum = 8
        self.grid = wx.grid.Grid(self, -1)
        self.grid.CreateGrid(8, collumNum)
        # Set the Grid size.
        self.grid.SetRowLabelSize(40)
        lbList = ((20,  ' '), # connected indicator.
                  (80,  'GateWay_ID'),
                  (100, 'IP_Address'),
                  (60,  'GW_Ver'),
                  (80,  'DPDK_Ver'),
                  (100, 'GPS_Position'),
                  (120, 'Login_Time'),
                  (110, 'Last_Report_Time'))
        for i, val in enumerate(lbList):
            self.grid.SetColSize(i, val[0])
            self.grid.SetColLabelValue(i, val[1])
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClick)
        mSizer.Add(self.grid, flag=flagsR, border=2)
        mSizer.AddSpacer(5)
        # Row idx 2: Display active.
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self, label="Selected GateWay: "), flag=flagsR, border=2)
        self.selGwlb = wx.StaticText(self, label="GateWay ID[xxx.xxx.xxx.xxx]")
        hbox1.Add(self.selGwlb, flag=flagsR, border=2)
        hbox1.AddSpacer(250)
        self.trackAcBt = wx.Button(self, label='Show the gateway detail data', size=(220, 22))
        self.trackAcBt.Bind(wx.EVT_BUTTON, self.onShowGw)
        hbox1.Add(self.trackAcBt, flag=flagsR, border=2)
        mSizer.Add(hbox1, flag=flagsR, border=2)
        return mSizer

#-----------------------------------------------------------------------------
    def addToGrid(self, dataID, dataDict):
        """ Add a new data in the grid."""
        rowIdx = dataDict['Idx']
        dataSequence = (str(dataID),
                        str(dataDict['IpMac']),
                        str(dataDict['version']),
                        str(dataDict['pdpkVer']),
                        str(dataDict['GPS']),
                        str(dataDict['LoginT']),
                        str(dataDict['ReportT']))
        for i in range(1, 8):
            self.grid.SetCellValue(rowIdx, i, dataSequence[i-1])
        self.grid.Refresh(True)

#-----------------------------------------------------------------------------
    def onLeftClick(self, event):
        """ Update the gate selection part when user left click the row title.
        """
        row_index = event.GetRow()
        if row_index >= 0:
            self.grid.SelectRow(row_index)  # High light the row.
            dataId = self.grid.GetCellValue(row_index, 1)
            dataIp = self.grid.GetCellValue(row_index, 2)
            if dataId: self.selGwlb.SetLabel(dataId+' [ '+dataIp+' ]')
            self.selectedID = dataId

#-----------------------------------------------------------------------------
    def onShowGw(self, event):
        gv.iSelectedGW =self.selectedID
        gv.iMainFrame.updateGateWayInfo()

#-----------------------------------------------------------------------------
    def updateGrid(self):
        """ update the grid report time data and connection indicator."""
        for (_, item) in gv.iDataMgr.getDataDict('items()'):
            idx = item['Idx']
            rpTime = item['ReportT']
            deltT = time.time() - rpTime
            if  deltT > 10:
                self.grid.SetCellBackgroundColour(idx, 0, wx.Colour('RED'))
            elif 5 < deltT <= 10:
                self.grid.SetCellBackgroundColour(idx, 0, wx.Colour('YELLOW'))
            else:
                self.grid.SetCellBackgroundColour(idx, 0, wx.Colour('GREEN'))
            self.grid.SetCellValue(idx, 7, str(rpTime))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelChart(wx.Panel):
    """ chart to display data based on time.
    """
    def __init__(self, parent, recNum=20, yRange=1 pnlSize=(540, 320)):
        """ Init the panel."""
        wx.Panel.__init__(self, parent, size=pnlSize)
        self.SetBackgroundColour(wx.Colour(230, 230, 230))
        self.title = ''     
        self.yLabel = ''
        self.lColor = (82, 153, 85)
        self.panelSize = pnlSize
        self.recNum = recNum
        self.yRange = yRange
        self.updateFlag = True  # flag whether we update the diaplay area
        self.data = [0] * self.recNum
        self.times = ('-80', '-70', '-60', '-50','-40', '-30', '-20', '-10', '0')
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetDoubleBuffered(True)

    def setData(self, dataList):
        self.data = dataList

    def setChartCmt(self, title, yLaber, lColor):
        self.title = title
        self.yLabel = yLaber
        self.lColor = lColor


#--PanelChart--------------------------------------------------------------------
    def appendData(self, number):
        """ Append the data into the data hist list.
            numsList Fmt: [(current num, average num, final num)]
        """
        self.data.append(number)
        self.data.pop(0) # remove the first oldest recode in the list.
    
#--PanelChart--------------------------------------------------------------------
    def drawBG(self, dc):
        """ Draw the line chart background."""
        (w, h) = self.panelSize
        zx, zy = 40, h-40
        dc.SetPen(wx.Pen('WHITE'))
        dc.DrawRectangle(40, 40, w-80, h-80)
        # DrawTitle:
        font = dc.GetFont()
        font.SetPointSize(8)
        dc.SetFont(font)
        dc.DrawText(self.title, w//2-40, 30)

        # Draw Axis and Grids:(Y-people count X-time)
        dc.SetPen(wx.Pen('#D5D5D5')) #dc.SetPen(wx.Pen('#0AB1FF'))
        dc.DrawLine(zx, zy, w-100, zy)
        dc.DrawLine(zx, zy, zx, 100)
        dc.DrawText('time[sec]', w-90, zy)
        dc.DrawText(self.yLabel, 10, 60)

        offsetY = (h-100)//10
        
        for i in range(10):
            dc.DrawLine(zx, i*offsetY, w-100, i*offsetY)
            dc.DrawText(str(i*self.yRange).zfill(2), 15, i*offsetY+5)


        for i in range(2, 22, 2):
            dc.DrawLine(2, i*offsetY, w-100, i*offsetY) # Y-Grid
            dc.DrawLine(2, i*offsetY, -5, i*offsetY)  # Y-Axis
            dc.DrawText(str(i).zfill(2), -25, i*offsetY+5)  # format to ## int, such as 02
        offsetX = (w-40)//len(self.times)

        for i in range(len(self.times)): 
            dc.DrawLine(i*offsetX, -5, i*offsetX, h-100) # X-Grid
            dc.DrawText(self.times[i], i*offsetX-10, -5)
        
#--PanelChart--------------------------------------------------------------------
    def drawFG(self, dc):
        """ Draw the front ground data chart line."""
        # draw item (Label, color)
        (w, h) = self.panelSize
        (label, color) = ('data1', '#0AB1FF')
        dc.SetPen(wx.Pen(color, width=2, style=wx.PENSTYLE_SOLID))
        dc.DrawText('data:'+str(self.data[-1]), w-150, h-80)
        #dc.DrawSpline([(i*20, self.data[i]*10) for i in range(self.recNum)])
        gdc = wx.GCDC(dc)
        #self.lColor = (82, 153, 85)
        (r, g, b),  alph = self.lColor, 128 # half transparent alph
        gdc.SetBrush(wx.Brush(wx.Colour(r, g, b, alph)))
        delta = (w-100)//20
        poligon =[(-1, 0)]+[(i*delta, self.data[i]*10) for i in range(self.recNum)]+[(w-100, -1)]
        gdc.DrawPolygon(poligon)

#--PanelChart--------------------------------------------------------------------
    def updateDisplay(self, updateFlag=None):
        """ Set/Update the display: if called as updateDisplay() the function will 
            update the panel, if called as updateDisplay(updateFlag=?) the function 
            will set the self update flag.
        """
        if updateFlag is None and self.updateFlag: 
            self.Refresh(True)
            self.Update()
        else:
            self.updateFlag = updateFlag

#--PanelChart--------------------------------------------------------------------
    def OnPaint(self, event):
        """ Main panel drawing function."""
        dc = wx.PaintDC(self)
        # set the axis orientation area and fmt to up + right direction.
        # This only work in WIndows.
        #(w, h) = self.panelSize
        #dc.SetDeviceOrigin(40, h-40)
        #dc.SetAxisOrientation(True, True)
        self.drawBG(dc)
        self.drawFG(dc)


class ChartDisplayPanel(sc.SizedScrolledPanel):
    """ chart display panel.
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        sc.SizedScrolledPanel.__init__(self, parent, size=(1110, 700))
        #self.SetBackgroundColour(wx.Colour(200, 200, 210))
        self.SetBackgroundColour(wx.Colour(18, 86, 133))
        self.SetSizer(self._buidUISizer())

    def _buidUISizer(self):
        """ Build the panel's main UI Sizer. """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        mSizer = wx.BoxSizer(wx.VERTICAL)
        mSizer.AddSpacer(10)
        gs = wx.GridSizer(2, 2, 5, 5)
        self.downPanel = PanelChart(self)
        gs.Add(self.downPanel,flag=flagsR, border=2)
        self.downPanel.setChartCmt('Income Throughput Speed', 'Mbps',(200, 0, 0))
        self.uploadPanel = PanelChart(self)
        gs.Add(self.uploadPanel,flag=flagsR, border=2)
        self.uploadPanel.setChartCmt('Outcome Throughput Speed', 'Mbps',(82, 153, 85))
        self.throuthPanel = PanelChart(self)
        gs.Add(self.throuthPanel,flag=flagsR, border=2)
        self.throuthPanel.setChartCmt('Income Packet Encryption Pct', '%',(0, 0, 200))
        self.percetPanel = PanelChart(self)
        gs.Add(self.percetPanel,flag=flagsR, border=2)
        self.percetPanel.setChartCmt('Outcome Packet Encryption Pct', '%', (120, 120, 120))
        mSizer.Add(gs, flag=flagsR, border=2)
        mSizer.AddSpacer(50)
        return mSizer

    def updateData(self, dataList):
        self.downPanel.setData(dataList[0])
        self.uploadPanel.setData(dataList[1])
        self.throuthPanel.setData(dataList[2])
        self.percetPanel.setData(dataList[3])

    def updateDisplay(self):
        self.downPanel.updateDisplay()
        self.uploadPanel.updateDisplay()
        self.throuthPanel.updateDisplay()
        self.percetPanel.updateDisplay()


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelCtrl(wx.Panel):
    """ Function control panel."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.gpsPos = None
        self.SetSizer(self._buidUISizer())
    
#--PanelCtrl-------------------------------------------------------------------
    def _buidUISizer(self):
        """ build the control panel sizer. """
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        ctSizer = wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        ctSizer.AddSpacer(5)
        # Row idx 0: show the search key and map zoom in level.
        hbox0.Add(wx.StaticText(self, label="Search key : ".ljust(15)),
                  flag=flagsR, border=2)
        self.scKeyCB = wx.ComboBox(
            self, -1, choices=['IPv4', 'URL'], size=(60, 22), style=wx.CB_READONLY)
        self.scKeyCB.SetSelection(0)
        hbox0.Add(self.scKeyCB, flag=flagsR, border=2)
        hbox0.AddSpacer(20)
        hbox0.Add(wx.StaticText(
            self, label="Map ZoomIn Level : ".ljust(20)), flag=flagsR, border=2)
        self.zoomInCB = wx.ComboBox(
            self, -1, choices=[str(i) for i in range(10, 15)], size=(60, 22), style=wx.CB_READONLY)
        self.zoomInCB.SetSelection(3)
        hbox0.Add(self.zoomInCB, flag=flagsR, border=2)
        ctSizer.Add(hbox0, flag=flagsR, border=2)
        ctSizer.AddSpacer(5)
        # Row idx 1: URL/IP fill in text field.
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self, label="IP/URL : "),
                  flag=flagsR, border=2)
        self.scValTC = wx.TextCtrl(self, size=(220, 22))
        hbox1.Add(self.scValTC, flag=flagsR, border=2)
        hbox1.AddSpacer(2)
        self.searchBt = wx.Button(self, label='Search', size=(55, 22))
        self.searchBt.Bind(wx.EVT_BUTTON, self.onSearch)
        hbox1.Add(self.searchBt, flag=flagsR, border=2)
        ctSizer.Add(hbox1, flag=flagsR, border=2)
        ctSizer.AddSpacer(5)
        # Row idx 2: url parse detail information display area.
        ctSizer.Add(wx.StaticText(self, label="Detail Information : "),
                    flag=flagsR, border=2)
        ctSizer.AddSpacer(5)
        self.detailTC = wx.TextCtrl(
            self, size=(330, 300), style=wx.TE_MULTILINE)
        ctSizer.Add(self.detailTC, flag=flagsR, border=2)
        ctSizer.AddSpacer(5)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.clearBt = wx.Button(self, label='Clear', size=(70, 22))
        self.clearBt.Bind(wx.EVT_BUTTON, self.onClear)
        hbox2.Add(self.clearBt, flag=flagsR, border=2)
        hbox2.AddSpacer(10)
        self.searchBt = wx.Button(
            self, label='Mark GPS position on google map >>', size=(250, 22))
        self.searchBt.Bind(wx.EVT_BUTTON, self.onMark)
        hbox2.Add(self.searchBt, flag=flagsR, border=2)
        ctSizer.Add(hbox2, flag=flagsR, border=2)
        return ctSizer

#--PanelCtrl-------------------------------------------------------------------
    def onClear(self, event):
        """ Clear all the text field."""
        self.updateDetail(None)

#--PanelCtrl-------------------------------------------------------------------
    def onMark(self, event):
        """ Creat the google map gps position marked url and open the url by the 
            system default browser.
        """
        url = "http://maps.google.com/maps?z=12&t=m&q=loc:" + \
            str(self.gpsPos[0])+"+"+str(self.gpsPos[1])
        webbrowser.open_new(url)
        webbrowser.get('chrome').open_new(url)

#--PanelCtrl-------------------------------------------------------------------
    def onSearch(self, event):
        """ Convert a url to the IP address, find the GPS position of the IP 
            address and draw it on the map.
        """
        self.updateDetail("----- %s -----" % str(datetime.today()))
        scIPaddr = val = self.scValTC.GetValue()
        # Convert the URL to ip address if needed.
        if self.scKeyCB.GetSelection():
            url = str(
                val.split('//')[1]).split('/')[0] if 'http' in val else val.split('/')[0]
            self.updateDetail(url)
            scIPaddr = gv.iGeoMgr.urlToIp(url)
        if gv.iGeoMgr.checkIPValid(scIPaddr):
            self.updateDetail(scIPaddr)
        else:
            self.updateDetail(" The IP address [%s] is invalid." %str(scIPaddr))
            return None
        # get the gps pocition:
        self.gpsPos = (lat, lon) = gv.iGeoMgr.getGpsPos(scIPaddr)
        self.updateDetail('Server GPS position[%s]' % str((lat, lon)))
        (dcId, dist) = gv.iDCPosMgr.fineNear(self.gpsPos)
        self.updateDetail('Nearest AWS data center[%s]' % str(dcId))
        self.updateDetail('Distance [%s] Km' % str(dist))
        # get the position google map and update the display
        bitmap = gv.iGeoMgr.PIL2wx(gv.iGeoMgr.getGoogleMap(
            lat, lon, 3, 2, int(self.zoomInCB.GetValue())))
        if gv.iMapPanel:
            gv.iMapPanel.updateBitmap(bitmap)
            gv.iMapPanel.updateDisplay()
        self.updateDetail("----- Finished ----- \n")

#--PanelCtrl-------------------------------------------------------------------
    def updateDetail(self, data):
        """ Update the data in the detail text field. Input 'None' will clear the 
            detail information text field.
        """
        if data is None:
            self.scValTC.Clear()
            self.detailTC.Clear()
        else:
            self.detailTC.AppendText(" - %s \n" %str(data))





