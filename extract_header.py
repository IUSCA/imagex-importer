#!/usr/bin/env python

from astropy import wcs
from astropy.io import fits
import json
import os, sys


def get_zeros(header):

    # Parse the WCS keywords in the primary HDU
    w = wcs.WCS(header)

    #get RA,DEC of image coords 0,0
    zeros = w.all_pix2world([[0,0]], 0, ra_dec_order=True)
    return zeros[0]

def load_header(filename):
    hdulist = fits.open(filename)
    h = hdulist[0].header
    zeros = get_zeros(h)
    h["FILENAME"] = os.path.basename(filename)
    temp = str(str(h["COMMENT"]).encode('ascii', 'ignore'))  # encode in ascii as unicode doesn't play nice
    h = {key: value for key, value in h.items()  # remove double comment field
              if key is not "COMMENT"}
    h["COMMENT"] = temp.replace("\n", "  ")  # put comments back in

    results = {
        'name' : h['OBJECT'],
        'filter': h['FILTER'],
        'width': h['NAXIS1'],
        'height': h['NAXIS2'],
        'pixelscale': h['PIXSCAL1'],
        'ra0': zeros[0],
        'dec0': zeros[1],
        'header': h
    }

    #print results

    return results


if __name__ == '__main__':
    print load_header(sys.argv[1])
