"""
not real code yet. staging ideas for random music, circular buffers,... test////
the sample sound files have 8-second long notes, ascending from C0, C0#, ...C7...
"""

import logging

logger = logging.getLogger(__name__)
import numpy as np
import threading
import mingus.core.notes as notes
import mingus.core.scales as scales
import mingus.core.chords as chords # pip install mingus
import random

# class audioBuffer:
#     def __init__(self):
#         self.buffer = np.zeros((44100 * 8, 2), np.float32)  # keep -1.0 ... 1.0 sample data
#         self.position = 0
#         self.circleLock = threading.Lock()

#     #
#     # the following has never been tested for the wrap-around remove case.
#     # in fact, it will always be called 441 samples at a time because that
#     # is the resolution for the note-ready test in the yield code, below.
#     #
#     def removez(self, buf):  # removes (leaving zeros) the oldest data and returns in buf
#         with self.circleLock:
#             remainingSize = buf.shape[0]  # destination buffer size implies amount to move
#             assert remainingSize <= self.buffer.shape[0] and buf.shape[1] == 2 and self.buffer.shape[1] == 2
#             firstChunkSize = min(remainingSize, self.buffer.shape[0] - self.position)
#             # from position to end, maybe less...
#             buf[:firstChunkSize, :] = self.buffer[self.position : self.position + firstChunkSize, :]
#             self.buffer[self.position : self.position + firstChunkSize, :] = 0
#             self.position += firstChunkSize
#             remainingSize -= firstChunkSize
#             if remainingSize > 0:  # but wait, there's more at the beginning...
#                 buf[firstChunkSize:, :] = self.buffer[0:remainingSize, :]
#                 self.buffer[:remainingSize, :] = 0
#                 self.position = remainingSize
#             elif self.position >= self.buffer.shape[0]:
#                 self.position -= self.buffer.shape[0]
#                 assert self.position == 0  # this is the edge case
#             assert 0 <= self.position and self.position < self.buffer.shape[0]

#     #
#     # this most likely has been tested for wrap-around overlay case
#     #
#     def overlay(self, buf):  # overlay new data at current position. Only removez will advance position.
#         if buf is not None:  # generators feed None instead of np.zeros
#             with self.circleLock:
#                 remainingSize = buf.shape[0]
#                 assert remainingSize <= self.buffer.shape[0] and buf.shape[1] == 2 and self.buffer.shape[1] == 2
#                 firstChunkSize = min(remainingSize, self.buffer.shape[0] - self.position)
#                 # the += on the next line overlays this data on existing data (or zeros)
#                 self.buffer[self.position :: self.position + firstChunkSize, :] += buf[:firstChunkSize, :]
#                 remainingSize -= firstChunkSize
#                 if remainingSize > 0:
#                     self.buffer[:firstChunkSize, :] += buf[firstChunkSize:, :]


time = 0
chunkSize = 441
cycleLength = 3 * 44100  # 1 sec fade + 2 sec static

# cycleLength-44100: downbeat clock is 2 seconds in the future of global time==0
# cycleLength: delay for this note
# 5: a very low note for the drum beat

downbeat = drum(
    piano,
    cycleLength - 44100,
    [
        (cycleLength, 5),
        (cycleLength, 5),
    ],
)


def audioMain():
    global time
    ab = audioBuffer()
    chunk = np.zeros((chunkSize, 2), np.float32)
    while 1:
        ab.overlay(next(downbeat))
        ab.overlay(next(piano))
        ab.overlay(next(voice))
        ab.removez(chunk)
        yield chunk
        time += chunk.shape[0]


def drum(instrument, oTime, pattern):
    global time
    ipat = 0
    while 1:
        if time < oTime:
            yield None
        else:
            assert time == oTime
            delay, note = pattern[ipat]

            ipat = (ipat + 1) % len(pattern)
            oTime += chunkSize


