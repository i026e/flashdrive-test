#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 15:32:22 2016

@author: pavel
"""
from datetime import datetime
import disk_operations as dsk_opr

from utils import safe_get, pretty_disk_size, pretty_time_diff, pretty_speed

template = """
REPORT
----------------------------------------
Test of {device}
Date: {date}

Declared capacity: {pretty_capacity} ({capacity} bytes)
Number of sectors: {num_sectors}
Sector size: {sec_size} bytes

Result of testing sectors {start} - {end}
----------------------------------------
Number of tested sectors: {num_tested}
Tested size: {size_tested} bytes
Time elapsed: {elp_time}

Average writing rate: {w_speed}
Average readind rate: {r_speed}

Number of bad sectors: {bad_num}
First bad sector position: {first_bad}
Last bad sector position: {last_bad}

Available space at the beginning: {beg_space} bytes
Available space at the end: {end_space} bytes
Total available space: {tot_av_space} bytes

----------------------------------------

Bad sectors: 
{bad_list}
----------------------------------------
"""

def report_generator(device, bad_sectors, write_speed, read_speed, timer):
    sector_size = safe_get(dsk_opr.sector_size, 0, device)
    capacity = safe_get(dsk_opr.size, 0, device)
    pretty_capacity = pretty_disk_size(capacity)
    
    num_sectors = safe_get(dsk_opr.num_sectors, 0, device)
    date = str(safe_get(datetime.now, 0))
    
    start = bad_sectors.get_first_sector()
    end = bad_sectors.get_last_sector()
    
    num_tested = bad_sectors.get_num_sectors()
    size_tested = num_tested*sector_size
    
    elp_time = pretty_time_diff(timer.get_total_time())
    w_speed = pretty_speed(write_speed.get_mean_speed())
    r_speed = pretty_speed(read_speed.get_mean_speed())    
    
    bad_num = bad_sectors.get_num_bad_sectors()
    good_num = bad_sectors.get_num_good_sectors()
    first_bad = bad_sectors.get_first_bad_sector()
    last_bad = bad_sectors.get_last_bad_sector()
    
    good_space = good_num * sector_size

    begin_space = good_space if first_bad is None else (first_bad - start) * sector_size
    end_space = 0 if last_bad is None else (end - last_bad) * sector_size
    
    bad_list = "\n".join(str(gr) for gr in bad_sectors.get_bad_groups())
    
    report = template.format(device = device,
                             capacity = capacity,
                             pretty_capacity = pretty_capacity,
                             num_sectors = num_sectors,
                             sec_size = sector_size,
                             date = date,
                             start = start,
                             end = end,
                             num_tested = num_tested,
                             size_tested = size_tested,
                             elp_time = elp_time,
                             w_speed = w_speed,
                             r_speed = r_speed,
                             bad_num = bad_num,
                             first_bad = first_bad,
                             last_bad = last_bad,
                             beg_space = begin_space,
                             end_space = end_space,
                             tot_av_space = good_space,
                             bad_list = bad_list )
    
    return report

