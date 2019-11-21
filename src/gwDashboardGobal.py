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
import sys

dirpath = os.getcwd()
print("Current working directory is : %s" % dirpath)
APP_NAME = 'Quantum Safe Gateway Dashboard'
#WIN_SYS = sys.platform.startswith('win')
WIN_SYS = False

#------<IMAGES PATH>-------------------------------------------------------------
IMG_FD = 'img'
ICO_PATH = os.path.join(dirpath, IMG_FD, "gwIcon.ico")
NWSAM_PATH = os.path.join(dirpath, IMG_FD, "networkSample.png")
LOGO_PATH = os.path.join(dirpath, IMG_FD, "logo2.png")

GWOL_PATH = os.path.join(dirpath, IMG_FD, "gwOnline.png")
GWDE_PATH = os.path.join(dirpath, IMG_FD, "gwDelay.png")
GWFL_PATH = os.path.join(dirpath, IMG_FD, "gwoffline.png")
GWQE_PATH = os.path.join(dirpath, IMG_FD, "gwqenable.png")
GWQD_PATH = os.path.join(dirpath, IMG_FD, "qsdisable.png")

PTQS_PATH = os.path.join(dirpath, IMG_FD, "pctLb1.png")
PTGP_PATH = os.path.join(dirpath, IMG_FD, "pctLb2.png")

# dashboard own UDP server IP address.
SE_IP = ('0.0.0.0', 5005)       # Sensor server IP

#-------<GLOBAL PARAMTERS>-----------------------------------------------------
iMainFrame = None
iSimuMode = False    #simulation mode.
iDataMgr = None
iOwnID = 'Own_00'
iSelectedGW = None  # selected gateway ID
iTitleFont = None
iWeidgeClr = None
iMasterMode = False  # execution mode.
iGWTablePanel = None   # panel to do the control
iChartsPanel = None