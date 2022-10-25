#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 19 October 2022

@author: 
    Daniele Borio
""" 

from ipywidgets import (VBox, Dropdown, HTML, Layout, RadioButtons, Button )

# Main file with actual parsing routines
from process_cnav import parse_data


class process_button_widget(VBox) :
    """
    Summary:
        Simple widget with a single button to start the processing.
    """
    def __init__(self, filename, options) :
        """
        Summary :
            Object constructor.
            
        Arguments:
            filename - filename of the file to process
            options - list with the options defining the processing parameters
            
        Returns:
            The process_button_widget.
        """
        self.filename = filename
        self.options = options
        
        self.wb_process = Button(
            description='Parse',
            disabled=False,
            icon='Initialize'
        )
        
        @self.wb_process.on_click
        def process_on_click(b) :
            _type = None
            
            # Get the _rx type
            if self.options[0] == "Septentrio" :
                rx = "sep"
                
                if len(self.options) > 1 :
                    if self.options[1] == 'decimal' :
                        _type = "txt"
                    elif self.options[1] == 'binary':
                        _type = "bin"
                else :
                    _type = "hexa"
            
            elif self.options[0] == "Novatel" :
                rx = "nov"
            elif self.options[0] == "Javad" :
                rx = "jav"
            else :
                raise Exception("Unsupported Receiver Type")
                
            # Start the processing
            parse_data(filename, rx, _type, True)
        
        super().__init__([self.wb_process],
                         layout=Layout(border='1px solid black'))
            
class receiver_type_widget(VBox) :
    """
    Summary:
        Simple widget used to select the input data type.
        The selection is based on the type of receiver used for the data 
        collection. 
        
        The following receivers are currently supported:
            Septentrio - Galileo CNAV message
            NovAtel - GALCNAVRAWPAGE message in ASCII format
            Javad - ED message
    """
    
    # List of recevier currently supported
    rx_list = ["Javad",
               "Novatel",
               "Septentrio"]
    
    def __init__(self) :
        """
        Summary :
            Object constructor.
            
        Arguments:
            None.
            
        Returns:
            The receiver_type_widget.
        """
        
        # Create a drop-down menu with the list of supported receivers
        self.rx_ddmenu = Dropdown(
                            options = receiver_type_widget.rx_list,
                            description="Rx Type:",
                            placeholder="rx_type",
                            disabled=False )
        
        self.other_elements = None
        
        def on_down_change(change) :
            
            # Do something only if "Septentrio" is selected
            if self.rx_ddmenu.value == "Septentrio" :
                # Add a format type (radio button)
                radio_input = RadioButtons(
                                options=['binary','hexadecimal', 'decimal'],
                                description = 'File Type',   
                                disabled = False)
                
                self.children = [HTML(value = "<B>Receiver type:</B>"),
                                 self.rx_ddmenu, radio_input]                
            else:
                self.other_elements = None
                self.children = [HTML(value = "<B>Receiver type:</B>"),
                                 self.rx_ddmenu]
                
        self.rx_ddmenu.observe(on_down_change, 'value')
        
        super().__init__([HTML(value = "<B>Receiver type:</B>"),
                         self.rx_ddmenu],
                         layout=Layout(border='1px solid black'))
        
    
    def get_options(self) :
        """
        Summary :
            Obtain the options set in through the widget.
            
        Arguments:
            None.
            
        Returns:
            List with the options.
        """
        
        options = [self.rx_ddmenu.value]
        if options[ 0 ] == "Septentrio" :
            if len(self.children) == 3 :
                options.append(self.children[-1].value)
            else :
                raise Exception("Missing parameter")
            
        return options
    