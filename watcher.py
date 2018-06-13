#!/usr/bin/env python

import os, sys
import logging
import watchdog
import Queue
from threading import Thread
import time
import subprocess

import config

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import_queue = Queue.Queue()

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


def process_new_worker():
    while True:
        if not import_queue.empty():
            src_path = import_queue.get()
            if src_path == None:
                import_queue.task_done()
                break
            else:
                cmd = config.process_cmd + src_path
                external_call(cmd, 'PreProcessor')
                # os.remove(src_path)  ## Let the preprocessor decide to remove/keep/move file
                import_queue.task_done()
        time.sleep(1)


class Monkey(object):
    def __init__(self, filename):
        print 'Watching %s' % filename
        self._cached_stamp = 0
        self.filename = filename
        self.changed = False

    def ook(self):
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            self.changed = True
        else:
            self.changed = False


class FITSHandler(PatternMatchingEventHandler):
    patterns = ["*.fits", "*.fz"]

    def watch(self, event):
        print event.src_path, event.event_type
        watch = Monkey(event.src_path)
        time.sleep(10)
        while True:
            watch.ook()
            if not watch.changed:
                import_queue.put(event.src_path)
                break
            else:
                time.sleep(10)


    def on_created(self, event):
        self.watch(event)

    def __del__(self):
        print "Removing handler"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    observer = Observer()

    t = Thread(target=process_new_worker)
    t.daemon = True
    t.start()

    observer.schedule(FITSHandler(), config.dropfolder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        import_queue.put(None)
    observer.join()
    t.join()