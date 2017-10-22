#!/usr/bin/env python

import os, sys
import uuid
import subprocess
import errno
import requests
import json
import status
import extract_header

from config import *


def mkdirs(newdir, mode=0777):
    try:
        os.makedirs(newdir, mode)
    except OSError, err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise


def cleanup_files(clean_list):
    for i in cleanup:
        print "Removing %s" % i
        try:
            os.remove(i)
        except:
            print "error removing %s" % i


def external_call(cmd_string, name='external process'):
    print cmd_string
    print "====="
    sys.stdout.flush()
    try:
        ret = subprocess.Popen(cmd_string.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        (_stdout, _stderr) = ret.communicate()
        print "%s done with ret-code: %d!" % (name, ret.returncode)
        sys.stdout.flush()
        if ret.returncode != 0:
            print _stdout, _stderr
        # print _stdout, _stderr
        return ret.returncode
    except OSError as e:
        print >> sys.stderr, "External Process Execution failed:", e
        sys.exit(1)


def register_new_image(fitsfile):
    if not os.path.isfile(fitsfile):
        return None

    params = extract_header.load_header(fitsfile)
    params["size"] = os.path.getsize(fitsfile)
    p = requests.post(url+'/api/exposures', json=params)
    if p.status_code == 200:
        res = json.loads(p.content)
        return res[u'id']
    else:
        print p
        return None

if __name__ == "__main__":

    infile = sys.argv[1]
    fitsfiles = []
    master_pid = None

    if os.path.isdir(infile):
        print "Starting in batch mode"
        master_pid = status.make_new_process('Batch Image Import', owner='Importer')
        for f in os.listdir(infile):
            if '.fits' in f:
                fitsfiles.append(os.path.join(infile, f))
    else:
        print "Starting in single-file mode"
        fitsfiles.append(infile)

    # master_pid = status.make_new_process('Image Import',owner='Importer')
    #
    # if len(fitsfiles) < 1:
    #     print "No valid input files found in %s" % scandir
    #     sys.exit(1)

    try:
        tile_dir = sys.argv[2]
    except:
        tile_dir = outfolder

    mkdirs(tile_dir)
    status.update_process(master_pid, status='WORKING')

    completed = 0
    for f in fitsfiles:

        cleanup = []

        name = os.path.basename(f)
        fid = register_new_image(f)
        pid = status.make_new_process('Import %s' % name, owner='Importer', refID=fid, parentID=master_pid)

        if fid == None:
            print "registration failed for %s" % f
            status.update_process(pid,status='Error registering metadata')
            break
        else:
            status.update_process(pid,status='Registered metadata',progress=0.1)

        outpng = os.path.join(tmp_dir, fid + '.png')
        cmd = 'python2.7 -W ignore fits2png.py %s --scale adaptive --out %s --nsamples 2500 --resize 1.0' % (f, outpng)
        retcode = external_call(cmd, 'fits2png')
        if retcode:
            cleanup_files(cleanup)
            status.update_process(pid, status='Error generating PNG')
            break
        else:
            status.update_process(pid, status='Converted FITS to PNG', progress=0.5)

        cleanup.append(outpng)

        tile_out = os.path.join(tile_dir, fid)
        mkdirs(tile_out)

        tile_name = os.path.join(tile_out, 'image.dzi')

        cmd = 'python2.7 -W ignore png2dzi.py %s %s' % (outpng, tile_name)
        retcode = external_call(cmd, 'png2dzi')
        if retcode:
            cleanup_files(cleanup)
            status.update_process(pid, status='Error generating tiles')
            break
        else:
            status.update_process(pid, status='Created .dzi tiles', progress=0.9)

        completed += 1
        progress = completed / (1.0 * len(fitsfiles))
        status.update_process(master_pid, 'Done with %s/%s' % (completed,len(fitsfiles)), progress)
        status.complete_process(pid)
        cleanup_files(cleanup)

    status.complete_process(master_pid)