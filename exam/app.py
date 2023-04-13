import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import time

from datetime import date, datetime, timedelta

from rest_client import Rest_Client


#init the rest client object
rest_client = Rest_Client()



#Write the title
st.title('Urban Noise Monitoring')
st.title('User interface')
#Write the app description
st.markdown("""
    This is a user inteface to work with data collected trough the urban noise monitoring system.
""")   


st.write("---")

st.markdown(
    """
    ### Devices
    Select the devices that you are interested in 
    """
)
#Load the devices mac_addresses
#get_devices = st.cache_data(func = rest_client.get_devices)
devices = sorted(rest_client.get_devices())


#Multiple choice
selected_devices = st.multiselect(
    label='Devices',
    options=devices, #list of possible options
    default=devices,  #as default value insert all the teams
    on_change=rest_client.get_devices,
    key='devices_selection'
)

#Date selection
dates = st.date_input(label='Date Range: ',
            value=(date.today(), date.today()+timedelta(days=1)),
            key='#date_range',
            help="The start and end date time")




#Convert into datetime
datetimes = [datetime.combine(d, datetime.min.time()) for d in dates]
from_ = int(datetime.timestamp(datetimes[0])*1000)
to_ = int(from_+8.64e+7 if (len(datetimes) == 1) or (datetimes[0]==datetimes[1]) else datetime.timestamp(datetimes[1])*1000)  



#For each device plot the distribution and the occurances per day
if len(selected_devices) >0 :
    device_without_data = []
    device_with_data = []
    
    for device in selected_devices:
        data = rest_client.get_devices_from_to(device, from_, to_)
        if len(data) > 0:
            #print(device,'\n',data)
            data['date'] = pd.to_datetime(data['timestamps'], unit='ms')
            temp = data.groupby(by=[pd.Grouper(key='date',freq='1Min'),'detections']).count()
            pivoted = pd.pivot_table(temp, values='timestamps', index='date', columns='detections')
            device_with_data.append((device, [data['detections'].value_counts().sort_index(), pivoted]))
        else:
            device_without_data.append(device)
    
    if len(device_with_data) > 0:
        fig, (axs_device) = plt.subplots(len(device_with_data), 2)

        if axs_device.shape == (2,):
            axs_device =[axs_device]

        for (device, [distribution, pivoted]), [line, bar] in zip(device_with_data, axs_device):
            #print(f'Device info: {device}')
            
            distribution.plot.bar(ax = bar, title = f'{device} total detections by class')
            pivoted.plot.line(ax=line, title='Detections per minute')


        plt.tight_layout()
        st.pyplot(fig)
    if len(device_without_data) > 0:
        st.write(f'Devices {device_without_data} have not data for the selected time interval')
else:
    st.write('Please select at least one device')


st.write("---")

st.markdown(
    """
    ### Zones
    Select the zones that you are interested in 
    """
)
#Load the devices mac_addresses
#get_zones = st.cache_data(func = rest_client.get_zones)
zones = sorted(rest_client.get_zones())

#Multiple choice
selected_zones = st.multiselect(
    label='Zones',
    options=zones, #list of possible options
    default=zones,  #as default value insert all the teams,
    on_change=rest_client.get_zones,
    key='zones_selection'
)

#Date selection
zones_dates = st.date_input(label='Date Range: ',
            value=(date.today(), date.today()+timedelta(days=1)),
            key='#date_zone',
            help="The start and end date time")

#Convert into datetime
datetimes = [datetime.combine(d, datetime.min.time()) for d in zones_dates]
from_ = int(datetime.timestamp(datetimes[0])*1000)
to_ = int(from_+8.64e+7 if (len(datetimes) == 1) or (datetimes[0]==datetimes[1]) else datetime.timestamp(datetimes[1])*1000)  



#For each device plot the distribution and the occurances per day


#For each device plot the distribution and the occurances per day
if len(selected_zones) >0 :
    zone_without_data = []
    zone_with_data = []
    
    for zone in selected_zones:
        data = rest_client.get_zone_from_to(zone, from_, to_)
        if len(data) > 0:
            #print(zone,'\n',data)
            data['date'] = pd.to_datetime(data['timestamps'], unit='ms')
            temp = data.groupby(by=[pd.Grouper(key='date',freq='1Min'),'detections']).count()
            pivoted = pd.pivot_table(temp, values='timestamps', index='date', columns='detections')
            zone_with_data.append((device, [data['detections'].value_counts().sort_index(), pivoted]))
        else:
            zone_without_data.append(zone)
    
    if len(zone_with_data) > 0:
        fig, (axs_device) = plt.subplots(len(zone_with_data), 2)

        if axs_device.shape == (2,):
            axs_device =[axs_device]

        for (zone, [distribution, pivoted]), [line, bar] in zip(zone_with_data, axs_device):
            #print(f'Device info: {zone}')
            
            distribution.plot.bar(ax = bar, title = f'{zone} total detections by class')
            pivoted.plot.line(ax=line, title='Detections per minute')


        plt.tight_layout()
        st.pyplot(fig)
    if len(zone_without_data) > 0:
        st.write(f'Zones {zone_without_data} have not data for the selected time interval')
else:
    st.write('Please select at least one zone')


st.write("---")

st.markdown(
    """
    ### Delete Device
    """
)

device_to_remove = st.selectbox('Select the device to remove', options= devices)

def delete_device(device_to_remove):
    if rest_client.delete_device(device_to_remove):
            st.write(f'{device_to_remove} deleted')

def delete_zone(zone_to_remove):
    if rest_client.delete_zone(zone_to_remove):
        st.write(f'{zone_to_remove} deleted')

st.button('Remove the device', on_click=delete_device, args=[device_to_remove])
    


st.write("---")

st.markdown(
    """
    ### Delete Zone
    """
)

zone_to_remove = st.selectbox('Select the zone to remove', options= zones)
st.button('Remove the zone', on_click=delete_zone, args=[zone_to_remove])
    


















