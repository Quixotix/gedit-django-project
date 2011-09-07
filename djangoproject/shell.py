import os
import signal
import subprocess
import shlex
import logging
from gi.repository import GObject, Gtk, Vte, GLib

logging.basicConfig()
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

class Shell(Gtk.HBox):
    """
    A terminal widget setup to run as shell. The command will automatically
    re-start when it is killed.
    """
    __gtype_name__ = "DjangoProjectShell"
    
    def __init__(self):
        Gtk.HBox.__init__(self, homogeneous=False, spacing=0)  
        self.command = None
        self.cwd = None
        self._pid = None
        self._vte = Vte.Terminal()
        self._vte.set_size(self._vte.get_column_count(), 5)
        self._vte.set_size_request(200, 50)
        self._vte.set_font_from_string("monospace 10")
        self._vte.connect("child-exited", self.on_child_exited)
        self.pack_start(self._vte, True, True, 0)
        scrollbar = Gtk.Scrollbar.new(Gtk.Orientation.VERTICAL, self._vte.get_vadjustment())
        self.pack_start(scrollbar, False, False, 0)
        self.show_all()
            
    def on_child_exited(self, vte, data=None):
        logger.debug("Child exited: %s" % self._pid);
        if self._running:
            self.run()

    def run(self):
        self._running = True
        args = shlex.split(self.command)
        self._pid = self._vte.fork_command_full(Vte.PtyFlags.DEFAULT, 
                                                self.cwd,
                                                args,
                                                None,
                                                GLib.SpawnFlags.SEARCH_PATH,
                                                None, 
                                                None)[1]                         
        logger.debug("Running %s (pid %s)" % (self.command, self._pid))
    
    def kill(self):
        self._running = False
        if self._pid:
            os.kill(self._pid, signal.SIGKILL)
        self._vte.reset(False, True)
        
    def set_font(self, font_name):
        self._vte.set_font_from_string(font_name)
        
