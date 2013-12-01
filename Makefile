.PHONY: default all clean superclean

version := $(shell ./quakesounds_version.py)

bundle_expak := true
bundle_pkg_resources := true

unar := unar -q
zip := zip -q
curl := curl

utils := ffmpeg sox

win_utils := $(addsuffix .exe,$(addprefix util/win/,$(utils)))
mac_utils := $(addprefix util/mac/,$(utils))


# must begin with "ffmpeg-"
ffmpeg_win_dist := ffmpeg-20131123-git-638d79a-win32-static.7z
ffmpeg_win_url := http://ffmpeg.zeranoe.com/builds/win32/static/$(ffmpeg_win_dist)
ffmpeg_win_exe := ffmpeg-20131123-git-638d79a-win32-static/bin/ffmpeg.exe
ffmpeg_win_txt := ffmpeg: FFmpeg \(www.ffmpeg.org\) 32-bit build 20131123 for Windows, from ffmpeg.zeranoe.com

# must begin with "sox-"
sox_win_dist := sox-14.4.1a-win32.zip
sox_win_url := http://softlayer-dal.dl.sourceforge.net/project/sox/sox/14.4.1/$(sox_win_dist)
sox_win_exe := sox-14.4.1/sox.exe
sox_win_txt := sox: SoX 32-bit version 14.4.1a for Windows, from sox.sourceforge.net
# Supporting the extra files this way is bogus -- the file is generated if and
# only if the associated exe is. Need better makefile mojo.
sox_win_extras := sox-14.4.1/zlib1.dll

ffmpeg_mac_dist_src := SnowLeopard_Lion_Mountain_Lion_Mavericks_04.11.2013.zip
# must begin with "ffmpeg-"
ffmpeg_mac_dist := ffmpeg-$(ffmpeg_mac_dist_src)
ffmpeg_mac_url := http://ffmpegmac.net/resources/$(ffmpeg_mac_dist_src)
ffmpeg_mac_exe := ffmpeg
ffmpeg_mac_txt := ffmpeg: FFmpeg \(www.ffmpeg.org\) 64-bit build 04.11.2013 for OS X, from ffmpegmac.net

# must begin with "sox-"
sox_mac_dist := sox-14.4.1-macosx.zip
sox_mac_url := http://softlayer-dal.dl.sourceforge.net/project/sox/sox/14.4.1/$(sox_mac_dist)
sox_mac_exe := sox-14.4.1/sox
sox_mac_txt := sox: SoX 32-bit version 14.4.1 for OS X, from sox.sourceforge.net


sources := $(shell find quakesounds_src -type f)

extras := LICENSE quakesounds.targets README.md LAUNCHING.md CONFIGURING.md

win_util_dists := $(addprefix util_dists/win/,$(foreach dist,$(addsuffix _win_dist, $(utils)),$($(dist))))
mac_util_dists := $(addprefix util_dists/mac/,$(foreach dist,$(addsuffix _mac_dist, $(utils)),$($(dist))))
noarch_util_dists :=

util_dists_readme :=\
This distribution of quakesounds has one or more internally bundled sound\
\\nprocessing utilities. The files in this directory are the original packages\
\\nfrom which those utilities were sourced while building quakesounds.\
\\n\\nThe packages in this directory are NOT necessary for running quakesounds. They\
\\nare included here only for informational purposes, to make sure that you have\
\\naccess to any documentation or licensing info provided in the original package.\
\\n\\nWhen you run quakesounds, it will also list information about any internally\
\\nbundled utilities, including their version number and relevant URLs.


empty :=
space := $(empty) $(empty)


.SECONDEXPANSION:

.PRECIOUS: $(win_util_dists) $(mac_util_dists) $(win_utils) $(mac_utils)


default: all

util/win/%.exe: util_dists/win/$$(%_win_dist)
	@echo "Extracting $@"
	$(eval util := $(basename $(@F)))
	@mkdir -p util_staging
	@$(unar) -o util_staging $<
	@mkdir -p util/win
	@cp util_staging/$($(util)_win_exe) $@
	@if [ -n "$($(util)_win_extras)" ]; then cp util_staging/$($(util)_win_extras) $(@D); fi
	@echo $($(util)_win_txt) > util/win/$(util)_info.txt
	@echo $(util).exe > util/win/$(util)_exename.txt
	@rm -rf util_staging

util/mac/%: util_dists/mac/$$(%_mac_dist)
	@echo "Extracting $@"
	$(eval util := $(basename $(@F)))
	@mkdir -p util_staging
	@$(unar) -o util_staging $<
	@mkdir -p util/mac
	@cp util_staging/$($(util)_mac_exe) $@
	@if [ -n "$($(util)_mac_extras)" ]; then cp util_staging/$($(util)_mac_extras) $(@D); fi
	@echo $($(util)_mac_txt) > util/mac/$(util)_info.txt
	@rm -rf util_staging

util_dists/win/%:
	@echo "Downloading $@"
	$(eval util := $(word 1,$(subst -,$(space),$(@F))))
	@mkdir -p util_dists/win
	@$(curl) $($(util)_win_url) -o $@
	@echo $($(util)_win_txt) > util_dists/win/$(util)_info.txt

util_dists/mac/%:
	@echo "Downloading $@"
	$(eval util := $(word 1,$(subst -,$(space),$(@F))))
	@mkdir -p util_dists/mac
	@$(curl) $($(util)_mac_url) -o $@
	@echo $($(util)_mac_txt) > util_dists/mac/$(util)_info.txt

build/quakesounds_$(version)_%.py: $$(%_utils) $(sources)
	@echo "Building $@"
	@mkdir -p build
	@rm -rf build/quakesounds_src
	@cp -r quakesounds_src build/
	@if $(bundle_expak); then cp bundled_modules/expak.py build/quakesounds_src/; fi
	@if $(bundle_pkg_resources); then cp bundled_modules/pkg_resources.py build/quakesounds_src/; fi
	@if ls util/$*/* &>/dev/null; then cp util/$*/* build/quakesounds_src/res/; fi
	@cd build/quakesounds_src; $(zip) -r ../quakesounds.zip *
	@echo '#!/usr/bin/env python' | cat - build/quakesounds.zip > $@
	@chmod +x $@
	@rm build/quakesounds.zip
	@rm -rf build/quakesounds_src

build/quakesounds_$(version)_%.zip: build/quakesounds_$(version)_%.py $(extras) $$(%_util_dists)
	@echo "Bundling $@"
	@cp $(extras) build/
	@rm -rf build/util_dists_info
	@if test -n "$($*_util_dists)"; then mkdir build/util_dists_info; fi
	@if test -n "$($*_util_dists)"; then cp util_dists/$*/* build/util_dists_info/; fi
	@if test -n "$($*_util_dists)"; then echo $(util_dists_readme) > build/util_dists_info/README.txt; fi
	@cd build; mv quakesounds_$(version)_$*.py quakesounds.py; $(zip) quakesounds_$(version)_$*.zip $(extras) util_dists_info/* quakesounds.py
	@cd build; rm -rf $(extras) util_dists_info quakesounds.py

all: build/quakesounds_$(version)_noarch.zip build/quakesounds_$(version)_win.zip build/quakesounds_$(version)_mac.zip

clean:
	rm -rf build

superclean: clean
	rm -rf util_staging
	rm -rf util_dists
	rm -rf util
