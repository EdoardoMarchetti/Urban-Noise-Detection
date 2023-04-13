print('Preparing the environment')
from time import sleep, time
from datetime import datetime
import sounddevice as sd
import os
import argparse as ap
import psutil as ps
import uuid
import redis
import numpy as np
import tensorflow as tf
import tensorflow_io as tfio
import zipfile
from argparse import ArgumentParser
import psutil as ps
import uuid
import paho.mqtt.client as mqtt
import json
import random

print('Import completed')
#-------------------------START--------------------------------------------
OUTPUT_FOLDER = 'audio_records'

# Selected labels
LABELS = ['car','bus','motorcycle']#,'chatter','other','truck']

#------------------------PARSING------------------------------------------
parser = ap.ArgumentParser()

parser.add_argument('--device', type = int, default=5, required=False)#True)
parser.add_argument('--host', help='the Redis Cloud host.', type = str, required=False)#True)
parser.add_argument('--port', help='the Redis Cloud port.', type = int, required=False)#True)
parser.add_argument('--user', help='the Redis Cloud username.', type = str, required=False)#True)
parser.add_argument('--password', help='the Redis Cloud password.', type = str, required=False)#True)

args = parser.parse_args()

# Recording parameters
DEVICE = args.device
CHANNELS = 1
DTYPE = 'int16'
AUDIO_FILE_LENGTH_IN_S = 1

# Redis parameters
'''
REDIS_HOST = args.host
REDIS_PORT = args.port
REDIS_USER = args.user
REDIS_PASSWORD = args.password
'''
# Parameters for is_silence function
IS_SILENCE_ARGS = {
    'downsampling_rate' : 44100,
    'frame_length_in_s' : 0.0001,
    'dbFSthres' : -90,
    'duration_thres' : 0.016
}

# Parameters for mfccs function
PREPROCESSING_MFCCS_ARGS = {
    'downsampling_rate': 44100,
    'frame_length_in_s': 0.016,
    'frame_step_in_s': 0.016,
    'num_mel_bins' : 40,
    'lower_frequency': 20,
    'upper_frequency': 8000,
    'num_mfccs_coefficients':20
}

# Prediction threshold
thresh = 0.8

#-----------------------UTILITY FUNCTIONS---------------------------------
def get_audio_from_numpy(indata):
    indata = tf.convert_to_tensor(indata, dtype=tf.float32)
    indata = 2 * ((indata + 32768) / (32767 + 32768)) - 1  # CORRECT normalization between -1 and 1
    indata = tf.squeeze(indata)

    return indata

def get_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s):
    audio_padded = get_audio_from_numpy(indata)

    sampling_rate_float32 = tf.cast(downsampling_rate, tf.float32)
    frame_length = int(frame_length_in_s * sampling_rate_float32)
    frame_step = int(frame_step_in_s * sampling_rate_float32)

    spectrogram = stft = tf.signal.stft(
        audio_padded, 
        frame_length=frame_length,
        frame_step=frame_step,
        fft_length=frame_length
    )
    spectrogram = tf.abs(stft)

    return spectrogram

def get_log_mel_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s, num_mel_bins, lower_frequency, upper_frequency):
    spectrogram= get_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s)

    sampling_rate_float32 = tf.cast(downsampling_rate, tf.float32)
    frame_length = int(frame_length_in_s * sampling_rate_float32)
    num_spectrogram_bins = frame_length // 2 + 1

    linear_to_mel_weight_matrix = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=num_mel_bins,
        num_spectrogram_bins=num_spectrogram_bins,
        sample_rate=downsampling_rate,
        lower_edge_hertz=lower_frequency,
        upper_edge_hertz=upper_frequency
    )

    mel_spectrogram = tf.matmul(spectrogram, linear_to_mel_weight_matrix)

    log_mel_spectrogram = tf.math.log(mel_spectrogram + 1.e-6)

    return log_mel_spectrogram

def get_mfccs(indata, downsampling_rate, frame_length_in_s, frame_step_in_s, num_mel_bins, lower_frequency, upper_frequency, num_coefficients):
    log_mel_spectrogram= get_log_mel_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s, num_mel_bins, lower_frequency, upper_frequency)

    mfccs =  tf.signal.mfccs_from_log_mel_spectrograms(log_mel_spectrogram)

    mfccs = mfccs[:,:num_coefficients]

    return mfccs

