#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  2 16:15:24 2017

@author: pavel
"""
import time

class Percent:
    def __init__(self, init_val, final_val, num_stages):
        self._init_val = init_val
        self._final_val = final_val
        
        self.total_work = (final_val - init_val)*num_stages
        
    def get_percent_done(self, current_val, current_stage):
        return 100.0 * (current_val * current_stage - self._init_val) / self.total_work

class Timer:
    def __init__(self, init_val, final_val):
        self._start_time = time.monotonic()
        
        self._init_val = init_val
        self._final_val = final_val
        self._total_work = final_val - init_val
        
        self._last_time = self._start_time
        
    def start(self):
        self._start_time = time.monotonic()
        
    def estimate(self, current_val):
        self._last_time = time.monotonic()
        elapsed =  self._last_time - self._start_time 
        
        work_done = current_val - self._init_val
        work_left = self._total_work - work_done
        
        estimated_left = elapsed * work_left / work_done
        
        return elapsed, estimated_left
        
    def get_total_time(self):
        return self._last_time - self._start_time
    
        
        
class Speed:
    def __init__(self, block_size, init_block):
        self._start_time = time.monotonic()
        self._last_time = time.monotonic()
        
        self._block_size = block_size #bytes
        self._init_block = init_block
        self._last_block = init_block
        
        self.mean_speed = 0
        
    def start(self):
        self._start_time = time.monotonic()
        self._last_time = self._start_time
        
    def _speed(self, begin_time, current_time, begin_block, current_block):
        if begin_time >= current_time:
            return 0
        return int((current_block - begin_block)/(current_time - begin_time) 
                                                            * self._block_size)
        
    def estimate(self, current_block):
        current_time = time.monotonic()
        
        last_speed = self._speed(self._last_time, current_time,
                                 self._last_block, current_block)
        self.mean_speed = self._speed(self._start_time, current_time,
                                 self._init_block, current_block)
        
        self._last_time = current_time
        self._last_block = current_block
        
        return last_speed
        
    def get_mean_speed(self):
        return self.mean_speed
            

class BadSectors:    
    def __init__(self, start_ind):
        self.start_ind = self.end_ind = start_ind
        
        self.bad_sectors = []        
        
        self.num_sectors = 0
        self.num_bad_sectors = 0
        self.bad_run_start = 0
        self.current_state_bad = False
        
    def add(self, ind, bad_state = False):
        """ indecies should be consequtive 1, 2, 3, 4, ..."""
        self.num_sectors += 1
        
        #good -> good: nothing to do anymore
        
        if (self.current_state_bad) and (bad_state): #bad -> bad
            self.num_bad_sectors += 1
            
        elif (self.current_state_bad) and (not bad_state): #bad -> good
            self.current_state_bad = False
            self.bad_sectors.append((self.bad_run_start, ind -1))
            
        elif (not self.current_state_bad) and (bad_state): # good -> bad
            self.current_state_bad = True
            self.num_bad_sectors += 1
            self.bad_run_start = ind
            
    def finalize(self, ind):
        self.end_ind = ind
        
        if self.current_state_bad:
            self.bad_sectors.append((self.bad_run_start, ind -1))
            self.current_state_bad = False
            
    def get_first_sector(self):
        return self.start_ind
        
    def get_last_sector(self):
        return self.end_ind
            
    def get_first_bad_sector(self):
        if len(self.bad_sectors) > 0:
            return self.bad_sectors[0][0]
            
    def get_last_bad_sector(self):
        if len(self.bad_sectors) > 0:
            return self.bad_sectors[-1][1]
            
    def get_bad_groups(self):
        for bad_run in self.bad_sectors:            
            yield bad_run
        
    def get_good_groups(self):
        if len(self.bad_sectors) == 0:
            yield (self.start_ind, self.end_ind)
        else:
            if self.bad_sectors[0][0] != self.start_ind:
                yield (self.start_ind, self.bad_sectors[0][0] -1)
                
            bad_end = self.bad_sectors[0][1]
            
            for (run_begin, run_end) in self.bad_sectors[1:]:
                yield(bad_end + 1, run_begin - 1)
                bad_end = run_end
                
            if bad_end != self.end_ind:
                yield(bad_end + 1, self.end_ind)                
            
    def get_num_bad_sectors(self):
        return self.num_bad_sectors
        
    def get_num_good_sectors(self):
        return self.num_sectors - self.num_bad_sectors
        
    def get_num_sectors(self):
        return self.num_sectors
        