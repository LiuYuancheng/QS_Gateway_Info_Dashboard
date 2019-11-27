from influxdb import InfluxDBClient
from datetime import datetime
import random
import time

# Connect to the 
client = InfluxDBClient('localhost', 8086, 'root', 'root', 'gatewayDB')



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





