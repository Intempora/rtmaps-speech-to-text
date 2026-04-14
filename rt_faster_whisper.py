# ---------------- SAMPLE -------------------
# This sample just copies the input to the output.
# It also shows two different manners to define an output, whether by using AUTO 
# or directly specify the type you need (INTEGER64, CANFRAME, IPLIMAGE, etc.).

import io
from queue import Queue
import datetime
from datetime import timedelta

import rtmaps.types
import rtmaps.reading_policy
from rtmaps.base_component import BaseComponent  # base class

from faster_whisper import WhisperModel
import speech_recognition as sr 


"""
RTMaps Python Bridge wrapper for faster-whisper

This script allows the user to add Speech-to-Text on their diagram
The audio is fetched dirently from the device in this code.
We only output the detected text. 

CPU & GPU compatible
Currently English only

Follow setup and configuration from their github :
https://github.com/SYSTRAN/faster-whisper  


requirements :

pip install pyaudio
pip install faster_whisper
pip install SpeechRecognition 

"""
   
# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
     
    def __init__(self):
        BaseComponent.__init__(self)  
        self.force_reading_policy(rtmaps.reading_policy.SAMPLING)


# Dynamic()  
    def Dynamic(self):  
        self.add_output("text_out", rtmaps.types.AUTO, buffer_size = 64)  
 
        self.add_property("verbose", False) 

        self.add_property("model_size", "5|1|tiny|base|small|medium|large-v2", rtmaps.types.ENUM)
        self.add_property("device", "3|0|auto|cpu|cuda", rtmaps.types.ENUM) 
        self.add_property("compute_type", "6|1|auto|int8|int8_floatt16|float16|int16|float32", rtmaps.types.ENUM) 

        self.add_property("record_timeout", 2.0) 
        self.add_property("phrase_timeout", 0.05) 
        self.add_property("threads", 0) 
 

# Birth() 
    def Birth(self):
        self.model_size = self.properties["model_size"].get_selected_value()# + ".en"
        self.device = self.properties["device"].get_selected_value()
        self.compute_type = self.properties["compute_type"].get_selected_value()

        self.verbose = self.properties["verbose"].data  
        self.threads = self.properties["threads"].data  
        self.record_timeout = self.properties["record_timeout"].data
        self.phrase_timeout = self.properties["phrase_timeout"].data

        print("---------------------------------") 
        print("Faster Whisper Model Configuration") 
        print("device [" + self.device + "]")
        print("model size [" + self.model_size + "]")
        print("compute type [" + self.compute_type + "]") 
        print("---------------------------------") 

        # The last time a recording was retreived from the queue.
        self.phrase_time = None

        # Current raw audio bytes.
        self.last_sample = bytes()

        # Thread safe Queue for passing data from the threaded recording callback.
        self.data_queue = Queue()

        # We use SpeechRecognizer to record our audio because it has a nice feauture where it can detect when speech ends.
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 500
        self.recorder.dynamic_energy_threshold = False

        self.source = sr.Microphone(sample_rate=16000) 

        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
 
        def record_callback(_, audio:sr.AudioData) -> None: 
            # Grab the raw bytes and push it into the thread safe queue.
            data = audio.get_raw_data()
            self.data_queue.put(data)
            if self.verbose == True :
                print("record_callback\n") 


        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=self.record_timeout)

        print("Model loading...") 
        self.model = WhisperModel(self.model_size,  device=self.device, compute_type=self.compute_type, cpu_threads=self.threads) 
        print("All ready! Listening...\n") 

# Core() 
    def Core(self):  
        now = datetime.datetime.utcnow()

        # Pull raw recorded audio from the queue.
        if not self.data_queue.empty():
            phrase_complete = False
            
            if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
                self.last_sample = bytes()
                phrase_complete = True
                
            self.phrase_time = now

            # Concatenate our current audio data with the latest audio data.
            while not self.data_queue.empty():
                data = self.data_queue.get()
                self.last_sample += data

            # Use AudioData to convert the raw data to wav data.
            audio_data = sr.AudioData(self.last_sample, self.source.SAMPLE_RATE, self.source.SAMPLE_WIDTH)
            wav_data = io.BytesIO(audio_data.get_wav_data())

            # Read the transcription.
            text = ""
                
            segments, info = self.model.transcribe(wav_data)
            for segment in segments:
                text += segment.text 
  
            if self.verbose == True :
                print(text) 

            # Write the text on the output
            self.write("text_out", text)

# Death() 
    def Death(self):
        pass
