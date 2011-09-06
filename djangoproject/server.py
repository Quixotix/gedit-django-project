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

class DjangoServer(Gtk.HBox):
    """
    A terminal widget setup to run the Django development server management
    command providing Start/Stop button.
    
    Start and stop the server by calling start() and stop() methods.
    
    Connect to the "server-started" and "server-stopped" signals to update UI as
    the server may stop for any number of reasons, including errors in Django
    code, pressing <CTRL+C>, or the stop button on the widget.
    """
    __gtype_name__ = "DjangoServer"
    __gsignals__ = {
        "server-started": 
            (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, 
            (GObject.TYPE_PYOBJECT,)),
        "server-stopped": 
            (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, 
            (GObject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self):
        Gtk.HBox.__init__(self, homogeneous=False, spacing=0)  
        self.command = "python manage.py runserver"
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
        self._button = Gtk.Button()
        self._button.connect("clicked", self.on_button_clicked)
        box = Gtk.VButtonBox()
        box.set_border_width(5)
        box.set_layout(Gtk.ButtonBoxStyle.START)
        box.add(self._button)
        self.pack_start(box, False, False, 0)
        self._start_icon = Gtk.Image.new_from_stock(Gtk.STOCK_EXECUTE, Gtk.IconSize.BUTTON)
        self._stop_icon = Gtk.Image.new_from_stock(Gtk.STOCK_STOP, Gtk.IconSize.BUTTON)
        self.refresh_ui()
        self.show_all()
 
    def is_running(self):
        if self._pid is not None:
            return True
        else:
            return False
    
    def on_button_clicked(self, widget=None, data=None):
        if self.is_running():
            self.stop()
        else:
            self.start()
            
    def on_child_exited(self, vte, data=None):
        pid = self._pid
        self._pid = None
        self.refresh_ui()
        self.emit("server-stopped", pid)
        logger.debug("Development server stopped (pid %s)" % pid)
    
    def start(self):
        if self.is_running():
            return
        args = shlex.split(self.command)
        self._pid = self._vte.fork_command_full(Vte.PtyFlags.DEFAULT, 
                                                self.cwd,
                                                args,
                                                None,
                                                GLib.SpawnFlags.SEARCH_PATH,
                                                None, 
                                                None)[1]  
        self.refresh_ui()                        
        self.emit("server-started", self._pid)
        logger.debug("Development server started (pid %s)" % self._pid)
        
    def stop(self):
        if self.is_running():
            os.kill(self._pid, signal.SIGKILL)
    
    def refresh_ui(self):
        if self.is_running():
            self._button.set_image(self._stop_icon)
            self._button.set_label("Stop")
        else:
            self._button.set_image(self._start_icon)
            self._button.set_label("Start")
        
        self._button.set_sensitive(bool(self.cwd))
            
