import argparse as ap
import sounddevice as sd
import os
import tensorflow as tf
import tensorflow_io as tfio
import numpy as np
import altair as alt
import pandas as pd

from scipy.io.wavfile import write
from time import sleep, time


print('Import completed')
#-------------------------START--------------------------------------------
OUTPUT_FOLDER = 'audio_records'
CHANNELS = 1
RESOLUTION = 'int16'
SAMPLING_RATE = 16000


store_audio = True
#------------------------PARSING------------------------------------------
parser = ap.ArgumentParser()
parser.add_argument('--device', type = int, default= 1)
args = parser.parse_args()



#-----------------------UTILITY FUNCTIONS---------------------------------
def callback(indata, frames, call_back, status):

    
    store_audio = is_silence(indata = indata, downsampling_rate= SAMPLING_RATE, frame_length_in_s=0.0001, dbFSthres=-90, duration_thres=0.02)
    
    if store_audio:
        timestamp = time()
        file_path = f'{OUTPUT_FOLDER}/{timestamp}.wav'
        print(file_path)
        write(filename= file_path, rate = SAMPLING_RATE, data = indata) #filename = outputpath
        size_in_bytes = os.path.getsize(file_path)
        size_in_kb = size_in_bytes / 1024
        print(f'Size {size_in_kb} KB')


def get_audio_from_numpy(indata):
    indata = tf.convert_to_tensor(indata, dtype=tf.float32)
    indata = 2 * ((indata + 32768) / (32767 + 32768)) - 1  # CORRECT normalization between -1 and 1
    indata = tf.squeeze(indata)

    return indata


# Gets an spectrogram that takes time x amplitude to frequency x magnitude
def get_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s):
    audio = get_audio_from_numpy(indata)

    sampling_rate_float32 = tf.cast(downsampling_rate, tf.float32)
    # Create the frame length and step for the stft (Short-Time Fourier Transform)
    frame_length = int(frame_length_in_s * sampling_rate_float32)
    frame_step = int(frame_step_in_s * sampling_rate_float32)
    # Compute the stft
    stft = tf.signal.stft(
        audio,
        frame_length = frame_length,
        frame_step = frame_step,
        fft_length = frame_length
    )
    #Get the spectogram
    spectogram = tf.abs(stft)

    return spectogram

def is_silence(indata, downsampling_rate, frame_length_in_s, dbFSthres, duration_thres):

    spectrogram = get_spectrogram(
        indata,
        downsampling_rate,
        frame_length_in_s,
        frame_length_in_s
    )

    dbFS = 20 * tf.math.log(spectrogram + 1.e-6)
    energy = tf.math.reduce_mean(dbFS, axis=1)

    print('Energy len: ', len(energy))
    print('Time len: ', len(np.arange(0,1,frame_length_in_s)))

    plot_data = {
        'Time': np.arange(0, 1, frame_length_in_s),
        'Energy': energy,
    }
    df= pd.DataFrame(plot_data)
    print(df)

    chart= alt.Chart(df).mark_bar().encode(
        x = 'Time:Q',
        y = 'Energy:Q'
    )
    
    chart.interactive().show()


    non_silence = energy > dbFSthres
    non_silence_frames = tf.math.reduce_sum(tf.cast(non_silence, tf.float32))
    non_silence_duration = (non_silence_frames + 1) * frame_length_in_s

    print('Non_silence_duration: ', non_silence_duration, " duration_thres: ", duration_thres)

    if non_silence_duration > duration_thres:
        return 0
    else:
        return 1


print('Start Recording...')

with sd.InputStream(device=args.device,                   #device = id of the input device
               channels= 1,         #channels = number of microphones used at the same time
               samplerate= SAMPLING_RATE,    #samplerate = number of samples per second; the higher the higher the resolution
               dtype= 'int16',          #dtype = The sample format of the numpy.ndarray provided to the stream callback, read() or write().
               callback= callback,              #callback = indicate the calback function name  
               blocksize= SAMPLING_RATE):    #blocksize = every how many samples the callback is invoked 
                          
    while True: 

        key = input()
        if key in ['Q', 'q']:
            print('Stop recording')
            break
        elif key in ['P', 'p']:
            store_audio = not store_audio

        sleep(1)
        