# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 17:05:49 2023

@author: Daniele
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import allantools as at


import matplotlib as mp
fsize = 16
mp.rc('xtick', labelsize=fsize) 
mp.rc('ytick', labelsize=fsize) 


plt.style.use('ggplot')
gnss_ids = ["G", "", "E"]
gnss_spell = ["GPS", "", "Galileo"]

# load the csv file with the clock corrections
# filename = "SEPT1010.22_has_clk.csv"
filename = "SEPT293_GALRawCNAV.zip_has_clk.csv"
fname = filename[:filename.rfind(".")]
df = pd.read_csv(filename)

# determine which GNSS is present in the correction file
GNSS = np.unique(df["gnssID"].values)

###################### SOME INFO #####################
# light speed [m/sec]
v_light = 299792458

# # Frequency E1
# f1 = 1575.42e6

# # Frequency E5a
# f2 = 1176.45e6

# # Wavelength E1
# lambda1 = v_light/ f1 

# # Wavelength E5a
# lambda2 = v_light / f2

# # Coefficient linear combiantion
# a = f1**2 / (f1**2 + f2**2)
# b = f2**2 / (f1**2 - f2**2)

# # Equivalent wavelength 
# lambda_eq = lambda1 * lambda2 / (a * lambda1 + b * lambda2)

# Tau for ADEV
tau = np.logspace(1, 5, 40)

#######################################################

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
        clk_corr = clk_corr[ind] / v_light
        
        # measurement rate
        Ts = np.median(np.diff(time))
        rate = 1 / Ts 
        clk_freq = np.diff(clk_corr) / Ts
        
        t, ad, ade, adn = at.oadev( clk_corr, rate = rate, \
                                    data_type = "phase", taus = tau[:-3])
            
        # finally plot the result
        ax.loglog(t, ad, "-.", label = f"{gnss_ids[gnss]}{sat}")
        
    # Some cosmetics for the plots
    # ax.tick_params(axis='x', labelrotation = 45)
    ax.set_xlabel("Averaging Interval [s]", fontsize = fsize)
    ax.set_ylabel("ADEV", fontsize = fsize)
    ax.legend(loc=(1.05, 0), fontsize = 14, ncol=2)
    ax.autoscale(tight=True)
    ax.set_title(f"{gnss_spell[gnss]}", fontsize = fsize)
    plt.tight_layout()
 
    # Save as pdf
    plt.savefig(f"{fname}_{gnss_spell[gnss]}_adev.png", bbox_inches="tight")    