"""
a nested set of boxes of boxes of ... list of notes
each box element has an offset time, repeat count, sub-name.
The list of notes is not a box.
A box runs all of its children in parallel; at any 441 step
one or more children may produce samples from the bottom-most
list of notes (into the circular buffer.)
Each child box uses the globaltime and the childtime to pace itself.
The root Song collection might have a drone track, first half track,
and last half track. They are all started with offsets of 0,0,and 0.5(totalsamples),
and all are called every time. one of the half tracks bails early when t < .5, etc.
when the half track does not bail, it runs sub collections.
"""

class Instrument: # produces a note with freq, amp, attack, sustain, hold
    def __init__(self,):
        pass
    def get(self,fre,amp,att,sus,hol): # return a synthesized buffer, probably longer than 441 samples
        pass     

class Samplegen: # base for sequence and musicbox
    def __init__(self,):
        pass


class Sequence(Samplegen): # asks instruments for next note's samples; this is where the notes are clocked out and wait their turn
    def __init__(self,instrumentPatternList):
        self.children = instrumentPatternList # each list element knows when the note begins RELATIVE to start time of container
        pass
    def get(self,time,buf):             
        pass


class MusicBox(Samplegen): # 
    def __init__(self,boxPatternList):
        self.children = boxPatternList # list of sample generators (both Sequences and MusicBoxes)
        pass
    def get(self,time,buf):
        # get samples from all child boxes

        # get leaf samples of my own

        pass


"""
FSM for chord progression

Key: 1..11 - the starting note                   for example, C

(There are always 12 half steps in a mode pattern to get to the next octave)

Scale: 7 notes starting at key                   C D E F G A B 
       Major: W W H W W W H                       w w h w w w h   Ionian mode, or major

        Dorian mode                              D E F G A B C   
                                                  w h w w w h w   Dorian

        Phrygian mode                            E F G A B C D
                                                  h w w w h w w   Phrygian

        Natural Minor Aeolian mode               A B C D E F G
                                                  w h w w h w w   Aeolian

        Harmonic Minor: W H W W H (W+H) H        A B C D E F G#   "big step"   W+H is 3 half steps
                                                  w h w w h 3  h   https://music.stackexchange.com/a/60542 

        melodic minor W H W W W W H              A B C D E F# G#  "going up, never
                                                  w h w w w  w  h  needs 3 half steps"
                                                                  "going down, use Aeolian"


Chord: 3 notes starting at scale note
        major chord I, iii, IV -- the 1st, 3rd, and 5th notes of a major scale
        Minor chord - flat the 3rd note of the scale.  
        Augmented chord - sharp the 5th note of the scale.  
        7th - flat the 7th note of the scale.

by Michael Thomas  https://www.michael-thomas.com/music/class/chords_notesinchords.htm
Chord       Major       Minor       7th     Aug(+)
C 	        C,E,G 	    C,Eb,G 	    Bb 	    C,E,G#
Db/C# 	    Db,F,Ab 	Db,E,Ab 	B 	    Db,F,A
D 	        D,F#,A 	    D,F,A 	    C 	    D,F#,Bb
Eb/D# 	    Eb,G,Bb 	Eb,Gb,Bb 	Db 	    Eb,G,B
E 	        E,G#,B 	    E,G,B 	    D 	    E,G#,C
F 	        F,A,C 	    F,Ab,C 	    Eb 	    F,A,C#
Gb/F# 	    Gb,Bb,Db 	Gb,A,Db 	E 	    Gb,Bb,D
G 	        G,B,D 	    G,Bb,D 	    F 	    G,B,D#
Ab/G# 	    Ab,C,Eb 	Ab,B,Eb 	F# 	    Ab,C,E
A 	        A,C#,E 	    A,C,E 	    G 	    A,C#,F
Bb/A# 	    Bb,D,F 	    Bb,Db,F 	Ab 	    Bb,D,Gb
B 	        B,D#,F# 	B,D,F# 	    A 	    B,D#,G

https://www.skoove.com/blog/major-and-minor-chords/
C major (I)     C, E, G
G major (V)     G, B, D
A minor (vi)    A, C, E
F major (IV)    F, A, C

https://en.wikipedia.org/wiki/Diminished_triad
Chord 	Root 	Minor third 	    Diminished fifth
Cdim 	C 	    E♭ 	                G♭
C♯dim 	C♯ 	    E 	                G
D♭dim 	D♭ 	    F♭ (E) 	            A double flat (G)
Ddim 	D 	    F 	                A♭
D♯dim 	D♯ 	    F♯ 	                A
E♭dim 	E♭ 	    G♭ 	                B double flat (A)
Edim 	E 	    G 	                B♭
Fdim 	F 	    A♭ 	                C♭ (B)
F♯dim 	F♯ 	    A 	                C
G♭dim 	G♭ 	    B double flat (A) 	D double flat (C)
Gdim 	G 	    B♭ 	                D♭
G♯dim 	G♯ 	    B 	                D
A♭dim 	A♭ 	    C♭ (B) 	            E double flat (D)
Adim 	A 	    C 	                E♭
A♯dim 	A♯ 	    C♯ 	                E
B♭dim 	B♭ 	    D♭ 	                F♭ (E)
Bdim 	B 	    D 	                F 

"""

