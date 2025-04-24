# setup
"""
This is the main program; it launches/starts 3 threads to do the work.
It also connects generators to the threads; the generators customize the result.
This code is NOT the place to customize a video, except to select the custom generator functions.

BUGS: make sure the audio pipe closes when the picture pipe closes. never terminated.
      play with the encoding quality. currently making 35GB with "-b:v", "5000k", BLU RAY quality?
      aspect ratio is 1:1 2048 x 2048. Add ... something... 2160 x 3840.
"""
import logging
logger = logging.getLogger(__name__)
format = "%(asctime)s %(filename)s %(lineno)d: %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
#logging.basicConfig(filename='myapp.log', level=logging.INFO)

import os
import tempfile
import logging
import threading
import encoder
import picture
import sound

import DragonVideo
picGen = DragonVideo.getPictureGenerator()

import DragonAudio
audGen = DragonAudio.getAudioGenerator(end=55*60*100) # duration: 55 minutes of 1/100 sec frames

xImg = 1920
yImg = 1080
outputfile="/home/c/Desktop/Dragons.mp4" # must have .mp4 extension, maybe needs full path
logger.debug(F"xImg={xImg} yImg={yImg}")
# start the threads. they block, momentarily, as the pipes are connected
# because the pipe must have two endpoints (regardless of direction r/w)
# https://stackoverflow.com/a/24099738 
tmpdir = tempfile.mkdtemp()
audPipe = os.path.join(tmpdir, "audPipe")
os.mkfifo(audPipe)
vidPipe = os.path.join(tmpdir, "vidPipe")
os.mkfifo(vidPipe)
t1=threading.Thread(target=encoder.setup, args=(audPipe,vidPipe,xImg,yImg,outputfile)).start() # deamon, no join needed
t2=threading.Thread(target=sound.setup, args=(audPipe,audGen)).start() # deamon, no join needed
t3=threading.Thread(target=picture.setup, args=(vidPipe,picGen)).start() # deamon, no join needed
logger.debug("after")
raise SystemExit(0)



# profile:
      # python3 -m cProfile -o test.stats begin.py
      # gprof2dot --colour-nodes-by-selftime -f pstats test.stats | dot -Tpng -o output.png

