#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 07:21:56 2016

@author: pavel
"""
import random
from const import BYTE_ORDER, BYTE_BITS, RND_SEED

def get_data(block_number, block_size):
    random.seed(RND_SEED + block_number)
    
    bits = random.getrandbits(BYTE_BITS*block_size)
    return bits.to_bytes(block_size, byteorder=BYTE_ORDER)
    
    