# rtmaps-nlp
Example of RTMaps components to add an NLP model on a diagram

**intent_model_robot_ctrl.rtd** uses two python bridges.
One to get the microphone audio & convert the audio to text using FasterWhisper.

The other parses the inputed text with an intent model to find orders to give to a Gazebo robot (i.e Twist) 
The model can return the following orders from natural language :

"stop" - "forward" - "left" -"right" - "back" - "encore"

We recommend creating a venv for both scripts.
Set the python bridge property "Python executable" to use your venv python executable i.e :

```
PB_STT.pythonExecutable = <<venv-stt\Scripts\python.exe>>
```

## Update intents
You can modify the intents.json to add/remove understood orders.
If you do so, you need to retrain the model before running the diagram again.
Right click on the python bridge and select retrain model.
This may take a while.
