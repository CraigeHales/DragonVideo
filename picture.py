# image functions
"""
This is the picture pumper thread; it pumps pictures from a generator to the encoder via a pipe.
This code is NOT the place to customize a video. Do that in the generator.
"""
import numpy as np
import math
import logging
logger = logging.getLogger(__name__)

def setup(vidPipe,generator):
    logger.info('Started')
    logger.debug(f"opening {vidPipe}")
    f = open(vidPipe, "wb")
    logger.debug(f"opened {vidPipe}")
# write 5 seconds of 2kx2kx30FPS
#    image = np.zeros((2048,2048,3),dtype=np.int8)
#    image[:,:,1] = 255 # all green
#    for i in range(30*5):
    finished = False # needs work, manually set with debugger
    for image in generator:
        y,x,z=image.shape
        for j in range(y):
            f.write(memoryview(image[j,:,:]))
        if finished:
            break            
    f.close()
    logger.debug(f"closed {vidPipe}")
    logger.info('Finished')