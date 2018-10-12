from dbus.exceptions import DBusException
import time
import struct
import os
import subprocess
import keyboard
from collections import namedtuple

JoyKeyStruct = namedtuple("JoyKeyStruct", "tp vl nm")

class CheckEvent:
    """Check for a controlerkey event and executes
    additional instructions."""
    play_pause_flag = 0
    controller_dev = 0
    xbox_joy_dev_path = '/dev/input/js0'
    actionList = [8]
    xbox_joy_dev = None

    def set_dev_type(self):
        if self.controller_dev == 0:
            self.actionList.insert(0, JoyKeyStruct(1, 1, 5))
            self.actionList.insert(1, JoyKeyStruct(1, 1, 4))
            self.actionList.insert(2, JoyKeyStruct(1, 1, 6))
            self.actionList.insert(3, JoyKeyStruct(1, 1, 7))
            self.actionList.insert(4, JoyKeyStruct(1, 1, 0))
            self.actionList.insert(5, JoyKeyStruct(2, -32767, 5))
            self.actionList.insert(6, JoyKeyStruct(2, 32767, 5))
            self.actionList.insert(7, JoyKeyStruct(1, 1, 1))
        elif self.controller_dev == 1:
            self.actionList.insert(0, 'f')
            self.actionList.insert(1, 'b')
            self.actionList.insert(2, 'left')
            self.actionList.insert(3, 'right')
            self.actionList.insert(4, 'space')
            self.actionList.insert(5, 'up')
            self.actionList.insert(6, 'down')
            self.actionList.insert(7, 'esc')

    def __init__(self):
        self.set_dev_type()

    """Dev 0 = XboxJoy, Dev 1 = Keyboard"""
    def check_xbox_joy_dev(self):
        """Check if Input Device exists"""
        if self.controller_dev == 0:
            while True:
                try:
                    self.xbox_joy_dev = open(self.xbox_joy_dev_path, 'rb')
                    break
                except IOError:
                    time.sleep(1)

    def get_input_event(self):
        if self.controller_dev == 0:
            try:
                dev_buf = self.xbox_joy_dev.read(8)
                if dev_buf:
                    joytime, value, button_type, number = struct.unpack(
                        'IhBB', dev_buf)
                    return JoyKeyStruct(button_type, value, number)

            except IOError:
                try:
                    self.xbox_joy_dev = open(self.xbox_joy_dev_path, 'rb')
                except IOError:
                    time.sleep(1)
                    return False
        if self.controller_dev == 1:
            try:
                key_event = keyboard.read_event()
                if key_event.event_type == 'down':
                    return key_event.name
                return False
            except IOError:
                return False

    def start_listen(self, youplay):
        if self.controller_dev == 0:
            self.check_xbox_joy_dev()
        while True:
            sem = youplay.get_sem()
            if sem == 1:
                key_pressed = self.get_input_event()
                if key_pressed != False:
                    if key_pressed == self.actionList[0]:
                        # next track forward
                        youplay.close_video()
                    elif key_pressed == self.actionList[1]:
                        # one track back
                        track_count = youplay.get_track_count()
                        if track_count == 1:
                            youplay.track_count -= 1
                        elif track_count >= 2:
                            youplay.track_count -= 2
                            youplay.close_video()    
                    elif key_pressed == self.actionList[2]:
                        # play backward
                        player = youplay.get_player()
                        try:
                            position_sec = player.position()
                            player.set_position(position_sec - 20)
                        except DBusException:
                            youplay.close_video()
                    elif key_pressed == self.actionList[3]:
                        # play vorward
                        player = youplay.get_player()
                        try:
                            position_sec = player.position()
                            player.set_position(position_sec + 20)
                        except DBusException:
                            youplay.close_video()
                    elif key_pressed == self.actionList[4]:
                        # pause and play video
                        player = youplay.get_player()
                        if self.play_pause_flag == 0:
                            self.play_pause_flag += 1
                            player.pause()
                        else:
                            self.play_pause_flag -= 1
                            player.play()
                    elif key_pressed == self.actionList[5]:
                        # volume up
                        subprocess.call(
                            ["amixer", '-M', 'set', 'PCM', '5%+'])
                    elif key_pressed == self.actionList[6]:
                        # volume down
                        subprocess.call(
                            ["amixer", '-M', 'set', 'PCM', '5%-'])
                    elif key_pressed == self.actionList[7]:
                        # close application
                        close_flag = 1
                        youplay.set_close_flag(close_flag)
                        youplay.close_video()
                    #os.system('clear')
            time.sleep(0.05)
