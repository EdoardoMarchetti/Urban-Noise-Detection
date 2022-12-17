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

print('Import completed')
#-------------------------START--------------------------------------------
OUTPUT_FOLDER = 'audio_records'

# Selected labels
LABELS = ['go', 'stop']

#------------------------PARSING------------------------------------------
parser = ap.ArgumentParser()

parser.add_argument('--device', type = int, required=True)
parser.add_argument('--host', help='the Redis Cloud host.', type = str, required=True)
parser.add_argument('--port', help='the Redis Cloud port.', type = int, required=True)
parser.add_argument('--user', help='the Redis Cloud username.', type = str, required=True)
parser.add_argument('--password', help='the Redis Cloud password.', type = str, required=True)

args = parser.parse_args()

# Recording parameters
DEVICE = args.device
CHANNELS = 1
DTYPE = 'int16'
AUDIO_FILE_LENGTH_IN_S = 1

# Redis parameters
REDIS_HOST = args.host
REDIS_PORT = args.port
REDIS_USER = args.user
REDIS_PASSWORD = args.password

# Parameters for is_silence function
IS_SILENCE_ARGS = {
    'downsampling_rate' : 16000,
    'frame_length_in_s' : 0.0001,
    'dbFSthres' : -90,
    'duration_thres' : 0.016
}

# Parameters for mfccs function
PREPROCESSING_MFCCS_ARGS = {
    'downsampling_rate': 16000,
    'frame_length_in_s': 0.016,
    'frame_step_in_s': 0.016,
    'num_mel_bins' : 40,
    'lower_frequency': 20,
    'upper_frequency': 8000,
    'num_mfccs_coefficients':10
}

# Prediction threshold
thresh = 0.95

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
    store_audio = is_silence(indata=indata,
                             downsampling_rate=IS_SILENCE_ARGS['downsampling_rate'],
                             frame_length_in_s=IS_SILENCE_ARGS['frame_length_in_s'],
                             dbFSthres=IS_SILENCE_ARGS['dbFSthres'],
                             duration_thres=IS_SILENCE_ARGS['duration_thres'])


    if not store_audio:
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

        # Select predicted label and magnitude
        top_index = np.argmax(output[0])
        prediction_magnitude = output[0][top_index]
        prediction_label = LABELS[top_index]

        print(f'Prediction: {prediction_label} with magnitude: {prediction_magnitude}')

        # If prediction magnitude greater the a threshold change the state of the application
        if (prediction_magnitude > thresh and prediction_label == 'go'):
            store_information = True
        elif (prediction_magnitude > thresh and prediction_label == 'stop'):
            store_information = False

    if (store_information == True):  # If state is to store information then store it
            timestamp = time()
            battery_level = ps.sensors_battery().percent
            power_plugged = int(ps.sensors_battery().power_plugged)
            timestamp_ms = int(timestamp * 1000)

            # Addition of the data to the time series
            redis_client.ts().add(mac_address+':battery', timestamp_ms, battery_level)
            redis_client.ts().add(mac_address+':power', timestamp_ms, power_plugged)
            print('Added on Redis')

# Create Redis Client
redis_client = redis.Redis(host= args.host, \
                           port= args.port,\
                           username= args.user,\
                           password= args.password)
print('Is redis connected? ', redis_client.ping())


redis_client.flushdb()

# Get the mac_address
mac_address = hex(uuid.getnode())
print('MAC address: ', mac_address)

# Create the timesries_name
mac_battery = f'{mac_address}:battery_level'
mac_power = f'{mac_address}:power_plugged'
try:
    redis_client.ts().create(mac_battery, uncompressed = False, chunk_size=128)                                                                                        #timeseries for battery level \in [0,100]
    redis_client.ts().create(mac_power, uncompressed = False, chunk_size=128)                                        
except redis.ResponseError:
    pass

# Obtain the model to integrate
MODEL_NAME = 'best_model'

print('Unzipping the model')
zipped_model_path = os.path.join('.', f'{MODEL_NAME}.tflite.zip')
with zipfile.ZipFile(zipped_model_path, 'r') as zip_ref:
    zip_ref.extractall("./")

# Implement the interpreter
print('Loading the model')
model_path = os.path.join('./tflite_models/', f'{MODEL_NAME}.tflite')
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

print('...script is starting...')
# State of the application
store_information = False
print('Press q+Enter to terminate\n\n\n')

with sd.InputStream(device=DEVICE,
                    channels=CHANNELS,
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