# ffmpeg functions
"""
This is the encoder thread. It launches FFMpeg with pipes attached to the other threads.
This code is NOT the place to customize a video. Except for FFMpeg parameters.
"""
import subprocess
#import sys
#import os
import selectors
import subprocess
import logging
logger = logging.getLogger(__name__)
def setup(audPipe,vidPipe, xImg, yImg, outputfile):
    logger.info('Started')
    # ffmpeg -pix_fmts  (see https://stackoverflow.com/a/54196619)
    # Pixel formats:
    # I.... = Supported Input  format for conversion
    # .O... = Supported Output format for conversion
    # ..H.. = Hardware accelerated format
    # ...P. = Paletted format
    # ....B = Bitstream format
    # FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL
    # -----
    # (many many rows deleted...)    
    # IO... rgb24                  3            24  <<< one of these will be
    # IO... bgr24                  3            24  <<< the 3-byte format
    # IO... bgr8                   3             8
    # .O..B bgr4                   3             4
    # IO... bgr4_byte              3             4
    # IO... rgb8                   3             8
    # .O..B rgb4                   3             4
    # IO... rgb4_byte              3             4
    # IO... argb                   4            32   <<< this is the JMP windows easy format
    # IO... rgba                   4            32
    # IO... abgr                   4            32
    # IO... bgra                   4            32

# ffmpeg -format (https://trac.ffmpeg.org/wiki/audio%20types)
# File formats:
#  D. = Demuxing supported
#  .E = Muxing supported
#  -- (many many deleted   ffmpeg -formats | grep PCM  )
#  DE alaw    PCM A-law
#  DE f32be   PCM 32-bit floating-point big-endian
#  DE f32le   PCM 32-bit floating-point little-endian
#  DE f64be   PCM 64-bit floating-point big-endian
#  DE f64le   PCM 64-bit floating-point little-endian
#  DE mulaw   PCM mu-law
#  DE s16be   PCM signed 16-bit big-endian
#  DE s16le   PCM signed 16-bit little-endian
#  DE s24be   PCM signed 24-bit big-endian
#  DE s24le   PCM signed 24-bit little-endian
#  DE s32be   PCM signed 32-bit big-endian
#  DE s32le   PCM signed 32-bit little-endian
#  DE s8      PCM signed 8-bit
#  DE u16be   PCM unsigned 16-bit big-endian
#  DE u16le   PCM unsigned 16-bit little-endian
#  DE u24be   PCM unsigned 24-bit big-endian
#  DE u24le   PCM unsigned 24-bit little-endian
#  DE u32be   PCM unsigned 32-bit big-endian
#  DE u32le   PCM unsigned 32-bit little-endian
#  DE u8      PCM unsigned 8-bit
#  DE vidc    PCM Archimedes VIDC

# ffmpeg -f f32le -channels 2 -i pipe:0 -f wav file-out.wav
# https://superuser.com/a/1436849    <<<<<<< channels <<<<<<<
# https://superuser.com/questions/1436830/how-to-convert-raw-pcm-data-to-a-valid-wav-file-with-ffmpeg
    
# ffmpeg -f s16le -sample_rate 48000 -channels 2 -codec:a pcm_s16le -channel_layout stereo -i /dev/zero -f s16le -codec:a pcm_s16le -y xxx.pcm
# https://lists.ffmpeg.org/pipermail/ffmpeg-user/2013-February/013266.html
    
