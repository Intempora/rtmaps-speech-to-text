"""
RTMaps Python Bridge wrapper for faster-whisper

This script allows the user to add Speech-to-Text on their diagram
This component takes audio on its input and output the detected text. 

CPU & GPU compatible
Currently English only

Follow setup and configuration from their github :
https://github.com/SYSTRAN/faster-whisper  

Highly recommend using a virtual environment 
To configure a Python Bridge with a venv, simply set its Python executable porperty to the python executable of your venv

requirements :

pip install pyaudio
pip install faster_whisper
pip install SpeechRecognition 

"""

import io
from queue import Queue
import datetime
from datetime import timedelta

import rtmaps.types
import rtmaps.reading_policy
from rtmaps.base_component import BaseComponent  # base class

from faster_whisper import WhisperModel
import speech_recognition as sr 

 
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
   
# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
     
    def __init__(self):
        BaseComponent.__init__(self)  
        self.force_reading_policy(rtmaps.reading_policy.REACTIVE)

# Transcribe
    def transcribe(self):
        # Pull raw recorded audio from the queue.
        if not self.data_queue.empty(): 
            
            # Concatenate our current audio data with the latest audio data. 
            while not self.data_queue.empty():
                data = self.data_queue.get() 
                self.last_sample += data 

            try: 
                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(self.last_sample, SAMPLE_RATE, SAMPLE_WIDTH) 
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Read the transcription.
                text = ""
                    
                segments, info = self.model.transcribe(wav_data)
                for segment in segments:
                    text += segment.text 

                if self.verbose == True :
                    print(text) 

                # Write the text on the output
                self.write("text_out", text[:self.txt_buffer_size-1])
            except :
                return 

# Dynamic()  
    def Dynamic(self):  
        self.add_input("audio_in", rtmaps.types.AUTO)  
        self.add_output("text_out", rtmaps.types.AUTO)  
 
        self.add_property("verbose", False) 
        self.add_property("phrase_timeout", 10000) 
 

        self.add_property("model_size", "5|1|tiny|base|small|medium|large-v2", rtmaps.types.ENUM)
        self.add_property("device", "3|0|auto|cpu|cuda", rtmaps.types.ENUM) 
        self.add_property("compute_type", "6|1|auto|int8|int8_floatt16|float16|int16|float32", rtmaps.types.ENUM) 

        self.add_property("threads", 0) 
        self.add_property("output_buffer", 512) 
 

# Birth() 
    def Birth(self):
        self.first_time = True 
        self.model_size = self.properties["model_size"].get_selected_value()# + ".en"
        self.device = self.properties["device"].get_selected_value()
        self.compute_type = self.properties["compute_type"].get_selected_value()

        self.verbose = self.properties["verbose"].data  
        self.phrase_timeout = self.properties["phrase_timeout"].data
        self.threads = self.properties["threads"].data   
        self.txt_buffer_size = self.properties["output_buffer"].data   

        # The last time a recording was retreived from the queue.
        self.phrase_time = None

        # Current raw audio bytes.
        self.last_sample = bytes() 
        self.last_ts = 0
        
        # Thread safe Queue for passing data from the threaded recording callback.
        self.data_queue = Queue()

        print("---------------------------------") 
        print("Faster Whisper Model Configuration") 
        print("device [" + self.device + "]")
        print("model size [" + self.model_size + "]")
        print("compute type [" + self.compute_type + "]") 
        print("---------------------------------")  
 
        print("Model loading...") 
        self.model = WhisperModel(self.model_size,  device=self.device, compute_type=self.compute_type, cpu_threads=self.threads) 
        print("All ready! Listening...\n") 

# Core() 
    def Core(self):   
        print("STT Core()")
        try:  
            if self.first_time:
                self.outputs["text_out"].alloc_output_buffer(self.txt_buffer_size)
                self.first_time = False 
        except KeyError:
            return

        now = self.current_timestamp 

        input_audio = self.inputs["audio_in"].ioelt.data   
        # Convert darray to Bytes
        self.data_queue.put(input_audio.tobytes())  
 
        # STT when enough audio data has been received
        if now - self.last_ts >= self.phrase_timeout : 
            self.last_sample = bytes() 
            self.transcribe()

        self.last_ts = now
 
# Death() 
    def Death(self):
        pass
