import os
import logging
from gi.repository import GObject, Gtk, Gedit, Gio, GdkPixbuf
from project import DjangoProject
from server import DjangoServer
from output import OutputBox
from shell import Shell
from appselector import AppSelector

logging.basicConfig()
LOG_LEVEL = logging.ERROR
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
SETTINGS_SCHEMA = "org.gnome.gedit.plugins.djangoproject"
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
STOCK_DBSHELL = "dbshell"
STOCK_SERVER = "server"
STOCK_PYTHON = "python"

class Plugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "GeditDjangoProjectPlugin"
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._project = None
        self._server = None
        self._output = None
        self._shell = None
        self._dbshell = None
        self._install_stock_icons()
        # TODO: The admin and manage commands should configurable so that they
        # could be changed to various virtual environments. Even better would
        # be able to specify the commands on a per-project basis.        
        #self._admin_cmd = "/home/micah/.virtual-environments/django-1.4/bin/django-admin.py" 
        #self._manage_cmd = "/home/micah/.virtual-environments/django-1.4/bin/python manage.py"
        self._admin_cmd = "django-admin.py" 
        self._manage_cmd = "python manage.py"
        self._font = "monospace 10"
    
    def _add_dbshell_panel(self):
        """ Adds a database shell to the bottom pane. """
        logger.debug("Adding database shell panel.")
        self._dbshell = Shell()
        self._dbshell.set_font(self._font)
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._dbshell, "DjangoDbShell", 
                                       "Database Shell", STOCK_DBSHELL)
        self._setup_dbshell_panel()
                                       
    def _add_output_panel(self):
        """ Adds a widget to the bottom pane for django command output. """
        self._output = OutputBox()
        self._output.set_font(self._font)
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._output, "DjangoOutput", 
                                       "Django Output", Gtk.STOCK_EXECUTE)
        try:
            command = "%s --version" % (self._admin_cmd)
            self._output.run(command)
        except:
            pass
        
    def _add_server_panel(self, cwd=None):
        """ Adds a VTE widget to the bottom pane for development server. """
        logger.debug("Adding server panel.")
        self._server = DjangoServer()
        self._server.set_font(self._font)
        self._server.command = "%s runserver" % (self._manage_cmd)
        if cwd:
            self._server.cwd = cwd
        self._server.connect("server-started", self.on_server_started)
        self._server.connect("server-stopped", self.on_server_stopped)
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._server, "DjangoServer", 
                                       "Django Server", STOCK_SERVER)
        self._setup_server_panel()
    
    def _add_shell_panel(self):
        """ Adds a python shell to the bottom pane. """
        logger.debug("Adding shell.")
        self._shell = Shell()
        self._shell.set_font(self._font)
        panel = self.window.get_bottom_panel()
        panel.add_item_with_stock_icon(self._shell, "DjangoShell", 
                                       "Python Shell", STOCK_PYTHON)
        self._setup_shell_panel()
                                       
    def _add_ui(self):
        """ Merge the 'Django' menu into the Gedit menubar. """
        ui_file = os.path.join(DATA_DIR, 'menu.ui')
        manager = self.window.get_ui_manager()
        
        # global actions are always sensitive
        self._global_actions = Gtk.ActionGroup("DjangoGlobal")
        self._global_actions.add_actions([
            ('Django', None, "_Django", None, None, None),
            ('NewProject', Gtk.STOCK_NEW, "_New Project...", 
                "<Shift><Control>N", "Start a new Django project.", 
                self.on_new_project_activate),
            ('OpenProject', Gtk.STOCK_OPEN, "_Open Project", 
                "<Shift><Control>O", "Open an existing Django project.", 
                self.on_open_project_activate),
            ('NewApp', Gtk.STOCK_NEW, "New _App...", 
                "<Shift><Control>A", "Start a new Django application.", 
                self.on_new_app_activate),
        ])
        self._global_actions.add_toggle_actions([
            ('ViewServerPanel', None, "Django _Server", 
                None, "Add the Django development server to the bottom panel.", 
                self.on_view_server_panel_activate, True),
            ('ViewPythonShell', None, "_Python Shell", 
                None, "Add a Python shell to the bottom panel.", 
                self.on_view_python_shell_panel_activate, False),
            ('ViewDbShell', None, "_Database Shell", 
                None, "Add a Database shell to the bottom panel.", 
                self.on_view_db_shell_panel_activate, False),
        ])
        manager.insert_action_group(self._global_actions)       
        
        # project actions are sensitive when a project is open
        self._project_actions = Gtk.ActionGroup("DjangoProject")
        self._project_actions.add_actions([
            ('CloseProject', Gtk.STOCK_CLOSE, "_Close Project...", 
                "", "Close the current Django project.", 
                self.on_close_project_activate),
            ('Manage', None, "_Manage", None, None, None),
            ('SyncDb', Gtk.STOCK_REFRESH, "_Synchronize Database", None, 
                "Creates the database tables for all apps whose tables have not already been created.", 
                self.on_manage_command_activate),
            ('Cleanup', None, "_Cleanup", None, 
                "Clean out old data from the database.", 
                self.on_manage_command_activate),
            ('DiffSettings', None, "Di_ff Settings", None, 
                "Displays differences between the current settings and Django's default settings.", 
                self.on_manage_command_activate),
            ('InspectDb', None, "_Inspect Database", None, 
                "Introspects the database and outputs a Django model module.", 
                self.on_manage_command_activate),
            ('Flush', None, "_Flush", None, 
                "Returns the database to the state it was in immediately after syncdb was executed.", 
                self.on_manage_command_activate),
                # all clear custom flush
            ('Sql', None, "S_QL...", None, 
                "Prints the CREATE TABLE SQL statements for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('SqlAll', None, "SQL _All...", None, 
                "Prints the CREATE TABLE and initial-data SQL statements for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('SqlClear', None, "SQL C_lear...", None, 
                "Prints the DROP TABLE SQL statements for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('SqlCustom', None, "SQL C_ustom...", None, 
                "Prints the custom SQL statements for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('SqlFlush', None, "S_QL Flush", None, 
                "Prints the SQL statements that would be executed for the flush command.", 
                self.on_manage_command_activate),
            ('SqlIndexes', None, "SQL _Indexes...", None, 
                "Prints the CREATE INDEX SQL statements for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('SqlSequenceReset', None, "SQL Sequence Rese_t...", None, 
                "Prints the SQL statements for resetting sequences for the given app name(s).", 
                self.on_manage_app_select_command_activate),
            ('Validate', None, "_Validate", None, 
                "Validates all installed models.", 
                self.on_manage_command_activate),
            ('LoadData', None, "_Load Data...", None, 
                "Loads the contents of fixtures into the database.", 
                self.on_manage_load_data_activate),
            ('DumpData', None, "_Dump Data...", None, 
                "Outputs all data in the database associated with the named application(s).", 
                self.on_manage_app_select_command_activate),
        ])
        self._project_actions.add_toggle_actions([
            ('RunServer', None, "_Run Development Server", 
                "<Shift>F5", "Start/Stop the Django development server.", 
                self.on_manage_runserver_activate, False),
        ])
        self._project_actions.set_sensitive(False)
        manager.insert_action_group(self._project_actions)   
        
        self._ui_merge_id = manager.add_ui_from_file(ui_file)
        manager.ensure_update()
    
    def close_project(self):
        self._project = None
        self._server.stop()
        self._server.cwd = None
        self._server.refresh_ui()
        if self._shell:
            self._shell.kill()
        if self._dbshell:
            self._dbshell.kill()
        self._project_actions.set_sensitive(False)
        self._update_run_server_action()
    
    def confirmation_dialog(self, message):
        """ Display a very basic informative Yes/No dialog. """
        dialog = Gtk.MessageDialog(self.window,
                                   Gtk.DialogFlags.MODAL | 
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO,  
                                   message)
        dialog.set_title("Confirm")
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES: 
            return True
        else:
            return False
            
    def do_activate(self):
        logger.debug("Activating plugin.")
        self._add_ui()
        self._add_output_panel()
        self._add_server_panel()

    def do_deactivate(self):
        logger.debug("Deactivating plugin.")
        self._remove_ui()
        self._remove_output_panel()
        self._remove_server_panel()
        self._remove_shell_panel()
        self._remove_dbshell_panel()

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
    
    def _has_settings_schema(self):
        schemas = Gio.Settings.list_schemas()
        if not SETTINGS_SCHEMA in schemas:
            return False
        else:
            return True
    
    def _install_stock_icons(self):
        """ Register custom stock icons used on the tabs. """
        logger.debug("Installing stock icons.")
        icons = (STOCK_PYTHON, STOCK_DBSHELL, STOCK_SERVER)
        factory = Gtk.IconFactory()
        for name in icons:
            filename = name + ".png"
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(os.path.join(DATA_DIR, "icons", filename))
            iconset = Gtk.IconSet.new_from_pixbuf(pixbuf)
            factory.add(name, iconset)
        factory.add_default()
    
    def new_app(self, path, name):
        """ Runs the 'startapp' Django command. """ 
        try:
            self.run_admin_command("startapp %s" % name, path)
        except Exception as e:
            self.error_dialog(str(e))
            
    def new_dialog(self, title):
        filename = os.path.join(DATA_DIR, 'dialogs.ui')
        path = name = None
        builder = Gtk.Builder()
        try:
            builder.add_from_file(filename)
        except Exception as e:
            logger.error("Failed to load %s: %s." % (filename, str(e)))
            return 
        dialog = builder.get_object('new_dialog')
        if not dialog:
            logger.error("Could not find 'new_dialog' widget in %s." % filename)
            return
        dialog.set_transient_for(self.window)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_title(title)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name_widget = builder.get_object('name')
            project_widget = builder.get_object('directory')
            name = name_widget.get_text()
            path = project_widget.get_filename()
        dialog.destroy()
        
        return (name, path)
    
    def new_project(self, path, name):
        """ Runs the 'startproject' Django command and opens the project. """ 
        try:
            self.run_admin_command("startproject %s" % name, path)
        except Exception as e:
            self.error_dialog(str(e))
            return
        
        self.open_project(os.path.join(path, name))
    
    def new_tab_from_output(self):
        message = "Do you want to create a new document with the output?"
        if not self.confirmation_dialog(message):
            return
        tab = self.window.create_tab(False)
        buff = tab.get_view().get_buffer()
        end_iter = buff.get_end_iter()
        buff.insert(end_iter, self._output.get_last_output())
        self.window.set_active_tab(tab)
            
    def on_close_project_activate(self, action, data=None):
        self.close_project()
   
    def on_manage_command_activate(self, action, data=None):
        """ Handles simple manage.py actions. """
        command = action.get_name().lower()
        if command in ('syncdb', 'flush'):
            command += ' --noinput'
        try:
            self.run_management_command(command)
        except:
            pass # errors show up in output
        
        if command in ('inspectdb', 'sqlflush', 'diffsettings'):
            self.new_tab_from_output()
    
    def on_manage_app_select_command_activate(self, action, data=None):
        dialog = Gtk.Dialog("Select apps...",
                            self.window,
                            Gtk.DialogFlags.MODAL | 
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                            Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_size(300, 200)
        selector = AppSelector()
        selector.show_all()
        try:
            selector.load_from_settings(self._project.get_settings_filename())
        except Exception as e:
            self.error_dialog("Error getting app list: %s" % str(e))
        box = dialog.get_content_area()
        box.set_border_width(10)
        box.pack_start(selector, True, True, 0)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = selector.get_selected()
            command = action.get_name().lower()
            full_command = "%s %s" % (command, " ".join([f for f in files]) )
            try:
                self.run_management_command(full_command)
            except Exception as e:
                self.error_dialog(str(e))
        dialog.destroy()
        
        # only after the dialog is destroyed do we prompt them for a new tab
        if response == Gtk.ResponseType.OK:
            if command[:3] == "sql" or command in ('dumpdata'):
                self.new_tab_from_output()
        
    def on_manage_load_data_activate(self, action, data=None):
        """ Prompt user for fixtures to load into database. """
        dialog = Gtk.FileChooserDialog("Select fixtures...",
                                       self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                       Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        if self._project:
            dialog.set_filename(self._project.get_path())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_files()
            command = "loaddata "+" ".join([f.get_path() for f in files]) 
            try:
                self.run_management_command(command)
            except Exception as e:
                self.error_dialog(str(e))
            
        dialog.destroy()
         
    def on_manage_runserver_activate(self, action, data=None):
        """ Run Django development server. """
        if not self._server:
            return
        try:
            if not action.get_active() and self._server.is_running():
                self._server.stop()
            elif action.get_active() and not self._server.is_running():
                self._server.start()
        except Exception as e:
            self.error_dialog(str(e))
            return
        
    def on_new_app_activate(self, action, data=None):
        """ Prompt user for new app name and directory """
        name, path = self.new_dialog("New Django App")
        if name and path:
            self.new_app(path, name)
            
    def on_new_project_activate(self, action, data=None):
        """ Prompt user for new project name and directory """
        name, path = self.new_dialog("New Django Project")
        if name and path:
            self.new_project(path, name)
    
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
        panel = self.window.get_bottom_panel()
        panel.activate_item(self._server)
                
    def on_server_stopped(self, server, pid, data=None):
        self._project_actions.get_action("RunServer").set_active(False)
    
    def on_view_db_shell_panel_activate(self, action, data=None):
        """ Show/Hide database shell from main menu. """
        if action.get_active():
            self._add_dbshell_panel()
        else:
            self._remove_dbshell_panel()
        
    def on_view_python_shell_panel_activate(self, action, data=None):
        """ Show/Hide python shell from main menu. """
        if action.get_active():
            self._add_shell_panel()
        else:
            self._remove_shell_panel()
        
    def on_view_server_panel_activate(self, action, data=None):
        """ Show/Hide development server from main menu. """
        if action.get_active():
            self._add_server_panel()
        else:
            self._remove_server_panel()
        self._update_run_server_action()
        
    def open_project(self, path):
        logger.debug("Opening Django project: %s" % path)
        if self._project:
            self.close_project()
        try:
            self._project = DjangoProject(path)
        except IOError as e:
            self.error_dialog("Could not open project: %s" % str(e))
            return

        self._output.cwd = self._project.get_path()
        self._setup_server_panel()
        self._setup_shell_panel()
        self._setup_dbshell_panel()
        self._project_actions.set_sensitive(True)
        self._update_run_server_action()

    def _setup_dbshell_panel(self):
        if self._dbshell and self._project:
            self._dbshell.cwd = self._project.get_path()
            self._dbshell.command = "%s dbshell" % self._manage_cmd
            self._dbshell.run()
    
    def _setup_server_panel(self):
        if self._server and self._project:
            self._server.cwd = self._project.get_path()
            self._server.refresh_ui()
        
    def _setup_shell_panel(self):
        if self._shell and self._project:
            self._shell.cwd = self._project.get_path()
            self._shell.command = "%s shell" % self._manage_cmd
            self._shell.run()
        
    def _remove_output_panel(self):
        """ Remove the output box from the bottom panel. """
        logger.debug("Removing output panel.")
        if self._output:
            self._remove_panel(self._output)
            self._output = None
    
    def _remove_panel(self, item):
        panel = self.window.get_bottom_panel()
        panel.remove_item(item)
        
    def _remove_server_panel(self):
        """ Stop and remove development server panel from the bottom panel. """
        if self._server:
            logger.debug("Removing server panel.")
            self._server.stop()
            self._remove_panel(self._server)
            self._server = None
            
    
    def _remove_shell_panel(self):
        """ Remove python shell from bottom panel. """
        if self._shell:
            logger.debug("Removing shell panel.")
            self._remove_panel(self._shell)
            self._shell = None
    
    def _remove_dbshell_panel(self):
        """ Remove database shell from bottom panel. """
        if self._dbshell:
            logger.debug("Removing database shell panel.")
            self._remove_panel(self._dbshell)
            self._dbshell = None
            
    def _remove_ui(self):
        """ Remove the 'Django' menu from the the Gedit menubar. """
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_merge_id)
        manager.remove_action_group(self._global_actions)
        manager.remove_action_group(self._project_actions)
        manager.ensure_update()
    
    def run_admin_command(self, command, path=None):
        """ Run a django-admin.py command in the output panel. """
        self.window.get_bottom_panel().activate_item(self._output)
        full_command = "%s %s" % (self._admin_cmd, command)
        original_cwd = self._output.cwd
        self._output.cwd = path
        self._output.run(full_command)
        self._output.cwd = original_cwd
            
    def run_management_command(self, command):
        """ Run a manage.py command in the output panel. """
        self.window.get_bottom_panel().activate_item(self._output)
        full_command = "%s %s" % (self._manage_cmd, command)
        self._output.run(full_command)
    
    def _update_run_server_action(self):
        if not self._server or not self._project:
            self._project_actions.get_action("RunServer").set_sensitive(False)
        else:
            self._project_actions.get_action("RunServer").set_sensitive(True)
  
        
