#!/bin/bash
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

# flip coordinates for tms <-> zxy
#
# this function is deprecated because the reader
# detects scheme and adjusts anyway
#
# Warning: Does not update metadata!

if [ $# -ne 2 ] ; then
    echo "Usage: mbtilesflip.sh in.mbtiles out.mbtiles" >&2
    exit 1
fi

echo rm -rf output
rm -rf output

echo mb-util $1 output
mb-util $1 output

echo mb-util --scheme=tms output $2
mb-util --scheme=tms output $2

echo rm -rf output
rm -rf output
