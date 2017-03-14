#!/usr/bin/env python
"""
    Arbalet - ARduino-BAsed LEd Table
    Menu to Run Arbalet applications

    Runs and closes Arbalet apps according to a menu file

    Copyright 2017 Stefan Rick - Max2Play project - http://github.com/max2play
    License: GPL version 3 http://www.gnu.org/licenses/gpl.html
    
    EXECUTE WITH
    ~/Arbalet/arbapps/arbalet/tools/menu $ python menu.py -ng -w --server
    
"""
from arbalet.core import Application, Rate
from os.path import isfile, join, realpath, dirname
from os import chdir
from sys import executable 
from json import load
from subprocess import Popen
from glob import glob
from shlex import split
from time import sleep, time
from pygame import JOYBUTTONDOWN
from signal import SIGINT, signal
import pygame
import argparse

class Menu(Application):
    BG_COLOR = 'black'
    PIXEL_COLOR='darkred'
    is_touched = False
    
    def __init__(self, argparser, touch_mode='quadridirectional'):
        self.start_server(True, True)
        
        Application.__init__(self, argparser, touch_mode=touch_mode)        
        self.running = True
 
    def run(self):        
        
        if len(self.args.menu) > 0:
            menu_file = join(realpath(dirname(__file__)), self.args.menu)
            if not isfile(menu_file):
                print("[Arbalet Menu] Menu file '{}' not found".format(menu_file))
            else:                
                # read the Menu
                with open(menu_file) as fmenu:
                    self.menu = load(fmenu)
                # and launch every app in the sequence as a client
                try:
                    self.execute_menu()
                finally:                    
                    self.model.set_all(self.BG_COLOR)
                    self.model.flash()      
                    self.close_server()
                    print("Exit")
    
    def close_server(self):
        if self.server_process:
            self.server_process.send_signal(SIGINT)
            self.server_process.wait()
            self.server_process = None
    
    def start_server(self, hardware, no_gui):
        command = "{} -m arbalet.tools.server".format(executable)
        if hardware:
            command += ' -w'
        if no_gui:
            command += ' -ng'
        print("[Arbalet Sequencer] Starting server with: " + command)
        self.server_process = Popen(command.split())
    
    def close_processes(self, signal, frame):
        self.running = False
        
    def execute_appstart(self, appdetails):        
        
        def purify_args(args):
            for rm_arg in ['-h, --hardware', ]:
                try:
                    args.remove(rm_arg)
                except ValueError:
                    pass
            for add_arg in ['--no-gui', '--server']:
                args.append(add_arg)
            return args

        def expand_args(args, cwd):            
            expanded_args = []
            for arg in args:
                globed_arg = glob(arg)
                if len(globed_arg)==0:
                    expanded_args.append(arg)
                else:
                    for expanded_arg in globed_arg:
                        expanded_args.append(expanded_arg)
            return expanded_args
        
        # close Arbalink
        self.arbalet.arbalink.close()
        self.arbalet.arbaclient.close()
        self.arbalet.events.close()
        print("Arbalink and Arbaclient closed")
        
        
        args = "{} -m {} {}".format(executable, appdetails['app'], appdetails['args'] if 'args' in appdetails else '')
        module_command = purify_args(expand_args(args.split(), join(*appdetails['app'].split('.'))))
        while self.running:  # Loop allowing the user to play again, by restarting app
            print("[Arbalet Sequencer] STARTING {}".format(module_command))                        
            
            process = Popen(module_command, cwd=self.cwd)
            timeout = appdetails['timeout'] if 'timeout' in appdetails else -1
            reason = self.wait(timeout, appdetails['interruptible'], process) # TODO interruptible raw_input in new_thread for 2.7, exec with timeout= for 3
            print("[Arbalet Sequencer] END: {}".format(reason))
            if reason != 'terminated' or not self.running:
                process.send_signal(SIGINT)
                process.wait()
            if reason != 'restart':
                break
        
        #Reconnect to Table
        print("Reinit Hardware")
        sleep(1)
        self.arbalet.reinit_hardware()
        print("Reinit Hardware Done")
        
    def wait(self, timeout=-1, interruptible=False, process=None):
        start = time()
        # We loop while the process is not terminated, the timeout is not expired, and user has not asked 'next' with the joystick
        while self.running and (timeout < 0 or time()-start < timeout) and (process is None or process.poll() is None):
            for e in self.arbalet.events.get():
                if interruptible and e.type == JOYBUTTONDOWN and e.button in self.arbalet.joystick['back']:
                    # A "back" joystick key jumps to the next app, unless interruptible has been disabled
                    return 'joystick'
                elif e.type == JOYBUTTONDOWN and e.button in self.arbalet.joystick['start']:
                    # A "start" joystick key restarts the same app
                    return 'restart'
                else:
                    # Any other activity resets the timer
                    start = time()
            sleep(0.01)
        return 'timeout' if (process is None or process.poll() is None) else 'terminated'
    
    def process_events(self):        
        retval = False
        for event in self.arbalet.touch.get():
            if self.is_touched == False:
                x, y=self.queue.pop(0)
                self.model.set_pixel(x,y, self.BG_COLOR)
                
                if event['key']=='up' and x > 0:
                    x -= 1
                elif event['key']=='down' and x < self.height-1:
                    x += 1
                elif event['key']=='right' and y < self.width-1:
                    y += 1
                    # start App
                    self.execute_appstart(self.menu['menu'][x])
                    retval = True                    
                elif event['key']=='left' and y > 0:
                    y -= 1            
                self.model.set_pixel(x,y, self.PIXEL_COLOR)                
                self.is_touched = True
                
                self.queue.append((x, y))
            else:
                self.is_touched = False
                
        return retval
    
    def execute_menu(self):        
        
        # change WD to the modules' root        
        self.cwd = join(realpath(dirname(__file__)), '..', '..', 'apps')
        chdir(self.cwd)
        
        # Init Table and show Menu Options
        self.model.set_all(self.BG_COLOR)
        self.model.flash()      
        
        # Print Apps
        i = 1
        for command in self.menu['menu']:
            # Print Line for Selection
            self.model.write("   {} {}".format(i,command['app']), 'blue')            
            #print("_ {} {}".format(i,command['app']))
            i += 1
        
        # Print Menu control
        row = 1
        for command in self.menu['menu']:
            for y in range(row):
                 self.model.set_pixel(row,y, 'blue')
            row += 1
           
        self.HEAD=(0,5)
        self.queue=[self.HEAD]
        self.model.set_pixel(self.HEAD[0],self.HEAD[1], self.PIXEL_COLOR)
                
        while True:
             if self.process_events() == True:
                row = 1
                for command in self.menu['menu']:
                    for y in range(row):
                         self.model.set_pixel(row,y, 'blue')
                    row += 1
             sleep(0.2)
             
             
parser = argparse.ArgumentParser(description='Application Menu: Start different Applications defined in a menu.json')
parser.add_argument('-q', '--menu',
                    type=str,
                    default='menus/default.json',
                    nargs='?',
                    help='Configuration file describing the sequence of apps to launch')
Menu(parser).start()
             
