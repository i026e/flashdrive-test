#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 07:34:45 2016

@author: pavel
"""
import os


#!/usr/bin/env python

"""
Read block device data from sysfs
"""


import glob
import re


from const import BLK_DEVICE_PATTERN


def detect_devs():
    #http://echorand.me/site/notes/articles/python_linux/article.html
    for block_device in glob.glob("/sys/block/*"):
        for pattern in BLK_DEVICE_PATTERN:
            if re.compile(pattern).match(os.path.basename(block_device)):
                yield dev_path(block_device)

def block_path(device):
    """return /sys/block/... path"""
    return os.path.join("/sys/block", os.path.basename(device))
    
def dev_path(block_device):
    """return /dev/... path"""
    return os.path.join("/dev", os.path.basename(block_device))

def num_sectors(device):
    block_device = block_path(device)
    with open(block_device+"/size") as s_size:
        return int(s_size.read().rstrip("\n"))
    
def sector_size(device):
    block_device = block_path(device)
    with open(block_device+"/queue/hw_sector_size") as s_size:
        return int(s_size.read().rstrip("\n"))
                
def size(device):
    """Get the device size (in bytes) """
    block_device = block_path(device)
    return num_sectors(block_device) * sector_size(block_device)
    
def disk_size(device):
    """ Get the device size (in bytes)  by seeking at end"""
    fd = os.open(device, os.O_RDONLY) 
    size = os.lseek(fd, 0, os.SEEK_END)
    os.close(fd)
    return size    

def mount_points(device):
    with open("/proc/mounts", "r") as ifp:
        for line in ifp:
            params = line.strip().split()
            if (len(params) > 1) and params[0].startswith(device):
                yield(params[1])
                
def unmount(device):
    for point in mount_points(device):
        os.system("umount %s" % point)
        #yield(point)



def read(device, sector_size, start, num_sectors):
    """device : disk to read from
       bloc_size : size of one data chunk in bytes
       start : start block number
       num_blocks : number of blocks to read
    """
        
    with open(device, "rb") as data_stream:
        data_stream.seek(start * sector_size) # set cursor
        
        for block_ind in range(num_sectors):
            data = data_stream.read(sector_size)
            
            yield start + block_ind, data
            
def write(device, sector_size, start, num_sectors, get_data_func):
    """device : disk to read from
       bloc_size : size of one data chunk in bytes
       start : start block number
       num_blocks : number of blocks to write
       get_data_func : function(index, block_size) should return byte string
    """
    with open(device, "rb+") as data_stream:
        data_stream.seek(start * sector_size) # set cursor
        
        for sector_ind in range(num_sectors):
            abs_sector_ind = start + sector_ind
            data = get_data_func(abs_sector_ind, sector_size)
            result = data_stream.write(data)
            
            yield abs_sector_ind, result
    

        