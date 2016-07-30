#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# convert mbtiles into kap files

import sys
from math import ceil

args = list(sys.argv)
del args[0]

colors = 16
if len(args) > 0 and args[0] == "-colors":
   colors = int(args[1])
   del args[0]
   del args[0]

if len(args) != 1 and len(args) != 2:
    print "Usage: " + sys.argv[0] + "[-colors NUM] input.mbtiles [boxes]"
    print "Required Arguments"
    print "     input.mbtiles - tile database, must be in wmts coordinates"
    print ""
    print "Optional Arguments:"
    print "     -colors NUM - specify how many colors to use from 2-127"
    print "                   default 16"
    print "     boxes - file containing lines with a name, and bounding box"
    print "             for each kap if not specified it will be computed"
    print "             giving full coverage of the tile database"
    print ""
    exit(1)

#sys.path.insert(0, '/home/sean/build/landez')

import subprocess
import logging
#logging.basicConfig(level=logging.DEBUG)

from landez import ImageExporter
from landez import GoogleProjection

ie = ImageExporter(mbtiles_file=args[0], cache=False, tile_scheme='tms')
if len(args) == 2:
    f = open(args[1])

content = f.readlines()

count = 0
total = len(content)

for line in content:
    l = line.rstrip().split(' ')
    print l
    bbox=(float(l[2]), float(l[1]), float(l[4]), float(l[3]))
    zoomlevel=17
    imagepath=l[0]+".png"
    kappath=l[0]+".kap"

    print "%.1f%%" % (100.0 * count / total), " converting ", bbox, zoomlevel
    count = count + 1

    ie.export_image(bbox, zoomlevel, imagepath)

#    proj = GoogleProjection(ie.tile_size, [zoomlevel], 'wmts')
    proj = GoogleProjection(ie.tile_size, [zoomlevel])
    xmin, ymin, xmax, ymax = bbox
    ll0 = (xmin, ymax)
    ll1 = (xmax, ymin)
    px0=proj.project_pixels(ll0, zoomlevel)
    px1=proj.project_pixels(ll1, zoomlevel)
    print px0, px1, ll0, ll1
    mintile = int(px0[0]/proj.tilesize), int(px0[1]/proj.tilesize)
    maxtile = int(ceil(px1[0]/proj.tilesize)), int(ceil(px1[1]/proj.tilesize))

    tilecount = (maxtile[0] - mintile[0]) * (maxtile[1] - mintile[1])
    print "%d tiles from" % tilecount, mintile, "to", maxtile

    minpx = mintile[0]*proj.tilesize, mintile[1]*proj.tilesize
    maxpx = maxtile[0]*proj.tilesize, maxtile[1]*proj.tilesize

    crop = 1
    if crop == 1:
        p0 = px0[0] - minpx[0], px0[1] - minpx[1];
        p1 = px1[0] - minpx[0], px1[1] - minpx[1];
        size = p1[0] - p0[0], p1[1] - p0[1];
        cropcommand = ["convert", imagepath, "-crop", "%dx%d+%d+%d" % (size[0], size[1], p0[0], p0[1]), imagepath]
        print ' '.join(cropcommand)
        subprocess.call(cropcommand)

        imgkapcommand = ["imgkap", imagepath, str(ll0[1]), str(ll0[0]), str(ll1[1]), str(ll1[0]), kappath]
    else:
        minll = proj.unproject_pixels(minpx, zoomlevel)
        maxll = proj.unproject_pixels(maxpx, zoomlevel)
        imgkapcommand = ["imgkap", imagepath, str(minll[1]), str(minll[0]), str(maxll[1]), str(maxll[0]), kappath]

    usepngquant = 1
    if usepngquant == 1:
        pngquantcommand = ["pngquant", str(colors), "-f", "--ext", ".png", imagepath]
        print ' '.join(pngquantcommand)
        subprocess.call(pngquantcommand)
    else:
        convertcommand = ["convert", "-colors", colors, imagepath, imagepath]
        print ' '.join(convertcommand)
        subprocess.call(convertcommand)

    print ' '.join(imgkapcommand)
    subprocess.call(imgkapcommand)
