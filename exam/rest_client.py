import requests
from time import time
import pandas as pd




class Rest_Client():

    def __init__(self) -> None:
        self.host = 'https://251b70cc-64ed-4269-9639-75a0d233eb14.deepnoteproject.com'
        self.decoded_labels = {
            1:'car',
            2:'bus',
            4:'motorcycle',
        }


    def get_zones(self):
        """
        DESCRIPTION:
            Get the list of zones stored in the dataset
        OUTPUT:
            zones:list = the list containing the zones names
        """
        response = requests.get(self.host + '/zones')
        if response.status_code == 200:
            zones = response.json()['zones']
            print(f'Asking for zones ... The zone names are {zones}.')
            return zones
        else:
            print('I tired to get the zones but i recived this error:')
            print(response.text)


            

    def get_devices(self):
        """
        DESCRIPTION:
            Get the list of zones stored in the dataset
        OUTPUT:
            devices:list = the list containing the devices mac_address
        """
        response = requests.get(self.host + '/devices')
        if response.status_code == 200:
            devices = response.json()['mac_addresses']
            print(f'Asking for mac addresses ... the mac addresses are {devices}.')
            return devices
        else:
            print('I tired to get the devices but I recived this error:')
            print(response.text)


    
    def get_devices_from_to(self, device, from_, to_):

        response = requests.get(f"{self.host}/device/{device}?from={from_}&to={to_}")
        data = pd.DataFrame()
        if response.status_code == 200:
            timestamps = response.json()['timestamps']
            numerical_labels = response.json()['labels']
            detections = [self.decoded_labels[int(z)] for z in numerical_labels]
            data['timestamps'] = timestamps
            data['detections'] = detections
            
        else:
            print(response.text)
        
        return data
    
    def get_zone_from_to(self, zone, from_, to_):

        response = requests.get(f"{self.host}/zone/{zone}?from={from_}&to={to_}")
        data = pd.DataFrame()
        if response.status_code == 200:
            timestamps = response.json()['timestamps'][0]
            zone_labels = response.json()['labels']
            numerical_labels = [label for mac in zone_labels for label in mac]
            detections = [self.decoded_labels[int(z)] for z in numerical_labels]
            data['timestamps'] = timestamps
            data['detections'] = detections
            
        else:
            print(response.text)
        
        return data
    
    def delete_device(self, device):
        response = requests.delete(self.host + f'/device/{device}')
        if response.status_code == 200:
            print('Item deleted.')
            return True
        else:
            print(response.text)
            exit()
            return False
        
    def delete_zone(self, zone):
        response = requests.delete(self.host + f'/zone/{zone}')
        if response.status_code == 200:
            print('Item deleted.')
            return True
        else:
            print(response.text)
            exit()
            return False


        

        
