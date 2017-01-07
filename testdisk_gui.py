#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 30 11:44:00 2016

@author: pavel
"""
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject

import threading

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

APP_NAME = "testdisk"
GLADE_FILE = "ui.glade"


import disk_operations 
import testdisk
import report
import utils
import filesave

# decorators
def gtk_idle(gui_task):    
    def job(*args, **kwargs):
        def idle():
            gui_task(*args, **kwargs)
            return False # !!!
        GObject.idle_add(idle)
    return job
    
def async(func):
    def job(*args, **kwargs):
        thr = threading.Thread(target = func, args=args, kwargs = kwargs)
        thr.start()
    return job
    
class Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]    
    

class AboutDialog(metaclass=Singleton):
    def __init__(self, builder):
        self.builder = builder
        self.dialog = self.builder.get_object("about_dialog")
        self.dialog.connect("delete-event", self.on_hide)
        
    def show(self):
        self.dialog.run()
        self.on_hide()
        
    def on_hide(self, *args):
        self.dialog.hide()
        return True     

class TestSettingsDialog(metaclass=Singleton):    
    def __init__(self, builder):
        self.builder = builder
        
        self.dialog = self.builder.get_object("test_settings_dialog")
        self.dialog.connect("delete-event", self.on_hide)
                        
        self.start_entry = self.builder.get_object("settings_dialog_start")
        self.stop_entry = self.builder.get_object("settings_dialog_stop")
        
        self.start_entry.connect("changed", self.force_digits)
        self.stop_entry.connect("changed", self.force_digits)
        
        self.entry_values = {self.start_entry : 0,
                               self.stop_entry : -1}        
        
        
    def on_hide(self, *args):
        self.dialog.hide()
        return True
        
    def show(self, start, stop):
        self.entry_values[self.start_entry] = start
        self.entry_values[self.stop_entry] = stop
        
        self.start_entry.set_text(str(start))
        self.stop_entry.set_text(str(stop))
        
        response = self.dialog.run()
        self.on_hide()
        
        if response == Gtk.ResponseType.APPLY: # confirmed
            start = self.entry_values.get(self.start_entry)
            stop = self.entry_values.get(self.stop_entry)
            return start, stop       

                
    def force_digits(self, entry):
        new_val = entry.get_text().strip()
        try:            
            if len(new_val) == 0:
                new_val = 0
            elif new_val == "-" :# allowing minus sign alone
                new_val = -1
            else:
                new_val = int(new_val) 
            self.entry_values[entry] = new_val
        except:
            entry.set_text(str(self.entry_values[entry]))


class FileSaveDialog(metaclass=Singleton):
    def __init__(self, builder):
        self.builder = builder
        self.dialog = self.builder.get_object("file_save_dialog")   
        self.dialog.connect("delete-event", self.on_hide)
        
        self.last_dir = filesave.get_home_dir()
        
        
    def on_hide(self, *args):
        self.last_dir = self.dialog.get_current_folder()
        self.dialog.hide()
        return True
        
    def get_fname(self, default_name):
        self.dialog.set_current_folder(self.last_dir)
        self.dialog.set_current_name(default_name)
        
        response = self.dialog.run()
        self.on_hide()
        
        if response == Gtk.ResponseType.OK:
            return self.dialog.get_filename()
        
class ConfirmationDialog(metaclass=Singleton):
    def __init__(self, builder):
        self.builder = builder
        self.dialog = self.builder.get_object("confirm_dialog")   
        self.dialog.connect("delete-event", self.on_hide)
        
    def on_hide(self, *args):
        self.dialog.hide()
        return True        
        
    def confirm(self, text, additional_text, func, *args, **kwargs):
        self.dialog.set_property("text", text)
        self.dialog.set_property("secondary-text", additional_text)
        
        response = self.dialog.run()
        self.on_hide()
        
        if response == Gtk.ResponseType.YES: # confirmed
            func(*args, **kwargs)
            
class ErrorDialog(metaclass=Singleton):
    def __init__(self, builder):
        self.builder = builder
        self.dialog = self.builder.get_object("error_dialog")   
        self.dialog.connect("delete-event", self.on_hide)   
        
    def on_hide(self, *args):
        self.dialog.hide()
        return True
        
    def show(self, err_text):
        self.dialog.set_property("secondary-text", err_text)
        response = self.dialog.run()
        self.on_hide()
        
class DriveSelection:
    DRIVE_NAME = 0
    DRIVE_SIZE = 1
    
    def __init__(self, builder, on_change_cb):
        self.builder = builder
        self.on_change_cb = on_change_cb
        
        self.drive_box = self.builder.get_object("drive_selection_box")
        self.drive_box.connect("changed", self.on_drive_changed)
        
        self.list_store = Gtk.ListStore(str, str)
        self.drive_box.set_model(self.list_store)
        
        self.renderer_name = Gtk.CellRendererText()
        self.renderer_size = Gtk.CellRendererText()
        
        self.drive_box.pack_start(self.renderer_name, True)
        self.drive_box.add_attribute(self.renderer_name, "text", self.DRIVE_NAME)
        
        self.drive_box.pack_start(self.renderer_size, False)
        self.drive_box.add_attribute(self.renderer_size, "text", self.DRIVE_SIZE)
        
        self.update_model()
        
    def update_model(self):
        self.list_store.clear()
        try:
            for dev in disk_operations.detect_devs():                
                size = utils.pretty_disk_size(disk_operations.size(dev))
                print("detected", dev, size)
                self.list_store.append([dev, size])
        except Exception as e:
            print(e)
            
    def get_drive(self):
        """return drive name or None"""
        iter_ = self.drive_box.get_active_iter()
        if iter_ is not None:
            return self.list_store.get_value(iter_, self.DRIVE_NAME)
            
    def on_drive_changed(self, *args):
        self.on_change_cb(self.get_drive())
            
    def enable(self):
        self.drive_box.set_sensitive(True)
            
    def disable(self):
        self.drive_box.set_sensitive(False)
        
class RunButton:
    TXT_RUN = "Test"
    TXT_STOP = "Stop"
    
    def __init__(self, builder, on_click_cb):
        self.builder = builder
        self.on_click_cb = on_click_cb
        
        self.button = self.builder.get_object("run_test_btn")
        self.button.connect("clicked", self.on_clicked)
        
        #self.disable()
        #self.set_txt_run()
        
    def on_clicked(self, *args):
        self.on_click_cb()
        
    def set_txt(self, txt):
        self.button.set_label(txt)
        
    def enable(self):
        self.button.set_sensitive(True)
            
    def disable(self):
        self.button.set_sensitive(False)    

class TestVisualization:
    CONTEXT_ID = 0
    def __init__(self, builder):  
        self.builder = builder
        
        self.progress_bar = self.builder.get_object("progress_bar")
        
        self.status_lbl = self.builder.get_object("status_lbl")
        self.status_extra_lbl = self.builder.get_object("status_extra_lbl")
        
        self.speed_lbl = self.builder.get_object("speed_lbl")
        self.progress_lbl = self.builder.get_object("progress_lbl")
        self.time_elp_lbl = self.builder.get_object("time_elapsed_lbl")
        self.time_left_lbl = self.builder.get_object("time_left_lbl")
        
        self.info_view = self.builder.get_object("info_view")
        self.info_buffer = self.info_view.get_buffer()
    
    @gtk_idle    
    def reset(self):
        self.progress_bar.set_fraction(0)
        
        self.status_lbl.set_text("")
        self.status_extra_lbl.set_text("")
        self.speed_lbl.set_text("")
        self.progress_lbl.set_text("")
        self.time_elp_lbl.set_text("")
        self.time_left_lbl.set_text("")

    
    @gtk_idle    
    def on_status_updated(self, old_status, new_status):
        status_name = testdisk.get_status_name(new_status)
        self.status_lbl.set_text(status_name)
    
    @gtk_idle    
    def on_error(self, err):
        enditer = self.info_buffer.get_end_iter()
        enditer = self.info_buffer.insert(enditer, os.linesep)
        
        self.info_buffer.insert(enditer, err)

    
    @gtk_idle    
    def on_progress(self, group_val, gr_start_sector, gr_num_sectors,
                 speed, percent, elapsed_time, left_time):
       
        self.progress_bar.set_fraction(percent / 100)
        
        self.speed_lbl.set_text(utils.pretty_speed(speed))
        self.progress_lbl.set_text(utils.pretty_percent(percent))
        self.time_elp_lbl.set_text(utils.pretty_time_diff(elapsed_time))
        self.time_left_lbl.set_text(utils.pretty_time_diff(left_time))
        self.status_extra_lbl.set_text("sector {}".format(gr_start_sector + gr_num_sectors))
  
    
    @gtk_idle    
    def on_device_changed(self, device):        
        self.reset() 
        
        device_info = report.info_generator(device).strip()
        self.info_buffer.set_text(device_info)
        
    @gtk_idle    
    def on_test_report(self, report):
        self.info_buffer.set_text(report.strip())

        
        
        

class Window:    
    
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP_NAME)
        self.builder.add_from_file(GLADE_FILE)
        
        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self.on_close)        
        
        self.drive_selection = DriveSelection(self.builder, self.on_drive_selection)
        self.run_button = RunButton(self.builder, self.on_run_clicked)
        self.test_visual_info = TestVisualization(self.builder)
        
        self.confirm_dialog = ConfirmationDialog(self.builder)   
        
        
        self.__init_vars()
        self.__init_menu()
        
    def __init_vars(self):
        self.drive = None        
        self.drive_test = None
        self.test_report = ("", "")
        self.first_sector_ind = 100000 #0
        self.last_sector_ind = 200000 #-1
        
    def __init_menu(self):
        self.menuitem_quit = self.builder.get_object("menuitem_quit")
        self.menuitem_save = self.builder.get_object("menuitem_save")
        self.menuitem_reload = self.builder.get_object("menuitem_reload")
        self.menuitem_sett = self.builder.get_object("menuitem_settings")
        self.menuitem_about = self.builder.get_object("menuitem_about")
        
        self.menuitem_quit.connect("activate", self.on_close)
        self.menuitem_save.connect("activate", self.on_report_save)
        self.menuitem_reload.connect("activate", 
                                     lambda *args: self.drive_selection.update_model())
        
        self.menuitem_sett.connect("activate", self.on_settings_edit)
        self.menuitem_about.connect("activate", 
                                    lambda *args: AboutDialog(self.builder).show())
        
    def show(self):
        self.window.show()
        Gtk.main()
        
    def on_close(self, *args):            
        self.confirm_dialog.confirm("Close the program?", "", Gtk.main_quit) 
        return True
        
    def on_drive_selection(self, new_drive):
        self.drive = new_drive
        
        self.test_visual_info.reset()
        if self.drive is not None:
            self.run_button.enable()
            self.test_visual_info.on_device_changed(self.drive)
            
    def on_settings_edit(self, *args):
        result = TestSettingsDialog(self.builder).show(self.first_sector_ind,
                                                        self.last_sector_ind)
        
        if result is not None:
            first_sector, last_sector = result
            self.first_sector_ind = first_sector
            self.last_sector_ind = last_sector
        
    def on_run_clicked(self):        
        if (self.drive is not None) and (self.drive_test is None):
            self.confirm_dialog.confirm("This will destroy all data on the drive.",
                                        "Start the test?", self.run_test)
            
        elif (self.drive_test is not None):
            self.confirm_dialog.confirm("All progress will be lost.", 
                                        "Stop the test?", self.stop_test)            
            
    def run_test(self):
        @async
        def start_test():
            self.drive_test = testdisk.DriveTest(self.drive, 
                                                 self.first_sector_ind, 
                                                 self.last_sector_ind)
            handler = self.drive_test.get_handler()           
            
            handler.add_callback("update", 
                                 self.test_visual_info.on_status_updated)            
            handler.add_callback("progress", self.test_visual_info.on_progress)
            
            handler.add_callback("error", self.on_test_error, self.drive)
            handler.add_callback("cancel", self.on_test_cancel, self.drive)
            handler.add_callback("finish", self.on_test_finish, self.drive)
            
            self.drive_test.test()  
            
            
        self.disallow_changes()
        start_test()
    
    def stop_test(self):
        self.drive_test.cancel()        
        
    def on_test_error(self, err, drive):
        self.test_visual_info.on_error(err)        
        self.allow_changes()
        
        ErrorDialog(self.builder).show(err)
        
        
    def on_test_cancel(self, bads, write_speed, read_speed, timer, drive):
        rep = report.report_generator(drive, bads, 
                                         write_speed, read_speed, timer)
        self.test_report = (drive, rep)
        self.test_visual_info.on_test_report(rep)
        self.allow_changes()
        
        
    def on_test_finish(self, bads, write_speed, read_speed, timer, drive):
        rep = report.report_generator(drive, bads, 
                                         write_speed, read_speed, timer)
        
        self.test_report = (drive, rep)
        self.test_visual_info.on_test_report(rep)        
        self.allow_changes()
        
        #save rep to tmp
        filesave.autosave(drive, rep)
        
    def on_report_save(self, *args):
        drive, rep = self.test_report
        
        fname = FileSaveDialog(self.builder).get_fname(filesave.get_fname(drive))
        
        if fname is not None:
            err = filesave.save(fname, rep)
            if err is not None:
                ErrorDialog(self.builder).show(err)
        
    def allow_changes(self):
        self.drive_test = None
        self.drive_selection.enable()
        self.run_button.set_txt("Test")
        self.menuitem_reload.set_sensitive(True)
        self.menuitem_sett.set_sensitive(True)
        
    def disallow_changes(self):
        self.drive_selection.disable()    
        self.run_button.set_txt("Stop")
        self.menuitem_reload.set_sensitive(False)
        self.menuitem_sett.set_sensitive(False)
        


if __name__ == "__main__":
    window = Window()
    window.show()    

