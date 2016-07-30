##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------

all: subpng imgkap mbtiles-nautical-boxes

mbtiles-nautical-boxes:
	git clone https://github.com/seandepagnier/mbtiles-nautical-boxes
	make -C mbtiles-nautical-boxes

subpng: subpng.c
	gcc -o subpng subpng.c -lpng -O3 -Wno-unused-result

imgkap: imgkap.c
	gcc -o imgkap imgkap.c -lfreeimage -lm -O3

install:
	install subpng /usr/local/bin
	install imgkap /usr/local/bin
	install mbtiles2kaps.py /usr/local/bin
	install mbtilesrecolor.sh /usr/local/bin
	install mbtilesreduce.sh /usr/local/bin
	install mbtilessub.sh /usr/local/bin

clean:
	rm -f subpng imgkap