# seekable https://ffmpeg.org/ffmpeg-protocols.html

    command = [ "/usr/bin/ffmpeg", '-y', # overwrite output
                "-f", "rawvideo", # tell ffmpeg the stdin data coming in is
                "-vcodec", "rawvideo", # "raw" pixels, uncompressed, no meta data
                "-s", F"{xImg}X{yImg}", # raw video needs this meta data to know the size of the image
                # think about this, we might actually have bgr, not argb
                "-pix_fmt", "bgr24", # the JSL color values are easily converted to argb with MatrixToBlob
                "-r", "60", # input FPS
                "-thread_queue_size", "256", # 128 was slow.  applies to the following input. is this in frames or some other unit? 8 produces a warning, 1024 is too big?
                "-i", vidPipe, # this is the pipe input. everything before this is describing the input data
                #"-an", # disable audio, or supply a sound file as another input
                "-f", "s16le", # seems likely: signed 16 bit little endian
                #"-sample_rate", "44100", #
                #"-channels", "2", # stereo
                "-channel_layout", "stereo", #
                #"-seekable", "0",#
                "-ar", "44.1k", # https://stackoverflow.com/a/11990796
                "-ac", "2", # https://stackoverflow.com/questions/11986279/can-ffmpeg-convert-audio-from-raw-pcm-to-wav
                "-i", audPipe, # 
                # output parms follow
                
                # mpeg  "-vcodec", "mpeg4", # encoding for the output
                # think about reducing the data rate...
                # mpeg  "-b:v", "50000k", # bits per second for the output
                
                # H.264 https://trac.ffmpeg.org/wiki/Encode/H.264
                "-crf", "20", # smaller is bigger file, -6 doubles file size, 0-23-51
                "-preset", "veryslow", # compression control: ultrafast superfast veryfast faster fast medium slow slower veryslow 
                "-tune", "film", # "grain" or "film" ? https://superuser.com/questions/564402/explanation-of-x264-tune
                "-c:v", "libx264",


                outputfile, # the name of the output (should end with .mp4)
                #Eval Insert(">ffmpeg.stdout^chapter0based+1-1^.txt 2>ffmpeg.stderr^chapter0based+1-1^.txt\!"")}
                # '-f', 'dshow', 
                # '-rtbufsize', '100M',
                # '-i', 'video=Datapath VisionAV Video 01' ,
                # '-video_size', '640x480',
                # '-pix_fmt', 'bgr24', 
                # '-r','25',  
                # '-f', 'image2pipe', 
                # '-' 
                ] # output    
    pipe = subprocess.Popen(command, stdout = subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    # https://stackoverflow.com/a/56918582 - selectors to get stdout/err interleaved
    sel = selectors.DefaultSelector()
    sel.register(pipe.stdout, selectors.EVENT_READ)
    sel.register(pipe.stderr, selectors.EVENT_READ)

    while True:
        for key, _ in sel.select():
            data = key.fileobj.read1().decode()
            if not data:
                exit()
            if key.fileobj is pipe.stdout:
                logger.info(data) #, end="")
            else:
                logger.info(data) #, end="") #, file=sys.stderr)


    # try:    
    #     pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) # `
    #     ffmpeg_output, _ = pipe.communicate()
    # except  subprocess.CalledProcessError as err:
    #     print("FFmpeg stdout output on error:\n" + err.output)




#     width = 640
#     height = 360
#     iterator = 0
#     cmd = ['ffmpeg', 
#            '-loglevel', 'quiet',
#            '-f', 'dshow',
#            '-i', 'video=HD USB Camera',
#            #'-vf','scale=%d:%d,smartblur'%(width,height),
#            '-preset' ,'ultrafast', 
#            '-tune', 'zerolatency',
#            '-f', 'rawvideo',
#            '-pix_fmt','bgr24',
#            '-']
#     p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

#     while True:
#         arr = numpy.frombuffer(p.stdout.read(width*height*3), dtype=numpy.uint8)
#         iterator += 1 
#         if len(arr) == 0:
#             p.wait()
#             print("awaiting")
#             #return
#         if iterator >= 1000:
#             break

#         frame = arr.reshape((height, width,3))
#         cv2.putText(frame, "frame{}".format(iterator), (75, 70),
#                 cv2.cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
#         im = Image.fromarray(frame)
#         im.save("ffmpeg_test/test%d.jpeg" % iterator)
#         yield arr


# from PIL import Image
# from imutils.video import FPS
# for i, frame in enumerate(video_frames_ffmpeg()):
#     if i == 0:
#         fps = FPS().start()
#     else: fps.update()
# fps.stop()
# print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
# cv2.destroyAllWindows()



    logger.info('Finished')
# run ffmpeg with 3 named pipes
# https://stackoverflow.com/questions/67388548/multiple-named-pipes-in-ffmpeg

# {"dell9010", 
#   idea from https://stackoverflow.com/questions/34167691/pipe-opencv-images-to-ffmpeg-using-python
# "\!"/mnt/nfsc/farm/repeater.py 2>repeater.stderr.txt|ffmpeg", "-y", // overwrite output
# "-f", "rawvideo", // tell ffmpeg the stdin data coming in is
# "-vcodec", "rawvideo", // "raw" pixels, uncompressed, no meta data
# "-s", Eval Insert( "^ncols(frame)^X^nrows(frame)^" ), // raw video needs this meta data to know the size of the image
# "-pix_fmt", "argb", // the JSL color values are easily converted to argb with MatrixToBlob
# "-r", "30", // input FPS
# "-thread_queue_size", "256", // 128 was slow.  applies to the following input. is this in frames or some other unit? 8 produces a warning, 1024 is too big?
# "-i", "-", // this is the pipe input. everything before this is describing the input data
# //"-an", // disable audio, or supply a sound file as another input
# "-i", Eval Insert( "/mnt/nfsc/farm/PolarisAudio_Chapter_^chapter0based+1-1^.wav" ), // 
# "-vcodec", "mpeg4", // encoding for the output
# "-b:v", "5000k", // bits per second for the output
# Eval Insert( "/mnt/nfsc/farm/polaris_Chapter_^chapter0based+1-1^.mp4" ), // the name of the output
# Eval Insert(">ffmpeg.stdout^chapter0based+1-1^.txt 2>ffmpeg.stderr^chapter0based+1-1^.txt\!"")}

# https://www.reddit.com/r/ffmpeg/comments/yc430v/ffmpeg_calling_lseek_on_named_pipes_fifo/?rdt=35901
###### -seekable 0 #####
# https://unix.stackexchange.com/questions/483359/how-can-i-stop-ffmpeg-from-quitting-when-it-reaches-the-end-of-a-named-pipe
# https://stackoverflow.com/questions/32584220/how-to-make-ffmpeg-write-its-output-to-a-named-pipe -format <format>
# https://github.com/kkroening/ffmpeg-python?tab=readme-ov-file -- probably don't want to add this to the mix
    