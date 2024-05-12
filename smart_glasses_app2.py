import os
import pvporcupine
from pvrecorder import PvRecorder
import pyaudio
import audioop
from pvleopard import create, LeopardActivationLimitError
import requests
from picamera2 import Picamera2 as PiCamera, Preview
import io
import wave
import time
from threading import Thread
import pygame
from gtts import gTTS

# Configuration constants
BASE_URL = 'https://ac8c-102-191-232-144.ngrok-free.app'
ACCESS_KEY = ACCESS_KEY  # Assuming you have defined ACCESS_KEY elsewhere
KEYWORD_FILE_PATH = KEYWORD_FILE_PATH  # Assuming you have defined KEYWORD_FILE_PATH elsewhere
SENSITIVITY = 0.5
RECORD_TIMER = 3

# Recorder class to handle audio recording in a separate thread
class Recorder(Thread):
    def __init__(self, audio_device_index):
        super().__init__()
        self._pcm = []
        self._is_recording = False
        self._stop = False
        self._audio_device_index = audio_device_index

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True
        recorder = PvRecorder(frame_length=160, device_index=self._audio_device_index)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()
        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass
        return self._pcm

# Create an instance of Leopard for speech-to-text processing
LEOPARD = create(access_key=ACCESS_KEY, model_path=model_pat)

# Function to convert speech to text
def speech_to_text():
    recorder = None
    print("Starting recording...")
    recorder = Recorder(-1)  # Assuming -1 represents the default audio device index
    recorder.start()
    time.sleep(RECORD_TIMER)
    try:
        transcript, words = LEOPARD.process(recorder.stop())
        print("Transcript:", transcript)
        filter_words(words)
    except LeopardActivationLimitError:
        print('AccessKey has reached its processing limit.')
        recorder = None

# Function to filter words and determine the mode of operation
def filter_words(words):
    print("Filtering words:", words)
    mode = None
    object_to_be_found = None
    for word in words:
        if word.word == "money":
            mode = "currency"
            break
        elif word.word == "read":
            mode = "text"
            break
        elif word.word == "find":
            object_to_be_found = words[-1]
            mode = "find"
            break
        elif word.word == "detect":
            mode = "object"
            break
        elif word.word == "describe":
            mode = "describe"
            break
        else:
            speak_english("Try again")
            return

    print("Mode:", mode)
    if mode:
        capture_images()
        dedect_api(mode, object_to_be_found)

# Function to interact with the detection API
def dedect_api(mode, object_to_be_found):
    print("Detecting API")
    try:
        data = {'select_mode': mode, 'object_to_be_found': object_to_be_found}
        files = {'file': open('/home/pi/Desktop/output_img.png', 'rb')}
        response = requests.post(BASE_URL+'/detect', data=data, files=files)
        
        if response.status_code == 200:
            result = response.json()[0]['result']
            print("API Response:", result)
            api_response_callback(result)
        else:
            print('Error:', response.status_code)
            api_response_callback('Error')
    except requests.RequestException as e:
        print("Request Error:", e)
        api_response_callback('Error')

# Callback function for API response
def api_response_callback(response):
    print("API Response Callback:", response)
    if response:
        if is_english:
            speak_english(response)
        else:
            speak_arabic(translate_text('ar', response)['translatedText'])

# Function to play notification sound
def notify():
    print("Notifying")
    pygame.init()
    pygame.mixer.music.load('/home/pi/Desktop/voicerecognation/notify.wav')
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.quit()

# Function to speak English text
def speak_english(text):
    print("Speaking English:", text)
    tts = gTTS(text=text, lang='en')
    tts.save("english.mp3")
    os.system("mpg321 english.mp3")

# Function to speak Arabic text
def speak_arabic(text):
    print("Speaking Arabic:", text)
    tts = gTTS(text=text, lang='ar')
    tts.save("arabic.mp3")
    os.system("mpg321 arabic.mp3")

# Function to capture images using PiCamera
def capture_images():
    print("Capturing images")
    with PiCamera() as camera:
        camera.start()
        time.sleep(1)
        camera.capture_file("/home/pi/Desktop/output_img.png")
        camera.stop()

# Main function
def main():
    global is_english
    is_english = True  # Define the is_english variable
    
    # Initialize Porcupine for keyword detection
    handle = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_FILE_PATH],
        sensitivities=[SENSITIVITY]
    )
    recorder = PvRecorder(device_index=-1, frame_length=handle.frame_length)
    speak_english("Welcome to smart glasses")
    print('Start listening...')
    
    try:
        recorder.start()
        while True:
            keyword_index = handle.process(recorder.read())
            if keyword_index == 0:
                print("Keyword detected")
                notify()
                speech_to_text()
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
    finally:
        handle.delete()
        recorder.delete()

# Entry point of the script
if __name__ == "__main__":
    main()
