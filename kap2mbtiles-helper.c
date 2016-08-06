/*   Copyright (C) 2016 by Sean D'Epagnier                                 *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#include <math.h>

#include "pngsimple.c"

static double polytrans(double c[10], double x, double y)
{
    double x2 = x*x;
    double y2 = y*y;

    return c[0] + c[1]*x + c[2]*y + c[3]*x2 + c[4]*x*y + c[5]*y2 +
        c[6]*x*x2 + c[7]*x2*y + c[8]*x*y2 + c[9]*y*y2;
}

static struct png_file image;
int read_image(const char* file_name)
{
    return read_png_file(file_name, &image);
}

static double wpx[10], wpy[10];
void set_wp(double pwpx[10], double pwpy[10])
{
    memcpy(wpx, pwpx, sizeof wpx);
    memcpy(wpy, pwpy, sizeof wpy);
}

static double *ply;
static int plycnt;
void set_ply(double *p, int cnt)
{
    plycnt = cnt;
    int size = sizeof(double)*cnt*2;
    ply = malloc(size);
    memcpy(ply, p, size);
}

static int test_ply(double x, double y)
{
    int total = 0;
    int l = plycnt-1;
    for(int i=0; i<plycnt; i++) {
        double x0 = ply[2*i], y0 = ply[2*i+1];
        double x1 = ply[2*l], y1 = ply[2*l+1];
        l = i;
        double xl, xh, yl, yh;
        if(x0 > x1)
            xl = x1, yl = y1, xh = x0, yh = y0;
        else
            xl = x0, yl = y0, xh = x1, yh = y1;

        if(x < xl)
            continue;

        if(x >= xh)
            continue;

        if(y > yl) {
            if(y > yh || (y - yl)*(xh - xl) > (yh - yl) * x)
                total++;
        } else if(y > yh && (y - yl)*(xh - xl) > (yh - yl) * x)
            total++;
    }

    return total&1;
}

static double unproject_lat(double y, double c)
{
    double g = M_PI*(1 - 2*y/c);
    return 180/M_PI * (2 * atan(exp(g)) - M_PI/2);
}

static double unproject_lon(double x, double c)
{
    return 360*x/c - 180;
}

#define minmax(v, min, max) (v < min ? min : v > max ? max : v)
void put_tile(const char *tilepath, int tx, int ty, int c, int tilesize)
{
    struct png_file tile;

    if(read_png_file(tilepath, &tile)) {
        if(tile.width != tilesize || tile.height != tilesize) {
            printf("invalid tile %s\n", tilepath);
            exit(1);
        }
    } else {
        // initialize tile to transparent
        tile.width = tile.height = tilesize;
        tile.color_type = 6;
        tile.bit_depth = 8;

        tile.row_pointers = (png_bytep*) malloc(sizeof(png_bytep) * tilesize);
        for (int y=0; y<tilesize; y++) {
            tile.row_pointers[y] = (png_byte*) malloc(4*tilesize);
            memset(tile.row_pointers[y], 0, 4*tilesize);
        }
    }
    
    // remap the input kap into the tile pixel by pixel
    int write = 0; // don't write if no pixels are written
    for(int y=0; y<tilesize; y++) {
        double lat = unproject_lat(ty*tilesize+y, c);
        unsigned char *tr = tile.row_pointers[y];
        for(int x=0; x<tilesize; x++) {
            double lon = unproject_lon(tx*tilesize+x, c);
            double kap_x = polytrans(wpx, lon, lat);
            double kap_y = polytrans(wpy, lon, lat); 
            int kap_x0 = (int)floor(kap_x), kap_y0 = (int)floor(kap_y);

            if(kap_x0 >= 0 && kap_x0 < image.width-1 &&
               kap_y0 >= 0 && kap_y0 < image.height-1 &&
               test_ply(kap_x, kap_y)) {
                double dx = kap_x - kap_x0;
                double dy = kap_y - kap_y0;

                unsigned char *r0 = image.row_pointers[kap_y0];
                unsigned char *r1 = image.row_pointers[kap_y0+1];
                int i0 = 4*kap_x0, i1 = 4*(kap_x0+1);
                for(int k=0; k<3; k++) {
                    if(0) // interpolate
                    {
                        double v0 = r0[i0+k];
                        double v1 = r0[i1+k];
                        double v2 = r1[i0+k];
                        double v3 = r1[i1+k];

                        double v01 = v0*(1-dx) + v1*dx;
                        double v23 = v2*(1-dx) + v3*dx;

                        double v = v01*(1-dy) + v23*dy;
                        v = minmax(v, 0, 255);
                        tr[4*x+k] = v;
                    } else {
                        int kap_xi = round(kap_x), kap_yi = round(kap_y);
                        tr[4*x+k] = image.row_pointers[kap_yi][4*kap_xi + k];
                    }
                }
                tr[4*x+3] = 255;
                write = 1;
            }
        }
    }

    if(write)
        write_png_file(tilepath, &tile);
}
