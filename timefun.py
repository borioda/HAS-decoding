# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 08:43:00 2018

@author: daniele
"""

import math
import numpy as np
import pandas as pd

def datetimeToGps( time ) :
    val = pd.to_datetime(time)
    
    year = val.year
    month = val.month
    day = val.day
    hours = val.hour
    minutes = val.minute
    seconds = val.second    

    tow, gpsweek = DateToGPS( year, month, day, hours )
    tow += minutes * 60 + seconds
    
    return tow, gpsweek
    
def vecDT2Gps( time ) :
    return np.vectorize(datetimeToGps)(time)    

"""    
DateToMjd - Converts a date into the modified julian day

    input:
        year, month, day and hour
    
    output:
        the mjd - modified julian day

"""
def DateToMjd( year, month, day, hour ):
    
    # year, month and day are considered as unsigned integers
    # hour can be a float
    if month <= 2:
        year -= 1
        month += 12
        
    p1 = math.floor( 365.25 * ( float( year ) + 4716.0 ) )
    p2 = math.floor( 30.6001 * ( float( month ) + 1 ) )
    
    # compute the julian day
    julian = p1 + p2 + float(day) + float(hour) / 24 - 1537.5
    
    mdj = julian - 2400000.5
    
    return mdj
    
"""    
DateToGps - Converts a date into GPS week and GPS tow

    input:
        year, month, day and hour
    
    output:
        GpsWeek - the GPS week
        tow - the time of week

"""
def DateToGPS( year, month, day, hour ):
    # First get the mdj
    mdj = DateToMjd( year, month, day, hour )

    # Compute the 'GPS days'
    gpsDays = mdj - DateToMjd( 1980, 1, 6, 0.0 )

    # Get the GPS week
    GpsWeek = int( gpsDays / 7 )

    # Finally compute the Tow
    tow = int(( gpsDays - 7 * GpsWeek ) * 86400 + 0.5)

    return tow, GpsWeek        

"""    
GpsToDate - Converts GPS week and GPS tow into a date

    input:
        GpsWeek - the GPS week
        tow - the time of week
    
    output:
        year, month, day and hour
"""
def GpsToDate( GpsWeek, GpsSeconds ) :
    mjd = GpsToMjd( GpsWeek, GpsSeconds )
    year, month, day, hour = MjdToDate( mjd )
    
    return year, month, day, hour

"""
Converts the modified Julian day into a date
"""
def MjdToDate( Mjd ) :

    # Get the Julian day from the modified julian day
    jd = Mjd + 2400000.5;

    # Take only the integer part (integer Julian day)
    jdi = int( jd )
    
    # Fractional part of the day
    jdf = jd - float( jdi ) + 0.5;
        
    # Really the next calendar day?
    if jdf >= 1.0 :
       jdf = jdf - 1
       jdi = jdi + 1
    
    # Extract the hour from the fractional part of the day
    hour = jdf * 24.0    
    l = int( jdi + 68569 )
    n = ( 4 * l ) / 146097

    l = l - ((146097 * n + 3) / 4)
    year = int(4000 * (l + 1) ) / 1461001

    l = l - (1461 * year ) / 4 + 31
    month = int(80 * l ) / 2447

    day = l - (2447 * month) / 80

    l = month / 11

    month = month + 2 - 12 * l
    year = 100 * (n - 49) + year + l

    return year, month, day, hour

"""
    Convert GPS Week and Seconds to Modified Julian Day.
    Ignores UTC leap seconds.
"""

def GpsToMjd ( GpsWeek, GpsSeconds ) :
    

	GpsDays = 7 * float( GpsWeek ) + ( GpsSeconds / 86400)
		
	Mjd = DateToMjd( 1980, 1, 6, 0 ) + GpsDays

	return Mjd

