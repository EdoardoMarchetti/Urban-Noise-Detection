from time import sleep, time
from datetime import datetime

import argparse as ap
import psutil as ps
import uuid
import redis
import numpy as np


parser = ap.ArgumentParser()

parser.add_argument('--host', help='the Redis Cloud host.', type = str, default= 'redis-19577.c81.us-east-1-2.ec2.cloud.redislabs.com')
parser.add_argument('--port', help='the Redis Cloud port.', type = int, default = 19577)
parser.add_argument('--user', help='the Redis Cloud username.', type = str, default = 'default')
parser.add_argument('--password', help='the Redis Cloud password.', type = str, default = 'so7BaeUMztM1pEpKusnIWrk9PN0nSVdm')

args = parser.parse_args()


DELTA_t = 1 #every DELTA_t seconds a record is stored
RECORDS_IN_A_MB = 655360                               #1024**2 (bytes in a MB)/1.6 (bytes per record)
NO_AGGREGATE_RET_TIME = int(RECORDS_IN_A_MB*5*1e3)     #each record corresponds to one second 
                                                       #-> just multiply the record in a MB by 5 then by 1e3 to obtain the ms
AGGREGATE_RET_TIME = int(RECORDS_IN_A_MB*24*60*60*1e3) #each record corresponds to 1 day 
                                                       #-> multiply the number of records in a MB by the ms in a day (1e3*60*60*24)

#Get redis_client
redis_client = redis.Redis(host= args.host, \
                           port= args.port,\
                           username= args.user,\
                           password= args.password)
print('Is redis connected? ', redis_client.ping())

redis_client.flushdb()

#Get the mac_address
mac_address = hex(uuid.getnode())
print('MAC address: ', mac_address)

#Create the timesries_name
mac_battery = f'{mac_address}:battery_level'
mac_power = f'{mac_address}:power_plugged'
mac_power_in_s = f'{mac_address}:plugged_secods'


#Create the timeseries
day_in_msec = int(24*60*60*1e3) #24 hours in ms
try:

    redis_client.ts().create(mac_battery, uncompressed = False, chunk_size=128)                                                                                        #timeseries for battery level \in [0,100]
    redis_client.ts().create(mac_power, uncompressed = False, chunk_size=128)                                                                                          #timeseries to check if battery is plugged \in {0,1}
    redis_client.ts().create(mac_power_in_s, uncompressed = False, chunk_size=128)                                                                                     #timeseires that automatically stores how many seconds the power have been plugged in the last 24 hours 
 
    redis_client.ts().alter(mac_battery, retention_msec= NO_AGGREGATE_RET_TIME*5)
    redis_client.ts().alter(mac_power, retention_msec= NO_AGGREGATE_RET_TIME*5)
    redis_client.ts().alter(mac_power_in_s, retention_msec= AGGREGATE_RET_TIME)

    #Create the rule to sum the data
    redis_client.ts().createrule(mac_power, mac_power_in_s, aggregation_type='sum', bucket_size_msec=day_in_msec)    
except redis.ResponseError:
    pass


i = 0
minutes = 0
record_per_minute = list()
start = 0
timestamp = 0

while True:

        #Prepare the timestamp
        timestamp = time()
        start = timestamp if start == 0 else start
        timestamp_in_ms = int(timestamp*1000)
        formatted_datetime = datetime.fromtimestamp(timestamp)

        #Get the data
        battery_level = ps.sensors_battery().percent
        power_plugged = int(ps.sensors_battery().power_plugged)

        #Store the data on redis
        redis_client.ts().add(mac_battery, timestamp= timestamp_in_ms, value= battery_level)
        redis_client.ts().add(mac_power, timestamp= timestamp_in_ms, value= power_plugged)

        print(f'Total stored records {i}')
        print(f'Redis battery record: {redis_client.ts().get(mac_battery)}')
        print(f'Redis power record: {redis_client.ts().get(mac_power)}')
        print(f'Redis power seconds record: {redis_client.ts().get(mac_power_in_s)}')

        print()
        i += 1
        sleep(DELTA_t)





