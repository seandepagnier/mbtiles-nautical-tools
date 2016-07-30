#!/bin/bash
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

# subtract a tile from mbtiles useful for filtering identical data from all tiles

if [ $# -ne 3 ] ; then
    echo "Usage: mbtilessub.sh in.mbtiles out.mbtiles negativetile.png" >&2
    exit 1
fi

echo rm -rf output
rm -rf output

echo mb-util $1 output
mb-util $1 output

echo cd output
cd output

for i in `find | grep png`; do
#    echo convert $i $3 -compose add  -composite
#    convert $i $3 -compose add -composite $i
    echo subpng $i $3 $i
    subpng $i $3 $i
done

echo cd ..
cd ..

echo mb-util output $2
mb-util output $2

echo rm -rf output
rm -rf output
