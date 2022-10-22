#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  9 07:08:06 2022

@author: daniele
"""

import pandas as pd
import numpy as np
import timefun as tf
"""
Summary :
    Set of functions implementing data loading from different file formats
    
     Mainly based on the code developed by Melania Susi.
"""


def load_from_parsed_Septentrio(filename : str, _type : str = "hexa" ) :
    """
        Summary :
            Load the data from a text file obtained by parsing the GALRawCNAV
            message.
        
        Arguments :
            filename - pathname of the file to be loaded
            _type - indicates the way data have been parsed 
                    txt: payload as 32 bit integers
                    hexa: payload as sequence of hexadecimal values
    """
    # Specify the data type
    data_types = {"word 1" : np.uint32, "word 2" : np.uint32, "word 3" : np.uint32,
                  "word 4" : np.uint32, "word 5" : np.uint32, "word 6" : np.uint32,
                  "word 7" : np.uint32, "word 8" : np.uint32, "word 9" : np.uint32,
                  "word 10" : np.uint32, "word 11" : np.uint32, "word 12" : np.uint32,
                  "word 13" : np.uint32, "word 14" : np.uint32, "word 15" : np.uint32,
                  "word 16" : np.uint32}

    if _type == "txt" :
        # header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType", "NAVBits"]
        header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType", "word 1", \
                       "word 2", "word 3", "word 4", "word 5", "word 6", "word 7", "word 8",\
                       "word 9", "word 10", "word 11", "word 12", "word 13", "word 14",\
                       "word 15", "word 16"]
        
        
        if filename.endswith('.zip') :               
            df = pd.read_csv(filename, compression='zip', sep=',| ', names=header_list, \
                         engine='python', dtype = data_types)
        else :
            df = pd.read_csv(filename, sep=',| ', names=header_list, \
                         engine='python', dtype = data_types)
                    
    elif _type == "hexa" :
        header_list = ["TOW", "WNc [w]", "SVID", "CRCPassed", "ViterbiCnt", "signalType",\
                       "VITERBI_TYPE","RxChannel","word 1", \
                       "word 2", "word 3", "word 4", "word 5", "word 6", "word 7", "word 8",\
                       "word 9", "word 10", "word 11", "word 12", "word 13", "word 14",\
                       "word 15", "word 16"]
            
        converters = {
            "word 1" : lambda x: int(x, 16),\
            "word 2" : lambda x: int(x, 16),\
            "word 3" : lambda x: int(x, 16),\
            "word 4" : lambda x: int(x, 16),\
            "word 5" : lambda x: int(x, 16),\
            "word 6" : lambda x: int(x, 16),\
            "word 7" : lambda x: int(x, 16),\
            "word 8" : lambda x: int(x, 16),\
            "word 9" : lambda x: int(x, 16),\
            "word 10" : lambda x: int(x, 16),\
            "word 11" : lambda x: int(x, 16),\
            "word 12" : lambda x: int(x, 16),\
            "word 13" : lambda x: int(x, 16),\
            "word 14" : lambda x: int(x, 16),\
            "word 15" : lambda x: int(x, 16),\
            "word 16" : lambda x: int(x, 16)
            }
        
        if filename.endswith('.zip') :
            df = pd.read_csv(filename, compression='zip', sep=',| ', names=header_list, \
                         engine='python', converters = converters)
        else :
            df = pd.read_csv(filename, sep=',| ', names=header_list, \
                         engine='python', converters = converters)
        
        IsInterpreted = False        
                
        # Apply specific processing depending if data have been interpreted or if left raw
        if isinstance(df["CRCPassed"].values[0], str) :
            df["CRCPassed"] = (df["CRCPassed"].values == "Passed")    
            IsInterpreted = True
        
        if isinstance(df["SVID"].values[0], str) :
            df["SVID"] = df["SVID"].apply(lambda x: int(x[1:]))
            IsInterpreted = True
        
        if not IsInterpreted :
            # In this case, the Tow is expressed in ms
            # Covert it in s
            df["TOW"] = (df["TOW"].values / 1000).astype(int)
            
            # The Galileo satellite IDs have an offset of 70
            df["SVID"] = df["SVID"].values - 70

    return df

def load_from_Javad(filename : str ) :
    """
        Summary :
            Load the data from a Javad binary file.
        
        Arguments :
            filename - pathname of the file to be loaded
    """
    
    # Open the input file
    fid = open(filename, "rb")
    
    # Dictionary with the parsed information
    data = { "TOW" : [], 
             "WNc [w]" : [], 
             "SVID": [], 
             "CRCPassed" : [], 
             "ViterbiCnt" : [], 
             "signalType" : [], 
             "word 1": [],
             "word 2": [], 
             "word 3": [], 
             "word 4": [], 
             "word 5": [], 
             "word 6": [], 
             "word 7": [], 
             "word 8": [],
             "word 9": [], 
             "word 10": [], 
             "word 11": [], 
             "word 12": [], 
             "word 13": [], 
             "word 14": [],
             "word 15": [], 
             "word 16": []
            }
    
    WN = 0
    
    # read the file line by line
    while True :
        
        line = fid.readline()
        if not line :
            break
        
        
        if len(line) < 9 :
            continue
        
        try :
            header = str(line[:5], 'utf-8')
        except :
            continue
        
        # Message containing the data
        # This message is used to determine the GPS week
        if header == 'RD006' :
            year  = line[5] + 256 * line[6]
            month = line[7]
            day   = line[8]
            
            # compute the GPS week
            _, WN = tf.DateToGPS(year, month, day, 0)
            
            continue
           
        # Message with the E6B navigation bits after Viterbi decoding
        if header[:2] == 'ED' :
        
            # Check if the signal type is correct
            # and the message length is as expected
            # signal (sig = 6 refers to Galileo E6B)
            if (line[10] != 6) or (line[11] != 62 ):
                continue
            
            # Check if the line is too short or broken on two lines
            # This is just a work around
            while len(line) < 76 :
                line1 = fid.readline()
                line = line + line1
            
            # prn
            prn = line[5]
            data["SVID"].append(prn)
            
            # Time of receiving message
            ToW = int.from_bytes( line[6:10], 'little')
            data["TOW"].append(ToW)
            data["WNc [w]"].append(WN)
            
            # Other data value set to default values
            data["CRCPassed"].append(True) 
            data["ViterbiCnt"].append(0) 
            data["signalType"].append(19)
            
            # save the 16 words (16 x 32 bits = 512)
            for ii in range(15) :
                word = int.from_bytes( line[(12 + ii*4):(12 + (ii + 1)*4)], 'big' )
                data[f"word {ii + 1}"].append(word)                

            # last word
            # 62 is nav message length in bytes
            word = int.from_bytes( line[(12 + 15*4):(12 + 62)], 'big' ) << 16
            data["word 16"].append(word)
                           
    # close the inpu file
    fid.close()
    
    # create the output dataframe
    df = pd.DataFrame(data=data)
    
    return df

def load_from_TopCon(filename : str ) :
    """
        Summary :
            Load the data from a Topcon binary file. 
            Very similar to the Javad case
        
        Arguments :
            filename - pathname of the file to be loaded
    """
    # Open the input file
    fid = open(filename, "rb")
    
    # Dictionary with the parsed information
    data = { "TOW" : [], 
             "WNc [w]" : [], 
             "SVID": [], 
             "CRCPassed" : [], 
             "ViterbiCnt" : [], 
             "signalType" : [], 
             "word 1": [],
             "word 2": [], 
             "word 3": [], 
             "word 4": [], 
             "word 5": [], 
             "word 6": [], 
             "word 7": [], 
             "word 8": [],
             "word 9": [], 
             "word 10": [], 
             "word 11": [], 
             "word 12": [], 
             "word 13": [], 
             "word 14": [],
             "word 15": [], 
             "word 16": []
            }
    
    WN = 0
    ToW = 0
    year = 0
    month = 0
    day = 0
    daysec = 0 
    
    # read the file line by line
    while True :
        
        line = fid.readline()
        if not line :
            break
        
        
        if len(line) < 9 :
            continue
        
        try :
            header = str(line[:5], 'utf-8')
        except :
            continue
        
        # Message containing the data
        # This message is used to determine the GPS week
        if header == 'RD006' :
            year  = line[5] + 256 * line[6]
            month = line[7]
            day   = line[8]
            
            hour = daysec / 3600.0
            
            # compute the GPS week
            ToW, WN = tf.DateToGPS(year, month, day, hour)
            
            continue
        
        # Message providing the seconds of the day
        if header == '~~005' :
        
            # seconds of the day
            daysec = int.from_bytes( line[5:9], 'little') / 1000.0
            
            # compute the GPS week
            if year != 0 :
                hour = daysec / 3600.0
                ToW, WN = tf.DateToGPS(year, month, day, hour)
            
            continue

        if header[:2] == 'MD' :
             
            # prn
            prn = line[6]
            data["SVID"].append(prn)
            
            # Time of receiving message
            data["TOW"].append(ToW)
            data["WNc [w]"].append(WN)
            
            # Other data value set to default values
            data["CRCPassed"].append(True) 
            data["ViterbiCnt"].append(0) 
            data["signalType"].append(19)
            
            # save the 16 words (16 x 32 bits = 512)
            for ii in range(16) :
                word = int.from_bytes( line[(8 + ii*4):(8 + (ii + 1)*4)], 'little' )
                data[f"word {ii + 1}"].append(word)                
                           
    # close the inpu file
    fid.close()
    
    # create the output dataframe
    df = pd.DataFrame(data=data)
    
    return df

def load_from_Novatel(filename : str ) :
    """
        Summary :
            Load the data from a Novatel data file. 
        
        Arguments :
            filename - pathname of the file to be loaded
    """
    # Open the input file
    fid = open(filename, "rb")
    
    # Dictionary with the parsed information
    data = { "TOW" : [], 
             "WNc [w]" : [], 
             "SVID": [], 
             "CRCPassed" : [], 
             "ViterbiCnt" : [], 
             "signalType" : [], 
             "word 1": [],
             "word 2": [], 
             "word 3": [], 
             "word 4": [], 
             "word 5": [], 
             "word 6": [], 
             "word 7": [], 
             "word 8": [],
             "word 9": [], 
             "word 10": [], 
             "word 11": [], 
             "word 12": [], 
             "word 13": [], 
             "word 14": [],
             "word 15": [], 
             "word 16": []
            }
    
    WN = 0
    
    # read the file line by line
    while True :
        
        line = fid.readline()
        if not line :
            break
        
        if len(line) < 16 :
            continue
        
        # Try to convert the string in a sequence of characters
        try :
            str_line = str(line, 'utf-8')
        except :
            continue
        
        # Check if str_line contains 'GALCNAVRAWPAGE'
        if (str_line.find("GALCNAVRAWPAGE") > -1) :
            
            # This is valid message
            
            # Get the message time
            if (str_line.find("SATTIME") > -1) :
                split_line = str_line.split()
                time_ind = split_line.index('SATTIME')
                WN = int(split_line[time_ind + 1])
                ToW = float(split_line[time_ind + 2]) + 1
            else :
                continue
            
            # Now read the next line that contains the PRN info and the payload
            line = fid.readline()
            
            # If this generates an error, it means there is a problem with the
            # data stream
            str_line = str(line, 'utf-8')
            
            # Split the data
            split_line = str_line.split()
            prn = int(split_line[2])
            
            payload = split_line[-1]
            
            # Write the extracted information to the dictionary
            data["SVID"].append(prn)
            data["TOW"].append(ToW)
            data["WNc [w]"].append(WN)
            
            # Other data value set to default values
            data["CRCPassed"].append(True) 
            data["ViterbiCnt"].append(0) 
            data["signalType"].append(19)
            
            # Now extract the different words
            for ii in range(14) :
                word = int(payload[(8*ii):(8*ii + 8)], 16)
                data[f"word {ii + 1}"].append(word)                

            # last two words
            word = int( payload[112:], 16 ) << 16
            data["word 15"].append(word)
            data["word 16"].append(0)
    
    # close the inpu file
    fid.close()
    
    # create the output dataframe
    df = pd.DataFrame(data=data)
    
    return df    