import os
import imp
import sys
import logging

logging.basicConfig()
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

class DjangoProject(object):

    def __init__(self, path):
        self.set_path(path)
    
    def get_path(self):
        """
        Return the path to the django project (where settings.py and manage.py 
        are found).
        """
        return self._path
        
    def set_path(self, path):
        """
        Set Path
        
        Set the full filesystem path to where the Django project files are stored
        or raise IOError if the path does not exist or if settings.py or manage.py
        cannot be found in the path.
        """
        if not os.path.exists(path):
            raise IOError("Django project directory does not exist: %s" % path)
        
        # find manage.py
        manage = os.path.join(path, 'manage.py')
        if not os.path.isfile(manage):
            raise IOError("Django manage file does not exist: %s" % manage)

        # find settings.py in Django >= 1.4
        settings = os.path.join(path, os.path.basename(path), 'settings.py')
        if not os.path.isfile(settings):
            # find settings.py in Django < 1.4
            settings = os.path.join(path, 'settings.py')
            if not os.path.isfile(settings):
                raise IOError("Django settings file does not exist: %s" % settings)

        self._path = path
        self._settings = settings
        self._manage = manage
    
    def get_settings_filename(self):
        return self._settings
    
    def get_manage_filename(self):
        return self._manage
        
