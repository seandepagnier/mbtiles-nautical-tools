#!/usr/bin/python
##---------------------------------------------------------------------------
## Author:      Sean D'Epagnier
## Copyright:   
## License:     GPLv3+
##---------------------------------------------------------------------------
#
# Convert http archive to mbtiles
#

import json
import base64
import os
import sys
import subprocess

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input.har output.mbtiles"
    exit(1)

with open(sys.argv[1]) as data_file:
    data = json.load(data_file)

output = 'output'
if not os.path.exists(output):
    os.makedirs(output)

def numeric(c):
    return c == '0' or c == '1' or c == '2' or c == '3' or c == '4' or \
        c == '5' or c == '6' or c == '7' or c == '8' or c == '9'
    
for entry in data['log']['entries']:
    url = entry['request']['url']

    #search for /#/#/#

    state = 0
    count = 0
    numx = numy = numz = 0

    for c in url:
        if state == 0:
            if c == '/':
                state = 1
            count = 0

        elif state == 1:
            if c == '/' and count > 0:
                state = 2
                count = 0
            elif not numeric(c):
                state = 0
            else:
                numz *= 10
                numz += int(c)
                count = count + 1

        elif state == 2:
            if c == '/' and count > 0:
                state = 3
                count = 0
            elif not numeric(c):
                state = 0
            else:
                numx *= 10
                numx += int(c)
                count = count + 1

        elif state == 3:
            if not numeric(c):
                if count > 0:
                    state = 4
                else:
                    state = 0
            else:
                numy *= 10
                numy += int(c)
                count = count + 1
        else:
            break

    # failed to parse tms path from url
    if state != 4:
        continue

    try:
        content = entry['response']['content']
        encoding = content['encoding']
        text = content['text']
        size = content['size']
    except:
        continue
    
    if encoding == 'base64':
        decode = base64.b64decode(text)

        numy = 2 ** numz - 1 - numy

        path = 'output/%d/%d' % (numz, numx)
        filename = path+'/%d.png' % numy
        print filename
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(filename, 'wb')
        f.write(decode)
        f.close()

mbutil = ["mb-util", 'output', sys.argv[2]]
print ' '.join(mbutil)
if subprocess.call(mbutil) != 0:
    print "mbutil failed"

# cleanup
import shutil
shutil.rmtree('output', ignore_errors=True)
print ""
