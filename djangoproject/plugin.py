import os
import logging
from gi.repository import GObject, Gtk, Gedit
from project import DjangoProject
from server import DjangoServer
from output import OutputBox

logging.basicConfig()
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class Plugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "GeditDjangoProjectPlugin"
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._server = None
        
        # TODO: move to configuration settings
        self._admin_cmd = "django-admin" # django-admin.py on some systems
        self._manage_cmd = "python manage.py"
        
    def _add_output_panel(self):
        """ Adds a widget to the bottom pane for django command output. """
        self._output = OutputBox()
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._output, "DjangoOutput", 
                                       "Django Output", Gtk.STOCK_EXECUTE)
        
    def _add_server_panel(self, cwd=None):
        """ Adds a VTE widget to the bottom pane for development server. """
        logger.debug("Adding server panel.")
        self._server = DjangoServer()
        self._server.command = "%s runserver" % (self._manage_cmd)
        if cwd:
            self._server.cwd = cwd
        self._server.connect("server-started", self.on_server_started)
        self._server.connect("server-stopped", self.on_server_stopped)
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._server, "DjangoServer", 
                                       "Django Server", Gtk.STOCK_NETWORK)
        
    def _add_ui(self):
        """ Merge the 'Django' menu into the Gedit menubar. """
        ui_file = os.path.join(DATA_DIR, 'menu.ui')
        manager = self.window.get_ui_manager()
        
        # global actions are always sensitive
        self._global_actions = Gtk.ActionGroup("DjangoGlobal")
        self._global_actions.add_actions([
            ('Django', None, "_Django", None, None, None),
            ('NewProject', Gtk.STOCK_NEW, "_New Project", 
                "<Shift><Control>N", "Start a new Django project.", 
                self.on_new_project_activate),
            ('OpenProject', Gtk.STOCK_OPEN, "_Open Project", 
                "<Shift><Control>O", "Open an existing Django project.", 
                self.on_open_project_activate),
        ])
        manager.insert_action_group(self._global_actions)       
        
        # project actions are sensitive when a project is open
        self._project_actions = Gtk.ActionGroup("DjangoProject")
        self._project_actions.add_actions([
            ('CloseProject', Gtk.STOCK_CLOSE, "_Close Project...", 
                "<Shift><Control>W", "Close the current Django project.", 
                self.on_close_project_activate),
            ('Manage', None, "_Manage", None, None, None),
            #('SyncDb', gtk.STOCK_REFRESH, "_Synchronize Database", 
            #    None, "Synchronize database", self.on_manage_syncdb_activate),
        ])
        self._project_actions.add_toggle_actions([
            ('RunServer', Gtk.STOCK_CONNECT, "_Run Development Server", 
                None, "Start/Stop the Django development server.", 
                self.on_manage_runserver_activate, False),
        ])
        self._project_actions.set_sensitive(False)
        manager.insert_action_group(self._project_actions)   
        
        self._ui_merge_id = manager.add_ui_from_file(ui_file)
        manager.ensure_update()
        
    def do_activate(self):
        logger.debug("Activating plugin.")
        self._add_ui()
        self._add_output_panel()
        self._add_server_panel()
        # TEMPORARY
        #self.open_project("/home/micah/Documents/Quixotix/projects/quix.django.comments/demo")

    def do_deactivate(self):
        logger.debug("Deactivating plugin.")
        self._remove_ui()
        self._remove_output_panel()
        self._remove_server_panel()

    def do_update_state(self):
        pass
    
    def error_dialog(self, message):
        """ Display a very basic error dialog. """
        logger.warn(message)
        dialog = Gtk.MessageDialog(self.window,
                                   Gtk.DialogFlags.MODAL | 
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 
                                   message)
        dialog.set_title("Error")
        dialog.run()
        dialog.destroy()
    
    def new_project(self, path, name):
        """ Runs the 'startproject' Django command and opens the project. """ 
        try:
            command = "%s startproject %s" % (self._admin_cmd, name)
            self._output.run(command, path)
        except Exception as e:
            self.error_dialog(str(e))
            return
        
        self.open_project(os.path.join(path, name))
        
    def on_close_project_activate(self, action, data=None):
        pass
        
    def on_manage_runserver_activate(self, action, data=None):
        try:
            if not action.get_active() and self._server.is_running():
                self._server.stop()
            elif action.get_active() and not self._server.is_running():
                self._server.start()
                panel = self.window.get_bottom_panel()
                panel.activate_item(self._server)
        except Exception as e:
            self.error_dialog(str(e))
            return
    
    def on_new_project_activate(self, action, data=None):
        self.new_project("/home/micah/tmp", "testproject")
        
    def on_open_project_activate(self, action, data=None):
        """ Prompt the user for the Django project directory. """
        path = None
        dialog = Gtk.FileChooserDialog("Select project folder...", self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK: 
            path = dialog.get_filename()
        dialog.destroy()
        if path:
            self.open_project(path)
    
    def on_server_started(self, server, pid, data=None):
        self._project_actions.get_action("RunServer").set_active(True)
    
    def on_server_stopped(self, server, pid, data=None):
        self._project_actions.get_action("RunServer").set_active(False)
        
    def open_project(self, path):
        logger.debug("Opening Django project: %s" % path)
        try:
            self._project = DjangoProject(path)
        except IOError as e:
            self.error_dialog("Could not open project: %s" % str(e))
            return
        #self._add_server_panel(self._project.get_path())
        self._server.cwd = self._project.get_path()
        self._server.refresh_ui()
        self._project_actions.set_sensitive(True)

    def _remove_output_panel(self):
        """ Remove the output box from the bottom panel. """
        logger.debug("Removing output panel.")
        if self._output:
            panel = self.window.get_bottom_panel()
            panel.remove_item(self._output)
            self._output = None
        
    def _remove_server_panel(self):
        """ Stop and remove development server panel from the bottom panel. """
        if self._server:
            logger.debug("Removing server panel.")
            self._server.stop()
            panel = self.window.get_bottom_panel()
            panel.remove_item(self._server)
            self._server = None
            
    def _remove_ui(self):
        """ Remove the 'Django' menu from the the Gedit menubar. """
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_merge_id)
        manager.remove_action_group(self._global_actions)
        manager.remove_action_group(self._project_actions)
        manager.ensure_update()
    
    