def is_silence(indata, downsampling_rate, frame_length_in_s, dbFSthres, duration_thres):

    spectrogram = get_spectrogram(
        indata,
        downsampling_rate,
        frame_length_in_s,
        frame_length_in_s
    )
    dbFS = 20 * tf.math.log(spectrogram + 1.e-6)
    energy = tf.math.reduce_mean(dbFS, axis=1)

    non_silence = energy > dbFSthres
    non_silence_frames = tf.math.reduce_sum(tf.cast(non_silence, tf.float32))
    
    non_silence_duration = (non_silence_frames + 1) * frame_length_in_s
    
    if non_silence_duration > duration_thres:
        return 0
    else:
        return 1

def callback(indata, frames, call_back, status):

    global store_information
    
    # Check if the audio is noisy
    store_audio = np.random.choice([0,1])
    '''is_silence(indata=indata,
                             downsampling_rate=IS_SILENCE_ARGS['downsampling_rate'],
                             frame_length_in_s=IS_SILENCE_ARGS['frame_length_in_s'],
                             dbFSthres=IS_SILENCE_ARGS['dbFSthres'],
                             duration_thres=IS_SILENCE_ARGS['duration_thres'])
    '''

    if not store_audio:
        '''
        # Compute the MFCCs
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        mfccs = get_mfccs(indata=indata,
                          downsampling_rate=PREPROCESSING_MFCCS_ARGS['downsampling_rate'],
                          frame_length_in_s=PREPROCESSING_MFCCS_ARGS['frame_length_in_s'],
                          frame_step_in_s=PREPROCESSING_MFCCS_ARGS['frame_step_in_s'],
                          num_mel_bins=PREPROCESSING_MFCCS_ARGS['num_mel_bins'],
                          lower_frequency=PREPROCESSING_MFCCS_ARGS['lower_frequency'],
                          upper_frequency=PREPROCESSING_MFCCS_ARGS['upper_frequency'],
                          num_coefficients=PREPROCESSING_MFCCS_ARGS['num_mfccs_coefficients'])
        

        mfccs = tf.expand_dims(mfccs, 0)
        mfccs = tf.expand_dims(mfccs, -1)

        # Perform the prediction
        interpreter.set_tensor(input_details[0]['index'], mfccs)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        '''
        
        if task == 'singlelabel':
            # Select predicted label and magnitude
            top_index = np.random.randint(0,len(LABELS)-1)#np.argmax(output[0])
            prediction_magnitude = random.uniform(0.7,1)#output[0][top_index]
            prediction_label = LABELS[top_index]
            print(f'Prediction: {prediction_label} with magnitude: {prediction_magnitude}')

        else:
            mask = output[0] > 0.5
            prediction_magnitude = output[0][mask]
            prediction_label = np.array(LABELS)[mask]
            print(list(zip(prediction_label,prediction_magnitude)))
        

        #Get the mac address
        mac_address = hex(uuid.getnode())
        #Prepare the timestamp
        timestamp = time()
        timestamp_in_ms = int(timestamp*1000)
            #Prepare the payload
        #for label in prediction_label:
        payload_dict = {
            'mac_address': mac_address,
            'timestamp':timestamp_in_ms,
            # Forse anche la zona però no lo sappaimo ancora
            'label': prediction_label, 
        }
        payload = json.dumps(payload_dict)
        #Publish the message
        client.publish(
            topic = 'montevideo', # Da controllare se effetivamente va hardcoded questo
            payload = payload # message to sent
        )

# Obtain the model to integrate
task = 'singlelabel'
MODEL_NAME = f'model_{task}'

'''print('Unzipping the model')
zipped_model_path = os.path.join('.', f'{MODEL_NAME}.tflite.zip')
with zipfile.ZipFile(zipped_model_path, 'r') as zip_ref:
    zip_ref.extractall("./")

# Implement the interpreter
print('Loading the model')
model_path = os.path.join('./tflite_models/', f'{MODEL_NAME}.tflite')
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

'''
print('...script is starting...')
# State of the application
store_information = False

client =  mqtt.Client()

#-----------On connect callback-------------
def on_connect(client,userdata,flags,rc):
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

# print('Sending...... Type Ctrl+C to stop')

print('Press q + Enter to terminate\n\n\n')

with sd.InputStream(#device=DEVICE,
                    #channels=CHANNELS,
                    samplerate=IS_SILENCE_ARGS['downsampling_rate'],
                    dtype=DTYPE,
                    blocksize=IS_SILENCE_ARGS['downsampling_rate'] * AUDIO_FILE_LENGTH_IN_S,
                    callback=callback):
    while True:
        # Allow keyboard interrupt
        key = input()
        if key in ['Q', 'q']:
            print('Stopping the script')
            break

        time.sleep(1)