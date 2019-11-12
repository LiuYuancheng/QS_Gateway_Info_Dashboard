import socket
import sys
import time
import random
import gwDashboardGobal as gv

SEV_IP = ('0.0.0.0', 5005) 

def main():
    gwClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("send the login message")
    gwClient.sendto('L;local01;192.168.0.1;4D-EC-4B-C2-71-48;[1.2966,103.7742]'.encode('utf-8'), ("127.0.0.1", SEV_IP[1]))
    while True:
        time.sleep(1)
        msg = 'D;local01;'+';'.join([str(random.randint(1,20)) for i in range(4)])
        print("msg: %s" %msg)
        gwClient.sendto(msg.encode('utf-8'), ("127.0.0.1", SEV_IP[1]))


if __name__== "__main__":
    main()
# Create a UDP socket





