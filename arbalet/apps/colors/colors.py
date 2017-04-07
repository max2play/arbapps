#!/usr/bin/env python
"""
    Arbalet - ARduino-BAsed LEd Table
    Color Demonstrator - Arbalet Color Demonstrator

    Copyright 2015 Yoan Mollard - Arbalet project - http://github.com/arbalet-project
    License: GPL version 3 http://www.gnu.org/licenses/gpl.html
"""
import random
from arbalet.core import Application, Rate
from .generators import gen_random_flashing, gen_sweep_async, gen_sweep_rand
from time import sleep
import time

class ColorDemo(Application):
    generators = [gen_random_flashing, gen_sweep_async, gen_sweep_rand, ]

    def __init__(self, parser, animations):
        Application.__init__(self, parser, touch_mode='audioplayercontrol')                
        self.animations = animations
        config = animations[self.args.type]
        self.durations = [int(config['dur_min']*config['rate']), int(config['dur_max']*config['rate'])]
        self.rate = Rate(config['rate'])
        self.colors = config['colors']        
        self.generator = self.generators[config['generator_id']]
        
        # Set some values
        self.colors = [[1.0, 1.0, 1.0],[0.25, 1.0, 1.0],[0.5, 1.0, 1.0],[0.75, 1.0, 1.0],[0.15, 1.0, 1.0],[0.62, 1.0, 1.0],[0.35, 1.0, 1.0]]
        #self.colors = [[1.0, 1.0, 0.5],[0.25, 1.0, 0.5],[0.5, 1.0, 1.0],[0.75, 1.0, 1.0],[0.15, 1.0, 1.0],[0.62, 1.0, 1.0],[0.35, 1.0, 1.0]]
        self.animationtypes = animations.keys()
        self.currentanimation = i = 0
        for curranim in self.animationtypes:
            if curranim == self.args.type:                
                self.currentanimation = i
            i = i + 1
        self.generator_id = config['generator_id']
        self.is_touched = False
        self.lasttouched=["none"]
        self.touchpadactive = True
        self.timelasttouch = int(time.time())
        self.exit = False
    
    def process_events(self):        
        retval = False
        for event in self.arbalet.touch.get():
            # Catch not wanted double click
            if self.is_touched == False:            
                lasttouched = self.lasttouched.pop()
                
                # Activate Keypad
                self.timelasttouch = int(time.time())
                self.touchpadactive = True
                self.arbalet.touch.set_keypad(True)
                
                if event['key']=='next':                    
                    print('Change Colors...')
                    if len(self.colors) != 7:
                        # Reset to Default Colors
                        self.colors = [[1.0, 1.0, 1.0],[0.25, 1.0, 1.0],[0.5, 1.0, 1.0],[0.75, 1.0, 1.0],[0.15, 1.0, 1.0],[0.62, 1.0, 1.0],[0.35, 1.0, 1.0]]    
                    #Hue is the actual color from 0.0 (red) to 1.0 (also red because it's a wheel). 0.5 is cyan, 0.25 is green, 0.75 is purple...
                    #Saturation is its intensity from 0.0 to 1.0
                    #Value is its brightness from 0.0 (dark = black) to 1.0 (bright)                    
                    self.colors.append(self.colors.pop(0))
                    retval = True
                elif event['key']=='previous':                    
                    self.generator_id = (self.generator_id + 1) % 3
                    self.generator = self.generators[self.generator_id]
                    retval = True
                    print('Change Generator...')
                                     
                elif event['key']=='volup':
                    print("Make All Current Colors brighter")
                    for i in range(0, len(self.colors)):
                        self.colors[i][2] += 0.1
                    retval = True    
                    
                elif event['key']=='play':
                    print("Switch Animation Type")
                    self.currentanimation = (self.currentanimation + 1) % 5
                    config = self.animations[self.animationtypes[self.currentanimation]]
                    self.durations = [int(config['dur_min']*config['rate']), int(config['dur_max']*config['rate'])]
                    self.rate = Rate(config['rate'])
                    self.colors = config['colors']        
                    self.generator = self.generators[config['generator_id']]
                    retval = True
                elif event['key']=='voldown':                    
                    print("Make All Current Colors darker")
                    for i in range(0, len(self.colors)):
                        self.colors[i][2] -=  0.1
                    retval = True
                elif event['key']=='exit':
                    print("Exit")
                    self.exit = True
                
                    
                self.lasttouched.append(event['key'])                           
                self.is_touched = True                
            else:
                # Prevent double click
                self.is_touched = False
                
        return retval
    
    def create_generators(self):
        generators = []
        for h in xrange(self.height):
            line = []
            for w in xrange(self.width):
                duration = random.randrange(0, self.durations[1]-self.durations[0])
                line.append(self.generator(self.durations[0], int(2./self.rate.sleep_dur), duration, self.colors))
            generators.append(line)
        return generators
    
    def run(self):
        # Construct all pixel generators
        generators = self.create_generators()        

        # Browse all pixel generators at each time
        while self.exit == False:
            with self.model:
                for h in xrange(self.height):
                    for w in xrange(self.width):
                        try:
                            color = next(generators[h][w])
                        except StopIteration:
                            pass
                        else:
                            self.model.set_pixel(h, w, color)
            self.rate.sleep()
            
            if self.process_events():
                generators = self.create_generators()
                         
            if self.touchpadactive == True and self.timelasttouch < (int(time.time()) - 10):
                self.arbalet.touch.set_keypad(False)
                self.touchpadactive = False

        
        #Deactivate Touch
        self.arbalet.touch.toggle_touch()
        print("Touch Deactivated")
        self.model.set_all('black')
        sleep(1)  
        print("End of Colors")
        exit()
