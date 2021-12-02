#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 20 11:38:28 2021

@author: daniele
"""

import abc
import numpy as np


def get_bits(body, byte_offset, bit_offset, num_bits) :
    """
    Summary:
        Function that extracts a sequence of bits from a stream of elements 
        of GF(2^8)
        
    Arguments:
        body - stream of GF(2^8) elements
        byte_offset - the byte offset in the stream
        bit_offset - the bit offset in the stream
        num_bits - number of bits to extract
        
    Returns:
        val - the return value
        byte_offset - the new byte offset
        bit_offset - the new bit offset        
    """
    
    # first understand the return type
    if num_bits < 9 :
        val = np.uint8(0)
    elif num_bits > 8 and num_bits < 17 :
        val = np.uint16(0)
    elif num_bits > 16 and num_bits < 33 :
        val = np.uint32(0)
    elif num_bits > 32 and num_bits < 65 :
        val = np.uint64(0)
    else :
        # not supported type
        return None

    # bit masks
    bit_masks = [0x0, 0x1, 0x3, 0x7, 0xF, 0x1F, 0x3F, 0x7F, 0xFF]
    
    # number of bits in current byte
    rem_bits = int(num_bits)
    
    while rem_bits != 0 :
        # Number of bits in the current byte
        bits_in_byte = int(min([rem_bits, 8 - bit_offset]))
        
        # extract the new bits
        new_bits = np.uint8(body[byte_offset]) >> (8 - bit_offset - bits_in_byte)
        new_bits &= bit_masks[bits_in_byte]
        
        # add them to the return value
        val <<= type(val)(bits_in_byte)
        val += type(val)(new_bits)

        # New bit offset
        bit_offset = (bit_offset + bits_in_byte) % 8
        
        # New byte offset
        if bit_offset == 0 :
            byte_offset += 1

        rem_bits -= bits_in_byte

    return val, byte_offset, bit_offset   

def two_complement( val, nbits) :
    """
    Summary :
        Interpret an unsigned value (val) as a two's complement number.
        
    Arguments :
        val - the value to be interpreted as two's complement
        nbits - number of bits to consider for the evaluation of the complement.
        
    Returns:
        retval - the two's complement of val.
    """
    
    # if it is a negative number
    if (val >> type(val)(nbits - 1)) & 0x1 == 1 :
        retval = val - 2**nbits 
    else:
        retval = val
    
    return retval

###############################################################################
class has_mask :
    """
        System and signal mask
    """
    gal_signals = ["E1-B", "E1-C", "E1-B+E1-C", "E5a-I", "E5a-Q", "E5a-I+E5a-Q",\
                   "E5b-I", "E5b-Q", "E5b-I+E5b-Q","E5-I", "E5-Q", "E5-I+E5-Q",\
                   "E6-B", "E6-C", "E6-B+E6-C", "Reserved"]    
                   
    gps_signals = ["L1 C/A", "Reserved", "Reserved", "L1C(D)", "L1C(P)", "L1C(D+P)", \
                   "L2C(M)", "L2C(L)", "L2C(M+L)", "L2P", "Reserved", "L5-I", "L5-Q", \
                   "L5-I + L5-Q", "Reserved", "Reserved"]    
    
    def __init__(self) :
        # The GNSS ID
        # Two values are supported
        #   0 - GPS
        #   1 - Reserved
        #   2 - Galileo
        #   3-15 - Reserved
        
        self.gnss_ID = np.uint8(0)
        
        # Satellites corrected
        # list of PRNs indicating which satellites are corrected 
        # To be extracted from the satellite mask (40 bits)
        self.prns = []
        
        # Signals for which corrections are available
        # To be extracted from the signal mask (16 bits)
        self.signals = []
        
        # Cell mask
        self.cell_mask_flag = 0
        self.cell_mask = []
        
        # Nav message
        # 0 - I/NAV for GAL or LNAV for GPS
        # 1-7 - Reserved
        self.nav_message = np.uint8(0)

    def interpret_mask(self, body, byte_offset, bit_offset) :
        
        # get the GNSS ID
        self.gnss_ID, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, 4 ) 
        
        # Satellite mask
        satmask, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, 40 )

        # Convert it into a list of PRNs
        satmask = format(satmask, '040b')
        for jj in range(len(satmask)) :
            if satmask[jj] == '1' :
                self.prns.append(jj + 1)
                    
        # Signal mask
        sigmask, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, 16 )
        
        # Convert it into a list of signals
        sigmask = format(sigmask, '016b')
        for jj in range(len(sigmask)) :
            if sigmask[jj] == '1' :
                self.signals.append(jj + 1)
                
        # Cell mask flag
        self.cell_mask_flag, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, 1 )
        
        # Extract the cell mask if available
        if self.cell_mask_flag == 1 :
            Nsat = len(self.prns) # Number of satellites
            Nsig = len(self.signals) # Number of signals per satellite

            # For each satellite record the signal mask
            for ii in range(Nsat) :
                cell_mask, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, Nsig )
                self.cell_mask.append(cell_mask.copy())
            
        # get the nav message corrected in the orbits
        self.nav_message, byte_offset, bit_offset = get_bits( body, byte_offset, bit_offset, 3 )
    
        return byte_offset, bit_offset

###############################################################################
class has_correction(metaclass = abc.ABCMeta) :
    """
    Summary :
        Parent class defining the basic properties of a HAS correction.
        This is an abstract class, which defines basic interfaces
    """
    def __init__(self, gnss_ID, prn, validity, tow = -1, toh = -1, IOD = -1) :
        """
        Summary :
            Object constructor.
            
        Arguments :
            gnss_ID - identifier defining the GNSS of the correction
            prn - satellite identifier
            validity - validity of the correction in seconds
            tow - time of week (extracted from the navigation message) in seconds
            toh - time of hour extracted from the HAS header in seconds
            IOD - Issue of Data extracted from the HAS header
            
        Returns:
            The correction object.
        """
        # GNSS ID
        self.gnss_ID = gnss_ID
        
        # Satellite PRN
        self.prn = prn
        
        # Validity interval
        self.validity = validity

        # time of week
        self.tow = tow

        # time of hour
        self.toh = toh
        
        # issue of data
        self.IOD = IOD
    
    @abc.abstractmethod
    def interpret(self, body, byte_offset, bit_offset) :
        """
        Summary :
            Abstract method defining how to interpret the body of the has message
            and use it to fill the different parts of the correction.
            
        Arguments :
            body - array of bytes
            byte_offset - the byte offset in body
            bit_offset - the bit offset in body
        
        Returns:
            byte_offset - the new byte offset in body
            bit_offset - the new bit offset in body
        """
        pass
    
    def __str__(self) :
        """
        Summary :
           Build a string representation of the object.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the content of the object
        """
        out_str = str(self.tow) + ',' +  str(self.toh) + ',' + str(self.IOD) + \
                 ',' + str(self.validity) + ',' + str(self.gnss_ID) + ',' + str(self.prn)
        
        return out_str
    
    def get_header(self) :
        """
        Summary :
           Build the string describing the attributes in the class __str__() 
           method.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the attributes of __str__()
        """
        return "ToW,ToH,IOD,validity,gnssID,PRN"

class has_orbit_correction(has_correction) :
    """
        HAS orbit corrections        
    """
    
    def __init__(self, gnss_ID, prn, validity, tow = -1, toh = -1, IOD = -1) :
        """
        Summary :
            Object constructor for the orbit correction
                
        Arguments :
            gnss_ID - identifier defining the GNSS of the correction
            prn - satellite identifier
            validity - validity of the correction in seconds
            tow - time of week (extracted from the navigation message) in seconds
            toh - time of hour extracted from the HAS header in seconds
            IOD - Issue of Data extracted from the HAS header
            
        Returns:
            The correction object. 
        """
        
        # Initialize the parent class
        super().__init__(gnss_ID, prn, validity, tow, toh, IOD)
        
        # GNSS IOD - This is a system related parameter and should not be confused
        # with the correction IOD
        self.gnss_IOD = 0

        # Radial correction
        self.delta_radial = 0
        
        # In-track correction
        self.delta_in_track = 0
        
        # Delta Cross-Track
        self.delta_cross_track = 0
        
    def interpret(self, body, byte_offset, bit_offset ) :
        """
        Summary :
            Actual implementation of the  method defining how to interpret the 
            body of the has message and use it to fill the different parts of 
            the correction.
            
        Arguments :
            body - array of bytes
            byte_offset - the byte offset in body
            bit_offset - the bit offset in body
        
        Returns:
            byte_offset - the new byte offset in body
            bit_offset - the new bit offset in body
        """        
        
        # get the GNSS IOD - the related number of bits depends on the type of GNSS
        if self.gnss_ID == 0 :  
            # GPS
            num_bits = 8
        
        elif self.gnss_ID == 2 :
            # Galileo
            num_bits = 10
        else :
            raise Exception("Unsupported GNSS")
        
        # GNSS IOD
        self.gnss_IOD, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, num_bits)
        
        # Delta Radial
        # "b1000000000000" indicates data not available.
        delta, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 13)
        
        if delta == 4096 :
            self.delta_radial = np.nan
        else :
            self.delta_radial = two_complement(delta, 13) * 0.0025
            
        # Delta In-Track
        # "b100000000000" indicates data not available.
        delta, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 12)
        
        if delta == 2048 :
            self.delta_in_track = np.nan
        else :
            self.delta_in_track = two_complement(delta, 12) * 0.008
            
        # Delta Cross-Track
        # "b100000000000" indicates data not available.
        delta, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 12)
        
        if delta == 2048 :
            self.delta_cross_track = np.nan
        else :
            self.delta_cross_track = two_complement(delta, 12) * 0.008
            
        return byte_offset, bit_offset

    def __str__(self) :
        """
        Summary :
           Build a string representation of the object.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the content of the object
        """
        out_str = super().__str__() + ',' + str(self.gnss_IOD) + ',' + \
                  str(self.delta_radial) + ',' + str(self.delta_in_track) + \
                  ',' + str(self.delta_cross_track)
                  
        return out_str
    
    def get_header(self) :
        """
        Summary :
           Build the string describing the attributes in the class __str__() 
           method.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the attributes of __str__()
        """
        out_str = super().get_header() + ',gnssIOD,delta_radial,' +\
                  'delta_in_track,delta_cross_track'
                  
        return out_str
        
class has_clock_corr(has_correction) :
    """
        Clock orbit corrections        
    """
    def __init__(self, gnss_ID, prn, validity, sys_mul, tow = -1, toh = -1, IOD = -1) :
        """
        Summary :
            Object constructor for the clock correction
                
        Arguments :
            gnss_ID - identifier defining the GNSS of the correction
            prn - satellite identifier
            validity - validity of the correction in seconds
            tow - time of week (extracted from the navigation message) in seconds
            toh - time of hour extracted from the HAS header in seconds
            IOD - Issue of Data extracted from the HAS header
            sys_mul - multiplier at the GNSS level for the clock C0 correction

        Returns:
            The correction object. 
        """
        # Initialize the parent class
        super().__init__(gnss_ID, prn, validity, tow, toh, IOD)
                
        # Multiplier for all Delta Clock C0 corrections
        self.multiplier = sys_mul
        
        # Delta Clock C0
        self.delta_clock_c0 = 0
        
        # status 0 - OK, 1 - not available, 2 - shall not be used
        self.status = 0
        
    def interpret(self, body, byte_offset, bit_offset) :
        """
        Summary :
            Actual implementation of the  method defining how to interpret the 
            body of the has message and use it to fill the different parts of 
            the correction.
            
        Arguments :
            body - array of bytes
            byte_offset - the byte offset in body
            bit_offset - the bit offset in body
        
        Returns:
            byte_offset - the new byte offset in body
            bit_offset - the new bit offset in body
        """  
        # Delta Clock C0
        # "b1000000000000" indicates data not available
        # "b0111111111111" indicates the satellite shall not be used.
        delta, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 13)
        
        if delta == 4096 :
            self.status = 1
        elif delta == 4095 :
            self.status = 2
        else :
            self.delta_clock_c0 = two_complement(delta, 13) * 0.0025
            
        return byte_offset, bit_offset

    def __str__(self) :
        """
        Summary :
           Build a string representation of the object.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the content of the object
        """
        out_str = super().__str__() + ',' + str(self.multiplier) + ',' + \
                  str(self.delta_clock_c0) + ',' + str(self.status)
                  
        return out_str

    def get_header(self) :
        """
        Summary :
           Build the string describing the attributes in the class __str__() 
           method.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the attributes of __str__()
        """
        out_str = super().get_header() + ',multiplier,delta_clock_c0,' + \
                  'status'
        
        return out_str
                  
class has_code_bias(has_correction) :
    """
        HAS code bias corrections.
    """
    def __init__(self, gnss_ID, prn, validity, signals, tow = -1, toh = -1, IOD = -1) :
        """
        Summary :
            Object constructor for the clock correction
                
        Arguments :
            gnss_ID - identifier defining the GNSS of the correction
            prn - satellite identifier
            validity - validity of the correction in seconds
            tow - time of week (extracted from the navigation message) in seconds
            toh - time of hour extracted from the HAS header in seconds
            IOD - Issue of Data extracted from the HAS header
            signals - list of signals for which code biases are available

        Returns:
            The correction object. 
        """
        
        # Initialize the parent class
        super().__init__(gnss_ID, prn, validity, tow, toh, IOD)
        
        # List of supported signals
        self.signals = signals

        # Code biases        
        self.biases = np.zeros(len(signals))
            
        # Availability flags related to the code biases
        self.availability_flags = np.ones(len(signals))
            
    def interpret(self, body, byte_offset, bit_offset) :
        """
        Summary :
            Actual implementation of the  method defining how to interpret the 
            body of the has message and use it to fill the different parts of 
            the correction.
            
        Arguments :
            body - array of bytes
            byte_offset - the byte offset in body
            bit_offset - the bit offset in body
        
        Returns:
            byte_offset - the new byte offset in body
            bit_offset - the new bit offset in body
        """ 
        
        for ii in range(len(self.signals)) :
        
            bias, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 11)
            
            if bias == 1024 :
                self.availability_flags[ii] = 0
            else :
                self.biases[ii] = two_complement(bias, 11) * 0.02
                
        return byte_offset, bit_offset
    
    def is_empty(self) :
        """
        Summary:
            Check if the correction contains actual data or if it is empty.
            
        Arguments:
            None.
            
        Returns:
            True if there are no corrections available.
        """
        if len(self.signals) == 0 :
            return True
        
        if len(self.biases) == 0 :
            return True
        
        return False
    
    def __str__(self) :
        """
        Summary :
           Build a string representation of the object.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the content of the object
        """
        out_str = ""
        
        if self.is_empty() :
            return out_str
        
        for ii in range(len(self.signals) - 1) :
            
            sig_str = super().__str__() + ',' + str(self.signals[ii]) + \
                      ',' + str(self.biases[ii]) + ',' + \
                      str(self.availability_flags[ii]) + '\n' 
            
            out_str = out_str + sig_str
            
        # Add the last one with return carriage
        sig_str = super().__str__() + ',' + str(self.signals[-1]) + \
                ',' + str(self.biases[-1]) + ',' + str(self.availability_flags[-1])

        out_str = out_str + sig_str
        
        return out_str

    def get_header(self) :
        """
        Summary :
           Build the string describing the attributes in the class __str__() 
           method.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the attributes of __str__()
        """
        out_str = super().get_header() + ',signal,code_bias,av_flag'
        
        return out_str
    
class has_phase_bias(has_correction) :
    """
        HAS carrier phase corrections.
    """
    def __init__(self, gnss_ID, prn, validity, signals, tow = -1, toh = -1, IOD = -1) :
        """
        Summary :
            Object constructor for the clock correction
                
        Arguments :
            gnss_ID - identifier defining the GNSS of the correction
            prn - satellite identifier
            validity - validity of the correction in seconds
            tow - time of week (extracted from the navigation message) in seconds
            toh - time of hour extracted from the HAS header in seconds
            IOD - Issue of Data extracted from the HAS header
            signals - list of signals for which carrier phase biases are available

        Returns:
            The correction object. 
        """
        # Initialize the parent class
        super().__init__(gnss_ID, prn, validity, tow, toh, IOD)
        
        # List of supported signals
        self.signals = signals
        
        # List of carrier phase biases
        self.biases = np.zeros(len(signals))
        
        # Phase discontinuity indexes
        self.phase_discontinuity_inds = np.zeros(len(signals))
        
        # Availability flags related to the carrier phase biases
        self.availability_flags = np.ones(len(signals))
            
    def interpret(self, body, byte_offset, bit_offset) :
        """
        Summary :
            Actual implementation of the  method defining how to interpret the 
            body of the has message and use it to fill the different parts of 
            the correction.
            
        Arguments :
            body - array of bytes
            byte_offset - the byte offset in body
            bit_offset - the bit offset in body
        
        Returns:
            byte_offset - the new byte offset in body
            bit_offset - the new bit offset in body
        """            
        for ii in range(len(self.signals)) :
            bias, byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 11)
            
            if bias == 1024 :
                self.availability_flags[ii] = 0
            else :
                self.biases[ii] = two_complement(bias, 11) * 0.01
                
            self.phase_discontinuity_inds[ii], byte_offset, bit_offset = get_bits(body, byte_offset, bit_offset, 2)
                
        return byte_offset, bit_offset
    
    def is_empty(self) :
        """
        Summary:
            Check if the correction contains actual data or if it is empty.
            
        Arguments:
            None.
            
        Returns:
            True if there are no corrections available.
        """
        if len(self.signals) == 0 :
            return True
        
        if len(self.biases) == 0 :
            return True
        
        return False
    
    def __str__(self) :
        """
        Summary :
           Build a string representation of the object.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the content of the object
        """
        out_str = ""
        
        if self.is_empty() :
            return ""
        
        for ii in range(len(self.signals) - 1) :
            
            sig_str = super().__str__() + ',' + str(self.signals[ii]) + \
                      ',' + str(self.biases[ii]) + ',' + \
                      str(self.availability_flags[ii]) + ',' + \
                      str(self.phase_discontinuity_inds[ii]) + '\n' 
            
            out_str = out_str + sig_str
            
        # Add the last one with return carriage
        sig_str = super().__str__() + ',' + str(self.signals[-1]) + \
                ',' + str(self.biases[-1]) + ',' + str(self.availability_flags[-1]) + \
                ',' + str(self.phase_discontinuity_inds[-1])      

        out_str = out_str + sig_str
        
        return out_str
    
    def get_header(self) :
        """
        Summary :
           Build the string describing the attributes in the class __str__() 
           method.
           
        Arguments :
            None. The object its self.
            
        Returns:
            String representing the attributes of __str__()
        """
        out_str = super().get_header() + ',signal,phase_bias,av_flag,phase_discontinuity_ind'
        
        return out_str