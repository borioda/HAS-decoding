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
    


def plot_clk( filename ) :

    fsize = 16
    mp.rc('xtick', labelsize=fsize) 
    mp.rc('ytick', labelsize=fsize) 
    
    
    plt.style.use('ggplot')
    gnss_ids = ["G", "", "E"]
    gnss_spell = ["GPS", "", "Galileo"]
    
    # load the csv file with the clock corrections
    fname = filename[:filename.rfind(".")]
    df = pd.read_csv(filename)
    
    # determine which GNSS is present in the correction file
    GNSS = np.unique(df["gnssID"].values)
    
    # make different plots for each gnss
    for gnss in GNSS :
        # filter by gnss
        gnss_df = df[df["gnssID"] == gnss]
        
        # Create a new plot
        fig, ax = plt.subplots()
        fig.set_size_inches((12, 8))
        # Determine the list of prn
        sats = np.unique(gnss_df["PRN"].values)
        
        # Make a plot for each satellite
        for sat in sats :
            sat_df = gnss_df[gnss_df["PRN"] == sat]
            
            # build the time index
            time = np.floor( sat_df["ToW"].values / 3600 )  * 3600 + sat_df["ToH"].values
            
            # build the clock correction
            clk_corr = sat_df["delta_clock_c0"].values * sat_df["multiplier"].values
            
            # remove duplicated values
            time, ind = np.unique(time, return_index = True)
            clk_corr = clk_corr[ind]
            
            # finally plot the result
            ax.plot(time, clk_corr, ".", label = f"{gnss_ids[gnss]}{sat}")
           
        # Some cosmetics for the plots
        ax.tick_params(axis='x', labelrotation = 45)
        ax.set_xlabel("Time of Week [s]", fontsize = fsize)
        ax.set_ylabel("Clock Corrections [m]", fontsize = fsize)
        ax.legend(loc=(1.05, 0), fontsize = 14, ncol=2)
        ax.autoscale(tight=True)
        ax.set_title(f"{gnss_spell[gnss]}", fontsize = fsize)
        plt.tight_layout()
     
        # Save as pdf
        plt.savefig(f"{fname}_{gnss_spell[gnss]}.png", bbox_inches="tight")

if __name__ == "__main__":
    
    # Set the input file name        
    filename = "SEPT293_GALRawCNAV.zip_has_clk.csv"
    plot_clk( filename )
    