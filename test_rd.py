#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 13:18:29 2021

@author: daniele
"""

import galois
import reed_solomon as rd
import numpy as np


gf2m = galois.GF(2**8)
k = 32

p = rd.get_poly_gen( gf2m, k )

# Coefficients can be accessed as
# p.coeffs

message = np.array([71, 12, 25, 210, 178, 81, 243, 9, 112, 98, 196, 203, 48, 125,
                    114, 165, 181, 193, 71, 174, 168, 42, 31, 128, 245, 87, 150,
                    58, 192, 66, 130, 179], dtype = np.uint8)

enc_msg = rd.rs_encode( gf2m, message, p, "desc" )

H =  rd.get_encoding_matrix(gf2m, p)
 
enc_msg2 = np.flip(H @ gf2m(np.flip(message)))

H1 = np.fliplr(np.flipud(H))

# print the matrix to file
fout = open("has_encoding_matrix.csv", "w")

for ii in range(H1.shape[0]) :
    for jj in range(H1.shape[1]) :
        if jj != 0 :
            fout.write(',')
        fout.write(str(int(H1[ii,jj])))
    fout.write('\n')

fout.close()