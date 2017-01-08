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
import filesave

from report import report_generator, info_generator
    
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
        dev_info = info_generator(dev)
        print(dev_info)          
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
        -e=end : stop test after this sector
        -o=output_file : save report to this file""")
        
def _on_status_changed(old_status, new_status) :
    print()    
    print(testdisk.get_status_name(new_status))
    print()
    
def _on_error(err):
    print("Unexpected error:", err)
    
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
    
def _on_finish(bads, write_speed, read_speed, timer, device, output):
    rep = report_generator(device, bads, write_speed, read_speed, timer)
    print()
    print("====================")
    print(rep)
    print("====================")
    
    filesave.autosave(device, rep)
    
    if output is not None:
        output = os.path.expanduser(output)
        err = filesave.save(output, rep)
        if err is not None:
            print("Problem with file", output)
            print(err)
        
def test_(device, start=0, end=-1, output=None):  
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
    handler = test.get_handler()
    handler.add_callback("error", _on_error)
    handler.add_callback("update", _on_status_changed)
    handler.add_callback("progress", _on_progress, start + test.num_sectors_test - 1)
    handler.add_callback("finish", _on_finish, device, output)
    test.test()    

  
if __name__ == "__main__":
    commands = {"help" : help_,
                "list" : list_,
                "info" : info_,
                "test" : test_}
    
    param_shortcuts = {"s" : ("start", int),
                       "e" : ("end", int) ,
                       "o" : ("output", str)}
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
                
                name, type_ = param_shortcuts.get(name, (name, str))                  
                params[name] = type_(val)
                
                
    func = commands.get(command, help_)
    
    func(device, **params)
        
        

            


    