#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 08:47:52 2021

@author: daniele
"""

import numpy as np

# use the "galois" package for operations on GF(2^8) and Reed-Solomon decoding
import galois


class has_message :
    """
    Summary :
        
        Container class for a HAS message. A message is made of several pages,
        each page is made of 53 bytes (424 bits). Each byte has to be interpreted
        as an element of GF(2^8)
    """
    
    # Static members - these variables should never be touched (after initialization)!
    
    # Finite field for decoding operations
    GF256 = galois.GF(2**8)
    
    # Reed-Solomon encoding matrix
    H = np.genfromtxt('has_encoding_matrix.csv', delimiter=',', dtype=np.uint8)

    def __init__(self, mtype, mid, size) :
        """        
        Summary :
            Object constructor.
    
        Arguments :
            mtype - type of the message (only MT1 is currently supported) 
            mid - ID of the message
            msize - size of the message expressed in number of pages
        
        Returns:
            Nothing.
        """
        
        # Set the message type
        self.mtype = mtype 
        
        # Set the message ID
        self.id = mid
        
        # Set the size of message in pages
        self.size = size
        
        # Allocate the matrix containing the different pages
        self.pages = np.zeros((size, 53), dtype = np.uint8)
        
        # Array with the page ID
        self.page_ids = - np.ones(size, dtype = np.uint8)
        
        # Index pointing to the next available page slot
        self.page_index = 0
        
        # Age of the message: tells for how many epochs the message was not
        # updated. To be used by the decoder to remove messages
        self.age = 0
        
        
    def add_page( self, page_id, page ) :
        """
        Summary :
            Add a new page to the message
            
        Arguments :
            page_id - the page ID
            page - array with the 53 bytes of the new page 
        
        Returns :
            True if the update was correctly performed
        """
        # In any case reset the age of the message
        self.age = 0
        
        # Add a page only if the message is not complete
        if self.page_index == self.size : 
            return False

        # Add a page only if it is not present in the message
        if page_id not in self.page_ids :
            # Add the page to the message
            self.page_ids[self.page_index] = page_id
            self.pages[self.page_index, :] = page
            self.page_index += 1
        
            return True
        else :
            return False
    
    def add_page_sep_bytes(self, page_as_sep_bytes) :
        """
        Summary :
            A Septentrio receiver provides the CNAV page as an array of 16 32-bit 
            integers (512 bits) including headers and other unecessary elements.
            This function update the a HAS message using the bytes provided by the
            Septentrio receiver.
        
        Arguments :
            page_as_sep_bytes - array with 16 32-bit integers representing the HAS
                                message
        Returns :
            True if the update was correctly performed        
        """
        
        # Extract the header
        HAS_Header = ( (page_as_sep_bytes[0] & 0x3FFFF) << 6 ) + \
                     ( page_as_sep_bytes[1] >> 26)
        
        mtype = ( HAS_Header >> 18 ) & 0x3 
        
        if mtype != self.mtype :
            return False
        
        mid = ( HAS_Header >> 13 ) & 0x1F

        if mid != self.id :
            return False

        msize = (( HAS_Header >> 8 ) & 0x1F) + 1        
        
        if msize != self.size :
            return False

        # If here, everything is fine and we can start building the actual page
        # in bytes             
        page_id = (HAS_Header) & 0xFF
        
        page = np.zeros(53, dtype = np.uint16)
        
        # Treat the first 32 bit integer differently 
        page[0] = ( page_as_sep_bytes[1] >> 18 ) & 0xFF
        page[1] = ( page_as_sep_bytes[1] >> 10 ) & 0xFF
        page[2] = ( page_as_sep_bytes[1] >> 2 ) & 0xFF
        
        # two bits are left
        rem_bits = ( page_as_sep_bytes[1] & 0x3 ) << 6
        
        # Process the other bytes (last excluded)
        for ii in range(2, 14) :
            page[3 + (ii - 2) * 4] = rem_bits + (( page_as_sep_bytes[ii] >> 26 ) & 0x3F)
            page[4 + (ii - 2) * 4] = ( page_as_sep_bytes[ii] >> 18 ) & 0xFF
            page[5 + (ii - 2) * 4] = ( page_as_sep_bytes[ii] >> 10 ) & 0xFF
            page[6 + (ii - 2) * 4] = ( page_as_sep_bytes[ii] >> 2 ) & 0xFF
            rem_bits = ( page_as_sep_bytes[ii] & 0x3 ) << 6
       
        # Two more bytes to be extracted from the last 32 bit integer
        page[51] = rem_bits + (( page_as_sep_bytes[14] >> 26 ) & 0x3F)
        page[52] = ( page_as_sep_bytes[14] >> 18 ) & 0xFF
       
        # Now we are ready for updating the message
        success = self.add_page(page_id, page )
       
        return success
   
    def increase_age(self) :
        """
        Summary :    
            Increase the age of the message
            
        Arguments :
            None.
            
        Returns :
            Nothing.
        """
        self.age += 1
    
    def is_old(self, limit_age) :
        """
        Summary :    
            Tell if the message is old
            
        Arguments :
            limit_age - the maximum age allowed for the message
            
        Returns :
            True if the message is old.
        """
        if self.age > limit_age :
            return True
        else :
            return False
    
    def complete(self) :
        """
        Summary :    
            Check if the message is complete, i.e. if all the pages required have been
            collected
        
        Arguments :
            None.    
            
        Returns :
            True if the message is complete
        """
        return (self.size == self.page_index)
    
    def is_message(self, msg_type, msg_id, msg_size) :
        """
        Summary :    
            Check if this message is the one identified by msg_type, msg_id, msg_size
        
        Arguments :
            msg_type - the message type 
            msg_id - the message id 
            msg_size - the message size   
            
        Returns :
            True if this is the correct message
        """
        is_message = (self.mtype == msg_type) and (self.id == msg_id) and \
                     (self.size == msg_size)
                     
        return is_message
        
    def decode(self) :
        """
        Summary :    
            Decode the message.
            
        Arguments :
            None.
            
        Returns :
            The deconded message 
        """
        
        if not self.complete() :
            return None
        
        # For the moment only MT1 messages are supported
        if self.mtype != 1 :
            return None 
        
        # If here, perform decoding
        # Get the reduced encoding matrix
        HR = self.GF256(self.H[self.page_ids, 0:self.size])
        
        try :
            HRinv = np.linalg.inv(HR)
        except :
            return None
        
        msg = HRinv @ self.GF256(self.pages)
        
        return msg
        
        