print(notes.augment("C"))  # "C#"
print(scales.Major("C").ascending())  #  ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C']
scales.HarmonicMinor("A").ascending()  # ['A', 'B', 'C', 'D', 'E', 'F', 'G#', 'A']
scales.HarmonicMinor("A").descending()  # ['A', 'G#', 'F', 'E', 'D', 'C', 'B', 'A']
scales.NaturalMinor("A").descending()  # same as aeolian
scales.MelodicMinor("A").descending()  # ascending is not reverse of descending
scales.Aeolian("A").ascending()  #       ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'A']
scales.Aeolian("A").descending()  #      ['A', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
scales.HarmonicMinor("A").tonic  # "A"
chords.major_triad("C")  # ['C', 'E', 'G'] G is the 5th
chords.dominant("C")  # ['G', 'B', 'D'] starts on 5th
chords.minor_triad("C")  # ['C', 'Eb', 'G']
chords.triads("C")  # [['C', 'E', 'G'], ['D', 'F', 'A'], ['E', 'G', 'B'], ['F', 'A', 'C'], ['G', 'B', 'D'], ['A', 'C', 'E'], ['B', 'D', 'F']]
chords.triads("Ab")  # [['Ab', 'C', 'Eb'], ['Bb', 'Db', 'F'], ['C', 'Eb', 'G'], ['Db', 'F', 'Ab'], ['Eb', 'G', 'Bb'], ['F', 'Ab', 'C'], ['G', 'Bb', 'Db']]
chords.from_shorthand("A")  # ['A', 'C#', 'E']
chords.from_shorthand("A/G")  # ['G', 'A', 'C#', 'E']
chords.from_shorthand("Ab7")  # ['Ab', 'C', 'Eb', 'Gb']


print(chords.from_shorthand("Dm6/b6"))

