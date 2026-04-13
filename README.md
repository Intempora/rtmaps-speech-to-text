# rtmaps-speech-to-text
Python Bridge scripts to add Speech-to-text to a diagram 

**stt_example.rtd** uses two python bridges.
One to get the microphone audio, the other to convert the audio to text using FasterWhisper.

We recommend creating a venv for both scripts.
Set the python bridge property "Python executable" to use your venv python executable i.e :

```
PB_STT.pythonExecutable = <<venv-stt\Scripts\python.exe>>
```

### CPU vs GPU
FasterWhisper models are available for both.

See their git for more details :
https://github.com/SYSTRAN/faster-whisper  

To use CUDA you will need to install the torch + cuda combination for your GPU + cuda.

## Microphone
RTMaps Python Bridge script to get audio from default system microphone
 
requirements :

```
pip install pyaudio 
pip install SpeechRecognition  
```
 
## STT
RTMaps Python Bridge wrapper for faster-whisper

Follow setup and configuration from their github :
https://github.com/SYSTRAN/faster-whisper  


requirements :

```
pip install pyaudio
pip install faster_whisper
pip install SpeechRecognition 
```
