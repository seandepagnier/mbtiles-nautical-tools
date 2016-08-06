#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# c routines called from python for building mbtiles

from cffi import FFI
ffibuilder = FFI()

ffibuilder.set_source("kap2mbtilesffi",
    """
int read_image(const char* file_name);
void set_wp(double pwpx[10], double pwpy[10]);
void set_ply(double *ply, int cnt);
void put_tile(const char *tilepath, int tx, int ty, int c, int tilesize);
    """,
                      libraries=['png'],
                      sources=['kap2mbtiles-helper.c'],
    )

ffibuilder.cdef("""     // some declarations from the man page
int read_image(const char* file_name);
void set_wp(double pwpx[10], double pwpy[10]);
void set_ply(double *ply, int cnt);
void put_tile(const char *tilepath, double tx, double ty, double c, int tilesize);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
