#!/bin/bash

# Old script, not good method, see python version

if [ $# -ne 2 ] ; then
    echo "Usage: mbtiles2kap.sh filename.mbtiles filename.kap" >&2
    exit 1
fi

echo mb-util $1 output
mb-util $1 output

cd output

#convert tiles to kap
# requires montage and convert from imagemagick as well as imgkap
# kap is a single image not a pyramid, select first directory
Z=`ls -t1 | head -n 1`


#Z=18

cd $Z
echo "entering `pwd`"

# combine into columns
for i in `ls`; do
    echo montage -geometry 256x256+0+0 -tile 1x `find $i | sort -r | xargs echo`/out1.png;
   montage -geometry 256x256+0+0 -tile 1x `find $i | sort -r | xargs echo`/out1.png;
   done

# combine columns to make full image (this can be slow and use lots of ram)
echo "montage -geometry 256x$((256*($(find $(ls -1 | head -n 1) | wc -l)-2)))+0+0 -tile `ls -1 | wc -l`x1 `find | grep out1.png | sort | xargs echo` out2.png"
montage -geometry 256x$((256*($(find $(ls -1 | head -n 1) | wc -l)-2)))+0+0 -tile `ls -1 | wc -l`x1 `find | grep out1.png | sort | xargs echo` out2.png

# clean up intermediate files
find | grep out1.png | xargs rm

# flip y for kap
echo convert out2.png -flip out.png
convert out2.png -flip out.png

rm out2.png

# use convert to reduce to 16 color for better compression
echo convert out.png -colors 16 out.png
convert out.png -colors 16 out.png

# calculate lat/lon coordinates
X0=`ls -1 | head -n 1`
X1=`ls -1 | grep -v out | tail -n 1`
STARTLON=$(echo "360*($X0)/2^$Z-180" | bc -l)
ENDLON=$(echo "360*($X1+1)/2^$Z-180" | bc -l)

Y0=`ls -1 $X0 | head -n 1 | sed s/\\.png//1`
Y1=`ls -1 $X0 | tail -n 1 | sed s/\\.png//1` 
STARTLAT=$(echo "pi=4*a(1); n=pi-2*pi*($Y0)/(2^$Z); 180/pi*a(.5*(e(-n)-e(n)))" | bc -l)
ENDLAT=$(echo "pi=4*a(1); n=pi-2*pi*($Y1+1)/(2^$Z); 180/pi*a(.5*(e(-n)-e(n)))" | bc -l)

echo imgkap out.png $STARTLAT $STARTLON $ENDLAT $ENDLON ../../$2
echo `pwd`
imgkap out.png $STARTLAT $STARTLON $ENDLAT $ENDLON ../../$2

cd ../..
rm -r output
