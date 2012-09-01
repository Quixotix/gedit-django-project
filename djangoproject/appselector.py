import imp
from gi.repository import GObject, Gtk

class AppSelector(Gtk.VBox):
    __gtype_name__ = "DjangoProjectAppSelector"
    def __init__(self, settings_module=None):
        Gtk.VBox.__init__(self, homogeneous=False, spacing=0) 
        self._model = Gtk.ListStore(GObject.TYPE_INT, GObject.TYPE_STRING)
        treeview = Gtk.TreeView.new_with_model(self._model)
        treeview.set_headers_visible(False)
        column = Gtk.TreeViewColumn("Apps")
        cell = Gtk.CellRendererToggle()
        cell.set_activatable(True)
        cell.connect("toggled", self.on_toggled, (self._model, 0))
        column.pack_start(cell, False)
        column.add_attribute(cell, "active", 0)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 1)
        treeview.append_column(column)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(treeview)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.show_all()
        self.pack_start(scrolled, True, True, 0)
        if settings_module:
            self.load_from_settings(settings_module)
    
    def load_from_settings(self, settings_module):
        [self._model.append((False, app,)) for app in settings_module.INSTALLED_APPS]
    
    def get_selected(self, short_names=True):
        selected = []
        if short_names:
            [selected.append(row[1][row[1].rfind(".")+1:]) for row in self._model if row[0]]
        else:
            [selected.append(row[1]) for row in self._model if row[0]]
        return selected
            
    def on_toggled(self, renderer, path, data=None):
        model, column = data
        model[path][column] = not model[path][column]
        
