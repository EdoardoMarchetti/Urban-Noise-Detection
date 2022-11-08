import argparse as ap
import pandas as pd
import sounddevice as sd
import os
import tensorflow as tf
import tensorflow_io as tfio
import numpy as np
import altair as alt

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


    store_audio = is_silence(indata = indata, downsampling_rate= SAMPLING_RATE, frame_length_in_s=0.0005, dbFSthres=-90, duration_thres=0.02)
    
    if not store_audio:
        timestamp = time()
        file_path = f'{OUTPUT_FOLDER}/{timestamp}.wav'
        print(file_path)
        write(filename= file_path, rate = SAMPLING_RATE, data = indata) #filename = outputpath
        size_in_bytes = os.path.getsize(file_path)
        size_in_kb = size_in_bytes / 1024
        print(f'Size {size_in_kb} KB')


def get_audio_from_numpy(indata):
    indata = tf.convert_to_tensor(indata, dtype = tf.float32)   
    indata = (indata+32768) / (32767+32768)
    indata = tf.squeeze(indata)

    return indata


# Gets an spectrogram that takes time x amplitude to frequency x magnitude
def get_spectrogram(indata, downsampling_rate, frame_length_in_s, frame_step_in_s):
    # TODO: Write your code here
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

def is_silence(indata, downsampling_rate, frame_length_in_s, dbFSthres, duration_thres):

    spectrogram = get_spectrogram(
        indata,
        downsampling_rate,
        frame_length_in_s,
        frame_length_in_s
    )

    dbFS = 20 * tf.math.log(spectrogram + 1.e-6)
    print('dbfs: ', dbFS)
    energy = tf.math.reduce_mean(dbFS, axis=1)
    print('Energy: ', energy)

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
    print('Mask: ', non_silence)
    non_silence_frames = tf.math.reduce_sum(tf.cast(non_silence, tf.float32))
    print('Non silence frames: ', non_silence_frames)
    non_silence_duration = (non_silence_frames + 1) * frame_length_in_s

    print('Non_silence_duration: ', non_silence_duration, " duration_thres: ", duration_thres)

    if non_silence_duration > duration_thres:
        return 0
    else:
        return 1


print('Start Recording...')

with sd.InputStream(device=args.device,                   #device = id of the input device
               channels= 1,                               #channels = number of microphones used at the same time
               samplerate= SAMPLING_RATE,                 #samplerate = number of samples per second; the higher the higher the resolution
               dtype= 'int16',                            #dtype = The sample format of the numpy.ndarray provided to the stream callback, read() or write().
               callback= callback,                        #callback = indicate the calback function name  
               blocksize= SAMPLING_RATE):                 #blocksize = every how many samples the callback is invoked 
                          
    while True: 

        key = input()
        if key in ['Q', 'q']:
            print('Stop recording')
            break
        elif key in ['P', 'p']:
            store_audio = not store_audio

        sleep(1)
        