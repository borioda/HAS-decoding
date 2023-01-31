#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 14:34:40 2023

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

# load the csv file with the clock corrections
filename = "SEPT293_GALRawCNAV.zip_has_orb.csv"
fname = filename[:filename.rfind(".")]
df = pd.read_csv(filename)

# determine which GNSS is present in the correction file
GNSS = np.unique(df["gnssID"].values)

# make different plots for each gnss
for gnss in GNSS :
    # filter by gnss
    gnss_df = df[df["gnssID"] == gnss]
    
    # Create a new plot
    fig, ax = plt.subplots(nrows=3, ncols=1, sharex = True)
    fig.set_size_inches((14, 9))
    # Determine the list of prn
    sats = np.unique(gnss_df["PRN"].values)
    
    # Make a plot for each satellite
    for sat in sats :
        sat_df = gnss_df[gnss_df["PRN"] == sat]
        
        # build the time index
        time = np.floor( sat_df["ToW"].values / 3600 )  * 3600 + sat_df["ToH"].values
        
        # extract the corrections
        radial = sat_df["delta_radial"].values
        in_track = sat_df["delta_in_track"].values
        cross_track = sat_df["delta_cross_track"].values
        
        # remove duplicated values
        time, ind = np.unique(time, return_index = True)
        radial = radial[ind]
        in_track = in_track[ind]
        cross_track = cross_track[ind]
        
        # finally plot the result
        ax[0].plot(time, radial, ".", label = f"{gnss_ids[gnss]}{sat}")
        ax[1].plot(time, in_track, ".", label = f"{gnss_ids[gnss]}{sat}")
        ax[2].plot(time, cross_track, ".", label = f"{gnss_ids[gnss]}{sat}")
       
    # Some cosmetics for the plots
    ax[2].tick_params(axis='x', labelrotation = 45)
    ax[2].set_xlabel("Time of Week [s]", fontsize = fsize)
    
    ax[0].set_ylabel("Radial [m]", fontsize = fsize)
    ax[1].set_ylabel("In Track [m]", fontsize = fsize)
    ax[2].set_ylabel("Cross Track [m]", fontsize = fsize)
    
    ax[2].legend(loc=(1.05, 0), fontsize = 14, ncol=2)

    ax[0].autoscale(tight=True)
    ax[1].autoscale(tight=True)
    ax[2].autoscale(tight=True)
    
    ax[0].set_title(f"{gnss_spell[gnss]}", fontsize = fsize)
    
    # plt.tight_layout()
 
    # Save as pdf
    plt.savefig(f"{fname}_{gnss_spell[gnss]}.png", bbox_inches="tight")