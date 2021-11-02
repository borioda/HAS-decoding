#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 31st May 2021

@author: 
    Daniele Borio
""" 

import numpy as np
import pandas as pd
import has_decoder as hd
from tqdm import trange 

# load the CNAV data extracted from the Septentrio Rx
filename = '/home/daniele/Documents/Projects/2021/HAS Decoding/input/NORD1660.21/NORD1660.21__SBF_GALRawCNAV.zip'
_type = "txt"

if _type == "txt" :
    # header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType", "NAVBits"]
    header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType", "word 1", \
                   "word 2", "word 3", "word 4", "word 5", "word 6", "word 7", "word 8",\
                   "word 9", "word 10", "word 11", "word 12", "word 13", "word 14",\
                   "word 15", "word 16"]
    
    # Specify the data type
    data_types = {"word 1" : np.uint32, "word 2" : np.uint32, "word 3" : np.uint32,
                  "word 4" : np.uint32, "word 5" : np.uint32, "word 6" : np.uint32,
                  "word 7" : np.uint32, "word 8" : np.uint32, "word 9" : np.uint32,
                  "word 10" : np.uint32, "word 11" : np.uint32, "word 12" : np.uint32,
                  "word 13" : np.uint32, "word 14" : np.uint32, "word 15" : np.uint32,
                  "word 16" : np.uint32}
                   
    df = pd.read_csv(filename, compression='zip', sep=',| ', names=header_list, \
                     engine='python', dtype = data_types)
    
elif _type == "hexa" :
    header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType",\
                   "VITERBI_TYPE","RxChannel","word 1", \
                   "word 2", "word 3", "word 4", "word 5", "word 6", "word 7", "word 8",\
                   "word 9", "word 10", "word 11", "word 12", "word 13", "word 14",\
                   "word 15", "word 16"]
        
    converters = {
        "word 1" : lambda x: int(x, 16),\
        "word 2" : lambda x: int(x, 16),\
        "word 3" : lambda x: int(x, 16),\
        "word 4" : lambda x: int(x, 16),\
        "word 5" : lambda x: int(x, 16),\
        "word 6" : lambda x: int(x, 16),\
        "word 7" : lambda x: int(x, 16),\
        "word 8" : lambda x: int(x, 16),\
        "word 9" : lambda x: int(x, 16),\
        "word 10" : lambda x: int(x, 16),\
        "word 11" : lambda x: int(x, 16),\
        "word 12" : lambda x: int(x, 16),\
        "word 13" : lambda x: int(x, 16),\
        "word 14" : lambda x: int(x, 16),\
        "word 15" : lambda x: int(x, 16),\
        "word 16" : lambda x: int(x, 16)
        }
        
    df = pd.read_csv(filename, compression='zip', sep=',| ', names=header_list, \
                     engine='python', converters = converters)

print("Data loaded ...\n")
    
# Now compute the HAS page type (bits from 14 to 38)
HAS_Header = ( (df["word 1"].values & 0x3FFFF) << 6 ) + \
           (df["word 2"].values >> 26)

# Find non-dummy elements
non_dummy = np.argwhere((HAS_Header != 0xAF3BC3) & (df["CRCPassed"].values == 1)).flatten()

# Select only non-dummy
df_valid = df.iloc[non_dummy].copy()



HAS_Header = HAS_Header[non_dummy]

# Extract valid information from the header
df_valid["HAS_status"] = (HAS_Header >> 22) & 0x3
df_valid["Message_Type"] = ( HAS_Header >> 18 ) & 0x3 
df_valid["Message_ID"] = ( HAS_Header >> 13 ) & 0x1F
df_valid["Message_Size"] = (( HAS_Header >> 8 ) & 0x1F) + 1
df_valid["Page_ID"] = (HAS_Header) & 0xFF

# Allocate the decoder
decoder = hd.has_decoder()

valid_tows = np.unique(df_valid['TOW'])

masks = None

# different files where to save the different corrections
orbit_filename = filename.split('__')[0] + '_has_orb.csv'
clock_filename = filename.split('__')[0] + '_has_clk.csv'
cbias_filename = filename.split('__')[0] + '_has_cb.csv'
pbias_filename = filename.split('__')[0] + '_has_cp.csv'

orbit_file = open(orbit_filename, 'w')
clock_file = open(clock_filename, 'w')
cbias_file = open(cbias_filename, 'w')
pbias_file = open(pbias_filename, 'w')

orbit_header = False
clock_header = False
cbias_header = False
pbias_header = False

for hh in trange(len(valid_tows)) :
    
    tow = valid_tows[hh]
    
    tow_ind = np.argwhere(df_valid['TOW'].values == tow).flatten()
    
    page_block = []
    for ii in tow_ind :
        page = np.array([df_valid["word %d" % kk].iloc[ii] for kk in range(1, 17)], dtype=np.uint32)
        page_block.append(page)
        
    msg_type = df_valid['Message_Type'].iloc[tow_ind[0]]
    msg_id = df_valid['Message_ID'].iloc[tow_ind[0]]
    msg_size = df_valid['Message_Size'].iloc[tow_ind[0]]
    
    msg = decoder.update(tow, page_block, msg_type, msg_id, msg_size)
    masks = None
    
    if msg is not None :
        header = hd.interpret_mt1_header(msg.flatten()[0:4])
        # print(int(tow / 1000) % 3600)
        # print(header)
        
        info = {'ToW' : int(tow / 1000),
                'ToH' : header['TOH'],
                'IOD' : header['IOD Set ID'] }
        
        # Check on timing information
        # if (info['ToW'] % 3600) < info['ToH'] :
        #     print('Invalid ToH')
        #     continue
        
        body = msg.flatten()[4:]
        byte_offset = 0 
        bit_offset = 0
        
        if header["Mask"] == 1 :
            try :
                masks, byte_offset, bit_offset = hd.interpret_mt1_mask(body)
            except :
                continue
            
        if masks is None :
            continue
        
        if header['Orbit Corr'] == 1 :
            try :
                cors, byte_offset, bit_offset = hd.interpret_mt1_orbit_corrections(body,\
                                                byte_offset, bit_offset, masks, info)
            except :
                continue
            
            if len(cors) == 0 :
                continue
            
            # print the corrections to file
            if not orbit_header :
                orbit_file.write(cors[0].get_header() + '\n')
                orbit_header = True
                
            for cor in cors :
                cor_str = cor.__str__() + '\n'
                orbit_file.write(cor_str)
            
        if header['Clock Full-set'] == 1 :
            try :
                cors, byte_offset, bit_offset = hd.interpret_mt1_full_clock_corrections(body,\
                                                byte_offset, bit_offset, masks, info)
            except :
                continue
            
            if len(cors) == 0 :
                continue
            
            # print the corrections to file
            if not clock_header :
                clock_file.write(cors[0].get_header() + '\n')
                clock_header = True
                
            for cor in cors :
                cor_str = cor.__str__() + '\n'
                clock_file.write(cor_str)
            
        if header['Clock Subset'] == 1 :
            # This block needs an "external" mask 
            if masks is not None :
                try :
                    cors, byte_offset, bit_offset = hd.interpret_mt1_subset_clock_corrections(body,\
                                                byte_offset, bit_offset, masks, info)
                except :
                    continue
                
                if len(cors) == 0 :
                    continue
                
                # print the corrections to file
                if not clock_header :
                    clock_file.write(cors[0].get_header() + '\n')
                    clock_header = True

                for cor in cors :
                    cor_str = cor.__str__() + '\n'
                    clock_file.write(cor_str) 

        if header['Code Bias'] == 1 :
            try :
                cors, byte_offset, bit_offset = hd.interpret_mt1_code_biases(body,\
                                            byte_offset, bit_offset, masks, info)
            except :
                continue
            
            if len(cors) == 0 :
                continue
            
            # print the corrections to file
            if not cbias_header :
                cbias_file.write(cors[0].get_header() + '\n')
                cbias_header = True
                
            for cor in cors :
                cor_str = cor.__str__() + '\n'
                cbias_file.write(cor_str)
            
        if header['Phase Bias'] == 1 :
            try:
                cors, byte_offset, bit_offset = hd.interpret_mt1_phase_biases(body,\
                                            byte_offset, bit_offset, masks, info)
            except:
                continue
            
            if len(cors) == 0 :
                continue
            
            # print the corrections to file
            if not pbias_header :
                pbias_file.write(cors[0].get_header() + '\n')
                pbias_header = True
                
            for cor in cors :
                cor_str = cor.__str__() + '\n'
                pbias_file.write(cor_str)
                
orbit_file.close()
clock_file.close()
cbias_file.close()
pbias_file.close()