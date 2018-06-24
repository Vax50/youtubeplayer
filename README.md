# youtubeplayer

This Application is intended for raspberry pis. Developed and tested on 
raspbian. Play videos from youtube with user defined tracklists in a random 
order. Controlling of the player is only supported with an xbox 360 controller 
for now.

# Dependencies

- omxplayer
- omxplayer-wrapper
- pafy 
- pip 
- Python 2 >=2.7.9
- xboxdrv

Install pip and omxplayer:

    sudo apt-get update && sudo apt-get upgrade
    sudo apt-get install python-pip omxplayer

Install pafy and omxplayer-wrapper:

    pip install omxplayer-wrapper pafy

# Usage:

    cat playlistexample.txt | sudo python youtubeplayer.py

# Key Bindings

   Action       |   Key
:-------------: | ------------
 pause, play    |   A
 close program  |   B
 next track     |   RB
 one track back |   LB
 play forward   |   RT
 play backward  |   LT
 volume up      |   D-PAD UP
 volume down    |   D-PAD DOWN
