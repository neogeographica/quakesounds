Configuring quakesounds
-----------------------

This description assumes that you've already read the "Quickstart" and
"Customizing" sections in README.md. Below are more details about exactly how
the quakesounds configuration is interpreted.

### Config format

A line in the config file is ignored if it is empty, or if its first non-
whitespace character is a "#" character.

All other lines are interpreted as settings. Every setting in the config file
is in the format of a setting name and a setting value, separated by a colon.
You can put some spaces before the setting name and/or around the colon if you
want, to make things more readable.

For example:

    targets_path : quakesounds.targets

The value can have colon characters in it if necessary; only the first colon
on the line is used to separate the setting name from its value. The value can
also have spaces in it, although leading or trailing whitespace in the value
will be stripped. (But cf. the description of the `%space%` token below.)

Settings specified on the command line for quakesounds follow the same format,
although the whole setting (name, colon, value) will need to be enclosed in
quote marks if the value contains spaces, or if you want to put spaces around
the colon.

Command-line settings take precedence over settings from the config file.

### Config example

If you run quakesounds without any command-line arguments, and without any
"quakesounds.cfg" file in the working directory, then it will create a
default "quakesounds.cfg" file in the working directory. This default config
file contains examples of all of the required and optional settings and is
heavily commented, so it's a good additional reference.

### Path format

Any setting value that is a path to a file or directory should be in the
format appropriate for the OS you're using to run quakesounds.

### Setting value substitution

Every setting value can include the value of some other setting(s), as well
as some special automatically generated values. For some settings this can be
very useful. For others not so much, but just to keep things clear the same
rules are applied to **every** setting value.

To include the value of setting `A` in the value of setting `B`, you would
refer to the value of setting `A` by using the token `%A%` somewhere in the
value of setting `B`. So for example if you defined these three settings:

    pak_paths : %my_home_dir%pak0.pak
    out_working_dir : %my_home_dir%quakesounds_output
    my_home_dir : /home/bob/

... then the value of `pak_paths` will be /home/bob/pak0.pak and the value of
`out_working_dir` will be /home/bob/quakesounds_output. It doesn't matter in
what order the settings are defined. It doesn't matter if some are defined on
the command line and some in the config file.

If you need to get fancy, the result of a substitution can itself contain
more settings tokens, etc. and so forth, but creating a super-deep stack of
substitutions is not allowed & will cause quakesounds to shut down.

Once all the substitutions have been processed for tokens that reference
user-defined settings, a few more special tokens will be taken care of:

* `%qs_home%` is the complete path to the directory containing the quakesounds
application, including any trailing path separator.

* `%qs_working_dir%` is the complete path to the current working directory at
the time that quakesounds is invoked, including any trailing path separator.

* `%qs_internal%` is the path to a directory where any resources packaged
inside the quakesounds application are temporarily stored while quakesounds is
running. It is a directory that will be deleted, along with its contents, when
quakesounds exits. When quakesounds starts, this directory is populated with
the following files:

  * A SoX noise-reduction profile useful for Quake sounds is made available as
  `%qs_internal%noiseprofile`

  * If your version of quakesounds is bundled with the SoX utility included,
  that is made available as `%qs_internal%sox`

  * If your version of quakesounds is bundled with the ffmpeg utility
  included, that is made available as `%qs_internal%ffmpeg`

* `%percent%` will resolve to the "%"" character.

* `%comma%` will resolve to the comma character. This can be useful in a
couple of the settings below whose values are comma-separated lists of things,
if you need to actually have a comma in one of the values.

* `%space%` and `%empty%` will resolve to the space character or emptystring,
respectively. quakesounds will strip whitespace from the beginning or end of
any setting value (or any element in a comma-separated list), and will discard
any setting with a completely empty value. So if you really need a value to
begin/end with a space, or to represent emptystring, you can use these tokens.

* `%sound_name%` and `%write_to%` are special tokens that are only available
for use in settings that define converter commands.

  * `%sound_name%` will resolve to the name to be used for the sound resource
  that is currently being processed (as defined in the file pointed to by the
  required `targets_path` setting). Commonly you'll use this as the basename
  of the file to create in the final command stage.

  * `%write_to%` represents a special sound-processing command that takes one
  argument, which is a file path to create and write to. It takes data on
  stdin and writes it directly to the specified file without changing the data.
  `%write_to%` can be the command for the only or last stage in a chain. Any
  other stages after a `%write_to%` stage it will be ignored.

For more context about `%sound_name%` and `%write_to%`, see the default
"quakesounds.cfg", its converter command definitions, and their comments.

For any special token that represents a path, its value will always be in the
correct format for the current operating system.

### A technical note that probably won't matter

Tokens in a value are discovered reading from left to right. Note that even
though the settings substitutions are done first, they won't disturb the
special tokens. So as a contrived example, if you have these two settings:

    foo : fish
    bar : foo%comma%foo%comma%foo

... then the final value of `bar` will be foo,foo,foo rather than
foo%commafishcomma%foo.
