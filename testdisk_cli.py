#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 17:18:39 2016

@author: pavel
"""
import os
import sys

import disk_operations
import utils
import testdisk
import const

from report import report_generator
    
def list_(*args, **kwargs):
    for device in disk_operations.detect_devs():
        size = utils.pretty_disk_size(disk_operations.size(device))
        sectors = disk_operations.num_sectors(device)
        
        print("{dev} : {size} ({sec} sectors)".format(dev = device,
                                                          size = size,
                                                          sec = sectors))
        
def check_device_exists(device):
    devices = [dev for dev in disk_operations.detect_devs()]
    if device not in devices:
        print("No such device:", device)
        return False
    return True 
              
def info_(device=None, **kwargs):
    devices = []    
    if device is None:
        devices = [dev for dev in disk_operations.detect_devs()]
    elif check_device_exists(device):        
        devices = [device]
        
    for dev in devices:
        print("Device:", dev)    
        print("Block device:", disk_operations.block_path(dev))
        
        size = utils.pretty_disk_size(disk_operations.size(dev))
        print("Capacity:", size)
        
        sectors = disk_operations.num_sectors(dev)
        sec_size = disk_operations.sector_size(dev)
        print(sectors, "sectors of", sec_size, "bytes")        
        
        print("Mounted as:")        
        for point in disk_operations.mount_points(dev):
            print(point)    
        
        print() 
    
def help_(*args, **kwargs):
    script_name = os.path.basename(__file__)
    print("Usage:", script_name , "command")
    print()
    print("""Commands:
        help : show this message        
        list : show available devices        
        info [device]: show information about device 
        test device [options]: test device""")
    print()
    print("""Options:
        -s=start : begin test from this sector
        -e=end : stop test after this sector""")
        
def _on_status_changed(old_status, new_status, comment) :
    print()    
    print(testdisk.get_status_name(new_status), comment)
    print()
    
def _on_progress(group_val, gr_start_sector, gr_num_sectors,
                 speed, percent, elapsed_time, left_time, num_sectors):   
    message = "Progress {percent} ({sec} of {num_sec}) \n Elaps.Time: {elp}, \t Time Left: {left}, \t Avg.speed {speed}"
    
    
    sys.stdout.write(const.LINE_UP_SYMB)
    sys.stdout.write(const.CAR_BACK_SYMB)
    sys.stdout.write(message.format(percent = utils.pretty_percent(percent), 
                                    sec = gr_start_sector + gr_num_sectors,
                                    num_sec = num_sectors,
                                    elp = utils.pretty_time_diff(elapsed_time),
                                    left = utils.pretty_time_diff(left_time),
                                    speed = utils.pretty_speed(speed)))
    sys.stdout.flush()
    
def _on_finish(bads, write_speed, read_speed, timer, device):    
    print()
    print("====================")
    print(report_generator(device, bads, write_speed, read_speed, timer))
    print("====================")
        
def test_(device, start=0, end=-1):  
    if not check_device_exists(device):
        return
    info_(device)
    print("All information will be destroyed!!!")
    print()
    """
    answer = input("Type YES to proceed: ").lower()
    if answer != "yes":
        return
    """    
    test = testdisk.DriveTest(device, start_sector = start, stop_sector = end)
    test.add_callback("update", _on_status_changed)
    test.add_callback("progress", _on_progress, test.num_sectors_test)
    test.add_callback("finish", _on_finish, device)
    test.test()    

  
if __name__ == "__main__":
    commands = {"help" : help_,
                "list" : list_,
                "info" : info_,
                "test" : test_}
    
    param_shortcuts = {"s" : "start",
                       "e" : "end" }
    command = "help"
    device = None
    params = {}   
    
    
    if len(sys.argv) >= 2:
        command = sys.argv[1].strip()
        
    if len(sys.argv) >= 3:
        device = sys.argv[2].strip()
        
    if len(sys.argv) >= 4:
        for param in sys.argv[3:]:            
            eq_pos = param.find("=")
            if eq_pos > 0:
                name = param[:eq_pos].strip("-")
                val = param[eq_pos+1:]
                
                name = param_shortcuts.get(name, name)                    
                params[name] = val
                
                
    func = commands.get(command, help_)
    
    func(device, **params)
        
        

            


    