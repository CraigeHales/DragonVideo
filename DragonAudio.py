"""
custom generator for audio
"""

import logging
logger = logging.getLogger(__name__)
#import math
import numpy as np
import wave
import random

import mingus.core.notes as notes
import mingus.core.scales as scales
import mingus.core.chords as chords # pip install mingus

def getSamples(filename):
    logger.info(f"{filename}: opening.")
    wav = wave.open(filename, mode='rb')

    logger.info(f"{wav.getnchannels()}: audio channels (1 for mono, 2 for stereo).")
    assert wav.getnchannels()==2
    logger.info(f"{wav.getsampwidth()}: sample width in bytes.")
    assert wav.getsampwidth()==2
    logger.info(f"{wav.getframerate()}: sampling frequency.")
    assert wav.getframerate()==44100
    logger.info(f"{wav.getnframes()}: number of audio frames.")
    assert wav.getnframes()>44100*8*12*8 # the wav is 44100 x Stereo x 16 bits x 8 seconds per note x 12 notes per octave x 8+ octaves 
    logger.info(f"{wav.getcomptype()}: compression type ('NONE' is the only supported type).")
    logger.info(f"{wav.getcompname()}: Human-readable version of getcomptype(). Usually 'not compressed' parallels 'NONE'.")
    # a frame is two 16 bit samples
    wavdat = wav.readframes(wav.getnframes())
    wav.close()
    wavdat = wavdat[0:int(44100*2*2*8*12*8)]
    samps = np.reshape(np.frombuffer(wavdat, dtype=np.int16), (8,12,44100*8,2)) # octave 0..7, note 0..11, 8 seconds, L+R
    return samps.astype(np.float32)


piano = getSamples("PianoBell.wav") * .4
choir = getSamples("AhhChoir1.wav") * .4
organ = getSamples("OrganRisingSun.wav") * .4
psine = getSamples("puresine.wav") * .4

# c1 = [2, 5, 8, 11]
# c2 = [1, 4, 7, 10]
# def getAudioGenerator(duration):
#     for i in range(duration):
#         if i%1500 == 0:
#             yield memoryview(piano[6,10,:,:])
#         elif i%500 == 0:
#             yield memoryview(piano[5,c2[random.randrange(len(c2))],:,:])
#         elif i%250 == 0:
#             yield memoryview(piano[4,c2[random.randrange(len(c2))],:,:])
#         elif i%200 == 0:
#             yield memoryview(piano[3,c2[random.randrange(len(c2))],:,:])
#         elif i%150 == 0:
#             yield memoryview(piano[0,c1[random.randrange(len(c1))],:,:])
#         elif i%100 == 0:
#             yield memoryview(piano[1,c1[random.randrange(len(c1))],:,:])
#         elif i%50 == 0:
#             yield memoryview(piano[2,c1[random.randrange(len(c1))],:,:])
#         elif i%25 == 0:
#             yield memoryview(piano[3,c1[random.randrange(len(c1))],:,:])
#         else:
#             yield None
#         i+=1
        
# def pianoGenerator(begin,end,step,octave,note):
#     for i in range(2000000000):
#         if (begin <= i and i <= end) and (i - begin) % step == 0:
#             yield memoryview(piano[octave[random.randrange(len(octave))],note[random.randrange(len(note))],:,:])
#         else:
#             yield None

notelist = None

def notesGenerator(begin,end,step,octave,volume,play):
    for i in range(2000000000):
        if begin <= i and i <= end and (i - begin) % step == 0:
            yield piano[octave,notelist[random.randrange(len(notelist))],:,:]*volume*play(i)
        else:
            yield None


