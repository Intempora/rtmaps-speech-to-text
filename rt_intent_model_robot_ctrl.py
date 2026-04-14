import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent

import os
import json
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

import numpy as np 
import nltk 

"""
RTMaps Python Bridge wrapper for intent model

  
requirements :

pip install torch 
pip install nltk 

"""
def print_f_name(fun):
    print(fun.__name__)

class BrainModel(nn.Module):

    def __init__(self, input_size, output_size):
        super(BrainModel, self).__init__()
 
        #fully connected layer
        self.fc1 = nn.Linear(input_size, 128) # input_size -> 128 neurons
        self.fc2 = nn.Linear(128, 64)         # 128 neurons -> 64 neurons
        self.fc3 = nn.Linear(64, output_size) # 64 neurons -> output_size (nb of paths/intents)
        self.relu = nn.ReLU()                 # Activation func == Rectified linear Unit
        self.dropout = nn.Dropout(0.5)

    # how stuff move from layers
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)

        return x
 
class BrainAssistant:

    def __init__(self, intents_path, function_mappings = None):
        self.model = None
        self.intents_path = intents_path

        self.documents = []
        self.vocabulary = []
        self.intents = []
        self.intents_responses = {}

        self.function_mappings = function_mappings

        self.X = None
        self.y = None

    @staticmethod
    def tokenize_and_lemmatize(text):
        lemmatizer = nltk.WordNetLemmatizer()

        words = nltk.word_tokenize(text)
        words = [lemmatizer.lemmatize(word.lower()) for word in words]

        return words

    def bag_of_words(self, words):
        return [1 if word in words else 0 for word in self.vocabulary]

    def parse_intents(self):
        lemmatizer = nltk.WordNetLemmatizer()

        if os.path.exists(self.intents_path):
            with open(self.intents_path, 'r') as f:
                intents_data = json.load(f)

            for intent in intents_data['intents']:
                if intent['tag'] not in self.intents:
                    self.intents.append(intent['tag'])
                    self.intents_responses[intent['tag']] = intent['responses']

                for pattern in intent['patterns']:
                    pattern_words = self.tokenize_and_lemmatize(pattern)
                    self.vocabulary.extend(pattern_words)
                    self.documents.append((pattern_words, intent['tag']))

                self.vocabulary = sorted(set(self.vocabulary))

    def prepare_data(self):
        bags = []
        indices = []

        for document in self.documents:
            words = document[0]
            bag = self.bag_of_words(words)

            intent_index = self.intents.index(document[1])

            bags.append(bag)
            indices.append(intent_index)

        self.X = np.array(bags)
        self.y = np.array(indices)

    def train_model(self, batch_size, lr, epochs):
        X_tensor = torch.tensor(self.X, dtype=torch.float32)
        y_tensor = torch.tensor(self.y, dtype=torch.long)

        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model = BrainModel(self.X.shape[1], len(self.intents)) 

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)

        for epoch in range(epochs):
            running_loss = 0.0

            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                running_loss += loss
            
            print(f"Epoch {epoch+1}: Loss: {running_loss / len(loader):.4f}")

    def save_model(self, model_path, dimensions_path):
        torch.save(self.model.state_dict(), model_path)

        with open(dimensions_path, 'w') as f:
            json.dump({ 'input_size': self.X.shape[1], 'output_size': len(self.intents) }, f)

    def load_model(self, model_path, dimensions_path):
        with open(dimensions_path, 'r') as f:
            dimensions = json.load(f)

        self.model = BrainModel(dimensions['input_size'], dimensions['output_size'])
        self.model.load_state_dict(torch.load(model_path, weights_only=True))

    def process_message(self, input_message): 
        if len(input_message) < 4: 
            return None 

        words = self.tokenize_and_lemmatize(input_message)
        bag = self.bag_of_words(words)

        bag_tensor = torch.tensor([bag], dtype=torch.float32)

        self.model.eval()
        with torch.no_grad():
            predictions = self.model(bag_tensor)

        predicted_class_index = torch.argmax(predictions, dim=1).item()
        predicted_intent = self.intents[predicted_class_index]

        if self.function_mappings:
            if predicted_intent in self.function_mappings:
                self.function_mappings[predicted_intent](input_message)

        if self.intents_responses[predicted_intent]:
            return random.choice(self.intents_responses[predicted_intent])
        else:
            return None
  
class rtmaps_python(BaseComponent):

    def __init__(self):
        BaseComponent.__init__(self)  


    # # # # # # # # # # # # # # # # # # 
    # Training
    def retrainModel(self):    
        print("This may take a while...")
        self.assistant = BrainAssistant('intents.json')
        self.assistant.parse_intents()
        self.assistant.prepare_data()
        self.assistant.train_model(batch_size=8, lr=0.001, epochs=1000)
        self.assistant.save_model("./trained/model.pth", "./trained/dimensions.json")
        print("Retraining done !") 

    # # # # # # # # # # # # # # # # # # 
    # Callbacks    
    def cb_stop(self, input_message): 
        print(f"[cb_stop]") 
        self.WriteTwist("stop")

    def cb_encore(self, input_message): 
        print(f"[cb_encore]") 
        self.WriteTwist(self.last_order)
        
    def cb_forward(self, input_message): 
        print(f"[cb_forward]") 
        self.WriteTwist("z")
        
    def cb_left(self, input_message): 
        print(f"[cb_left]") 
        self.WriteTwist("q")
        
    def cb_right(self, input_message): 
        print(f"[cb_right]") 
        self.WriteTwist("d")
        
    def cb_back(self, input_message): 
        print(f"[cb_back]")   
        self.WriteTwist("s")
 

    # # # # # # # # # # # # # # # # # # 

    def Dynamic(self): 
        self.add_input("text", rtmaps.types.ANY)  
        self.add_output("twist", rtmaps.types.FLOAT64)  
        self.add_action("retrain_model", self.retrainModel)

    def Birth(self):
        # # # # # # # # # # # # # # # # # # 
        # Brain Assistant
        self.function_mappings = {
                                'stop': self.cb_stop, 
                                'encore' : self.cb_encore,
                                'forward': self.cb_forward, 
                                'left': self.cb_left,
                                'right': self.cb_right,
                                'back': self.cb_back, 
                            } 
 
        self.assistant = BrainAssistant('intents.json', function_mappings = self.function_mappings)
        self.assistant.parse_intents()
        self.assistant.load_model("./trained/model.pth", "./trained/dimensions.json") 

        self.last_order = "stop"

    def Core(self):         
        input_data = self.inputs["text"].ioelt.data
        # Send input through intent model
        self.assistant.process_message(input_data)      

    def WriteTwist(self, order):  
        steering  = 0.0
        velocity  = 0.0

        self.last_order = order

        if order == "stop": 
            steering  = 0.0
            velocity  = 0.0

        elif order == "z": 
            steering  = 0.0
            velocity  = 1.0

        elif order == "s": 
            steering  = 0.0
            velocity  = -1.0

        if order == "q": 
            steering  = 90.0
 
        elif order == "d": 
            steering  = -90.0 

        # write on output 
        elt = rtmaps.types.Ioelt()
        elt.data = np.array([velocity, 0.0, 0.0, 0.0, 0.0, (steering)], dtype=np.float64)
        self.write("twist", elt)

    def Death(self):
        pass
