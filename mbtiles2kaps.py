#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# convert mbtiles into kap files

import os
import sys
from math import ceil

args = list(sys.argv)
del args[0]

colors = 127
if len(args) > 0 and args[0] == "-colors":
   colors = int(args[1])
   del args[0]
   del args[0]

if len(args) != 2 and len(args) != 3:
    print "Usage: " + sys.argv[0] + "[-colors NUM] input.mbtiles output-dir [boxes]"
    print "Required Arguments"
    print "     input.mbtiles - tile database, must be in wmts coordinates"
    print "     output - directory name for output"
    print ""
    print "Optional Arguments:"
    print "     -colors NUM - specify how many colors to use from 2-127"
    print "                   default 16"
    print "     boxes - file containing lines with a name, and bounding box"
    print "             for each kap if not specified it will be computed"
    print "             giving full coverage of the tile database"
    print ""
    exit(1)

import subprocess
import logging
#logging.basicConfig(level=logging.DEBUG)

from landez import ImageExporter
from landez import GoogleProjection

topoutputdir = args[1];
if not os.path.exists(topoutputdir):
   os.makedirs(topoutputdir)

ie = ImageExporter(mbtiles_file=args[0], cache=False, tile_scheme='tms')
if len(args) == 3:
    f = open(args[2])
    content = f.readlines()
    crop = True
else:
   # calculate chart area by expanding contiguous areas

   zoomlevels = ie.reader.zoomlevels()
   content = []

   for zoom in range(min(zoomlevels), max(zoomlevels)+1):
#      c = ie.reader.find_coverage(zoom)
#      print "coverage", c
      num = 0
      query = ie.reader._query('''SELECT tile_column, tile_row FROM tiles
                            WHERE zoom_level=?
                            ORDER BY tile_column, tile_row;''', (zoom,))
      tiles = {}
      t = query.fetchone()
      while t:
         tiles[t] = True
         t = query.fetchone()

      while len(tiles) > 0:
         sys.stdout.write(("%d charts with %d tiles remaining\r" % (num, len(tiles))))
         sys.stdout.flush();
         # grab the first cell
         cell = sorted(list(tiles.keys()))[0]

         minp = maxp = cell

         # limit to 1000 tiles to avoid excessively huge images
         while (maxp[0]-minp[0]+1)*(maxp[1]-minp[1]+1) < 1000:
            def havecol(x, y0, y1):
               for y in range(y0, y1+1):
                  if not tiles.has_key((x, y)):
                     return False
               return True
         
            def haverow(x0, x1, y):
               for x in range(x0, x1+1):
                  if not tiles.has_key((x, y)):
                     return False
               return True

            if havecol(maxp[0]+1, minp[1], maxp[1]):
               if haverow(minp[0], maxp[0], maxp[1]+1) and tiles.has_key((maxp[0]+1, maxp[1]+1)):
                  maxp = maxp[0]+1, maxp[1]+1
               else:
                  maxp = maxp[0] + 1, maxp[1]
            else:
               if haverow(minp[0], maxp[0], maxp[1]+1):
                  maxp = maxp[0], maxp[1] + 1
               else:
                  break

         proj = GoogleProjection(ie.tile_size, [zoom])
         minll = proj.unproject_pixels((minp[0]*ie.tile_size, (maxp[1]+1)*ie.tile_size), zoom)
         maxll = proj.unproject_pixels(((maxp[0]+1)*ie.tile_size, minp[1]*ie.tile_size), zoom)

         content.append("%d %d %f %f %f %f" % (num, zoom, minll[1], minll[0], maxll[1], maxll[0]))

         # remove this block of cells
         for x in range(minp[0], maxp[0]+1):
            for y in range(minp[1], maxp[1]+1):
               del tiles[(x, y)]
         
         num = num + 1
      print "%d charts for zoom %d                              " % (num, zoom)
   crop = False

   print "will generate", len(content), "charts"

count = 0
total = len(content)

for line in content:
   l = line.rstrip().split(' ')
   bbox=(float(l[3]), float(l[2]), float(l[5]), float(l[4]))
   zoomlevel=int(l[1])

   outputdir = topoutputdir+"/"+str(zoomlevel)
   if not os.path.exists(outputdir):
      os.makedirs(outputdir)
   
   imagepath=outputdir+"/"+l[0]+".png"
   kappath=outputdir+"/"+l[0]+".kap"

   print "%.1f%%" % (100.0 * count / total), " converting ", bbox, zoomlevel
   count = count + 1

   proj = GoogleProjection(ie.tile_size, [zoomlevel])
   xmin, ymin, xmax, ymax = bbox
   ll0 = (xmin, ymax)
   ll1 = (xmax, ymin)
   px0=proj.project_pixels(ll0, zoomlevel)
   px1=proj.project_pixels(ll1, zoomlevel)

   mintile = int(px0[0]/proj.tilesize), int(px0[1]/proj.tilesize)
   maxtile = int(ceil(px1[0]/proj.tilesize)), int(ceil(px1[1]/proj.tilesize))

   print "export_image", bbox, zoomlevel, imagepath
   tilecount = (maxtile[0] - mintile[0]) * (maxtile[1] - mintile[1])
   print "%d tiles from" % tilecount, mintile, "to", maxtile
   ie.export_image(bbox, zoomlevel, imagepath)
   
   minpx = mintile[0]*proj.tilesize, mintile[1]*proj.tilesize
   maxpx = maxtile[0]*proj.tilesize, maxtile[1]*proj.tilesize

   if crop:
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
      convertcommand = ["convert", "-colors", str(colors), imagepath, imagepath]
      print ' '.join(convertcommand)
      subprocess.call(convertcommand)
      
   print ' '.join(imgkapcommand)
   subprocess.call(imgkapcommand)

