from influxdb import InfluxDBClient
from datetime import datetime
import random
import time

# Connect to the 
client = InfluxDBClient('localhost', 8086, 'root', 'root', 'gatewayDB')


#Add the gatway information


json_body = [
    {
        "measurement": "gatewaytable",
        "tags": {
            "gatewayID": "Demo_GW_02",
            },
        "fields": {
            "ipAddr": "138.75.53.187",
            "gwVer":  "v1.1",
            "dpdk_v": "19.08",
            "dpdk_c": "Openssl",
            "dpdk_e": "AES-CBC 256",
            "keyE": "Custom",
            "GPS": "[1.2988,103.836]",
            "value": random.uniform(1.0, 100.0)
            }
    }]
# Insert the 
#client.write_points(json_body)
#exit()


tls_json = [
    {
        "measurement": "tlsConn",
        "tags": {
            "Name": "time",
            },
        "fields": {
            "src": "137.132.213.225",
            "dest": "136.132.213.218",
            "ver": "TLS 1.2", 
            "cipher": "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
            }
    }]
#client.write_points(tls_json)

for i in range(1000):
    print("insert a value")
    data_json = [
        {
            "measurement": "dataVals",
            "tags": {
                "Name": "time",
                },
            "fields": {
                "ival": random.uniform(100.0, 300.0),
                "oval": random.uniform(100.0, 300.0),
                "latVal": random.randint(10, 80),
                "pctVal": random.randint(10, 100),
                "frgVal": random.randint(1, 10),
                }
        }]

    client.write_points(data_json)
    time.sleep(2)

print('finished')
exit()




for i in range(14):
    json_body = [
    {
        "measurement": "temp",
        "tags": {
            "Name": "data1",
            },
        "fields": {
            "value": random.uniform(1.0, 100.0)
            }
    }]

    client.write_points(json_body)
    result = client.query('select * from temp;')
    time.sleep(1)

exit()

for i in range(14):
    json_body = [
    {
        "measurement": "cpu_load_short",
        "tags": {
            "host": "server01",
            "region": "us-west"
            },
        #"time": str(datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
        "time": '2019-11-27T16:35:47Z',
        "fields": {
            "value": random.uniform(1.0, 100.0)
            }
    }]
    client.write_points(json_body)
    result = client.query('select value from cpu_load_short;')
    #print("Result: {0}".format(result))
    time.sleep(1)





