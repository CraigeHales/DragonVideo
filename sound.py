# music functions
"""
This is the sound pumper thread. It pumps audio from a generator to the encoder via a pipe.
This code is NOT the place to customize a video. Do that in the generator.
"""
import logging
logger = logging.getLogger(__name__)
#import math
import numpy as np
# import wave
import threading
# wav = wave.open("PianoBell.wav", mode='rb')

# logger.info(f"{wav.getnchannels()}: audio channels (1 for mono, 2 for stereo).")
# assert wav.getnchannels()==2
# logger.info(f"{wav.getsampwidth()}: sample width in bytes.")
# assert wav.getsampwidth()==2
# logger.info(f"{wav.getframerate()}: sampling frequency.")
# assert wav.getframerate()==44100
# logger.info(f"{wav.getnframes()}: number of audio frames.")
# assert wav.getnframes()>44100*8*12*8 # the wav is 44100 x Stereo x 16 bits x 8 seconds per note x 12 notes per octave x 8+ octaves 
# logger.info(f"{wav.getcomptype()}: compression type ('NONE' is the only supported type).")
# logger.info(f"{wav.getcompname()}: Human-readable version of getcomptype(). Usually 'not compressed' parallels 'NONE'.")
# # a frame is two 16 bit samples
# wavdat = wav.readframes(wav.getnframes())
# wav.close()
# wavdat = wavdat[0:int(44100*2*2*8*12*8)]
# piano = np.reshape(np.frombuffer(wavdat, dtype=np.int16), (8,12,44100*8,2)) # octave 0..7, note 0..1, 8 seconds, L+R
# # composer
# # two piano notes that overlap the 8 second interval for each 
# # get combined. A sequencer determines what note and when will
# # start next; the 8 seconds of data for the not are blended into a 1 second + 8 seconds
# # composition buffer. when the sequencer is beyond the 1 second area, send the 1 second
# # completed part. (8 seconds is from the wav file note duration/spacing)

class AudioBuffer:
    def __init__(self):
        self.buffer = np.zeros((44100 * 8, 2), np.float32)  # keep -1.0 ... 1.0 sample data
        self.position = 0
        self.circleLock = threading.Lock()

    def removez(self, buf):  # removes (leaving zeros) the oldest data and returns in buf
        assert buf.dtype == np.int16
        with self.circleLock:
            remainingSize = buf.shape[0]  # destination buffer size implies amount to (re)move
            assert remainingSize <= self.buffer.shape[0] and buf.shape[1] == 2 and self.buffer.shape[1] == 2
            firstChunkSize = min(remainingSize, self.buffer.shape[0] - self.position)
            buf[:firstChunkSize, :] = self.buffer[self.position:self.position + firstChunkSize, :].round().astype(np.int16)
            self.buffer[self.position:self.position + firstChunkSize, :] = 0
            self.position += firstChunkSize
            remainingSize -= firstChunkSize
            if remainingSize > 0:
                buf[firstChunkSize:, :] = self.buffer[:remainingSize, :].round().astype(np.int16)
                self.buffer[:remainingSize, :] = 0
                self.position = remainingSize
            elif self.position >= self.buffer.shape[0]:
                self.position -= self.buffer.shape[0]
                assert self.position == 0
            assert 0 <= self.position and self.position < self.buffer.shape[0]

    def overlay(self, buf):  # overlay new data at current position. Only removez will advance position.
        if buf is not None:  # generators feed None instead of np.zeros
            with self.circleLock:
                remainingSize = buf.shape[0]
                assert remainingSize <= self.buffer.shape[0] and buf.shape[1] == 2 and self.buffer.shape[1] == 2
                firstChunkSize = min(remainingSize, self.buffer.shape[0] - self.position)
                # the += on the next line overlays this data on existing data (or zeros)
                self.buffer[self.position:self.position + firstChunkSize, :] += buf[:firstChunkSize, :]
                remainingSize -= firstChunkSize
                if remainingSize > 0:
                    self.buffer[:remainingSize, :] += buf[firstChunkSize:, :]


ab = AudioBuffer()

def setup(audPipe,generator):
    logger.info('Started')
    logger.debug(f"opening {audPipe}")
    f = open(audPipe, "wb")
    logger.debug(f"opened {audPipe}")
    # # write 5 seconds of 44100 x 16 bit x 2 chan signed 16 bit little endian
    # # 440Hz tone left, 1kHz tone right
    # leftCyclesPerSample = 440.0/44100.0
    # leftpos=0
    # rightCyclesPerSample = 1000.0/44100.0
    # rightpos=0
    # pair = np.zeros(2,dtype=np.int16)
    # for i in range(44100*5):
    #     pair[0]=10000*math.sin(leftpos)
    #     leftpos+=leftCyclesPerSample
    #     pair[1]=10000*math.sin(rightpos)
    #     rightpos+=rightCyclesPerSample
    #     # does not work pair.tofile(f) https://stackoverflow.com/a/64218229  https://stackoverflow.com/questions/55889401/obtaining-file-position-failed-while-using-ndarray-tofile-and-numpy-fromfile
    #     #f.write(memoryview(pair))
    #     #bytesPerNote=44100*2*2*8
    #     #desiredNote=50
    #     #notedata=wavdat[bytesPerNote*desiredNote:bytesPerNote*(desiredNote+1)]
    #     #f.write(notedata)
    finished = False # needs work, manually set with debugger
    circlebuf = None
    # volume = 0.5
    buf = np.zeros((441,2), dtype=np.int16)
    for a in generator:
        if a is not None:
            ab.overlay(a) # np.asarray(a) for memoryview
        # if a is not None:
        #     b = volume * np.asarray(a)
        #     if circlebuf is None:
        #         circlebuf = b
        #         circlepnt = 0
        #     else:
        #         if circlepnt == 0:
        #             circlebuf[ : , : ] += b[ : , : ]
        #         else:
        #             circlebuf[ circlepnt: , : ] += b[ :-circlepnt , : ]
        #             circlebuf[ :circlepnt , : ] += b[ -circlepnt: , : ]
        # f.write(circlebuf[circlepnt:circlepnt+441,:].round().astype(np.int16))
        # circlebuf[circlepnt:circlepnt+441,:] = 0
        # circlepnt+=441
        # if circlepnt >= circlebuf.shape[0]:
        #     circlepnt -= circlebuf.shape[0]
        ab.removez(buf)
        f.write(buf)
        if finished:
            break
    f.close()
    logger.debug(f"closed {audPipe}")
    logger.info('Finished')
