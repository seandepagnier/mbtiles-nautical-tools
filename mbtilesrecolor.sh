#!/bin/bash
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

# recolor mbtiles using color matrix, useful to apply different color schemes

# for example:
# mbtilescolor.sh in.mbtiles out.mbtiles '.8 .2 .1 .2 .7 .2 .1 .1 1'

if [ $# -ne 3 ] ; then
    echo "Usage: mbtilescolor.sh in.mbtiles out.mbtiles matrix" >&2
    exit 1
fi

echo rm -rf output
rm -rf output

echo mb-util $1 output
mb-util $1 output

echo cd output
cd output

for i in `find | grep png`; do
    echo convert $i -recolor \"$3\" $i
    convert $i -recolor "$3" $i
done

echo cd ..
cd ..

echo mb-util output $2
mb-util output $2

echo rm -rf output
rm -rf output
