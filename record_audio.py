import numpy as np
import pyaudio
import requests
import hex2xy

def start_recording():

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
    RECORD_SECONDS = 1

    # Create instance of PyAudio and stream which will be used for recording
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=DEVICE_INDEX)

    y = np.empty(1)

    # Record sound and adjust color in the loop
    # Uncomment line bellow to make loop terminatable if sound is too loud
    #while (y.max() < 32000):
    while (y.max() < 100000):

        print("Recording")

        data = stream.read(RATE * RECORD_SECONDS)  #read audio stream
        y = np.fromstring(data, dtype=np.int16)
        y = y.astype(np.float32)

        # Calculate db value
        db = 20*np.log10(np.sqrt(np.mean(np.abs(y.max())**2)))
        print(db)

        # Set color based on db value
        if db <= 50:
            hex = "#1F81F2"
        elif db <= 72:
            hex = "#34D800"
        elif db <= 80:
            hex = "#F5D549"
        else: hex = "#E62942"

        color = hex2xy.convert(hex)

        url = f'http://{BRIDGE_IP}/api/{KEY}/lights/4/state'
        json = {
            "on": True,	
            "xy": color[0],            
            "bri": color[1]
        }

        requests.put(url, json = json)
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

start_recording()