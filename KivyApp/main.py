#import kivy
#kivy.require('1.9.1') # replace with your current kivy version !

#******************************************************************
# BLE-PixMaker see LICENSE file for details of Apache-2.0 License.
#
# jaron42 effectively this is release 2.0 of Pixel Maker, however,
# the name was changed because of conflict with other apps.  This
# version was a full rewrite without original source code in an
# attempt to make it more portable to other platforms eventually.
# This first release worked on Windows XP using a BLE dongle which
# was accessed via socket commands to a blesocket helper service
# that did the BLE.  This worked for the beta testing in 2016, but
# the plan moving forward is to remove this dependency and get
# this kivy app running on Android using BLE natively.
#******************************************************************

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.properties import BoundedNumericProperty
import platform
from threading import Timer
#import bluetooth
#from bluetooth.ble import DiscoveryService
from time import sleep

import socket
import numpy as np

#def search():
    #devices = bluetooth.discover_devices(duration=20, lookup_names=True)
    # bluetooth low energy scan
    #service = DiscoveryService()
    #devices = service.discover(2)
    #return devices.items()
    #return devices

class GridButton(Button):
    background_state = BoundedNumericProperty(0, min=0, max=6)
    shadow_state = 0
    button_backgrounds = ['black_gray_border.png',
                          'red_gray_border.png',
                          'green_gray_border.png',
                          'yellow_gray_border.png',
                          'black_red_border.png',
                          'black_green_border.png',
                          'black_yellow_border.png',]

    def callback(self, instance):
        print('My button <%s>' % (instance))
        if(instance.background_state > 3):
            # Is a shadow state so go back to off
            instance.background_state = 0
        elif(instance.background_state == 3):
            instance.background_state = instance.shadow_state
        else:
            instance.background_state=instance.background_state+1
        instance.background_normal=instance.button_backgrounds[instance.background_state]
        #print('My button state <%s>' % (instance.background_state))
        #instance.Update

    def on_background_state(self, instance, value):
        if value > 3:
            instance.shadow_state = value;
        instance.background_normal=instance.button_backgrounds[value]
        
    def __init__(self, **kwargs):
        # make sure we aren't overriding any important functionality
        super(Button, self).__init__(**kwargs)
        self.background_normal=self.button_backgrounds[self.background_state]
        #self.bind(state=self.setter("state"))
        
class DisplayWidget(GridLayout):
    buttons = [[0 for x in range(8)] for y in range(8)]

    def deserializeStates(self, states):
        for x in range(8):
            for y in range(8):
                nextState = states[x*8+y]
                if 'O' == nextState:
                    # Check if a shadow state exists so it is not overritten
                    if self.buttons[x][y].shadow_state < 4:
                        self.buttons[x][y].background_state = 0
                elif 'R' == nextState:
                    self.buttons[x][y].background_state = 1
                elif 'G' == nextState:
                    self.buttons[x][y].background_state = 2
                elif 'Y' == nextState:
                    self.buttons[x][y].background_state = 3
                else:
                    # ignore shadow states
                    self.buttons[x][y].background_state = 0
                #End if
            #End y
        #End x
        print('The grid state is <%s>' % (states))

    def serializeStates(self):
        states = ''
        for x in range(8):
            for y in range(8):
                if 0 == self.buttons[x][y].background_state:
                    nextState = 'O'
                elif 1 == self.buttons[x][y].background_state:
                    nextState = 'R'
                elif 2 == self.buttons[x][y].background_state:
                    nextState = 'G'
                elif 3 == self.buttons[x][y].background_state:
                    nextState = 'Y'
                else:
                    # The state is one of the shadows of the previous frame
                    # default off
                    nextState= 'O'
                #End if
                states = states + nextState
            #End y
        #End x
        print('The grid state is <%s>' % (states))
        return states

    def deserializeShadowStates(self, states):
        for x in range(8):
            for y in range(8):
                nextState = states[x*8+y]
                if 'O' == nextState:
                    self.buttons[x][y].background_state = 0
                    self.buttons[x][y].shadow_state = 0
                elif 'R' == nextState:
                    self.buttons[x][y].background_state = 4
                elif 'G' == nextState:
                    self.buttons[x][y].background_state = 5
                elif 'Y' == nextState:
                    self.buttons[x][y].background_state = 6
                else:
                    #
                    self.buttons[x][y].background_state = 0
                #End if
            #End y
        #End x
        print('The grid state is <%s>' % (states))

    def callback(instance, value):
        print('My button <%s> state is <%s>' % (instance, value))

    def __init__(self, **kwargs):
        # make sure we aren't overriding any important functionality
        super(DisplayWidget, self).__init__(**kwargs)
        #size_hint=(0.1, 0.1),
        #pos_hint={'x': 0.2, 'y': 0.2},

        for x in range(8):
            for y in range(8):
                btn1 = GridButton(
                    text="",
                    background_color=[1, 1, 1, 1],
                    background_down='white_gray_border.png',
                    border=[4,4,4,4],
                    background_state=0)
                #btn2 = Button(
                #text="",
                #background_color=[1, 1, 1, 1],
                #background_normal='green_gray_border.png',
                #background_down='red_gray_border.png',
                #border=[4,4,4,4])
                #btn1.bind(state=callback)
                self.add_widget(btn1)
                btn1.bind(on_press=btn1.callback)
                self.buttons[x][y]=btn1

