import socket
import sys
import time
import json
import random
import gwDashboardGobal as gv

SEV_IP = ('127.0.0.1', 5005)
GW_IN_JSON = 'tp01_in_info.json'
GW_OUT_JSON = 'tp01_out_info.json'
TEST_MODE = True
#GW_IN_JSON = 'income.json'
#GW_OUT_JSON = 'outcome.json'


def main():
    gwClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("load the configure file")
    
    dataDist = None
    with open('gwConfig.json', "r") as fh:
        lines = fh.readlines()
        line = lines[-1].rstrip()
        dataDist = json.loads(line)
    lat, lon = dataDist['GPS'].split(',')
    loginStr = ";".join(('L', dataDist['gatewayID'], lat, lon))
    print("send the login message: <%s>" %str(loginStr))

    gwClient.sendto(loginStr.encode('utf-8'), ("127.0.0.1", SEV_IP[1]))
    # load the configure file.

    while True:
        time.sleep(1)
        #msg = 'D;'+dataDist['gatewayID']+';' + \
        #    ';'.join([str(round(random.uniform(1, 100), 2)) for i in range(4)])
        random1 = None
        random2 = None

        with open(GW_IN_JSON, "r") as fh:
            lines = fh.readlines()
            idx = random.randint(0, len(lines)-1) if TEST_MODE else -1
            line = lines[idx].rstrip()
            random1 = json.loads(line)

        with open(GW_OUT_JSON, "r") as fh:
            lines = fh.readlines()
            idx = random.randint(0, len(lines)-1)  if TEST_MODE else -1
            line = lines[idx].rstrip()
            random2 = json.loads(line)

        msg = ';'.join( ('D', dataDist['gatewayID'], 
                        str(random1["throughput_mbps"]),
                        str(random2["throughput_mbps"]),
                        str(random1["percent_enc"]) ))
        print("msg: %s" % msg)
        gwClient.sendto(msg.encode('utf-8'), ("127.0.0.1", SEV_IP[1]))

if __name__== "__main__":
    main()
# Create a UDP socket





