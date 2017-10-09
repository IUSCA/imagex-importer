#!/usr/bin/env python

import os, sys
import deepzoom

def main():
    source = sys.argv[1]
    dest = sys.argv[2]

    if not os.path.isfile(source):
        sys.exit(1)
    creator = deepzoom.ImageCreator(tile_size=512, tile_overlap=2, tile_format="png", image_quality=0.9, resize_filter="bicubic")
    creator.create(source, dest)

if __name__ == "__main__":
    main()