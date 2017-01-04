#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 30 11:44:00 2016

@author: pavel
"""
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

APP_NAME = "testdisk"
GLADE_FILE = "ui.glade"

class Window:    
    
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP_NAME)
        self.builder.add_from_file(GLADE_FILE)
        
        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self._on_close)
        
    def run(self):
        self.window.show()
        Gtk.main()
        
    def _on_close(self, *args):
        Gtk.main_quit()      


    
if __name__ == "__main__":
    window = Window()
    window.run()    


