quakesounds: audio processing pipeline for Quake sound samples
==============================================================

**Current release:** [1.0](https://github.com/neogeographica/quakesounds/releases)

quakesounds is a utility for easily ripping sound effects out of Quake pak
files and pushing them through a sequence of audio processing effects.

The idea originated when I had the urge to use a few Quake-related noises as
alert sounds on my phone. That involved a surprising amount of work to find
good alert-sound candidates and then extract, rename, noise-reduce,
format-convert, and gain-normalize them. So I thought it might be neat if I
gave other folks a shortcut for all that.

Distributing the processed files was illegal-ish though, so I put together a
utility that you can throw your own pak files at and have processed sounds pop
out the other end, to do with as you will.

The project took on extra life as an excuse to see what was involved in a
complete/proper open-source user-configurable release of a modestly-scoped
Python application. So the end result is somewhat overpowered for its original
purposes. While it should still be easy to use this to just crank out a few
ringtones, it's also data-driven to the point where you could use it to apply
an arbitrary processing pipeline, using any external utilities that you like,
to anything contained in a pak file.


Prerequisites
-------------

You'll need to have Python 2.6 or 2.7 installed in order to run quakesounds.
If you are working on Linux or OS X, you probably already have this; if on
Windows, probably not (unless you've already gone to the trouble of installing
it yourself). In any case, if you don't have Python then you can [go get a
Python installer for your platform of choice](http://python.org/download/).
**Note that you will specifically need Python version 2.6 or 2.7**;
quakesounds doesn't yet support any other Python versions.

Once you've installed Python, the next issue is whether you need to install
any sound-processing utilities for quakesounds to control. All of the default
processing pipelines in quakesounds use [SoX](http://sox.sourceforge.net/),
and the pipeline for creating m4r files (iOS alert/ringtone sounds) uses both
SoX and [ffmpeg](http://www.ffmpeg.org/). But before you go downloading and
installing those, consider:

* If you are going to run on OS X (64-bit) or Windows, you can choose to use a
build of the quakesounds application that includes internally-bundled versions
of SoX and ffmpeg. You won't need to worry about installing them yourself.

* If you are on some other platform -- like Linux or 32-bit OS X -- then you
*will* need to separately install SoX and/or ffmpeg if you are going to do any
processing that uses them.

* If you intend to use audio processing utilities other than SoX or ffmpeg,
quakesounds can certainly accomodate that, but you'll have to install those
utilities separately.

That's about it. quakesounds also depends on the Python modules
[expak](https://github.com/neogeographica/expak) and pkg_resources, but if you
don't have the module already installed on your system then quakesounds will
automatically use an internally-bundled version of that module.


Choosing your quakesounds flavor
--------------------------------

You can get a quakesounds distribution at the [quakesounds releases page on
GitHub](https://github.com/neogeographica/quakesounds/releases).

quakesounds is a Python 2.6/2.7 application, so it will run on any system that
has the necessary Python version. As mentioned above though, you can choose to
download a build of quakesounds that has internally-bundled sound utilities
for convenience. Those utilities are built specifically for OS X or for
Windows, so that's why there are unique quakesounds download options for OS X
and for Windows.

To be clear: the quakesounds application itself will still run on any platform,
regardless of which flavor you download. You can change the configuration so
that it doesn't use the internal versions of the utilities, and make it use
more appropriate external utilities that you have installed. But obviously the
internally-bundled utilities will just be dead weight if you're not going to
use them on the OS for which they were built.

Note for power users: even if you're running on Windows or OS X, you may want
to choose the "lightweight" build with no bundled utilities, and just set up
your sound utilities externally in the exact manner that you prefer. This will
also make quakesounds start up a little faster (although the difference is not
really noticeable on a modern PC with an SSD.)


Launching
---------

The quakesounds application is the file named "quakesounds.py". The
distribution zipfile that you downloaded will have other stuff in it, but only
"quakesounds.py" is necessary for running the application.

quakesounds is a Python application, so if you are already familiar with
running Python scripts you don't have anything new to see here, except to note
that you can set `pause_on_exit` to True in the quakesounds configuration if
you're spawning a console window that disappears before you can read it.
(More about configuration below.)

For everyone not familiar with running Python scripts, please see the
LAUNCHING.md file for the rundown.


Quickstart
----------

quakesounds is very configurable, but you can ignore a lot of the details for
starters. This quickstart section will walk through a few steps that will
generated some converted sounds using the default settings.

For the example command lines in this section, I'll assume that you're on
Windows, that Python is on your executables path, that "quakesounds.py" is in
your current working directory, and that you're running it manually from a
command prompt. If not, adjust the examples as necessary... the important
thing here is not going to be exactly how quakesounds is launched, but rather
what command-line arguments (if any) we give it.

### The config file

The most important thing to know is that quakesounds will look for its
configuration in a file named "quakesounds.cfg". That config file contains the
settings that control the behavior of quakesounds, although settings can also
be specified on the command line to add to or change the settings taken from
the file.

quakesounds expects the "quakesounds.cfg" file to be in the current working
directory. If you're manually running quakesounds then the working directory
is whatever directory you're in. If you run quakesounds by double-clicking an
icon, then the working directory is normally whatever directory
"quakesounds.py" is in, although you can also create shortcuts that use
different working directories.

If there is no "quakesounds.cfg" file in the working directory, and no
settings on the command line, then quakesounds will create a default version
of the config file and exit. Let's do that now by running quakesounds without
any command-line arguments:

    .\quakesounds.py

You should now see a new file named "quakesounds.cfg" in the working
directory.

### The targets file

We also need to tell quakesounds what sounds to extract. This info needs to be
in a file that contains a list of sound resource names. This list can also
specify a new name to use for each sound.

The quakesounds distribution comes with an example of such a file, named
"quakesounds.targets".

You can tell quakesounds to read this info from whatever file you like, using
the `targets_path` setting, but for now we'll just roll with the defaults. So
make sure that the "quakesounds.targets" file is in the current working
directory, since that's the default configuration.

### Which pak files to read

The names and locations of pak files are affected by the `pak_paths` and
`pak_home` settings. Again we're going to roll with the defaults, so just copy
your "pak0.pak" and "pak1.pak" files into the current working directory.

### Sound utilities

If your flavor of quakesounds has internally-bundled versions of SoX and
ffmpeg then you have nothing to worry about here.

If you're setting up your own utilities externally, then for the purposes of
this example make sure that your externally-installed versions of those
utilities are named "sox" and "ffmpeg" and that they are on your executables
path.

### Processing the sounds

The audio processing pipeline for the extracted sounds is controlled by the
`converter` setting. Again though we're going to stick with the default in
this example, which should create noise-reduced, gain-normalized, iOS-ready
versions of the sounds selected in "quakesounds.targets".

So now that you have a config file and everything else in place, just run
quakesounds again:

    .\quakesounds.py

If something went wrong, hopefully a nice error message has explained the
problem. If all went well though, a directory named "quakesounds_out" should
have been created in the working directory, containing a bunch of m4r files.

### Overriding the config file

Let's say you want Ogg Vorbis versions of the sounds instead, because you
want to make alert sounds for an Android phone. Run quakesounds with a
command-line argument this time:

    .\quakesounds.py converter:ogg

The result should be the creation of a bunch of ogg files in "quakesounds_out".

What you did there was change the value of a setting using the command line,
for that one run of quakesounds only. You could have the same effect more
permanently by editing the config file and replacing the value of the
converter setting in there.

You can specify as many settings on the command line as you like. If you like
the Ogg Vorbis output but want it to be a bit louder, you could override the
normalized DB setting in the config file (which is -15) like so:

    .\quakesounds.py converter:ogg norm_db:-13

And if your pak files were located somewhere else, for example in "C:\Quake":

    .\quakesounds.py converter:ogg norm_db:-13 pak_home:C:\Quake

If you need to work with a setting value that has spaces in it, just put
quotes around the whole setting:

    .\quakesounds.py converter:ogg norm_db:-13 "pak_home:C:\path with a space"

Of course if there's a particular setting value that you want to use
repeatedly, you should just edit that setting's value in the config file.
(No quote marks required for values in the config file BTW.)


Customizing
-----------

At this point the natural question is, "what settings are available?" There's
a simple answer, and then a less-simple answer.

### Required settings

quakesounds only has three required settings, i.e. settings that **must** have
values either in the config file or on the command line. These settings are
`targets_path`, `pak_paths`, and `converter`. You can read more about them in
the comments in the default "quakesounds.cfg" file, in the "REQUIRED SETTINGS"
section, but here's the gist.

If you're using the default "quakesounds.cfg", there are four legal values
for the `converter` setting:

* passthru : This extracts the sound file without making any changes.

* wav : This keeps the sound file as a WAV file but performs noise reduction
and gain normalization.

* ogg : Along with noise reduction and gain normalization, this converts the
sound file to Ogg Vorbis format.

* m4r : Along with noise reduction and gain normalization, this converts the
sound file to M4A format, and gives it the iOS-expected m4r file extension.

`targets_path` specifies the file containing a list of selected sounds, as
described above; it can be any file path in the format appropriate for your
OS. (For the format of this file's contents, see the example
"quakesounds.targets" file, and the comments about `targets_path` in the
default "quakesounds.cfg".)

`pak_paths` is a comma-separated list of file paths of pak files to read.

### Optional settings

quakesounds also has an additional group of settings that it will look for,
but if it doesn't find values for them it will assume that they should be
considered false or unset. You can find descriptions of these in the
"OPTIONAL SETTINGS" section of the default "quakesounds.cfg".

The `pak_home` setting used above, for example, is one of the optional
settings. If it is set, then it is used to resolve any relative paths in the
pak_paths list. The `pause_on_exit` setting mentioned earlier is another
optional setting. You can set the `verbose` setting to True for more logging.
You can set `out_working_dir` to control where the output files are generated.

The remaining optional settings are more situational, but it's worth having
a look at their descriptions to see what's available.

### Additional settings

The required and optional settings aren't all the possible settings though.
For example, the `norm_db` setting used in the examples above isn't in either
of those groups. This is because, for convenience, the value of a setting can
include values from other settings, and you can define as many settings as
you like.

`norm_db` is a useful setting because most of the settings that can be
referred to by the `converter` value include a reference to a setting called
`sox_norm`, and `sox_norm` in turn contains a reference to `norm_db`.

Other referenced settings include `sox_path` and `ffmpeg_path`, which define
the file paths to those utilities; you may need to change their values if you
are using external utilities that aren't on your executables path.

And there is nothing sacred about the default collection of available
`converter` values (passthru, wav, ogg, m4r). When you choose a value for the
`converter` setting, you are just naming any other setting. That other
setting's value must define which utility or utilities to launch for
processing sound data, and what arguments to use.

So you can examine the current definitions of the `passthru`, `wav`, `ogg`,
and `m4r` settings to see exactly what they are doing to the sound data. You
can edit the definitions of those settings. You can also add a new setting
containing a definition of a different sound processing pipeline, with
whatever setting name you like, and then specify it as the `converter` to use.

For more information about the way the config settings work, please see the
CONFIGURING.md file.


Legal stuff
-----------

The quakesounds application is licensed under version 3 of the GPL. See the
LICENSE file for the full text of that license.

The SoX and ffmpeg utilities bundled in some distributions of quakesounds are
licensed under version 2 of the GPL. My understanding is that there are no
incompatibilities with that arrangement, especially since I don't compile
against their source or link with their libraries.

The bundled copy of the expak module is also licensed under GPLv3. The bundled
copy of pkg_resources is licensed to be used under the Python Software
Foundation License or the Zope Public License.

