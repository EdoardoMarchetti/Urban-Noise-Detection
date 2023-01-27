from argparse import ArgumentParser
import psutil as ps
from time import sleep, time
import uuid
import paho.mqtt.client as mqtt
import json

parser = ArgumentParser()


parser.add_argument('--topic',
help='Message topic',
type=str,
default='s303873')

args = parser.parse_args()



#Client object
client =  mqtt.Client()

#-----------On connect callback-------------
def on_connect(
    client,
    userdata,
    flags,
    rc
):
    """
        When the client is connected to the 
        broker this callback is called.
    """
    print(f"Connected with result code {str(rc)}")
    
client.on_connect = on_connect #band the client to on_connect

#Connect the client to the message broker
client.connect(
    host='mqtt.eclipseprojects.io',
    port=1883
)

print('Sending......Type Ctrl+C to stop')
while True: 
    #Get the mac address
    mac_address = hex(uuid.getnode())
    #Get the data
    battery_level = ps.sensors_battery().percent
    power_plugged = int(ps.sensors_battery().power_plugged)
    #Prepare the timestamp
    timestamp = time()
    timestamp_in_ms = int(timestamp*1000)
    #Prepare the payload
    payload_dict = {
        'mac_address': mac_address,
        'timestamp':timestamp_in_ms,
        'battery_level':battery_level,
        'power_plugged':power_plugged
    }
    payload = json.dumps(payload_dict)
    #Publish the message
    client.publish(
        topic= args.topic,
        payload= payload #message to sent
    )
    sleep(1)