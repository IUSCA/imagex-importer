#!/usr/bin/env python

from astropy import wcs
from astropy.io import fits
import json
import os, sys
from collections import OrderedDict as od

def get_corners(header):

    # Parse the WCS keywords in the primary HDU
    _wcs = wcs.WCS(header)

    #get RA,DEC of image coords 0,0
    w = header['NAXIS1'] - 1
    h = header['NAXIS2'] - 1
    ccs = [[0,0],[w,0],[w,h],[0,h]]
    corners = _wcs.all_pix2world(ccs, 0, ra_dec_order=True)
    return corners.tolist()

def get_key(header, keywords, default):
    for k in keywords:
        if k in header:
            return header[k]

    return default


def header_to_orderdict(h, exclude=[]):
    d = od()
    for key, value in h.items():
        if key not in exclude:
            d[key] = value
    return d

def header_to_array(h, exclude=[]):
    a = []
    for key, value in h.items():
        if key not in exclude:
            a.append({'key':key, 'value':value, 'comment': h.comments[key]})
    return a

def load_header(filename):
    hdulist = fits.open(filename)
    if '.fz' in filename:
        h = hdulist[1].header
    else:
        h = hdulist[0].header
    corners = get_corners(h)
    h["FILENAME"] = os.path.basename(filename)
    try:
        temp = str(str(h["COMMENT"]).encode('ascii', 'ignore'))  # encode in ascii as unicode doesn't play nice
    except:
        temp = "No comments"
    _h = header_to_orderdict(h, ['COMMENT'])
    _h["COMMENT"] = temp.replace("\n", "  ")  # put comments back in

    results = {
        'name' : get_key(h, ['OBJECT','TILENAME'], 'Unknown'),
        'filter': h['FILTER'],
        'width': h['NAXIS1'],
        'height': h['NAXIS2'],
        'pixelscale': get_key(h, ['PIXSCAL1', 'PIXLSCAL'], 0.2),
        'corners' : corners,
        'ra0': corners[0][0],
        'dec0': corners[0][1],
        'loc.type' : 'Point',
        'loc.coordinates' : [corners[0][0] - 180.0, corners[0][1]],
        'header': _h
    }

    #print results

    return results


if __name__ == '__main__':
    print load_header(sys.argv[1])
