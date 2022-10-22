#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 31st May 2021

@author: 
    Daniele Borio
""" 

import numpy as np
import data_loading as dl
import has_decoder as hd

# Import the right library depending on the environment
import sys
if 'ipykernel_launcher.py' in sys.argv[0] :
    from tqdm.notebook import tqdm
else :
    from tqdm import tqdm 
    
def parse_data( filename, _rx, _type = None, _page_offset = 1) :
    
    """
    Summary :
        Main function performing the actual parsing.
        It calls several objects in carge of the different operations.
        
    Arguments:
        filename - string specifying the path name of the file to be parsed
        _rx - specify the receiver used to generate the input file. The following
              options are currently supported:
                  
                  sep - Septentrio receiver
                  nov - Novatel GALCNAVRAWPAGE - ASCII format
                  jav - Javad ED message
                  
        _type - in the case of a Septentrio receiver, different input data formats can
                be used. In particular, Binary SBF files are first parsed to 
                extract the Galileo CNAV message. Depending on the parser version,
                hexadecimal or decimal data input can be found.
                The options supported are:
                    hexa - hexadecimal format
                    txt - decimal format
                  
        _page_offset - during the initial HAS test phase, page numbering was starting from 1, now
                     it is starting from 0. The page offset allows one to account for this 
                     convention. It should be set to 1 unless data from the very initial test phase 
                     are used.                  
    """    
    print("Process started")
    
    if _rx == "sep" :
        df = dl.load_from_parsed_Septentrio(filename, _type)
    
    elif _rx == "nov" :
        df = dl.load_from_Novatel(filename)
        
    elif _rx == "jav" :
        df = dl.load_from_Javad(filename)
        
    else :
        raise Exception("Unsupported Receiver format")
            
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
    decoder = hd.has_decoder(_page_offset)
    
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
    
    # Masks have to be propagated between different loops
    masks = None
    
    for hh in tqdm(range(len(valid_tows))) :
        
        tow = valid_tows[hh]
        
        tow_ind = np.argwhere(df_valid['TOW'].values == tow).flatten()
        
        
        page_block = []
        for ii in tow_ind :
            page = np.array([df_valid["word %d" % kk].iloc[ii] for kk in range(1, 17)], dtype=np.uint32)
            page_block.append(page)
            
        msg_type = df_valid['Message_Type'].iloc[tow_ind[0]]
        msg_id = df_valid['Message_ID'].iloc[tow_ind[0]]
        msg_size = df_valid['Message_Size'].iloc[tow_ind[0]]
        
        # also get the week number
        week = df_valid['WNc [w]'].iloc[tow_ind[0]]
        
        msg = decoder.update(tow, page_block, msg_type, msg_id, msg_size)
        
        
        if msg is not None :
            header = decoder.interpret_mt1_header(msg.flatten()[0:4])
            
            info = {'ToW' : int(tow),
                    'WN' : week,
                    'ToH' : header['TOH'],
                    'IOD' : header['IOD Set ID']}
            # Check on timing information
            # if (info['ToW'] % 3600) < info['ToH'] :
            #     print('Invalid ToH')
            #     continue
            
            body = msg.flatten()[4:]
            byte_offset = 0 
            bit_offset = 0
            
            if header["Mask"] == 1 :
                try :
                    masks, byte_offset, bit_offset = decoder.interpret_mt1_mask(body)
                except :
                    continue
                
            if masks is None :
                continue
            
            if header['Orbit Corr'] == 1 :
                try :
                    cors, byte_offset, bit_offset = decoder.interpret_mt1_orbit_corrections(body,\
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
                    cors, byte_offset, bit_offset = decoder.interpret_mt1_full_clock_corrections(body,\
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
                        cors, byte_offset, bit_offset = decoder.interpret_mt1_subset_clock_corrections(body,\
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
                    cors, byte_offset, bit_offset = decoder.interpret_mt1_code_biases(body,\
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
                    if cor.is_empty() :
                        continue
                    
                    cor_str = cor.__str__() + '\n'
                    cbias_file.write(cor_str)
                
            if header['Phase Bias'] == 1 :
                try:
                    cors, byte_offset, bit_offset = decoder.interpret_mt1_phase_biases(body,\
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
                    if cor.is_empty() :
                        continue
                    
                    cor_str = cor.__str__() + '\n'
                    pbias_file.write(cor_str)
                    
    orbit_file.close()
    clock_file.close()
    cbias_file.close()
    pbias_file.close()

    
if __name__ == "__main__":
    
    # Set the input file name
    filename = "/media/daniele/Elements/Projects/2022/HAS/has/data 29Sep/220929_000030_javad_Delta3.jps"

    # Receiver options
    # _rx = "sep"
    # _rx = "jav"
    _rx = "jav"

    
    # If Septentrio is selected, different options are supported 
    # depending on the Septentrio parser
    
    # Not relevant for other receivers
    _type = "hexa"
    
    # Should always be set to 1
    _page_offset = 1
    
    # Finally parse the data    
    parse_data( filename, _rx, _type, _page_offset )
    
