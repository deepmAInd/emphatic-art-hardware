import numpy as np
import pyaudio
import requests
import hex2xy
import noisereduce as nr

import librosa
from pydub import AudioSegment, effects

import skimage.io
from skimage.transform import rescale, resize, downscale_local_mean
from skimage.util import img_as_ubyte 

from tensorflow import keras


MODEL_NAME = 'model_comb_v1_6iter'

MODELS_PATH = 'models'

# Use GET https://discovery.meethue.com/ to find bridge IP
BRIDGE_IP = "192.168.2.189"

# Use POST http://{BRIDGE_IP}/api after pressing button on the bridge with the following JSON body
#  	{
# 	    "devicetype":"app_name#instance_name", 
# 	    "generateclientkey":true
#   }
#
# Value of the "username" field in the response should be used as a KEY 
KEY = "wTtLrjUQX2aHO05qlatdIhvID7FJtMXKT2UmUJhr"

# Use get_input_devices() function to find devise ID
DEVICE_INDEX = 2

CHUNK = 1024

# Configure this settings based on the microphone specs
CHANNELS = 1
RATE = 44100

# How often surrounding sound will be analysed
RECORD_SECONDS = 5

IMG_SIZE = (224, 224)

MODEL = keras.models.load_model(f'{MODELS_PATH}/{MODEL_NAME}')

EMOTIONS_MAP = {
    'happy': 0,
    'surprise': 1,
    'anger': 2,
    'sad': 3,
    'neutral': 4,
    'disgust': 5,
    'fear': 6
}

def scale_minmax(X, min=0.0, max=1.0):
    X_std = (X - X.min()) / (X.max() - X.min())
    X_scaled = X_std * (max - min) + min
    return X_scaled

def spectrogram_image(data, path):
    mels = librosa.feature.melspectrogram(data)
    mels = np.log(mels + 1e-9) # add small number to avoid log(0)
    # min-max scale to fit inside 8-bit range
    img = scale_minmax(mels, 0, 255).astype(np.uint8)
    img = np.flip(img, axis=0) # put low frequencies at the bottom in image
    img = 255-img # invert. make black==more energy
    # img = rescale(img, 2, anti_aliasing=True)
    img = img_as_ubyte(img)
    img = resize(img, IMG_SIZE)

    # save as PNG
    skimage.io.imsave(path, img)
    return img

def convert_to_image(data, save_path):

    norm_sound=librosa.util.normalize(data, norm=5)
    # raw_sound = AudioSegment.from_raw(data, sample_width=RECORD_SECONDS, channels=CHANNELS, frame_rate=RATE)
    # x, sr = librosa.load(audio_path, sr = None)

    # Normalizing +5.0db, transform audio signals to an array
    # normalized_sound=effects.normalize(raw_sound,headroom = 5.0)
    # normal_x = np.array(norm_sound.get_array_of_samples(), dtype = 'float32')

    # Trimming the silence in the beginning and end
    # xt, index = librosa.effects.trim(norm_sound, top_db = 30)
    # final_x = nr.reduce_noise(y=norm_sound,
    #                           y_noise=norm_sound,sr=44100)
    # padded_x = np.pad(xt, (0, samplerate * RECORD_SECONDS - len(xt)), 'constant')

    # Saving as image
    img = spectrogram_image(norm_sound, save_path)
    # img = np.array(img) / 255
    img = np.repeat(img[..., np.newaxis], 3, -1)# (64, 224, 224, 3)
    # print(img) 
    return img


def convert_to_mfcc(data, save_path):
    mfcc_data = librosa.feature.mfcc(y=data, sr=RATE)
    print(mfcc_data.shape)
    if mfcc_data.shape[1] < 229:
        arr_ = np.zeros((20, 229 - mfcc_data.shape[1]))
        mfcc_data = np.append(mfcc_data, arr_, axis = 1)
    else:
        if mfcc_data.shape[1] > 229:
            indexes = []
            for i in range(229, mfcc_data.shape[1]):
                indexes.append(i)
            mfcc_data = np.delete(mfcc_data, indexes, axis=1)
    mfcc_data = np.array(mfcc_data) / 255
    return mfcc_data
    

def start_predicting():

    # Create instance of PyAudio and stream which will be used for recording
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK,
                input_device_index=DEVICE_INDEX)
    y = 1

    # Record sound and adjust color in the loop
    # Uncomment line bellow to make loop terminatable if sound is too loud
    #while (y.max() < 32000):
    while (True):
        # y+=1
        print("Recording")
        data = stream.read(RATE * RECORD_SECONDS)  #read audio stream
        y = np.fromstring(data, dtype=np.int16)
        y = y.astype(np.float32)
        
        img = convert_to_image(y, "tmp.png")
        mfcc = convert_to_mfcc(y, "tmp.png")
        print(img.shape)
        print(mfcc.shape)
        res = MODEL.predict([np.expand_dims(img, axis=0), np.expand_dims(mfcc, axis=0)])
        print(np.argmax(res))
        print(res[0].astype(float))
        print(list(EMOTIONS_MAP.keys())[list(EMOTIONS_MAP.values()).index(np.argmax(res))])
        # # Calculate db value
        # db = 20*np.log10(np.sqrt(np.mean(np.abs(y.max())**2)))
        # print(db)

        # # Set color based on db value
        # if db <= 50:
        #     hex = "#1F81F2"
        # elif db <= 72:
        #     hex = "#34D800"
        # elif db <= 80:
        #     hex = "#F5D549"
        # else: hex = "#E62942"

        # color = hex2xy.convert(hex)

        # url = f'http://{BRIDGE_IP}/api/{KEY}/lights/4/state'
        # json = {
        #     "on": True,	
        #     "xy": color[0],            
        #     "bri": color[1]
        # }

        # requests.put(url, json = json)
        # print("* playing")
        # stream.write(data, RATE * RECORD_SECONDS)  #play back audio stream

        print("Done")

    stream.stop_stream()
    stream.close()

    p.terminate()

def get_input_devices():

    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

# Uncomment to get device ID
# get_input_devices()

start_predicting()

