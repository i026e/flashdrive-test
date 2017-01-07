#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 08:36:04 2017

@author: pavel
"""
import os
from datetime import datetime

def get_fname(device):
    time_ = (datetime.now().strftime("%Y.%m.%d-%H.%M"))
    dev_ = device.replace(os.path.sep, "_")
    
    return "report-{dev_}-{time_}.txt".format(dev_=dev_, time_=time_)
 
def get_home_dir():
    return os.path.expanduser("~")
                             
def get_tmp_dir():
    if os.path.isdir("/var/tmp"):
        return "/var/tmp"
    return "/tmp"
    
def default_save_path(device):
    return os.path.join(get_tmp_dir(), get_fname(device))

    
def save(path, text_data):
    try:
        with open(path, "w") as f:
            f.write(text_data)
        return None
    except Exception as e:
        return e
        
def autosave(device, report):
    path = default_save_path(device)
    return save(path, report)