LENGTH100=200 # hundredths of a second
fade = np.ones(((44100) * 8, 2), np.float32)
fade[44100*LENGTH100//100 : 44100*LENGTH100//100 + (44100//4) , 0] = np.arange((44100//4),0,-1)/(44100//4)
fade[44100*LENGTH100//100 + (44100//4) : , 0] = 0
fade[:,1] = fade[:,0]
def chordGenerator(begin,end,step,octave,volume):
    global notelist
    ctab = Ctab("C1")
    for i in range(2000000000):
        if (begin <= i and i <= end) and (i - begin) % step == 0:
            secs=int(i/100)
            mins=int(secs/60)
            secs -= mins*60
            print(f"{mins}:{secs} ",end="")
            key = "major" if i%12000 < 6000 else "minor"
            print(key,end=" ")
            notelist = ctab.nextNotes(key)
            result = psine[octave,notelist[0],:,:]*fade
            for i in range(1,len(notelist)):
                result += psine[octave,notelist[i],:,:]*fade
            yield result*volume
        else:
            yield None

def getAudioGenerator(end):
    g = [
            chordGenerator(begin=0,end=end,step=LENGTH100,octave=4,volume=.125),
            # the high notes play in the transition from 3.5 to 15 seconds...
            # ramp 0 : 0.1      500 : 1.0    1000 : 1.0   1500 : 0.1
            notesGenerator(begin=0,            end=end,step=LENGTH100//5,octave=6,volume=.0625,play=lambda x: (x%1500 - 500)/500*.8+.2 if x%1500 < 500 else 1.0 if x%1500 < 1000 else 1-(x%1500 - 1000)/500*.8+.2),
            notesGenerator(begin=LENGTH100//10,end=end,step=LENGTH100//5,octave=5,volume=.125, play=lambda x: (x%1500 - 500)/500*.8+.2 if x%1500 < 500 else 1.0 if x%1500 < 1000 else 1-(x%1500 - 1000)/500*.8+.2),
            #
            notesGenerator(begin=0,end=end,step=LENGTH100//4,octave=3,volume=.25,play=lambda x: 0.75),
            notesGenerator(begin=LENGTH100//8,end=end,step=LENGTH100//4,octave=2,volume=0.75,play=lambda x: 1.0),
            #
            notesGenerator(begin=0,end=end,step=LENGTH100//2,octave=2,volume=1.0,play=lambda x: 1.0),
        ]
    for i in range(end):
        result = None
        for gen in g:
            r = next(gen)
            if r is not None:
                if result is None:
                    result = np.asarray(r)*1
                else:
                    result += np.asarray(r)
        yield result


# def getAudioGenerator(end):
#     f1 = end//7
#     f2 = 2*f1
#     f3 = 3*f1
#     f4 = 4*f1
#     f5 = end
#     g = [
#             pianoGenerator(begin=0,end=f1,step=50,octave=[4],note=[1, 3, 5,]),
#             pianoGenerator(begin=f1,end=f2,step=50,octave=[4],note=[3, 5, 7]),
#             pianoGenerator(begin=f2,end=f3,step=50,octave=[4],note=[5, 7, 10]),
#             pianoGenerator(begin=f3,end=f4,step=50,octave=[4],note=[1, 3, 7]),
#             pianoGenerator(begin=f4,end=f5,step=50,octave=[4],note=[1, 5, 10]),
#         ]
#     for i in range(end):
#         result = None
#         for gen in g:
#             r = next(gen)
#             if r is not None:
#                 if result is None:
#                     result = np.asarray(r)*1
#                 else:
#                     result += np.asarray(r)
#         yield result

class Ctab:
    # this state table is a dictionary with chord names keys for states (left-most column)
    # column 2 is a set of variations the chord might be played with
    # column 3 (top and bottom) is the next chord to use to stay in/move to major (lighter)
    # column 4 (top and bottom) is the next chord to use to stay in/move to minor (darker)
    # Dm Am F are the common chords between the table and where the change
    # from major to minor happens; if the minor/major flag changes, either the very next
    # state can be in the other half of the table OR one more  
    # fmt: off
    transitionTable = { # see https://mugglinworks.com/chordmaps/ (Thanks!)
        # this half is the C Major progression (1 suffix on state names)
        # state   choices of chords for state          choices of next state to stay in major         choices to switch to minor
        "C1":   (("C","C6","CM7","CM9",),             ("Dm1","Em1","F1","G1","Am1","C/G1","F/C1",), ("Dm1","Am1","F1",),), # "Csus",
        "Dm1":  (("Dm","Dm7",),                       ("G1","G1","Em1","C/G1",),                    ("Am2","Bdim2","Am/E2",),), # "Dm9","E2",
        "Em1":  (("Em","Em7",),                       ("C1","C1","Am1","F1",),                      ("Am1","F1",),),
        "F1":   (("F","F6",),                         ("C1","C1","Dm1","G1","C/G1",),               ("Dm2","Bdim2",),),  # "FM7",
        "G1":   (("G","G7","Gsus",),                  ("C1","C1","Em1","Am1",),                     ("Am2",),), # "G13","G9","G11",
        "Am1":  (("Am",),                             ("F1","F1","Dm1",),                           ("Bdim2","Dm2","F2",),), ###"Caug2","E2",
        "C/G1": (("C/G",),                            ("G1",),                                      ("G1",),),
        "F/C1": (("F/C","G/C",),                      ("C1",),                                      ("C1",),),
        # this half is the A Minor progression (2 suffix on state names)
        # state    choices of chords for state     choices to switch to major   choices of next state to stay in minor
        "Am2":   (("Am",),                         ("F1","Dm1",),             ("Bdim2","Dm2","F2","Am/E2","Dm/A2",),),   ###"Caug2","E2",
        "Bdim2": (("Bdim","G#dim/B",),             ("Am2",),                  ("Am/E2",),), #     ###"Caug2","E2",
        #"Caug2": (("Caug","Am/C",),                ("Am2","Dm2","F2",),       ("Am2","Dm2","F2",),), # 
        "Dm2":   (("Dm","Dm7",),                   ("G1","Em1","C/G1",),      ("Am2","Bdim2","Am/E2",),), # "Dm9",   ###"E2",
        "E2":    (("E",),                          ("Am2","F2",),             ("Am2","F2",),), # "Esus","Eb9","E7","Eb13",  ###"Caug2",
        "F2":    (("F","F6",),                     ("Dm1","G1","C/G1","C1",), ("Dm2","Bdim2",),), # "FM7",
        "Am/E2": (("Am/E",),                       ("E2",),                   ("E2",),),
        "Dm/A2": (("Dm/A",),                       ("Am2",),                  ("Am2",),), # "E/A",
    }
    # fmt: on

    def __init__(self, nextChordName="C1"):
        self.nextChordName = nextChordName
    
    def nextNotes(self, majmin):
        print(self.nextChordName, end=" ")
        chordChoices, newMajorNames, newMinorNames = self.transitionTable[self.nextChordName]
        if majmin == "major":
            self.nextChordName = newMajorNames[random.randrange(len(newMajorNames))]
        elif majmin == "minor":
            self.nextChordName = newMinorNames[random.randrange(len(newMinorNames))]
        else:
            assert False
        chordName = chordChoices[random.randrange(len(chordChoices))]
        c = chords.from_shorthand(chordName)
        print(f"<<< {chordName} >>> {c}")
        return [notes.note_to_int(n) for n in c]
# ctab = Ctab("C1")
# x = ctab.nextNotes("major")
# print(x) # [0, 4, 7, 9] or [0, 4, 7]...0 is C and matches the LMMS file that starts with C
