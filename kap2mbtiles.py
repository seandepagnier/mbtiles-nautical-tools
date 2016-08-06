#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# convert kap to mbtiles
#
# First of all, this can never work in an optimal way
# in terms of data storage because mbtiles only supports
# integral logarithmic scales
# this creates a lot more colors in the palette as the
# image gets "remapped" alternately without interpolation, dataloss is obvious
#

import sys
import os
import png
import math
import subprocess
import logging
import tempfile
from mbutil import disk_to_mbtiles, mbtiles_to_disk

#logging.basicConfig(level=logging.DEBUG)

from landez import GoogleProjection

from kap2mbtilesffi import ffi, lib

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input.kap output.mbtiles"
    exit(1)

# convert the kap to png with imgkap
kapheaderin = tempfile.NamedTemporaryFile(suffix=".kap")
kapheaderinname = kapheaderin.name
pngfile = tempfile.NamedTemporaryFile(suffix=".png")
pngfilename = pngfile.name
imgkapcommand = ["imgkap", sys.argv[1], kapheaderinname, pngfilename]
print ' '.join(imgkapcommand)
if subprocess.call(imgkapcommand) != 0:
    print "imgkap failed, aborting"
    exit(1)

# fit the refpoints
kapheader = kapheaderin
#kapheader = tempfile.NamedTemporaryFile(suffix=".kap")
#kapheadername = kapheader.name
#kapfitcommand = ["kapfit", kapheaderin, kapheadername]
#print ' '.join(kapfitcommand)
#if subprocess.call(kapfitcommand) != 0:
#    print "kapfit failed, aborting"
#    exit(1)
    
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
ply = []

for l in headerlines:
    if l[0][:6] == 'BSB/NA':
        kwl = False
        for i in l:
            v = i.split('=')
            if v[0] == 'RA':
                kap_width = int(v[1])
                kwl = True
            elif kwl:
                kap_height = int(v[0])
                kwl = False
    elif l[0][:3] == 'PLY':
        ply.append(map(float, l[1:]))
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

lib.set_wp(ffi.new("double []", wpx), ffi.new("double []", wpy))

#convertcommand = ["convert", "-define", "png:color-type=6", pngfilename, pngfilename]
#print ' '.join(convertcommand)
#subprocess.call(convertcommand)

if not lib.read_image(ffi.new("char []", pngfilename)):
    print "failed to read input file"
    exit(1)

def polytrans(c, xy):
    x, y = xy
    x2 = x*x
    y2 = y*y
    return c[0] + c[1]*x + c[2]*y + c[3]*x2 + c[4]*x*y + c[5]*y2 + \
        c[6]*x*x2 + c[7]*x2*y + c[8]*x*y2 + c[9]*y*y2

def kap_ll_to_px(p):
    return polytrans(wpx, (p[1], p[0])), polytrans(wpy, (p[1], p[0]))

def kap_px_to_ll(x, y):
    return polytrans(pwx, (x, y)), polytrans(pwy, (x, y))

# all 6 points are needed to handle polyconic projections
ll_range = kap_px_to_ll(0, 0),          kap_px_to_ll(kap_width, 0), \
           kap_px_to_ll(0, kap_height), kap_px_to_ll(kap_width, kap_height), \
           kap_px_to_ll(kap_width/2, 0), kap_px_to_ll(kap_width/2, kap_height) \

ll_min = map(min, apply(zip, ll_range))
ll_max = map(max, apply(zip, ll_range))

# read existing mbtiles
tiles_dir = tempfile.mkdtemp()
if os.path.exists(sys.argv[2]):
    os.rmdir(tiles_dir)
    mbtiles_to_disk(sys.argv[2], tiles_dir)
    os.remove(sys.argv[2])
    os.remove(tiles_dir + "/metadata.json")

tile_size = 256
proj = GoogleProjection(tile_size, range(0, 21))

# compute zoom level
px0=proj.project_pixels(ll_min, 20)
px1=proj.project_pixels(ll_max, 20)

plypx = map(kap_ll_to_px, ply)
lplypx = []
for p in plypx:
    lplypx.extend(p)

lib.set_ply(ffi.new("double []", lplypx), len(plypx))

zoom = 20 - math.log(float(px1[0] - px0[0]) / kap_width) / math.log(2)

if zoom < 1 or zoom > 20:
    print "calculated zoom %d: invalid" % zoom
    exit(1)

# for now zoom is an integer
zoom = int(math.ceil(zoom)); # make higher integer zoom to ensure no data loss

print "input %dx%d using mbtiles zoom level %d" % \
    (kap_width, kap_height, zoom)

px0=proj.project_pixels(ll_min, zoom)
px1=proj.project_pixels(ll_max, zoom)

mint = int(px0[0]/proj.tilesize), int(px1[1]/proj.tilesize)
maxt = int(math.ceil(px1[0]/proj.tilesize)), int(math.ceil(px0[1]/proj.tilesize))

tilecount = (maxt[0] - mint[0]) * (maxt[1] - mint[1])
print tilecount, "tiles from", mint, "to", (maxt[0]-1, maxt[1]-1)

c = proj.tilesize * 2**zoom;
for ty in range(mint[1], maxt[1]):
    y = ty-mint[1]
    yd = maxt[1]-mint[1]
    sys.stdout.write("%.1f%% %d of %d\r" % (100.0 * y / yd, y, yd))
    sys.stdout.flush()

    for tx in range(mint[0], maxt[0]):
        tile_dir = tiles_dir + '/' + str(zoom) + '/' + str(tx)
        if not os.path.exists(tile_dir):
            os.makedirs(tile_dir)

        tile_path = tile_dir + '/' + str(ty) + '.png'
        lib.put_tile(ffi.new("char []", tile_path), tx, ty, c, proj.tilesize)

# write mbtiles to disk
disk_to_mbtiles(tiles_dir, sys.argv[2])

# cleanup
import shutil
shutil.rmtree(tiles_dir, ignore_errors=True)
print ""
