##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

all: subpng mbtiles-nautical-boxes

mbtiles-nautical-boxes:
	git clone https://github.com/seandepagnier/mbtiles-nautical-boxes
	make -C mbtiles-nautical-boxes

subpng: subpng.c
	gcc -o subpng subpng.c -lpng -O3 -Wno-unused-result

install: all
	install subpng /usr/local/bin
	install mbtiles2kaps.py /usr/local/bin
	install mbtilesrecolor.sh /usr/local/bin
	install mbtilesreduce.sh /usr/local/bin
	install mbtilessub.sh /usr/local/bin
	install mbtilesflip.sh /usr/local/bin

clean:
	rm -f subpng
