import random
import math

from tqdm import tqdm
import getopt, sys
from PIL import Image


exc = []
def rng2d(x, y):
    collisions = 0
    while (brnd := (random.randrange(x), random.randrange(y))) in exc:
        collisions += 1
        if collisions > 3:
            print("#RANDOM COLLISIONS: ", collisions) #Data might be too big or the container might be too small.
        continue
    exc.append(brnd)
    return brnd


options = {}
options["pxhead"] = 8
options["lsb"] = 1
options["ext"] = False
options["verb"] = 0
argumentList = sys.argv[1:]
try:
    arguments, values = getopt.getopt(argumentList, "hes:i:o:l:p:v:", ["help", "extract", "seed", "input", "output", "lsb", "pxhead", "verbosity"])
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--help"):
            print("""Options in <> are mandatory, ones in [] are optional
            -e / --extract   <persistance>  #Default of whether to extract data or not.
            -s / --seed      <32bit int>    #PRNG seed number, aka "password".
            -i / --input     <filepath>     #If "extract flag" IS set, IMAGE filepath should be provided.
            -o / --output    <filepath>     #If "extract flag" is NOT set, IMAGE filepath should be provided.
            -l / --lsb       [int 1-8]      #Num of last bits considered least significant (1-8).              Default: 1
            -p / --pxhead    [int > 2]      #Num of pixels to leave as a size header.                          Default: 8
            -v / --verbosity [int 0-2]      #Level of verbosity. Level 2 lists all pixel accesses, be careful. Default: 0
            """)
        elif currentArgument in ("-e", "--extract"):
            options["ext"] = True
        elif currentArgument in ("-s", "--seed"): #PRNG seed
            options["seed"] = int(currentValue)
        elif currentArgument in ("-i", "--input"):
            options["input"] = currentValue
        elif currentArgument in ("-o", "--output"):
            options["output"] = currentValue
        elif currentArgument in ("-l", "--lsb"):
            options["lsb"] = int(currentValue)
        elif currentArgument in ("-p", "--pxhead"):
            options["pxhead"] = int(currentValue)
        elif currentArgument in ("-v", "--verbosity"): #0-2
            options["verb"] = int(currentValue)
except getopt.error as err:
    print(str(err))


def say(data, level):
    if level <= options["verb"]:
        print(data)


def pixtobits(img, coord, lsblen=1):
    px = tuple(map(lambda x: bin(x)[2:].zfill(8), img.getpixel(coord)))
    lsb = [c[-lsblen:] for c in px]
    say(("".join(lsb), 'r', px, coord), 2)
    return "".join(lsb)


def bitstopix(img, coord, bits, lsblen=1):
    say(("#"*64, bits, 'w', coord), 2)
    pixel = img.getpixel(coord)
    bpx = list(map(lambda x: bin(x)[2:].zfill(8), pixel))
    say((bpx, pixel), 2)
    for ch in range(3):
        bpx[ch] = bpx[ch][:-lsblen]
        bpx[ch] += bits[lsblen*ch:lsblen*(ch+1)]
        say((bpx), 2)
    px = tuple([int(c, 2) for c in bpx])
    say((bpx, px), 2)
    img.putpixel(coord, px)


if __name__=="__main__":
    random.seed(a=options["seed"])
    volume = (options["lsb"]*3)
    say(options, 1)
    
    if options["ext"]:
        im = Image.open(options["input"])
        size = int("".join([pixtobits(im, rng2d(*im.size), lsblen=options["lsb"]) for _ in range(options["pxhead"])]), 2)
        say((size, "bytes to extract"), 0)
        decoding = ""
        for i in tqdm(range(math.ceil((size*8)/volume)+1)):
            decoding += pixtobits(im, rng2d(*im.size), lsblen=options["lsb"])
        decoding = decoding[:size*8]
        byt = [decoding[i:i+8] for i in range(0, size*8, 8)]
        byt = "".join(map(lambda x: chr(int(x, 2)), byt))
        say("Saving extracted text", 0)
        with open(options["output"], "wb") as fs:
            fs.write(byt.encode())
    
    elif not options["ext"]:
        say("Encoded image will be saven with prefix 'steg_' and extension '.png'.\n  (you can edit it on line 119)", 0)
        im = Image.open(options["output"])
        if options["verb"] >= 2:
            log = Image.new("RGB", im.size, (0, 255, 0))
        with open(options["input"], "rb") as fs:
            encoding = "".join([bin(x)[2:].zfill(8) for x in fs.read()])
        pixels = math.ceil(len(encoding)/volume)
        encoding = bin(len(encoding)//8)[2:].zfill(options["pxhead"]*volume) + encoding
        encoding = encoding.ljust((pixels+options["pxhead"])*volume, "0")
        for i in tqdm(range(pixels+options["pxhead"])):
            pos = rng2d(*im.size)
            if options["verb"] >= 2:
                log.putpixel(pos, (255, 0, 0))
            bitstopix(im, pos, encoding[i*volume:(i+1)*volume], lsblen=options["lsb"])
        say("Saving image", 0)
        im.save("steg_"+options["output"]+".png", quality='keep') #LOSSY FORMATS DONT WORK
        if options["verb"] >= 2:
            log.save("log.png", quality='keep')    
    say("Quitting", 1)