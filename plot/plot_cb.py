#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 13:10:31 2023

@author: daniele
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import matplotlib as mp
fsize = 16
mp.rc('xtick', labelsize=fsize) 
mp.rc('ytick', labelsize=fsize) 


plt.style.use('ggplot')
gnss_ids = ["G", "", "E"]
gnss_spell = ["GPS", "", "Galileo"]
gnss_ind = [1, -1, 0]

# Signal table - indentifies the different signals
signal_table = [["E1-B I/NAV OS", "L1 C/A"],
                ["E1-C", ""], 
                ["E1-B + E1-C", ""], 
                ["E5a-I F/NAV OS", "L1C(D)"], 
                ["E5a-Q", "L1C(P)"], 
                ["E5a-I+E5a-Q", "L1C(D+P)"], 
                ["E5b-I I/NAV OS", "L2 CM"], 
                ["E5b-Q", "L2 CL"], 
                ["E5b-I+E5b-Q", "L2 CM+CL"], 
                ["E5-I", "L2 P"], 
                ["E5-Q", "Reserved"], 
                ["E5-I + E5-Q", "L5 I"], 
                ["E6-B C/NAV HAS", "L5 Q"], 
                ["E6-C", "L5 I + L5 Q"], 
                ["E6-B + E6-C", ""], 
                ["", ""]]

# load the csv file with the code bias corrections
filename = "SEPT293_GALRawCNAV.zip_has_cb.csv"
fname = filename[:filename.rfind(".")]
df = pd.read_csv(filename)

# determine which GNSS is present in the correction file
GNSS = np.unique(df["gnssID"].values)

# make different plots for each gnss
for gnss in GNSS :
    # filter by gnss
    gnss_df = df[df["gnssID"] == gnss]

    # determine the number of unique signals in the file
    signals = np.unique(gnss_df["signal"].values)    

    # Create a new plot with as many subplots as signals
    fig, ax = plt.subplots(nrows=len(signals), ncols = 1)
    fig.set_size_inches((8, 8))

    # Loop on the different signals
    for ii, signal in enumerate(signals) :
        signal_df = gnss_df[gnss_df["signal"] == signal]
                
        # Determine the list of prn
        sats = np.unique(signal_df["PRN"].values)
    
        # Make a plot for each satellite
        for sat in sats :
            sat_df = signal_df[signal_df["PRN"] == sat]
        
            # build the time index
            time = np.floor( sat_df["ToW"].values / 3600 )  * 3600 + sat_df["ToH"].values
        
            # build the code bias
            code_bias = sat_df["code_bias"].values
        
            # remove duplicated values
            time, ind = np.unique(time, return_index = True)
            code_bias = code_bias[ind]
        
            # finally plot the result
            ax[ii].plot(time, code_bias, ".--", label = f"{gnss_ids[gnss]}{sat}")
       
        ax[ii].set_ylabel("Code bias [m]", fontsize = fsize)
        ax[ii].autoscale(tight=True)
        ax[ii].set_title(f"{gnss_spell[gnss]} - {signal_table[signal - 1][gnss_ind[gnss]]}", fontsize = fsize)
        if ax[ii] != ax[-1] :
             ax[ii].set_xticks([])
        
        
    # Some cosmetics for the plots
    ax[-1].tick_params(axis='x', labelrotation = 45)
    ax[-1].set_xlabel("Time of Week [s]", fontsize = fsize)
    ax[-1].legend(loc=(1.05, 0), fontsize = 14, ncol=2)
    
    # plt.tight_layout()
 
    # Save as pdf
    plt.savefig(f"{fname}_{gnss_spell[gnss]}.png", bbox_inches="tight")    