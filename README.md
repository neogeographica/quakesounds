quakesounds: audio processing pipeline for Quake sound samples
==============================================================

**Current release:** [1.0](https://github.com/neogeographica/quakesounds/releases)

quakesounds is a utility for easily ripping sounds out of Quake pak files and
pushing them through a sequence of audio processing effects.

Motivation came from my experience setting up a few Quake-related noises as
alert sounds on my phone. That involved a surprising amount of work to find
good alert-sound candidates and then extract, rename, noise-reduce,
format-convert, and gain-normalize them. So I thought it might be neat if I
gave other folks a shortcut for that process.

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
processing that uses them. It's preferable to get the most recent versions of
those utilities.

* If you intend to use audio processing utilities other than SoX or ffmpeg,
quakesounds can certainly accomodate that, but you'll have to install other
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
starters. In this quickstart section we'll create some sound files as quickly
as possible; the next sections will describe what is happening in more
detail.

1. If you're using a quakesounds distribution that has internally-bundled
utilities, skip ahead to step 2. Otherwise, if you're using your own external
versions of sox and ffmpeg, then make sure that those utilities are installed
and ready to go. For the purposes of this quickstart, sox and ffmpeg (or on
Windows, sox.exe and ffmpeg.exe) need to be placed in your executables path
-- i.e. running them should not require typing their entire path.

2. If you're going to run quakesounds from a command prompt, make sure that
the working directory for that command prompt is the directory where the
"quakesounds.py" file is located.

3. Now run quakesounds once, using "quakesounds.py" (as described in
LAUNCHING.md).

4. You should see a "quakesounds.cfg" file appear in that directory.

5. Now make sure that that directory also contains the file
"quakesounds.targets" that came with the quakesounds distribution.

6. Copy your "pak0.pak" and "pak1.pak" files into that same directory.

7. Run quakesounds again. (You may see a couple of warnings about "clipping";
this is expected. If you see a *lot* of warnings, your version of the SoX
utility may be old.)

8. You should see a "quakesounds_out" subdirectory appear. "quakesounds_out"
should contain several files with the m4r extension; these are noise-reduced,
gain-normalized, iOS-alert-sound-ready versions of a few selected Quake
sounds.

Victory! But now let's take a closer look at what is going on there.


Walkthrough
-----------

For the example command lines in this section, I'll assume that you're on
Windows, that Python is on your executables path, that "quakesounds.py" is in
your current working directory, and that you're running it manually from a
command prompt. If not, adjust the examples as necessary... the important
thing here is not going to be exactly how quakesounds is launched, but rather
what command-line arguments (if any) we give it.

### The config file

quakesounds will look for its configuration in a file named "quakesounds.cfg".
Settings can also be specified on the command line to add to or change the
settings taken from this file; however the command line will usually be used
for temporarily changing just a few settings, while the "quakesounds.cfg" file
should contain the complete baseline configuration that you use.

quakesounds expects the "quakesounds.cfg" file to be in the current working
directory. If you're manually running quakesounds then the working directory
is whatever directory you're in. If you run quakesounds by double-clicking an
icon, then the working directory is normally whatever directory
"quakesounds.py" is in, although you can also create shortcuts that use
different working directories.

If there is no "quakesounds.cfg" file in the working directory, and no
settings on the command line, then quakesounds will create a default version
of the config file and exit. So if you run quakesounds without any
command-line arguments:

    .\quakesounds.py

... then that will create a default "quakesounds.cfg" file in the working
directory **if** there is not currently such a file. On the other hand, if
there already is a config file, then invoking quakesounds like this will run
it using whatever settings are in the config file.

### The targets file

We also need to tell quakesounds what sounds to extract. This info needs to be
in a file that contains a list of sound resource names. This list can also
specify a new name to use for each sound.

The quakesounds distribution comes with an example of such a file, named
"quakesounds.targets". Take a look inside that file to see an example of how
the sounds were selected and named.

You can tell quakesounds to read this info from whatever file you like, using
the `targets_path` setting. The setting in the default "quakesounds.cfg"
will look for a file named "quakesounds.targets" in the working directory.

### Which pak files to read

The names and locations of pak files are affected by the `pak_paths` and
`pak_home` settings. In the default "quakesounds.cfg" file, `pak_paths` is set
to pak0.pak,pak1.pak and `pak_home` is unset. This configuration will make
quakesounds look for "pak0.pak" and "pak1.pak" files in the current working
directory.

### Processing the sounds

The audio processing pipeline for the extracted sounds is controlled by the
`converter` setting. In the default "quakesounds.cfg" file, `converter` is
set to m4r, which will create iOS alert sounds.

In the quickstart, once you had a config file in place, you ran quakesounds
again without any command line arguments and without editing the config file.
This means that all of the default settings described above were used to
select and process the sound files, the result being a bunch of m4r files
in the "quakesounds_out" directory.

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

    .\quakesounds.py converter:ogg norm_db:-12

And if your pak files were located somewhere else, for example in
"C:\Quake\id1":

    .\quakesounds.py converter:ogg norm_db:-12 pak_home:C:\Quake\id1

If you need to work with a setting value that has spaces in it, just put
quotes around the whole setting:

    .\quakesounds.py converter:ogg norm_db:-12 "pak_home:C:\path with a space"

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
You can set `out_working_dir` to specify the directory where the output files
are placed.

The remaining optional settings are more situational, but it's worth having
a look at their descriptions to see what's available.

### Additional settings

The required and optional settings aren't all the possible settings though.
For example, the `norm_db` setting used in the examples above isn't in either
of those groups. This is because, for convenience, the value of a setting can
include values from other settings, and you can define as many settings as
you like.

In the default "quakesounds.cfg" file, `norm_db` is one of these additional
settings used by other settings. `norm_db` is referenced in a setting named
`sox_norm`, which defines the command-line arguments necessary for gain
normalization with SoX. The `sox_norm` setting in turn is referenced in every
converter command definition that uses SoX and does gain normalization.

So by setting a value for `norm_db` you affect any sound conversion that does
gain normalization. With `norm_db` isolated in this way, gain adjustments are
simpler to do (especially when doing them on the quakesounds command line).

Other settings referenced in the default config include `sox_path` and
`ffmpeg_path`, which define the file paths to those utilities; you may need to
change their values if you are using external utilities that aren't on your
executables path.

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
