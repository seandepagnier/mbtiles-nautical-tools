#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# convert kap to mbtiles

import sys
import os
import png
import math
import subprocess
import logging
import tempfile
from mbutil import disk_to_mbtiles
#logging.basicConfig(level=logging.DEBUG)

from landez import ImageExporter
from landez import GoogleProjection

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input.kap output.mbtiles"
    exit(1)

# convert the kap to png with imgkap
kapheader = tempfile.NamedTemporaryFile(suffix=".kap")
kapheadername = kapheader.name
pngfile = tempfile.NamedTemporaryFile(suffix=".png")
pngfilename = pngfile.name
imgkapcommand = ["imgkap", sys.argv[1], kapheadername, pngfilename]
print ' '.join(imgkapcommand)
if subprocess.call(imgkapcommand) != 0:
    print "imgkap failed, aborting"
    exit(1)

content = kapheader.readlines()

prev = []
headerlines = []
# pre-parse header combining multilines
for line in content:
    l = line.rstrip()
    if l[:4] == '    ':
        prev = prev + l.strip().split(',')
    else:
        if len(prev):
            headerlines.append(prev)
        prev = l.split(',')
headerlines.append(prev)

# parse kap header
wpx = wpy = pwx = pwy = []
projection = None
for l in headerlines:
    if l[0][:6] == 'KNP/SC':
        for i in l:
            v = i.split('=')
            if v[0] == 'PR':
                projection = v[1]
    elif l[0][:3] == 'WPX':
        wpx = map(float, l[1:])
    elif l[0][:3] == 'WPY':
        wpy = map(float, l[1:])
    elif l[0][:3] == 'PWX':
        pwx = map(float, l[1:])
    elif l[0][:3] == 'PWY':
        pwy = map(float, l[1:])

if min(map(len, (wpx, wpy, pwx, pwy))) < 3:
    print "input kap has not enough polynominals"
    exit(1)

# expand polynominals to have enough zeros
map(lambda l: l.extend([0, 0, 0, 0, 0, 0, 0, 0, 0]), (wpx, wpy, pwx, pwy))

if not projection:
    print "invalid or unsupported projection"
    exit(1)
    
# convertcommand = ["convert", "-define", "png:color-type=6", imagepath, imagepath]
#    print convertcommand
#    subprocess.call(convertcommand)

r = png.Reader(pngfile)
kap_width, kap_height, png_data, png_info = r.asRGB8()
print "reading png data (this may take a while)"
kap_pixels = list(png_data)

def polytrans(c, xy):
    x, y = xy
    x2 = x*x
    y2 = y*y

    return c[0] + c[1]*x + c[2]*y + c[3]*x2 + c[4]*x*y + c[5]*y2 + \
        c[6]*x*x2 + c[7]*x2*y + c[8]*x*y2 + c[9]*y*y2
    
def kap_px_to_ll(x, y):
    return polytrans(pwx, (x, y)), polytrans(pwy, (x, y))

def kap_ll_to_px(ll):
    return polytrans(wpx, ll), polytrans(wpy, ll)

def kap_px_at(x, y):
    return kap_pixels[y][3*x], kap_pixels[y][3*x+1], kap_pixels[y][3*x+2]

# all 4 corners are needed to handle polyconic projections
ll_range = kap_px_to_ll(0, 0),          kap_px_to_ll(kap_width, 0), \
           kap_px_to_ll(0, kap_height), kap_px_to_ll(kap_width, kap_height)

ll_min = map(min, apply(zip, ll_range))
ll_max = map(max, apply(zip, ll_range))

# read existing mbtiles
tiles_dir = tempfile.mkdtemp()
if os.path.exists(sys.argv[2]):
    mbtiles_to_disk(sys.argv[2], tiles_dir)

tile_size = 256
proj = GoogleProjection(tile_size, range(0, 21))

# compute zoom level
px0=proj.project_pixels(ll_min, 20)
px1=proj.project_pixels(ll_max, 20)

