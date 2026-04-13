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

import speech_recognition as sr 

import numpy as np

"""
RTMaps Python Bridge script to get audio from default system microphone
 
requirements :

pip install pyaudio 
pip install SpeechRecognition 

"""
   
# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
     
    def __init__(self):
        BaseComponent.__init__(self)  
        self.force_reading_policy(rtmaps.reading_policy.SAMPLING)


# Dynamic()  
    def Dynamic(self):  
        self.add_output("mic_out", rtmaps.types.STREAM8)  
 
        self.add_property("verbose", False)  

        self.add_property("record_timeout", 2.0) 
        self.add_property("phrase_timeout", 0.05) 
 
        self.add_property("output_buffer", 441000) 

# Birth() 
    def Birth(self):  
        self.first_time = True 
        self.verbose = self.properties["verbose"].data   
        self.record_timeout = self.properties["record_timeout"].data
        self.phrase_timeout = self.properties["phrase_timeout"].data
 
        self.out_buffer_size = self.properties["output_buffer"].data   

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

        print(self.source.SAMPLE_RATE)
        print(self.source.SAMPLE_WIDTH)

        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
 
        def record_callback(_, audio:sr.AudioData) -> None: 
            # Grab the raw bytes and push it into the thread safe queue.
            data = audio.get_raw_data()
            self.data_queue.put(data)  

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=self.record_timeout)
  
# Core() 
    def Core(self):   
        now = datetime.datetime.utcnow()

        try:  
            if self.first_time:
                self.outputs["mic_out"].alloc_output_buffer(self.out_buffer_size)
                self.first_time = False 
        except KeyError:
            return 

        # Pull raw recorded audio from the queue.
        if not self.data_queue.empty():
            
            if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
                self.last_sample = bytes()
                
            self.phrase_time = now

            # Concatenate our current audio data with the latest audio data.
            while not self.data_queue.empty():
                data = self.data_queue.get()
                self.last_sample += data 

            try: 
             # Write the audio data on the output
                self.write("mic_out", self.last_sample)
            except :
                return 

# Death() 
    def Death(self):
        pass
