#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:59:27 2023

@author: daniele
"""

from plot_orb import plot_orb
from plot_clk import plot_clk
from plot_cb import plot_cb
from plot_cp import plot_cp
from clk_adev import clk_adev


basename = "SEPT271k.22__has"

# Orbits
filename = basename + "_orb.csv"
plot_orb(filename)

# Clocks
filename = basename + "_clk.csv"
plot_clk(filename)
clk_adev(filename)

# Code bias
filename = basename + "_cb.csv"
plot_cb(filename)

# Carrier phase bias
filename = basename + "_cp.csv"
plot_cp(filename)

