/*
 * Copyright 2002-2010 Guillaume Cottenceau.
 *
 * This software may be freely redistributed under the terms
 * of the X11 license.
 *
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#include "pngsimple.c"

void process_file(struct png_file *i, struct png_file *s)
{
    if (png_get_color_type(i->png_ptr, i->info_ptr) == PNG_COLOR_TYPE_RGB)
        abort_("[process_file] input file is PNG_COLOR_TYPE_RGB but must be PNG_COLOR_TYPE_RGBA "
               "(lacks the alpha channel)");

    if (png_get_color_type(i->png_ptr, i->info_ptr) != PNG_COLOR_TYPE_RGBA)
        abort_("[process_file] color_type of input file must be PNG_COLOR_TYPE_RGBA (%d) (is %d)",
               PNG_COLOR_TYPE_RGBA, png_get_color_type(i->png_ptr, i->info_ptr));

    if (png_get_color_type(s->png_ptr, s->info_ptr) == PNG_COLOR_TYPE_RGB)
        abort_("[process_file] sub file is PNG_COLOR_TYPE_RGB but must be PNG_COLOR_TYPE_RGBA "
               "(lacks the alpha channel)");

    if (png_get_color_type(s->png_ptr, s->info_ptr) != PNG_COLOR_TYPE_RGBA)
        abort_("[process_file] color_type of sub file must be PNG_COLOR_TYPE_RGBA (%d) (is %d)",
               PNG_COLOR_TYPE_RGBA, png_get_color_type(s->png_ptr, s->info_ptr));

    if(i->height != s->height || i->width != s->width)
        abort_("not matching dimensions input!\n");
    
    int x, y, k;
    for (y=0; y<i->height; y++) {
        png_byte* row = i->row_pointers[y];
        png_byte* srow = s->row_pointers[y];
        for (x=0; x<i->width; x++) {
            png_byte* sptr = &(srow[x*4]);
            if(sptr[0] == 0 && sptr[1] == 0 && sptr[2] == 0)
                continue;

            png_byte* ptr = &(row[x*4]);

            for(k=0; k<3; k++)
                ptr[k] = ptr[k] + (sptr[k]>>1) + (sptr[k]*ptr[k]>>9);
        }
    }
}

int main(int argc, char **argv)
{
    if (argc != 4)
        abort_("Usage: program_name <file_in> <file_sub> <file_out>");

    struct png_file i, s;
    read_png_file(argv[1], &i);
    read_png_file(argv[2], &s);
    process_file(&i, &s);
    write_png_file(argv[3], &i);

    return 0;
}
