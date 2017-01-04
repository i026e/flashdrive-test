#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 09:10:30 2016

@author: pavel
"""

import data_generator as data_gen
import disk_operations as dsk_opr

from statistics import BadSectors, Speed, Timer, Percent


STATUS_INIT         = 0
STATUS_FINISHED     = 1
STATUS_ERROR        = 2
STATUS_CANCELLED    = 3
    
STATUS_PREPARING    = 10
STATUS_WRITING      = 11
STATUS_COMPARING    = 12    


names = {STATUS_INIT : "Initialization",
         STATUS_FINISHED : "Finished",
         STATUS_ERROR : "Error",
         STATUS_CANCELLED : "Cancelled",
         STATUS_PREPARING : "Preparing...",
         STATUS_WRITING : "Writing data...",
         STATUS_COMPARING : "Checking data..."
         } 

def get_status_name(status):
    return names.get(status, "Unknown status") 

class GroupOfSectors:
    def __init__(self, group_size, start_sector, stop_sector):
        self.group_size = group_size
        self.start_sector = start_sector
        self.stop_sector = stop_sector
        
        self.reset_group()
        
    def add(self, sector_index, sector_val):
        if not self.group_setted: self.set_group(sector_index)
            
        self.group_val &= sector_val
        
        if ( ((sector_index - self.group_start) >= self.group_size) or
            (sector_index == self.stop_sector)):
            
            val = self.group_val
            start = self.group_start
            size = sector_index - self.group_start
            
            self.reset_group()
            
            return val, start, size
            
    def reset_group(self):
        self.group_setted = False
        self.group_start = self.start_sector
        self.group_val = True
        
            
    def set_group(self, sector_index):
        self.group_setted = True
        self.group_start = sector_index
        self.group_val = True
        


class EventHandler:
    def __init__(self, period, sector_size, start_sector, stop_sector):
        """period (in sectors) : how often send uppdates"""
        print(start_sector, stop_sector)
        self.sectors_group = GroupOfSectors(period, start_sector, stop_sector)
        
        self.start_sector = start_sector
        self.stop_sector = stop_sector
        self.num_sectors = stop_sector - start_sector
                
        self.bads = BadSectors(start_sector)
        self.write_speed = Speed(sector_size, start_sector)
        self.read_speed = Speed(sector_size, start_sector)
        
        print(start_sector, stop_sector)
        self.percent_done = Percent(start_sector, stop_sector, 2)
        self.timer = Timer(0, 100) # percents
        
        self.listeners = {"finish": [],
                          "cancel": [],
                          "progress" : [],
                          "update" : [] }
                          
    def add_listener(self, event, func, *user_data):
        if event in self.listeners:
            self.listeners[event].append((func, user_data))        
        
    def _on_status_update(self, old_status, new_status, data):
        for listener, user_data in self.listeners["update"]:
            listener(old_status, new_status, data, *user_data)
             
    def _on_finish(self, is_ok): 
        if is_ok:
            for listener, user_data in self.listeners["finish"]:
                listener(self.bads, self.write_speed, self.read_speed, self.timer, *user_data)            
        
    
    def _on_cancel(self, is_ok):
        if is_ok:
            for listener, user_data in self.listeners["cancel"]:
                listener(*user_data)
    
    def _on_progress(self, group_val, gr_start_sector, gr_num_sectors, 
                    speed, percent, elapsed_time, left_time):
        for listener, user_data in self.listeners["progress"]:
            listener(group_val, gr_start_sector, gr_num_sectors, 
                    speed, percent, elapsed_time, left_time, *user_data)
        
    def _on_prepare(self):
        self.timer.start()
    
    def _on_write_begin(self):
        self.sectors_group.reset_group()
        self.write_speed.start()
    
    def _on_write_end(self):
        pass
    
    def _on_compare_begin(self):
        self.sectors_group.reset_group()
        self.read_speed.start()
    
    def _on_compare_end(self):
        self.bads.finalize(self.stop_sector)
    
    def _on_write_progress(self, sector_index, is_ok):
        result = self.sectors_group.add(sector_index, is_ok)
        if result is not None:
            group_val, gr_start_sector, gr_num_sectors = result
            speed = self.write_speed.estimate(sector_index)
            percent = self.percent_done.get_percent_done(sector_index, 1)
            
            elapsed_time, left_time = self.timer.estimate(percent)
            
            self._on_progress(group_val, gr_start_sector, gr_num_sectors, 
                         speed, percent, elapsed_time, left_time)            
        
    
    def _on_compare_progress(self, sector_index, is_ok):
        self.bads.add(sector_index, not is_ok)
        
        result = self.sectors_group.add(sector_index, is_ok)
        if result is not None:
            group_val, gr_start_sector, gr_num_sectors = result
            speed = self.read_speed.estimate(sector_index)
            
            percent = self.percent_done.get_percent_done(sector_index, 2)
            elapsed_time, left_time = self.timer.estimate(percent)
            
            self._on_progress(group_val, gr_start_sector, gr_num_sectors, 
                         speed, percent, elapsed_time, left_time)



         
class DriveTest:
            
    def __init__(self, device, start_sector = 0, stop_sector = -1, update_period = 1000):
        """ 
        device : device to test
        start_sector,  stop_sector
        """
        self.status = STATUS_INIT
        
        self.dev = device
        self.dev_sectors = dsk_opr.num_sectors(self.dev)
        self.dev_sector_size = dsk_opr.sector_size(self.dev)
        
        self._set_start_sector(start_sector)
        self._set_stop_sector(stop_sector) 
        
        print(self.start_sector, self.stop_sector)
        self.handler = EventHandler(update_period, self.dev_sector_size,
                                    self.start_sector, self.stop_sector)
        

        
        
        
        self.num_sectors_test = self.stop_sector - self.start_sector + 1
        
        
    def _set_start_sector(self, start = 0):
        self.start_sector = max(0, min(start, self.dev_sectors - 1))
        
    def _set_stop_sector(self, stop = -1):
        if stop < 0:
            stop += self.dev_sectors
        self.stop_sector = max(self.start_sector, min(stop, self.dev_sectors - 1))   

        
    def _update_status(self, new_status, comment):
        # args may contain some additional information
        if ((self.status != STATUS_CANCELLED) and
            (self.status != STATUS_FINISHED) and
            (self.status != STATUS_ERROR) ):
            
            self.handler._on_status_update(self.status, new_status, comment)           
            self.status = new_status
            return True            
        
        return False

    def test(self):
        self.prepare()
        #self.write()
        self.compare()
        self.finish()

        
    def prepare(self):
        if self._update_status(STATUS_PREPARING, ""):
            try:
                dsk_opr.unmount(self.dev)
            except Exception as e:
                self._update_status(STATUS_ERROR, e)
            finally:
                self.handler._on_prepare()
        
    def write(self):
        if self._update_status(STATUS_WRITING, ""):
            self.handler._on_write_begin()
            try:
                for (ind_, bytes_w) in dsk_opr.write(self.dev, 
                                               self.dev_sector_size,
                                               self.start_sector,
                                               self.num_sectors_test,
                                               data_gen.get_data):
                    
                    if self.is_cancelled():  break
            
                    #number of bytes written == sector size
                    result = (bytes_w == self.dev_sector_size)             
                    self.handler._on_write_progress(ind_, result)
            except Exception as e:
                self._update_status(STATUS_ERROR, e)
            finally:
                self.handler._on_write_end()
           
            
    def compare(self):
        if self._update_status(STATUS_COMPARING, ""):
            self.handler._on_compare_begin()          
            try:                
                for (ind_, data) in dsk_opr.read(self.dev,
                                            self.dev_sector_size,
                                            self.start_sector,
                                            self.num_sectors_test): 
                
                    control_data = data_gen.get_data(ind_, self.dev_sector_size)
                    result = (data == control_data)
                    
                    self.handler._on_compare_progress(ind_, result)            

            except Exception as e:
                self._update_status(STATUS_ERROR, e)
                
            finally:
                self.handler._on_compare_end()
                
    def finish(self):
        self._update_status(STATUS_FINISHED, "")
        self.handler._on_finish(self.is_finished()) 

            
    def cancel(self):
        self._update_status(STATUS_CANCELLED, "Cancelled by user") 
        self.handler._on_cancel(self.is_cancelled)
                
    def is_cancelled(self):
        return self.status == STATUS_CANCELLED
        
    def is_finished(self):
        return self.status == STATUS_FINISHED
        
    def add_callback(self, event, func, *user_data):
        self.handler.add_listener(event, func, *user_data)
        
            

        

        