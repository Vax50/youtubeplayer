#!/usr/bin/env python
"""This application plays custom defined videos from youtube. It needs
a playlist as standard input, containing links of youtubevideos. An example of
a tracklist, is given in the file playlistexample.txt. This player supports
controlling through xbox 360 controller.

Controlling map:
pause, play:    A
close program   B
track forward:  RB
track backward: LB
play forward:   RT
play backward:  LT
volume up:      D-PAD UP
volume down:    D-PAD DOWN"""
import pafy
import sys
import os
import re
import random
import subprocess
import struct
import time
import errno
from omxplayer.player import OMXPlayer
from collections import namedtuple
from thread import start_new_thread
from dbus.exceptions import DBusException

JoyKeyStruct = namedtuple("JoyKeyStruct", "tp vl nm")

def check_pid(pid_):
    """Check if a pid exists in the current process table."""
    if pid_ < 0:
        return False
    try:
        os.kill(pid_, 0)
    except OSError, read_pid_error:
        return read_pid_error.errno == errno.EPERM
    else:
        return True

class YouPlay(object):
    """This is the class, wich provides the main functions of this
    programm. The playing of videos starts in the start_player function."""
    track_count = 0
    close_flag = 0
    sem = 0

    def get_player(self):
        """Returns the OMXPlayer object."""
        return self.player

    def get_track_count(self):
        """Returns the track number for the playlist."""
        return self.track_count

    def set_track_count(self, track_count_):
        """Set the track number."""
        self.track_count = track_count_

    def set_close_flag(self, close_flag_):
        """Set the close flag to quit the programm."""
        self.close_flag = close_flag_

    def get_sem(self):
        """Get semaphore."""
        sem_ = self.sem
        if self.sem == 0:
            self.set_sem(1)
        return self.sem

    def set_sem(self, sem_):
        """Set semaphore."""
        if sem_ == 0:
            if self.sem == 1:
                self.sem = sem_
        if sem_ == 1:
            if self.sem == 0:
                self.sem = sem_

    def close_video(self):
        """Quit a video."""
        player = self.get_player()
        sem = self.get_sem()
        if sem == 1:
            sem = 0
            self.set_sem(sem)
            player.quit()

    def check_event(self):
        """Check for a controlerkey event and executes
        additional instructions."""
        joy_dev_path = '/dev/input/js0'
        close_flag = 0
        play_pause_flag = 0
        while True:
            try:
                joy_dev = open(joy_dev_path, 'rb')
                break
            except IOError:
                time.sleep(1)

        while True:
            sem = self.get_sem()
            try:
                if sem == 1:
                    dev_buf = joy_dev.read(8)
                    if dev_buf:
                        joytime, value, button_type, number = struct.unpack(
                            'IhBB', dev_buf)
                        key_pressed = JoyKeyStruct(button_type, value, number)
                        if key_pressed == JoyKeyStruct(1, 1, 5):
                            # next track forward
                            self.close_video()
                        elif key_pressed == JoyKeyStruct(1, 1, 4):
                            # one track back
                            track_count = self.get_track_count()
                            if track_count == 1:
                                track_count -= 1
                            else:
                                track_count -= 2
                                self.close_video()
                            #self.set_track_count(track_count)
                        elif key_pressed == JoyKeyStruct(1, 1, 6):
                            # play backward
                            player = self.get_player()
                            try:
                                position_sec = player.position()
                                player.set_position(position_sec - 20)
                            except DBusException:
                                self.close_video()
                        elif key_pressed == JoyKeyStruct(1, 1, 7):
                            # play vorward
                            player = self.get_player()
                            try:
                                position_sec = player.position()
                                player.set_position(position_sec + 20)
                            except DBusException:
                                self.close_video()
                        elif key_pressed == JoyKeyStruct(1, 1, 0):
                            # pause and play video
                            player = self.get_player()
                            if play_pause_flag == 0:
                                play_pause_flag += 1
                                player.pause()
                            else:
                                play_pause_flag -= 1
                                player.play()
                        elif key_pressed == JoyKeyStruct(2, -32767, 5):
                            # volume up
                            subprocess.call(
                                ["amixer", '-M', 'set', 'PCM', '5%+'])
                        elif key_pressed == JoyKeyStruct(2, 32767, 5):
                            # volume down
                            subprocess.call(
                                ["amixer", '-M', 'set', 'PCM', '5%-'])
                        elif key_pressed == JoyKeyStruct(1, 1, 1):
                            # close application
                            close_flag = 1
                            self.set_close_flag(close_flag)
                            self.close_video()
                        self.set_sem(0)
                        os.system('clear')

            except IOError:
                try:
                    joy_dev = open(joy_dev_path, 'rb')
                except IOError:
                    time.sleep(1)
            time.sleep(0.05)

    def start_player(self, argin):
        """This is the main function of this class. This function creates
        a playlist from standard input. Main functionality is to playing
        videos from the created playlist in a random order."""
        playlist = []
        listcount = 0
        for line in argin:
            link_condition1 = re.match('^https://', line)
            #link_condition2 = re.search('()', line)
            if link_condition1 != None:
                line = line.replace("\n", "")
                url = line
                playlist.insert(listcount, url)
                listcount += 1
        local_time = time.localtime()
        seconds = time.mktime(local_time)
        random.seed(seconds)
        random.shuffle(playlist)
        start_new_thread(self.check_event, ())
        while self.get_track_count() < len(playlist):
            track_count = self.get_track_count()
            video_url = playlist[track_count]
            try:
                video = pafy.new(video_url)
                video_best = video.getbest(preftype="mp4")
                video_url = video_best.url
                track_count += 1
                self.track_count = track_count
                self.player = OMXPlayer(
                    video_url, ['-b', '-o', 'alsa', '--layout', '5.1'])
                pid = subprocess.check_output(["pidof", 'omxplayer.bin'])
                pid = pid.replace("\n", "")
                while check_pid(int(pid)):
                    self.set_sem(1)
                    time.sleep(0.2)
                    self.set_sem(0)
                # close app
                if self.close_flag == 1:
                    break
            except IOError, valid_link_error:
                time.sleep(0)

def main(argin):
    """Starting the main routine."""
    if argin != None:
        player = YouPlay()
        player.start_player(argin)
    else:
        print 'Usage: youtubeplayer.py "<YoutubeVideoUrl>"\n'

if __name__ == "__main__":
    sys.exit(main(sys.stdin))
