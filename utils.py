#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 16:48:33 2016

@author: pavel
"""

def pretty_percent(percent):
    return "{val:7.3f}%".format(val = percent)

def pretty_disk_size(size_bytes):
    units = ("KiB", "MiB", "GiB", "TiB")
    size = float(size_bytes)
    unit = "B"
    
    for u in units:
        if size < 1000: break
    
        size = size / 1024.0
        unit = u
        
    return "{val:8.3f} {u}".format(val=size, u=unit)
    
def pretty_speed(speed_bytes_per_sec):
    return "{val}/s".format(val = pretty_disk_size(speed_bytes_per_sec))
    
def pretty_time_diff(time_diff):
    time_sec = round(time_diff)
    hours, rest = divmod(time_sec, 3600)
    minutes, sec = divmod(rest, 60)
    
    return "{h:02d}:{m:02d}:{s:02d}".format(h=hours, m=minutes, s=sec)

def safe_get(func, default, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return default       

