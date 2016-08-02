#!/bin/bash
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

# convert format of mbtiles database (eg: png->jpg)

# for example:
# mbtilesreduce.sh in.mbtiles out.mbtiles png jpg
#
# most satellite imagery compresses far better in jpg format

if [ $# -ne 4 ] ; then
    echo "Usage: mbtilesconvert.sh in.mbtiles out.mbtiles oldext newext" >&2
    exit 1
fi

echo rm -rf output
rm -rf output

echo mb-util $1 output
mb-util $1 output

echo cd output
cd output

for i in `find | grep png`; do
    echo convert -quality 40 $i ${i/$3/$4}
    convert -quality 40 $i ${i/$3/$4}
    rm $i
done

echo cd ..
cd ..

echo mb-util output $2
mb-util --image_format $4 output $2 > /dev/null

echo rm -rf output
rm -rf output
