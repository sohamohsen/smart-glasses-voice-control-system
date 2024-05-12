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

BASE_URL = 'https://ac8c-102-191-232-144.ngrok-free.app'
ACCESS_KEY = "Ocq+LFkR/KsYJkC8ZxBRqXDLhc4+uA6YCOvugWCxpPAaWctIhJQzIg=="
KEYWORD_FILE_PATH = '/home/pi/Desktop/voicerecognation/hey-glasses_en_raspberry-pi_v3_0_0 (1)/hey-glasses_en_raspberry-pi_v3_0_0.ppn'
SENSITIVITY = 0.5
RECORD_TIMER = 3

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

LEOPARD = create(access_key=ACCESS_KEY, model_path='/home/pi/Desktop/voicerecognation/find object-leopard-v2.0.0-24-05-10--12-09-36.pv')

def speech_to_text():
    recorder = None
    print("Starting recording...")
    recorder = Recorder(-1)
    recorder.start()
    time.sleep(RECORD_TIMER)
    try:
        transcript, words = LEOPARD.process(recorder.stop())
        print("Transcript:", transcript)
        filter_words(words)
    except LeopardActivationLimitError:
        print('AccessKey has reached its processing limit.')
        recorder = None

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

def api_response_callback(response):
    print("API Response Callback:", response)
    if response:
        if is_english:
            speak_english(response)
        else:
            speak_arabic(translate_text('ar', response)['translatedText'])

def notify():
    print("Notifying")
    pygame.init()
    pygame.mixer.music.load('/home/pi/Desktop/voicerecognation/notify.wav')
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.quit()

def speak_english(text):
    print("Speaking English:", text)
    tts = gTTS(text=text, lang='en')
    tts.save("english.mp3")
    os.system("mpg321 english.mp3")

def speak_arabic(text):
    print("Speaking Arabic:", text)
    tts = gTTS(text=text, lang='ar')
    tts.save("arabic.mp3")
    os.system("mpg321 arabic.mp3")

def capture_images():
    print("Capturing images")
    with PiCamera() as camera:
        camera.start()
        time.sleep(1)
        camera.capture_file("/home/pi/Desktop/output_img.png")
        camera.stop()

def main():
    global is_english
    is_english = True  # Define the is_english variable
    
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

if __name__ == "__main__":
    main()
