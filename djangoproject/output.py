import os
import subprocess
import shlex
import logging
from gi.repository import GObject, Gtk, GLib, Pango

logging.basicConfig()
LOG_LEVEL = logging.ERROR
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

class OutputBox(Gtk.HBox):
    """
    A widget to display the output of running django commands.    
    """
    __gtype_name__ = "DjangoProjectOutputBox"
    
    def __init__(self):
        Gtk.HBox.__init__(self, homogeneous=False, spacing=4) 
        # configurable options
        self.cwd = None
        self._last_output = None
        scrolled = Gtk.ScrolledWindow()
        self._view = self._create_view()
        scrolled.add(self._view)
        self.pack_start(scrolled, True, True, 0)
        self.set_font("monospace 10")
        self.show_all()
    
    def _create_view(self):
        """ Create the gtk.TextView used for shell output """
        view = Gtk.TextView()
        view.set_editable(False)
        buff = view.get_buffer()
        buff.create_tag('bold', foreground='#7F7F7F', weight=Pango.Weight.BOLD)
        buff.create_tag('info', foreground='#7F7F7F', style=Pango.Style.OBLIQUE)
        buff.create_tag('error', foreground='red')
        return view
    
    def get_last_output(self):
        return self._last_output
        
    def set_font(self, font_name):
        font_desc = Pango.FontDescription(font_name)
        self._view.modify_font(font_desc)
        
    def run(self, command, cwd=None):
        """ Run a command inserting output into the gtk.TextView """
        self.insert("Running: ", 'info')
        self.insert("%s\n" % command, 'bold')
        args = shlex.split(command)
        output = None
        if cwd is None:
            cwd = self.cwd
        logger.debug(cwd)
        process = subprocess.Popen(args, 0, 
                                   shell=False, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   cwd=cwd)
        output = process.communicate()
        if output[0]:
            self.insert(output[0])
            self._last_output = output[0]
        if output[1]:
            self.insert(output[1], 'error')
        
        self.insert("\nExit: ", 'info')
        self.insert("%s\n\n" % process.returncode, 'bold')
        
        if output[1] and process.returncode <> 0:
            raise Exception(output[1])
    
    def insert(self, text, tag_name=None):
        """ Insert text, apply tag, and scroll to end iter """
        buff = self._view.get_buffer()
        end_iter = buff.get_end_iter()
        buff.insert(end_iter, "%s" % text)
        if tag_name:
            offset = buff.get_char_count() - len(text)
            start_iter = buff.get_iter_at_offset(offset)
            end_iter = buff.get_end_iter()
            buff.apply_tag_by_name(tag_name, start_iter, end_iter)
        while Gtk.events_pending():
            Gtk.main_iteration()
        self._view.scroll_to_iter(buff.get_end_iter(), 0.0, True, 0.0, 0.0)
        