# # this state table is a dictionary with chord names keys for states (left-most column)
# # column 2 is a set of variations the chord might be played with
# # column 3 (top and bottom) is the next chord to use to stay in/move to major (lighter)
# # column 4 (top and bottom) is the next chord to use to stay in/move to minor (darker)
# # Dm Am F are the common chords between the table and where the change
# # from major to minor happens; if the minor/major flag changes, either the very next
# # state can be in the other half of the table OR one more  
# # fmt: off
# transitionTable = { # see https://mugglinworks.com/chordmaps/ (Thanks!)
#     # this half is the C Major progression (1 suffix on state names)
#     # state   choices of chords for state          choices of next state to stay in major         choices to switch to minor
#     "C1":   (("C","C6","CM7","CM9","Csus",),      ("Dm1","Em1","F1","G1","Am1","C/G1","F/C1",), ("Dm1","Am1","F1",),),
#     "Dm1":  (("Dm","Dm7","Dm9",),                 ("G1","G1","Em1","C/G1",),                    ("Am2","E2","Bdim2","Am/E2",),),
#     "Em1":  (("Em","Em7",),                       ("C1","C1","Am1","F1",),                      ("Am1","F1",),),
#     "F1":   (("F","F6","FM7",),                   ("C1","C1","Dm1","G1","C/G1",),               ("Dm2","Bdim2",),),
#     "G1":   (("G","G7","G9","G11","G13","Gsus",), ("C1","C1","Em1","Am1",),                     ("Am2",),),
#     "Am1":  (("Am",),                             ("F1","F1","Dm1",),                           ("Bdim2","Caug2","Dm2","E2","F2",),),
#     "C/G1": (("C/G",),                            ("G1",),                                      ("G1",),),
#     "F/C1": (("F/C","G/C",),                      ("C1",),                                      ("C1",),),
#     # this half is the A Minor progression (2 suffix on state names)
#     # state    choices of chords for state     choices to switch to major   choices of next state to stay in minor
#     "Am2":   (("Am",),                         ("F1","Dm1",),             ("Bdim2","Caug2","Dm2","E2","F2","Am/E2","Dm/A2",),),
#     "Bdim2": (("Bdim","G#dim/B"),              ("Am2",),                  ("E2","Caug2","Am/E2",),),
#     "Caug2": (("Caug","Am/C",),                ("Am2","Dm2","F2",),       ("Am2","Dm2","F2",),),
#     "Dm2":   (("Dm","Dm7","Dm9",),             ("G1","Em1","C/G1",),      ("Am2","E2","Bdim2","Am/E2",),),
#     "E2":    (("E","E7","Eb9","Eb13","Esus",), ("Am2","F2",),             ("Am2","Caug2","F2",),),
#     "F2":    (("F","F6","FM7",),               ("Dm1","G1","C/G1","C1",), ("Dm2","Bdim2",),),
#     "Am/E2": (("Am/E",),                       ("E2",),                   ("E2",),),
#     "Dm/A2": (("Dm/A","E/A",),                 ("Am2",),                  ("Am2",),),
# }

# fmt: on

currentState = "C1"

for i in range(11):
    print("\nmajor...",end=" ")
    for j in range(18):
        representations, majorTrans, minorTrans = transitionTable[currentState]
        currentState=majorTrans[random.randint(0,len(majorTrans)-1)]
        print(currentState,end="\t")
    print("\nminor...",end=" ")
    for j in range(18):
        representations, majorTrans, minorTrans = transitionTable[currentState]
        currentState=minorTrans[random.randint(0,len(minorTrans)-1)]
        print(currentState,end="\t")

currentState=minorTrans[random.randint(0,len(minorTrans)-1)]
representations, majorTrans, minorTrans = transitionTable[currentState]
print(currentState,end="    ")
for i in range(len(representations)):
    r=representations[i]
    c=chords.from_shorthand(r)
    print(c,end="(")
    #prev=-99
    first=-99
    for j in range(len(c)):
        n=notes.note_to_int(c[j])
        if j==0:
            first=n
        if "/" not in r or j<len(c)-1: # first notes are rising, add 12 as needed. the note after / is in bass, subtract 12 as needed
            if n < first:
                n+=12
        else:
            if n>=first:
                n-=12
        print(n,end=" ")
    print(")",end=" ")
print()

