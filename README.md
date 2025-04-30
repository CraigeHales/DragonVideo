Using FFMpeg with pipes for the input audio and video. Python code
generates the data on-the-fly. 
<video src='https://github.com/user-attachments/assets/9425d553-1e13-4eac-b918-aa550571953d'/>

The python code used three threads for image generation, audio generation,
and running the encoder. 

begin.py makes generator functions and pipes and connects everything together. 

encoder.py runs ffmpeg and logs the output. The video input is handled as 
uncompressed 8 bit rgb, described in the ffmpeg parameters. Similar for the
signed 16 bit audio.

The hls code is borrowed from https://gist.github.com/reinhrst/2d693a16c04861a8fbc5253938312410 ,
thanks [@reinhrst](https://github.com/reinhrst) . The pictures are sorted by dominate hue.

picture.py and sound.py are tiny functions that copy the output of the generators
to the pipes. The generators could have been written to feed the pipes directly, but
I wanted to use a generator...

DragonVideo.py gets the image list from a hardcoded path, uses PIL and numpy to sort 
the images and PngInfo saves the sort key in the png meta data. OpenCV cv2 displays
in a full screen window. There is no magic here; colors in a 3D space can't really
be sorted; all this does is count pixels that go in 9 bins (red, blue, green, magenta, cyan, yellow, grey, white, black)
sort by count, and make a key that lists the dominate colors in descending order so
that sorting by that key puts pictures with more red,blue,... are adjacent...
Around line 188 "key" takes on a different meaning: within a picture the entire set of pixels (1920x1080 of them)
are sorted, this time by their rgb values. The goal is to find similar pixels in adjacent pairs
of images (paired by the previous sort of hues) and make a transition from prev to next image
by flying the old pixels into new positions. The code refers to a 40 bit sort that included some
x-y position; that is turned off because it created visual artifacts. The key is built with the 
3 most significant bits being the 1 most significant bit from each of r,g,b followed by (at one time)
the MSB of X and MSB of Y coord. Then repeat until all the rgb bits are in the key; sorting that key
from low to high for two adjacent images puts similar pixels at the same index in both key lists.
Flying all the pixels at once was not pretty after removing the xy from the 40 bit key, there 
was no cohesion of a group of pixels. line 337 creates 10 individual segments of color ranges.
Around line 350 the rest of the code is just making 'tweens by interpolating positions and colors.
It can make about 4fps.

DragonAudio.py loads wav files (use LMMS to build them from the .mmpz files, they are 16 bit stereo 8 seconds/note.) 
Only two are actually used. There is a small nest of semi-random generators and a chord transition table from
Stephen Mugglin (thanks! the maps are really useful for the barely musically inclined like me!)
https://mugglinworks.com/chordmaps/

After all that, the youtube compression is too heavy-handed; sometimes it looks almost OK but often it
is largely blurred.


click for youtube video...

<div align="center">
  <a href="https://www.youtube.com/watch?v=3DK0RUCdaFU"><img src="https://img.youtube.com/vi/3DK0RUCdaFU/0.jpg" alt="IMAGE ALT TEXT"></a>
</div>

