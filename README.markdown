Gedit Django Project
====================

This is a plugin for [Gedit][2], the official text editor of the GNOME desktop
environment. This plugin is for Gedit versions 3 and above. **This plugin is NOT
compatible with Gedit 2.x**.

Gedit Django Project adds GUI interfaces for [django-admin.py and manage.py][1] 
commands within Gedit and simplifies working with Django projects.


Features
--------

* Create new projects (`manage.py startproject`) and apps (`manage.py startapp`).
* Supports *most* of the django-admin.py and manage.py commands.
* Run the Django development server (`manage.py runserver`) in a dedicated bottom panel.
* Run the interactive Python interpreter (`manage.py shell`) in a dedicated 
  bottom panel.
* Run the interactive database shell (`manage.py dbshell`) in a dedicated bottom
  panel.
* Management commands which produce usable output such as `dumpdata`, `sql`,
  `inspectdb` can optionally be loaded into a new Gedit document.
* Select appropriate apps from a GUI list of available apps for management
  commands which take a list of apps as parameters.


Installation
------------

1. Download the source code form this repository or using the `git clone` command.
2. Copy the files to the Gedit plugins directory `~/.local/share/gedit/plugins/`.
3. Restart Gedit.

#### For Example...

    git clone git://github.com/Quixotix/gedit-django-project.git
    cp djangoproject.plugin ~/.local/share/gedit/plugins/
    cp -R djangoproject ~/.local/share/gedit/plugins/
    



Screenshot
----------

![Screenshot showing Django menu and bottom panels in Gedit][3]

[1]: http://docs.djangoproject.com/en/dev/ref/django-admin/
[2]: http://www.gedit.org
[3]: http://www.micahcarrick.com/images/gedit-django-project/gedit-django-project.jpg


