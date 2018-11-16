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
import time
import errno
import getopt
from keymap import CheckEvent
from omxplayer.player import OMXPlayer
from collections import namedtuple
from thread import start_new_thread
from threading import Semaphore

JoyKeyStruct = namedtuple("JoyKeyStruct", "tp vl nm")

def check_pid(pid_):
    """Check if a pid exists in the current process table."""
    if pid_ < 0:
        return False
    try:
        os.kill(pid_, 0)
    except OSError, read_pid_error:
        return read_pid_error.errno == errno.EPERM
    
    return True

class YouPlay(object):
    """This is the class, wich provides the main functions of this
    programm. The playing of videos starts in the start_player function."""
    track_count = 0
    close_flag = 0
    sem = Semaphore()

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
        return self.sem

    def set_sem(self, sem_):
        """Set semaphore."""
        if sem_ == 0 and self.sem == 1:
            self.sem = sem_
        if sem_ == 1 and self.sem == 0:
            self.sem = sem_

    def close_video(self):
        """Quit a video."""
        self.sem.acquire()
        self.player.quit()
        self.sem.release()

    def start_player(self, argin):
        """This is the main function of this class. This function creates
        a playlist from standard input. Main functionality is to playing
        videos from the created playlist in a random order."""
        checkevent = CheckEvent()
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
        randvalue = random.SystemRandom()
        randvalue.shuffle(playlist)
        start_new_thread(checkevent.start_listen, (self,))
        while self.track_count < len(playlist):
            self.sem.acquire()
            video_url = playlist[self.track_count]
            self.track_count += 1
            try:
                video = pafy.new(video_url)
                video_best = video.getbest(preftype="mp4")
                video_url = video_best.url
                self.player = OMXPlayer(
                    video_url, ['-b', '--no-osd', '-o', 'alsa', '--layout', '5.1'])
                pid = subprocess.check_output(["pidof", 'omxplayer.bin'])
                pid = pid.replace("\n", "")
                self.sem.release()
                while check_pid(int(pid)):
                    time.sleep(0.2)
                # close app
                if self.close_flag == 1:
                    break
            except IOError, valid_link_error:
                # TODO: implement algorithm to handle invalid URLs
                #self.sem.acquire()
                self.sem.release()
                time.sleep(0)
            

def main(argv, argin):
    """Starting the main routine."""
    inputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:")
    except getopt.GetoptError:
        print('youtubeplayer.py <options> -i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('usage:\n\tyoutubeplayer.py <options> -i <inputfile>\n')
            print('options:\n'\
                '\t-rand\t= random playing videos\n'\
                '\t-h\t= print help text')
        elif opt == '-i':
            inputfile = arg
    if inputfile != '':
        youplayer = YouPlay()
        #youplayer.set_options()
        youplayer.start_player(inputfile)
    elif argin != None:
        youplayer = YouPlay()
        #youplayer.set_options()
        youplayer.start_player(argin)
    else:
        print 'youtubeplayer.py <options> -i <inputfile>\n'

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin))
