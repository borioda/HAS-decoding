#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 08:54:47 2021

@author: daniele
"""

import has_message as hm
import has_corrections as hc
import numpy as np

class has_decoder :
    """
    Summary :
        Class implementing the decoder for the HAS message
    """
    
    # static variable
    LIMIT_AGE = 120
    
    def __init__(self) :
        """
        Summary :
            Object constructor.
            
        Arguments:
            
        Returns:
        """
        # list of HAS messages
        self.message_list =[]
        
    def update(self, tow, sep_pages, msg_type, msg_id, msg_size) :
        """
        Summary :
            Update the decoder using blocks of pages in the format provided by the 
            Septentrio receiver. All the pages are from the same epoch.
            
        Arguments:
            tow - time of week
            sep_page - block of pages with the same TOW. Each page is an array 
                       with 16 32-bit integers representing the HAS message
            msg_type - message type
            msg_id - messge id 
            msg_size - message size
            
        Returns:
            Nothing.
        """
        has_message = False
        decoded_msg = None 
        
        for message in self.message_list :
            
            # check if this is the correct message 
            if message.is_message(msg_type, msg_id, msg_size) :
               has_message = True
               
               # update the message
               for page in sep_pages :
                   message.add_page_sep_bytes(page)
                                 
            # This is not the correct message
            else :
                # increase the age of the message
                message.increase_age()
                
        # if the message was not present add it to the list
        if not has_message :
            message = hm.has_message(msg_type, msg_id, msg_size)
            
            # update the message
            for page in sep_pages :
                message.add_page_sep_bytes(page)
                
            # add it to the decoder list
            self.message_list.append(message)
            
        # Do some clean up
        for message in self.message_list :
        
            decoded_msg = None 
            
            # if the message is old, remove it
            if message.is_old(self.LIMIT_AGE) :
                self.message_list.remove(message)
            
            # if the message is complete, decode it and remove it from the list
            elif message.complete() :
                decoded_msg = message.decode()
                self.message_list.remove(message)
            
        # The actual decoding should be performed here
        if decoded_msg is not None :
            pass
        
        return decoded_msg
    
def interpret_mt1_header( header ) :
    """
    Summary:
        Interpret the header (32 bits) of a MT1 message
        
    Arguments:
        header - 4 bytes of the message header
        
    Returns:
        header_content - dictionary with the decoded header
    """
    # Time of Hour
    ToH = (int(header[0]) << 4) + (int(header[1] ) >> 4)
    
    # Mask ID
    maskID = ((int(header[2]) & 0x3) << 3) + (int(header[3] ) >> 5)
    
    # IOD Set ID
    iodID = int(header[3]) & 0x1F
    
    header_content = {"TOH" : ToH, 
                      "Mask" : ( int(header[1] ) >> 3 ) & 0x1,
                      "Orbit Corr" : ( int(header[1] ) >> 2 ) & 0x1,
                      "Clock Full-set" : ( int(header[1] ) >> 1 ) & 0x1,
                      "Clock Subset" : int(header[1]) & 0x1,
                      "Code Bias" : ( int(header[2] ) >> 7 ) & 0x1,
                      "Phase Bias" : ( int(header[2] ) >> 6 ) & 0x1,
                      "Mask ID" : maskID,
                      "IOD Set ID" : iodID
                      }
    
    return header_content

###############################################################################
    
def interpret_mt1_mask(body, byte_offset = 0, bit_offset = 0) :
    """
    Summary:
        Interpret the body of a MT1 HAS message as a "Mask"
        
    Arguments:
        body - array of bytes
        
    Returns:
        masks - the interpreted satellite masks
    """
    
    # Determine the number of system supported
    Nsys, byte_offset, bit_offset = hc.get_bits( body, byte_offset, bit_offset, 4 ) 
    
    masks = []
    
    # interpret the first mask
    for ii in range(Nsys) :
        
        # create a new mask
        mask = hc.has_mask()
        byte_offset, bit_offset = mask.interpret_mask(body, byte_offset, bit_offset)
         
        masks.append(mask)
        
    return masks, byte_offset, bit_offset

# validity intervals as specified by Table 13 of the ICD
validity_t13 = [5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1800, 3600, -1]
    
def interpret_mt1_orbit_corrections(body, byte_offset, bit_offset, masks, info = None) :
    """
    Summary:
        Interpret the body of a MT1 HAS message as orbit corrections
        
    Arguments:
        body - array of bytes
        byte_offset - the byte offset in body
        bit_offset - the bit offset in body
        masks - list of mask indicating how to interpret the orbit corrections
    
    Returns:
        orbit corrections - list of orbit corrections
        byte_offset - the new byte offset in body
        bit_offset - the new bit offset in body
    """
    
    if info is not None :
        tow = info['ToW']
        toh = info['ToH']
        IOD = info['IOD']
    else:
        tow = -1
        toh = -1
        IOD = -1
        
    orbit_corrections = []
    
    # first get the validity index
    vi_index, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)

    # convert the the validity index in a validity interval (Table 13 of ICD)
    validity = validity_t13[vi_index]
    
    for mask in masks :
        # get the gnss ID        
        gnss = mask.gnss_ID

        # for each satellite in the mask, get an orbit correction        
        for prn in mask.prns :
            # creat the orbit correction
            orbit_cor = hc.has_orbit_correction(gnss, prn, validity, tow, toh, IOD) 
            
            # interpret the message
            byte_offset, bit_offset = orbit_cor.interpret(body, byte_offset, bit_offset)
            
            # add the correction to the list
            orbit_corrections.append(orbit_cor)
        
    return orbit_corrections, byte_offset, bit_offset          

def interpret_mt1_full_clock_corrections(body, byte_offset, bit_offset, masks, info = None) :
    """
    Summary:
        Interpret the body of a MT1 HAS message as clock full-set corrections
        
    Arguments:
        body - array of bytes
        byte_offset - the byte offset in body
        bit_offset - the bit offset in body
        masks - list of mask indicating how to interpret the orbit corrections
    
    Returns:
        full_clock_corr - list of clock corrections
        byte_offset - the new byte offset in body
        bit_offset - the new bit offset in body
    """
    if info is not None :
        tow = info['ToW']
        toh = info['ToH']
        IOD = info['IOD']
    else:
        tow = -1
        toh = -1
        IOD = -1
        
    clock_cors = []
    
    # first get the validity index
    vi_index, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)

    # convert the the validity index in a validity interval (Table 13 of ICD)
    validity = validity_t13[vi_index]

    # ...then get the system multiplier
    sys_mul = np.zeros(len(masks))

    for ii in range(len(masks)) :
        sys_mul[ii], byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 2)
    
    sys_mul += 1
    
    # now get the clock corrections
    ii = 0
    for mask in masks :
        # get the gnss ID        
        gnss = mask.gnss_ID

        # for each satellite in the mask, get a clock full-set correction        
        for prn in mask.prns :
            # creat the orbit correction
            clock_cor = hc.has_clock_corr(gnss, prn, validity, sys_mul[ii], tow, toh, IOD) 
            
            # interpret the message
            byte_offset, bit_offset = clock_cor.interpret(body, byte_offset, bit_offset)
            
            # add the correction to the list
            clock_cors.append(clock_cor)
        
    return clock_cors, byte_offset, bit_offset

def interpret_mt1_subset_clock_corrections(body, byte_offset, bit_offset, masks, info = None) :
    """
    Summary:
        Interpret the body of a MT1 HAS message as clock full-set corrections
        
    Arguments:
        body - array of bytes
        byte_offset - the byte offset in body
        bit_offset - the bit offset in body
        masks - list of mask indicating how to interpret the orbit corrections
    
    Returns:
        full_clock_corr - list of clock corrections
        byte_offset - the new byte offset in body
        bit_offset - the new bit offset in body
    """
    if info is not None :
        tow = info['ToW']
        toh = info['ToH']
        IOD = info['IOD']
    else:
        tow = -1
        toh = -1
        IOD = -1
        
    clock_cors = []
    
    # first get the validity index
    vi_index, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)

    # convert the the validity index in a validity interval (Table 13 of ICD)
    validity = validity_t13[vi_index]
    
    # then get the actual number of GNSSs
    Nsys, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)
    
    # loop over the different GNSS
    for ii in range(Nsys) :
        
        # get the GNSS ID
        gnssID, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)
      
        # find the related mask
        for mask in masks :
            if mask.gnss_ID == gnssID :
                break
            
        signals = mask.prns
        Nsig = len(signals)
      
        # get the system multiplier
        sys_mul, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 2)
        sys_mul += 1
        
        # get the signal mask
        sig_mask, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, Nsig)
        sig_mask = bin(sig_mask)[2:].zfill(Nsig)
        
        # loop over the different signals
        for kk in range(len(signals)) :
            
            if sig_mask[kk] == '1' :
                
                # creat the orbit correction
                clock_cor = hc.has_clock_corr(gnssID, signals[kk], validity, sys_mul, tow, toh, IOD ) 
            
                # interpret the message
                byte_offset, bit_offset = clock_cor.interpret(body, byte_offset, bit_offset)
            
                # add the correction to the list
                clock_cors.append(clock_cor)    
        # end loop on the different signals
    # end loop on the different GNSS
    return clock_cors, byte_offset, bit_offset
        
def interpret_mt1_code_biases(body, byte_offset, bit_offset, masks, info = None ) :
    
    if info is not None :
        tow = info['ToW']
        toh = info['ToH']
        IOD = info['IOD']
    else:
        tow = -1
        toh = -1
        IOD = -1
    
    code_biases = []
    
    # first get the validity index
    vi_index, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)

    # convert the the validity index in a validity interval (Table 13 of ICD)
    validity = validity_t13[vi_index]

    # loop over the different masks
    for mask in masks :
        gnss_id = mask.gnss_ID
                
        # loop over the differnt PRNs
        for ii in range(len(mask.prns)) :
            
            prn = mask.prns[ii]
            
            # determine the number of biases/signals
            if mask.cell_mask_flag == 0 :
                signals = mask.signals
            else :
                signals = []
                signal_mask = bin(self.cell_mask[ii])[2:]
                
                for kk in range(len(mask.signals)) :
                    if signal_mask[-kk-1] == '1' :
                        signals.append(mask.signals[kk])
            
            # Now create the new bias
            cbias = hc.has_code_bias(gnss_id, prn, validity, signals, tow, toh, IOD)
            
            # ... and interpret the message 
            byte_offset, bit_offset = cbias.interpret(body, byte_offset, bit_offset)
            
            code_biases.append(cbias)
        # end loop on the prns
    #end loop on the GNSS
    
    return code_biases, byte_offset, bit_offset

def interpret_mt1_phase_biases(body, byte_offset, bit_offset, masks, info = None) :
    
    if info is not None :
        tow = info['ToW']
        toh = info['ToH']
        IOD = info['IOD']
    else:
        tow = -1
        toh = -1
        IOD = -1
    
    phase_biases = []
    
    # first get the validity index
    vi_index, byte_offset, bit_offset = hc.get_bits(body, byte_offset, bit_offset, 4)

    # convert the the validity index in a validity interval (Table 13 of ICD)
    validity = validity_t13[vi_index]

    # loop over the different masks
    for mask in masks :
        gnss_id = mask.gnss_ID
                
        # loop over the differnt PRNs
        for ii in range(len(mask.prns)) :
            
            prn = mask.prns[ii]
            
            # determine the number of biases/signals
            if mask.cell_mask_flag == 0 :
                signals = mask.signals
            else :
                signals = []
                signal_mask = bin(self.cell_mask[ii])[2:]
                
                for kk in range(len(mask.signals)) :
                    if signal_mask[-kk-1] == '1' :
                        signals.append(mask.signals[kk])
            
            # Now create the new bias
            pbias = hc.has_phase_bias(gnss_id, prn, validity, signals, tow, toh, IOD)
            
            # ... and interpret the message 
            byte_offset, bit_offset = pbias.interpret(body, byte_offset, bit_offset)
            
            phase_biases.append(pbias)
        # end loop on the prns
    #end loop on the GNSS
    
    return phase_biases, byte_offset, bit_offset    
    