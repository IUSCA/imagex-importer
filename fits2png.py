#!/usr/bin/env python

import os
import sys
import numpy
import pyfits
from scipy.ndimage.interpolation import zoom
from optparse import OptionParser
from PIL import Image
from skimage import exposure
from skimage import io
import ConfigParser

config = ConfigParser.RawConfigParser()

if __name__ == "__main__":

    # Read the command line options
    parser = OptionParser()
    parser.add_option("", "--scale", dest="scaling",
                      help="Type of scaling (lin / asinh)",
                      default="lin")
    parser.add_option("-s", "--tilesize", dest="tilesize",
                      help="size of an individual size",
                      default=512, type=int)
    parser.add_option("-o", "--out", dest="outfile",
                      help="output filename",
                      default="fits2png",
                      )
    parser.add_option("-t", "--type", dest="filetype",
                      help="file type (e.g. png, jpg)",
                      default="png",
                      )
    parser.add_option("--min", dest="mingood",
                      help="minimum good flux value",
                      default=-1e10, type=float)
    parser.add_option("--max", dest="maxgood",
                      help="maximum good flux value",
                      default=+1e10, type=float)
    parser.add_option("--mask", dest="mask",
                      help="mask all pixels without valid data",
                      action="store_true")
    parser.add_option("--resize", dest="resize",
                      help="resize output image by this factor",
                      default=0.5, type=float),
    parser.add_option("-n", "--nsamples", dest="nsamples",
                      help="number of samples for scaling determination",
                      default=1000, type=int),
    parser.add_option("-f", "--fixed", dest="fixfile",
                      help="Use or set hardcoded scaling parameters.  If fixfile does not exist (first run) it will "
                           "be created.",
                      default=False)
    parser.add_option("-i", "--fixid", dest="fixid",
                      help="Section ID to use in fixed config file.  Ignored if fixfile is not set.",
                      default="default")
    (options, cmdline_args) = parser.parse_args()

    #
    # Open FITS file
    #
    infile = cmdline_args[0]
    hdulist = pyfits.open(infile)

    #
    # Find best scaling
    #
    if '.fz' in infile:
        data = hdulist[1].data
    else:
        data = hdulist[0].data

    data = zoom(data, options.resize)
    data = numpy.asfarray(data)
    if data is None:
        print ("No image data found in PrimaryHDU - need to run mef2fits first?")
        sys.exit(0)

    print("Image-size: %d x %d" % (data.shape[1], data.shape[0]))
    print("Masking out pixels with intensities outside valid range")
    data[(data < options.mingood) | (data > options.maxgood)] = numpy.NaN

    if options.mask:
        print("Masking out pixels without valid data")
        data[data == 0.0] = numpy.NaN
    # print data
    # print data.shape

    _med = 0.0
    _sigma = 0.0
    _std = 0.0
    create_fix = False

    if options.fixfile:
        create_fix = True
        if os.path.isfile(options.fixfile):
            config.read(options.fixfile)
            if not config.has_section(options.fixid):
                create_fix = True
            else:
                create_fix = False
                _med = config.getfloat(options.fixid, '_med')
                _sigma = config.getfloat(options.fixid, '_sigma')
                options.scaling = config.get(options.fixid, 'scaling')

    if not options.fixfile or create_fix:
        n_samples = options.nsamples
        boxwidth = 10

        box_center_x = numpy.random.randint(boxwidth, data.shape[1] - boxwidth, n_samples)
        box_center_y = numpy.random.randint(boxwidth, data.shape[0] - boxwidth, n_samples)
        samples = numpy.zeros(n_samples)

        for i in range(n_samples):
            x1, x2 = int(box_center_x[i] - boxwidth), int(box_center_x[i] + boxwidth)
            y1, y2 = int(box_center_y[i] - boxwidth), int(box_center_y[i] + boxwidth)

            samples[i] = numpy.mean(data[y1:y2, x1:x2])

        #
        # Now do some filtering of the median values
        #
        valid = numpy.isfinite(samples)
        # _old_sigma, _old_med = numpy.max(samples) - numpy.min(samples)
        for _iter in range(3):

            _med = numpy.median(samples[valid])
            _std = numpy.std(samples[valid])
            print "Iteration {:d}: {:e} -- {:e}".format(_iter + 1, _med, _std)
            valid = numpy.isfinite(samples) & (samples > _med - 3 * _std) & (samples < _med + 3 * _std)
            if numpy.sum(valid) <= 0:
                break

        _sigma = _std

        if create_fix:
            config.add_section(options.fixid)
            config.set(options.fixid, '_med', _med)
            config.set(options.fixid, '_sigma', _sigma)
            config.set(options.fixid, 'scaling', options.scaling)
            with open(options.fixfile, 'wb') as configfile:
                config.write(configfile)

    gammas = {
        'sRGB': (2.4, 12.92, 0.055, 0.00304),
        'BT.709': (1. / 0.45, 4.5, 0.099, 0.018),
        'pow': (1.0, 0., 0., 0.),
    }

    norm_flux = data
    if options.scaling == "lin":
        min_intensity = _med - _sigma
        max_intensity = _med + 10 * _sigma
        print "linear Intensity scaling: %f -- %f" % (min_intensity, max_intensity)

        norm_flux = (data - min_intensity) / (max_intensity - min_intensity)
        norm_flux[norm_flux < 0] = 0.0
        norm_flux[norm_flux > 1] = 1.0
    elif options.scaling == "asinh":
        min_intensity = _med - 3 * _sigma
        max_intensity = _med + 30 * _sigma
        print "arcsinh Intensity scaling: %f -- %f" % (min_intensity, max_intensity)

        norm_flux = (data - min_intensity) / (max_intensity - min_intensity)
        norm_flux[norm_flux < 0] = 0.0
        norm_flux[norm_flux > 1] = 1.0
        norm_flux = numpy.arcsinh(norm_flux)
    elif options.scaling == "BT.709":
        min_intensity = _med - 1 * _sigma
        max_intensity = _med + 50 * _sigma
        g, a, b, It = gammas[options.scaling]
        I = (data - min_intensity) / (max_intensity - min_intensity)
        I[I < 0] = 0.0
        I[I > 1] = 1.0
        p = numpy.empty(I.shape)
        I_low = I * a
        I_hi = numpy.power(I, 1 / g) * (1 + b) - b
        p = I_low
        p[I >= It] = I_hi[I >= It]
        norm_flux = p
    elif options.scaling == "adaptive":
        min_intensity = _med - 3 * _sigma
        max_intensity = _med + 40 * _sigma
        I = (data - min_intensity) / (max_intensity - min_intensity)
        I[I < -1] = -1.0
        I[I > 1] = 1.0
        greyscale = exposure.equalize_adapthist(I, clip_limit=0.04)
        greyscale = numpy.flipud(greyscale)
        io.imsave(options.outfile, greyscale)
        sys.exit()
    #
    # Create PNG file:
    # remap data from intensity range to 0...255
    #
    greyscale = (norm_flux * 255.).astype(numpy.uint8)
    # greyscale = greyscale.astype(numpy.uint8)
    img = Image.fromarray(greyscale)
    # img = img.rotate(90)
    # greyscale.save("%s.%s" % (
    #   options.outfile, options.filetype))
    if not options.outfile.endswith(options.filetype):
        options.outfile += '.'+options.filetype
    img.transpose(Image.FLIP_TOP_BOTTOM).save("%s" % options.outfile)
