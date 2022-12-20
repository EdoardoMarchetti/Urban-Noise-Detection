import json
import uuid 
import redis
from redis.commands.json.path import Path

REDIS_HOST='redis-19577.c81.us-east-1-2.ec2.cloud.redislabs.com'
REDIS_PORT = 19577
REDIS_USER = 'default'
REDIS_PASSWORD = 'so7BaeUMztM1pEpKusnIWrk9PN0nSVdm'

redis_client = redis.Redis(
    host = REDIS_HOST,
    port = REDIS_PORT,
    username = REDIS_USER,
    password = REDIS_PASSWORD
    )

is_connected = redis_client.ping()
print(is_connected)

#redis_client.flushdb()

item = {
    'message':'Buy coffee',
    'completed':True
}

#Get a unique identifier
uid = uuid.uuid4()
print(uid)
#Load the item within the Redis DB
redis_client.json().set(
    f'todo:{uid}',
    Path.root_path(),
    item
)

#Get all the todo elements' keys 
keys = redis_client.keys(
    'todo:*'
)

print(keys)

#Get the item linked to the key
for key in keys:
    #decode the key
    key = key.decode()
    #Get the item
    item = redis_client.json().get(key)
    print(key, item)
