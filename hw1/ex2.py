from time import sleep, time
from datetime import datetime

import argparse as ap
import psutil as ps
import uuid
import redis


parser = ap.ArgumentParser()

parser.add_argument('--host', help='the Redis Cloud host.', type = str, required= True)
parser.add_argument('--port', help='the Redis Cloud port.', type = int, required= True)
parser.add_argument('--user', help='the Redis Cloud username.', type = str, required= True)
parser.add_argument('--password', help='the Redis Cloud password.', type = str, required= True)

args = parser.parse_args()


DELTA_t = 1 #every DELTA_t seconds a record is stored

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
bucket_size_msec = 3000 #24 hours in ms
try:

    redis_client.ts().create(mac_battery, uncompressed = False, chunk_size=128)                                                                                        #timeseries for battery level \in [0,100]
    redis_client.ts().create(mac_power, uncompressed = False, chunk_size=128)                                                                                          #timeseries to check if battery is plugged \in {0,1}
    redis_client.ts().create(mac_power_in_s, uncompressed = False, chunk_size=128)                                                                                     #timeseires that automatically stores how many seconds the power have been plugged in the last 24 hours 
 
    redis_client.ts().alter(mac_battery,retention_msec=bucket_size_msec*100)
    redis_client.ts().alter(mac_power,retention_msec=bucket_size_msec*100)
    redis_client.ts().alter(mac_power_in_s, retention_msec=bucket_size_msec*100)

    #Create the rule to sum the data
    redis_client.ts().createrule(mac_power, mac_power_in_s, aggregation_type='sum', bucket_size_msec=bucket_size_msec)    
except redis.ResponseError:
    pass


i = 0
while True:
    #Prepare the timestamp
    timestamp = time()
    timestamp_in_ms = int(timestamp*1000)
    formatted_datetime = datetime.fromtimestamp(timestamp)

    #Get the data
    battery_level = ps.sensors_battery().percent
    power_plugged = int(ps.sensors_battery().power_plugged)

    #Store the data on redis
    redis_client.ts().add(mac_battery, timestamp= timestamp_in_ms, value= battery_level)
    redis_client.ts().add(mac_power, timestamp= timestamp_in_ms, value= power_plugged)

    print(f'Stored records: at {i*1e3}ms')
    print(f'Redis battery record: {redis_client.ts().get(mac_battery)}')
    print(f'Redis power record: {redis_client.ts().get(mac_power)}')
    print(f'Redis power seconds record: {redis_client.ts().get(mac_power_in_s)}')

    print()
    i += 1
    sleep(DELTA_t)
