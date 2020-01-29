#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        attackHost.py [python2.7/python3]
#
# Purpose:     This module is used to create a flask http server on port 5000 
#              to control the PLC-railway system attack.
# Author:      Yuancheng Liu
#
# Created:     2020/01/03
# Copyright:   YC @ Singtel Cyber Security Research & Development Laboratory
# License:     YC
#-----------------------------------------------------------------------------
import socket
from flask import Flask, redirect, url_for, request, render_template

TEST_MODE = True # Test mode flag - True: test on local computer

SEV_IP = ('127.0.0.1', 5005) if TEST_MODE else ('192.168.10.244', 5006)
BUFFER_SZ = 1024

# Init the UDP send server
crtClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Init the flask web server program.
app = Flask(__name__)

@app.route('/')
def index():
    # Add CSS in the html for flask is shown in this link: 
    # https://pythonhow.com/add-css-to-flask-website/
    return render_template('index.html')

#rendering the HTML page which has the button
@app.route('/json')
def json():
    return render_template('index.html')

#Start the gateway encryption.
@app.route('/enableEncrypt')
def startAtt1():
    print ("Start the gateway encryption.")
    if request.method == 'GET':
        msg = 'T;1'
        crtClient.sendto(msg.encode('utf-8'), SEV_IP)
    return ("nothing")

#Disable the gateway encryption
@app.route('/disableEncrypt')
def stopAtt1():
    print ("Disable the gateway encryption")
    if request.method == 'GET':
        msg = 'T;0'
        crtClient.sendto(msg.encode('utf-8'), SEV_IP)
    return ("nothing")

# Start the key exchange
@app.route('/exchangeKey')
def startAtt2():
    print ("Start the key exchange.")
    if request.method == 'GET':
        msg = 'T;2'
        crtClient.sendto(msg.encode('utf-8'), SEV_IP)
    return ("nothing")

if __name__ == '__main__':
    app.run(host= "0.0.0.0", debug=False, threaded=True)
   