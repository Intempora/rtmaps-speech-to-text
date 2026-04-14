import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
import numpy as np

import keyboard


class rtmaps_python(BaseComponent):

    def __init__(self):
        BaseComponent.__init__(self)
        self.waypoints = []
        self.current_wp = 0
        self.last_path_ts = -1

    def Dynamic(self): 
        self.add_output("twist", rtmaps.types.FLOAT64) 

    def Birth(self):
        pass

    def Core(self):        
        steering  = 0.0
        velocity  = 0.0
 
        if keyboard.is_pressed('z'): 
            steering  = 0.0
            velocity  = 1.0

        elif keyboard.is_pressed('s'): 
            steering  = 0.0
            velocity  = -1.0

        if keyboard.is_pressed('q'): 
            steering  = 90.0
 
        elif keyboard.is_pressed('d'): 
            steering  = -90.0 

        # write on output 
        elt = rtmaps.types.Ioelt()
        elt.data = np.array([velocity, 0.0, 0.0, 0.0, 0.0, (steering)], dtype=np.float64)
        self.write("twist", elt)

    def Death(self):
        pass
