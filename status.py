#!/usr/bin/env python

import requests
import json
import time
import os
from datetime import datetime

from config import *

def make_new_process(proc_name='NEWPROCESS',status='NEW',owner=None,refID=None,parentID=None):
    us = url + proc_api
    if not parentID:
        parentID = None
    data = {'name': proc_name,
            'progress': 0.0,
            'status': status,
            'owner': owner,
            'refID': refID,
            'parentID': parentID,
            'started_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    print data
    headers = {"Content-type": 'application/json',
               "Accept": "application/json"}
    r = requests.post(us, json.dumps(data), headers=headers)
    #print r.status_code, r.reason
    res = json.loads(r.content)
    #print res
    return res

def update_process(pid,  status='WORKING', progress=0.0):
    if not pid:
        return
    us = url + proc_api +"/"+pid
    data = {'progress': progress, 'status' : status}
    headers = {"Content-type": 'application/json',
               "Accept": "application/json"}
    r = requests.patch(us, json.dumps(data), headers=headers)
    #print r.status_code, r.reason

def complete_process(pid,  status='COMPLETE', progress=1.0):
    if not pid:
        return
    us = url + proc_api +"/"+pid
    data = {'progress': progress,
            'status' : status,
            'ended_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    headers = {"Content-type": 'application/json',
               "Accept": "application/json"}
    r = requests.patch(us, json.dumps(data), headers=headers)

