#!/bin/bash
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

# reduce size with losses via pngquant

# for example:
# mbtilesreduce.sh in.mbtiles out.mbtiles colors
#
# most raster nautical charts can easily be represented in 16 colors greatly reducing file size

if [ $# -ne 3 ] ; then
    echo "Usage: mbtilesreduce.sh in.mbtiles out.mbtiles colors" >&2
    echo "Reduce tiles to png with specified number of colors" >&2
    echo "This can greatly reduce the size of an mbtiles database" >&2
    exit 1
fi

echo rm -rf output
rm -rf output

echo mb-util $1 output
mb-util $1 output

echo cd output
cd output

for i in `find | grep png`; do
    echo pngquant $3 -f --ext .png $i
    pngquant $3 -f --ext .png $i
done

echo cd ..
cd ..

echo mb-util output $2
mb-util output $2

echo rm -rf output
rm -rf output
