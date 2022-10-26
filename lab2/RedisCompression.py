import redis
from requests import delete
from Redis_client import Redis_Client
from time import time, sleep

redis_client = Redis_Client().get_client()
print("Is connected? ", redis_client.ping())

TEMPERATURE ='temperature'
TEMPERATURE_UNC = 'temperature_unc'

redis_client.delete(TEMPERATURE) #delete the tameseries related to the key

try:
    redis_client.ts().create(TEMPERATURE, chunk_size = 128)
except redis.ResponseError:
    pass


print("==========TEMPERATURE INFO===============")
print('Memory (bytes)', redis_client.ts().info(TEMPERATURE).memory_usage)
print('#samples :',redis_client.ts().info(TEMPERATURE).total_samples)
print('#chunks :',redis_client.ts().info(TEMPERATURE).chunk_count)

try:
    redis_client.ts().create(TEMPERATURE_UNC, chunk_size = 128, uncompressed = True)
except redis.ResponseError:
    pass

for i in range(100):
    timestamp_ms = int(time()*1000)
    redis_client.ts().add(TEMPERATURE_UNC, timestamp_ms, 25 + i/50)
    sleep(0.1)

print("==========TEMPERATURE INFO===============")
print('Memory (bytes)', redis_client.ts().info(TEMPERATURE_UNC).memory_usage)
print('#samples :',redis_client.ts().info(TEMPERATURE_UNC).total_samples)
print('#chunks :', redis_client.ts().info(TEMPERATURE_UNC).chunk_count)



day_ms = 24*60*60*1000
redis_client.ts().alter(TEMPERATURE, retention_msec = day_ms)

TEMPERATURE_AVG = 'temperature_avg'

try:
    redis_client.ts().create(TEMPERATURE_AVG, chunk_size = 128, uncompressed = True)
except redis.ResponseError:
    pass

bucket_duration_ms = 1000
redis_client.ts().createrule(TEMPERATURE, TEMPERATURE_AVG,
                            aggregation_type= 'avg',
                            bucket_size_msec= bucket_duration_ms)

for i in range(100):
    timestamp_ms = int(time()*1000)
    redis_client.ts().add(TEMPERATURE_UNC, timestamp_ms, 25 + i/50)
    sleep(0.1)

print("==========UPDATE TEMPERATURE INFO===============")
print('Memory (bytes)', redis_client.ts().info(TEMPERATURE).memory_usage)
print('#samples :',redis_client.ts().info(TEMPERATURE).total_samples)
print('#chunks :', redis_client.ts().info(TEMPERATURE).chunk_count)

print("==========UPDATE TEMPERATURE INFO===============")
print('Memory (bytes)', redis_client.ts().info(TEMPERATURE_AVG).memory_usage)
print('#samples :',redis_client.ts().info(TEMPERATURE_AVG).total_samples)
print('#chunks :', redis_client.ts().info(TEMPERATURE_AVG).chunk_count)