"""
RTMaps Python Bridge script to get audio from default system microphone
 
requirements :

pip install pyaudio 
pip install SpeechRecognition 

"""

import io
from queue import Queue
import datetime
from datetime import timedelta

import rtmaps.types
import rtmaps.reading_policy
from rtmaps.base_component import BaseComponent  # base class

import speech_recognition as sr 

import numpy as np
 
   
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
        self.add_property("output_buffer", 441000) 

# Birth() 
    def Birth(self):  
        self.first_time = True 
        self.verbose = self.properties["verbose"].data   
        self.record_timeout = self.properties["record_timeout"].data 
 
        self.out_buffer_size = self.properties["output_buffer"].data    

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

            try: 
             # Write the audio data on the output
                if self.first_time:
                    self.outputs["mic_out"].alloc_output_buffer(self.out_buffer_size)
                    self.first_time = False 

                self.write("mic_out", data)
            except :
                return 

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=self.record_timeout)
  
# Core() 
    def Core(self):   
        pass 

# Death() 
    def Death(self):
        pass