class RootWidget(FloatLayout):
    MAX_FRAMES = 42
    frame_count=1
    frames = ['O'*64] #start with one frame 64 Os to default all off
    current_frame=1
    repeats_run = 0
    
    def callback(instance, value):
        print('My button <%s> state is <%s>' % (instance, value))
        

    def add_callback(self, instance):
        if len(self.frames) < self.MAX_FRAMES:
            self.frames.append('O'*64)
            self.frame_count=self.frame_count + 1
            self.frame_count_label.text = str(self.frame_count)
        # for now just don't add if reached max, but a dialog would be nice
        #TODO

    def del_callback(self, instance):
        if len(self.frames) < 2:
            # must have at least one frame so they must mean clear it
            self.display_grid.deserializeStates('O'*64)
            self.frames[self.current_frame-1] = self.display_grid.serializeStates()
            return
        if self.current_frame == len(self.frames):
            # deleting the last frame so decrement after delete
            del self.frames[self.current_frame-1]
            self.current_frame = self.current_frame - 1
            self.current_frame_label.text = str(self.current_frame)
        else:
            # just delete because the next frame becomes the new current
            del self.frames[self.current_frame-1]
        #End if
        # refresh the display remember 0 index is frame 1
        self.frame_count = self.frame_count - 1
        self.frame_count_label.text = str(self.frame_count)        
        if self.current_frame > 1:
            # We need to draw the shadows of the previous frame
            self.display_grid.deserializeShadowStates(self.frames[self.current_frame-2])
        else:
            # need to zero out all shadow states
            self.display_grid.deserializeShadowStates('O'*64)     
        self.display_grid.deserializeStates(self.frames[self.current_frame-1])
 
    def next_callback(self, instance):
        if self.current_frame < self.frame_count:
            #First store the state of the current frame
            self.frames[self.current_frame-1] = self.display_grid.serializeStates()
            self.current_frame = self.current_frame + 1
            self.current_frame_label.text = str(self.current_frame)
            # refresh the display remember 0 index is frame 1
            if self.current_frame > 1:
                # We need to draw the shadows of the previous frame
                self.display_grid.deserializeShadowStates(self.frames[self.current_frame-2])
            else:
                # need to zero out all shadow states
                self.display_grid.deserializeShadowStates('O'*64)                
            self.display_grid.deserializeStates(self.frames[self.current_frame-1])

    def prev_callback(self, instance):
        if self.current_frame > 1:
            #First store the state of the current frame
            self.frames[self.current_frame-1] = self.display_grid.serializeStates()
            self.current_frame = self.current_frame - 1
            self.current_frame_label.text = str(self.current_frame)
            # refresh the display remember 0 index is frame 1
            if self.current_frame > 1:
                # We need to draw the shadows of the previous frame
                self.display_grid.deserializeShadowStates(self.frames[self.current_frame-2])
            else:
                # need to zero out all shadow states
                self.display_grid.deserializeShadowStates('O'*64)    
            self.display_grid.deserializeStates(self.frames[self.current_frame-1])

    def run_callback(self, instance):
        if instance.text == 'Run Animation':
            #First store the state of the current frame
            self.frames[self.current_frame-1] = self.display_grid.serializeStates()
            self.current_frame = 1
            # need to zero out all shadow states
            self.display_grid.deserializeShadowStates('O'*64)       
            self.current_frame_label.text = str(self.current_frame)
            self.display_grid.deserializeStates(self.frames[self.current_frame-1])
            self.t = Timer(int(self.anim_value_input.text)/1000.0, self.run_next_callback)
            instance.text = 'Stop Animation'
            self.repeats_run = 1
            self.t.start()
        else:
            # stop
            #TODO should we put it back to the original frame they were on?
            self.t.cancel()
            self.current_frame = 1
            self.current_frame_label.text = str(self.current_frame)
            self.display_grid.deserializeStates(self.frames[self.current_frame-1])
            instance.text = 'Run Animation'

    def run_next_callback(self):
        if self.current_frame < self.frame_count:
            # move to next and restart timer
            self.current_frame = self.current_frame + 1
            self.current_frame_label.text = str(self.current_frame)
            self.display_grid.deserializeStates(self.frames[self.current_frame-1])
            self.t = Timer(int(self.anim_value_input.text)/1000.0, self.run_next_callback)
            self.t.start()
        else:
            # Could still need to repeat
            if self.repeats_run < int(self.repeats_input.text):
                #run again
                self.repeats_run = self.repeats_run + 1
                self.current_frame = 1
                self.current_frame_label.text = str(self.current_frame)
                self.display_grid.deserializeStates(self.frames[self.current_frame-1])
                self.t = Timer(int(self.anim_value_input.text)/1000.0, self.run_next_callback)
                self.t.start()
            else:
                # stop   
                #TODO should we put it back to the original frame they were on?
                self.t.cancel()
                self.current_frame = 1
                self.current_frame_label.text = str(self.current_frame)
                self.display_grid.deserializeStates(self.frames[self.current_frame-1])
                self.run_animation.text = 'Run Animation'
            
    def download_animation_callback(self, instance):
        #First store the state of the current frame
        self.frames[self.current_frame-1] = self.display_grid.serializeStates()
        # Use socket instead of BLE
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        # appears hitting a max buffer size of 20 bytes
        buffer = 'C%02dD%04dR%04d' % (self.frame_count,int(self.anim_value_input.text),int(self.repeats_input.text))    
        client_socket.send(buffer.encode('ascii', 'ignore'))
        delay = 0.1
        for frame in self.frames:
            print('Slicing %s' % frame)
            for i in range(0,8):
                sleep(delay)
                # Note there is NO reason these should need an extra character
                # but the recieving side is not getting the last character
                # however if remove the program format is wrong
                buffer = frame[i*8:i*8+8] 
                print('Sending %s' % buffer)   
                client_socket.send(buffer.encode('ascii', 'ignore'))
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()        

    def __init__(self, **kwargs):
        # make sure we aren't overriding any important functionality
        super(RootWidget, self).__init__(**kwargs)
        sqr_dim=(Window.height/12.0)*8.0
        relative_left_side=(1-sqr_dim/Window.width)/2-0.05
        print('sqr_dim = %d'%sqr_dim)
        print('self.height = %d'%self.height)
        print('Window.height = %d'%Window.height)
        #sqr_w_prct=self.height*sqr_h_prct/self.width

        # init data
        
        # layout widgets
        #size_hint=(sqr_size, sqr_size),
        #size_hint=(.1, .1),
        self.display_grid = DisplayWidget(
            cols=8,
            rows=8,
            size=(sqr_dim, sqr_dim),
            size_hint=(None, None),
            pos_hint={'x': 0.2, 'y': 0.2},)
        self.add_widget(self.display_grid)
        add_frame = Button(
            color=[0.004, 0, 0.25098, 1],
            text='Add Frame',
            background_color=[1, 1, 1, 1],
            background_normal='green_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.18, 0.08),
            pos_hint={'x': relative_left_side, 'center_y': 11.1/12.0},)
        self.add_widget(add_frame)
        add_frame.bind(on_press=self.add_callback)
        self.current_frame_label = Button(
            color=[1, 0.859, 0.282, 1],
            text='%s'%self.current_frame,
            background_color=[1, 1, 1, 1],
            background_normal='purple_white_border.png',
            background_down='purple_white_border.png',
            border=[2,2,2,2],
            size_hint=(0.06, 0.04),
            pos_hint={'x': relative_left_side+0.185, 'center_y': 11.1/12.0},)
        self.add_widget(self.current_frame_label)
        frame_dash_label = Label(
            color=[1, 0.859, 0.282, 1],
            text='/',
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.23, 'center_y': 11.1/12.0},)
        self.add_widget(frame_dash_label)
        self.frame_count_label = Label(
            color=[1, 0.859, 0.282, 1],
            text='%s'%self.frame_count,
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.25, 'center_y': 11.1/12.0},)
        self.add_widget(self.frame_count_label)
        del_frame = Button(
            color=[0.004, 0, 0.25098, 1],
            text='Delete Frame',
            background_color=[1, 1, 1, 1],
            background_normal='green_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.2, 0.08),
            pos_hint={'x': relative_left_side+0.3, 'center_y': 11.1/12.0},)
        self.add_widget(del_frame)
        del_frame.bind(on_press=self.del_callback)
        prev = Label(
            color=[0.612, 0.612, 0.313, 1],
            text='Prev',
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side, 'y': 1.9/12.0},)
        self.add_widget(prev)
        next_label = Label(
            color=[0.612, 0.612, 0.313, 1],
            text='Next',
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.15, 'y': 1.9/12.0},)
        self.add_widget(next_label)
        prev_frame = Button(
            color=[0.004, 0, 0.25098, 1],
            text='<',
            background_color=[1, 1, 1, 1],
            background_normal='green_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side, 'y': 1.4/12.0},)
        self.add_widget(prev_frame)
        prev_frame.bind(on_press=self.prev_callback)
        self.next_frame = Button(
            color=[0.004, 0, 0.25098, 1],
            text='>',
            background_color=[1, 1, 1, 1],
            background_normal='green_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.15, 'y': 1.4/12.0},)
        self.add_widget(self.next_frame)
        self.next_frame.bind(on_press=self.next_callback)
        self.run_animation = Button(
            color=[1, 1, 1, 1],
            text='Run Animation',
            background_color=[1, 1, 1, 1],
            background_normal='blue_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.17, 0.05),
            pos_hint={'x': relative_left_side+0.25, 'y': 1.4/12.0},)
        self.add_widget(self.run_animation)
        self.run_animation.bind(on_press=self.run_callback)
        download_animation = Button(
            color=[0.004, 0, 0.25098, 1],
            text='Download\nAnimation',
            background_color=[1, 1, 1, 1],
            background_normal='green_white_border.png',
            background_down='white_gray_border.png',
            border=[4,4,4,4],
            size_hint=(0.2, 0.1),
            pos_hint={'x': relative_left_side, 'y': 0.01},)
        self.add_widget(download_animation)
        download_animation.bind(on_press=self.download_animation_callback)
        #self.anim_value=25
        self.anim_value_input = TextInput(
            foreground_color=[1, 0.859, 0.282, 1],
            text='%s'%100,
            background_color=[1, 1, 1, 1],
            background_normal='purple_white_border.png',
            border=[2,2,2,2],
            padding=[7,3,6,3],
            size_hint=(0.06, 0.04),
            pos_hint={'x': relative_left_side+0.21, 'y': 0.07},
            input_filter='int',)
        self.add_widget(self.anim_value_input)
        anim_value_units = Label(
            color=[1, 0.859, 0.282, 1],
            text='Anim Value',
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.3, 'y': 0.06},)
        self.add_widget(anim_value_units)
        #self.repeats=5
        self.repeats_input = TextInput(
            foreground_color=[1, 0.859, 0.282, 1],
            text='%s'%5,
            background_color=[1, 1, 1, 1],
            background_normal='purple_white_border.png',
            border=[2,2,2,2],
            padding=[7,3,6,3],
            size_hint=(0.06, 0.04),
            pos_hint={'x': relative_left_side+0.21, 'y': 0.03},
            input_filter='int',)
        self.add_widget(self.repeats_input)
        repeats_units = Label(
            color=[1, 0.859, 0.282, 1],
            text='# of Repeats',
            size_hint=(0.05, 0.05),
            pos_hint={'x': relative_left_side+0.3, 'y': 0.02},)
        self.add_widget(repeats_units)
        
class MainApp(App):

    def build(self):
        self.root = root = RootWidget()
        root.bind(size=self._update_rect, pos=self._update_rect)

        with root.canvas.before:
            Color(0.004, 0, 0.25098, 1)  # dark blue; colors range from 0-1 not 0-255
            self.rect = Rectangle(size=root.size, pos=root.pos)
        return root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

if __name__ == '__main__':
    Window.fullscreen = True
    
    print('platform.system = %s'%platform.system())
    #if(platform.system()=='Windows'):
    #else:
        #results =search()
        #if(results != None):
            #for address, name in results:
                #print('addres=%s name=%s',address, name)
            #End for
        #End if results found
    #End If
    MainApp().run()
