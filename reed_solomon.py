#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 

@author: 
"""

import galois
import numpy as np

def get_poly_gen( gf2m, k ) :

    """
    Summary:
        Funtion that produces the generating polynomial for Reed-Solomon
        encoding

    Arguments:
        gf2m - struct containing the elements for the different operations
              in GF(2^m)
        k - number of input words 

    Returns:
        polygen - vector containing the coefficients in GF(2^m) of the 
                generating polynomial

    History:
        Mar 27/19 - Function created by Daniele Borio.
        Jun 
    Remarks:
        1) polygen will be used to generate a RS( 2^m - 1, k ) code
        2) polygen is obtained by considering consecutive powers of alpha,
           the generating elements
    """
    
    n = gf2m.order - 1
    
    # Degree of the generating polynomial
    pdeg = n - k
    
    # allocate the first term of the generating polynomial
    pgen = gf2m.Ones(2)
    
    # Initialize the polynomial as (z + alpha)
    pgen[0] = gf2m.primitive_element
    
    polygen = galois.Poly(pgen.copy(), order="asc")

    # Now perform the multiplications by (z + alpha^ii)
    for ii in range(pdeg - 1) :
        pgen[0] *= gf2m.primitive_element
        p = galois.Poly(pgen, order="asc")
        
        polygen *= p
        
    return polygen

def rs_encode( gf2m, message, polygen, order = "asc" ) :
    """
    Summary:
        Function that encodes in a systematic way a message using the
        Reed-Solomon code defined by polygen on GF(2^m)
 
    Arguments:
        gf2m - struct containing the elements for the different operations
               in GF(2^m)
        message - vector containing the message to encode
        polygen - the generating polynomial
 
    Returns:
        cwords - the encoded message
    """

    # first check that all the elements are compatible
    msg_len = gf2m.order - len(polygen.coeffs)

    if msg_len != len(message) :
        print("Wrong message length, it should be %d" % msg_len)
        return None
    
    # allocate the encoded message
    if order == "asc" :
        coeffs = np.concatenate((np.zeros(len(polygen.coeffs) - 1, dtype=type(message[0])), message))
    else :
        coeffs = np.concatenate((message, np.zeros(len(polygen.coeffs) - 1, dtype=type(message[0]))))
        
    msg_poly = galois.Poly(coeffs, order=order, field=gf2m)
    
    # get the reminder
    rpol = msg_poly % polygen
    
    # add the reminder with the generating polynomial
    msg_poly += rpol
    
    return msg_poly.coeffs
    
def get_encoding_matrix( gf2m, polygen ) :

    # Build the generating matrix from 'polygen'
    n = gf2m.order - 1
    k = gf2m.order - len(polygen.coeffs)

    G = gf2m.Zeros( (n, k) )
    
    gcol = gf2m.Zeros( n )
    gcol[:(n-k+1)] = np.flip(polygen.coeffs)

    for ii in range(k) :
        G[:, ii] = np.roll(gcol, ii)
        

    Gk = G[(n-k):n,:] 
    InvGk = np.linalg.inv( Gk )

    # Finally find H
    H = gf2m.Zeros( G.shape )
    
    for ii in range(k) :
        H[n - k + ii, ii] = 1

    H[:(n-k),:] = G[:(n-k),:] @ InvGk
    
    return H

    