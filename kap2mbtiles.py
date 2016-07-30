##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# convert kap to mbtiles

import sys

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input.mbtiles"
    exit(1)

sys.path.insert(0, '/home/sean/build/landez')

import subprocess
import logging
logging.basicConfig(level=logging.DEBUG)

from landez import ImageExporter
from landez import GoogleProjection

ie = ImageExporter(mbtiles_file=sys.argv[1])
f = open(sys.argv[2])
content = f.readlines()

for line in content:
    l = line.rstrip().split(' ')

    bbox=(float(l[2]), float(l[1]), float(l[4]), float(l[5]))
    zoomlevel=8
    imagepath=l[0]+".png"
    kappath=l[0]+".kap"

    proj = GoogleProjection(ie.tile_size, [16], 'wmts')
    xmin, ymin, xmax, ymax = bbox
    ll0 = (xmin, ymax)
    ll1 = (xmax, ymin)
    px0=proj.project_pixels(ll0, zoomlevel)
    px1=proj.project_pixels(ll1, zoomlevel)
    minpx = int(px0[0]/proj.tilesize)*proj.tilesize, int(px0[1]/proj.tilesize)*proj.tilesize
    maxpx = (int(px1[0]/proj.tilesize)+1)*proj.tilesize, (int(px1[1]/proj.tilesize)+1)*proj.tilesize
    minll = proj.unproject_pixels(minpx, zoomlevel)
    maxll = proj.unproject_pixels(maxpx, zoomlevel)
    ie.export_image(bbox, zoomlevel, imagepath)

#    convertcommand = ["convert", imagepath, imagepath]
#    print convertcommand
#    subprocess.call(convertcommand)

    imgkapcommand = ["imgkap", imagepath, str(minll[1]), str(minll[0]), str(maxll[1]), str(maxll[0]), kappath]
    print imgkapcommand
    subprocess.call(imgkapcommand)