""" old stuff ...

majkey = 40  # pick a starting note/key for a major scale
parkey = majkey  # parallel minor starts on same note/key
relkey = majkey - 3  # relative minor starts 3 notes down

theMajor = 0, 2, 4, 5, 7, 9, 11, 12  # add to majkey to get the root notes of the chords in the scale
natMinor = 0, 2, 3, 5, 7, 8, 10, 12  # add to parkey or relkey for natural minor scale chord roots
#harMinor = 0, 2, 3, 5, 7, 8, 11, 12  # add to parkey or relkey for harmonic minor scale chord roots
# melodic minor (going up vs going down) will not be handled by this state machine.
# I think I'll prefer natural over harmonic
# I think I'll prefer relative minor over parallel minor
majScale = theMajor + majkey  # C D E F G A B
minScale = natMinor + relkey  # A B C D E F G#

# patterns for chords
patMaj = ((1,),      (3,),    (5,),             ) # notes 1,3,5 from the scale
patMa1 = ((1,-12,),  (3,),    (5,),             ) # notes 1,3,5 from the scale, /1 in bass
patMa5 = ((1,),      (3,),    (5,-12,),         ) # notes 1,3,5 from the scale, /5 in bass
patMin = ((1,),      (3,-1),  (5,),             ) # flat the 3rd note
patMi1 = ((1,-12),   (3,-1),  (5,),             ) # flat the 3rd note, /1 in bass
patMi5 = ((1,),      (3,-1),  (5,-12),          ) # flat the 3rd note /5 in bass
patAug = ((1,),      (3,),    (5,1,),           ) # sharp the 5th note
#Patsev = ((1,),      (3,),    (5,),      (7,-1),) # flat the 7th note
# in a twelve-tone equal temperament, a diminished triad has three semitones 
# between the third and fifth, three semitones between the root and third, 
# and six semitones between the root and fifth. https://en.wikipedia.org/wiki/Diminished_triad
patDim = ((1,),      (1,3,),  (1,6,),           ) #

# the chords used in the transition tables.
transTable = {
    "I": ((majScale[0],patMaj,),),      #  C, E, G
    "im": ((minScale[0],patMin,),),     #  A, C, E **
    #
    "iim": ((majScale[1]),patMin,),     #  D, F, A ***
    "ii°": ((minScale[1],patDim,),),    #  B, D, F
    #
    "iiim": ((majScale[2]),patMin,),    #  E, G, B
    "bIII+": ((minScale[2],patAug,),),  #  C, E, G             b means use III from majScale?
    #
    "IV": ((majScale[3],patMaj,),),     #  F, A, C ****
    "ivm": ((minScale[3],patMin,),),    #  D, F, A ***
    #
    "Va": ((majScale[4],patMaj,),),     #  G, B, D
    "Vb": ((minScale[4],patMaj,),),     #  E, G, B
    #
    "vim": ((majScale[5]),patMin,),     #  A, C, E **
    "bVI": ((minScale[5],patMaj,),),    #  F, A, C ****            b means use VI from maj scale?
    #
    "IV/1": ((majScale[3],patMa1,),),   #  bass(F), A, C
    "ivm/1": ((minScale[3],patMi1,),),  #  bass(D), F, A
    #
    "I/5": ((majScale[0],patMa5),),     #  C, E, bass(G)
    "im/5": ((minScale[0],patMi5),),    #  A, C, bass(E)
}

# from a scale (major or minor) use notes 1,3,5 to make the (major or minor) chord with root 1

# the progression state table for chords in a chosen key has 8 states
# + = aug     ° = dim     °7 = dim7
# major  minor  root
# I      im       0
# iim    ii°      1
# iiim   bIII+    2   ignore the leading b? https://music.stackexchange.com/questions/114038/what-is-the-difference-between-the-biii-and-iii-chord-in-a-minor-scale
# IV     ivm      3
# Va     Vb       4   Va and Vb are the same except for variations
# vim    bVI      6   ignore the leading b? https://music.stackexchange.com/questions/114038/what-is-the-difference-between-the-biii-and-iii-chord-in-a-minor-scale
# IV/1   ivm/1    3   what does /1 mean? put scale note 1 in the bass, an octave down(?)
# I/5    im/5     1   what does /5 mean? put scale note 5 in the bass

# maybe leave out the last two states

# build all 24 tables using majkey 40...51 and major and minor sequences.
# for all 24 chords (which are the I in each progression state table) note
# which other progression state tables the chord appears in (mod 12 for wrap-around).


"""
