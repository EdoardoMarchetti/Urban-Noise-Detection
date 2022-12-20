from time import sleep
import paho.mqtt.client as mqtt

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


for i in range(10): # in an Iot application we have a infinite loop
    print('Sending message....')
    client.publish(
        topic= 's001122',
        payload= f'Hello world {i}' #message to sent
    )
    sleep(1)