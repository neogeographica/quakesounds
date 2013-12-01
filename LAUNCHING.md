Launching quakesounds
---------------------

The quakesounds application is the file named "quakesounds.py". The
distribution zipfile that you downloaded will have other stuff in it, but only
"quakesounds.py" is necessary for running the application.

quakesounds is a Python application, so if you are already familiar with
running Python scripts you don't have anything new to see here, except to note
that you can set `pause_on_exit` to True in the quakesounds configuration if
you're spawning a console window that disappears before you can read it.
(More about configuration in README.md.)

### Manual launch

One way to run quakesounds is to manually run it from a command prompt.
(Windows command prompt, OS X terminal, Linux shell, etc.)

This is straightforward if your Python program is on your executables path. On
Windows you also want the ".py" file extension to be associated with Python.
Normally these things will be true... the Python installer will take care of
getting things set up correctly.

So if your "quakesounds.py" file is in the directory "C:\Users\Me\Desktop",
you could run quakesounds like so:

    C:\Users\Me\Desktop\quakesounds.py

If you have placed "quakesounds.py" in a directory that is in your executables
path, you don't even have to specify what directory it is in; just enter:

    quakesounds.py

Now if you don't have Python in your executables path, or if on Windows you
don't have ".py" files associated with Python, then the above examples
wouldn't work. In that case you'll have to explicitly run Python and give it
the path to quakesounds.py, like so:

    C:\Python27\python.exe C:\Users\Me\Desktop\quakesounds.py

### GUI launch

In some cases it may also be possible to launch quakesounds by activating the
icon for "quakesounds.py" in your window manager (e.g. double-click on it).
This method also requires that Python is on your executables path, and on
Windows that ".py" files are associated with Python.

Running quakesounds in this way will temporarily create a window to contain
the messages printed during the run, and that window will go away when the
program is done. If you want to keep the window up to read the messages,
you'll need to change the quakesounds configuration to set `pause_on_exit` to
True. (See the README.md file for more about configuration.)

It's possible to create shortcuts to launch quakesounds with specific
command-line arguments and/or a specific working directory. That can be
useful, but it's beyond the scope of this readme.

### Special note for PowerShell

If you're using PowerShell on Windows, then when you manually run a Python
script it will behave as if you had launched it through the GUI.

If you want it to instead print messages inside the PowerShell window, then
you need to modify the PATHEXT environment variable to include the .PY
file extension. You can make this change for the current PowerShell by
entering this:

    $env:PATHEXT += ";.PY"

To make the change permanently for all future PowerShell windows, you'll need
to use the appropriate Windows control panel to edit the value of the
PATHEXT environment variable. This isn't difficult, but it's another thing
beyond the scope of this readme.