zoom = 20 - int(math.log(float(px1[0] - px0[0]) / kap_width) / math.log(2))

if zoom < 1 or zoom > 20:
    print "calculated zoom %d: invalid" % zoom
    exit(1)

print "input %dx%d with projection %s, using mbtiles zoom level %d" % \
    (kap_width, kap_height, projection, zoom)

px0=proj.project_pixels(ll_min, zoom)
px1=proj.project_pixels(ll_max, zoom)

mint = int(px0[0]/proj.tilesize), int(px1[1]/proj.tilesize)
maxt = int(math.ceil(px1[0]/proj.tilesize)), int(math.ceil(px0[1]/proj.tilesize))

tilecount = (maxt[0] - mint[0]) * (maxt[1] - mint[1])
print tilecount, "tiles from", mint, "to", (maxt[0]-1, maxt[1]-1)

for yt in range(mint[1], maxt[1]):
    y = yt-mint[1]
    yd = maxt[1]-mint[1]
    sys.stdout.write("%.1f%% %d of %d\r" % \
                     (100.0 * y / yd, y, yd))
    sys.stdout.flush()

    for xt in range(mint[0], maxt[0]):
        tile_dir = tiles_dir + '/' + str(zoom) + '/' + str(xt)
        tile_path = tile_dir + '/' + str(yt) + '.png'
        if os.path.exists(tile_path):
            r = png.Reader(tile_path)
            x, y, p, i = r.asRGBA8();
            if x != proj.tilesize or y != proj.tilesize:
                print "invalid tile %d, %d", zoom, tx, ty
                exit(1)
            tile_pixels = list(p)
        else:
            if not os.path.exists(tile_dir):
                os.makedirs(tile_dir)

            # initialize tile to transparent
            scanline = []
            for x in range(0, proj.tilesize):
                scanline.append(0)
                scanline.append(0)
                scanline.append(0)
                scanline.append(0)

            tile_pixels = []
            for y in range(0, proj.tilesize):
                tile_pixels.append(scanline[:])

        # remap the input kap into the tile pixel by pixel
        for y in range(0, proj.tilesize):
            for x in range(0, proj.tilesize):

                p = (xt*proj.tilesize+x, yt*proj.tilesize+y)
                
                ll = proj.unproject_pixels(p, zoom)
                kap_px = kap_ll_to_px(ll)
                kap_px0 = int(kap_px[0]), int(kap_px[1])

                if kap_px0[0] >= 0 and kap_px0[0] < kap_width-1 and \
                   kap_px0[1] >= 0 and kap_px0[1] < kap_height-1:
                    d = kap_px[0] - kap_px0[0], kap_px[1] - kap_px0[1]

                    interp = True
                    if interp:
                        v0 = kap_px_at(kap_px0[0],   kap_px0[1])
                        v1 = kap_px_at(kap_px0[0]+1, kap_px0[1])
                        v2 = kap_px_at(kap_px0[0],   kap_px0[1]+1)
                        v3 = kap_px_at(kap_px0[0]+1, kap_px0[1]+1)

                        def interp(d, v0, v1):
                            return map(lambda v0, v1: v0*(1-d) + v1*d, v0, v1)

                        v01 = interp(d[0], v0, v1)
                        v23 = interp(d[0], v2, v3)

                        v = interp(d[1], v01, v23)
                    else:
                        v = kap_px_at(int(round(kap_px0[0])),
                                      int(round(kap_px0[1])))

                    v = map(lambda x : min(max(int(x), 0), 255), v)

                    ind = 4*x
                    tile_pixels[y][ind+0] = v[0]
                    tile_pixels[y][ind+1] = v[1]
                    tile_pixels[y][ind+2] = v[2]
                    tile_pixels[y][ind+3] = 255

        png.from_array(tile_pixels, 'RGBA').save(tile_path)

# write mbtiles to disk
disk_to_mbtiles(tiles_dir, sys.argv[2])

# cleanup
import shutil
shutil.rmtree(tiles_dir, ignore_errors=True)
