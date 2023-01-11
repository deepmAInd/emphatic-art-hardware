import wave

import librosa
import pyaudio

chunk = 1024  # record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1  # 1 indicates mono, 2 indicates suround sound
sample_rate = 44100  # record at 44100 samples per second
seconds = 5  # change for diferent lengths of audio based on model

p = pyaudio.PyAudio()  # create an interface to PortAudio

stream = p.open(
    format=sample_format,
    channels=channels,
    rate=sample_rate,
    frames_per_buffer=chunk,
    input=True,
)


print("Start Recording")
while True:
    frames = []  # initialize array to store frames

    print("Start Recording 5s")

    # store data in chunks for 5 seconds
    for i in range(0, int(sample_rate / chunk * seconds)):
        data = stream.read(chunk, False)
        frames.append(data)

    print("Finished Recording 5s")

    # save the recorded data as a WAV file
    wf = wave.open("src/recording.wav", "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b"".join(frames))
    wf.close()

    # load the audio file
    waveform, sr = librosa.load("src/recording.wav")

    # addd your model here & observe the predictions

# stream.stop_stream()
# stream.close()

# p.terminate()

# print("Terminated Recording")
