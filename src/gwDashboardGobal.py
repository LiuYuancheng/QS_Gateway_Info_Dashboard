#-----------------------------------------------------------------------------
# Name:        gwDashboardGobal.py
#
# Purpose:     This module is used as a local config file to set the constants, 
#              global parameters which will be used in the other modules.
#              
# Author:      Yuancheng Liu
#
# Created:     2019/11/09
# Copyright:   YC @ Singtel Cyber Security Research & Development Laboratory
# License:     YC
#-----------------------------------------------------------------------------
import os

dirpath = os.getcwd()
print("Current working directory is : %s" % dirpath)
APP_NAME = 'GateWay DashBoat'

#------<IMAGES PATH>-------------------------------------------------------------
IMG_FD = 'img'
ICO_PATH = os.path.join(dirpath, IMG_FD, "gwIcon.ico")
NWSAM_PATH = os.path.join(dirpath, IMG_FD, "networkSample.png")

# dashboard own UDP server IP address.
SE_IP = ('0.0.0.0', 5005)       # Sensor server IP

#-------<GLOBAL PARAMTERS>-----------------------------------------------------
iMainFrame = None
iDataMgr = None
iOwnID = 'Own_00'
iSelectedGW = None  # selected gateway ID
iTitleFont = None
iMasterMode = False  # execution mode.
iCtrlPanel = None   # panel to do the control