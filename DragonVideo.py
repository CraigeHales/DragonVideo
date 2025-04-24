"""
custom generator for images
"""

import os
import json
import cv2 as cv    # source .venv/bin/activate    then    pip3 install opencv-python
import numpy as np
import math
import RGB_HLS as cc  # cc.rgb_to_hls(np.reshape(self.picture.im, (-1, 3)))
import logging

from PIL import Image # only for pngmeta?     source .venv/bin/activate    then   pip3 install pillow
from PIL.PngImagePlugin import PngInfo

logger = logging.getLogger(__name__)
# https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do-in-python

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)

showPictures = 1
gCurpic = None
gNumStaticFrames = 120 # 900 total frames @ 60FPS is 15 seconds or 1500 441 samples in audio
gNumTransitionFrames = 780 # activefraction expects mult of 3
# audio generator informed by this value
def getCurpic():
    global gCurpic
    return gCurpic
def getNumStaticFrames():
    global gNumStaticFrames
    return gNumStaticFrames
def getNumTransitionFrames():
    global gNumTransitionFrames
    return gNumTransitionFrames


def getPictureGenerator():
    mypath = "/home/c/Desktop/images/"
    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) and f.endswith(".png")]
    logger.info(f"n files={len(onlyfiles)}")
    keyfiles = []
    global gCurpic
    for f in onlyfiles:
        # json_file = os.path.join(mypath, f[:-4] + "json")
        # if not os.path.isfile(json_file):
        #     logger.info("missing json---{f}")
        #     continue

        # with open(json_file) as file:
        #     json_decoded = json.load(file)

        image = Image.open(os.path.join(mypath, f))
        # print(image.text) there is also .info, but I used add_text in the stableDiffusionDriver code
        json_decoded = image.text
        if "colorkey" in json_decoded:
            keyfiles.append((json_decoded["colorkey"], f))
           # logger.info(f)
        else:
            # if len(keyfiles)> 20:
            #    break
            pic = cv.imread(os.path.join(mypath, f), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
            #    pic=cv.resize(pic, (1920, 1080))
            ydim, xdim, zdim = pic.shape
#            lo = np.min(pic)
#            hi = np.max(pic)
            # print(f"pic.shape={pic.shape},lo={lo},hi={hi} {f}")
            temp = np.reshape(pic / 255, (-1, 3))
            hls = cc.rgb_to_hls(temp[:, ::-1])
            # print(f"hls={hls.shape}")
            hue = hls[:, 0]  # reverse hue here
            light = hls[:, 1]
            sat = hls[:, 2]
            # print(f"hue.shape={hue.shape},np.min(hue)={np.min(hue)},np.max(hue)={np.max(hue)} ")
            white = light > 0.7
            cwhite = np.count_nonzero(white)
            black = light < 0.3
            cblack = np.count_nonzero(black)
            middle = ~(white | black)
            cmiddle = np.count_nonzero(middle)
            gray = middle & (sat < 0.5)
            cgray = np.count_nonzero(gray)
            color = ~(gray | black | white)
            ccolor = np.count_nonzero(color)
            yellow = color & ((30 / 360) < hue) & (hue <= (90 / 360))  # 60
            cyellow = np.count_nonzero(yellow)
            green = color & ((90 / 360) < hue) & (hue <= (150 / 360))  # 120
            cgreen = np.count_nonzero(green)
            cyan = color & ((150 / 360) < hue) & (hue <= (210 / 360))  # 180
            ccyan = np.count_nonzero(cyan)
            blue = color & ((210 / 360) < hue) & (hue <= (270 / 360))  # 240
            cblue = np.count_nonzero(blue)
            magenta = color & ((270 / 360) < hue) & (hue <= (330 / 360))  # 300
            cmagenta = np.count_nonzero(magenta)
            red = color & (((330 / 360) < hue) | (hue <= (30 / 360)))
            cred = np.count_nonzero(red)
            if cblack + cwhite + cgray + cred + cgreen + cblue + ccyan + cmagenta + cyellow != ydim * xdim:
                raise Exception("hls to colors")
            # print(f"black={cblack} white={cwhite} gray={cgray} red={cred} yellow={cyellow} green={cgreen} cyan={ccyan} blue={cblue} magenta={cmagenta}")
            # create the sort key for this picture by sorting the colors
            key = [
                (cred, "1red"),
                (cblue, "2blu"),
                (cgreen, "3grn"),
                (cmagenta, "4mag"),
                (ccyan, "5cyn"),
                (cyellow, "6yel"),
                (cgray, "7gry"),
                (cwhite, "8wht"),
                (cblack, "9blk"),
            ]  #
            # print(f"key={key}") # [(180283, '1'), (1472, '2'), (7, '3'), (83, '4'), (923564, '5'), (14, '6'), (1096, '7'), (962995, '8'), (4086, '9')]
            key.sort(key=lambda a: a[0], reverse=True)  # [(7, '3'), (14, '6'), (83, '4'), (1096, '7'), (1472, '2'), (4086, '9'), (180283, '1'), (923564, '5'), (962995, '8')]
            # print(f"key={key}")
            key = "".join([x[1] for x in key])  # list comprehension ['3', '6', '4', '7', '2', '9', '1', '5', '8']

            if f == 'title.png':
                key = '~~~~~~~' # sort title at end


            json_decoded["colorkey"] = key

            # with open(json_file, "w") as file:
            #     json.dump(json_decoded, file)


            metadata = PngInfo() 
            for key2 in json_decoded:
                metadata.add_text(key2, str(json_decoded[key2]))
            image.save(os.path.join(mypath, f), pnginfo=metadata)



            logger.info(f"add {key} {f} ")

            keyfiles.append((json_decoded["colorkey"], f))
        if 0 and showPictures:
            pic = cv.imread(os.path.join(mypath, f), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
            pic = cv.resize(pic, (1920, 1080))
            cv.imshow(f, pic)
            cv.moveWindow(f, 1280, 0)  # 1280 is width of other monitor at left origin
            cv.setWindowProperty(f, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
            while cv.getWindowProperty(f, cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:
                pass
            cv.destroyWindow(f)
            cv.waitKey(1)

    #
    # bin the hls colors by hue, the total bins is the total pixels 2k*2k, but maybe only 8 bins.
    # the bincode for a picture is the sorted indexes of bins , 78653421 means bin 7 was large and bin 1 was small.
    # sort the pictures by the bincodes. pictures with similar amounts of hues will be adjacent.
    # ALSO sort the pixels by HUE,x,y not r,g,b,x,y
    #
    logger.info(f" nkeyfiles={len(keyfiles)}")
    keyfiles.sort(key=lambda a: a[0])
    # print(keyfiles)

    # i = 0
    # f = keyfiles[i]

    # pic = cv.imread(os.path.join(mypath, f[1]), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
    # pic = cv.resize(pic, (1920, 1080))
    # cv.imshow("quicktest", pic)
    # cv.moveWindow("quicktest", 1280, 0)  # 1280 is width of other monitor at left origin
    # # cv.setWindowProperty("quicktest", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    # while cv.getWindowProperty("quicktest", cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:
    #     pass

    # for f in keyfiles:
    #     i += 1
    #     if i % 50 != 0:
    #        continue
    #     print(f"{i/len(keyfiles)} {f[0]} {f[1]}")
    #     pic = cv.imread(os.path.join(mypath, f[1]), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
    #     pic = cv.resize(pic, (1920, 1080))
    #     cv.imshow("quicktest", pic)
    #     while cv.getWindowProperty("quicktest", cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:  # 1: wait for a key for 1ms
    #         pass
    #     cv.waitKey(30)
    # cv.destroyWindow("quicktest")
    # cv.waitKey(1)

    #
    # above sorted all the pictures into a rainbow sequence so adjacent pictures will be similar colors.
    # below sorts pixels in two adjacent pictures; pixels with same sort index will be similar colors.
    #

    # build the result matrix of 40-bit keys that sort the pixels into a linear order
    def getkeys(im, result):
        if result.shape != (1920 * 1080,):
            raise Exception("shape 1")
        if im.shape != (1080, 1920, 3):
            raise Exception("shape 2")
        green = np.reshape(im[:, :, 1], -1)  # separate the colors; green is most important, red is least. Maybe.
        blue = np.reshape(im[:, :, 0], -1)
        red = np.reshape(im[:, :, 2], -1)

        # picg = np.zeros((yDim, xDim, zDim), dtype=np.uint8)
        # picg[:, :, 1] = np.reshape(green, (xDim, yDim))
        # picg = cv.resize(picg, (1920, 1080))
        # cv.imshow("green", picg)
        # cv.moveWindow("green", 1280, 0)  # 1280 is width of other monitor at left origin
        # # cv.setWindowProperty("green", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        # while cv.getWindowProperty("green", cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:
        #     pass
        # cv.destroyWindow("green")
        # cv.waitKey(1)

        # picg = np.zeros((yDim, xDim, zDim), dtype=np.uint8)
        # picg[:, :, 0] = np.reshape(blue, (xDim, yDim))
        # picg = cv.resize(picg, (1920, 1080))
        # cv.imshow("blue", picg)
        # cv.moveWindow("blue", 1280, 0)  # 1280 is width of other monitor at left origin
        # # cv.setWindowProperty("blue", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        # while cv.getWindowProperty("blue", cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:
        #     pass
        # cv.destroyWindow("blue")
        # cv.waitKey(1)

        # picg = np.zeros((yDim, xDim, zDim), dtype=np.uint8)
        # picg[:, :, 2] = np.reshape(red, (xDim, yDim))
        # picg = cv.resize(picg, (1920, 1080))
        # cv.imshow("red", picg)
        # cv.moveWindow("red", 1280, 0)  # 1280 is width of other monitor at left origin
        # # cv.setWindowProperty("red", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        # while cv.getWindowProperty("red", cv.WND_PROP_VISIBLE) and cv.waitKey(1) < 0:
        #     pass
        # cv.destroyWindow("red")
        # cv.waitKey(1)

        result[:] = 0  # clear answer before shifting in the rgbxy bits
        valRGB = 128  # high bit of RGB 0..255
        valX = xBits - 1  # xyBits==11 for 0..2047
        valY = yBits - 1  # -1 is the high bit (2**10==1024, mid-screen)
        for i in range(8):
            result[:] *= 2
            bits = (green & valRGB) != 0
            result[:] += bits

            result[:] *= 2
            bits = (blue & valRGB) != 0
            result[:] += bits

            result[:] *= 2
            bits = (red & valRGB) != 0
            result[:] += bits

            #
            # first 3 bits, above are the high bits of RGB, below the 2 high bits of the address
            # repeat 8 times. when these keys are sorted, similar colors in similar locations
            # will be near each other. If the overall similarity of the pictures is good, then
            # paired sorted lists from two pictures will identify similar pixels in the pictures.
            #


            # maybe works, but makes seams in pic
        # result[:] *= 2
        # bits = (xpos & 2**valX) != 0  # 0+11-8 ... 7 + 11 - 9
        # result[:] += bits

        # result[:] *= 2
        # bits = (ypos & 2**valY) != 0
        # result[:] += bits


            valRGB //= 2
            valX -= 1  # exponent - 1
            valY -= 1  # to cut in half
        # result[:]=  np.arange(result.size) # 0 # why does repeated values fail???
        # result[:]*=(2**20)
        # result[:]&=np.arange(result.size, dtype=np.uint64)

    # use the last file as initial prev, might help with looping the video
    picOld = cv.imread(os.path.join(mypath, keyfiles[-1][1]), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
    yDim, xDim, zDim = picOld.shape
    logger.info(f"x={xDim} y={yDim} z={zDim}")
    xBits = int(math.log2(xDim))
    yBits = int(math.log2(yDim))
    if xDim != 2**xBits or yDim != 2**yBits:
        pass # raise Exception("bad size")
    # assume the last file's dims are consistent with all

    ypos = np.zeros((yDim, xDim), dtype=np.uint32)
    for iy in range(yDim):
        ypos[iy, :] = iy
    ypos = np.reshape(ypos, -1)

    xpos = np.zeros((yDim, xDim), dtype=np.uint32)
    for ix in range(xDim):
        xpos[:, ix] = ix
    xpos = np.reshape(xpos, -1)

    # getkeys has all it needs now
    oldKeys = np.zeros((yDim * xDim), dtype=np.uint64)
    newKeys = np.zeros((yDim * xDim), dtype=np.uint64)
    getkeys(picOld, oldKeys)
    rankOld = oldKeys.argsort()

    # prove the ranked keys cover all the pixel positions
    temp = np.zeros(yDim * xDim)
    temp[rankOld] = 1
    if not np.all(temp == 1):
        raise Exception("oops 1")

    xOld = xpos[rankOld]
    yOld = ypos[rankOld]

    # prove xpos/ypos cover the pixels too
    temp[xOld + yOld * xDim] = 3
    if not np.all(temp == 3):
        temp2 = np.where(temp != 3)
        raise Exception("oops 2")

    rOld = np.reshape(picOld[:, :, 2], xDim * yDim)
    rOld = rOld[rankOld]
    gOld = np.reshape(picOld[:, :, 1], xDim * yDim)
    gOld = gOld[rankOld]
    bOld = np.reshape(picOld[:, :, 0], xDim * yDim)
    bOld = bOld[rankOld]
    if showPictures:
        temppo = cv.resize(picOld, (1920, 1080))
        cv.imshow("transition", temppo)
        cv.moveWindow("transition", 1280*0, 0)  # 1280 is width of other monitor at left origin
        cv.setWindowProperty("transition", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        cv.waitKey(30)

    """
    don't move all the colors at the same time
    after watching a lot of pictures go gray in the middle of the transition because (1) rgb space
    is gray in the center and (2) the pixels are completely scrambled mid transition...let's fix 2.
    in the old scheme, alpha/beta are scalars in 
    x3[:] = 0.5 + ((alpha * xOld) + (beta * xNew))
    that control the fraction of the x move from xold to xnew. But xold,xnew are the linear index 
    list of coords of similar color positions. as the t/fract goes from 0 to 1 , modify ...


    """
    segments = 10 # black begins seg 0 and completes just before the middle seg 1 starts. seg 2 is white at the end. the ascending getkeys argsort makes a dark to light.
    activefraction = gNumTransitionFrames // segments
    profile = np.zeros(gNumTransitionFrames+1, dtype=np.float16) # ramp from 1 to 0, ease in, ease out      zeroes after transition
    for i in range(gNumTransitionFrames+1):
        fract = min(1, i / activefraction) # clamp fraction at 1
        profile[i] = (math.cos(math.pi * fract) + 1) / 2 # cos starts at 1, drops to -1, transforms into 1...drops 20 times...0,0,0,0,0,0,0,0
    alphas = np.ones((gNumTransitionFrames+1, yDim * xDim), dtype=np.float16) # huge 61steps*1080*1920*2bytes*2ab -> .5GB   ones before transition
    for u in range(yDim * xDim):
        ufract = u / (yDim * xDim)
        framestart = int((gNumTransitionFrames - activefraction) * ufract)
        alphas[framestart:gNumTransitionFrames+1, u] = profile[0:gNumTransitionFrames+1-framestart]
    betas = 1 - alphas

    for iFile in range(len(keyfiles)):
        gCurpic = keyfiles[iFile]
        picNew = cv.imread(os.path.join(mypath, keyfiles[iFile][1]), cv.IMREAD_COLOR)  # cv.cvtColor(, cv.COLOR_BGR2RGB)
        logger.info(f"{iFile} {picNew.shape} {keyfiles[iFile][0]} {keyfiles[iFile][1]}")
        # ydim,xdim,zdim=picNew.shape
        # the sort key for each pixel
        getkeys(picNew, newKeys)
        rankNew = newKeys.argsort()
        # rankNew[n] and rankOld[n] both hold a linear index into picNew and picOld for pixels of rank n
        # which should be similar color and location
        xNew = xpos[rankNew]
        yNew = ypos[rankNew]

        temp[xNew + yNew * xDim] = 4
        if not np.all(temp == 4):
            temp2 = np.where(temp != 4)
            raise Exception("oops 4")

        rNew = np.reshape(picNew[:, :, 2], xDim * yDim)
        rNew = rNew[rankNew]
        gNew = np.reshape(picNew[:, :, 1], xDim * yDim)
        gNew = gNew[rankNew]
        bNew = np.reshape(picNew[:, :, 0], xDim * yDim)
        bNew = bNew[rankNew]

        # each of the 2K x 2K pixels has a starting X,Y,R,G,B and an ending X,Y,R,G,B
        # the 0<=t<=1 interpolation time (maybe let it go out of range and vibrate at end)
        # drives the pixel to the destination/color
        dest = np.reshape(np.copy(picNew), (xDim * yDim, 3))
        x3 = np.zeros(yDim * xDim, dtype=np.uint32)
        y3 = np.zeros(yDim * xDim, dtype=np.uint32)
        xy = np.zeros(yDim * xDim, dtype=np.uint32)
        for t in range(gNumTransitionFrames+1):
            fract = (t) / gNumTransitionFrames  # t==0 is static
            alpha = (math.cos(math.pi * fract) + 1) / 2  # ease in, ease out 1...0
            beta = 1 - alpha
            # print(f"fract={fract:.2f} alpha={alpha:.2f} beta={beta:.2f}")
            x3[:] = 0.5 + ((alphas[t] * xOld) + (betas[t] * xNew))
            y3[:] = 0.5 + ((alphas[t] * yOld) + (betas[t] * yNew))
            xy[:] = (y3 * xDim) + x3
            # this is NOT expected, the in-transit XYs can overlap
            # temp[xy]=5
            # if not np.all(temp == 5):
            #     temp2 = np.where(temp != 5)
            #     raise Exception("oops 5")

            fract = (t) / gNumTransitionFrames  # t==0 is static
            fract = 1 - ( ( math.cos(math.pi * fract) + 1 ) / 2 ) # push the color transition even more to the center
            alpha = (math.cos(math.pi * fract) + 1) / 2  # ease in, ease out 1...0
            beta = 1 - alpha

            r3 = alphas[t] * rOld + betas[t] * rNew
            g3 = alphas[t] * gOld + betas[t] * gNew
            b3 = alphas[t] * bOld + betas[t] * bNew
            dest[xy, 0] = b3
            dest[xy, 1] = g3
            dest[xy, 2] = r3

            im = np.reshape(dest, (yDim, xDim, zDim))
            if showPictures:
                tempim = cv.resize(im, (1920, 1080))
                cv.imshow("transition", tempim)
                cv.waitKey(30)
            if t == 0:
                for k in range(gNumStaticFrames-1):
                    yield im  # gNumStaticFrames static frames
            yield im  # gNumTransitionFrames transition frames
            if iFile == len(keyfiles)-1: # the end, fade out
                for k in range(255,0,-1):
                    yield round(math.sqrt(k)*im/math.sqrt(255)) # 

        # bookkeeping...
        picOld = picNew  #
        oldKeys, newKeys = newKeys, oldKeys  # swap
        xOld = xNew
        yOld = yNew
        rOld = rNew
        gOld = gNew
        bOld = bNew
    if showPictures:
        cv.destroyWindow("transition")
        cv.waitKey(1)
